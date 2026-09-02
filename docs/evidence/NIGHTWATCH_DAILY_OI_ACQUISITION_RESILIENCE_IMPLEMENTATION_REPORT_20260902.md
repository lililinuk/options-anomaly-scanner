# Nightwatch Daily OI Acquisition Resilience Implementation Report

Date: 2026-09-02

Authorization: future-production acquisition resilience only. No historical repair,
canonical scan, deployment, GCP change, live Nightwatch validation, or production database
write was authorized or performed.

## Repository checkpoint

- Canonical repository: `F:\options-anomaly-scanner`
- Base branch: `main`
- `BASE_HEAD`: `e4d43f9ff08e45d55a5d82d0dad17815439e7796`
- Freshly fetched `origin/main` before branching:
  `e4d43f9ff08e45d55a5d82d0dad17815439e7796`
- Implementation branch: `fix/daily-oi-acquisition-resilience`
- The worktree was clean before branch creation.
- `feat/trading-dashboard-vnext` was not checked out, changed, merged, or rebased.

## Accepted root causes addressed

### HTTP 429 aborted the remaining ticker expiries

Before this change, the production Scheduler-created Nightwatch client used
`max_retries=0`. A chain-snapshot HTTP 429 raised `NightwatchError` from
`DailyOiArchiver._fetch_materialized_chain`. The expiry loop handled only HTTP 404, so
the 429 escaped `_archive_ticker`. The outer ticker loop then set the ticker row to
`VENDOR_ERROR`. Because all expiry rows had already been created as `PENDING`, every
later independent expiry stayed `PENDING` and was never requested. The original 429
was present in `api_usage_audit`, but the ticker detail was reduced to the terminal
vendor error.

`CURRENT_429_BEHAVIOR=ABORT_TICKER_AND_LEAVE_LATER_EXPIRIES_PENDING`

### Parser-invalid HTTP 200 had no recovery opportunity

Before this change, a chain HTTP 200 was parsed once. `INVALID_RESPONSE` set the expiry
to incomplete, recorded aggregate invalid reasons, and continued to later expiries.
There was no retry. Missing, null, non-numeric, negative, non-integral, or otherwise
invalid open interest remained invalid; explicit numeric zero was already valid.

`CURRENT_INVALID_RESPONSE_BEHAVIOR=FAIL_CLOSED_AND_CONTINUE_WITHOUT_RETRY`

### Pre-fix operational summary

- `CURRENT_ABORT_SCOPE=TICKER_FOR_NON_404_NIGHTWATCH_ERROR`
- `CURRENT_RETRY_POLICY=PRODUCTION_CLIENT_ZERO_TRANSPORT_RETRIES;_ONLY_202_MATERIALIZATION_POLLING_IS_BOUNDED`
- `CURRENT_RATE_PACING=NO_429_PACING;_202_USES_PAYLOAD_RETRY_AFTER_THEN_HEADER_THEN_2_SECOND_DEFAULT`
- `CURRENT_VENDOR_DATE_GUARD=OI_SURFACE_REQUIRES_ONE_VENDOR_DATE;_NO_DEFERRED_CHAIN_RECOVERY_GUARD_EXISTED`

## Implemented two-phase behavior

### Phase A: normal acquisition

Normal expiry acquisition is unchanged for successful, bounded, 202-materializing, and
404 lifecycle cases. A 429 is now contained at expiry scope:

1. The original request remains in the existing append-only API usage audit.
2. The expiry is marked `TRANSIENT_RATE_LIMIT`, not complete.
3. Safe failure metadata and the source request ID are retained.
4. The delay is selected from `Retry-After`, then `X-RateLimit-Reset`, then the configured
   two-second recovery defer.
5. The delay is honored before any later expiry request.
6. Later independent expiries continue after the wait instead of remaining `PENDING`.
7. The failed expiry is queued for Phase B.

An HTTP 200 classified by the unchanged parser as `INVALID_RESPONSE` also enters the
Phase-B queue. Its raw payload was already persisted through the existing ingestion
path, preserving the original invalid response.

### Phase B: bounded deferred recovery

After the normal expiry pass, each queued expiry can receive one direct recovery
request. The code does not call the multi-poll materialization helper in Phase B, so one
recovery attempt is one network request. An HTTP 202 recovery remains incomplete as
`MATERIALIZATION_PENDING`; it does not trigger extra polls.

The retry uses the same chain endpoint, expiration identity, parser, raw ingestion, API
usage observer, global quota budget, and persistence model as normal acquisition. It has
a distinct safe audit command:
`daily_archive.options.chain_snapshot.deferred_recovery`.

- A second 429 is recorded and stops without another retry.
- A second `INVALID_RESPONSE` remains incomplete.
- `FULL_COMPLETE` and `COMPLETE_BOUNDED_SNAPSHOT` are accepted only under their existing
  meanings and only after the vendor-date guard passes.
- Successful recovery removes the expiry from the current incomplete list, decrements
  the existing incomplete counter, persists contracts once, and updates the existing
  complete/full/bounded counters.

## Retry timing and cost governance

The versioned `ArchiveLimits` configuration now contains:

- `recovery_max_attempts_per_failed_expiry=1`
- `recovery_max_attempts_per_run=7`
- `recovery_default_defer_seconds=2.0`

Seven is deliberately tied to the fixed MAG7 universe: pathological failures can add no
more than one recovery request per constituent on average. This is a separate, tighter
boundary inside the existing 250-paid-unit and 350-network-attempt archive budgets. It
prevents every failed expiry in a pathological run from multiplying paid work while
still permitting one recovery opportunity across the normal seven-ticker collection.

The per-expiry and run-level caps apply to attempts, not only paid responses. No recovery
loop is unbounded.

## Mandatory vendor-date guard

A recovery can persist contracts only when:

- the unchanged parser returns an accepted complete classification;
- chain-level `open_interest_as_of` is explicitly present;
- its date equals the ticker collection's single Daily OI vendor date; and
- every contract-level `open_interest_as_of` that is explicitly present has the same
  date.

Missing identity is rejected. Rolled-forward data is retained only as later raw/audit
attempt evidence, the expiry becomes `VENDOR_DATE_MISMATCH`, and no contract rows are
written for the old vendor date. Vendor timestamps are never backdated.

## Data quality and idempotency

The parser was not relaxed. Explicit OI zero remains valid. Missing, null, unparseable,
negative, non-finite, and non-integral OI remain invalid and are never converted to zero.

Successful persistence is centralized in one helper used by normal and recovery paths.
It preserves the existing contract unique identity and refuses to persist again once the
expiry already has an accepted complete status. Recovery creates no expiry row, ticker
row, archive run, canonical slot, scan, Candidate, or First-Knowledge row.

The ticker JSON keeps `deferred_recovery_history` with safe metadata for original outcome,
original request ID, retry reason, retry number, actual retry time, expected vendor date,
returned vendor/as-of identity, parser result, final outcome, and persisted contract
count. Secrets and request headers are excluded. Original raw payload and API usage rows
remain append-only.

## Compatibility boundaries

- Ticker `COMPLETE` still requires no genuine current incomplete expiry.
- A retry attempt alone never changes readiness eligibility.
- `COMPLETE_BOUNDED_SNAPSHOT` remains distinct from `FULL_COMPLETE`.
- The accepted 400-contract near-ATM vendor bound is unchanged.
- Accepted expired-expiry HTTP 404 lifecycle behavior is unchanged.
- Radar continues to require persisted literal `COMPLETE` where it previously did.
- Daily OI readiness accepted statuses are unchanged.
- Previous-XNYS-session selection is unchanged.
- Phase2A scoring, Stage9, Candidate, and Frozen First-Knowledge semantics are unchanged.

## Historical production preservation

No code path was run against the 2026-09-01 archive. Its RADAR_OI, DEALER_GEX, and
ACTIVITY_VNEXT slots were not read or written during implementation. The historical
`HELD_NOT_READY` Activity occurrence, `scan_run_id=null`, AAPL/TSLA archive evidence, and
all historical request timestamps remain unchanged. No retroactive scan or backfill was
created.

## Historical option-chain capability finding

Repository-preserved Nightwatch capability/OpenAPI evidence documents
`GET /v1/options/chain-snapshot/{ticker}` with one required `expiration` parameter and no
date, as-of, start, end, before, after, cursor, page, or other historical selector. No
documented immutable historical OI chain endpoint was found.

- `HISTORICAL_OI_CHAIN_RETRIEVAL_SUPPORTED=NO`
- `HISTORICAL_ENDPOINT_IF_DOCUMENTED=NONE`

No OpenAPI, discover, health, paid data, or other Nightwatch request was made for this
finding.

## Files changed

Application:

- `backend/app/scanner/archive.py`
- `backend/app/scanner/config.py`
- `backend/app/nightwatch/client.py`
- `backend/app/nightwatch/errors.py`
- `backend/app/scanner/daily.py`
- `backend/app/cli.py`

Tests:

- `backend/tests/test_daily_oi_acquisition_resilience.py`

Evidence:

- `docs/evidence/NIGHTWATCH_DAILY_OI_ACQUISITION_RESILIENCE_IMPLEMENTATION_REPORT_20260902.md`

No migration was created.

## Validation evidence

All tests used mocks, fixtures, and local model objects. No test contacted Nightwatch or
the production database.

- Focused new resilience plus existing Daily OI remediation: 28 passed.
- Phase2A/readiness regression group: 71 passed.
- Existing Nightwatch client, Daily OI archive, and archive parser group: 31 passed.
- Stage9 regression group: 40 passed.
- GCP canonical Scheduler regression: 25 passed.
- Full backend suite from the required `backend` working directory: 499 passed.
- Ruff over the full backend: passed.
- `git diff --check`: passed (Git emitted only the repository's Windows line-ending
  conversion warnings).
- Alembic: one head, `20260828_0020`.

The first full-suite command was intentionally run from the repository root and exposed
one unrelated path-sensitive test that opens `alembic/...` relative to the current
directory. Re-running from the intended `backend` directory passed all 499 tests. No code
change was made for that harness issue.

## External effects

- Nightwatch requests: 0
- Paid units: 0
- Production database writes: 0
- Remote schema writes: 0
- Manual Scheduler dispatches: 0
- GCP configuration changes: 0
- Historical production rows modified: 0
- Retroactive canonical scans: 0

External URLs/API endpoints contacted: none.

## Residual limitations

- Deferred recovery is intentionally limited to HTTP 429 and parser
  `INVALID_RESPONSE`, the two accepted incident modes. Other non-404 Nightwatch errors
  retain their existing fail-closed ticker behavior.
- A recovery HTTP 202 receives no additional materialization poll because the resilience
  contract permits one recovery request per failed expiry.
- Recovery requires explicit chain OI date identity. A response lacking that identity is
  intentionally unusable for repair.
- The seven-attempt cap can leave additional failures unretried; those expiries and the
  ticker remain non-complete and readiness remains fail-closed.
- No documented vendor endpoint can retrieve an immutable prior chain after the live
  snapshot rolls forward, so preservation at acquisition time remains essential.

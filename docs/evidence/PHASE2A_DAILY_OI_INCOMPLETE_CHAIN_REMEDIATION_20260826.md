# Phase 2A Daily OI Incomplete-Chain Remediation

Date: 2026-08-26

Authorization: approved acquisition/reliability remediation

Result: implementation and offline regression verification complete; natural scheduled runtime pending

## Incident evidence

The production parent run `2b307e83-e806-4409-9eee-bddd78859298` was `PARTIAL` for New York
market date `2026-08-26`. Radar completed with 350 persisted rows across seven tickers. Daily OI
persisted 11,190 contracts but completed only 58 of 96 attempted expiry chains; 38 were incomplete.
The parent recorded 77 consumed quota units, 110 network attempts, and 630.663 elapsed seconds.

Child run `f6f3275e-497c-4d27-a68b-b11baded4c81` was `PARTIAL`, with 70 consumed units, 103
network attempts, 58 complete chains, 38 incomplete chains, and 11,190 contracts persisted.
Ticker completion counts were AAPL 9/14, AMZN 9/14, GOOGL 7/14, META 6/14, MSFT 8/13, NVDA
10/13, and TSLA 9/14.

Historical child run `ccb84da6-3e58-4fff-b978-72df37c722c3` remained `RUNNING` after its
parent failed through `PendingRollbackError`. This remediation did not mutate that historical row.

## Exact root causes

### HTTP 202

Before remediation, `NightwatchClient.request()` treated HTTP 202 as a non-error successful
response. HTTP 202 was absent from the ordinary transient-status retry set, the client did not read
`_meta.retry_after_seconds`, and `DailyOiArchiver` immediately passed the empty materializing
payload to the completeness parser. The result was a generic incomplete chain with no poll.

Repository vendor evidence establishes that on-demand materialization can return HTTP 202 with
`_meta.status`, `_meta.hint`, and `_meta.retry_after_seconds`. The incident audit contained 33
HTTP 202 chain responses. Those responses had `consumed_quota=NULL` in historical audit rows and
were excluded from the authoritative 70 paid units: seven OI-surface HTTP 200 responses plus 63
chain HTTP 200 responses equal the recorded 70.

After remediation, only the unresolved ticker/expiry request is polled. The request identity and
expiration parameters are unchanged. The client abstraction performs the delay. Delay precedence
is payload `_meta.retry_after_seconds`, then HTTP `Retry-After`, then the configured 2-second
fallback. The bound is three total network calls per chain and no more than 30 seconds of aggregate
poll wait. Exhaustion persists `MATERIALIZATION_TIMEOUT`; it never becomes fake `COMPLETE`.
Each poll passes through the normal usage observer, so every actual request increments
`network_attempts`. HTTP 202 is now explicitly non-paid and HTTP 200 remains one paid unit under
the established accounting evidence.

### Pagination and the 400-row cap

The preserved repository/OpenAPI capability evidence exposes one required query parameter for
`/v1/options/chain-snapshot/{ticker}`: `expiration`. It contains no supported cursor, page,
offset, limit, next-page token, continuation URL, or other retrieval contract. No pagination
parameter was invented.

The incident raw evidence confirms:

- META `2026-09-18`: 400 returned of 434, `truncated=false`.
- NVDA `2026-12-18`: 400 returned of 494, `truncated=false`.

The old client made one request and stopped. The remediated classifier persists these as
`PAGINATION_INCOMPLETE` and writes no contract rows from the subset. If Nightwatch later documents
a continuation contract, multi-page retrieval remains a separately evidence-gated follow-up.

### Complete-count cases

The old parser first checked `returned == total` and `truncated == false`, then silently invalidated
the entire chain when any contract failed a required invariant. It returned only `complete=false`,
so the stored incident detail exposed counts but not the actual row defect.

A targeted read-only transaction over preserved raw payloads found:

- GOOGL `2026-09-04`: 204/204, `truncated=false`, two invalid/missing `open_interest` values.
- TSLA `2026-08-31`: 236/236, `truncated=false`, four invalid/missing `open_interest` values.
- TSLA `2026-09-02`: 240/240, `truncated=false`, four invalid/missing `open_interest` values.

These were legitimate other completeness failures, not stale count/truncation state. They remain
incomplete as `INVALID_RESPONSE`, now with aggregate `INVALID_OPEN_INTEREST` counts. A valid HTTP
200 response with matching count, `truncated=false`, valid unique contract identities, matching
expiration/right, positive strike, and numeric OI is explicitly `COMPLETE`.

The classifier now emits `COMPLETE`, `MATERIALIZATION_TIMEOUT`,
`PAGINATION_INCOMPLETE`, `ROW_COUNT_MISMATCH`, `TRUNCATED`, or `INVALID_RESPONSE` as
applicable. Existing 404 lifecycle classifications remain unchanged. Duplicate contract symbols
are rejected before persistence and cannot create duplicate contract rows.

### Orphan `RUNNING` lifecycle

The historical orphan originated when a handled vendor path attempted a second ticker row for the
same `(archive_run_id, ticker)` key. The resulting integrity failure poisoned the SQLAlchemy
transaction, and cleanup attempted terminal-state persistence before a successful rollback,
producing `PendingRollbackError`. The canonical starting branch already contained the targeted
duplicate-row/rollback remediation.

This remediation strengthens the prospective terminal path: it rolls back before reading or
updating the child run, sets `FAILED`, `completed_at`, counters, and a safe exception class, then
commits. If the original session cannot commit, it retries terminal persistence in a fresh
SQLAlchemy session bound to the same engine. The parent path retains its rollback before recording
the failed child subjob and can persist its own terminal state.

## Observability

After every attempted Daily OI ticker, scheduled output now includes a compact line containing:

`ticker`, `status`, `vendor_oi_date`, `expiries_expected`, `complete_chains`,
`incomplete_chains`, `contracts_persisted`, and sorted aggregate `incomplete_reasons`.

Unexpected ticker exceptions emit only ticker identity, terminal failure label, and safe exception
class. Credentials, headers, raw payloads, and contract lists are never logged. The final CLI line
remains concise. Standalone Daily OI now also exits non-zero for partial/failed outcomes; the
scheduled parent continues to map `COMPLETE` to zero and `PARTIAL`/`FAILED` to non-zero.

## Files changed

Application files:

- `backend/app/nightwatch/client.py`
- `backend/app/scanner/config.py`
- `backend/app/scanner/parsers.py`
- `backend/app/scanner/archive.py`
- `backend/app/cli.py`

Test files:

- `backend/tests/test_phase2a_daily_oi_remediation.py`
- `backend/tests/test_stage4a_daily_pipeline.py`

Evidence:

- `docs/evidence/PHASE2A_DAILY_OI_INCOMPLETE_CHAIN_REMEDIATION_20260826.md`

No Radar qualification, OI materiality, candidate, scoring/ranking, Phase 2B, Dealer/GEX,
dashboard, schedule, ticker-universe, or paid-frequency logic changed.

## Verification

- Focused backend regression: `47 passed in 2.31s`.
- Focused Ruff: `All checks passed`.
- Full backend regression: `413 passed in 4.48s`.
- Frontend ESLint: passed.
- Frontend Next.js production build: passed, including TypeScript and static-page generation.
- `git diff --check`: passed.

The focused suite proves 202-to-200 completion, payload retry delay handling through the client
abstraction, bounded repeated 202 behavior, explicit timeout persistence, per-poll attempt
accounting, established paid-unit semantics, capped-response rejection, duplicate fail-closed
behavior, complete valid responses, legitimate other invariant failures, and child terminal
finalization after rollback. Existing Stage 4A and Stage 8 suites preserve Radar and CLI
false-green behavior. The full suite guards candidate/scoring and all other application behavior.

## Cost, writes, migrations, and external contacts

```text
NIGHTWATCH_REQUESTS=0
PAID_UNITS=0
MANUAL_GITHUB_WORKFLOW_RUNS=0
REMOTE_DB_WRITES=0
REMOTE_SCHEMA_WRITES=0
MIGRATIONS=0
PRS=0
WORKTREES=0
```

External systems contacted:

- `https://github.com/lililinuk/options-anomaly-scanner.git` via `git fetch` for the mandated
  alignment checks and final synchronization.
- Read-only PostgreSQL transaction at
  `postgresql://aws-0-ap-northeast-1.pooler.supabase.com:5432/postgres` for the five targeted
  preserved chain payloads and aggregate usage evidence.

No Nightwatch URL/API endpoint was contacted. No GitHub Actions workflow was dispatched. The
read-only database transaction was explicitly set `READ ONLY` and rolled back; it printed no
credentials or raw payloads.

## Git and final-state recording

Starting branch/state:

```text
branch=main
HEAD=c364183fff98d74e1d79f78a38a4fb07f94493f9
origin/main=c364183fff98d74e1d79f78a38a4fb07f94493f9
working_tree=clean
```

Implementation branch: `fix/phase2a-daily-oi-incomplete-chain`.

The report is committed with the remediation, so it cannot self-record the containing commit's
SHA without changing that SHA. The exact accepted commit, final local `HEAD`, fetched
`origin/main`, current branch, and clean-tree verification are recorded in the task's final
response after push.

## Residual vendor/data risks

- Capped 400-row chains remain truthfully incomplete because no supported continuation contract is
  preserved in repository/vendor evidence.
- Materialization can exceed the three-attempt/30-second poll-wait policy and will remain
  `PARTIAL` with `MATERIALIZATION_TIMEOUT`.
- Vendor rows with missing required OI remain unavailable rather than being converted to zero.
- A total database outage can prevent any process from persisting a terminal row; the remediation
  covers recoverable failed-transaction/session poisoning with a fresh-session fallback.

## Next natural scheduled run acceptance

The next natural Phase 2A scheduled run on `origin/main` must prove:

- Radar remains `COMPLETE`.
- 202 responses are polled only within the configured bound and explainable attempt accounting.
- Materialized 200 responses become complete only when every invariant passes.
- Capped responses remain explicit `PAGINATION_INCOMPLETE` until vendor continuation is proven.
- Missing/invalid required OI remains explicit `INVALID_RESPONSE`.
- Every child run reaches a terminal state with `completed_at`.
- GitHub logs contain ticker summaries and aggregate reason counts.
- Daily OI is `COMPLETE` when all vendor data resolves within policy; otherwise `PARTIAL` remains
  truthful and the CLI remains non-zero.

No manual validation, rerun, workflow dispatch, or Nightwatch request is authorized after push.

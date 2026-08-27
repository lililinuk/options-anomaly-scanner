# Phase 2A Vendor-Bounded Chain Semantics Amendment

Date: 2026-08-27

Result: implemented, verified offline, and ready for the next natural scheduled runtime.

## 1. Vendor-confirmed product contract

The Nightwatch developer confirmed the contract for:

`GET /v1/options/chain-snapshot/{ticker}`

for one ticker and expiration:

- the maximum returned contract count is 400;
- when the expiry contains more than 400 contracts, Nightwatch selects the 400
  contracts whose strikes are closest to the underlying price;
- this is a near-ATM bounded snapshot, not a mathematically full option chain;
- the endpoint has no pagination, cursor, offset, limit, or next-page mechanism;
- contracts outside the returned 400 cannot currently be retrieved through this endpoint;
- `_meta.truncated=false` does not represent this internal product cap; and
- `total_contracts > contracts.length` with 400 valid returned rows is intentional
  vendor-bounded delivery, not an acquisition failure.

The vendor contract is preserved in validated archive configuration as a 400-row limit,
`NEAR_ATM_BOUNDED` coverage scope, and `pagination_supported=false`.

## 2. Previous and amended semantics

Before the vendor clarification, the fail-closed classifier treated every
`total_contracts > contracts.length` response as `PAGINATION_INCOMPLETE`. This caused
the expiry, ticker, Daily OI parent, CLI exit, and scheduled job to become incomplete/red.
That behavior was conservative under the prior evidence.

The amended chain classifier now emits:

- `FULL_COMPLETE`: the valid returned-row count equals the vendor total and all accepted
  invariants pass;
- `COMPLETE_BOUNDED_SNAPSHOT`: exactly 400 valid rows are returned, the vendor total is
  greater than 400, materialization resolved, and no other acquisition/integrity failure
  exists; or
- a genuine incomplete reason such as `MATERIALIZATION_TIMEOUT`, `INVALID_RESPONSE`,
  `ROW_COUNT_MISMATCH`, `TRUNCATED`, or an upstream HTTP/persistence/database failure.

A shortfall below 400 does not qualify for the bounded product rule. For example, 399
returned rows with a larger total remains `ROW_COUNT_MISMATCH`. Invalid required rows
are checked before bounded qualification and remain `INVALID_RESPONSE`.
`PAGINATION_INCOMPLETE` is no longer emitted by this endpoint classifier because the
vendor confirms that pagination does not exist.

The exact new bounded status name is `COMPLETE_BOUNDED_SNAPSHOT`.

## 3. Persisted status compatibility

No migration was created.

For compatibility with existing Radar and persistence eligibility gates:

- the existing persisted `ExpiryOiDailySnapshot.chain_status="COMPLETE"` remains the
  full-chain marker;
- the classifier names that state `FULL_COMPLETE` in its explicit result and the JSON
  summaries count it as `full_complete_chains`; and
- a bounded expiry persists
  `ExpiryOiDailySnapshot.chain_status="COMPLETE_BOUNDED_SNAPSHOT"`.

This avoids changing Radar logic. Bounded coverage is not promoted to the legacy
`chain_status="COMPLETE"` full-chain gate.

## 4. Coverage metadata

Every newly accepted bounded expiry is recorded in the existing
`DailyOiArchiveTicker.details.bounded_complete_expiries` JSON array with:

- `expiration`;
- `coverage_type=COMPLETE_BOUNDED_SNAPSHOT`;
- `coverage_scope=NEAR_ATM_BOUNDED`;
- `full_chain_available=false`;
- `vendor_contract_limit=400`;
- `vendor_total_contracts=<vendor total>`;
- `contracts_returned=400`;
- `contracts_omitted=vendor_total_contracts - contracts_returned`; and
- `pagination_supported=false`.

Ticker details also preserve `coverage_reason_counts`,
`accepted_lifecycle_unavailable_chains`, and the explicit chain counters below.
No missing value is fabricated.

## 5. Counter semantics

The existing persisted integer counters remain backward-compatible:

- `complete_chains` counts operationally accepted archived snapshots and therefore
  includes both full-complete and complete-bounded snapshots;
- `incomplete_chains` retains its historical attempt-accounting behavior: it includes
  genuine incomplete chains and unavailable chains, including the separately accepted
  expired-expiry 404 lifecycle case.

Because those legacy integers cannot alone express research coverage, ticker details,
run summary JSON, Daily OI parent details, CLI output, and ticker logs now distinguish:

- `full_complete_chains`: mathematically full vendor-total coverage;
- `bounded_complete_chains`: valid Nightwatch-observable near-ATM bounded snapshots; and
- `true_incomplete_chains`: genuine blocking acquisition/integrity failures, excluding
  accepted expired-expiry 404 lifecycle conditions.

Bounded snapshots contribute to `complete_chains` because they are successful delivery
of the complete currently supported vendor product and are operationally accepted. They
do not contribute to `full_complete_chains`.

## 6. Ticker, parent, CLI, and observability behavior

A ticker containing only full-complete chains, complete-bounded snapshots, and accepted
`EXPIRED_EXPIRY_CHAIN_404` lifecycle conditions is operationally `COMPLETE`. A Daily
OI parent containing only accepted subjob states is also `COMPLETE`, and the CLI maps
that terminal state to exit 0.

Ticker logs expose full, bounded, and true-incomplete counts plus
`coverage_reasons`. `COMPLETE_BOUNDED_SNAPSHOT` is not logged as an incomplete or
failure reason. Raw payloads are not dumped.

Materialization timeouts, invalid responses or OI, duplicate contract identities, wrong
expiration/right/strike, unexpected row-count mismatch, active-expiry 404, HTTP errors,
budget/persistence/database failures, and other genuine failures remain fail-closed.

The accepted `EXPIRED_EXPIRY_CHAIN_404` behavior is unchanged and remains non-fatal to
an otherwise healthy ticker.

## 7. Research and Stage 9 compatibility

`COMPLETE_BOUNDED_SNAPSHOT != FULL_CHAIN`.

Future Stage 9 research can distinguish full-chain observations from bounded
observations through the persisted expiry status and JSON coverage metadata. Where
bounded snapshots exist, the archived contract universe must be described as the
Nightwatch-observable near-ATM bounded chain universe, never as all contracts in the
option chain.

Stage 9A and Stage 9B implementation, Research Sample identity, Forward Outcome
semantics, and eligibility code were not modified. Repository inspection confirmed that
Stage 9 does not consume Daily OI `complete_chains`, `incomplete_chains`, ticker
status, or chain reason codes.

The accepted cohort governance remains unchanged:

- canonical `scheduled_daily` production ProductCandidate occurrences can be primary
  research eligible subject to the existing Stage 9 contract; and
- manual, workflow-dispatch, diagnostic, remediation, and developer-rerun occurrences
  remain non-canonical research inputs.

Stage 9 was not implemented in this amendment and no Forward Outcome was computed.

## 8. Files changed

Application:

- `backend/app/cli.py`
- `backend/app/scanner/archive.py`
- `backend/app/scanner/config.py`
- `backend/app/scanner/daily.py`
- `backend/app/scanner/parsers.py`

Tests:

- `backend/tests/test_phase2a_daily_oi_remediation.py`

Evidence:

- `docs/evidence/PHASE2A_VENDOR_BOUNDED_CHAIN_SEMANTICS_AMENDMENT_20260827.md`

No migration was created. No Radar threshold, OI threshold, Candidate model/scoring,
Expiry Activity, Contract Persistence, ticker universe, schedule, API frequency, Stage
8, Trading Dashboard, Stage 9, Forward Outcome, or Dealer/GEX implementation was
changed.

## 9. Verification

All verification was offline:

- focused Phase 2A/archive compatibility suite: 42 passed;
- explicit Stage 9A/9B suite: 40 passed;
- complete backend suite: 460 passed;
- changed-file Ruff lint: passed;
- frontend ESLint: passed; and
- frontend production build and TypeScript checks: passed.

Focused regressions cover the confirmed 494/400 and 434/400 cases, explicit bounded
metadata, `truncated=false` behavior, full completion, sub-400 mismatch, invalid OI,
materialization timeout, accepted expired-404, mixed accepted ticker/parent completion,
full/bounded preservation, CLI exit codes, and the unchanged Radar full-chain gate.
The full backend suite includes the existing Candidate/scoring regressions.

## 10. Operations, migrations, and external contacts

- Nightwatch requests: 0
- Paid units: 0
- Manual workflow runs: 0
- Remote database writes: 0
- Remote schema writes: 0
- Historical production rows rewritten/backfilled: 0
- Migrations: 0
- Worktrees: 0
- Pull requests: 0

No Nightwatch URL or API endpoint was contacted. The only external URL contacted during
the task was the required Git remote
`https://github.com/lililinuk/options-anomaly-scanner.git` for `git fetch origin`
and the authorized final push. No GitHub Actions workflow was dispatched.

## 11. Residual limitations and next validation

Nightwatch does not expose the omitted contracts or a continuation mechanism, so a
bounded snapshot cannot be upgraded to a full chain by this acquisition path. Historical
rows retain their original semantics and are not backfilled.

The next validation is the next natural scheduled Phase 2A occurrence on canonical
`origin/main`. It should show operational `COMPLETE`/exit 0 when all paths are
accepted, with bounded coverage visible in metadata and logs. It must not be replaced by
a manual workflow-dispatch research occurrence.

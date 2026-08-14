# Phase 2B v1.2 — Dealer Heatmap Unavailable-State Resilience

Date context: 2026-08-14

Specification: `signal_spec_v1.2_phase2b`

Accepted implementation base: `e3748a52c5b43ff9692be53f36a0bbaad6c84818`

Calibration evidence commit present at task start: `8f90a3a4c53a59845124ca28b5304b8463f7edbd`

## Git / Safety

This is a narrow Phase 2B production-resilience amendment. It changes Dealer Heatmap
normalization, optional-layer orchestration semantics, candidate serialization, dashboard
unavailable presentation, version identity, tests, and documentation only. It changes no Phase 2A
source, database model, migration, financial threshold, score, ranking, Price calculation, IV
calculation, GEX interpretation, or direction rule. Phase 2B v2 setup states are not implemented.

## Root Cause

The Nightwatch transport already caught a Heatmap `NightwatchError`. The ticker context builder
then constructed a non-empty Dealer dict whose `cells` and `row_stacks` values were `NULL`.
`evaluate_heatmap()` treated the non-empty dict as evidence and directly ran list comprehensions
over both nullable values. Python raised `TypeError: 'NoneType' object is not iterable`.

That exception occurred after four successful context calls and before the service transaction
committed. The ticker context, candidate evaluations, raw success evidence, and later API-usage
persistence therefore rolled back together. The issue was not financial logic; it was a missing
normalization boundary between optional transport evidence and analytical evaluation.

## Normalization

`normalize_heatmap_payload()` now produces safe control-flow collections and an independent
analytical availability:

| Source shape | Analytical availability | Safe `cells` / `row_stacks` |
| --- | --- | --- |
| HTTP 400/error | `UNAVAILABLE` | `[]` / `[]` |
| Missing payload | `UNAVAILABLE` | `[]` / `[]` |
| Null, omitted, or non-list collection | `UNAVAILABLE` | `[]` / `[]` |
| Both collections are valid empty arrays | `AVAILABLE` | `[]` / `[]` |
| Valid vendor degraded surface | `AVAILABLE_DEGRADED` | Returned dict rows |
| Valid truncated surface | `INCOMPLETE_OR_TRUNCATED` | Returned dict rows |

The unavailable reason, source HTTP status, safe error code, request ID, endpoint/capability,
ticker, and UTC capture timestamp are retained in structured context/status evidence where the
source supplies them. Error messages, raw error details, Authorization headers, and credentials
are not persisted.

## Semantic States

Candidate cells now preserve three different meanings:

- `EXACT_MATCH`: usable surface and exact expiration/strike cell;
- `NOT_PRESENT`: usable surface inspected, exact cell absent;
- `UNAVAILABLE`: no usable surface.

Rows similarly use `ROW_EXACT_MATCH`, `ROW_NOT_PRESENT`, and `ROW_UNAVAILABLE`.

For `UNAVAILABLE`, candidate net/call/put GEX, row net/absolute GEX, and vendor row rank are all
`NULL`. A usable exact cell whose vendor GEX is numeric zero remains `EXACT_MATCH` with numeric
zero. It is not collapsed into either unavailable or not-present evidence.

## Transaction / Failure Isolation

Candidates are grouped by ticker before context acquisition. A refresh makes at most one Heatmap
request per ticker and shares its resulting state across every contract for that ticker.

A caught optional Heatmap failure is normalized before evaluation and therefore no longer raises
during candidate evaluation. Successful Price, Stock State, IV Rank, Term Structure, and
Positioning/Execution evidence commit with the candidate evaluation. The existing atomic service
transaction remains intact; unrelated database or evaluation failures still roll back normally.

Fresh v1.2 unavailable/degraded snapshots use the existing bounded freshness cache. This prevents
contract-count-driven duplicate failures without creating permanent negative caching. A later
freshness expiry or explicit forced refresh may try the vendor again.

Old v1.1 rows remain immutable. A v1.2 freshness lookup requires the v1.2 specification identity.
The explicit `--reuse-latest-raw` path may append a v1.2 normalized snapshot from preserved raw
evidence without a vendor request.

## API

The persisted candidate confirmation route returns HTTP 200 for the controlled unavailable
Dealer case. The TSLA read-back contained:

```text
Dealer availability       UNAVAILABLE
Candidate cell status     UNAVAILABLE
Candidate net/call/put    NULL / NULL / NULL
Row status                ROW_UNAVAILABLE
Row net/absolute/rank     NULL / NULL / NULL
Price                     AVAILABLE_WITH_GAPS
Stock State               AVAILABLE
Volatility                AVAILABLE
Execution                 AVAILABLE
Positioning               AVAILABLE
Direction                 UNRESOLVED
```

The browser still reads only the fixed Next.js proxy, which reads the FastAPI candidate route.
Neither browser component contacts Nightwatch.

## Dashboard

When Dealer context is unavailable, the candidate and all non-Dealer cards remain visible. The
Dealer card explicitly displays `Dealer/GEX：資料不可用`, `UNAVAILABLE`, and `ROW_UNAVAILABLE`.
It does not render a synthetic `0 GEX`.

## Tests

The deterministic tests cover:

- null, omitted, malformed, and empty collection shapes;
- HTTP 400 `VALIDATION_ERROR` normalization;
- unavailable versus usable `NOT_PRESENT` versus exact numeric zero;
- valid degraded Heatmap and exact candidate cell/row values;
- complete candidate evaluation with unavailable Dealer context;
- surviving Price, IV Rank/Term, Positioning, liquidity/Greeks, and unresolved direction;
- one Heatmap request for multiple same-ticker contracts;
- candidate API HTTP 200 serialization;
- dashboard unavailable wording and browser secret/direct-vendor guards.

Exact quality results:

- backend full suite: 194 passed;
- Ruff: passed;
- frontend ESLint: passed;
- glossary/null-safety/Dealer unavailable gate: passed, 109 documented fields;
- Next.js production build: passed;
- Phase 2A and Phase 2B v1/v1.1 regressions: included in the passing full backend suite;
- pytest emitted only the sandbox's optional cache-write permission warning.

## PostgreSQL / Alembic

- SQLAlchemy/Alembic runtime: PostgreSQL (`PostgresqlImpl`);
- Alembic current: `20260813_0009 (head)`;
- Alembic head: `20260813_0009`;
- migration/schema changes in this amendment: none;
- v1.2 TSLA ticker snapshot and candidate evaluation read-back: passed;
- in-process FastAPI route read-back from PostgreSQL: HTTP 200.

## Controlled Validation

Candidate: `TSLA260814C00335000`.

The explicit reprocessing path reused persisted v1.1 raw/context evidence. It appended one v1.2
ticker snapshot and one v1.2 candidate evaluation:

```text
ticker_snapshots_created       0
ticker_snapshots_reused        0
ticker_snapshots_reprocessed   1
evaluations                    1
network_attempts               0
paid_units                     0
```

The persisted original Heatmap endpoint evidence remains HTTP 400. Evaluation succeeded with the
Dealer/cell/row unavailable semantics listed above. No uncaught exception occurred and no numeric
zero was fabricated.

## Valid NVDA Regression

The accepted persisted NVDA degraded surface was evaluated with v1.2 normalization without a
vendor call:

| Field | Preserved value |
| --- | ---: |
| Availability | `AVAILABLE_DEGRADED` |
| Candidate cell | `EXACT_MATCH` |
| Candidate net GEX USD | 59,652,544 |
| Candidate call GEX USD | 59,166,863 |
| Candidate put GEX USD | 485,681 |
| Row status | `ROW_EXACT_MATCH` |
| Row net GEX USD | 81,553,764 |
| Row absolute GEX USD | 121,659,202 |
| Vendor row rank | 1 |

All values matched the accepted persisted candidate evaluation.

## Nightwatch Ledger / Quota

No Nightwatch endpoint was contacted during the controlled v1.2 validation.

| Endpoint | Calls | Paid units |
| --- | ---: | ---: |
| None | 0 | 0 |

- pre-validation quota remaining: 99,815;
- post-validation quota remaining: 99,815;
- network attempts: 0;
- paid units consumed: 0.

The HTTP 400 attached to the controlled TSLA row is reused persisted evidence from the prior
Calibration Gate, not a new request in this task.

## Security

- `.env` remains ignored;
- no local `DATABASE_URL` or Nightwatch key value is present in tracked files;
- neither secret is present in frontend tracked files;
- no Authorization header is persisted;
- browser code contains no direct Nightwatch request;
- only safe error/status metadata is persisted.

## Open Issues

The vendor `format=full` Heatmap request remains known to return HTTP 400 for AAPL, AMZN, GOOGL,
META, and TSLA under the previously validated runtime/account. v1.2 makes that state safe and
visible but does not resolve or reinterpret the vendor-side validation limitation. A later normal
refresh may re-probe after freshness expiry.

No blocker remains for the v1.2 resilience amendment. Phase 2B v2 setup states remain explicitly
out of scope.

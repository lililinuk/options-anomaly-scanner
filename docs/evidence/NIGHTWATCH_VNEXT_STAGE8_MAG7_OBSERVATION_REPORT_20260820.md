# Nightwatch Scanner vNext — Stage 8 MAG7 Observation Report

**Date:** 2026-08-20  
**Stage:** 8 — MAG7 Observation Period  
**Mode:** Read-only prerequisite assessment; observation stopped at runtime schema gate  
**Worktree:** `F:\options-anomaly-scanner-stage8`

## A. Result

```text
STAGE8_RESULT=HOLD_RUNTIME_PREREQUISITE
```

The already-configured runtime PostgreSQL database was reachable through a transaction explicitly
set to read-only. Its Alembic head was `20260815_0013`, not the required `20260818_0017` or a proven
compatible descendant. The four accepted Stage 5/6 runtime tables were absent. Per the execution
package, no application rows were queried after this prerequisite failure and no migration,
deployment, backfill, repair, live scan, or context refresh was attempted.

```text
STAGE8_RUNTIME_SCHEMA_READY=NO
RUNTIME_DEPLOYMENT_GATE_REQUIRED=YES
```

## B. Bootstrap

```text
STAGE7_ACCEPTED_COMMIT=3a63eaa1b9069d34199704fe31ac6466e8929d7d
STAGE8_BRANCH=vnext/stage8-mag7-observation
STAGE8_WORKTREE=F:\options-anomaly-scanner-stage8
STAGE8_BASE_HEAD=3a63eaa1b9069d34199704fe31ac6466e8929d7d
APPLICATION_CODE_CHANGES=0
```

The Stage 7 acceptance commit has parent
`d6cb38f5399dd3e30e8855f667ee16ef93a373e0`, the exact authorized subject
`vnext: accept stage7 candidate-first dashboard`, and 23 accepted paths. The Stage 7 worktree was
clean after the commit. No unrelated path was staged.

Accepted Stage 7 path set:

- Backend/API: `backend/app/api/routes/scans.py`, `backend/app/api/routes/system.py`,
  `backend/app/persistence/system_status.py`.
- Backend tests: `backend/tests/test_api.py`,
  `backend/tests/test_stage7_candidate_dashboard.py`.
- Frontend routes/helpers: `frontend/app/api/candidate-context/route.ts`,
  `frontend/app/api/candidate-context/proxy.ts`, `frontend/app/api/system-status/route.ts`,
  `frontend/app/api/system-status/proxy.ts`, `frontend/app/dashboard-semantics.ts`,
  `frontend/app/dashboard-types.ts`, `frontend/app/time-display.ts`.
- Frontend presentation: `frontend/app/field-guide/page.tsx`,
  `frontend/app/fieldGlossary.zh-TW.ts`, `frontend/app/globals.css`, `frontend/app/page.tsx`,
  `frontend/app/scan-dashboard.tsx`, `frontend/app/system-status-cards.tsx`.
- Frontend verification: `frontend/package.json`, `frontend/scripts/check-glossary.mjs`,
  `frontend/tests/mock-stage7-backend.mjs`, `frontend/tests/stage7-dashboard.test.mjs`.
- Evidence: `docs/evidence/NIGHTWATCH_VNEXT_STAGE7_CANDIDATE_FIRST_DASHBOARD_COMPLETION_REPORT_20260819.md`.

Stage 7 verification reproduced before commit:

```text
FULL_BACKEND=379/379 PASS
STAGE7_FRONTEND=13/13 PASS
GLOSSARY_SEMANTICS=34 CONCEPTS PASS
RUFF=PASS
TYPESCRIPT=PASS
FRONTEND_LINT=PASS
FRONTEND_BUILD=PASS
ALEMBIC_HEAD=20260818_0017 (single head)
```

The Stage 7 completion report in the worktree matched the canonical report byte-for-byte by
SHA-256: `CEADB5F382491C3D79982E87FF29FA6A2220F13479425BC777E4904CC2256FB5`.

## C. Governing evidence gate

All required and supporting files named by the opening prompt were present in
`F:\options-anomaly-scanner\docs\evidence` and were read completely. Every previously
manifested SHA-256 matched. The Stage 8 package, which the manifest historically labeled
`MISSING_SOURCE`, is now physically present and byte-identical to the uploaded source:

```text
STAGE8_PACKAGE_SHA256=C98DAD0D201393A9E9611D203402D1AD861F1CD640CBDECBA369E535CA24C9C2
MISSING_REQUIRED_GOVERNING_FILES=0
```

The manifest label is stale metadata rather than a current missing-file condition. The manifest
was not edited because Stage 8 authorizes only its own evidence directory after bootstrap.

## D. Repository orientation

```text
REPOSITORY_ORIENTATION
- Stage7 accepted diff: 23 accepted paths; 1,996 insertions and 642 deletions; acceptance commit 3a63eaa1b9069d34199704fe31ac6466e8929d7d.
- Stage7 dashboard candidate route: backend/app/api/routes/scans.py::GET /mag7/latest; frontend/app/api/mag7-scan/route.ts; frontend/app/scan-dashboard.tsx.
- ProductCandidate model/repository: backend/app/db/models.py::ProductCandidate; backend/app/scanner/candidate_persistence.py::load_product_candidate(s)_for_scan.
- ProductCandidateTrigger model/repository: backend/app/db/models.py::ProductCandidateTrigger; select-in trigger relationship and ordered reads in candidate_persistence.py.
- ProductCandidateContext model/repository: backend/app/db/models.py::ProductCandidateContext; backend/app/confirmation/vnext.py::load_context_history.
- AnomalyContextDetail model/repository: backend/app/db/models.py::AnomalyContextDetail; context/detail construction and reads in backend/app/confirmation/vnext.py.
- ScanRun market-date/status source: backend/app/db/models.py::ScanRun.market_date/status; successful completion/materialization in backend/app/scanner/v11.py; serialization in backend/app/api/routes/scans.py.
- daily collection health source: backend/app/db/models.py::DailyCollectionRun; backend/app/persistence/system_status.py::load_system_status.
- Dealer/GEX archive source: backend/app/db/models.py::DealerGexArchiveRun/DealerGexSnapshot; backend/app/dealer_archive/repository.py::best_archived_surface_at_or_before with vendor/capture cutoff bounds.
- quota metadata source: backend/app/db/models.py::ApiUsageAudit plus ScanRun/DailyCollectionRun/DealerGexArchiveRun consumption fields; backend/app/persistence/system_status.py.
- persistence analytics source: backend/app/db/models.py::ContractScanObservation persistent fields; backend/app/scanner/candidate_projection.py::persistent_public and accepted no-lookahead helpers.
- 0DTE status source: backend/app/db/models.py::ZeroDteActivitySessionSnapshot; backend/app/api/routes/scans.py::_zero_dte_public; canonical writes in backend/app/scanner/daily.py.
- Stage6 request/provenance telemetry: ProductCandidateContext/AnomalyContextDetail provenance JSON; backend/app/confirmation/vnext.py including chain_source_request_id; ApiUsageAudit for authoritative request/quota facts where present.
- rollover experiment evidence location: docs/evidence/OI_CHANGE_ROLLOVER_TIMING_EXPERIMENT_DEPLOYMENT_20260817.md; backend/app/research/oi_change_rollover.py.
- Alembic head: repository 20260818_0017; migration backend/alembic/versions/20260818_0017_stage6_balanced_context.py, down-revision 20260818_0016.
```

## E. Stage 8 evidence query plan

Only the first prerequisite query group was executed. Every query was or would be a `SELECT`
inside a transaction beginning with `SET TRANSACTION READ ONLY`; the executed transaction was
rolled back and disposed.

| Query/view | Metric supported | Why read-only | Execution state |
|---|---|---|---|
| `alembic_version`; `to_regclass` for four required tables | Runtime schema prerequisite | Metadata `SELECT` only in read-only transaction | EXECUTED; gate failed |
| `scan_runs` joined to `product_candidates` | Window, run state, O1, O6 | Aggregate `SELECT`; no ORM materializer/API call | NOT_EXECUTED_RUNTIME_GATE |
| `product_candidate_triggers` grouped by candidate/family/entity/qualification | O2 and O3 | Aggregate `SELECT` only | NOT_EXECUTED_RUNTIME_GATE |
| `contract_scan_observations` joined through persisted trigger source IDs | O4 persistence maturation | Historical fields read without recomputation or writes | NOT_EXECUTED_RUNTIME_GATE |
| baseline `product_candidate_contexts` plus `anomaly_context_details` | O5, O9, lag, cutoff/trigger integrity | Reads stored states/provenance only | NOT_EXECUTED_RUNTIME_GATE |
| context/detail provenance and chain source identities | O7 source-identity sharing and telemetry availability | Read persisted identifiers only; no loader invocation | NOT_EXECUTED_RUNTIME_GATE |
| refresh contexts plus `api_usage_audits` and authoritative request metadata | O8 refresh/request/quota facts | Stored telemetry `SELECT`; no refresh | NOT_EXECUTED_RUNTIME_GATE |
| candidate/trigger/context identity joins and baseline-vs-refresh comparison | First-knowledge, mutation, trigger-set, budget integrity | Referential/JSON comparison from preserved rows only | NOT_EXECUTED_RUNTIME_GATE |
| 0DTE session snapshots and stored maturity fields | 0DTE states/count/maturity/fallback | Stored-state `SELECT`; no canonical recomputation | NOT_EXECUTED_RUNTIME_GATE |
| daily collection and Dealer/GEX archive runs/snapshots | Operational health | Stored run/archive metadata `SELECT` only | NOT_EXECUTED_RUNTIME_GATE |

No old pre-vNext application rows were queried or relabeled as Stage 8 samples.

## F. Runtime prerequisite

```text
RUNTIME_DB_REACHABLE=YES
RUNTIME_DB_SCHEMA_HEAD=20260815_0013
RUNTIME_PRODUCT_CANDIDATE_TABLE_PRESENT=NO
RUNTIME_PRODUCT_CANDIDATE_TRIGGER_TABLE_PRESENT=NO
RUNTIME_PRODUCT_CANDIDATE_CONTEXT_TABLE_PRESENT=NO
RUNTIME_ANOMALY_CONTEXT_DETAIL_TABLE_PRESENT=NO
STAGE8_RUNTIME_SCHEMA_READY=NO
RUNTIME_DEPLOYMENT_GATE_REQUIRED=YES
```

Repository code expects the accepted single head `20260818_0017`. Stage 8 does not authorize an
`alembic upgrade`, deployment, schema write, or historical backfill, so no compatibility claim can
be made for runtime `20260815_0013`.

## G. Observation window

```text
OBSERVATION_FIRST_MARKET_DATE=NOT_ANALYZED_RUNTIME_PREREQUISITE
OBSERVATION_LAST_MARKET_DATE=NOT_ANALYZED_RUNTIME_PREREQUISITE
OBSERVED_COMPLETED_MARKET_DATES=NOT_ANALYZED_RUNTIME_PREREQUISITE
OBSERVED_SUCCESSFUL_SCAN_RUNS=NOT_ANALYZED_RUNTIME_PREREQUISITE
OBSERVED_FAILED_SCAN_RUNS=NOT_ANALYZED_RUNTIME_PREREQUISITE
OBSERVED_PRODUCT_CANDIDATE_OCCURRENCES=NOT_ANALYZED_RUNTIME_PREREQUISITE
OBSERVED_DISTINCT_CANDIDATE_DAYS=NOT_ANALYZED_RUNTIME_PREREQUISITE
```

## H. O1 — Candidates/day

```text
O1_CANDIDATES_PER_DAY=NOT_OBSERVED_RUNTIME_PREREQUISITE
```

No daily table or descriptive distribution was produced because the required candidate table is
absent. Pre-vNext scan rows were not used as substitutes.

## I. O2 — Anomalies/candidate

```text
O2_ANOMALIES_PER_CANDIDATE=NOT_OBSERVED_RUNTIME_PREREQUISITE
```

No occurrence table, trigger distribution, or min/median/max was calculated.

## J. O3 — Route frequencies

```text
O3_ROUTE_FREQUENCIES=NOT_OBSERVED_RUNTIME_PREREQUISITE
```

No legacy routes were mixed into the active-family sample and no multi-route interpretation was
made.

## K. O4 — Persistence maturation

```text
PERSISTENCE_MATURATION_OBSERVED=NO
PERSISTENCE_MATURATION_REASON=RUNTIME_PREREQUISITE_NOT_MET
CURRENT_TRIGGER_FRESHNESS_MODE=CALIBRATION_REQUIRED
```

No freshness window or missing-observation value was invented.

## L. O5 — Context availability

```text
CANDIDATES_WITH_BASELINE=NOT_ANALYZED_RUNTIME_PREREQUISITE
CANDIDATES_WITHOUT_BASELINE=NOT_ANALYZED_RUNTIME_PREREQUISITE
BASELINE_EXISTENCE_RATE=NOT_ANALYZED_RUNTIME_PREREQUISITE
B1_B5_AVAILABILITY_MATRIX=NOT_OBSERVED_RUNTIME_PREREQUISITE
```

No composite context score was created.

## M. O6 — Ticker concentration

```text
O6_TICKER_CONCENTRATION=NOT_OBSERVED_RUNTIME_PREREQUISITE
```

No threshold, bias label, or universe expansion was introduced.

## N. O7 — Chain reuse

```text
CHAIN_REUSE_TELEMETRY_AVAILABLE=NOT_EVALUATED_RUNTIME_PREREQUISITE
CHAIN_SOURCE_IDENTITY_REUSE_OBSERVED=NOT_EVALUATED_RUNTIME_PREREQUISITE
CHAIN_REUSE_RATE=UNRESOLVED_CURRENT_TELEMETRY
```

Repository architecture and fake-test results were not converted into a real runtime reuse rate.

## O. O8 — Phase 2B API cost

```text
PHASE2B_REFRESH_COST_OBSERVED=NO
OBSERVED_REFRESH_COUNT=NOT_ANALYZED_RUNTIME_PREREQUISITE
OBSERVED_VENDOR_REQUESTS=NOT_ANALYZED_RUNTIME_PREREQUISITE
OBSERVED_PAID_UNITS=NOT_ANALYZED_RUNTIME_PREREQUISITE
PER_ANOMALY_VENDOR_CALLS=NOT_ANALYZED_RUNTIME_PREREQUISITE
DEALER_HEATMAP_CALLS=NOT_ANALYZED_RUNTIME_PREREQUISITE
```

The accepted architecture remains up to four ticker-level refresh calls, zero per-anomaly calls,
and archive-only Dealer/GEX, but those design properties are not reported as observed cost.

## P. O9 — Freshness failures

```text
O9_FRESHNESS_FAILURE_RATE=NOT_OBSERVED_RUNTIME_PREREQUISITE
```

No state counts/rates or IV Rank trading interpretation was produced.

## Q. Baseline lag and integrity

```text
BASELINE_CREATION_LAG_OBSERVED=NO
OBSERVED_BASELINE_LOOKAHEAD_FOUND=NOT_EVALUATED_RUNTIME_PREREQUISITE
OBSERVED_BASELINE_MUTATION_FOUND=NOT_EVALUATED_RUNTIME_PREREQUISITE
OBSERVED_TRIGGER_SET_DRIFT_FOUND=NOT_EVALUATED_RUNTIME_PREREQUISITE
```

The absence of an observed `YES` is not reported as a clean integrity result. No baseline sample
existed in the runtime schema to inspect.

## R. Candidate/budget integrity

```text
OBSERVED_VALID_CANDIDATE_OMISSION_FOUND=NOT_EVALUATED_RUNTIME_PREREQUISITE
OBSERVED_DEEP_DIVE_BUDGET_SUPPRESSION_FOUND=NOT_EVALUATED_RUNTIME_PREREQUISITE
```

Repository fixture proof was not substituted for real Stage 8 observation.

## S. Operational/run state and 0DTE

```text
RUN_STATE_COUNTS=NOT_OBSERVED_RUNTIME_PREREQUISITE
DAILY_COLLECTION_HEALTH=NOT_OBSERVED_RUNTIME_PREREQUISITE
DEALER_GEX_ARCHIVE_AGE=NOT_OBSERVED_RUNTIME_PREREQUISITE
QUOTA_FACTS=NOT_OBSERVED_RUNTIME_PREREQUISITE
RADAR_OI_COLLECTION_STATE=NOT_OBSERVED_RUNTIME_PREREQUISITE

ZERO_DTE_PROVISIONAL_INTRADAY=NOT_OBSERVED_RUNTIME_PREREQUISITE
ZERO_DTE_CANONICAL_SESSION_COMPLETE=NOT_OBSERVED_RUNTIME_PREREQUISITE
ZERO_DTE_LEGACY_OR_AMBIGUOUS=NOT_OBSERVED_RUNTIME_PREREQUISITE
ZERO_DTE_HISTORY_MATURITY=NOT_OBSERVED_RUNTIME_PREREQUISITE
ZERO_DTE_FALLBACK_STATUS=NOT_OBSERVED_RUNTIME_PREREQUISITE
```

```text
ROLLOVER_EVIDENCE_AVAILABLE=YES
RADAR_OI_SCHEDULE_ACTIVATION=PENDING_ROLLOVER_EVIDENCE
```

The existing rollover deployment/evidence artifact was located read-only. No scheduling decision
was inferred and no workflow was dispatched.

## T. Carried ledger

All six carried items remain explicit and unchanged:

```text
CURRENT_TRIGGER_FRESHNESS_MODE=CALIBRATION_REQUIRED
RADAR_OI_SCHEDULE_ACTIVATION=PENDING_ROLLOVER_EVIDENCE
CROSS_RUN_CANDIDATE_LIFECYCLE=DEFERRED_NO_AUTO_MERGE
IV_RANK_CORE_ELIGIBILITY=WITHHOLD_PENDING_PROVENANCE
ISOLATED_POSTGRES_RUNTIME_VERIFIED=NO
N1_HISTORICAL_RUNTIME_DISTRIBUTION_VERIFIED=NO
```

The reachable configured database is a remote runtime and does not satisfy the carried isolated
PostgreSQL verification gate.

## U. New observations / defects

### Finding 1 — Runtime schema prerequisite not deployed

```text
finding=Configured runtime is at Alembic 20260815_0013 and lacks all four accepted vNext tables.
evidence=Read-only alembic_version and to_regclass prerequisite queries.
severity=BLOCKING_STAGE8_OBSERVATION
blocking Stage9? YES
requires remediation? YES, UNDER A SEPARATE DEPLOYMENT/MIGRATION AUTHORIZATION
```

No remediation was attempted. This finding does not assert that the repository migration is
defective; it records only that the configured runtime has not met the accepted deployment
prerequisite.

## V. Forward Outcome boundary

No Forward Outcome or later-price calculation was performed:

```text
T_PLUS_RETURNS_CALCULATED=NO
MFE_CALCULATED=NO
MAE_CALCULATED=NO
FUTURE_PRICE_PATH_CALCULATED=NO
ACTIONABILITY_CALCULATED=NO
```

## W. Authorization ledger

```text
APPLICATION_CODE_CHANGES=0
TEST_CODE_CHANGES=0
MIGRATION_CREATED=0
REMOTE_MIGRATIONS_RUN=0
REMOTE_DB_WRITES=0
WORKFLOWS_DISPATCHED=0

NIGHTWATCH_REQUESTS=0
PAID_UNITS=0

STAGE7_ACCEPTED_COMMITS_CREATED=1
STAGE8_IMPLEMENTATION_COMMITS_CREATED=0

PUSHES=0
PRS_CREATED=0
MERGES=0
```

External endpoint contacted:

```text
EXTERNAL_URLS_OR_API_ENDPOINTS_CONTACTED=[
  "postgresql://aws-0-ap-northeast-1.pooler.supabase.com:5432/postgres (schema prerequisite SELECTs only; username/password omitted)"
]
```

No HTTP(S) URL, Nightwatch endpoint, registry, GitHub API, workflow endpoint, or other external
service was contacted. Local npm verification used only the pre-existing offline cache.

## X. Stage 9 readiness

```text
STAGE9_READY=NO
NEXT_AUTHORIZED_STAGE=NONE
```

Reason: there is no runtime-deployed Stage 5/6 schema and therefore no genuine vNext
`ProductCandidate` plus frozen `FIRST_KNOWLEDGE_BASELINE` sample whose real integrity can be
observed. Stage 9 was not started.

STOP.

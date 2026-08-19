# Nightwatch Scanner vNext — Stage 6 Phase 2B Balanced Model Completion Report

**Date:** 2026-08-19
**Stage:** 6 — Phase 2B Balanced Product-Candidate Context Model
**Worktree:** `F:\options-anomaly-scanner-stage6`

## A. Result

```text
STAGE6_RESULT=PASS_WITH_CARRIED_ITEMS
```

Stage 6 adds one candidate-first, non-directional context evaluation layer with shared ticker
context and one immutable detail per persisted Stage 5 trigger. It adds no Phase 2A eligibility
logic, score, trade/action label, Forward Outcome input, scheduler, workflow, frontend redesign,
or live Dealer/GEX request.

## B. Bootstrap

```text
STAGE5_ACCEPTED_COMMIT=f441c64ba4422dad73fd04c29ba01172c37881bc
STAGE6_BRANCH=vnext/stage6-phase2b-balanced
STAGE6_WORKTREE=F:\options-anomaly-scanner-stage6
STAGE6_BASE_HEAD=f441c64ba4422dad73fd04c29ba01172c37881bc
WORKTREE_CLEAN_AT_STAGE6_START=NO
ALEMBIC_HEAD_BEFORE=20260818_0016
```

The Stage 5 acceptance commit was already present when this execution began. It has parent
`84b27b46311c35006def006621fe534b96c690d1`, message
`vnext: accept stage5 product candidate persistence`, and exactly the eight accepted Stage 5
paths. No duplicate Stage 5 commit was created. The Stage 6 worktree already contained
uncommitted partial additions in `backend/app/db/models.py` and
`backend/app/confirmation/vnext.py`; they were preserved, audited, completed, and remain
uncommitted.

## C. Repository orientation

- Stage 5 candidate/trigger read: `scanner/candidate_persistence.py::load_product_candidate` and
  the select-in `ProductCandidate.triggers` relationship.
- First-knowledge anchor: immutable `ProductCandidate.candidate_first_knowledge_at`, set from the
  successful `ScanRun.completed_at` cutoff in the Stage 5 materialization transaction.
- Stage 3 support: `EvaluationIdentity`, `CandidateFirstKnowledge`, and explicit
  source/vendor/local time provenance in `confirmation/provenance.py`.
- Legacy Phase 2B write/read: `confirmation/service.py`, `state_v2.py`, and `workspace_v3.py`;
  their models/tables remain intact and the new service does not write them.
- Price: existing canonical regular-session `calculate_price_context` logic is reused unchanged.
- Stock state: existing `normalize_stock_state` is reused.
- IV Rank: ticker-level raw value/provenance only; vendor semantics remain unverified.
- Term structure: one shared ticker payload supplies all expiry nodes and topology.
- Chain: `ContractOiDailySnapshot`, queried once per ticker-expiry with receipt/vendor/quote
  no-lookahead bounds.
- Dealer/GEX: `best_archived_surface_at_or_before`, which requires both vendor-observed and local
  capture times at or before the evaluation cutoff.
- Deep Dive: shared Stage 4 helpers; structure must be positive/accepted and clusters must be
  `VALID_CLUSTER` or `STRONG_CLUSTER`.
- API: candidate-id routes under `/api/v1/product-candidates/{candidate_id}/context`.
- Migration predecessor: `20260818_0016`.

## D. Core entities

```text
PRODUCT_CANDIDATE_CONTEXT_PERSISTED=YES
ANOMALY_CONTEXT_DETAIL_PERSISTED=YES
ONE_EVALUATION_LAYER_VERIFIED=YES
OLD_PHASE2B_LAYERS_PRESERVED_READ_ONLY=YES
```

`ProductCandidateContext` owns shared B1/B2/B3/B5 JSON blocks and explicit identity/time fields.
`AnomalyContextDetail` binds the evaluation to each authoritative Stage 5 trigger and owns B4,
expiry overlays, Deep-Dive references, availability, and provenance. Database constraints enforce
the baseline identity, evaluation time ordering, context+trigger uniqueness, and contract/expiry
payload separation.

## E. Evaluation identity

```text
FIRST_KNOWLEDGE_BASELINE_IMPLEMENTED=YES
REFRESH_IMPLEMENTED=YES
BASELINE_MUTATED_BY_REFRESH=NO
BASELINE_DETAIL_MUTATED_BY_REFRESH=NO
```

The baseline service reuses the same persisted baseline only when its exact trigger-id set still
matches. A mismatch fails closed. Refresh always creates a new context/detail set. The focused
proof serializes the baseline before and after refresh and obtains byte-identical JSON.

## F. Entry path

```text
PRODUCT_CANDIDATE_ENTRYPOINT=YES
RADAR_ONLY_SUPPORTED=YES
EXPIRY_ACTIVITY_ONLY_SUPPORTED=YES
PERSISTENCE_ONLY_SUPPORTED_WHEN_CURRENT_ELIGIBLE=YES
MIXED_TRIGGER_SUPPORTED=YES
RADAR_ONLY_GATE_REMAINS_IN_VNEXT=NO
```

The evaluator starts from `ProductCandidate.id` and the full persisted trigger list. Parameterized
tests exercise all four entry shapes without consulting the legacy exact-contract Radar gate.

## G. Balanced blocks

```text
B1_PRICE_CONTEXT=PASS
B2_VOLATILITY_CONTEXT=PASS
B3_DEALER_GEX_CONTEXT=PASS
B4_ANOMALY_CONTEXT=PASS
B5_PROVENANCE_AVAILABILITY=PASS
```

- B1 preserves canonical close, 1/5/20-observation returns, SMA20/50, ATR14, optional range/trend,
  and coverage/gap facts. Missing fields remain null.
- B2 derives candidate-expiry IV/topology from one shared term payload and contract IV from chain
  reuse. IV Rank is raw and withheld from core eligibility.
- B3 uses the accepted versioned raw-node rules against the time-eligible archive only. Decimal
  strike identity replaces raw float equality; invalid/missing strikes are discarded.
- B4 contract detail contains identity, anchored DTE, strike location, IV, Delta, bid/ask/spread,
  and quote time. Expiry detail contains only expiry activity and shared expiry overlays.
- B5 persists separate time identities, source ids, rule/config version/hash, and independent
  layer availability states.

## H. Cost/reuse

```text
CONFIGURED_SOURCE_CONTRACT=4
MAX_TICKER_SOURCE_CALLS_IN_FAKE_REFRESH=4
PER_ANOMALY_VENDOR_CALLS=0
STAGE6_DEALER_HEATMAP_CALLS=0
CHAIN_CONTEXT_REUSED_PER_TICKER_EXPIRY=YES
```

The fake-client proof uses a mixed candidate with three anomalies and observes exactly one request
for each configured ticker source: `daily_ohlc`, `stock_state`, `iv_rank`, and `term_structure`.
No per-contract endpoint or Dealer/GEX heatmap endpoint is present in the Stage 6 source contract.

## I. IV Rank

```text
IV_RANK_ENTITY=TICKER
IV_RANK_VENDOR_SEMANTICS=UNVERIFIED
IV_RANK_CORE_ELIGIBILITY=WITHHOLD_PENDING_PROVENANCE
IV_RANK_CLASSIFICATION_INTRODUCED=NO
```

## J. GEX / G16 / G17 / G18

```text
DEALER_GEX_ARCHIVE_ONLY=YES
INVALID_CLUSTER_POSITIVE_LEAK=NO
SUBTHRESHOLD_STRUCTURE_POSITIVE_LEAK=NO
STABILIZATION_BIAS_ACTIVE=NO
DOWNSIDE_ACCELERATION_RISK_ACTIVE=NO
MISSING_STRIKE_DISTANCE_ZERO_FOUND=NO
RAW_FLOAT_STRIKE_EQUALITY_USED=NO
```

The raw Primary Floor, Primary Upper Positive-GEX Node, and Immediate Below-Floor Node are retained
with rule-version audit metadata. No replacement directional label is generated.

## K. Option-detail boundaries

```text
EXPIRY_TRIGGER_FABRICATES_CONTRACT=NO
GAMMA_IN_PHASE2B_CORE=NO
THETA_IN_PHASE2B_CORE=NO
VEGA_IN_PHASE2B_CORE=NO
EXECUTION_SCORE_INTRODUCED=NO
```

## L. Time / no-lookahead

```text
CONTEXT_TIME_IDENTITIES_SEPARATE=YES
POST_CONTEXT_EVALUATION_EVIDENCE_CAN_ENTER_BASELINE=NO
VENDOR_TIME_FALLS_BACK_TO_LOCAL=NO
CREATED_AT_CAN_LAUNDER_FRESHNESS=NO
```

Baseline raw evidence requires local receipt at or before `context_evaluated_at`; a known vendor
observation must also be at or before the cutoff. Chain reuse independently bounds vendor OI time,
raw receipt, and quote time. Dealer archive selection independently bounds vendor and capture time.
Unknown vendor time remains null.

## M. Availability

```text
PER_LAYER_AVAILABILITY_PRESERVED=YES
COMPOSITE_CONTEXT_READINESS_PRESENT=NO
MISSING_CONTEXT_ZERO_FILLED=NO
```

The only active layer states are `AVAILABLE`, `PARTIAL`, `UNAVAILABLE`, and
`NOT_YET_AVAILABLE`. IV Rank core eligibility is preserved separately from data availability.

## N. API/backend contract

- `GET /api/v1/product-candidates/{candidate_id}/context` reads baseline and refresh history only.
- `POST /api/v1/product-candidates/{candidate_id}/context/baseline` freezes already-known/archive
  evidence and performs no vendor request.
- `POST /api/v1/product-candidates/{candidate_id}/context/refresh` is the explicit four-source
  ticker refresh; writes are committed only after the context and all details are complete.
- Missing candidate returns 404; a conflicting baseline replay returns 409.

Repeated GET proof records zero session writes and returns `NOT_YET_AVAILABLE` when no baseline
exists.

## O. Migration

```text
MIGRATION_CREATED=YES
ALEMBIC_HEAD=20260818_0017
ALEMBIC_SINGLE_HEAD=YES
HISTORICAL_BACKFILL_PERFORMED=NO
OLD_PHASE2B_TABLE_DROPPED=NO
ISOLATED_POSTGRES_RUNTIME_VERIFIED=NO
REMOTE_MIGRATION_RUN=NO
```

Migration `20260818_0017` creates only `product_candidate_contexts` and
`anomaly_context_details`, their FKs/checks/indexes, and the partial unique baseline index. It has
no application-data DML or historical backfill. Alembic version-table DML in generated offline SQL
is migration bookkeeping only. Offline PostgreSQL upgrade and downgrade SQL generation passed.

## P. Stage boundaries

```text
PHASE2A_SCORING_CHANGED=NO
DASHBOARD_STAGE7_STARTED=NO
FORWARD_OUTCOME_STARTED=NO
ACTIONABILITY_STARTED=NO
TRADE_EXPRESSION_STARTED=NO
```

## Q. N1 proof status

```text
N1_CODE_PATH_CONFIRMED=YES
N1_HISTORICAL_RUNTIME_DISTRIBUTION_VERIFIED=NO
```

No remote database proof was authorized or attempted.

## R. Carried items

```text
CURRENT_TRIGGER_FRESHNESS_MODE=CALIBRATION_REQUIRED
RADAR_OI_SCHEDULE_ACTIVATION=PENDING_ROLLOVER_EVIDENCE
CROSS_RUN_CANDIDATE_LIFECYCLE=DEFERRED_NO_AUTO_MERGE
IV_RANK_CORE_ELIGIBILITY=WITHHOLD_PENDING_PROVENANCE
ISOLATED_POSTGRES_RUNTIME_VERIFIED=NO
N1_HISTORICAL_RUNTIME_DISTRIBUTION_VERIFIED=NO
```

Destinations remain the founder calibration gate, rollover evidence gate, future lifecycle design
gate, IV Rank provenance proof, pre-remote-deployment isolated PostgreSQL gate, and later
DB-capable N1 evidence gate respectively. None was resolved by invention.

## S. Tests and static verification

- `python -B -m pytest tests/test_stage6_balanced_context.py -p no:cacheprovider` — passed,
  20 tests.
- Stage 5/4A/4B/3 plus legacy Phase 2B focused command — passed, 133 tests.
- `python -B -m pytest -p no:cacheprovider` — passed, 369 tests.
- `python -B -m ruff check --no-cache .` — passed.
- `python -B -m alembic heads` — passed, one head: `20260818_0017`.
- Offline PostgreSQL upgrade through `20260818_0017` — passed.
- Offline PostgreSQL downgrade `20260818_0017:20260818_0016` — passed.
- `npm run test:glossary` — passed: 39 legacy columns, 128 documented fields, null/expiry safety.
- `npm run lint` — passed.
- `npm run build` — passed, including TypeScript and static page generation.
- `git diff --check` — passed.

Frontend dependencies were installed with `npm ci --offline --ignore-scripts`, using only the
pre-existing local npm cache. Temporary `frontend/node_modules` and `frontend/.next` directories
were removed after verification.

## T. Diff

```text
FILES_CHANGED=7
LINES_ADDED=2639
LINES_REMOVED=1
MIGRATION_FILES=1
WORKFLOW_FILES=0
FRONTEND_FILES=0
```

Changed paths:

- `backend/app/db/models.py`
- `backend/alembic/versions/20260818_0017_stage6_balanced_context.py`
- `backend/app/confirmation/vnext.py`
- `backend/app/api/routes/candidate_contexts.py`
- `backend/app/api/router.py`
- `backend/tests/test_stage6_balanced_context.py`
- this report

## U. Authorization ledger

```text
NIGHTWATCH_REQUESTS=0
PAID_UNITS=0
REMOTE_DB_WRITES=0
REMOTE_MIGRATIONS_RUN=0
WORKFLOWS_DISPATCHED=0
STAGE5_ACCEPTED_COMMITS_CREATED=1
STAGE6_IMPLEMENTATION_COMMITS_CREATED=0
COMMITS_CREATED_THIS_EXECUTION=0
PUSHES=0
PRS_CREATED=0
MERGES=0
EXTERNAL_URLS_OR_API_ENDPOINTS_CONTACTED=[]
```

The four Nightwatch route templates exist only as the approved future explicit-refresh contract;
none was contacted. No registry, remote database, GitHub, or other external endpoint was contacted.

## V. Next-stage readiness

```text
STAGE7_READY=YES
NEXT_AUTHORIZED_STAGE=NONE
```

Stage 7 was not started. No further stage is authorized by this package.

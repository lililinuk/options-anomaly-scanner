# Nightwatch Scanner vNext — Stage 6 Phase 2B Balanced Model — Codex Execution Package

**Date:** 2026-08-18  
**Stage:** 6 — PHASE 2B vNext / BALANCED PRODUCT-CANDIDATE CONTEXT MODEL  
**Executor:** Codex implementation engineer  
**Authorization:** Stage 6 only  
**Accepted predecessor:** Stage 5 `CLOSED / ACCEPTED` with `PASS_WITH_CARRIED_ITEMS`  
**Accepted Stage 5 worktree:** `F:\options-anomaly-scanner-stage5`  
**Stage 5 branch:** `vnext/stage5-product-candidate-persistence`  
**Current pre-commit HEAD:** `84b27b46311c35006def006621fe534b96c690d1`  
**Expected Stage 6 branch:** `vnext/stage6-phase2b-balanced`  
**Preferred Stage 6 worktree:** `F:\options-anomaly-scanner-stage6`

---

# 0. Objective

Implement the Founder-approved **Phase 2B vNext — Balanced Product-Candidate Context Model** on top of persisted Stage 5 `ProductCandidate` / `ProductCandidateTrigger`.

Phase 2B's only job is to provide a time-correct, non-directional, minimum-sufficient market-context snapshot for each Product/Ticker Candidate — shared once at ticker level and detailed only where anomaly-specific — so later Forward Outcome research can understand the candidate without Phase 2B deciding whether or how to trade.

Target entity layer:

```text
ProductCandidate
    ↓
ProductCandidateContext          ticker-level shared context
    └── AnomalyContextDetail     one per referenced contract/expiry trigger
```

The old Phase 2B v1.2 → v2.0 → v3.1 stack remains historical/read-only data. Stage 6 does not extend that stack as the active model.

---

# 1. Accepted Predecessor State

Stage 5 is accepted with these required invariants:

```text
PRODUCT_CANDIDATE_PERSISTED=YES
PRODUCT_CANDIDATE_TRIGGER_PERSISTED=YES
CANDIDATE_FIRST_KNOWLEDGE_PHYSICAL=YES

CANDIDATE_FIRST_KNOWLEDGE_CUTOFF_VERIFIED=YES
POST_CUTOFF_EVIDENCE_CAN_ENTER_FIRST_KNOWLEDGE_SET=NO

STAGE5_MATERIALIZATION_ATOMIC=YES
PARTIAL_CANDIDATE_STATE_CAN_SURVIVE_FAILURE=NO

ZERO_CANDIDATE_OCCURRENCE_FREEZE_VERIFIED=YES
OLD_ZERO_CANDIDATE_RUN_CAN_REBUILD_FROM_FUTURE_STATE=NO

TRIGGER_LOGICAL_DUPLICATION_FOUND=NO
TRIGGER_OVER_DEDUPLICATION_FOUND=NO

FIRST_KNOWLEDGE_TRIGGER_SET_IMMUTABLE=YES
LATER_TRIGGER_CAN_BECOME_RETROACTIVE_FIRST_KNOWLEDGE=NO

ALEMBIC_HEAD=20260818_0016
ALEMBIC_SINGLE_HEAD=YES
```

Accepted candidate occurrence identity:

```text
ScanRun.id
+ ticker
+ phase2a_vnext_stage4b.product-candidate-materialization.v1
```

Preserve:

```text
CROSS_RUN_CANDIDATE_LIFECYCLE=DEFERRED_NO_AUTO_MERGE
```

---

# 2. Stage 6 Bootstrap — Freeze Stage 5 Without Another Review Loop

Stage 5 changes are accepted but remain uncommitted. This package authorizes one local Stage 5 accepted commit solely to create a stable Stage 6 base.

Inside `F:\options-anomaly-scanner-stage5`, verify the worktree still matches the accepted Stage 5 completion/final-closeout state. Expected accepted Stage 5 paths:

```text
backend/app/db/models.py
backend/alembic/versions/20260818_0016_stage5_product_candidate_persistence.py
backend/app/scanner/candidate_projection.py
backend/app/scanner/candidate_persistence.py
backend/app/scanner/v11.py
backend/app/api/routes/scans.py
backend/tests/test_stage5_product_candidate_persistence.py
docs/evidence/NIGHTWATCH_VNEXT_STAGE5_PRODUCT_CANDIDATE_PERSISTENCE_COMPLETION_REPORT_20260818.md
```

If the report path differs, verify against the accepted Stage 5 evidence and report the exact accepted set.

Stage only accepted Stage 5 paths. Do not use `git add .`, `git add -A`, or `git commit -a`.

Authorized local commit message:

```text
vnext: accept stage5 product candidate persistence
```

Record:

```text
STAGE5_ACCEPTED_COMMIT=<sha>
```

Then create from exactly that commit:

```text
branch   = vnext/stage6-phase2b-balanced
worktree = F:\options-anomaly-scanner-stage6
```

This is not another Stage 5 review. Do not push, PR, or merge.

---

# 3. Governing Documents

Read completely before editing:

1. `NIGHTWATCH_SCANNER_VNEXT_INTEGRATED_SPEC_PROMPT_20260817(1).md`
2. `NIGHTWATCH_VNEXT_STAGE1_READONLY_PROOF_GATE_REPORT_20260817.md`
3. `NIGHTWATCH_VNEXT_STAGE3_TIME_KNOWLEDGE_INTEGRITY_CODEX_EXECUTION_PACKAGE_20260817.md`
4. `NIGHTWATCH_VNEXT_STAGE5_PRODUCT_CANDIDATE_PERSISTENCE_CODEX_EXECUTION_PACKAGE_20260818.md`
5. `NIGHTWATCH_VNEXT_STAGE5_PRODUCT_CANDIDATE_PERSISTENCE_COMPLETION_REPORT_20260818.md`
6. Founder-provided Stage 5 final read-only closeout
7. this Stage 6 Execution Package.

Authority order:

```text
Founder-approved Integrated Spec
> this Stage 6 package
> accepted Stage 5 state
> accepted Stage 3 time/knowledge foundation
> Stage 1 proof findings
> current repository implementation detail
> older reviews/handoffs
```

If repository detail conflicts with approved semantics, STOP rather than silently redesign.

---

# 4. Semantic Red Lines

Preserve:

```text
missing ≠ zero
Call ≠ bullish
Put ≠ bearish
OI increase ≠ bought-to-open
positive/negative GEX ≠ market direction
UNRESOLVED ≠ Neutral
PERSISTENT_BUILD / DECLINE ≠ trade direction
no universal anomaly/ticker/conviction score
no Phase 2B composite score
no BUY / SELL
no Actionability labels
no rewriting accepted historical evidence
UTC persistence · NY market-calendar semantics · no-lookahead
live runtime never consumes Forward Outcome or future-derived features
```

Stage 6 is descriptive context, not a signal layer.

---

# 5. One Evaluation Layer / Two Entity Levels

Create one additive Stage 6 evaluation layer:

```text
ProductCandidateContext
    └── AnomalyContextDetail
```

`ProductCandidateContext` owns shared ticker-level B1/B2/B3/B5 data.

`AnomalyContextDetail` owns one row per persisted `ProductCandidateTrigger`, containing contract- or expiry-specific B4 detail plus expiry-anchored B2/B3 views and provenance.

Do not duplicate ticker-level data once per anomaly. All anomalies in the same ticker-expiry share one chain-context load/read. No paid API call per contract.

---

# 6. Evaluation Identity — FIRST_KNOWLEDGE_BASELINE vs REFRESH

Persist explicit:

```text
FIRST_KNOWLEDGE_BASELINE
REFRESH
```

Rules:

```text
one frozen FIRST_KNOWLEDGE_BASELINE per ProductCandidate occurrence
later REFRESH → separate ProductCandidateContext row
REFRESH never updates/replaces the baseline
```

A refresh may not mutate candidate first knowledge, baseline rows, baseline anomaly details, baseline source ids/timestamps, or baseline availability facts.

Do not auto-label legacy v1.2/v2.0/v3.1 rows as baseline.

---

# 7. Baseline Time Semantics

Keep separate:

```text
candidate_first_knowledge_at
context_evaluated_at
price_as_of
event_date
source_first_received_at
vendor_observed_at
local_captured_at
quote_as_of
```

For `FIRST_KNOWLEDGE_BASELINE`:

- `candidate_first_knowledge_at` remains the immutable Stage 5 anchor;
- `context_evaluated_at` records when Stage 6 computed/froze the context;
- every input must be knowable no later than its actual `context_evaluated_at`;
- evidence received/captured after `context_evaluated_at` cannot enter that baseline;
- do not claim an input was available at candidate first knowledge merely because its market/vendor date was earlier;
- preserve actual source times so research can distinguish candidate first knowledge from context evaluation time;
- unavailable sources remain truthfully unavailable/partial/not-yet-available;
- later data belongs to `REFRESH`, never to baseline.

No baseline backfill from future data.

---

# 8. Cost-Safe Baseline vs Explicit Paid Refresh

Do **not** hide new paid calls inside the Stage 5 / Phase 2A candidate materialization transaction.

The baseline path should freeze already-known/admissible evidence where available:

```text
persisted candidate + trigger evidence
already-loaded/archived chain snapshot data
already archived/cached source evidence whose source time is admissible
Dealer/GEX archive
canonical stored price data where available
```

Missing fresh ticker sources remain explicit missing/partial states. This keeps first-knowledge capture truthful and avoids silently changing Phase 2A scan cost.

Implement a separate Stage 6 `REFRESH` service/backend endpoint capable of the approved ticker-level source contract:

```text
daily_ohlc
stock_state
iv_rank
term_structure
```

Target granularity:

```text
once per ticker evaluation
not once per anomaly
```

Dealer/GEX remains archive-only with zero incremental calls.

No actual Nightwatch calls are authorized while executing this package. Tests use mocks/fakes/local fixtures only. Stage 7 later exposes refresh in the UI with cost disclosure.

---

# 9. B1 — Underlying Price Context

Ticker-level CORE:

```text
latest canonical regular-session close
1D return
5D return
20D return
SMA20
SMA50
ATR14
```

Derived/display-only:

```text
distance to SMA20
distance to SMA50
```

Optional:

```text
20-session high
20-session low
Trend State: UPTREND / DOWNTREND / MIXED / UNKNOWN
```

Trend State remains optional derived display from stored close/SMA20/SMA50. No `Price Bullish/Bearish`.

Preserve canonical regular-session policy, gap/ambiguity flags, and coverage quality. Missing/history-immature fields remain NULL/unavailable, never zero-filled.

---

# 10. B2 — Volatility Context

Use one shared normalized term-structure payload per ticker evaluation.

CORE:

```text
candidate-expiry IV per anomaly expiry
contract IV for contract anomalies from chain/archive reuse
```

## IV Rank

Stage 1 established:

```text
IV_RANK_ENTITY=TICKER
IV_RANK_VENDOR_SEMANTICS=UNVERIFIED
IV_RANK_TIME_PROVENANCE=PARTIAL
VNEXT_CORE_ELIGIBILITY=WITHHOLD_PENDING_PROVENANCE
```

Therefore Stage 6 must not:

```text
classify IV Rank LOW/MID/HIGH
use IV Rank in a score
use IV Rank in eligibility
pretend its window/scale is known
```

The model may preserve raw IV Rank + raw provenance if supplied, but its state remains `WITHHOLD_PENDING_PROVENANCE` until a separate proof.

Optional:

```text
Implied Move — vendor-provided value only, descriptive
```

Do not manufacture/self-derive a substitute if absent unless an already-authoritative vendor-defined derivation exists in current code/spec.

Expanded secondary context from the same term payload:

```text
nearest shorter expiry IV
nearest longer expiry IV
LOCAL_PEAK / LOCAL_TROUGH / RISING / FALLING / FLAT_OR_EQUAL / INCOMPLETE
```

No score or signal.

---

# 11. B3 — Dealer/GEX Structural Context

Stage 6 Dealer/GEX is:

```text
ARCHIVE-ONLY
ZERO incremental paid calls
```

The new active Stage 6 evaluator MUST NOT call:

```text
/v1/derived/heatmap/{ticker}/snapshot?format=full
```

Use the existing Dealer/GEX archive with no-lookahead time eligibility.

CORE per anomaly expiry:

```text
spot
anchor expiry
Primary Floor: strike + net GEX + sign
Primary Upper Positive-GEX Node: strike + net GEX + sign
Immediate Below-Floor Node: strike + net GEX + sign
```

Removed active labels:

```text
STABILIZATION_BIAS
DOWNSIDE_ACCELERATION_RISK
```

Keep raw nodes. Do not generate replacement directional labels.

Adjacent Expiry Context is optional. Do not use raw floating-point `==` for strike identity. Prefer canonical Decimal/normalized strike identity, an existing repository technical epsilon, or canonical quantization to persisted strike precision. Do not invent an analytical market threshold.

Missing/invalid strike rows are ineligible for nearest-strike logic and must never be distance 0. Distinguish single-available-negative, both-negative, and missing states.

---

# 12. B4 — Anomaly-Specific Option Snapshot

## Contract anomaly

Persist/serve:

```text
contract identity
expiration
right
strike
DTE with explicit anchor date
strike location vs spot: USD / % / ATR-normalized when available
contract IV
Delta
bid
ask
spread %
quote_as_of
```

Descriptive only. Delta is a moneyness/sensitivity descriptor, not direction.

Excluded from Phase 2B core:

```text
Gamma
Theta
Vega
```

No execution-quality score or executability gate.

## Expiry anomaly

Persist/serve:

```text
expiry identity
expiry activity evidence recap/reference
expiry-anchored B2 context
expiry-anchored B3 context
```

Do not fabricate contract symbol/strike/right/contract IV/Delta/bid/ask for expiry-only anomalies. Expiry Activity must have a complete Stage 6 path with no dead end.

---

# 13. Deep-Dive References — G16

Structure / Neighbor Strike / Cluster remain Phase 2A Deep Dive, not Phase 2B scoring.

Stage 6 may reference them only under accepted valid-state semantics:

```text
Cluster positive/reference: VALID_CLUSTER or STRONG_CLUSTER only
Structure reference: only accepted threshold-valid state
```

Do not ingest unfiltered top-5 clusters. `INVALID_CLUSTER` is never positive context. Missing Deep-Dive data remains NULL/unavailable. Do not roll Structure/Cluster into a Phase 2B score.

---

# 14. B5 — Provenance / Time / Availability

Per-layer availability:

```text
AVAILABLE
PARTIAL
UNAVAILABLE
NOT_YET_AVAILABLE
```

Use safe existing stale/history-immature states where already defined, but no composite readiness score.

Do not use active composite labels:

```text
CONTEXT_COMPLETE
CONTEXT_PARTIAL
CONTEXT_LIMITED
```

Execution availability does not require Gamma/Theta/Vega.

Preserve where applicable:

```text
ProductCandidate id
ProductCandidateTrigger id
source observation ids
raw payload ids
request ids
candidate_first_knowledge_at
context_evaluated_at
price_as_of
event_date
source_first_received_at
vendor_observed_at
local_captured_at
quote_as_of
context specification version
context rule/config version
context config hash
dealer archive source id + time eligibility
chain/archive source identity
```

No timestamp laundering.

---

# 15. Frozen Baseline Immutability / Idempotence

Required proof:

```text
baseline created at T0
refresh created at T1
baseline serialized/hash before refresh == baseline serialized/hash after refresh
```

Same baseline request replay:

```text
reuse same baseline
no duplicate
no re-read of later source state into baseline
```

Conflicting replay fails closed.

Baseline identity must bind at minimum:

```text
ProductCandidate occurrence
+ FIRST_KNOWLEDGE_BASELINE
+ Stage 6 context spec/rule identity
```

Refreshes are append-only distinct evaluation occurrences. `AnomalyContextDetail` uniqueness must bind context evaluation + ProductCandidateTrigger or equivalent authoritative identity.

---

# 16. Source Reuse / API Cost Discipline

Approved fresh ticker source contract:

```text
daily_ohlc          1
stock_state         1
iv_rank             1
term_structure      1
dealer_heatmap      0
```

Design target:

```text
<=4 ticker-level calls per explicit fresh evaluation
0 per-anomaly vendor calls
```

No actual calls during this package.

With fake client prove one candidate with N anomalies performs at most one call per ticker source and no contract-level multiplication. Anomalies sharing expiry reuse one chain-context/archive load per ticker-expiry or tighter.

If IV Rank is withheld at runtime, report both configured source contract and actual fake-call behavior; do not silently rewrite the governing contract.

---

# 17. N1 Dead Heatmap Handling

Stage 1 code proof established the old `format=full` Phase 2B heatmap call is invalid; historical DB runtime distribution remained unavailable.

Stage 6 rule:

```text
NEW_ACTIVE_STAGE6_HEATMAP_CALL=ABSENT
DEALER_GEX_SOURCE=ARCHIVE_ONLY
```

Do not require remote DB proof to build the new path. Do not falsely report historical runtime distribution as proven.

Return unless local authorized evidence exists:

```text
N1_CODE_PATH_CONFIRMED=YES
N1_HISTORICAL_RUNTIME_DISTRIBUTION_VERIFIED=NO
```

---

# 18. G24 — Candidate Entry / Refresh Dead End

Stage 6 entry point:

```text
ProductCandidate.id
+ full persisted ProductCandidateTrigger list
```

Never old exact-contract Radar-only gating.

Support:

```text
Radar-only candidate
Expiry-Activity-only candidate
configured-current Persistence-only candidate
mixed-trigger candidate
```

Current `CALIBRATION_REQUIRED` semantics remain unchanged: supporting Persistence alone cannot create the Stage 5 candidate, and Stage 6 must not reinterpret it.

Implement explicit backend Stage 6 read/evaluate/refresh service + route suitable for future Stage 7 UI use. No frontend redesign. GET must be read-only and must not trigger vendor calls or context writes.

---

# 19. Old Phase 2B Layers

Preserve historical tables/data:

```text
Phase2bTickerContextSnapshot
Phase2bCandidateEvaluation
Phase2bCandidateState
Phase2bV3ResearchWorkspace
```

Do not delete/destructively migrate. New Stage 6 writes only the new Stage 6 layer. If legacy refresh code remains, it is not the new ProductCandidate route. Legacy output remains explicitly legacy and cannot supply active vNext scores/direction/readiness semantics.

---

# 20. Additive Stage 6 Migration

Stage 6 owns one additive migration after:

```text
20260818_0016
```

Expected new head:

```text
20260818_0017
```

Migration may create:

```text
product_candidate_contexts
anomaly_context_details
```

plus required FKs/indexes/checks/uniqueness constraints.

No historical context backfill. No legacy Phase 2B INSERT/UPDATE repair. No Stage 5 history rewrite. No old-table drop.

Required:

```text
one Alembic head
offline PostgreSQL upgrade SQL
offline PostgreSQL downgrade SQL
ORM/migration agreement
no remote migration
```

If isolated PostgreSQL remains unavailable:

```text
ISOLATED_POSTGRES_RUNTIME_VERIFIED=NO
```

carry it.

---

# 21. Minimal Schema Requirements

After repository inspection choose the narrowest schema matching conventions.

`ProductCandidateContext` must represent at least:

```text
id
product_candidate_id
evaluation_kind
context_evaluated_at
context_specification_version
context_rule/config_version
context_config_hash
price context
shared volatility context
dealer/GEX context
candidate-level availability
candidate-level provenance
created_at audit time
```

`AnomalyContextDetail` must represent at least:

```text
id
product_candidate_context_id
product_candidate_trigger_id
anomaly entity type / identity
expiry anchor
contract B4 snapshot when CONTRACT
expiry B4 recap when EXPIRY
anomaly-specific volatility
anomaly-expiry GEX overlay
valid-only Deep-Dive references
anomaly-level availability
anomaly-level provenance
created_at audit time
```

Core identity/time fields must remain auditable. Structured JSON is acceptable for normalized blocks if consistent with repository conventions, but evaluation identity/FKs/timestamps must remain explicit.

---

# 22. API / Backend Contract

Implement backend support for at least:

```text
read persisted context by ProductCandidate id
read baseline + refresh history
create/evaluate FIRST_KNOWLEDGE_BASELINE through authorized baseline service
create explicit REFRESH through Stage 6 service
```

Prefer candidate-id routing. Follow repository conventions; example only:

```text
GET  /api/v1/product-candidates/{candidate_id}/context
POST /api/v1/product-candidates/{candidate_id}/context/refresh
```

Do not expose arbitrary vendor URLs. GET never creates/refreshes context. Missing baseline returns truthful missing/not-yet-available state with no side effects.

---

# 23. Forward Outcome / Actionability Boundary

New Stage 6 code must not read or derive from:

```text
Forward Outcome
T+1/T+3/T+5 returns
future price path
MFE
MAE
future labels
Actionability result
Trade Expression result
```

Phase 2B must not output BUY/SELL/BULLISH/BEARISH/ACTIONABLE/NOT_ACTIONABLE/WATCH/conviction/edge/expected return.

Direction remains `UNRESOLVED` where surfaced.

---

# 24. Carried Items

Preserve:

```text
CURRENT_TRIGGER_FRESHNESS_MODE=CALIBRATION_REQUIRED
RADAR_OI_SCHEDULE_ACTIVATION=PENDING_ROLLOVER_EVIDENCE
ISOLATED_POSTGRES_RUNTIME_VERIFIED=NO
CROSS_RUN_CANDIDATE_LIFECYCLE=DEFERRED_NO_AUTO_MERGE
IV_RANK_CORE_ELIGIBILITY=WITHHOLD_PENDING_PROVENANCE
```

Also carry `N1_HISTORICAL_RUNTIME_DISTRIBUTION_VERIFIED=NO` if no local DB proof exists.

Do not resolve any carried item by invention.

---

# 25. Mandatory Read-Only Repository Orientation

Before editing, trace:

1. Stage 5 candidate + trigger models/repository/materializer;
2. Stage 5 accepted transaction boundary;
3. Stage 3 evaluation identity/freshness/provenance support;
4. legacy Phase 2B v1.2/v2.0/v3.1 write/read paths;
5. daily_ohlc normalization/canonical-session logic;
6. stock_state normalization and exact fields;
7. IV Rank normalization/provenance;
8. term-structure normalization;
9. archived chain read path for IV/Delta/bid/ask/quote timestamps;
10. Dealer/GEX archive no-lookahead repository;
11. Structure/Cluster validity helpers;
12. current Phase 2B routes/CLI;
13. migrations/tests.

Return before editing:

```text
REPOSITORY_ORIENTATION
- Stage5 ProductCandidate read path:
- Stage5 trigger read path:
- Stage5 first-knowledge anchor:
- Stage3 evaluation identity support:
- legacy Phase2B write path:
- legacy Phase2B read path:
- daily_ohlc source/normalizer:
- stock_state source/normalizer:
- IV Rank source/provenance:
- term_structure source/normalizer:
- chain archive reuse path:
- dealer archive no-lookahead path:
- Deep-Dive validity path:
- candidate-id API entry point candidate:
- migration predecessor:
```

Then:

```text
AUTHORIZED_FILES_PROPOSED:
- <file>: <reason>
```

READ BROADLY; WRITE NARROWLY.

---

# 26. Authorized File Scope

Likely authorized categories:

```text
backend/app/db/models.py
backend/alembic/versions/<0017 Stage6 migration>
backend/app/confirmation/... or a narrow new Phase2B vNext module
backend/app/api/routes/... candidate context routes
backend/tests/... Stage6 focused tests
minimal glossary/API schema update only if required by backend serialization
```

Not authorized:

```text
.github/workflows/*
Radar/OI schedule changes
Dealer/GEX scheduler/archive collection changes
Phase 2A scoring/threshold changes
Stage 7 frontend redesign
Forward Outcome
Actionability
Trade Expression
```

---

# 27. Required Functional Proofs

## S6-A Candidate entry

Prove Radar-only, Expiry-Activity-only, configured-current Persistence-only, and mixed candidates all reach Stage 6 without a Radar-only exact-contract gate.

## S6-B Ticker sharing

Multiple anomalies under one candidate produce one shared ticker context and N anomaly details, not duplicated ticker data.

## S6-C Baseline immutability

```text
BASELINE_MUTATED_BY_REFRESH=NO
BASELINE_DETAIL_MUTATED_BY_REFRESH=NO
```

## S6-D Baseline source time

Post-`context_evaluated_at` evidence cannot enter baseline. Missing vendor timestamp remains NULL rather than local fallback.

## S6-E B1

Canonical close, 1/5/20D returns, SMA20/50, ATR14 retain coverage/gap semantics. Missing is not zero. No bullish/bearish.

## S6-F B2

Candidate-expiry IV from one shared term payload; contract IV from chain reuse; IV Rank raw/provenance only with WITHHOLD state; no per-contract vendor call.

## S6-G B3

```text
STAGE6_DEALER_HEATMAP_CALLS=0
DEALER_GEX_ARCHIVE_ONLY=YES
```

No-lookahead archive selection; no missing-strike distance 0; no removed GEX labels.

## S6-H Contract B4

Contract IV/Delta/bid/ask/spread/quote time and strike location present where available. No Gamma/Theta/Vega core and no execution score.

## S6-I Expiry B4

Expiry-only candidate gets valid context without fabricated contract fields.

## S6-J G16

Invalid/subthreshold Structure and invalid Cluster cannot appear as positive Deep-Dive references.

## S6-K Availability

Per-layer availability remains independent. No composite readiness score. Missing one block does not erase another.

## S6-L Cost/reuse

Fake client proof:

```text
one ticker + multiple anomalies
daily_ohlc <= 1
stock_state <= 1
iv_rank <= 1
term_structure <= 1
dealer_heatmap = 0
per-contract vendor calls = 0
```

## S6-M GET safety

Repeated GET causes zero DB writes and zero vendor calls.

## S6-N Legacy

Old Phase 2B rows remain readable; new vNext writes only new Stage 6 tables.

## S6-O Future leakage

```text
FORWARD_OUTCOME_INPUTS_USED=NO
ACTIONABILITY_INPUTS_USED=NO
```

---

# 28. Regression Tests

Run safely on Stage 6 worktree:

1. focused Stage 6 tests;
2. Stage 5 focused tests;
3. Stage 4A/4B regressions;
4. Stage 2/3 regressions;
5. full backend suite;
6. Ruff;
7. glossary/null-safety if API fields change;
8. frontend lint/build only if shared frontend/API types are touched;
9. Alembic heads;
10. offline PostgreSQL upgrade SQL;
11. offline PostgreSQL downgrade SQL;
12. `git diff --check`.

No external requests. No Nightwatch. No remote DB.

---

# 29. Completion Report

Create:

```text
docs/evidence/NIGHTWATCH_VNEXT_STAGE6_PHASE2B_BALANCED_MODEL_COMPLETION_REPORT_20260818.md
```

Return full report.

## A. Result

```text
STAGE6_RESULT=PASS/PASS_WITH_CARRIED_ITEMS/HOLD/FAIL
```

## B. Bootstrap

```text
STAGE5_ACCEPTED_COMMIT=
STAGE6_BRANCH=
STAGE6_WORKTREE=
STAGE6_BASE_HEAD=
WORKTREE_CLEAN_AT_STAGE6_START=YES/NO
ALEMBIC_HEAD_BEFORE=20260818_0016
```

## C. Core entities

```text
PRODUCT_CANDIDATE_CONTEXT_PERSISTED=YES/NO
ANOMALY_CONTEXT_DETAIL_PERSISTED=YES/NO
ONE_EVALUATION_LAYER_VERIFIED=YES/NO
OLD_PHASE2B_LAYERS_PRESERVED_READ_ONLY=YES/NO
```

## D. Evaluation identity

```text
FIRST_KNOWLEDGE_BASELINE_IMPLEMENTED=YES/NO
REFRESH_IMPLEMENTED=YES/NO
BASELINE_MUTATED_BY_REFRESH=YES/NO
BASELINE_DETAIL_MUTATED_BY_REFRESH=YES/NO
```

## E. Entry path

```text
PRODUCT_CANDIDATE_ENTRYPOINT=YES/NO
RADAR_ONLY_SUPPORTED=YES/NO
EXPIRY_ACTIVITY_ONLY_SUPPORTED=YES/NO
PERSISTENCE_ONLY_SUPPORTED_WHEN_CURRENT_ELIGIBLE=YES/NO
MIXED_TRIGGER_SUPPORTED=YES/NO
RADAR_ONLY_GATE_REMAINS_IN_VNEXT=YES/NO
```

## F. Blocks

```text
B1_PRICE_CONTEXT=PASS/FAIL
B2_VOLATILITY_CONTEXT=PASS/FAIL
B3_DEALER_GEX_CONTEXT=PASS/FAIL
B4_ANOMALY_CONTEXT=PASS/FAIL
B5_PROVENANCE_AVAILABILITY=PASS/FAIL
```

## G. Cost/reuse

```text
CONFIGURED_SOURCE_CONTRACT=4
MAX_TICKER_SOURCE_CALLS_IN_FAKE_REFRESH=
PER_ANOMALY_VENDOR_CALLS=
STAGE6_DEALER_HEATMAP_CALLS=
CHAIN_CONTEXT_REUSED_PER_TICKER_EXPIRY=YES/NO
```

Expected max <=4, per-anomaly 0, heatmap 0.

## H. IV Rank

```text
IV_RANK_ENTITY=TICKER
IV_RANK_VENDOR_SEMANTICS=UNVERIFIED
IV_RANK_CORE_ELIGIBILITY=WITHHOLD_PENDING_PROVENANCE
IV_RANK_CLASSIFICATION_INTRODUCED=YES/NO
```

Expected classification = NO.

## I. GEX / G16 / G17 / G18

```text
DEALER_GEX_ARCHIVE_ONLY=YES/NO
INVALID_CLUSTER_POSITIVE_LEAK=YES/NO
SUBTHRESHOLD_STRUCTURE_POSITIVE_LEAK=YES/NO
STABILIZATION_BIAS_ACTIVE=YES/NO
DOWNSIDE_ACCELERATION_RISK_ACTIVE=YES/NO
MISSING_STRIKE_DISTANCE_ZERO_FOUND=YES/NO
RAW_FLOAT_STRIKE_EQUALITY_USED=YES/NO
```

Expected YES / NO / NO / NO / NO / NO / NO.

## J. Option detail boundaries

```text
EXPIRY_TRIGGER_FABRICATES_CONTRACT=YES/NO
GAMMA_IN_PHASE2B_CORE=YES/NO
THETA_IN_PHASE2B_CORE=YES/NO
VEGA_IN_PHASE2B_CORE=YES/NO
EXECUTION_SCORE_INTRODUCED=YES/NO
```

Expected all NO.

## K. Time / no-lookahead

```text
CONTEXT_TIME_IDENTITIES_SEPARATE=YES/NO
POST_CONTEXT_EVALUATION_EVIDENCE_CAN_ENTER_BASELINE=YES/NO
VENDOR_TIME_FALLS_BACK_TO_LOCAL=YES/NO
CREATED_AT_CAN_LAUNDER_FRESHNESS=YES/NO
```

Expected YES / NO / NO / NO.

## L. Availability

```text
PER_LAYER_AVAILABILITY_PRESERVED=YES/NO
COMPOSITE_CONTEXT_READINESS_PRESENT=YES/NO
MISSING_CONTEXT_ZERO_FILLED=YES/NO
```

Expected YES / NO / NO.

## M. Migration

```text
MIGRATION_CREATED=YES
ALEMBIC_HEAD=
ALEMBIC_SINGLE_HEAD=YES/NO
HISTORICAL_BACKFILL_PERFORMED=YES/NO
OLD_PHASE2B_TABLE_DROPPED=YES/NO
ISOLATED_POSTGRES_RUNTIME_VERIFIED=YES/NO
REMOTE_MIGRATION_RUN=NO
```

## N. Stage boundaries

```text
PHASE2A_SCORING_CHANGED=YES/NO
DASHBOARD_STAGE7_STARTED=YES/NO
FORWARD_OUTCOME_STARTED=YES/NO
ACTIONABILITY_STARTED=YES/NO
TRADE_EXPRESSION_STARTED=YES/NO
```

Expected all NO.

## O. N1 proof status

```text
N1_CODE_PATH_CONFIRMED=YES
N1_HISTORICAL_RUNTIME_DISTRIBUTION_VERIFIED=YES/NO
```

No remote proof authorized.

## P. Carried items

Preserve current freshness, Radar/OI rollover, cross-run lifecycle, IV Rank provenance, isolated PG runtime, and N1 historical distribution as applicable.

## Q. Tests

List exact commands/results.

## R. Diff

```text
FILES_CHANGED=
LINES_ADDED=
LINES_REMOVED=
MIGRATION_FILES=
WORKFLOW_FILES=
FRONTEND_FILES=
```

## S. Authorization ledger

```text
NIGHTWATCH_REQUESTS=0
PAID_UNITS=0
REMOTE_DB_WRITES=0
REMOTE_MIGRATIONS_RUN=0
WORKFLOWS_DISPATCHED=0
STAGE5_ACCEPTED_COMMITS_CREATED=1
STAGE6_IMPLEMENTATION_COMMITS_CREATED=0
PUSHES=0
PRS_CREATED=0
MERGES=0
EXTERNAL_URLS_OR_API_ENDPOINTS_CONTACTED=[]
```

## T. Next-stage readiness

```text
STAGE7_READY=YES/NO
NEXT_AUTHORIZED_STAGE=NONE
```

Do not start Stage 7.

---

# 30. Hard STOP Conditions

STOP with `HOLD` if:

- accepted Stage 5 state cannot be isolated into the authorized predecessor commit;
- Stage 5 first-knowledge semantics would need rewriting;
- ProductCandidate cannot be the Stage 6 entry point;
- a second candidate eligibility algorithm would be required;
- baseline immutability cannot be enforced;
- baseline would need future evidence;
- Phase 2B requires a composite score;
- IV Rank semantics would need to be invented;
- GEX archive cannot be queried time-correctly and the only option is a new live heatmap call;
- expiry anomaly support requires fabricated contract data;
- implementation requires Phase 2A scoring changes;
- implementation requires Stage 7 dashboard work;
- implementation requires Forward Outcome / Actionability / Trade Expression;
- migration would rewrite/backfill old context history;
- a second Alembic head would be created;
- remote DB or real Nightwatch calls are required.

Report exact reason. Do not workaround an architectural HOLD.

---

# 31. Authorization Summary

Authorized:

```text
one local accepted Stage5 commit
new isolated Stage6 branch/worktree
ProductCandidateContext
AnomalyContextDetail
FIRST_KNOWLEDGE_BASELINE
REFRESH
Balanced Model B1-B5
candidate-id Stage6 backend API/service
ticker-level source reuse
archive-only Dealer/GEX
minimal additive 0017 migration
local mocked tests/regressions
```

Not authorized:

```text
Phase 2A redesign
Stage 7 dashboard redesign
Forward Outcome
Actionability
Trade Expression
universe expansion
numeric Persistence calibration
Radar/OI cron activation
Dealer/GEX scheduler changes
real Nightwatch calls
remote DB writes/migrations
push/PR/merge
```

At completion:

```text
NEXT_AUTHORIZED_STAGE=NONE
```

STOP.

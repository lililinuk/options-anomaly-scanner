# Nightwatch vNext — Stage 8 Observation Resume — First Genuine Sample Review — Execution Package

**Date:** 2026-08-24  
**Purpose:** Resume Stage 8 as a **zero-paid, read-only observation review** now that the third controlled MAG7 run has a complete genuine ProductCandidate + frozen first-knowledge baseline sample.  
**Authorization:** Founder explicitly authorized **Stage 8 Observation Resume**.  
**Execution worktree:** `F:\options-anomaly-scanner-stage8`  
**Branch:** `vnext/stage8-mag7-observation`  
**Runtime schema:** `20260818_0017`

---

# 0. Founder authorization

```text
FOUNDER_AUTHORIZATION=STAGE8_OBSERVATION_RESUME_20260824

STAGE8_OBSERVATION_RESUME_AUTHORIZED=YES

MAG7_SCAN_AUTHORIZED=NO
NIGHTWATCH_REQUEST_AUTHORIZED=NO
PAID_PHASE2B_REFRESH_AUTHORIZED=NO
DEALER_GEX_LIVE_CALL_AUTHORIZED=NO
REMOTE_APPLICATION_DATA_WRITE_AUTHORIZED=NO
REMOTE_SCHEMA_WRITE_AUTHORIZED=NO
FOURTH_MAG7_SCAN_AUTHORIZED=NO
STAGE9_EXECUTION_AUTHORIZED=NO
```

This task is read-only observation/review only.

---

# 1. Authoritative current sample

The current genuine Stage 8 sample is the third controlled run:

```text
TARGET_SCAN_RUN_ID=2c71e5bb-9334-4806-a195-0f8768d2d0f2
TARGET_SCAN_RUN_STATUS=COMPLETE

PRODUCT_CANDIDATES=7
PRODUCT_CANDIDATE_TRIGGERS=82

FIRST_KNOWLEDGE_BASELINES=7
ANOMALY_CONTEXT_DETAILS=82

BASELINE_LOOKAHEAD_FOUND=NO
BASELINE_SOURCE_TIME_VIOLATION_FOUND=NO
BASELINE_TRIGGER_SET_DRIFT_FOUND=NO
BASELINE_FIRST_KNOWLEDGE_CUTOFF_MISMATCH_FOUND=NO
```

Accepted prior Stage 8 runtime remediations:

```text
S4 identifier length defect = FIXED
post-candidate Deep-Dive PARTIAL escalation defect = FIXED
baseline JSONB null / SQL NULL defect = FIXED
baseline runtime DB configuration retry = PASS
```

Do not reinterpret the two earlier controlled runs as genuine successful candidate samples:

```text
FIRST_CONTROLLED_RUN_ID=090359ad-9d76-49b9-8902-f28ac54a1d1b
STATUS=FAILED

SECOND_CONTROLLED_RUN_ID=e9267160-503a-41c7-9bb1-8cc2b2e3d8c6
STATUS=PARTIAL
```

They may be included only in truthful run-level failure/zero-success accounting where relevant.

---

# 2. Canonical evidence root

Use:

```text
F:\options-anomaly-scanner\docs\evidence
```

If this exact execution package is attached and absent from canonical evidence, preserve it byte-for-byte as:

```text
F:\options-anomaly-scanner\docs\evidence\NIGHTWATCH_VNEXT_STAGE8_OBSERVATION_RESUME_FIRST_GENUINE_SAMPLE_EXECUTION_PACKAGE_20260824.md
```

If the canonical target exists with different bytes:

```text
STAGE8_OBSERVATION_RESULT=HOLD_PACKAGE_CONFLICT
```

Do not overwrite. STOP.

Read completely at minimum:

```text
F:\options-anomaly-scanner\docs\evidence\NIGHTWATCH_VNEXT_CANONICAL_EVIDENCE_MANIFEST.md

F:\options-anomaly-scanner\docs\evidence\NIGHTWATCH_SCANNER_VNEXT_INTEGRATED_SPEC_PROMPT_20260817(1).md

F:\options-anomaly-scanner\docs\evidence\NIGHTWATCH_VNEXT_STAGE4B_PHASE2A_VNEXT_CODEX_EXECUTION_PACKAGE_20260818.md

F:\options-anomaly-scanner\docs\evidence\NIGHTWATCH_VNEXT_STAGE5_PRODUCT_CANDIDATE_PERSISTENCE_COMPLETION_REPORT_20260818.md

F:\options-anomaly-scanner\docs\evidence\NIGHTWATCH_VNEXT_STAGE6_PHASE2B_BALANCED_MODEL_COMPLETION_REPORT_20260818.md

F:\options-anomaly-scanner\docs\evidence\NIGHTWATCH_VNEXT_STAGE6_BASELINE_CUTOFF_REMEDIATION_PASS_20260820.md

F:\options-anomaly-scanner\docs\evidence\NIGHTWATCH_VNEXT_STAGE7_CANDIDATE_FIRST_DASHBOARD_COMPLETION_REPORT_20260819.md

F:\options-anomaly-scanner\docs\evidence\NIGHTWATCH_VNEXT_STAGE8_MAG7_OBSERVATION_EXECUTION_PACKAGE_20260820.md

F:\options-anomaly-scanner\docs\evidence\NIGHTWATCH_VNEXT_THIRD_CONTROLLED_LIVE_MAG7_OBSERVATION_REPORT_20260820.md

F:\options-anomaly-scanner\docs\evidence\NIGHTWATCH_VNEXT_STAGE8_BASELINE_ONLY_CREATION_RETRY_REPORT_20260824.md
```

Also read the Stage 8 diagnostic/remediation reports as needed to explain carried runtime history, but do not let resolved defects distort current-sample metrics.

---

# 3. Hard authorization boundary

Authorized:

```text
repository/code inspection
read-only runtime DB SELECTs
read-only Stage 8 metric computation
read-only evidence/report inspection
local/offline calculations using already persisted data
primary + canonical evidence report creation
```

Forbidden:

```text
MAG7 scan
Nightwatch request
vendor request
Phase2B REFRESH
Dealer/GEX live request
ProductCandidate write
trigger write
baseline write
manual DB DML
schema write
migration
code/test edit
workflow/scheduler edit
threshold change
calibration change
universe expansion
Forward Outcome computation
Stage 9 execution
commit/push/PR/merge
```

Required:

```text
MAG7_SCAN_INVOCATIONS_THIS_TASK=0
NIGHTWATCH_REQUESTS_THIS_TASK=0
PAID_UNITS_THIS_TASK=0
REMOTE_DB_SCHEMA_WRITES=0
REMOTE_APPLICATION_DATA_WRITES=0
```

---

# 4. Sample eligibility and observation scope

Stage 8 must distinguish:

```text
run-level operational history
vs
genuine ProductCandidate observation samples
```

A genuine Stage 8 candidate sample requires:

```text
current vNext ProductCandidate
immutable trigger set
candidate_first_knowledge_at
frozen FIRST_KNOWLEDGE_BASELINE
accepted Stage 6 information-time semantics
```

For this review, identify all runtime records satisfying that definition.

Expected minimum:

```text
ELIGIBLE_GENUINE_SCAN_RUNS=1
ELIGIBLE_GENUINE_PRODUCT_CANDIDATES=7
ELIGIBLE_GENUINE_BASELINES=7
```

Do not invent a minimum day count.

Do not exclude the sample merely because it is currently one NY market date.

Return:

```text
ELIGIBLE_GENUINE_SCAN_RUN_COUNT=
ELIGIBLE_GENUINE_CANDIDATE_COUNT=
ELIGIBLE_GENUINE_BASELINE_COUNT=
ELIGIBLE_NY_MARKET_DATES=
```

---

# 5. Mandatory observation dimensions O1–O9

Observe the accepted Stage 8 dimensions.

## O1 — Candidates / day

Report by NY market date:

```text
distinct ProductCandidates
successful candidate-producing runs
successful zero-candidate runs
PARTIAL runs
FAILED runs
```

Do not convert failed/partial runs into zero-candidate successful observations.

For the genuine sample also report candidate count by ticker.

Return:

```text
O1_STATUS=OBSERVED/SPARSE/UNRESOLVED
```

---

## O2 — Anomalies / candidate

For each eligible ProductCandidate report:

```text
ticker
total immutable triggers
qualifying triggers
supporting triggers
contract-level triggers
expiry-level triggers
trigger-family breakdown
```

Do not call this Evidence Breadth.

Do not collapse to a conviction score.

Return descriptive distribution:

```text
min
median
mean
max
```

Return:

```text
O2_STATUS=OBSERVED/SPARSE/UNRESOLVED
```

---

## O3 — Route frequencies

Accepted active routes only:

```text
RADAR_EVENT
EXPIRY_ACTIVITY
CONTRACT_PERSISTENCE
```

Report:

```text
trigger counts by route
candidate count touched by each route
candidate-level route combinations
```

Do not infer direction.

Do not treat route count as conviction.

Return:

```text
O3_STATUS=OBSERVED/SPARSE/UNRESOLVED
```

---

## O4 — Persistence maturation

For CONTRACT_PERSISTENCE evidence report only the accepted fields actually available, including where present:

```text
accepted valid observations
3 / 5 / 10 observation markers
window/span
current-trigger vs supporting status
freshness state/reason
```

Critical rule:

```text
CURRENT_TRIGGER_FRESHNESS_MODE=CALIBRATION_REQUIRED
```

Do not choose a numeric freshness threshold.

Do not convert calibration-required into PASS/FAIL.

If one sample cannot show maturation over time, label that dimension `SPARSE` rather than inventing a threshold.

Return:

```text
O4_STATUS=OBSERVED/SPARSE/UNRESOLVED
```

---

## O5 — Phase 2B context availability

For each of seven frozen baselines, report B1–B5 independently.

Do not create a composite completeness score.

At minimum report:

```text
candidate ticker
B1 state
B2 state
B3 state
B4 detail count / availability state
B5 state
baseline existence
baseline creation lag
```

Baseline creation lag:

```text
context_evaluated_at - candidate_first_knowledge_at
```

This is descriptive only.

Do not interpret longer lag as lower quality unless accepted semantics say so.

Return per-layer state frequencies and reasons.

Return:

```text
O5_STATUS=OBSERVED/SPARSE/UNRESOLVED
```

---

## O6 — Ticker concentration

Universe remains MAG7 only.

Report:

```text
candidate count by ticker
trigger count by ticker
share of candidates by ticker
share of triggers by ticker
```

Describe concentration only.

Do not claim bias or over-concentration from one genuine day.

Do not propose universe expansion or threshold changes.

Return:

```text
O6_STATUS=OBSERVED/SPARSE/UNRESOLVED
```

---

## O7 — Chain reuse

Use only actual telemetry or directly measurable source identity.

Distinguish:

```text
actual chain fetch/reuse telemetry
shared persisted source identity
inference
```

If actual reuse cannot be measured from current telemetry:

```text
O7_STATUS=UNRESOLVED
O7_REASON=UNRESOLVED_CURRENT_TELEMETRY
```

Do not add instrumentation in this task.

Do not infer a chain reuse rate merely because multiple contexts reference the same archive/source row.

If shared source identity can be counted, report it separately as:

```text
SHARED_SOURCE_IDENTITY_OBSERVED=
```

not as a reuse rate.

---

## O8 — Phase 2B API cost

Use only actual persisted telemetry.

Separate:

```text
FIRST_KNOWLEDGE_BASELINE paid refresh calls
REFRESH paid calls
Dealer/GEX live calls
archive-only usage
scanner Nightwatch calls
```

For the baseline-only step:

```text
paid refresh = 0
Dealer/GEX live = 0
```

Do not make calls to complete the metric.

Report only what can be attributed truthfully.

Return:

```text
O8_STATUS=OBSERVED/SPARSE/UNRESOLVED
```

---

## O9 — Freshness failures

Report per-layer state/reason counts.

Do not create a composite freshness penalty.

Include, where applicable:

```text
current
stale
unavailable
not-yet-available
calibration-required
unknown/unresolved
```

Preserve missing != zero.

Return:

```text
O9_STATUS=OBSERVED/SPARSE/UNRESOLVED
```

---

# 6. Mandatory integrity spot checks

Spot-check all seven eligible candidates/baselines for:

```text
candidate_first_knowledge_at immutability
baseline evidence_cutoff_at equality
no baseline lookahead
no baseline mutation
trigger-set identity preserved
no Deep-Dive budget suppression
no Deep-Dive availability suppression
missing context truthfully represented
```

Return:

```text
SPOTCHECK_CANDIDATES_CHECKED=
CANDIDATE_FIRST_KNOWLEDGE_MUTATION_FOUND=YES/NO
BASELINE_LOOKAHEAD_FOUND=YES/NO
BASELINE_MUTATION_FOUND=YES/NO
TRIGGER_SET_DRIFT_FOUND=YES/NO
DEEP_DIVE_BUDGET_SUPPRESSION_FOUND=YES/NO
DEEP_DIVE_AVAILABILITY_SUPPRESSION_FOUND=YES/NO
MISSING_AS_ZERO_FOUND=YES/NO
```

Any integrity violation:

```text
STAGE8_OBSERVATION_RESULT=FAIL_BLOCKING_INTEGRITY_DEFECT
```

STOP. Do not fix within this task.

---

# 7. 0DTE observation

If any eligible candidate/trigger contains accepted 0DTE evidence, report the actual persisted state using only accepted vocabulary, including where relevant:

```text
PROVISIONAL_INTRADAY
CANONICAL_SESSION_COMPLETE
LEGACY_OR_AMBIGUOUS
```

If none:

```text
ZERO_DTE_SAMPLE_PRESENT=NO
```

Do not infer absent 0DTE behavior from non-0DTE records.

---

# 8. Forward Outcome hard prohibition

Stage 8 must not compute or use:

```text
T+1 return
T+3 return
T+5 return
MFE
MAE
max upside
max downside
future realized price
future realized volatility
future direction
```

Return:

```text
FORWARD_OUTCOME_USED=NO
FUTURE_DATA_USED=NO
```

---

# 9. No calibration / no threshold mutation

This review is observational.

Do not change:

```text
route thresholds
freshness thresholds
persistence thresholds
Deep-Dive budget
candidate rules
universe
scoring
dashboard ranking
```

Return:

```text
CALIBRATION_CHANGES=0
THRESHOLD_CHANGES=0
UNIVERSE_CHANGES=0
```

---

# 10. Stage 8 sufficiency assessment

Do not impose arbitrary:

```text
5-day
10-day
20-day
N-candidate
N-run
```

minimums.

Instead assess each O1–O9 dimension as:

```text
OBSERVED
SPARSE
UNRESOLVED
```

Then determine whether the current Stage 8 observation has:

```text
blocking integrity defect
or
no blocking integrity defect
```

and whether further natural observation would materially improve currently sparse dimensions.

Return:

```text
OBSERVED_DIMENSIONS=
SPARSE_DIMENSIONS=
UNRESOLVED_DIMENSIONS=
BLOCKING_INTEGRITY_DEFECT_FOUND=YES/NO
FURTHER_NATURAL_OBSERVATION_USEFUL=YES/NO
```

---

# 11. Stage 9 Design Gate readiness assessment only

This task does **not** authorize Stage 9.

Assess only whether a future Stage 9 **Design Gate** could be opened under the accepted criteria.

Required criteria:

```text
at least one genuine ProductCandidate sample exists
candidate_first_knowledge_at exists
frozen FIRST_KNOWLEDGE_BASELINE exists
no blocking information-time/integrity defect
O1–O9 are observed or explicitly unresolved/sparse with reason
no unresolved sample-key semantic blocker
```

Do not require a fabricated minimum number of days.

Return:

```text
STAGE9_DESIGN_GATE_READINESS=YES/NO
STAGE9_READINESS_BLOCKERS=
```

Even if readiness is YES:

```text
STAGE9_READY=NO
```

for this task, because no Stage 9 execution is authorized.

The distinction is:

```text
STAGE9_DESIGN_GATE_READINESS = analytical assessment
STAGE9_READY = execution authorization/state transition
```

---

# 12. Result states

Use exactly one:

```text
STAGE8_OBSERVATION_RESULT=PASS_WITH_CARRIED_ITEMS
STAGE8_OBSERVATION_RESULT=CONTINUE_OBSERVATION
STAGE8_OBSERVATION_RESULT=HOLD_RUNTIME_PREREQUISITE
STAGE8_OBSERVATION_RESULT=HOLD_MISSING_GOVERNING_EVIDENCE
STAGE8_OBSERVATION_RESULT=FAIL_BLOCKING_INTEGRITY_DEFECT
```

Guidance:

```text
PASS_WITH_CARRIED_ITEMS
= current observation dimensions are sufficiently characterized for the Stage 8 review purpose,
  with any residual items explicitly carried.

CONTINUE_OBSERVATION
= no blocker, but one or more important dimensions are materially sparse and natural additional
  observations would improve the evidence base.

Do not use CONTINUE_OBSERVATION merely because there is only one day.
```

---

# 13. Carried ledger

Preserve and report:

```text
CURRENT_TRIGGER_FRESHNESS_MODE=CALIBRATION_REQUIRED
RADAR_OI_SCHEDULE_ACTIVATION=PENDING_ROLLOVER_EVIDENCE
CROSS_RUN_CANDIDATE_LIFECYCLE=DEFERRED_NO_AUTO_MERGE
IV_RANK_CORE_ELIGIBILITY=WITHHOLD_PENDING_PROVENANCE
ISOLATED_POSTGRES_RUNTIME_VERIFIED=NO
N1_HISTORICAL_RUNTIME_DISTRIBUTION_VERIFIED=NO
```

Do not resolve them unless the current read-only evidence actually does so under accepted rules.

---

# 14. Evidence report — primary + canonical backup

Create primary:

```text
F:\options-anomaly-scanner-stage8\docs\evidence\stage8\NIGHTWATCH_VNEXT_STAGE8_OBSERVATION_RESUME_FIRST_GENUINE_SAMPLE_REPORT_20260824.md
```

Also save a byte-identical canonical backup:

```text
F:\options-anomaly-scanner\docs\evidence\NIGHTWATCH_VNEXT_STAGE8_OBSERVATION_RESUME_FIRST_GENUINE_SAMPLE_REPORT_20260824.md
```

Requirements:

```text
primary/canonical byte-identical
verify SHA-256 for both
never overwrite conflicting canonical content
```

If same-name canonical content differs:

```text
STAGE8_OBSERVATION_RESULT=HOLD_REPORT_CONFLICT
```

and STOP.

---

# 15. Required final fields

Return:

```text
STAGE8_OBSERVATION_RESULT=

FOUNDER_AUTHORIZATION=STAGE8_OBSERVATION_RESUME_20260824

ELIGIBLE_GENUINE_SCAN_RUN_COUNT=
ELIGIBLE_GENUINE_CANDIDATE_COUNT=
ELIGIBLE_GENUINE_BASELINE_COUNT=
ELIGIBLE_NY_MARKET_DATES=

O1_STATUS=
O2_STATUS=
O3_STATUS=
O4_STATUS=
O5_STATUS=
O6_STATUS=
O7_STATUS=
O8_STATUS=
O9_STATUS=

OBSERVED_DIMENSIONS=
SPARSE_DIMENSIONS=
UNRESOLVED_DIMENSIONS=

SPOTCHECK_CANDIDATES_CHECKED=
CANDIDATE_FIRST_KNOWLEDGE_MUTATION_FOUND=
BASELINE_LOOKAHEAD_FOUND=
BASELINE_MUTATION_FOUND=
TRIGGER_SET_DRIFT_FOUND=
DEEP_DIVE_BUDGET_SUPPRESSION_FOUND=
DEEP_DIVE_AVAILABILITY_SUPPRESSION_FOUND=
MISSING_AS_ZERO_FOUND=

ZERO_DTE_SAMPLE_PRESENT=

FORWARD_OUTCOME_USED=NO
FUTURE_DATA_USED=NO

CALIBRATION_CHANGES=0
THRESHOLD_CHANGES=0
UNIVERSE_CHANGES=0

BLOCKING_INTEGRITY_DEFECT_FOUND=
FURTHER_NATURAL_OBSERVATION_USEFUL=

STAGE9_DESIGN_GATE_READINESS=
STAGE9_READINESS_BLOCKERS=

MAG7_SCAN_INVOCATIONS_THIS_TASK=0
NIGHTWATCH_REQUESTS_THIS_TASK=0
PAID_UNITS_THIS_TASK=0
PHASE2B_REFRESH_CALLS=0
DEALER_GEX_LIVE_CALLS=0

REMOTE_DB_SCHEMA_WRITES=0
REMOTE_APPLICATION_DATA_WRITES=0

APPLICATION_CODE_CHANGES=0
TEST_CODE_CHANGES=0
MIGRATION_CHANGES=0
WORKFLOW_CHANGES=0
SCHEDULER_CHANGES=0
COMMITS_CREATED=0
PUSHES=0
PRS_CREATED=0
MERGES=0

PRIMARY_REPORT_PATH=
CANONICAL_REPORT_PATH=
PRIMARY_REPORT_SHA256=
CANONICAL_REPORT_SHA256=
REPORT_BACKUP_BYTE_IDENTICAL=YES/NO

FOURTH_MAG7_SCAN_AUTHORIZED=NO
STAGE8_OBSERVATION_RESUME_READY=YES/NO
STAGE9_READY=NO
NEXT_AUTHORIZED_STAGE=NONE
```

If result is:

```text
PASS_WITH_CARRIED_ITEMS
or
CONTINUE_OBSERVATION
```

and no blocking integrity defect exists:

```text
STAGE8_OBSERVATION_RESUME_READY=YES
```

This does not authorize another scan or Stage 9.

STOP.

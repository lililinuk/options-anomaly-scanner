# Nightwatch vNext — Third Controlled Live MAG7 Observation — Execution Package

**Date:** 2026-08-20  
**Purpose:** Obtain one genuine vNext MAG7 observation after both Stage 8 runtime blockers were narrowly remediated.  
**Authorization:** Founder explicitly authorized the **third Controlled MAG7 Observation**.  
**Execution worktree:** `F:\options-anomaly-scanner-stage8`  
**Branch:** `vnext/stage8-mag7-observation`  
**Base HEAD:** `3a63eaa1b9069d34199704fe31ac6466e8929d7d`  
**Runtime schema:** `20260818_0017`

---

# 0. Founder authorization

The Founder explicitly authorizes exactly one new production MAG7 scan invocation:

```text
FOUNDER_AUTHORIZATION=THIRD_CONTROLLED_MAG7_OBSERVATION_20260820

THIRD_MAG7_SCAN_INVOCATIONS_AUTHORIZED=1
UNIVERSE=MAG7_ONLY

EXPECTED_PAID_COST≈14
THIRD_SCAN_HARD_PAID_UNIT_CAP=20

PHASE2B_PAID_REFRESH_AUTHORIZED=NO
DEALER_GEX_LIVE_CALL_AUTHORIZED=NO
FOURTH_MAG7_SCAN_AUTHORIZED=NO
```

This authorization is exhausted after the first new MAG7 invocation whether it succeeds, produces zero candidates, becomes PARTIAL, or fails.

Do not retry automatically.

---

# 1. Accepted remediation prerequisites

Two Stage 8 blockers were already diagnosed and remediated.

## 1.1 S4 telemetry identifier remediation

Accepted state:

```text
OLD_STAGE_IDENTIFIER=S4_VNEXT_DEEP_DIVE_BUDGET_SELECTION
NEW_STAGE_IDENTIFIER=S4_VNEXT_DEEP_BUDGET_SELECTION

OLD_IDENTIFIER_LENGTH=35
NEW_IDENTIFIER_LENGTH=30

S4_IDENTIFIER_REMEDIATION=PASS
```

## 1.2 Post-candidate Deep-Dive PARTIAL remediation

Accepted state:

```text
STAGE8_POST_CANDIDATE_PARTIAL_REMEDIATION_RESULT=PASS
ROOT_CAUSE_ADDRESSED=YES

RUN_LEVEL_PARTIAL_FROM_POST_CANDIDATE_DEEP_DIVE_ONLY=BLOCKED
LEGITIMATE_PREEXISTING_PARTIAL_PRESERVED=YES

DEEP_DIVE_MISSING_STATE_PRESERVED=YES
MISSING_STRUCTURE_FABRICATED=NO

CANDIDATE_MATERIALIZATION_ELIGIBILITY_PRESERVED=YES
CANDIDATE_BEFORE_BUDGET_INVARIANT_PRESERVED=YES
S4_IDENTIFIER_REMEDIATION_PRESERVED=YES
```

Both accepted remediations are expected to remain in the current Stage 8 working tree.

Do not reset/stash/discard them.

---

# 2. Historical controlled runs remain immutable

Do not mutate either prior observation:

```text
FIRST_CONTROLLED_RUN_ID=090359ad-9d76-49b9-8902-f28ac54a1d1b
FIRST_CONTROLLED_RUN_STATUS=FAILED

SECOND_CONTROLLED_RUN_ID=e9267160-503a-41c7-9bb1-8cc2b2e3d8c6
SECOND_CONTROLLED_RUN_STATUS=PARTIAL
```

These are historical evidence.

---

# 3. Canonical evidence root

Canonical evidence directory:

```text
F:\options-anomaly-scanner\docs\evidence
```

If this exact execution package is attached and absent from the canonical root, save it byte-for-byte as:

```text
F:\options-anomaly-scanner\docs\evidence\NIGHTWATCH_VNEXT_THIRD_CONTROLLED_LIVE_MAG7_OBSERVATION_EXECUTION_PACKAGE_20260820.md
```

If that path already exists with different bytes, do not overwrite. Return:

```text
THIRD_CONTROLLED_OBSERVATION_RESULT=HOLD_PACKAGE_CONFLICT
```

and STOP.

Read completely from canonical full paths at minimum:

```text
F:\options-anomaly-scanner\docs\evidence\NIGHTWATCH_VNEXT_CANONICAL_EVIDENCE_MANIFEST.md

F:\options-anomaly-scanner\docs\evidence\NIGHTWATCH_SCANNER_VNEXT_INTEGRATED_SPEC_PROMPT_20260817(1).md

F:\options-anomaly-scanner\docs\evidence\NIGHTWATCH_VNEXT_STAGE5_PRODUCT_CANDIDATE_PERSISTENCE_COMPLETION_REPORT_20260818.md

F:\options-anomaly-scanner\docs\evidence\NIGHTWATCH_VNEXT_STAGE6_PHASE2B_BALANCED_MODEL_COMPLETION_REPORT_20260818.md

F:\options-anomaly-scanner\docs\evidence\NIGHTWATCH_VNEXT_STAGE6_BASELINE_CUTOFF_REMEDIATION_PASS_20260820.md

F:\options-anomaly-scanner\docs\evidence\NIGHTWATCH_VNEXT_STAGE7_CANDIDATE_FIRST_DASHBOARD_COMPLETION_REPORT_20260819.md

F:\options-anomaly-scanner\docs\evidence\NIGHTWATCH_VNEXT_STAGE8_MAG7_OBSERVATION_EXECUTION_PACKAGE_20260820.md

F:\options-anomaly-scanner\docs\evidence\NIGHTWATCH_VNEXT_STAGE8_S4_STAGE_IDENTIFIER_REMEDIATION_REPORT_20260820.md

F:\options-anomaly-scanner\docs\evidence\NIGHTWATCH_VNEXT_SECOND_CONTROLLED_LIVE_MAG7_OBSERVATION_REPORT_20260820.md

F:\options-anomaly-scanner\docs\evidence\NIGHTWATCH_VNEXT_STAGE8_PARTIAL_TERMINAL_STATE_DIAGNOSTIC_REPORT_20260820.md

F:\options-anomaly-scanner\docs\evidence\NIGHTWATCH_VNEXT_STAGE8_POST_CANDIDATE_DEEP_DIVE_PARTIAL_REMEDIATION_REPORT_20260820.md
```

Do not ask the Founder to re-upload files already available.

---

# 4. Code-state preflight — both remediations must be present

Before any paid request inspect:

```text
git rev-parse --abbrev-ref HEAD
git rev-parse HEAD
git status --short
git diff -- backend/app/scanner/v13.py
git diff -- backend/tests/test_stage4b_phase2a_vnext.py
git diff --check
```

Required:

```text
branch=vnext/stage8-mag7-observation
HEAD=3a63eaa1b9069d34199704fe31ac6466e8929d7d
```

The current working tree must contain both accepted remediations.

Verify:

```text
ACCEPTED_S4_REMEDIATION_PRESENT=YES
ACCEPTED_POST_CANDIDATE_PARTIAL_REMEDIATION_PRESENT=YES
UNEXPECTED_APPLICATION_DIFF_FOUND=NO
```

Specifically confirm:

```text
active S4 identifier = S4_VNEXT_DEEP_BUDGET_SELECTION
length <= 32
```

and confirm the vNext structure/deep-dive path no longer allows optional post-candidate structure unavailability to be the sole reason for run-level `PARTIAL`.

If either accepted remediation is absent, or unrelated application changes are present:

```text
THIRD_CONTROLLED_OBSERVATION_RESULT=HOLD_CODE_STATE_MISMATCH
```

STOP before any paid request.

Do not commit merely to execute this observation.

---

# 5. Runtime preflight

Read-only verify:

```text
REMOTE_ALEMBIC_HEAD=20260818_0017

PRODUCT_CANDIDATE_TABLE_PRESENT=YES
PRODUCT_CANDIDATE_TRIGGER_TABLE_PRESENT=YES
PRODUCT_CANDIDATE_CONTEXT_TABLE_PRESENT=YES
ANOMALY_CONTEXT_DETAIL_TABLE_PRESENT=YES
```

Also verify no currently running scanner run would conflict:

```text
RUNNING_SCAN_COUNT_BEFORE=
```

If runtime is not ready:

```text
THIRD_CONTROLLED_OBSERVATION_RESULT=HOLD_RUNTIME_NOT_READY
```

STOP.

Do not migrate, stamp, repair, or backfill.

---

# 6. Before-state isolation

Record read-only counts:

```text
scan_runs
scan_stages
product_candidates
product_candidate_triggers
product_candidate_contexts
anomaly_context_details
```

Keep both historical controlled run IDs separate from the new run.

No historical candidate backfill is authorized.

---

# 7. Cost / quota preflight

The first two controlled runs each consumed:

```text
14 paid units
```

The accepted remediations changed no vendor fan-out, retry logic, universe, or paid Phase2B behavior.

Before execution verify:

```text
VENDOR_FANOUT_CHANGED_BY_REMEDIATIONS=NO
RETRY_LOGIC_CHANGED_BY_REMEDIATIONS=NO
UNIVERSE_CHANGED_BY_REMEDIATIONS=NO
```

Prove:

```text
THIRD_SCAN_COST_BOUND_PROVEN=YES/NO
MAX_CONFIGURED_PAID_UNITS_FOR_THIRD_SCAN=
```

Required:

```text
MAX_CONFIGURED_PAID_UNITS_FOR_THIRD_SCAN<=20
```

If not provable:

```text
THIRD_CONTROLLED_OBSERVATION_RESULT=HOLD_BUDGET_BOUND_UNPROVEN
```

STOP before any paid request.

Record authoritative pre-scan usage/quota:

```text
PAID_UNITS_BEFORE_THIRD_SCAN=
QUOTA_REMAINING_BEFORE_THIRD_SCAN=
```

If unavailable, report `UNRESOLVED`; do not invent.

---

# 8. Execute exactly one third production MAG7 scan

After all preflight gates pass, execute exactly ONE existing production MAG7 scan invocation using:

```text
current remediated working-tree code
accepted MAG7 universe
accepted thresholds
accepted scoring
accepted retry behavior
```

Forbidden:

```text
fixture
threshold override
manual candidate seeding
universe expansion
second invocation
automatic retry
```

Return:

```text
THIRD_SCAN_INVOCATIONS_AUTHORIZED=1
ACTUAL_THIRD_SCAN_INVOCATIONS=

THIRD_SCAN_RUN_ID=
THIRD_SCAN_STARTED_AT=
THIRD_SCAN_COMPLETED_AT=
THIRD_SCAN_STATUS=
THIRD_SCAN_SAFE_ERROR=
```

Preserve the actual terminal state truthfully.

---

# 9. Runtime proof of both remediations

## 9.1 S4 identifier

If the run reaches S4, verify persisted stage:

```text
S4_VNEXT_DEEP_BUDGET_SELECTION
```

Return:

```text
THIRD_RUN_S4_STAGE_ROW_PRESENT=YES/NO/NOT_REACHED
THIRD_RUN_S4_STAGE_IDENTIFIER=
THIRD_RUN_S4_STAGE_IDENTIFIER_LENGTH=
S4_LENGTH_DATAERROR_RECURRED=YES/NO
```

## 9.2 Post-candidate Deep-Dive PARTIAL semantics

Inspect structure/deep-dive availability for the third run.

If one or more selected Deep-Dive expiries lack complete daily-chain archive, preserve that state truthfully.

Return:

```text
THIRD_RUN_MISSING_DEEP_DIVE_STRUCTURE_COUNT=
THIRD_RUN_MISSING_DEEP_DIVE_STRUCTURE_ITEMS=
```

Then determine:

```text
POST_CANDIDATE_DEEP_DIVE_ONLY_CAUSED_RUN_PARTIAL=YES/NO/NOT_APPLICABLE
```

Required:

```text
POST_CANDIDATE_DEEP_DIVE_ONLY_CAUSED_RUN_PARTIAL=NO
```

If the same confirmed defect recurs:

```text
THIRD_CONTROLLED_OBSERVATION_RESULT=FAIL_POST_CANDIDATE_PARTIAL_REMEDIATION_RUNTIME
```

Do not retry.

If run becomes PARTIAL/FAILED for another reason, preserve it and return:

```text
THIRD_CONTROLLED_OBSERVATION_RESULT=FAIL_SCAN_NEW_DEFECT
```

Do not diagnose or repair the new reason within this task.

---

# 10. ProductCandidate verification

If the run reaches an accepted successful materialization path, read back only ProductCandidates linked to the new third ScanRun.

Return:

```text
NEW_PRODUCT_CANDIDATE_COUNT=
NEW_PRODUCT_CANDIDATE_TRIGGER_COUNT=
```

For each candidate verify:

```text
ticker
candidate_first_knowledge_at
materialization rule version/hash
trigger count
qualifying trigger count
supporting trigger count
trigger families
```

Verify:

```text
candidate first knowledge immutable
trigger identities persisted
full active anomaly pool preserved
Deep-Dive budget did not suppress ProductCandidate existence
Deep-Dive structure availability did not suppress ProductCandidate existence
```

Return:

```text
VALID_CANDIDATE_OMISSION_FOUND=YES/NO
DEEP_DIVE_BUDGET_SUPPRESSION_FOUND=YES/NO
DEEP_DIVE_AVAILABILITY_SUPPRESSION_FOUND=YES/NO
```

If successful run legitimately has zero candidates:

```text
NEW_PRODUCT_CANDIDATE_COUNT=0
```

Do not manufacture candidates.

---

# 11. Create FIRST_KNOWLEDGE_BASELINE only

For every new ProductCandidate from the third run, create exactly one accepted:

```text
FIRST_KNOWLEDGE_BASELINE
```

using the accepted Stage 6 baseline service.

Authorized because this baseline path must use no paid Phase2B refresh.

Evidence cutoff:

```text
candidate_first_knowledge_at
```

Forbidden:

```text
REFRESH
daily_ohlc paid refresh
stock_state paid refresh
iv_rank paid refresh
term_structure paid refresh
live Dealer/GEX
```

Missing/non-knowable context remains:

```text
PARTIAL
UNAVAILABLE
NOT_YET_AVAILABLE
NULL
```

Do not backfill future information.

If baseline creation fails:

```text
THIRD_CONTROLLED_OBSERVATION_RESULT=FAIL_BASELINE_CREATION
```

No retry.

---

# 12. Baseline integrity

For each created baseline verify:

```text
evaluation_kind=FIRST_KNOWLEDGE_BASELINE
context_evaluated_at >= candidate_first_knowledge_at
trigger/detail set matches candidate trigger set
```

Verify all accepted source-specific information-time cutoffs.

Return:

```text
BASELINE_COUNT=
BASELINE_LOOKAHEAD_FOUND=YES/NO
BASELINE_TRIGGER_SET_DRIFT_FOUND=YES/NO
BASELINE_SOURCE_TIME_VIOLATION_FOUND=YES/NO
```

Any `YES`:

```text
THIRD_CONTROLLED_OBSERVATION_RESULT=FAIL_BASELINE_INTEGRITY
```

Do not repair.

---

# 13. Explicit paid refresh prohibition

Verify:

```text
PHASE2B_REFRESH_CALLS=0
DEALER_GEX_LIVE_CALLS=0
DEALER_GEX_SOURCE=ARCHIVE_ONLY
```

---

# 14. Post-scan cost verification

Record:

```text
PAID_UNITS_AFTER_THIRD_SCAN=
QUOTA_REMAINING_AFTER_THIRD_SCAN=
THIRD_SCAN_OBSERVED_PAID_UNIT_DELTA=
```

Required:

```text
THIRD_SCAN_OBSERVED_PAID_UNIT_DELTA<=20
```

If exceeded:

```text
THIRD_CONTROLLED_OBSERVATION_RESULT=FAIL_COST_CAP_EXCEEDED
```

No fourth scan.

Also report:

```text
FIRST_CONTROLLED_SCAN_PAID_UNITS=14
SECOND_CONTROLLED_SCAN_PAID_UNITS=14
THIRD_CONTROLLED_SCAN_PAID_UNITS=
CUMULATIVE_CONTROLLED_SCAN_PAID_UNITS=
```

---

# 15. Runtime delta evidence

Record exact new rows attributable to the third run:

```text
SCAN_RUN_ROWS_ADDED_BY_THIRD_OBSERVATION=
PRODUCT_CANDIDATE_ROWS_ADDED_BY_THIRD_OBSERVATION=
TRIGGER_ROWS_ADDED_BY_THIRD_OBSERVATION=
BASELINE_CONTEXT_ROWS_ADDED_BY_THIRD_OBSERVATION=
ANOMALY_DETAIL_ROWS_ADDED_BY_THIRD_OBSERVATION=
```

Do not attribute concurrent unrelated writes.

---

# 16. Result states

Use exactly one:

```text
THIRD_CONTROLLED_OBSERVATION_RESULT=PASS_WITH_CANDIDATES
THIRD_CONTROLLED_OBSERVATION_RESULT=PASS_NO_CANDIDATE

THIRD_CONTROLLED_OBSERVATION_RESULT=FAIL_POST_CANDIDATE_PARTIAL_REMEDIATION_RUNTIME
THIRD_CONTROLLED_OBSERVATION_RESULT=FAIL_S4_REMEDIATION_RUNTIME
THIRD_CONTROLLED_OBSERVATION_RESULT=FAIL_SCAN_NEW_DEFECT
THIRD_CONTROLLED_OBSERVATION_RESULT=FAIL_BASELINE_CREATION
THIRD_CONTROLLED_OBSERVATION_RESULT=FAIL_BASELINE_INTEGRITY
THIRD_CONTROLLED_OBSERVATION_RESULT=FAIL_COST_CAP_EXCEEDED

THIRD_CONTROLLED_OBSERVATION_RESULT=HOLD_CODE_STATE_MISMATCH
THIRD_CONTROLLED_OBSERVATION_RESULT=HOLD_RUNTIME_NOT_READY
THIRD_CONTROLLED_OBSERVATION_RESULT=HOLD_BUDGET_BOUND_UNPROVEN
THIRD_CONTROLLED_OBSERVATION_RESULT=HOLD_PACKAGE_CONFLICT
THIRD_CONTROLLED_OBSERVATION_RESULT=HOLD_REPORT_CONFLICT
```

Do not broaden these categories ad hoc.

---

# 17. Evidence report — primary + canonical backup

Create primary:

```text
F:\options-anomaly-scanner-stage8\docs\evidence\stage8\NIGHTWATCH_VNEXT_THIRD_CONTROLLED_LIVE_MAG7_OBSERVATION_REPORT_20260820.md
```

Also save byte-identical canonical backup:

```text
F:\options-anomaly-scanner\docs\evidence\NIGHTWATCH_VNEXT_THIRD_CONTROLLED_LIVE_MAG7_OBSERVATION_REPORT_20260820.md
```

Requirements:

- primary and canonical report byte-identical;
- verify SHA-256 of both;
- if canonical file exists with identical bytes, keep it;
- if same filename exists with different content, do not overwrite;
- return `HOLD_REPORT_CONFLICT` on conflict.

---

# 18. Required final fields

Return:

```text
THIRD_CONTROLLED_OBSERVATION_RESULT=

FOUNDER_AUTHORIZATION=THIRD_CONTROLLED_MAG7_OBSERVATION_20260820

THIRD_SCAN_INVOCATIONS_AUTHORIZED=1
ACTUAL_THIRD_SCAN_INVOCATIONS=

THIRD_SCAN_RUN_ID=
THIRD_SCAN_STATUS=
THIRD_SCAN_SAFE_ERROR=
THIRD_SCAN_STARTED_AT=
THIRD_SCAN_COMPLETED_AT=

ACCEPTED_S4_REMEDIATION_PRESENT=
ACCEPTED_POST_CANDIDATE_PARTIAL_REMEDIATION_PRESENT=

THIRD_RUN_S4_STAGE_ROW_PRESENT=
THIRD_RUN_S4_STAGE_IDENTIFIER=
THIRD_RUN_S4_STAGE_IDENTIFIER_LENGTH=
S4_LENGTH_DATAERROR_RECURRED=

THIRD_RUN_MISSING_DEEP_DIVE_STRUCTURE_COUNT=
POST_CANDIDATE_DEEP_DIVE_ONLY_CAUSED_RUN_PARTIAL=

THIRD_SCAN_COST_BOUND_PROVEN=
MAX_CONFIGURED_PAID_UNITS_FOR_THIRD_SCAN=

PAID_UNITS_BEFORE_THIRD_SCAN=
PAID_UNITS_AFTER_THIRD_SCAN=
THIRD_SCAN_OBSERVED_PAID_UNIT_DELTA=
QUOTA_REMAINING_BEFORE_THIRD_SCAN=
QUOTA_REMAINING_AFTER_THIRD_SCAN=

FIRST_CONTROLLED_SCAN_PAID_UNITS=14
SECOND_CONTROLLED_SCAN_PAID_UNITS=14
THIRD_CONTROLLED_SCAN_PAID_UNITS=
CUMULATIVE_CONTROLLED_SCAN_PAID_UNITS=

NEW_PRODUCT_CANDIDATE_COUNT=
NEW_PRODUCT_CANDIDATE_TRIGGER_COUNT=

VALID_CANDIDATE_OMISSION_FOUND=
DEEP_DIVE_BUDGET_SUPPRESSION_FOUND=
DEEP_DIVE_AVAILABILITY_SUPPRESSION_FOUND=

BASELINE_COUNT=
BASELINE_LOOKAHEAD_FOUND=
BASELINE_TRIGGER_SET_DRIFT_FOUND=
BASELINE_SOURCE_TIME_VIOLATION_FOUND=

PHASE2B_REFRESH_CALLS=0
DEALER_GEX_LIVE_CALLS=0

REMOTE_ALEMBIC_HEAD=20260818_0017
REMOTE_MIGRATIONS_RUN=0

APPLICATION_CODE_CHANGES_DURING_THIRD_OBSERVATION=0
TEST_CODE_CHANGES_DURING_THIRD_OBSERVATION=0
MIGRATION_FILES_CHANGED_DURING_THIRD_OBSERVATION=0
WORKFLOW_CHANGES=0
SCHEDULER_CHANGES=0

MAG7_SCAN_INVOCATIONS_THIS_TASK=
NIGHTWATCH_REQUESTS_THIS_TASK=
PAID_UNITS_THIS_TASK=

REMOTE_DB_SCHEMA_WRITES=0
REMOTE_APPLICATION_DATA_WRITES=AUTHORIZED_THIRD_CONTROLLED_OBSERVATION_ONLY

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

Expected after:

```text
PASS_WITH_CANDIDATES
or
PASS_NO_CANDIDATE
```

is:

```text
STAGE8_OBSERVATION_RESUME_READY=YES
```

Do not automatically proceed to broader Stage 8 analysis.

Do not run a fourth MAG7 scan.

Do not start Stage 9.

STOP.

---

# 19. Carried ledger

Preserve:

```text
CURRENT_TRIGGER_FRESHNESS_MODE=CALIBRATION_REQUIRED
RADAR_OI_SCHEDULE_ACTIVATION=PENDING_ROLLOVER_EVIDENCE
CROSS_RUN_CANDIDATE_LIFECYCLE=DEFERRED_NO_AUTO_MERGE
IV_RANK_CORE_ELIGIBILITY=WITHHOLD_PENDING_PROVENANCE
ISOLATED_POSTGRES_RUNTIME_VERIFIED=NO
N1_HISTORICAL_RUNTIME_DISTRIBUTION_VERIFIED=NO
```

Do not resolve these through this one observation.

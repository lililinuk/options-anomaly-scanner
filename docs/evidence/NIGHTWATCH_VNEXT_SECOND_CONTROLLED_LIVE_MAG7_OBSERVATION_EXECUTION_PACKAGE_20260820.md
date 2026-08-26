# Nightwatch vNext — Second Controlled Live MAG7 Observation — Execution Package

**Date:** 2026-08-20  
**Purpose:** Generate one new genuine vNext MAG7 runtime observation after the confirmed S4 telemetry identifier defect was remediated.  
**Authorization:** Founder explicitly authorized a **second Controlled MAG7 Observation**.  
**Execution worktree:** `F:\options-anomaly-scanner-stage8`  
**Branch:** `vnext/stage8-mag7-observation`  
**Base HEAD:** `3a63eaa1b9069d34199704fe31ac6466e8929d7d`  
**Runtime schema:** `20260818_0017`

---

# 0. Founder Authorization

The first Controlled MAG7 Observation authorization was consumed and ended in a truthful failed run.

The Founder now explicitly authorizes exactly one new scan invocation:

```text
FOUNDER_AUTHORIZATION=SECOND_CONTROLLED_MAG7_OBSERVATION_20260820

SECOND_MAG7_SCAN_INVOCATIONS_AUTHORIZED=1
UNIVERSE=MAG7_ONLY

EXPECTED_PAID_COST≈14
SECOND_SCAN_HARD_PAID_UNIT_CAP=20

PHASE2B_PAID_REFRESH_AUTHORIZED=NO
DEALER_GEX_LIVE_CALL_AUTHORIZED=NO
THIRD_MAG7_SCAN_AUTHORIZED=NO
```

This second authorization is exhausted after the first new MAG7 scan invocation, whether it succeeds, returns no candidates, or fails.

Do not automatically retry.

---

# 1. Accepted remediation prerequisite

The Stage 8 S4 remediation is accepted:

```text
STAGE8_S4_REMEDIATION_RESULT=PASS

OLD_STAGE_IDENTIFIER=S4_VNEXT_DEEP_DIVE_BUDGET_SELECTION
NEW_STAGE_IDENTIFIER=S4_VNEXT_DEEP_BUDGET_SELECTION

OLD_IDENTIFIER_LENGTH=35
NEW_IDENTIFIER_LENGTH=30

ACTIVE_STAGE_IDENTIFIER_LENGTHS_VALID=YES
DATAERROR_REPRODUCTION_AFTER_FIX=NO

MIGRATION_CREATED=NO
ALEMBIC_HEAD=20260818_0017
```

The remediation changed only:

```text
backend/app/scanner/v13.py
backend/tests/test_stage4b_phase2a_vnext.py
```

and full backend verification passed.

The original failed run must remain untouched:

```text
SCAN_RUN_ID=090359ad-9d76-49b9-8902-f28ac54a1d1b
STATUS=FAILED
PRODUCT_CANDIDATE_ROWS=0
FIRST_KNOWLEDGE_BASELINE_ROWS=0
```

Do not repair, reuse, or relabel that failed run.

---

# 2. Canonical evidence root

Canonical evidence directory:

```text
F:\options-anomaly-scanner\docs\evidence
```

Preserve this exact package there as:

```text
F:\options-anomaly-scanner\docs\evidence\NIGHTWATCH_VNEXT_SECOND_CONTROLLED_LIVE_MAG7_OBSERVATION_EXECUTION_PACKAGE_20260820.md
```

If this exact package is supplied as a thread attachment and the canonical target is absent, copy it byte-for-byte.

If the target exists with different content, do not overwrite it. Return:

```text
SECOND_CONTROLLED_OBSERVATION_RESULT=HOLD_PACKAGE_CONFLICT
```

and STOP.

Read completely from canonical full paths:

```text
F:\options-anomaly-scanner\docs\evidence\NIGHTWATCH_VNEXT_CANONICAL_EVIDENCE_MANIFEST.md

F:\options-anomaly-scanner\docs\evidence\NIGHTWATCH_SCANNER_VNEXT_INTEGRATED_SPEC_PROMPT_20260817(1).md

F:\options-anomaly-scanner\docs\evidence\NIGHTWATCH_VNEXT_STAGE5_PRODUCT_CANDIDATE_PERSISTENCE_COMPLETION_REPORT_20260818.md

F:\options-anomaly-scanner\docs\evidence\NIGHTWATCH_VNEXT_STAGE6_PHASE2B_BALANCED_MODEL_COMPLETION_REPORT_20260818.md

F:\options-anomaly-scanner\docs\evidence\NIGHTWATCH_VNEXT_STAGE6_BASELINE_CUTOFF_REMEDIATION_PASS_20260820.md

F:\options-anomaly-scanner\docs\evidence\NIGHTWATCH_VNEXT_STAGE7_CANDIDATE_FIRST_DASHBOARD_COMPLETION_REPORT_20260819.md

F:\options-anomaly-scanner\docs\evidence\NIGHTWATCH_VNEXT_STAGE8_MAG7_OBSERVATION_EXECUTION_PACKAGE_20260820.md

F:\options-anomaly-scanner\docs\evidence\NIGHTWATCH_VNEXT_STAGE8_RUNTIME_DEPLOYMENT_GATE_EXECUTION_PACKAGE_20260820.md

F:\options-anomaly-scanner\docs\evidence\NIGHTWATCH_VNEXT_CONTROLLED_LIVE_MAG7_OBSERVATION_EXECUTION_PACKAGE_20260820.md

F:\options-anomaly-scanner\docs\evidence\NIGHTWATCH_VNEXT_STAGE8_FAILED_SCAN_ROOT_CAUSE_DIAGNOSTIC_REPORT_20260820.md

F:\options-anomaly-scanner\docs\evidence\NIGHTWATCH_VNEXT_STAGE8_S4_STAGE_IDENTIFIER_REMEDIATION_REPORT_20260820.md
```

Also read from the Stage 8 worktree:

```text
F:\options-anomaly-scanner-stage8\docs\evidence\stage8\NIGHTWATCH_VNEXT_STAGE8_RUNTIME_DEPLOYMENT_GATE_REPORT_20260820.md

F:\options-anomaly-scanner-stage8\docs\evidence\stage8\NIGHTWATCH_VNEXT_CONTROLLED_LIVE_MAG7_OBSERVATION_REPORT_20260820.md

F:\options-anomaly-scanner-stage8\docs\evidence\stage8\NIGHTWATCH_VNEXT_STAGE8_FAILED_SCAN_ROOT_CAUSE_DIAGNOSTIC_REPORT_20260820.md

F:\options-anomaly-scanner-stage8\docs\evidence\stage8\NIGHTWATCH_VNEXT_STAGE8_S4_STAGE_IDENTIFIER_REMEDIATION_REPORT_20260820.md
```

Do not ask the Founder to re-upload files already available at these paths.

---

# 3. Preflight — exact remediated code must be used

Before any paid request, inspect:

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

The working tree must contain the accepted remediation:

```text
S4_VNEXT_DEEP_BUDGET_SELECTION
```

and must NOT contain the old active call-site identifier:

```text
S4_VNEXT_DEEP_DIVE_BUDGET_SELECTION
```

Only the accepted remediation code/test changes and Stage 8 evidence artifacts may be dirty/untracked.

Return:

```text
ACCEPTED_S4_REMEDIATION_PRESENT=YES/NO
UNEXPECTED_APPLICATION_DIFF_FOUND=YES/NO
```

If remediation is absent or unrelated application changes are present:

```text
SECOND_CONTROLLED_OBSERVATION_RESULT=HOLD_CODE_STATE_MISMATCH
```

STOP.

Do not commit the remediation merely to execute this observation.

---

# 4. Runtime preflight

Read-only verify:

```text
REMOTE_ALEMBIC_HEAD=20260818_0017

PRODUCT_CANDIDATE_TABLE_PRESENT=YES
PRODUCT_CANDIDATE_TRIGGER_TABLE_PRESENT=YES
PRODUCT_CANDIDATE_CONTEXT_TABLE_PRESENT=YES
ANOMALY_CONTEXT_DETAIL_TABLE_PRESENT=YES
```

If not:

```text
SECOND_CONTROLLED_OBSERVATION_RESULT=HOLD_RUNTIME_NOT_READY
```

STOP.

Do not migrate, stamp, repair, or backfill.

---

# 5. Before-state isolation

Before the second scan, record read-only counts for:

```text
scan_runs
product_candidates
product_candidate_triggers
product_candidate_contexts
anomaly_context_details
```

Also identify the prior failed run separately so it cannot be confused with the new run.

Return:

```text
PRIOR_FAILED_SCAN_RUN_ID=090359ad-9d76-49b9-8902-f28ac54a1d1b
PRIOR_FAILED_RUN_STATUS=FAILED
```

Do not count prior failed-run evidence as part of the new observation.

---

# 6. Cost / quota preflight

The first controlled run proved the existing MAG7 path used:

```text
NIGHTWATCH_REQUESTS=14
PAID_UNITS=14
```

The accepted remediation changed only the S4 telemetry identifier and a regression test, not vendor fan-out or retry logic.

Before the second scan, verify this remains true in the current code:

```text
VENDOR_FANOUT_CHANGED_BY_REMEDIATION=NO
RETRY_LOGIC_CHANGED_BY_REMEDIATION=NO
```

Prove the current one-scan maximum is bounded:

```text
SECOND_SCAN_COST_BOUND_PROVEN=YES/NO
MAX_CONFIGURED_PAID_UNITS_FOR_SECOND_SCAN=
```

Required:

```text
MAX_CONFIGURED_PAID_UNITS_FOR_SECOND_SCAN<=20
```

If not provable:

```text
SECOND_CONTROLLED_OBSERVATION_RESULT=HOLD_BUDGET_BOUND_UNPROVEN
```

STOP before any paid call.

Record authoritative local/runtime pre-scan usage facts where available:

```text
PAID_UNITS_BEFORE_SECOND_SCAN=
QUOTA_REMAINING_BEFORE_SECOND_SCAN=
```

Unknown remains `UNRESOLVED`.

---

# 7. Execute exactly one second MAG7 scan

After all gates pass, execute exactly one existing production MAG7 scan invocation using:

```text
current remediated working-tree code
accepted MAG7 universe
accepted thresholds
accepted scoring
accepted retry behavior
```

Do not run a fixture.

Do not change thresholds.

Do not expand the universe.

Do not manually seed evidence.

Do not run a third scan.

Return:

```text
SECOND_SCAN_INVOCATIONS_AUTHORIZED=1
ACTUAL_SECOND_SCAN_INVOCATIONS=

SECOND_SCAN_RUN_ID=
SECOND_SCAN_STARTED_AT=
SECOND_SCAN_COMPLETED_AT=
SECOND_SCAN_STATUS=
```

Truthfully preserve:

```text
SUCCESS_WITH_CANDIDATES
SUCCESS_NO_CANDIDATE
FAILED
```

If failed, do not retry.

---

# 8. S4 remediation runtime proof

For the new second ScanRun, inspect persisted `scan_stages`.

Expected if execution reaches S4:

```text
stage=S4_VNEXT_DEEP_BUDGET_SELECTION
```

and no length-related `DataError`.

Return:

```text
NEW_S4_STAGE_ROW_PRESENT=YES/NO/NOT_REACHED
NEW_S4_STAGE_IDENTIFIER=
NEW_S4_STAGE_IDENTIFIER_LENGTH=
S4_LENGTH_DATAERROR_RECURRED=YES/NO
```

If the exact old length defect recurs:

```text
SECOND_CONTROLLED_OBSERVATION_RESULT=FAIL_S4_REMEDIATION_RUNTIME
```

Do not run another scan.

If another unrelated failure occurs later, preserve it truthfully as `FAIL_SCAN_NEW_DEFECT` and record the safe error/stage. Do not diagnose or fix it in this task.

---

# 9. ProductCandidate verification

If:

```text
SECOND_SCAN_STATUS=SUCCESS_WITH_CANDIDATES
```

read back only ProductCandidates linked to the new second ScanRun.

For each candidate report:

```text
ProductCandidate.id
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
Deep-Dive budget did not suppress candidate existence
```

Return:

```text
NEW_PRODUCT_CANDIDATE_COUNT=
NEW_PRODUCT_CANDIDATE_TRIGGER_COUNT=
VALID_CANDIDATE_OMISSION_FOUND=YES/NO
DEEP_DIVE_BUDGET_SUPPRESSION_FOUND=YES/NO
```

If:

```text
SECOND_SCAN_STATUS=SUCCESS_NO_CANDIDATE
```

expected:

```text
NEW_PRODUCT_CANDIDATE_COUNT=0
```

Do not manufacture candidates.

---

# 10. Create FIRST_KNOWLEDGE_BASELINE only

For each new ProductCandidate created by this second scan, create exactly one accepted Stage 6:

```text
FIRST_KNOWLEDGE_BASELINE
```

using the accepted baseline service.

This is authorized because baseline creation uses no paid Stage 6 refresh calls.

Required evidence cutoff:

```text
candidate_first_knowledge_at
```

Do NOT run:

```text
REFRESH
daily_ohlc paid refresh
stock_state paid refresh
iv_rank paid refresh
term_structure paid refresh
live Dealer/GEX
```

If source context was not knowable by first knowledge, preserve truthful:

```text
PARTIAL
UNAVAILABLE
NOT_YET_AVAILABLE
NULL
```

Do not backfill later information.

If baseline creation fails:

```text
SECOND_CONTROLLED_OBSERVATION_RESULT=FAIL_BASELINE_CREATION
```

Do not run another scan or manually repair.

---

# 11. Baseline integrity verification

For every created baseline verify:

```text
evaluation_kind=FIRST_KNOWLEDGE_BASELINE
product_candidate_id matches
context_evaluated_at >= candidate_first_knowledge_at
trigger/detail set matches candidate trigger set
```

Verify source time eligibility:

```text
source receipt/capture/as-of <= candidate_first_knowledge_at
```

under the accepted source-specific Stage 6 rules.

For OHLC:

```text
payload/source knowable by cutoff
bar trading_date <= cutoff NY trading date
malformed/missing bar date fails closed
```

For chain:

```text
source receipt <= cutoff
vendor observation/OI as-of <= cutoff when known
quote_as_of <= cutoff when known
```

For Dealer/GEX:

```text
captured_at <= cutoff
vendor_observed_at <= cutoff
```

Return:

```text
BASELINE_COUNT=
BASELINE_LOOKAHEAD_FOUND=YES/NO
BASELINE_TRIGGER_SET_DRIFT_FOUND=YES/NO
BASELINE_SOURCE_TIME_VIOLATION_FOUND=YES/NO
```

Any `YES` results in:

```text
SECOND_CONTROLLED_OBSERVATION_RESULT=FAIL_BASELINE_INTEGRITY
```

Do not fix it.

---

# 12. Explicit refresh / GEX prohibition

Verify:

```text
PHASE2B_REFRESH_CALLS=0
DEALER_GEX_LIVE_CALLS=0
DEALER_GEX_SOURCE=ARCHIVE_ONLY
```

No page-load auto refresh.

---

# 13. Post-scan cost verification

After the one second scan invocation and any authorized zero-paid baseline creation, record:

```text
PAID_UNITS_AFTER_SECOND_SCAN=
QUOTA_REMAINING_AFTER_SECOND_SCAN=
SECOND_SCAN_OBSERVED_PAID_UNIT_DELTA=
```

Use authoritative usage facts only.

Required:

```text
SECOND_SCAN_OBSERVED_PAID_UNIT_DELTA<=20
```

If greater than 20:

```text
SECOND_CONTROLLED_OBSERVATION_RESULT=FAIL_COST_CAP_EXCEEDED
```

No third scan.

Also report cumulative Stage 8 controlled-scan vendor cost if authoritative:

```text
FIRST_CONTROLLED_SCAN_PAID_UNITS=14
SECOND_CONTROLLED_SCAN_PAID_UNITS=
CUMULATIVE_CONTROLLED_SCAN_PAID_UNITS=
```

This cumulative value is accounting only; the hard cap applies to the newly authorized second scan separately.

---

# 14. Runtime delta evidence

Record the exact new rows attributable to the second ScanRun/candidates:

```text
SCAN_RUN_ROWS_ADDED_BY_SECOND_OBSERVATION=
PRODUCT_CANDIDATE_ROWS_ADDED_BY_SECOND_OBSERVATION=
TRIGGER_ROWS_ADDED_BY_SECOND_OBSERVATION=
BASELINE_CONTEXT_ROWS_ADDED_BY_SECOND_OBSERVATION=
ANOMALY_DETAIL_ROWS_ADDED_BY_SECOND_OBSERVATION=
```

Do not attribute concurrent unrelated rows.

---

# 15. Result states

Use exactly one:

```text
SECOND_CONTROLLED_OBSERVATION_RESULT=PASS_WITH_CANDIDATES
SECOND_CONTROLLED_OBSERVATION_RESULT=PASS_NO_CANDIDATE

SECOND_CONTROLLED_OBSERVATION_RESULT=FAIL_SCAN_NEW_DEFECT
SECOND_CONTROLLED_OBSERVATION_RESULT=FAIL_S4_REMEDIATION_RUNTIME
SECOND_CONTROLLED_OBSERVATION_RESULT=FAIL_BASELINE_CREATION
SECOND_CONTROLLED_OBSERVATION_RESULT=FAIL_BASELINE_INTEGRITY
SECOND_CONTROLLED_OBSERVATION_RESULT=FAIL_COST_CAP_EXCEEDED

SECOND_CONTROLLED_OBSERVATION_RESULT=HOLD_CODE_STATE_MISMATCH
SECOND_CONTROLLED_OBSERVATION_RESULT=HOLD_RUNTIME_NOT_READY
SECOND_CONTROLLED_OBSERVATION_RESULT=HOLD_BUDGET_BOUND_UNPROVEN
SECOND_CONTROLLED_OBSERVATION_RESULT=HOLD_PACKAGE_CONFLICT
```

If the scan fails for a new reason, do not diagnose or remediate within this task.

---

# 16. Evidence report — primary + canonical backup

Create the primary report:

```text
F:\options-anomaly-scanner-stage8\docs\evidence\stage8\NIGHTWATCH_VNEXT_SECOND_CONTROLLED_LIVE_MAG7_OBSERVATION_REPORT_20260820.md
```

Also save a byte-identical canonical backup:

```text
F:\options-anomaly-scanner\docs\evidence\NIGHTWATCH_VNEXT_SECOND_CONTROLLED_LIVE_MAG7_OBSERVATION_REPORT_20260820.md
```

Requirements:

- primary and canonical report must be byte-identical;
- verify SHA-256 for both;
- if canonical target exists with identical bytes, keep it;
- if same filename exists with different content, do not overwrite;
- conflict result is `HOLD_REPORT_CONFLICT`;
- do not overwrite any other evidence file.

Return:

```text
PRIMARY_REPORT_PATH=
CANONICAL_REPORT_PATH=
PRIMARY_REPORT_SHA256=
CANONICAL_REPORT_SHA256=
REPORT_BACKUP_BYTE_IDENTICAL=YES/NO
```

---

# 17. Required final fields

Return:

```text
SECOND_CONTROLLED_OBSERVATION_RESULT=

FOUNDER_AUTHORIZATION=SECOND_CONTROLLED_MAG7_OBSERVATION_20260820

SECOND_SCAN_INVOCATIONS_AUTHORIZED=1
ACTUAL_SECOND_SCAN_INVOCATIONS=

SECOND_SCAN_RUN_ID=
SECOND_SCAN_STATUS=
SECOND_SCAN_STARTED_AT=
SECOND_SCAN_COMPLETED_AT=

ACCEPTED_S4_REMEDIATION_PRESENT=
NEW_S4_STAGE_ROW_PRESENT=
NEW_S4_STAGE_IDENTIFIER=
NEW_S4_STAGE_IDENTIFIER_LENGTH=
S4_LENGTH_DATAERROR_RECURRED=

SECOND_SCAN_COST_BOUND_PROVEN=
MAX_CONFIGURED_PAID_UNITS_FOR_SECOND_SCAN=

PAID_UNITS_BEFORE_SECOND_SCAN=
PAID_UNITS_AFTER_SECOND_SCAN=
SECOND_SCAN_OBSERVED_PAID_UNIT_DELTA=
QUOTA_REMAINING_BEFORE_SECOND_SCAN=
QUOTA_REMAINING_AFTER_SECOND_SCAN=

FIRST_CONTROLLED_SCAN_PAID_UNITS=14
SECOND_CONTROLLED_SCAN_PAID_UNITS=
CUMULATIVE_CONTROLLED_SCAN_PAID_UNITS=

NEW_PRODUCT_CANDIDATE_COUNT=
NEW_PRODUCT_CANDIDATE_TRIGGER_COUNT=

BASELINE_COUNT=
BASELINE_LOOKAHEAD_FOUND=
BASELINE_TRIGGER_SET_DRIFT_FOUND=
BASELINE_SOURCE_TIME_VIOLATION_FOUND=

VALID_CANDIDATE_OMISSION_FOUND=
DEEP_DIVE_BUDGET_SUPPRESSION_FOUND=

PHASE2B_REFRESH_CALLS=0
DEALER_GEX_LIVE_CALLS=0

REMOTE_ALEMBIC_HEAD=20260818_0017
REMOTE_MIGRATIONS_RUN=0
```

Authorization ledger:

```text
APPLICATION_CODE_CHANGES_DURING_SECOND_OBSERVATION=0
TEST_CODE_CHANGES_DURING_SECOND_OBSERVATION=0
MIGRATION_FILES_CHANGED_DURING_SECOND_OBSERVATION=0
WORKFLOW_CHANGES=0
SCHEDULER_CHANGES=0

MAG7_SCAN_INVOCATIONS_THIS_TASK=
NIGHTWATCH_REQUESTS_THIS_TASK=
PAID_UNITS_THIS_TASK=

REMOTE_DB_SCHEMA_WRITES=0
REMOTE_APPLICATION_DATA_WRITES=AUTHORIZED_SECOND_CONTROLLED_OBSERVATION_ONLY

COMMITS_CREATED=0
PUSHES=0
PRS_CREATED=0
MERGES=0

PRIMARY_REPORT_PATH=
CANONICAL_REPORT_PATH=
REPORT_BACKUP_BYTE_IDENTICAL=
```

Then:

```text
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

Do not automatically resume broader Stage 8 analysis.

Do not run a third MAG7 scan.

Do not start Stage 9.

STOP.

---

# 18. Carried ledger

Preserve:

```text
CURRENT_TRIGGER_FRESHNESS_MODE=CALIBRATION_REQUIRED
RADAR_OI_SCHEDULE_ACTIVATION=PENDING_ROLLOVER_EVIDENCE
CROSS_RUN_CANDIDATE_LIFECYCLE=DEFERRED_NO_AUTO_MERGE
IV_RANK_CORE_ELIGIBILITY=WITHHOLD_PENDING_PROVENANCE
ISOLATED_POSTGRES_RUNTIME_VERIFIED=NO
N1_HISTORICAL_RUNTIME_DISTRIBUTION_VERIFIED=NO
```

Do not resolve any of these through this single observation.

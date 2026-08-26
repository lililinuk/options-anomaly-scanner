# Nightwatch vNext — Stage 8 PARTIAL Terminal-State Diagnostic — Execution Package

**Date:** 2026-08-20  
**Purpose:** Diagnose why the second controlled MAG7 run completed persisted stages through S6 but terminated with `ScanRun.status=PARTIAL`, preventing ProductCandidate materialization.  
**Authorization:** Read-only / zero-paid diagnostic only.  
**Worktree:** `F:\options-anomaly-scanner-stage8`  
**Branch:** `vnext/stage8-mag7-observation`

## Trigger

Second controlled run:

```text
SECOND_SCAN_RUN_ID=e9267160-503a-41c7-9bb1-8cc2b2e3d8c6
SECOND_SCAN_STATUS=PARTIAL
SECOND_SCAN_SAFE_ERROR=NONE
LAST_PERSISTED_STAGE=S6_POSITIONING_SUMMARY_V12

S0_PREFLIGHT_V11=COMPLETE
S2_ACTIVITY_SURFACE_V12=COMPLETE
S3_DISCOVERY_CONFIRMATION=COMPLETE
S3_VNEXT_ACTIVE_DISCOVERY=COMPLETE
S4_VNEXT_DEEP_BUDGET_SELECTION=COMPLETE
S5_STRUCTURE_AND_RADAR=COMPLETE
S6_POSITIONING_SUMMARY_V12=COMPLETE

CANDIDATE_MATERIALIZED_AT=NULL
NEW_PRODUCT_CANDIDATE_COUNT=0
```

The prior S4 identifier defect did not recur. This task must determine exactly why the run became `PARTIAL`.

Do not assume PARTIAL is a bug until proven.

## Canonical evidence

Read from:

```text
F:\options-anomaly-scanner\docs\evidence
```

At minimum:

```text
F:\options-anomaly-scanner\docs\evidence\NIGHTWATCH_VNEXT_CANONICAL_EVIDENCE_MANIFEST.md
F:\options-anomaly-scanner\docs\evidence\NIGHTWATCH_SCANNER_VNEXT_INTEGRATED_SPEC_PROMPT_20260817(1).md
F:\options-anomaly-scanner\docs\evidence\NIGHTWATCH_VNEXT_STAGE5_PRODUCT_CANDIDATE_PERSISTENCE_COMPLETION_REPORT_20260818.md
F:\options-anomaly-scanner\docs\evidence\NIGHTWATCH_VNEXT_STAGE6_PHASE2B_BALANCED_MODEL_COMPLETION_REPORT_20260818.md
F:\options-anomaly-scanner\docs\evidence\NIGHTWATCH_VNEXT_STAGE8_FAILED_SCAN_ROOT_CAUSE_DIAGNOSTIC_REPORT_20260820.md
F:\options-anomaly-scanner\docs\evidence\NIGHTWATCH_VNEXT_STAGE8_S4_STAGE_IDENTIFIER_REMEDIATION_REPORT_20260820.md
F:\options-anomaly-scanner\docs\evidence\NIGHTWATCH_VNEXT_SECOND_CONTROLLED_LIVE_MAG7_OBSERVATION_REPORT_20260820.md
```

If this package is attached and absent from canonical evidence, save it byte-for-byte as:

```text
F:\options-anomaly-scanner\docs\evidence\NIGHTWATCH_VNEXT_STAGE8_PARTIAL_TERMINAL_STATE_DIAGNOSTIC_EXECUTION_PACKAGE_20260820.md
```

## Authorization boundary

Authorized:

```text
repository/code inspection
read-only runtime DB SELECTs
read-only inspection of the second ScanRun and run-linked rows
zero-paid local reproduction using persisted rows or fixtures
local tests with zero Nightwatch calls and zero remote writes
sanitized evidence/report files
```

Forbidden:

```text
third MAG7 scan
Nightwatch request
Phase2B refresh
Dealer/GEX live call
remote DB write
manual repair
migration
application code edit
test code edit
workflow/scheduler change
commit/push/PR/merge
```

Expected:

```text
NIGHTWATCH_REQUESTS=0
PAID_UNITS=0
REMOTE_DB_WRITES=0
APPLICATION_CODE_CHANGES=0
```

## 1. Trace terminal status computation

Find the exact production path that decides final `ScanRun.status`.

Return:

```text
TERMINAL_STATUS_FUNCTION=
TERMINAL_STATUS_CALL_CHAIN=
PARTIAL_STATUS_CONDITION=
COMPLETE_STATUS_CONDITION=
FAILED_STATUS_CONDITION=
```

Identify every input used to choose COMPLETE/PARTIAL/FAILED.

## 2. Explain this exact run

For run:

```text
e9267160-503a-41c7-9bb1-8cc2b2e3d8c6
```

read every persisted field that feeds terminal-status computation.

Return a table:

| Terminal-status input | Persisted value | Expected condition | Caused PARTIAL? |
|---|---|---|---|

At minimum inspect:

```text
ticker scan statuses
ticker error fields
required/completed stage counts
degraded or missing-source flags
activity availability
Radar availability
Persistence availability
Structure/deep-dive availability
positioning/bucket availability
candidate projection result
summary fields
quota/network result fields
```

## 3. Inspect all seven ticker results

For each MAG7 ticker report:

```text
ticker
ticker_scan_result status
safe error if any
activity source status
Radar source status
Persistence source status
Structure/deep-dive status
positioning summary status
qualifying candidate projection yes/no
```

Return:

```text
PARTIAL_CAUSING_TICKERS=
PARTIAL_CAUSING_SOURCE_FAMILIES=
```

## 4. Candidate materialization gate

Trace:

```text
terminal status
→ candidate materialization invocation or skip
```

Return:

```text
CANDIDATE_MATERIALIZATION_CALLED=YES/NO
CANDIDATE_MATERIALIZATION_SKIP_REASON=
PARTIAL_STATUS_BLOCKS_MATERIALIZATION=YES/NO
```

Then answer from accepted governing semantics only:

```text
IF_RUN_IS_PARTIAL_BUT_PHASE2A_HAS_VALID_QUALIFYING_CANDIDATES_SHOULD_MATERIALIZE=
YES/NO/UNRESOLVED
```

Do not redesign the rule.

## 5. Classify PARTIAL

Use exactly one:

```text
EXPECTED_PARTIAL_DUE_TO_REAL_MISSING_REQUIRED_DATA
EXPECTED_PARTIAL_DUE_TO_NONCRITICAL_DEGRADATION
BUG_PARTIAL_FROM_OPTIONAL_OR_POST_CANDIDATE_LAYER
BUG_PARTIAL_FROM_STALE_LEGACY_STATUS_RULE
BUG_PARTIAL_FROM_ACCOUNTING_OR_FINALIZATION
OTHER
UNRESOLVED
```

Return:

```text
PARTIAL_CLASSIFICATION=
PARTIAL_SEMANTICALLY_JUSTIFIED=YES/NO/UNRESOLVED
```

## 6. Zero-paid reproduction

If possible, reproduce terminal-status determination from persisted second-run rows without vendor calls or DB writes.

Return:

```text
ZERO_PAID_TERMINAL_STATUS_REPRODUCTION_ATTEMPTED=YES/NO
ZERO_PAID_TERMINAL_STATUS_REPRODUCTION_RESULT=REPRODUCED/NOT_REPRODUCED/NOT_POSSIBLE
REPRODUCED_STATUS=
```

## 7. Remediation scope — design only

If PARTIAL is not semantically justified:

```text
REMEDIATION_REQUIRED=YES/NO/UNRESOLVED
EXPECTED_FILES_TO_CHANGE=
MIGRATION_REQUIRED=YES/NO/UNRESOLVED
HISTORICAL_DATA_REPAIR_REQUIRED=YES/NO/UNRESOLVED
```

Do not implement.

If PARTIAL is legitimate but the Stage 8 observation package incorrectly treated it as a failed scan, return:

```text
STAGE8_OBSERVATION_PACKAGE_STATUS_MODEL_DEFECT=YES/NO
```

## 8. Preserve runtime truth

Verify:

```text
SECOND_SCAN_RUN_ID=e9267160-503a-41c7-9bb1-8cc2b2e3d8c6
status=PARTIAL
safe_error=NONE
candidate_materialized_at=NULL
ProductCandidate rows=0
ProductCandidateTrigger rows=0
ProductCandidateContext rows=0
AnomalyContextDetail rows=0
```

Return:

```text
SECOND_RUN_MUTATED=NO
PARTIAL_RUN_STATE_TRUTHFUL=YES/NO
```

## 9. Evidence report

Create primary:

```text
F:\options-anomaly-scanner-stage8\docs\evidence\stage8\NIGHTWATCH_VNEXT_STAGE8_PARTIAL_TERMINAL_STATE_DIAGNOSTIC_REPORT_20260820.md
```

Also save byte-identical canonical backup:

```text
F:\options-anomaly-scanner\docs\evidence\NIGHTWATCH_VNEXT_STAGE8_PARTIAL_TERMINAL_STATE_DIAGNOSTIC_REPORT_20260820.md
```

Verify SHA-256 for both. If same filename exists with different content, do not overwrite; return `HOLD_REPORT_CONFLICT`.

## 10. Final result

Use one:

```text
PARTIAL_DIAGNOSTIC_RESULT=ROOT_CAUSE_CONFIRMED
PARTIAL_DIAGNOSTIC_RESULT=ROOT_CAUSE_NARROWED_NOT_CONFIRMED
PARTIAL_DIAGNOSTIC_RESULT=EXPECTED_PARTIAL_CONFIRMED
PARTIAL_DIAGNOSTIC_RESULT=INSUFFICIENT_EVIDENCE
```

Return:

```text
PARTIAL_DIAGNOSTIC_RESULT=
TERMINAL_STATUS_FUNCTION=
PARTIAL_STATUS_CONDITION=

PARTIAL_CLASSIFICATION=
PARTIAL_SEMANTICALLY_JUSTIFIED=

PARTIAL_CAUSING_TICKERS=
PARTIAL_CAUSING_SOURCE_FAMILIES=

CANDIDATE_MATERIALIZATION_CALLED=
CANDIDATE_MATERIALIZATION_SKIP_REASON=
PARTIAL_STATUS_BLOCKS_MATERIALIZATION=
IF_RUN_IS_PARTIAL_BUT_PHASE2A_HAS_VALID_QUALIFYING_CANDIDATES_SHOULD_MATERIALIZE=

ZERO_PAID_TERMINAL_STATUS_REPRODUCTION_ATTEMPTED=
ZERO_PAID_TERMINAL_STATUS_REPRODUCTION_RESULT=
REPRODUCED_STATUS=

REMEDIATION_REQUIRED=
EXPECTED_FILES_TO_CHANGE=
MIGRATION_REQUIRED=
HISTORICAL_DATA_REPAIR_REQUIRED=

STAGE8_OBSERVATION_PACKAGE_STATUS_MODEL_DEFECT=

SECOND_RUN_MUTATED=NO

NIGHTWATCH_REQUESTS=0
PAID_UNITS=0
REMOTE_DB_WRITES=0
APPLICATION_CODE_CHANGES=0
TEST_CODE_CHANGES=0
MIGRATION_CHANGES=0
WORKFLOWS_DISPATCHED=0
COMMITS_CREATED=0
PUSHES=0
PRS_CREATED=0
MERGES=0

THIRD_MAG7_SCAN_AUTHORIZED=NO
STAGE8_OBSERVATION_RESUME_READY=NO
STAGE9_READY=NO
NEXT_AUTHORIZED_STAGE=NONE

PRIMARY_REPORT_PATH=
CANONICAL_REPORT_PATH=
PRIMARY_REPORT_SHA256=
CANONICAL_REPORT_SHA256=
REPORT_BACKUP_BYTE_IDENTICAL=YES/NO
```

STOP.

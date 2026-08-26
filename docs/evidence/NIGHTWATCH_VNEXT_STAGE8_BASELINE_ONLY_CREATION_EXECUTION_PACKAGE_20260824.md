# Nightwatch vNext — Stage 8 Baseline-Only Creation — Execution Package

**Date:** 2026-08-24  
**Purpose:** Create the original `FIRST_KNOWLEDGE_BASELINE` for the seven genuine ProductCandidates already materialized by the successful third controlled MAG7 scan, without another scanner invocation or paid vendor call.  
**Authorization:** Founder explicitly authorized **Baseline-only Creation**.  
**Worktree:** `F:\options-anomaly-scanner-stage8`  
**Branch:** `vnext/stage8-mag7-observation`  
**Runtime schema:** `20260818_0017`

## 0. Founder authorization

Authorized exactly once:

```text
FOUNDER_AUTHORIZATION=BASELINE_ONLY_CREATION_20260824

TARGET_SCAN_RUN_ID=2c71e5bb-9334-4806-a195-0f8768d2d0f2
TARGET_PRODUCT_CANDIDATE_COUNT=7
TARGET_PRODUCT_CANDIDATE_TRIGGER_COUNT=82

EVALUATION_KIND=FIRST_KNOWLEDGE_BASELINE
EVIDENCE_CUTOFF=candidate_first_knowledge_at

MAG7_SCAN_AUTHORIZED=NO
NIGHTWATCH_REQUEST_AUTHORIZED=NO
PHASE2B_REFRESH_AUTHORIZED=NO
DEALER_GEX_LIVE_CALL_AUTHORIZED=NO
FOURTH_MAG7_SCAN_AUTHORIZED=NO
```

This authorization covers only the seven original baselines for the existing third-run candidates.

## 1. Accepted prerequisites

Authoritative state:

```text
THIRD_SCAN_RUN_ID=2c71e5bb-9334-4806-a195-0f8768d2d0f2
THIRD_SCAN_STATUS=COMPLETE

PRODUCT_CANDIDATES=7
PRODUCT_CANDIDATE_TRIGGERS=82
PRODUCT_CANDIDATE_CONTEXTS_FOR_RUN=0
ANOMALY_CONTEXT_DETAILS_FOR_RUN=0
```

Accepted baseline remediation:

```text
STAGE8_BASELINE_JSONB_REMEDIATION_RESULT=PASS
ROOT_CAUSE_ADDRESSED=YES

CONTRACT_SNAPSHOT_NONE_AS_NULL=TRUE
EXPIRY_ACTIVITY_RECAP_NONE_AS_NULL=TRUE

POSTGRES_NULL_BIND_BEHAVIOR_VERIFIED=YES
CONTRACT_BRANCH_VERIFIED=YES
EXPIRY_BRANCH_VERIFIED=YES

CHECK_CONSTRAINT_PRESERVED=YES
ORM_DB_SCHEMA_MISMATCH_RESOLVED=YES

FIRST_KNOWLEDGE_CUTOFF_LOGIC_CHANGED=NO
EXISTING_7_CANDIDATES_STILL_REUSABLE=YES
```

Do not recreate or replace candidates/triggers.

## 2. Canonical evidence root

Use:

```text
F:\options-anomaly-scanner\docs\evidence
```

If this package is attached and absent from canonical evidence, save it byte-for-byte as:

```text
F:\options-anomaly-scanner\docs\evidence\NIGHTWATCH_VNEXT_STAGE8_BASELINE_ONLY_CREATION_EXECUTION_PACKAGE_20260824.md
```

If the target exists with different bytes, do not overwrite. Return `HOLD_PACKAGE_CONFLICT`.

Read completely at minimum:

```text
F:\options-anomaly-scanner\docs\evidence\NIGHTWATCH_VNEXT_CANONICAL_EVIDENCE_MANIFEST.md
F:\options-anomaly-scanner\docs\evidence\NIGHTWATCH_SCANNER_VNEXT_INTEGRATED_SPEC_PROMPT_20260817(1).md
F:\options-anomaly-scanner\docs\evidence\NIGHTWATCH_VNEXT_STAGE5_PRODUCT_CANDIDATE_PERSISTENCE_COMPLETION_REPORT_20260818.md
F:\options-anomaly-scanner\docs\evidence\NIGHTWATCH_VNEXT_STAGE6_PHASE2B_BALANCED_MODEL_COMPLETION_REPORT_20260818.md
F:\options-anomaly-scanner\docs\evidence\NIGHTWATCH_VNEXT_STAGE6_BASELINE_CUTOFF_REMEDIATION_PASS_20260820.md
F:\options-anomaly-scanner\docs\evidence\NIGHTWATCH_VNEXT_THIRD_CONTROLLED_LIVE_MAG7_OBSERVATION_REPORT_20260820.md
F:\options-anomaly-scanner\docs\evidence\NIGHTWATCH_VNEXT_STAGE8_FIRST_KNOWLEDGE_BASELINE_INTEGRITYERROR_DIAGNOSTIC_REPORT_20260820.md
F:\options-anomaly-scanner\docs\evidence\NIGHTWATCH_VNEXT_STAGE8_BASELINE_JSONB_SQL_NULL_REMEDIATION_REPORT_20260820.md
```

## 3. Authorization boundary

Authorized:

```text
read-only code inspection
read-only runtime DB preflight
read-only first-knowledge preview
exactly one baseline-only application write operation
creation of ProductCandidateContext FIRST_KNOWLEDGE_BASELINE rows for the seven existing candidates
creation of corresponding accepted AnomalyContextDetail rows
read-only post-write verification
report/evidence file creation
```

Forbidden:

```text
MAG7 scan
Nightwatch/vendor calls
Phase2B REFRESH
Dealer/GEX live request
new ProductCandidate or ProductCandidateTrigger
candidate/trigger mutation
manual SQL baseline INSERT/UPDATE
historical repair
schema write
migration
application/test code edit
workflow/scheduler change
commit/push/PR/merge
Stage 9
```

Required:

```text
NIGHTWATCH_REQUESTS=0
PAID_UNITS=0
PHASE2B_REFRESH_CALLS=0
DEALER_GEX_LIVE_CALLS=0
```

## 4. Code-state preflight

Before any write inspect:

```text
git rev-parse --abbrev-ref HEAD
git rev-parse HEAD
git status --short
git diff --check
```

Confirm:

```text
ACCEPTED_S4_IDENTIFIER_REMEDIATION_PRESENT=YES
ACCEPTED_POST_CANDIDATE_PARTIAL_REMEDIATION_PRESENT=YES
ACCEPTED_BASELINE_JSONB_SQL_NULL_REMEDIATION_PRESENT=YES
UNEXPECTED_APPLICATION_DIFF_FOUND=NO
```

Verify ORM still has:

```text
contract_snapshot = JSONB(none_as_null=True)
expiry_activity_recap = JSONB(none_as_null=True)
```

If not, `BASELINE_ONLY_CREATION_RESULT=HOLD_CODE_STATE_MISMATCH` and STOP.

Do not commit or modify code.

## 5. Runtime preflight

Read-only verify:

```text
REMOTE_ALEMBIC_HEAD=20260818_0017
TARGET_SCAN_RUN_STATUS=COMPLETE

TARGET_PRODUCT_CANDIDATE_COUNT_BEFORE=7
TARGET_PRODUCT_CANDIDATE_TRIGGER_COUNT_BEFORE=82
TARGET_FIRST_KNOWLEDGE_BASELINE_COUNT_BEFORE=0
TARGET_ANOMALY_CONTEXT_DETAIL_COUNT_BEFORE=0
```

Read all seven candidates by `scan_run_id`, not by ticker name.

Expected tickers:

```text
AAPL
AMZN
GOOGL
META
MSFT
NVDA
TSLA
```

For each record:

```text
candidate_id
ticker
candidate_first_knowledge_at
materialization rule version/hash
trigger count
```

If counts/status/baseline-before state differ, return `HOLD_RUNTIME_STATE_CHANGED` and STOP.

## 6. Mandatory zero-write first-knowledge preview

Before writing, reconstruct the accepted Stage 6 baseline for all seven candidates using the accepted selectors in read-only/preview mode.

Authoritative cutoff for each candidate:

```text
candidate_first_knowledge_at
```

Never substitute current time, context_evaluated_at, created_at, or latest-source timestamps.

For each candidate report:

```text
candidate_id
ticker
candidate_first_knowledge_at
selected source IDs/provenance
selected chain/archive IDs
selected Dealer/GEX archive ID if any
selected OHLC trading dates if any
B1 state
B2 state
B3 state
B4 detail count
B5 state
```

Verify accepted information-time rules, including:

```text
source receipt/capture <= candidate_first_knowledge_at
vendor observed/as-of <= cutoff where required
later source rows excluded
OHLC trading_date <= cutoff NY trading date
malformed/missing OHLC dates fail closed
Dealer/GEX archive-only source time <= cutoff
chain source receipt <= cutoff
```

Return:

```text
PREVIEW_CANDIDATE_COUNT=
PREVIEW_LOOKAHEAD_FOUND=YES/NO
PREVIEW_SOURCE_TIME_VIOLATION_FOUND=YES/NO
PREVIEW_TRIGGER_SET_DRIFT_FOUND=YES/NO
```

If any is `YES`, return `HOLD_FIRST_KNOWLEDGE_PREVIEW_INTEGRITY` and STOP before writes.

If an original baseline can no longer be reconstructed from persisted historical sources, return `HOLD_BASELINE_NOT_RECONSTRUCTIBLE`.

Missing context remains truthfully missing/unavailable.

## 7. Trigger-set integrity

Verify all 82 immutable triggers and their accepted trigger/detail mapping.

Return:

```text
TRIGGER_SET_DRIFT_BEFORE_WRITE=YES/NO
```

If YES, return `HOLD_TRIGGER_SET_DRIFT` and STOP.

## 8. Execute one baseline-only creation operation

After all gates pass, create exactly one:

```text
FIRST_KNOWLEDGE_BASELINE
```

for each of the seven existing ProductCandidates using the accepted Stage 6 service and current remediated ORM.

Required:

```text
evaluation_kind=FIRST_KNOWLEDGE_BASELINE
evidence_cutoff_at=candidate_first_knowledge_at
```

Do not use manual SQL DML.

A temporary local invocation harness is allowed only if needed to call the accepted service. It must not be committed, must not modify repository code/tests, must be removed after execution, and must make zero vendor calls.

Before writing report:

```text
BASELINE_CREATION_TRANSACTION_MODEL=
```

Prefer one atomic transaction across all seven if the existing service/session model permits without code changes. If the service imposes another boundary, document it; do not alter service code merely to force a different transaction model.

On any exception:

```text
stop
do not retry
rollback active transaction where applicable
do not manually repair
report any rows that actually committed
```

and return `FAIL_BASELINE_CREATION`.

## 9. Exact write scope

Authorized new application rows are limited to:

```text
ProductCandidateContext
AnomalyContextDetail
```

for the seven target candidates.

Return:

```text
PRODUCT_CANDIDATE_ROWS_CHANGED=0
PRODUCT_CANDIDATE_TRIGGER_ROWS_CHANGED=0
SCAN_RUN_ROWS_CHANGED=0
```

## 10. Post-write identity/count verification

Read-only verify exactly one baseline per candidate.

Expected:

```text
TARGET_FIRST_KNOWLEDGE_BASELINE_COUNT_AFTER=7
```

Return a seven-row table:

```text
candidate_id
ticker
candidate_first_knowledge_at
product_candidate_context_id
evaluation_kind
evidence_cutoff_at
context_evaluated_at
anomaly_detail_count
```

Verify:

```text
evaluation_kind=FIRST_KNOWLEDGE_BASELINE
one baseline per candidate
no duplicate baseline
context_evaluated_at >= candidate_first_knowledge_at
evidence_cutoff_at = candidate_first_knowledge_at
```

Return:

```text
ONE_BASELINE_PER_CANDIDATE=YES/NO
DUPLICATE_BASELINE_FOUND=YES/NO
```

## 11. Post-write information-time integrity

Verify every persisted baseline/source reference again.

Return:

```text
BASELINE_LOOKAHEAD_FOUND=YES/NO
BASELINE_SOURCE_TIME_VIOLATION_FOUND=YES/NO
BASELINE_TRIGGER_SET_DRIFT_FOUND=YES/NO
BASELINE_FIRST_KNOWLEDGE_CUTOFF_MISMATCH_FOUND=YES/NO
```

Any YES => `FAIL_BASELINE_INTEGRITY`. Do not delete/repair rows in this task.

## 12. AnomalyContextDetail integrity

Verify each new detail:

```text
belongs to one of the seven target baseline contexts
matches accepted candidate trigger/detail semantics
satisfies entity_type/payload mutual exclusion
```

For CONTRACT:

```text
contract_snapshot IS NOT SQL NULL
expiry_activity_recap IS SQL NULL
```

For EXPIRY:

```text
contract_snapshot IS SQL NULL
expiry_activity_recap IS NOT SQL NULL
```

Return:

```text
ANOMALY_CONTEXT_DETAIL_COUNT_AFTER=
CONTRACT_DETAIL_PAYLOAD_MATCH_VALID=YES/NO
EXPIRY_DETAIL_PAYLOAD_MATCH_VALID=YES/NO
DETAIL_ORPHAN_FOUND=YES/NO
```

Do not assume detail count must equal 82 unless accepted Stage 6 service semantics explicitly require one detail per trigger. Derive expected count from the accepted service contract.

## 13. No paid refresh / no scan proof

Verify:

```text
MAG7_SCAN_INVOCATIONS_THIS_TASK=0
NIGHTWATCH_REQUESTS_THIS_TASK=0
PAID_UNITS_THIS_TASK=0
PHASE2B_REFRESH_CALLS=0
DEALER_GEX_LIVE_CALLS=0
DEALER_GEX_SOURCE=ARCHIVE_ONLY
```

## 14. Runtime deltas

Return exact deltas:

```text
PRODUCT_CANDIDATE_CONTEXT_ROWS_ADDED=
ANOMALY_CONTEXT_DETAIL_ROWS_ADDED=
PRODUCT_CANDIDATE_ROWS_ADDED=0
PRODUCT_CANDIDATE_TRIGGER_ROWS_ADDED=0
SCAN_RUN_ROWS_ADDED=0
```

## 15. Result states

Use exactly one:

```text
BASELINE_ONLY_CREATION_RESULT=PASS
BASELINE_ONLY_CREATION_RESULT=FAIL_BASELINE_CREATION
BASELINE_ONLY_CREATION_RESULT=FAIL_BASELINE_INTEGRITY
BASELINE_ONLY_CREATION_RESULT=HOLD_CODE_STATE_MISMATCH
BASELINE_ONLY_CREATION_RESULT=HOLD_RUNTIME_STATE_CHANGED
BASELINE_ONLY_CREATION_RESULT=HOLD_FIRST_KNOWLEDGE_PREVIEW_INTEGRITY
BASELINE_ONLY_CREATION_RESULT=HOLD_BASELINE_NOT_RECONSTRUCTIBLE
BASELINE_ONLY_CREATION_RESULT=HOLD_TRIGGER_SET_DRIFT
BASELINE_ONLY_CREATION_RESULT=HOLD_PACKAGE_CONFLICT
BASELINE_ONLY_CREATION_RESULT=HOLD_REPORT_CONFLICT
```

## 16. Evidence report — primary + canonical backup

Create primary:

```text
F:\options-anomaly-scanner-stage8\docs\evidence\stage8\NIGHTWATCH_VNEXT_STAGE8_BASELINE_ONLY_CREATION_REPORT_20260824.md
```

Also save byte-identical canonical backup:

```text
F:\options-anomaly-scanner\docs\evidence\NIGHTWATCH_VNEXT_STAGE8_BASELINE_ONLY_CREATION_REPORT_20260824.md
```

Requirements:

```text
primary/canonical byte-identical
verify SHA-256 for both
do not overwrite conflicting canonical content
```

## 17. Required final fields

Return:

```text
BASELINE_ONLY_CREATION_RESULT=

FOUNDER_AUTHORIZATION=BASELINE_ONLY_CREATION_20260824

TARGET_SCAN_RUN_ID=2c71e5bb-9334-4806-a195-0f8768d2d0f2
TARGET_SCAN_RUN_STATUS=

TARGET_PRODUCT_CANDIDATE_COUNT_BEFORE=
TARGET_PRODUCT_CANDIDATE_TRIGGER_COUNT_BEFORE=
TARGET_FIRST_KNOWLEDGE_BASELINE_COUNT_BEFORE=
TARGET_ANOMALY_CONTEXT_DETAIL_COUNT_BEFORE=

ACCEPTED_S4_IDENTIFIER_REMEDIATION_PRESENT=
ACCEPTED_POST_CANDIDATE_PARTIAL_REMEDIATION_PRESENT=
ACCEPTED_BASELINE_JSONB_SQL_NULL_REMEDIATION_PRESENT=
UNEXPECTED_APPLICATION_DIFF_FOUND=

PREVIEW_CANDIDATE_COUNT=
PREVIEW_LOOKAHEAD_FOUND=
PREVIEW_SOURCE_TIME_VIOLATION_FOUND=
PREVIEW_TRIGGER_SET_DRIFT_FOUND=
TRIGGER_SET_DRIFT_BEFORE_WRITE=

BASELINE_CREATION_TRANSACTION_MODEL=

TARGET_FIRST_KNOWLEDGE_BASELINE_COUNT_AFTER=
ANOMALY_CONTEXT_DETAIL_COUNT_AFTER=

ONE_BASELINE_PER_CANDIDATE=
DUPLICATE_BASELINE_FOUND=

BASELINE_LOOKAHEAD_FOUND=
BASELINE_SOURCE_TIME_VIOLATION_FOUND=
BASELINE_TRIGGER_SET_DRIFT_FOUND=
BASELINE_FIRST_KNOWLEDGE_CUTOFF_MISMATCH_FOUND=

CONTRACT_DETAIL_PAYLOAD_MATCH_VALID=
EXPIRY_DETAIL_PAYLOAD_MATCH_VALID=
DETAIL_ORPHAN_FOUND=

PRODUCT_CANDIDATE_CONTEXT_ROWS_ADDED=
ANOMALY_CONTEXT_DETAIL_ROWS_ADDED=
PRODUCT_CANDIDATE_ROWS_ADDED=0
PRODUCT_CANDIDATE_TRIGGER_ROWS_ADDED=0
SCAN_RUN_ROWS_ADDED=0

PRODUCT_CANDIDATE_ROWS_CHANGED=0
PRODUCT_CANDIDATE_TRIGGER_ROWS_CHANGED=0
SCAN_RUN_ROWS_CHANGED=0

MAG7_SCAN_INVOCATIONS_THIS_TASK=0
NIGHTWATCH_REQUESTS_THIS_TASK=0
PAID_UNITS_THIS_TASK=0
PHASE2B_REFRESH_CALLS=0
DEALER_GEX_LIVE_CALLS=0

REMOTE_ALEMBIC_HEAD=20260818_0017
REMOTE_DB_SCHEMA_WRITES=0
REMOTE_APPLICATION_DATA_WRITES=AUTHORIZED_BASELINE_ONLY_CREATION_ONLY

APPLICATION_CODE_CHANGES_DURING_BASELINE_CREATION=0
TEST_CODE_CHANGES_DURING_BASELINE_CREATION=0
MIGRATION_FILES_CHANGED_DURING_BASELINE_CREATION=0
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

If and only if `BASELINE_ONLY_CREATION_RESULT=PASS`:

```text
STAGE8_OBSERVATION_RESUME_READY=YES
```

Do not automatically perform broader Stage 8 analysis.
Do not start Stage 9.
STOP.

## 18. Carried ledger

Preserve:

```text
CURRENT_TRIGGER_FRESHNESS_MODE=CALIBRATION_REQUIRED
RADAR_OI_SCHEDULE_ACTIVATION=PENDING_ROLLOVER_EVIDENCE
CROSS_RUN_CANDIDATE_LIFECYCLE=DEFERRED_NO_AUTO_MERGE
IV_RANK_CORE_ELIGIBILITY=WITHHOLD_PENDING_PROVENANCE
ISOLATED_POSTGRES_RUNTIME_VERIFIED=NO
N1_HISTORICAL_RUNTIME_DISTRIBUTION_VERIFIED=NO
```

# Nightwatch Scanner vNext — Stage 8 Baseline-Only Creation Report

Date: 2026-08-24  
Authorization: `FOUNDER_AUTHORIZATION=BASELINE_ONLY_CREATION_20260824`  
Target ScanRun: `2c71e5bb-9334-4806-a195-0f8768d2d0f2`

## Executive result

```text
BASELINE_ONLY_CREATION_RESULT=FAIL_BASELINE_CREATION
```

All mandatory read-only gates and the seven-candidate zero-write preview passed. The authorized creation command then failed before opening a connection to the configured remote runtime because the Stage 8 worktree has no `.env` and that command resolved the repository-relative settings file to the Stage 8 worktree. The ORM therefore used its localhost development default and timed out with `OperationalError`/`psycopg.errors.ConnectionTimeout` before any transaction reached the remote PostgreSQL runtime.

The active session was rolled back, no commit occurred, and no retry was made, as required by the execution package. A subsequent read-only query using the existing canonical repository configuration confirmed the remote runtime remains at 7 ProductCandidates, 82 ProductCandidateTriggers, 0 baseline contexts, and 0 anomaly context details for the target run. Broader Stage 8 observation is therefore not ready to resume.

## Package and evidence gate

The attached package was copied byte-for-byte to:

```text
F:\options-anomaly-scanner\docs\evidence\NIGHTWATCH_VNEXT_STAGE8_BASELINE_ONLY_CREATION_EXECUTION_PACKAGE_20260824.md
```

Attachment and canonical package SHA-256:

```text
4D1EE671105D311ADBB4040BF056C24CBCC2872FE3F17E0CE2F72F49738CD15C
```

The canonical manifest and all governing evidence required by the package were read from `F:\options-anomaly-scanner\docs\evidence`. No governing evidence was reconstructed from memory.

## Repository and accepted-remediation gate

```text
WORKTREE=F:\options-anomaly-scanner-stage8
BRANCH=vnext/stage8-mag7-observation
HEAD=3a63eaa1b9069d34199704fe31ac6466e8929d7d

ACCEPTED_S4_IDENTIFIER_REMEDIATION_PRESENT=YES
ACCEPTED_POST_CANDIDATE_PARTIAL_REMEDIATION_PRESENT=YES
ACCEPTED_BASELINE_JSONB_SQL_NULL_REMEDIATION_PRESENT=YES
UNEXPECTED_APPLICATION_DIFF_FOUND=NO
```

Accepted application/test changes present before and after this task:

```text
backend/app/db/models.py
backend/app/scanner/v13.py
backend/tests/test_stage4b_phase2a_vnext.py
backend/tests/test_stage6_balanced_context.py
```

Observed accepted implementation facts:

```text
S4_STAGE_IDENTIFIER=S4_VNEXT_DEEP_BUDGET_SELECTION
VNEXT_OPTIONAL_POST_CANDIDATE_PARTIAL_GUARD=PRESENT
contract_snapshot=JSONB(none_as_null=True)
expiry_activity_recap=JSONB(none_as_null=True)
```

`git diff --check` passed. This task did not modify application code, tests, migrations, workflows, or schedulers.

## Runtime state before creation

All pre-write runtime checks were read-only.

```text
REMOTE_ALEMBIC_HEAD=20260818_0017
TARGET_SCAN_RUN_STATUS=COMPLETE
TARGET_PRODUCT_CANDIDATE_COUNT_BEFORE=7
TARGET_PRODUCT_CANDIDATE_TRIGGER_COUNT_BEFORE=82
TARGET_FIRST_KNOWLEDGE_BASELINE_COUNT_BEFORE=0
TARGET_ANOMALY_CONTEXT_DETAIL_COUNT_BEFORE=0
```

Candidate inventory:

| Ticker | Candidate ID | Immutable triggers | candidate_first_knowledge_at |
|---|---|---:|---|
| AAPL | `e515baba-d875-40a9-8278-4db2b1eb0ba2` | 13 | `2026-08-20T10:07:16.687134Z` |
| AMZN | `10ef5e5a-2d37-42cc-b547-5ca09c6cefa1` | 10 | `2026-08-20T10:07:16.687134Z` |
| GOOGL | `8194d467-46b5-41ce-b477-30e2ba204c70` | 9 | `2026-08-20T10:07:16.687134Z` |
| META | `d8a1d3bc-f18e-40f4-834f-247c595246ab` | 4 | `2026-08-20T10:07:16.687134Z` |
| MSFT | `6597d042-817a-4318-a236-b8949845528a` | 5 | `2026-08-20T10:07:16.687134Z` |
| NVDA | `c35e7743-c2a7-45ff-b67d-312e779f8304` | 27 | `2026-08-20T10:07:16.687134Z` |
| TSLA | `36d7ad31-2038-4f0e-bc61-e18fb1e4bfa1` | 14 | `2026-08-20T10:07:16.687134Z` |

All seven candidates retained materialization rule `phase2a_vnext_stage4b.product-candidate-materialization.v1` and materialization hash `482a09...73ebd` as recorded in the read-only preflight.

## Mandatory zero-write preview

The accepted `Stage6BalancedContextService` selectors were executed against explicit read-only sessions with a no-write session adapter. `add()` and `flush()` were intercepted; no database writes were executed. The preview used each candidate's immutable `candidate_first_knowledge_at` as its evidence cutoff.

| Ticker | Preview details | Cutoff match | Trigger set match | Source-time violations | CONTRACT/EXPIRY bind valid |
|---|---:|---|---|---:|---|
| AAPL | 13 | YES | YES | 0 | YES |
| AMZN | 10 | YES | YES | 0 | YES |
| GOOGL | 9 | YES | YES | 0 | YES |
| META | 4 | YES | YES | 0 | YES |
| MSFT | 5 | YES | YES | 0 | YES |
| NVDA | 27 | YES | YES | 0 | YES |
| TSLA | 14 | YES | YES | 0 | YES |

The preview selected only archived source evidence at or before the cutoff. OHLC payloads were filtered using the accepted corrected rule: malformed/missing trading dates failed closed, and selected bars did not extend beyond the cutoff New York market date. Archived Dealer/GEX source times, raw vendor payload receive/observation times, contract quote times, and trigger source times did not exceed the cutoff.

```text
PREVIEW_CANDIDATE_COUNT=7
PREVIEW_DETAIL_COUNT=82
PREVIEW_LOOKAHEAD_FOUND=NO
PREVIEW_SOURCE_TIME_VIOLATION_FOUND=NO
PREVIEW_TRIGGER_SET_DRIFT_FOUND=NO
TRIGGER_SET_DRIFT_BEFORE_WRITE=NO
PREVIEW_DATABASE_WRITES=0
PREVIEW_CONTRACT_PAYLOAD_MATCH_VALID=YES
PREVIEW_EXPIRY_PAYLOAD_MATCH_VALID=YES
```

## Authorized creation attempt

Planned transaction model:

```text
BASELINE_CREATION_TRANSACTION_MODEL=ONE_TRANSACTION_ONE_COMMIT
```

The command rechecked head/status/count/zero-baseline preconditions before calling the accepted service, but its settings resolution used:

```text
F:\options-anomaly-scanner-stage8\.env (absent)
```

It consequently fell back to the development database target `localhost:5432/options_scanner`. Connection attempts to local IPv6 and IPv4 timed out before a remote connection or application transaction existed.

```text
CREATION_SAFE_ERROR=OperationalError
DBAPI_SAFE_ERROR=psycopg.errors.ConnectionTimeout
CREATION_COMMIT_OCCURRED=NO
ACTIVE_SESSION_ROLLBACK_CALLED=YES
CREATION_RETRY_ATTEMPTED=NO
REMOTE_CREATION_CONNECTION_OPENED=NO
```

Per the package's explicit exception rule, execution stopped. The configuration was not corrected for a second creation attempt because that would constitute a forbidden retry.

## Read-only post-failure verification

The post-failure verification explicitly loaded the existing canonical repository environment configuration and used `SET TRANSACTION READ ONLY`. It confirmed:

```text
REMOTE_ALEMBIC_HEAD_AFTER_FAILURE=20260818_0017
TARGET_SCAN_RUN_STATUS_AFTER_FAILURE=COMPLETE
TARGET_PRODUCT_CANDIDATE_COUNT_AFTER_FAILURE=7
TARGET_PRODUCT_CANDIDATE_TRIGGER_COUNT_AFTER_FAILURE=82
TARGET_FIRST_KNOWLEDGE_BASELINE_COUNT_AFTER=0
ANOMALY_CONTEXT_DETAIL_COUNT_AFTER=0

GLOBAL_PRODUCT_CANDIDATE_COUNT_AFTER=7
GLOBAL_PRODUCT_CANDIDATE_TRIGGER_COUNT_AFTER=82
GLOBAL_PRODUCT_CANDIDATE_CONTEXT_COUNT_AFTER=0
GLOBAL_ANOMALY_CONTEXT_DETAIL_COUNT_AFTER=0
GLOBAL_SCAN_RUN_COUNT_AFTER=9
```

Because no baseline or detail rows exist after the failed operation, persisted-baseline integrity assertions are not evaluable. The corresponding preview assertions passed, but they are not substituted for persisted-row proof.

```text
ONE_BASELINE_PER_CANDIDATE=NO
DUPLICATE_BASELINE_FOUND=NO
BASELINE_LOOKAHEAD_FOUND=NOT_EVALUATED_NO_BASELINE_ROWS
BASELINE_SOURCE_TIME_VIOLATION_FOUND=NOT_EVALUATED_NO_BASELINE_ROWS
BASELINE_TRIGGER_SET_DRIFT_FOUND=NOT_EVALUATED_NO_BASELINE_ROWS
BASELINE_FIRST_KNOWLEDGE_CUTOFF_MISMATCH_FOUND=NOT_EVALUATED_NO_BASELINE_ROWS
CONTRACT_DETAIL_PAYLOAD_MATCH_VALID=NOT_APPLICABLE_NO_DETAIL_ROWS
EXPIRY_DETAIL_PAYLOAD_MATCH_VALID=NOT_APPLICABLE_NO_DETAIL_ROWS
DETAIL_ORPHAN_FOUND=NO
```

## Write and authorization ledger

```text
PRODUCT_CANDIDATE_CONTEXT_ROWS_ADDED=0
ANOMALY_CONTEXT_DETAIL_ROWS_ADDED=0
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

REMOTE_DB_SCHEMA_WRITES=0
REMOTE_APPLICATION_DATA_WRITES=0

APPLICATION_CODE_CHANGES_DURING_BASELINE_CREATION=0
TEST_CODE_CHANGES_DURING_BASELINE_CREATION=0
MIGRATION_FILES_CHANGED_DURING_BASELINE_CREATION=0
WORKFLOW_CHANGES=0
SCHEDULER_CHANGES=0
COMMITS_CREATED=0
PUSHES=0
PRS_CREATED=0
MERGES=0
```

## Network/contact ledger

No HTTP URL or API endpoint was contacted. No Nightwatch/vendor request was made.

Database endpoints involved:

```text
postgresql://aws-0-ap-northeast-1.pooler.supabase.com:5432/postgres
  - read-only preflight
  - read-only seven-candidate preview
  - read-only post-failure verification

postgresql://localhost:5432/options_scanner
  - failed local connection attempt only
  - no transaction and no data write
```

Credentials were not printed or included in this report.

## Required result fields

```text
BASELINE_ONLY_CREATION_RESULT=FAIL_BASELINE_CREATION

FOUNDER_AUTHORIZATION=BASELINE_ONLY_CREATION_20260824

TARGET_SCAN_RUN_ID=2c71e5bb-9334-4806-a195-0f8768d2d0f2
TARGET_SCAN_RUN_STATUS=COMPLETE

TARGET_PRODUCT_CANDIDATE_COUNT_BEFORE=7
TARGET_PRODUCT_CANDIDATE_TRIGGER_COUNT_BEFORE=82
TARGET_FIRST_KNOWLEDGE_BASELINE_COUNT_BEFORE=0
TARGET_ANOMALY_CONTEXT_DETAIL_COUNT_BEFORE=0

ACCEPTED_S4_IDENTIFIER_REMEDIATION_PRESENT=YES
ACCEPTED_POST_CANDIDATE_PARTIAL_REMEDIATION_PRESENT=YES
ACCEPTED_BASELINE_JSONB_SQL_NULL_REMEDIATION_PRESENT=YES
UNEXPECTED_APPLICATION_DIFF_FOUND=NO

PREVIEW_CANDIDATE_COUNT=7
PREVIEW_LOOKAHEAD_FOUND=NO
PREVIEW_SOURCE_TIME_VIOLATION_FOUND=NO
PREVIEW_TRIGGER_SET_DRIFT_FOUND=NO
TRIGGER_SET_DRIFT_BEFORE_WRITE=NO

BASELINE_CREATION_TRANSACTION_MODEL=ONE_TRANSACTION_ONE_COMMIT_ATTEMPTED_NO_REMOTE_CONNECTION_NO_COMMIT

TARGET_FIRST_KNOWLEDGE_BASELINE_COUNT_AFTER=0
ANOMALY_CONTEXT_DETAIL_COUNT_AFTER=0

ONE_BASELINE_PER_CANDIDATE=NO
DUPLICATE_BASELINE_FOUND=NO

BASELINE_LOOKAHEAD_FOUND=NOT_EVALUATED_NO_BASELINE_ROWS
BASELINE_SOURCE_TIME_VIOLATION_FOUND=NOT_EVALUATED_NO_BASELINE_ROWS
BASELINE_TRIGGER_SET_DRIFT_FOUND=NOT_EVALUATED_NO_BASELINE_ROWS
BASELINE_FIRST_KNOWLEDGE_CUTOFF_MISMATCH_FOUND=NOT_EVALUATED_NO_BASELINE_ROWS

CONTRACT_DETAIL_PAYLOAD_MATCH_VALID=NOT_APPLICABLE_NO_DETAIL_ROWS
EXPIRY_DETAIL_PAYLOAD_MATCH_VALID=NOT_APPLICABLE_NO_DETAIL_ROWS
DETAIL_ORPHAN_FOUND=NO

PRODUCT_CANDIDATE_CONTEXT_ROWS_ADDED=0
ANOMALY_CONTEXT_DETAIL_ROWS_ADDED=0
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
REMOTE_APPLICATION_DATA_WRITES=0

APPLICATION_CODE_CHANGES_DURING_BASELINE_CREATION=0
TEST_CODE_CHANGES_DURING_BASELINE_CREATION=0
MIGRATION_FILES_CHANGED_DURING_BASELINE_CREATION=0
WORKFLOW_CHANGES=0
SCHEDULER_CHANGES=0
COMMITS_CREATED=0
PUSHES=0
PRS_CREATED=0
MERGES=0

PRIMARY_REPORT_PATH=F:\options-anomaly-scanner-stage8\docs\evidence\stage8\NIGHTWATCH_VNEXT_STAGE8_BASELINE_ONLY_CREATION_REPORT_20260824.md
CANONICAL_REPORT_PATH=F:\options-anomaly-scanner\docs\evidence\NIGHTWATCH_VNEXT_STAGE8_BASELINE_ONLY_CREATION_REPORT_20260824.md
PRIMARY_REPORT_SHA256=CALCULATED_AFTER_REPORT_FINALIZATION
CANONICAL_REPORT_SHA256=CALCULATED_AFTER_REPORT_FINALIZATION
REPORT_BACKUP_BYTE_IDENTICAL=VERIFIED_AFTER_REPORT_FINALIZATION

FOURTH_MAG7_SCAN_AUTHORIZED=NO
STAGE8_OBSERVATION_RESUME_READY=NO
STAGE9_READY=NO
NEXT_AUTHORIZED_STAGE=NONE
```

## Carried ledger

```text
CURRENT_TRIGGER_FRESHNESS_MODE=CALIBRATION_REQUIRED
RADAR_OI_SCHEDULE_ACTIVATION=PENDING_ROLLOVER_EVIDENCE
CROSS_RUN_CANDIDATE_LIFECYCLE=DEFERRED_NO_AUTO_MERGE
IV_RANK_CORE_ELIGIBILITY=WITHHOLD_PENDING_PROVENANCE
ISOLATED_POSTGRES_RUNTIME_VERIFIED=NO
N1_HISTORICAL_RUNTIME_DISTRIBUTION_VERIFIED=NO
```

No broader Stage 8 analysis was started. Stage 9 was not started.

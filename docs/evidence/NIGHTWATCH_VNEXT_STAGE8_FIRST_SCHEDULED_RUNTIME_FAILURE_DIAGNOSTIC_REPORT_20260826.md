# Nightwatch vNext — Stage 8 First Scheduled Runtime Failure Diagnostic Report

Date: 2026-08-26  
Authorization: zero-paid, read-only Stage 8 diagnostic  
Result: `PASS_ROOT_CAUSE_CONFIRMED`

## Executive finding

The first scheduled morning job did not fail before Nightwatch contact. The parent `DailyCollectionRun` counters incorrectly reported zero because the child `DailyOiArchiver` never returned its counters. Authoritative `api_usage_audit` proves two AAPL vendor attempts: an OI-per-expiry HTTP 200 that consumed one paid unit, followed by a chain-snapshot HTTP 404 `NOT_FOUND` for expiration `2026-08-24`.

The 404 was a normal `NightwatchError` input to an error-handling branch. That branch attempted to insert a second `daily_oi_archive_tickers` row for the same `(archive_run_id, ticker)` even though the AAPL `RUNNING` row had already been committed. The deployed and ORM-declared unique constraint `uq_archive_ticker_run_ticker` requires `UNIQUE (archive_run_id, ticker)`, so the duplicate insert deterministically failed. The resulting failed transaction was not rolled back before the archiver tried to mark its run failed and unlock its advisory lock. Those cleanup operations replaced the original constraint exception with `PendingRollbackError`.

Radar then ran on the same invalid SQLAlchemy session. Its first database operation raised the same `PendingRollbackError`; its isolation handler called `rollback()`, producing the visible SAWarning. Therefore Radar was a cascade, and the warning was secondary rather than causal.

The morning GitHub job was false green because `run_archive_mag7_daily()` always returned process exit `0` after receiving any normal `DailyCollectionSummary`, including `status=FAILED`. The workflow shell truthfully treated that process exit as success.

The evening readiness gate behaved correctly. It found all seven Radar tickers missing, returned exit `4`, and created no ScanRun, no Nightwatch usage, and no baseline.

## Package and governing evidence custody

The attached execution package was preserved byte-for-byte:

```text
SOURCE_PACKAGE=C:\Users\lili\Downloads\NIGHTWATCH_VNEXT_STAGE8_FIRST_SCHEDULED_RUNTIME_FAILURE_DIAGNOSTIC_EXECUTION_PACKAGE_20260826.md
CANONICAL_PACKAGE=F:\options-anomaly-scanner\docs\evidence\NIGHTWATCH_VNEXT_STAGE8_FIRST_SCHEDULED_RUNTIME_FAILURE_DIAGNOSTIC_EXECUTION_PACKAGE_20260826.md
SOURCE_SHA256=485D955815AA00629E7D9F91E4B7BE4FFA63E26839F6EB68A265D27D6A63F5AF
CANONICAL_SHA256=485D955815AA00629E7D9F91E4B7BE4FFA63E26839F6EB68A265D27D6A63F5AF
PACKAGE_BYTE_IDENTICAL=YES
PACKAGE_CONFLICT=NO
```

The canonical manifest, integrated vNext specification, Stage 4A package, Stage 8 daily automation gate report, and GitHub deployment report were read completely from their explicit canonical paths.

## Runtime target identity gate

The same canonical repository environment mechanism previously accepted for Supabase access was used. The connection was placed in an explicit read-only transaction before evidence queries. No credential or full database URL was printed.

```text
DB_TARGET_HOST=aws-0-ap-northeast-1.pooler.supabase.com
DB_TARGET_PORT=5432
DB_TARGET_DATABASE=postgres
DB_TARGET_IS_LOCALHOST=NO
DB_TARGET_IDENTITY_GATE=PASS
REMOTE_ALEMBIC_HEAD=20260818_0017
```

## GitHub run identity

Morning workflow run:

```text
GITHUB_WORKFLOW_RUN_ID=32840156933
GITHUB_WORKFLOW_RUN_NUMBER=1
GITHUB_JOB_ID=97777648843
GITHUB_JOB=radar-oi-archive
GITHUB_JOB_CONCLUSION=success
GITHUB_HEAD_SHA=55e9f96483c7edb897ff1829b63cbe84eac179a2
```

Evening workflow run:

```text
GITHUB_WORKFLOW_RUN_ID=32898160019
GITHUB_WORKFLOW_RUN_NUMBER=2
GITHUB_JOB_ID=97965922399
GITHUB_JOB=daily-vnext-observation
GITHUB_JOB_CONCLUSION=failure
GITHUB_HEAD_SHA=55e9f96483c7edb897ff1829b63cbe84eac179a2
```

## Exact persisted morning evidence

Parent daily run:

```text
DAILY_RUN_ID=c43274fd-cb86-4004-9f1c-b88ddc33dd6a
DAILY_RUN_STATUS=FAILED
STARTED_AT=2026-08-25T11:01:54.076026Z
COMPLETED_AT=2026-08-25T11:01:59.335025Z
NY_MARKET_DATE=2026-08-25
PERSISTED_PARENT_CONSUMED_UNITS=0
PERSISTED_PARENT_NETWORK_ATTEMPTS=0
DAILY_OI_SUBJOB_STATUS=FAILED
RADAR_SUBJOB_STATUS=FAILED
DAILY_OI_SAFE_ERROR_CLASS=PendingRollbackError
RADAR_SAFE_ERROR_CLASS=PendingRollbackError
```

Only the safe exception classes were persisted in `daily_collection_runs.subjobs`; safe codes and messages were not stored:

```text
DAILY_OI_SAFE_ERROR_CODE=NOT_PERSISTED
DAILY_OI_SAFE_ERROR_MESSAGE=NOT_PERSISTED
RADAR_SAFE_ERROR_CODE=NOT_PERSISTED
RADAR_SAFE_ERROR_MESSAGE=NOT_PERSISTED
PERSISTED_ERROR_DETAIL_AVAILABLE=PARTIAL
```

The child archive was not finalized:

```text
DAILY_OI_ARCHIVE_RUN_ID=ccb84da6-3e58-4fff-b978-72df37c722c3
DAILY_OI_ARCHIVE_RUN_STATUS=RUNNING
DAILY_OI_ARCHIVE_RUN_STARTED_AT=2026-08-25T11:01:54.973376Z
DAILY_OI_ARCHIVE_RUN_COMPLETED_AT=NULL
DAILY_OI_ARCHIVE_TICKER=AAPL
DAILY_OI_ARCHIVE_TICKER_STATUS=RUNNING
DAILY_OI_ARCHIVE_VENDOR_OI_DATE=2026-08-24
```

Authoritative API telemetry contradicts the parent zero counters:

| Attempt | Time UTC | Command | Endpoint | Expiration | HTTP | Error | Consumed quota |
|---:|---|---|---|---|---:|---|---|
| 1 | 2026-08-25 11:01:55.257282 | `daily_archive.options.oi_per_expiry` | `/v1/options/oi-per-expiry/AAPL` | — | 200 | — | true |
| 2 | 2026-08-25 11:01:57.979494 | `daily_archive.options.chain_snapshot` | `/v1/options/chain-snapshot/AAPL` | 2026-08-24 | 404 | `NOT_FOUND` | unknown/not charged by persisted telemetry |

```text
AUTHORITATIVE_MORNING_NETWORK_ATTEMPTS=2
AUTHORITATIVE_MORNING_PAID_UNITS=1
PARENT_COUNTER_UNDERREPORT_FOUND=YES
FAILURE_OCCURRED_BEFORE_NIGHTWATCH_CLIENT=NO
```

The HTTP 200 raw payload was persisted. The 404 has an API-usage audit row but no raw payload row, consistent with the client raising after audit persistence.

## Root-cause reconstruction

The deterministic sequence is:

1. `DailyDataPipeline.execute()` persisted the parent DailyCollectionRun.
2. `DailyOiArchiver.execute()` acquired its advisory lock and committed its child run.
3. `_archive_ticker("AAPL")` fetched and persisted the OI surface, created one AAPL `RUNNING` ticker row, and committed 15 `PENDING` expiry snapshots.
4. The first chain request, for expiration `2026-08-24`, returned HTTP 404 `NOT_FOUND`.
5. `backend/app/scanner/archive.py:113-122` caught `NightwatchError` and attempted a new AAPL `VENDOR_ERROR` ticker row rather than updating the already-committed AAPL row.
6. The database constraint `uq_archive_ticker_run_ticker = UNIQUE (archive_run_id, ticker)` rejected the duplicate key.
7. `backend/app/scanner/archive.py:124-138` did not roll back before attempting failed-run persistence and advisory unlock. The transaction remained failed, and `PendingRollbackError` replaced the original exception.
8. `backend/app/scanner/daily.py:153-161` caught that replacement exception but did not roll back before invoking Radar.
9. Radar encountered the invalid shared session before vendor fetch. `backend/app/scanner/daily.py:195-204` caught it and its rollback emitted the line-201 SAWarning.

ORM and deployed schema agree on the uniqueness rule. The violated key values are proven by the one persisted AAPL row and the handler's attempted construction using the same archive run and ticker. The exact original server error text was not persisted, but PostgreSQL's deterministic class for this operation is unique violation SQLSTATE `23505`, surfaced by SQLAlchemy as `IntegrityError` before it was masked.

```text
FIRST_VENDOR_FAILURE=HTTP_404_NOT_FOUND
FIRST_VENDOR_FAILURE_TICKER=AAPL
FIRST_VENDOR_FAILURE_EXPIRATION=2026-08-24
FIRST_FAILING_OPERATION=duplicate DailyOiArchiveTicker VENDOR_ERROR insert for an existing archive_run_id+AAPL key
FIRST_FAILING_CODE_PATH=backend/app/scanner/archive.py:113-122
ORIGINAL_DBAPI_ERROR_CLASS=IntegrityError_INFERRED_FROM_DETERMINISTIC_CONSTRAINT
ORIGINAL_POSTGRESQL_SQLSTATE=23505_INFERRED_NOT_PERSISTED
ORIGINAL_POSTGRESQL_ERROR_TEXT=NOT_RECOVERABLE_FROM_PERSISTED_STATE
ORM_DB_SCHEMA_AGREEMENT=YES
PRIMARY_FAILURE_CLASSIFICATION=LOCAL_ORCHESTRATION_LOGIC
PRIMARY_ROOT_CAUSE=NightwatchError handling inserts a duplicate per-run ticker status row, then missing rollback masks the unique-key failure and poisons the shared session
ROOT_CAUSE_CONFIDENCE=HIGH
```

The best-supported classification is local orchestration logic rather than schema defect: the one-row-per-run/ticker constraint is intentional and consistent in ORM and deployed PostgreSQL; the handler violates it.

## Radar cascade and transaction warning

```text
DAILY_OI_RUNS_BEFORE_RADAR=YES
RADAR_REQUIRES_DAILY_OI_SUCCESS=NO
RADAR_FAILURE_IS_CASCADE_FROM_DAILY_OI=YES

ACTIVE_TRANSACTION_EXPECTED_AT_FAILURE_POINT=YES
ROLLBACK_WARNING_IS_ROOT_CAUSE=NO
ROLLBACK_WARNING_CLASSIFICATION=SECONDARY
SESSION_STATE_INVALIDATED_BEFORE_ROLLBACK=YES
```

Radar is not explicitly gated on Daily OI success; the orchestrator proceeds to Radar. In this occurrence it never reached its Nightwatch fetch because the shared SQLAlchemy session was still in failed-transaction state. No Radar coverage or Radar observation row belongs to the failed parent run.

The SAWarning was emitted when `_isolated()` finally called `session.rollback()` after ORM state had been changed on an already non-active transaction. It is evidence of the earlier missing rollback, not the initial failure.

## False-green process semantics

`DailyDataPipeline.execute()` converted subjob exceptions into a returned `DailyCollectionSummary(status="FAILED")`. Because no exception escaped, `run_archive_mag7_daily()` reached `backend/app/cli.py:287-294`, printed the failed summary, and unconditionally returned `0`. `raise SystemExit(main())` propagated that zero process code. GitHub's standard `bash -e` step therefore reported success.

```text
CLI_EXIT_CODE_ON_INTERNAL_FAILED=0
CLI_FALSE_GREEN_CONFIRMED=YES
FALSE_GREEN_CODE_PATH=backend/app/cli.py:284-294
EXPECTED_CORRECT_EXIT_SEMANTICS=COMPLETE/NO_NEW_DATA and explicit legitimate scheduler skips -> 0; blocking FAILED/PARTIAL -> defined non-zero exit
```

This is separate from the primary morning collection defect and needs its own remediation.

## Evening fail-closed proof

GitHub log evidence:

```text
Daily vNext observation held before scan: RADAR_COVERAGE_INCOMPLETE missing=AAPL,AMZN,GOOGL,META,MSFT,NVDA,TSLA unexpected=NONE
Process completed with exit code 4
```

Read-only DB evidence for `2026-08-25T20:57:40Z` through `20:58:00Z`:

- no new `scan_runs`;
- no `api_usage_audit` rows;
- no ProductCandidateContext baselines;
- seven COMPLETE Activity tickers for market date 2026-08-25;
- zero COMPLETE Radar tickers for expected vendor OI date 2026-08-24.

`load_daily_observation_readiness()` checks Activity, Radar, and Daily OI coverage before the call to `Mag7Scanner.execute(trigger="scheduled_daily")`. The Radar check raised first, so the scan was never invoked.

```text
EVENING_READINESS_RESULT=RADAR_COVERAGE_INCOMPLETE
EVENING_MISSING_RADAR_TICKERS=AAPL,AMZN,GOOGL,META,MSFT,NVDA,TSLA
EVENING_MAG7_SCAN_INVOKED=NO
EVENING_NIGHTWATCH_PAID_UNITS=0
EVENING_BASELINES_CREATED=0
```

The evening gate is correct safety behavior and is not the primary defect.

## Persisted data impact

The morning run left partial truthful source evidence plus two misleading non-terminal child statuses:

```text
DAILY_OI_RUN_ROW_CREATED=YES
DAILY_OI_TICKER_ROWS_ADDED=1
DAILY_OI_EXPIRY_ROWS_ADDED=15
DAILY_OI_EXPIRY_ROWS_PENDING=15
RAW_VENDOR_PAYLOAD_ROWS_ADDED=1
API_USAGE_AUDIT_ROWS_ADDED=2
RADAR_COVERAGE_ROWS_ADDED=0
RADAR_EVENT_ROWS_ADDED=0
CONTRACT_OI_ROWS_ADDED=0
PARTIAL_RUNTIME_WRITES_FOUND=YES
```

The parent daily run truthfully says `FAILED`. The child archive run and AAPL ticker remain `RUNNING` because failure finalization was attempted on an invalid transaction. They must not be treated as success or complete coverage. No repair or deletion was performed.

## Narrow remediation recommendation — design only

R1, primary morning archive fix:

- In `backend/app/scanner/archive.py`, ensure each `(archive_run_id, ticker)` has one lifecycle row. When a chain request raises `NightwatchError`, update/finalize the existing ticker row instead of inserting another row.
- Roll back a failed transaction before attempting to persist a safe terminal child-run status, and make advisory unlock cleanup transaction-safe without masking the original exception.
- In `backend/app/scanner/daily.py`, roll back after a caught Daily OI exception before continuing to another isolated subjob; retain the original safe error and authoritative child usage counters where available.
- Add a mocked regression where OI surface succeeds, the first chain request returns 404, the existing ticker row becomes a truthful failure/partial state, the session remains usable, and Radar is not falsely reported as an independent DB failure.

R2, false-green CLI fix:

- In `backend/app/cli.py`, map returned DailyCollectionSummary states to process status: true success/no-new-data and explicit scheduler skips remain zero; blocking `FAILED`/`PARTIAL` return non-zero.
- Add CLI/workflow regressions proving an internal failed summary makes the GitHub step fail and legitimate skips remain green.

```text
REMEDIATION_REQUIRED=YES
PRIMARY_REMEDIATION_FILES=backend/app/scanner/archive.py; backend/app/scanner/daily.py; backend/tests/test_stage4a_daily_pipeline.py
FALSE_GREEN_REMEDIATION_FILES=backend/app/cli.py; backend/tests/test_stage4a_daily_pipeline.py; backend/tests/test_stage8_daily_automation_workflow.py
MIGRATION_REQUIRED=NO
HISTORICAL_REPAIR_REQUIRED=NO
PAID_RUNTIME_RETEST_REQUIRED_AFTER_FIX=NO
```

The defect and CLI semantics can be deterministically covered with mocked zero-network tests. A future natural scheduled cycle can provide runtime proof under separate authorization; an extra manual paid rerun is not required. Existing rows remain audit evidence and are not required to be repaired for the narrow code remediation.

## External contact ledger

The diagnostic contacted only these external systems:

```text
GitHub repository/action metadata and logs:
https://api.github.com/repos/lililinuk/options-anomaly-scanner/actions/workflows/341934128/runs?event=schedule&per_page=10
https://api.github.com/repos/lililinuk/options-anomaly-scanner/actions/runs/32840156933/jobs
https://api.github.com/repos/lililinuk/options-anomaly-scanner/actions/runs/32898160019/jobs
https://api.github.com/repos/lililinuk/options-anomaly-scanner/actions/jobs/97777648843/logs
https://api.github.com/repos/lililinuk/options-anomaly-scanner/actions/jobs/97965922399/logs

Read-only runtime database target:
aws-0-ap-northeast-1.pooler.supabase.com:5432/postgres
```

No Nightwatch endpoint was contacted by this diagnostic. The two historical Nightwatch endpoints were learned only from persisted API audit evidence:

```text
https://api.yehangshe.com/v1/options/oi-per-expiry/AAPL
https://api.yehangshe.com/v1/options/chain-snapshot/AAPL?expiration=2026-08-24
```

## Authorization ledger

```text
NIGHTWATCH_REQUESTS=0
PAID_UNITS=0
REMOTE_APPLICATION_DATA_WRITES=0
REMOTE_SCHEMA_WRITES=0
WORKFLOWS_DISPATCHED=0
CODE_CHANGES=0
MIGRATIONS_CREATED=0
COMMITS_CREATED=0
PUSHES=0
PRS_CREATED=0
MERGES=0
```

## Required result envelope

```text
STAGE8_FIRST_SCHEDULED_FAILURE_DIAGNOSTIC_RESULT=PASS_ROOT_CAUSE_CONFIRMED

DAILY_RUN_ID=c43274fd-cb86-4004-9f1c-b88ddc33dd6a
DAILY_RUN_STATUS=FAILED
DAILY_OI_SUBJOB_STATUS=FAILED
RADAR_SUBJOB_STATUS=FAILED

DAILY_OI_SAFE_ERROR_CLASS=PendingRollbackError
DAILY_OI_SAFE_ERROR_CODE=NOT_PERSISTED
DAILY_OI_SAFE_ERROR_MESSAGE=NOT_PERSISTED
RADAR_SAFE_ERROR_CLASS=PendingRollbackError
RADAR_SAFE_ERROR_CODE=NOT_PERSISTED
RADAR_SAFE_ERROR_MESSAGE=NOT_PERSISTED

FAILURE_OCCURRED_BEFORE_NIGHTWATCH_CLIENT=NO
FIRST_FAILING_OPERATION=duplicate DailyOiArchiveTicker VENDOR_ERROR insert for existing archive_run_id+AAPL
FIRST_FAILING_CODE_PATH=backend/app/scanner/archive.py:113-122

DAILY_OI_RUNS_BEFORE_RADAR=YES
RADAR_REQUIRES_DAILY_OI_SUCCESS=NO
RADAR_FAILURE_IS_CASCADE_FROM_DAILY_OI=YES

ROLLBACK_WARNING_IS_ROOT_CAUSE=NO
SESSION_STATE_INVALIDATED_BEFORE_ROLLBACK=YES

PRIMARY_FAILURE_CLASSIFICATION=LOCAL_ORCHESTRATION_LOGIC
PRIMARY_ROOT_CAUSE=NightwatchError handler duplicated an existing per-run ticker row; unique-key failure plus missing rollback masked the original error and poisoned the shared session
ROOT_CAUSE_CONFIDENCE=HIGH

CLI_EXIT_CODE_ON_INTERNAL_FAILED=0
CLI_FALSE_GREEN_CONFIRMED=YES
FALSE_GREEN_CODE_PATH=backend/app/cli.py:284-294
EXPECTED_CORRECT_EXIT_SEMANTICS=success/no-new-data/explicit scheduler skip -> 0; blocking FAILED/PARTIAL -> non-zero

EVENING_READINESS_RESULT=RADAR_COVERAGE_INCOMPLETE
EVENING_MISSING_RADAR_TICKERS=AAPL,AMZN,GOOGL,META,MSFT,NVDA,TSLA
EVENING_MAG7_SCAN_INVOKED=NO
EVENING_NIGHTWATCH_PAID_UNITS=0
EVENING_BASELINES_CREATED=0

DAILY_OI_RUN_ROW_CREATED=YES
DAILY_OI_TICKER_ROWS_ADDED=1
RADAR_COVERAGE_ROWS_ADDED=0
RADAR_EVENT_ROWS_ADDED=0
CONTRACT_OI_ROWS_ADDED=0
PARTIAL_RUNTIME_WRITES_FOUND=YES

REMEDIATION_REQUIRED=YES
PRIMARY_REMEDIATION_FILES=backend/app/scanner/archive.py; backend/app/scanner/daily.py; backend/tests/test_stage4a_daily_pipeline.py
FALSE_GREEN_REMEDIATION_FILES=backend/app/cli.py; backend/tests/test_stage4a_daily_pipeline.py; backend/tests/test_stage8_daily_automation_workflow.py
MIGRATION_REQUIRED=NO
HISTORICAL_REPAIR_REQUIRED=NO
PAID_RUNTIME_RETEST_REQUIRED_AFTER_FIX=NO

NIGHTWATCH_REQUESTS=0
PAID_UNITS=0
REMOTE_APPLICATION_DATA_WRITES=0
REMOTE_SCHEMA_WRITES=0
WORKFLOWS_DISPATCHED=0
CODE_CHANGES=0

PRIMARY_REPORT_PATH=F:\options-anomaly-scanner-stage8\docs\evidence\stage8\NIGHTWATCH_VNEXT_STAGE8_FIRST_SCHEDULED_RUNTIME_FAILURE_DIAGNOSTIC_REPORT_20260826.md
CANONICAL_REPORT_PATH=F:\options-anomaly-scanner\docs\evidence\NIGHTWATCH_VNEXT_STAGE8_FIRST_SCHEDULED_RUNTIME_FAILURE_DIAGNOSTIC_REPORT_20260826.md
PRIMARY_REPORT_SHA256=COMPUTED_AFTER_FINAL_BYTES
CANONICAL_REPORT_SHA256=COMPUTED_AFTER_FINAL_BYTES
REPORT_BACKUP_BYTE_IDENTICAL=VERIFIED_AFTER_FINAL_BYTES

STAGE8_STATUS=CONTINUE_OBSERVATION
NEXT_AUTHORIZED_STAGE=NONE
```

The report SHA-256 values are computed after final bytes are fixed and returned with the task result. Embedding a file's own final digest inside itself would change those bytes.


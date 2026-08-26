# Nightwatch vNext — Stage 8 First Scheduled Runtime Failure Diagnostic — Execution Package

**Date:** 2026-08-26  
**Purpose:** Diagnose the first naturally scheduled Stage 8 morning archive failure and the false-green GitHub job semantics without making any paid/vendor/runtime writes.  
**Founder context:** First natural scheduled cycle after deployment.  
**Canonical repo:** `F:\options-anomaly-scanner`  
**Stage 8 worktree:** `F:\options-anomaly-scanner-stage8`  
**Canonical evidence root:** `F:\options-anomaly-scanner\docs\evidence`

---

# 0. Known runtime evidence

Morning scheduled job:

```text
workflow = Phase 2A Daily Archive and vNext Observation
job = radar-oi-archive
command = python -m app.cli archive-mag7-daily --mode radar-oi --scheduled

daily_run_id = c43274fd-cb86-4004-9f1c-b88ddc33dd6a
status = FAILED
subjobs = daily_oi:FAILED, radar:FAILED
consumed_units = 0
network_attempts = 0
elapsed_seconds = 5.259
```

Visible warning:

```text
backend/app/scanner/daily.py:201:
SAWarning: Session's state has been changed on a non-active transaction - this state will be discarded.
self.session.rollback()
```

GitHub nevertheless showed the morning job as green/success.

Evening naturally scheduled observation then failed safely before scan with:

```text
RADAR_COVERAGE_INCOMPLETE
missing=AAPL,AMZN,GOOGL,META,MSFT,NVDA,TSLA
unexpected=NONE
exit code 4
```

Do not reinterpret the evening gate as the primary defect. It correctly blocked the paid scan because morning Radar coverage was absent.

---

# 1. Hard authorization boundary

Authorized:

```text
read repository/code/history
read GitHub workflow/job metadata and logs
read-only Supabase/runtime DB queries
read-only inspection of daily_run_id and all related subjob/error/coverage rows
inspect exception handling / transaction handling / CLI exit semantics
run local/offline tests with mocks
create diagnostic report
```

Forbidden:

```text
Nightwatch requests
MAG7 scan
workflow dispatch
manual rerun
paid units
remote application-data writes
remote schema writes
migration
code changes
test changes
workflow changes
commit/push/PR/merge
Forward Outcome
```

Required:

```text
NIGHTWATCH_REQUESTS=0
PAID_UNITS=0
REMOTE_APPLICATION_DATA_WRITES=0
REMOTE_SCHEMA_WRITES=0
WORKFLOWS_DISPATCHED=0
CODE_CHANGES=0
```

---

# 2. Canonical evidence

Read completely at minimum:

```text
F:\options-anomaly-scanner\docs\evidence\NIGHTWATCH_VNEXT_CANONICAL_EVIDENCE_MANIFEST.md
F:\options-anomaly-scanner\docs\evidence\NIGHTWATCH_SCANNER_VNEXT_INTEGRATED_SPEC_PROMPT_20260817(1).md
F:\options-anomaly-scanner\docs\evidence\NIGHTWATCH_VNEXT_STAGE4A_DAILY_PIPELINE_CODEX_EXECUTION_PACKAGE_20260818.md
F:\options-anomaly-scanner\docs\evidence\NIGHTWATCH_VNEXT_STAGE8_DAILY_AUTOMATION_DEPLOYMENT_GATE_REPORT_20260825.md
F:\options-anomaly-scanner\docs\evidence\NIGHTWATCH_VNEXT_STAGE8_DAILY_AUTOMATION_GITHUB_DEPLOYMENT_REPORT_20260825.md
```

If this package is attached and absent from canonical evidence, preserve it byte-for-byte as:

```text
F:\options-anomaly-scanner\docs\evidence\NIGHTWATCH_VNEXT_STAGE8_FIRST_SCHEDULED_RUNTIME_FAILURE_DIAGNOSTIC_EXECUTION_PACKAGE_20260826.md
```

Conflict => HOLD; never overwrite differing canonical evidence.

---

# 3. DB target identity gate

Use the same canonical runtime configuration mechanism already accepted for remote Supabase access.

Do not print credentials or full DATABASE_URL.

Return:

```text
DB_TARGET_HOST=
DB_TARGET_PORT=
DB_TARGET_DATABASE=
DB_TARGET_IS_LOCALHOST=
DB_TARGET_IDENTITY_GATE=PASS/FAIL
```

Expected non-local Supabase target.

Read-only only.

---

# 4. Inspect the exact failed daily run

For:

```text
daily_run_id=c43274fd-cb86-4004-9f1c-b88ddc33dd6a
```

Read all persisted run/subjob/error/coverage/audit rows that can explain:

```text
daily_oi:FAILED
radar:FAILED
network_attempts=0
```

Return at minimum:

```text
DAILY_RUN_STATUS=
DAILY_OI_SUBJOB_STATUS=
RADAR_SUBJOB_STATUS=

DAILY_OI_SAFE_ERROR_CLASS=
DAILY_OI_SAFE_ERROR_CODE=
DAILY_OI_SAFE_ERROR_MESSAGE=

RADAR_SAFE_ERROR_CLASS=
RADAR_SAFE_ERROR_CODE=
RADAR_SAFE_ERROR_MESSAGE=

FAILURE_OCCURRED_BEFORE_NIGHTWATCH_CLIENT=YES/NO
FIRST_FAILING_OPERATION=
FIRST_FAILING_CODE_PATH=
```

If detailed error information was not persisted, say:

```text
PERSISTED_ERROR_DETAIL_AVAILABLE=NO
```

Do not invent it.

---

# 5. Determine whether radar failure is primary or cascading

Trace orchestration order from current code.

Answer:

```text
DAILY_OI_RUNS_BEFORE_RADAR=YES/NO
RADAR_REQUIRES_DAILY_OI_SUCCESS=YES/NO
RADAR_FAILURE_IS_CASCADE_FROM_DAILY_OI=YES/NO/UNRESOLVED
```

If Radar was never attempted because Daily OI failed, do not describe two independent root causes.

---

# 6. Transaction/session diagnostic

Inspect current code around the exact rollback warning, especially:

```text
backend/app/scanner/daily.py
```

and all repository/service calls involved before the first network attempt.

Determine:

```text
ACTIVE_TRANSACTION_EXPECTED_AT_FAILURE_POINT=YES/NO
ROLLBACK_WARNING_IS_ROOT_CAUSE=YES/NO/SECONDARY/UNRESOLVED
SESSION_STATE_INVALIDATED_BEFORE_ROLLBACK=YES/NO
```

Trace likely sequence:

```text
session begin / implicit transaction
DB read/write/preflight
exception
rollback
SAWarning
```

Identify the original exception if possible from persisted state/code behavior.

Do not promote the SAWarning to root cause unless evidence proves it.

---

# 7. Zero-network failure classification

Because:

```text
network_attempts=0
consumed_units=0
```

classify the first failure into exactly one best-supported category:

```text
DB_CONNECTION_OR_TRANSACTION
DB_SCHEMA_OR_CONSTRAINT
RUNTIME_CONFIGURATION
TRADING_SESSION_OR_DATE_GATE
LOCAL_ORCHESTRATION_LOGIC
SECRET_OR_ENVIRONMENT_VALIDATION
OTHER_CONFIRMED
UNRESOLVED
```

Return:

```text
PRIMARY_FAILURE_CLASSIFICATION=
PRIMARY_ROOT_CAUSE=
ROOT_CAUSE_CONFIDENCE=HIGH/MEDIUM/LOW
```

Support it with exact code/runtime evidence.

---

# 8. False-green GitHub semantics diagnostic

Explain why this command:

```text
python -m app.cli archive-mag7-daily --mode radar-oi --scheduled
```

returned a successful process exit even though the application result was:

```text
status=FAILED
daily_oi=FAILED
radar=FAILED
```

Return:

```text
CLI_EXIT_CODE_ON_INTERNAL_FAILED=
CLI_FALSE_GREEN_CONFIRMED=YES/NO
FALSE_GREEN_CODE_PATH=
EXPECTED_CORRECT_EXIT_SEMANTICS=
```

Expected design principle:

```text
true collection success -> exit 0
legitimate scheduler skip -> explicit truthful skip semantics
blocking FAILED/PARTIAL -> non-zero exit
```

Do not change code in this diagnostic.

---

# 9. Evening gate proof

Read-only verify the evening failure corresponding to the same NY market date.

Return:

```text
EVENING_READINESS_RESULT=RADAR_COVERAGE_INCOMPLETE
EVENING_MISSING_RADAR_TICKERS=
EVENING_MAG7_SCAN_INVOKED=YES/NO
EVENING_NIGHTWATCH_PAID_UNITS=
EVENING_BASELINES_CREATED=
```

Expected safe behavior is no scan if prerequisites were absent.

---

# 10. Data-state impact

Determine what, if anything, was persisted by the morning failed run:

```text
DAILY_OI_RUN_ROW_CREATED=
DAILY_OI_TICKER_ROWS_ADDED=
RADAR_COVERAGE_ROWS_ADDED=
RADAR_EVENT_ROWS_ADDED=
CONTRACT_OI_ROWS_ADDED=
PARTIAL_RUNTIME_WRITES_FOUND=
```

Missing/failed must remain truthful.

Do not repair or delete anything.

---

# 11. Remediation recommendation — design only

Provide the smallest remediation scope needed.

Separate:

```text
R1 = primary morning archive root-cause fix
R2 = false-green CLI exit semantics fix
```

State exact files expected to change.

Return:

```text
REMEDIATION_REQUIRED=YES/NO
PRIMARY_REMEDIATION_FILES=
FALSE_GREEN_REMEDIATION_FILES=
MIGRATION_REQUIRED=YES/NO
HISTORICAL_REPAIR_REQUIRED=YES/NO
PAID_RUNTIME_RETEST_REQUIRED_AFTER_FIX=YES/NO
```

Prefer no historical repair if failed rows truthfully represent the failure.

Do not implement remediation in this task.

---

# 12. Diagnostic result

Use exactly one:

```text
STAGE8_FIRST_SCHEDULED_FAILURE_DIAGNOSTIC_RESULT=PASS_ROOT_CAUSE_CONFIRMED
STAGE8_FIRST_SCHEDULED_FAILURE_DIAGNOSTIC_RESULT=PASS_ROOT_CAUSE_PARTIALLY_CONFIRMED
STAGE8_FIRST_SCHEDULED_FAILURE_DIAGNOSTIC_RESULT=HOLD_INSUFFICIENT_RUNTIME_EVIDENCE
STAGE8_FIRST_SCHEDULED_FAILURE_DIAGNOSTIC_RESULT=HOLD_DB_UNAVAILABLE
```

---

# 13. Evidence report

Primary:

```text
F:\options-anomaly-scanner-stage8\docs\evidence\stage8\NIGHTWATCH_VNEXT_STAGE8_FIRST_SCHEDULED_RUNTIME_FAILURE_DIAGNOSTIC_REPORT_20260826.md
```

Canonical byte-identical backup:

```text
F:\options-anomaly-scanner\docs\evidence\NIGHTWATCH_VNEXT_STAGE8_FIRST_SCHEDULED_RUNTIME_FAILURE_DIAGNOSTIC_REPORT_20260826.md
```

Verify SHA-256 for both.

Conflict => HOLD; never overwrite.

---

# 14. Required final fields

```text
STAGE8_FIRST_SCHEDULED_FAILURE_DIAGNOSTIC_RESULT=

DAILY_RUN_ID=c43274fd-cb86-4004-9f1c-b88ddc33dd6a
DAILY_RUN_STATUS=
DAILY_OI_SUBJOB_STATUS=
RADAR_SUBJOB_STATUS=

DAILY_OI_SAFE_ERROR_CLASS=
DAILY_OI_SAFE_ERROR_CODE=
DAILY_OI_SAFE_ERROR_MESSAGE=
RADAR_SAFE_ERROR_CLASS=
RADAR_SAFE_ERROR_CODE=
RADAR_SAFE_ERROR_MESSAGE=

FAILURE_OCCURRED_BEFORE_NIGHTWATCH_CLIENT=
FIRST_FAILING_OPERATION=
FIRST_FAILING_CODE_PATH=

DAILY_OI_RUNS_BEFORE_RADAR=
RADAR_REQUIRES_DAILY_OI_SUCCESS=
RADAR_FAILURE_IS_CASCADE_FROM_DAILY_OI=

ROLLBACK_WARNING_IS_ROOT_CAUSE=
SESSION_STATE_INVALIDATED_BEFORE_ROLLBACK=

PRIMARY_FAILURE_CLASSIFICATION=
PRIMARY_ROOT_CAUSE=
ROOT_CAUSE_CONFIDENCE=

CLI_EXIT_CODE_ON_INTERNAL_FAILED=
CLI_FALSE_GREEN_CONFIRMED=
FALSE_GREEN_CODE_PATH=
EXPECTED_CORRECT_EXIT_SEMANTICS=

EVENING_READINESS_RESULT=
EVENING_MISSING_RADAR_TICKERS=
EVENING_MAG7_SCAN_INVOKED=
EVENING_NIGHTWATCH_PAID_UNITS=
EVENING_BASELINES_CREATED=

DAILY_OI_RUN_ROW_CREATED=
DAILY_OI_TICKER_ROWS_ADDED=
RADAR_COVERAGE_ROWS_ADDED=
RADAR_EVENT_ROWS_ADDED=
CONTRACT_OI_ROWS_ADDED=
PARTIAL_RUNTIME_WRITES_FOUND=

REMEDIATION_REQUIRED=
PRIMARY_REMEDIATION_FILES=
FALSE_GREEN_REMEDIATION_FILES=
MIGRATION_REQUIRED=
HISTORICAL_REPAIR_REQUIRED=
PAID_RUNTIME_RETEST_REQUIRED_AFTER_FIX=

NIGHTWATCH_REQUESTS=0
PAID_UNITS=0
REMOTE_APPLICATION_DATA_WRITES=0
REMOTE_SCHEMA_WRITES=0
WORKFLOWS_DISPATCHED=0
CODE_CHANGES=0

PRIMARY_REPORT_PATH=
CANONICAL_REPORT_PATH=
PRIMARY_REPORT_SHA256=
CANONICAL_REPORT_SHA256=
REPORT_BACKUP_BYTE_IDENTICAL=

STAGE8_STATUS=CONTINUE_OBSERVATION
NEXT_AUTHORIZED_STAGE=NONE
```

STOP.

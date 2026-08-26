# Nightwatch vNext — Stage 8 Failed Scan Root-Cause Diagnostic — Execution Package

**Date:** 2026-08-20  
**Purpose:** Diagnose the single controlled MAG7 scan failure without making any new paid call or changing application state.  
**Worktree:** `F:\options-anomaly-scanner-stage8`  
**Branch:** `vnext/stage8-mag7-observation`  
**HEAD/base:** `3a63eaa1b9069d34199704fe31ac6466e8929d7d`

## 0. Trigger

The one Founder-authorized controlled MAG7 observation completed with:

```text
CONTROLLED_OBSERVATION_RESULT=FAIL_SCAN
SCAN_RUN_ID=090359ad-9d76-49b9-8902-f28ac54a1d1b
SCAN_STATUS=FAILED
NIGHTWATCH_REQUESTS=14
PAID_UNITS=14
```

All 14 Nightwatch calls returned HTTP 200. The scanner failed later with sanitized SQLAlchemy:

```text
DataError
```

Persisted stage evidence shows:

```text
S0_PREFLIGHT_V11=COMPLETE
S2_ACTIVITY_SURFACE_V12=COMPLETE
S3_DISCOVERY_CONFIRMATION=COMPLETE
S3_VNEXT_ACTIVE_DISCOVERY=COMPLETE
S5 structure stage did not complete
```

This task diagnoses that failure only.

## 1. Canonical evidence root

Read from:

```text
F:\options-anomaly-scanner\docs\evidence
```

Read completely:

```text
F:\options-anomaly-scanner\docs\evidence\NIGHTWATCH_VNEXT_CANONICAL_EVIDENCE_MANIFEST.md
F:\options-anomaly-scanner\docs\evidence\NIGHTWATCH_SCANNER_VNEXT_INTEGRATED_SPEC_PROMPT_20260817(1).md
F:\options-anomaly-scanner\docs\evidence\NIGHTWATCH_VNEXT_STAGE8_MAG7_OBSERVATION_EXECUTION_PACKAGE_20260820.md
F:\options-anomaly-scanner\docs\evidence\NIGHTWATCH_VNEXT_STAGE8_RUNTIME_DEPLOYMENT_GATE_EXECUTION_PACKAGE_20260820.md
F:\options-anomaly-scanner\docs\evidence\NIGHTWATCH_VNEXT_CONTROLLED_LIVE_MAG7_OBSERVATION_EXECUTION_PACKAGE_20260820.md
```

Also read:

```text
F:\options-anomaly-scanner-stage8\docs\evidence\stage8\NIGHTWATCH_VNEXT_STAGE8_RUNTIME_DEPLOYMENT_GATE_REPORT_20260820.md

F:\options-anomaly-scanner-stage8\docs\evidence\stage8\NIGHTWATCH_VNEXT_CONTROLLED_LIVE_MAG7_OBSERVATION_REPORT_20260820.md
```

Do not ask the Founder to re-upload files already present.

## 2. Hard authorization boundary

Authorized:

```text
repository/code read
read-only runtime DB SELECTs
read-only inspection of persisted ScanRun / stages / source rows
read-only inspection of raw_vendor_payloads already persisted by the failed scan
local/offline reproduction using existing persisted payloads or fixtures
local test execution that makes zero Nightwatch calls
sanitized diagnostic evidence files
```

Not authorized:

```text
MAG7 scan
Nightwatch request
Phase2B refresh
Dealer/GEX live request
remote DB INSERT/UPDATE/DELETE
remote schema write
migration
workflow dispatch
scheduler change
application code edit
test code edit
manual data repair
commit/push/PR/merge
```

Expected:

```text
NIGHTWATCH_REQUESTS=0
PAID_UNITS=0
REMOTE_DB_WRITES=0
APPLICATION_CODE_CHANGES=0
```

## 3. First objective — find the exact DataError

Do not stop at the class name `DataError`.

Trace the one failed run:

```text
SCAN_RUN_ID=090359ad-9d76-49b9-8902-f28ac54a1d1b
```

Determine, if possible without a new scan:

```text
exact failing function
exact SQL statement / ORM operation class
exact target table
exact target column(s)
exact offending value or value shape
PostgreSQL/driver error code
original DBAPI error text
```

Sanitize any credential or sensitive vendor material.

Search:

```text
application logs if locally retained
ScanRun / ScanStage persisted summaries
SQLAlchemy exception handling paths
database constraints / column definitions
values selected for S5 structure processing
saved raw payloads from the failed run
```

Return:

```text
DATAERROR_ROOT_CAUSE_IDENTIFIED=YES/NO
FAILING_STAGE=
FAILING_FUNCTION=
TARGET_TABLE=
TARGET_COLUMN=
DB_ERROR_CODE=
SANITIZED_DB_ERROR=
OFFENDING_VALUE_SHAPE=
```

If exact DBAPI error text is no longer available, say so. Do not fabricate.

## 4. Locate the failure boundary precisely

Use persisted stage/run evidence and code flow to determine the narrowest supported boundary.

At minimum trace:

```text
S3 active route selection
→ deep-dive ticker/expiry selection
→ S5 structure preparation
→ DB write/read operation immediately preceding failure
```

Return:

```text
LAST_CONFIRMED_SUCCESSFUL_OPERATION=
FIRST_UNCONFIRMED_OPERATION=
FAILURE_BOUNDARY_CONFIDENCE=HIGH/MEDIUM/LOW
```

Do not infer successful execution past the last persisted evidence.

## 5. Inspect Stage 4A/4B → S5 data shape

The failed run persisted:

```text
104 expiry rows
17 deep_dive_eligible expiry rows
10 selected expiry rows
4 deep-dive tickers
```

Read the exact selected rows for the failed run and inspect every value that flows into the first S5 structure DB operation.

Check especially for:

```text
numeric precision / scale overflow
integer range overflow
string length overflow
invalid enum/check value
invalid datetime/date value
NaN / Infinity
Decimal conversion
JSON serialization shape
UUID/type mismatch
NULL sent to non-nullable column
foreign-key identity mismatch
```

Do not change the values.

Return a table:

```text
FIELD
SOURCE
VALUE_SHAPE / SAFE SANITIZED VALUE
TARGET TYPE
CONSTRAINT
VALID=YES/NO/UNRESOLVED
```

## 6. Compare ORM and migration schema

For every table/column touched between the last confirmed S3 operation and the expected S5 structure completion, compare:

```text
SQLAlchemy ORM type
Alembic/database type
nullable
precision/scale
length
enum/check constraints
FK
```

Return:

```text
ORM_DB_SCHEMA_MISMATCH_FOUND=YES/NO
```

If YES, identify exact mismatch.

## 7. Reproduction without vendor calls

If the saved persisted source rows/raw payloads are sufficient, attempt a zero-paid local/offline reproduction of the failing transformation.

Rules:

```text
no Nightwatch request
no remote DB write
no mutation of the failed ScanRun
```

Preferred order:

1. pure function/unit-level replay from saved values;
2. local test harness using existing fixtures/persisted payload snapshot;
3. transactionally isolated local PostgreSQL only if already available.

Do NOT use the remote runtime for speculative writes even if rolled back.

Return:

```text
ZERO_PAID_REPRODUCTION_ATTEMPTED=YES/NO
ZERO_PAID_REPRODUCTION_RESULT=REPRODUCED/NOT_REPRODUCED/NOT_POSSIBLE
```

If reproduced, capture the exact sanitized exception.

## 8. Determine defect class

Classify only from evidence:

```text
SCHEMA_TYPE_DEFECT
PARSER_NORMALIZATION_DEFECT
S5_STRUCTURE_PERSISTENCE_DEFECT
LEGACY_DATA_COMPATIBILITY_DEFECT
UNEXPECTED_VENDOR_VALUE_SHAPE
OTHER
UNRESOLVED
```

Return:

```text
DEFECT_CLASS=
DEFECT_IS_DETERMINISTIC_WITH_SAME_INPUT=YES/NO/UNRESOLVED
SECOND_PAID_SCAN_WOULD_LIKELY_REFAIL=YES/NO/UNRESOLVED
```

Do not authorize or run a second scan.

## 9. Scope the narrowest remediation — design only

If root cause is identified, propose the smallest safe remediation scope.

Return:

```text
REMEDIATION_REQUIRED=YES/NO/UNRESOLVED
EXPECTED_FILES_TO_CHANGE=
MIGRATION_REQUIRED=YES/NO/UNRESOLVED
HISTORICAL_DATA_REPAIR_REQUIRED=YES/NO/UNRESOLVED
```

Do not edit those files in this task.

If a migration appears required, explain why. Do not create it.

## 10. Verify the failed run remains truthful

Confirm read-only:

```text
ScanRun.status=FAILED
safe_error=DataError
candidate_materialization markers remain NULL/unmaterialized
ProductCandidate rows linked to this run=0
ProductCandidateTrigger rows linked to this run=0
baseline rows linked to this run=0
```

No repair.

Return:

```text
FAILED_RUN_STATE_TRUTHFUL=YES/NO
PARTIAL_PRODUCT_CANDIDATE_STATE_FOUND=YES/NO
```

## 11. Evidence report

Create:

```text
F:\options-anomaly-scanner-stage8\docs\evidence\stage8\NIGHTWATCH_VNEXT_STAGE8_FAILED_SCAN_ROOT_CAUSE_DIAGNOSTIC_REPORT_20260820.md
```

## 12. Result

Use exactly one:

```text
FAILED_SCAN_DIAGNOSTIC_RESULT=ROOT_CAUSE_CONFIRMED
FAILED_SCAN_DIAGNOSTIC_RESULT=ROOT_CAUSE_NARROWED_NOT_CONFIRMED
FAILED_SCAN_DIAGNOSTIC_RESULT=INSUFFICIENT_EVIDENCE
FAILED_SCAN_DIAGNOSTIC_RESULT=BLOCKING_SCHEMA_DEFECT_CONFIRMED
```

Return:

```text
DATAERROR_ROOT_CAUSE_IDENTIFIED=
FAILING_STAGE=
FAILING_FUNCTION=
TARGET_TABLE=
TARGET_COLUMN=
DB_ERROR_CODE=
SANITIZED_DB_ERROR=
DEFECT_CLASS=

ZERO_PAID_REPRODUCTION_ATTEMPTED=
ZERO_PAID_REPRODUCTION_RESULT=

ORM_DB_SCHEMA_MISMATCH_FOUND=
REMEDIATION_REQUIRED=
EXPECTED_FILES_TO_CHANGE=
MIGRATION_REQUIRED=
HISTORICAL_DATA_REPAIR_REQUIRED=

FAILED_RUN_STATE_TRUTHFUL=
PARTIAL_PRODUCT_CANDIDATE_STATE_FOUND=

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

SECOND_MAG7_SCAN_AUTHORIZED=NO
STAGE8_OBSERVATION_RESUME_READY=NO
STAGE9_READY=NO
NEXT_AUTHORIZED_STAGE=NONE
```

STOP.

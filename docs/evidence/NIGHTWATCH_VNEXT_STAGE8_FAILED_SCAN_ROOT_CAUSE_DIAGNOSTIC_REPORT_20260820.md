# Nightwatch vNext — Stage 8 Failed Scan Root-Cause Diagnostic Report

Date: 2026-08-20  
Worktree: `F:\options-anomaly-scanner-stage8`  
Branch: `vnext/stage8-mag7-observation`  
HEAD/base: `3a63eaa1b9069d34199704fe31ac6466e8929d7d`  
Failed ScanRun: `090359ad-9d76-49b9-8902-f28ac54a1d1b`  
Diagnostic package SHA-256: `D3766CB749F13F442EA6FECE573E9F90DFDE42CCD84011B2CE79EEC709083576`

## Executive result

```text
FAILED_SCAN_DIAGNOSTIC_RESULT=ROOT_CAUSE_CONFIRMED
DATAERROR_ROOT_CAUSE_IDENTIFIED=YES

FAILING_STAGE=S4_VNEXT_DEEP_DIVE_BUDGET_SELECTION telemetry persistence, before S5
FAILING_FUNCTION=app.scanner.service.Mag7Scanner._stage, called by app.scanner.v13.Mag7Scanner._select_dual
TARGET_TABLE=scan_stages
TARGET_COLUMN=stage
DB_ERROR_CODE=22001_DERIVED_ORIGINAL_NOT_RETAINED
SANITIZED_DB_ERROR=Original DBAPI text was not retained; evidence deterministically maps to PostgreSQL string_data_right_truncation for a 35-character value assigned to VARCHAR(32)
OFFENDING_VALUE_SHAPE=str(length=35,value=S4_VNEXT_DEEP_DIVE_BUDGET_SELECTION,overflow=3)

DEFECT_CLASS=OTHER:S4_SCAN_STAGE_IDENTIFIER_LENGTH_DEFECT
DEFECT_IS_DETERMINISTIC_WITH_SAME_INPUT=YES
SECOND_PAID_SCAN_WOULD_LIKELY_REFAIL=YES

ZERO_PAID_REPRODUCTION_ATTEMPTED=YES
ZERO_PAID_REPRODUCTION_RESULT=REPRODUCED

ORM_DB_SCHEMA_MISMATCH_FOUND=NO
REMEDIATION_REQUIRED=YES
EXPECTED_FILES_TO_CHANGE=backend/app/scanner/v13.py; backend/tests/test_stage4b_phase2a_vnext.py
MIGRATION_REQUIRED=NO
HISTORICAL_DATA_REPAIR_REQUIRED=NO

FAILED_RUN_STATE_TRUTHFUL=YES
PARTIAL_PRODUCT_CANDIDATE_STATE_FOUND=NO

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

The failed scan did not enter S5 structure processing. `v13.Mag7Scanner._select_dual()` successfully committed the ten selected-expiry flags and four selected-ticker flags, then immediately called `_stage("S4_VNEXT_DEEP_DIVE_BUDGET_SELECTION", ...)`. `_stage()` constructs a `ScanStage` and commits it. The identifier is 35 characters, while both the SQLAlchemy model and deployed PostgreSQL column define `scan_stages.stage` as non-null `VARCHAR(32)`. The expected S4 stage row is absent, the persisted safe exception is `DataError`, and psycopg maps PostgreSQL SQLSTATE `22001` to its `StringDataRightTruncation` subclass of `DataError`.

The original `DBAPIError.orig` object and PostgreSQL server message were not persisted and no retained application log contains them. Therefore this report does not claim to quote the original error text. SQLSTATE `22001` and the usual string-truncation meaning are derived from the exact, deterministic value/type conflict and the recorded SQLAlchemy class.

## Authorization and evidence preservation

The attached diagnostic package was saved byte-for-byte to:

```text
F:\options-anomaly-scanner\docs\evidence\NIGHTWATCH_VNEXT_STAGE8_FAILED_SCAN_ROOT_CAUSE_DIAGNOSTIC_EXECUTION_PACKAGE_20260820.md
```

Attachment and canonical package hashes are identical:

```text
SHA256=D3766CB749F13F442EA6FECE573E9F90DFDE42CCD84011B2CE79EEC709083576
BYTE_IDENTICAL=YES
```

All seven governing/report files named by the package were present at their explicit paths and read completely. No existing report or evidence file was overwritten or modified.

## Evidence chain

### 1. Truthful failed-run state

Read-only runtime evidence remains:

```text
ScanRun.status=FAILED
ScanRun.summary.safe_error=DataError
candidate_materialized_at=NULL
candidate_materialization_rule_version=NULL
candidate_materialization_rule_hash=NULL
ProductCandidate rows linked to run=0
ProductCandidateTrigger rows linked to run=0
ProductCandidateContext rows linked to run=0
AnomalyContextDetail rows linked to run=0
```

This is internally consistent with candidate materialization being restricted to successful `COMPLETE` scans. No partial Stage 5/6 entity state exists.

### 2. Persisted stage boundary

Persisted stages, in order:

| Stage | Status |
|---|---|
| `S0_PREFLIGHT_V11` | COMPLETE |
| `S2_ACTIVITY_SURFACE_V12` | COMPLETE |
| `S3_DISCOVERY_CONFIRMATION` | COMPLETE |
| `S3_VNEXT_ACTIVE_DISCOVERY` | COMPLETE |

There is no `S4_VNEXT_DEEP_DIVE_BUDGET_SELECTION` row and no S5 row.

At the same time, selection state from `_select_dual()` is durably present:

```text
DEEP_DIVE_ELIGIBLE_EXPIRIES=17
SELECTED_EXPIRIES=10
SELECTED_TICKERS=4
```

The code commits those selection flags immediately before calling `_stage()`. This proves the selection commit succeeded and isolates the next database operation to the S4 `ScanStage` insert/commit.

```text
LAST_CONFIRMED_SUCCESSFUL_OPERATION=v13.Mag7Scanner._select_dual self.session.commit() persisting selected_for_deep_scan for 10 expiries and 4 tickers
FIRST_UNCONFIRMED_OPERATION=service.Mag7Scanner._stage insertion/commit of S4_VNEXT_DEEP_DIVE_BUDGET_SELECTION into scan_stages
FAILURE_BOUNDARY_CONFIDENCE=HIGH
```

### 3. Exact failing operation

The application call is:

```python
self._stage(
    "S4_VNEXT_DEEP_DIVE_BUDGET_SELECTION",
    ...
)
```

`service.Mag7Scanner._stage()` performs:

```text
construct ScanStage
session.add(row)
session.commit()
```

Sanitized SQL operation class:

```sql
INSERT INTO scan_stages
  (scan_run_id, stage, status, started_at, completed_at, details)
VALUES
  (..., 'S4_VNEXT_DEEP_DIVE_BUDGET_SELECTION', 'COMPLETE', ..., ..., ...)
```

The exact driver-rendered SQL and parameter collection were not retained, so the statement above is a faithful sanitized operation shape rather than a verbatim server log.

### 4. Offending value proof

```text
VALUE=S4_VNEXT_DEEP_DIVE_BUDGET_SELECTION
PYTHON_TYPE=str
CHARACTER_LENGTH=35
ORM_DECLARED_LENGTH=32
RUNTIME_DB_DECLARED_LENGTH=32
EXCESS_CHARACTERS=3
```

PostgreSQL SQLSTATE lookup performed locally:

```text
SQLSTATE=22001
PSYCOPG_EXCEPTION_CLASS=StringDataRightTruncation
PSYCOPG_BASE_CLASS=DataError
RECORDED_SQLALCHEMY_SAFE_ERROR=DataError
```

The recorded error class, missing S4 row, preceding committed selection flags, fixed 35-character identifier, and deployed 32-character column form one consistent causal chain. No vendor-specific value is necessary to trigger it.

## Field/type inspection

Values flowing into the first unconfirmed database operation:

| Field | Source | Safe value shape | Target type | Constraint | Valid |
|---|---|---|---|---|---|
| `scan_run_id` | Current failed ScanRun | UUID | PostgreSQL `uuid` | NOT NULL, FK `scan_runs.id` | YES |
| `stage` | Fixed literal in `v13._select_dual` | string length 35 | `VARCHAR(32)` | NOT NULL; unique with `scan_run_id` | **NO** |
| `status` | `_stage` default | `COMPLETE`, length 8 | `VARCHAR(32)` | NOT NULL | YES |
| `started_at` | `utc_now()` | aware UTC datetime | `TIMESTAMPTZ` | NOT NULL | YES |
| `completed_at` | same `utc_now()` value | aware UTC datetime | `TIMESTAMPTZ` | nullable | YES |
| `details.route_priority` | fixed list | 3 JSON strings | `JSONB` | part of NOT NULL `details` | YES |
| `details.selected_expiries` | computed selection | integer 10 | `JSONB` | JSON-serializable | YES |
| `details.eligible_expiries` | computed selection | integer 17 | `JSONB` | JSON-serializable | YES |
| `details.operational_truncation` | computed selection | boolean | `JSONB` | JSON-serializable | YES |
| `details.truncated_expiries` | selected rows | list of ticker/ISO-date objects | `JSONB` | JSON-serializable | YES |
| `details.candidate_identity_affected` | fixed literal | `false` | `JSONB` | JSON-serializable | YES |
| `details.deduplicated_chain_loads` | selected rows | integer 10 | `JSONB` | JSON-serializable | YES |

No invalid UUID, datetime, JSON, NULL, FK identity, or duplicate stage identity was found for the operation. The only invalid field is `stage`.

## Selected rows and downstream S5 value audit

Although S5 was never entered, all ten selected expiry rows and their available archive sources were inspected to rule out a competing downstream cause:

| Ticker | Expiration | Trigger families | Vendor OI date | Complete archive | Archived contracts |
|---|---|---|---|---|---:|
| AAPL | 2026-08-21 | EXPIRY_ACTIVITY | 2026-08-11 | YES | 190 |
| AAPL | 2026-08-28 | EXPIRY_ACTIVITY | 2026-08-11 | YES | 142 |
| AMZN | 2026-08-21 | EXPIRY_ACTIVITY | 2026-08-11 | NO | 0 |
| AMZN | 2026-08-28 | EXPIRY_ACTIVITY | 2026-08-11 | NO | 0 |
| AMZN | 2026-10-16 | RADAR_EVENT | 2026-08-11 | YES | 120 |
| META | 2026-08-21 | EXPIRY_ACTIVITY | 2026-08-11 | YES | 396 |
| META | 2026-08-28 | EXPIRY_ACTIVITY | 2026-08-11 | YES | 344 |
| NVDA | 2026-08-21 | RADAR_EVENT + EXPIRY_ACTIVITY | 2026-08-11 | YES | 216 |
| NVDA | 2026-09-04 | RADAR_EVENT | 2026-08-11 | YES | 132 |
| NVDA | 2026-10-16 | RADAR_EVENT | 2026-08-11 | YES | 154 |

Offline computation regenerated 1,694 potential `ContractScanObservation` values from the existing archive and five potential `StrikeCluster` values. This was diagnostic only; none was inserted.

| Field family | Rows checked | Target contract | Result |
|---|---:|---|---|
| Contract numeric values | 1,694 | Declared Numeric precision/scale for strike, quote, ratio, share and score columns | All within bounds |
| Contract integer values | 1,694 | Integer/BigInteger | All within bounds |
| Contract strings | 1,694 | Declared VARCHAR lengths | All within bounds |
| Contract JSONB values | 1,694 | Native JSON; no NaN/Infinity/unsupported type | All serializable |
| Contract UUID/FK values | 1,694 | Existing UUID identities | Valid source identities |
| Cluster numeric/string values | 5 | Declared Numeric/VARCHAR contracts | All within bounds |
| Cluster JSONB values | 5 | Native JSON | All serializable |

Representative maxima remained valid, including `neighbor_strike_ratio=804.8` for `NUMERIC(12,5)`, `spread_pct=2.0` for `NUMERIC(12,8)`, maximum strike `1480`, and maximum structure score `94.814`. These calculations reinforce that S5 data was not the failing input, but the persisted boundary already proves S5 was never reached.

## Persisted raw payload inspection

All 14 failed-run `raw_vendor_payloads` rows were inspected read-only without copying sensitive payload content into this report:

```text
PAYLOAD_ROWS=14
PAYLOAD_JSON_TYPES=14 object
TOP_LEVEL_KEYS_FOR_ALL=_meta,data
ENDPOINTS=7 expiry-breakdown + 7 options-volume
S2_ACTIVITY_SURFACE_V12=COMPLETE
```

Payload sizes were finite and the normal parsers completed sufficiently to persist 7 ticker rows and 104 expiry rows. No raw payload is read by the failing `_stage()` operation. Therefore the failure is not classified as an unexpected vendor shape or parser-normalization defect.

## ORM and database schema comparison

`ScanStage.stage` agreement:

| Layer | Definition |
|---|---|
| SQLAlchemy ORM | `String(32)`, non-null |
| Alembic `20260812_0003` | `sa.String(32)`, non-null |
| Runtime PostgreSQL | `character varying(32)`, non-null |

The relevant `contract_scan_observations`, `strike_clusters`, `contract_oi_daily_snapshots`, and `expiry_oi_daily_snapshots` columns were also compared across ORM and runtime catalog for type, nullable, length, numeric precision/scale, PK, FK and unique constraints. No mismatch was found.

```text
ORM_DB_SCHEMA_MISMATCH_FOUND=NO
```

This is an application-value-versus-declared-contract defect, not schema drift. Both schema layers agree; `v13.py` emits a value outside that contract.

## Zero-paid deterministic reproduction

The exact production literal and the actual ORM metadata were replayed locally:

```text
OFFENDING_STAGE=S4_VNEXT_DEEP_DIVE_BUDGET_SELECTION
OFFENDING_STAGE_LENGTH=35
ORM_TYPE=VARCHAR(32)
EXCEEDS_DECLARED_LENGTH=TRUE
OVERFLOW_CHARACTERS=3
ZERO_PAID_LOCAL_CONTRACT_REPLAY=REPRODUCED
```

This reproduces the deterministic value/type contract violation without a vendor request or database write. A local PostgreSQL server was not installed, and the package explicitly forbids speculative writes to the remote runtime even inside rollback. Consequently the actual driver exception was not re-emitted; the original driver text remains unavailable.

Because the stage literal is unconditional whenever `_select_dual()` reaches its final telemetry call, the same accepted code will encounter the same length violation regardless of the particular MAG7 payload, provided execution reaches that point.

```text
ZERO_PAID_REPRODUCTION_ATTEMPTED=YES
ZERO_PAID_REPRODUCTION_RESULT=REPRODUCED
DEFECT_IS_DETERMINISTIC_WITH_SAME_INPUT=YES
SECOND_PAID_SCAN_WOULD_LIKELY_REFAIL=YES
```

## Test evidence and coverage gap

The existing Stage 4B test file was executed without external calls:

```text
python -m pytest tests/test_stage4b_phase2a_vnext.py -q -p no:cacheprovider
RESULT=15 passed
NIGHTWATCH_REQUESTS=0
```

The selection tests replace `_stage` with a no-op lambda, so they verify selection semantics while bypassing `ScanStage` construction and the declared field length. The passing test result is therefore consistent with the production defect and identifies the missing regression boundary.

## Defect classification and remediation design

```text
DEFECT_CLASS=OTHER:S4_SCAN_STAGE_IDENTIFIER_LENGTH_DEFECT
REMEDIATION_REQUIRED=YES
```

The narrowest supported remediation is design-only in this task:

1. In `backend/app/scanner/v13.py`, replace the 35-character S4 stage identifier with a stable identifier no longer than the existing 32-character contract.
2. In `backend/tests/test_stage4b_phase2a_vnext.py`, add a regression assertion that the actual emitted stage identifier fits `ScanStage.stage.type.length`, without stubbing away the value being asserted.

This avoids a schema widening solely for one telemetry literal. No other repository reference depends on the offending identifier, and no historical row with that identifier exists because every attempted insert fails.

```text
EXPECTED_FILES_TO_CHANGE=backend/app/scanner/v13.py; backend/tests/test_stage4b_phase2a_vnext.py
MIGRATION_REQUIRED=NO
HISTORICAL_DATA_REPAIR_REQUIRED=NO
```

No remediation was implemented.

## Repository and external-contact ledger

Final inspection found no application, test, migration, workflow, scheduler, or configuration diff. Only authorized diagnostic evidence files were created.

The only external endpoint contacted during this diagnostic was the configured runtime PostgreSQL endpoint for explicit read-only SELECT/catalog queries:

```text
postgresql://aws-0-ap-northeast-1.pooler.supabase.com:5432/postgres
```

Username/password were omitted. No HTTP(S), Nightwatch, GitHub, workflow, package-registry, or other external endpoint was contacted.

```text
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
```

## Final disposition

```text
FAILED_SCAN_DIAGNOSTIC_RESULT=ROOT_CAUSE_CONFIRMED
DATAERROR_ROOT_CAUSE_IDENTIFIED=YES
FAILED_RUN_STATE_TRUTHFUL=YES
PARTIAL_PRODUCT_CANDIDATE_STATE_FOUND=NO

SECOND_MAG7_SCAN_AUTHORIZED=NO
STAGE8_OBSERVATION_RESUME_READY=NO
STAGE9_READY=NO
NEXT_AUTHORIZED_STAGE=NONE
```

STOP. No second scan, Nightwatch call, database write, remediation, broader Stage 8 observation, or Stage 9 work was performed.

# Nightwatch Scanner vNext — Stage 8 Baseline-Only Creation Retry Report

Date: 2026-08-24  
Authorization: `FOUNDER_AUTHORIZATION=BASELINE_ONLY_CREATION_RETRY_20260824`  
Target ScanRun: `2c71e5bb-9334-4806-a195-0f8768d2d0f2`

## Executive result

```text
BASELINE_ONLY_CREATION_RETRY_RESULT=PASS
```

The one Founder-authorized baseline creation retry passed. A single process explicitly loaded the canonical repository runtime environment, resolved and credential-safely fingerprinted the database target, opened a read-only identity-gate connection, repeated the seven-candidate zero-write first-knowledge preview, and then used the same SQLAlchemy engine for one atomic creation transaction.

The transaction committed exactly seven `FIRST_KNOWLEDGE_BASELINE` contexts and 82 associated anomaly details. Post-write read-only verification found one baseline per target candidate, no duplicate, no lookahead, no source-time violation, no trigger-set drift, exact first-knowledge cutoffs, valid persisted CONTRACT/EXPIRY SQL-NULL semantics, and no orphan details. No scan, Nightwatch request, paid refresh, live Dealer/GEX request, migration, code change, or second retry occurred.

## Execution package and evidence

The attached retry package was saved byte-for-byte at:

```text
F:\options-anomaly-scanner\docs\evidence\NIGHTWATCH_VNEXT_STAGE8_BASELINE_ONLY_CREATION_RETRY_EXECUTION_PACKAGE_20260824.md
```

```text
RETRY_PACKAGE_SHA256=06226EEE604150759F0FF8349577CADDB5D2A5379F734924E146CE05DC76A504
RETRY_PACKAGE_BACKUP_BYTE_IDENTICAL=YES
```

The canonical manifest and every governing/report file referenced by the retry package were present and read from their explicit paths under `F:\options-anomaly-scanner\docs\evidence`. The prior failed creation report was preserved unchanged.

## Repository and code-state gate

```text
WORKTREE=F:\options-anomaly-scanner-stage8
BRANCH=vnext/stage8-mag7-observation
HEAD=3a63eaa1b9069d34199704fe31ac6466e8929d7d

ACCEPTED_S4_IDENTIFIER_REMEDIATION_PRESENT=YES
ACCEPTED_POST_CANDIDATE_PARTIAL_REMEDIATION_PRESENT=YES
ACCEPTED_BASELINE_JSONB_SQL_NULL_REMEDIATION_PRESENT=YES
UNEXPECTED_APPLICATION_DIFF_FOUND=NO
GIT_DIFF_CHECK=PASS
```

The only tracked worktree differences remained the four accepted Stage 8 remediation paths:

```text
backend/app/db/models.py
backend/app/scanner/v13.py
backend/tests/test_stage4b_phase2a_vnext.py
backend/tests/test_stage6_balanced_context.py
```

Verified accepted facts:

```text
ACTIVE_S4_IDENTIFIER=S4_VNEXT_DEEP_BUDGET_SELECTION
ACTIVE_S4_IDENTIFIER_LENGTH=30
POST_CANDIDATE_DEEP_DIVE_PARTIAL_GUARD=PRESENT
contract_snapshot=JSONB(none_as_null=True)
expiry_activity_recap=JSONB(none_as_null=True)

backend/app/scanner/v13.py_SHA256=E7B7E0A58EE3B30FC3AD3EA69A3E7251C2843381E39995EA27C0D0E33F035DC5
backend/tests/test_stage4b_phase2a_vnext.py_SHA256=A0CD77DDACF8A7E8C0896C01715A209CE2AD90FF7996289E8AE407CD4E03186E
```

No application, test, migration, workflow, or scheduler file was changed during this retry.

## Canonical runtime configuration and target identity gate

The process explicitly loaded the existing canonical repository environment configuration before importing Stage 8 settings. It did not read `F:\options-anomaly-scanner-stage8\.env`, did not fall back to localhost, and did not print or persist the password or full database URL.

The exact resolved configuration object used to create the SQLAlchemy engine was checked before connection. That one engine was then reused for the read-only identity gate, zero-write preview, authorized transaction, and post-write read-only verification.

```text
RUNTIME_CONFIG_SOURCE=CANONICAL_REPOSITORY_ENVIRONMENT:F:\options-anomaly-scanner\.env
RESOLVED_DB_TARGET_HOST=aws-0-ap-northeast-1.pooler.supabase.com
RESOLVED_DB_TARGET_PORT=5432
RESOLVED_DB_TARGET_DATABASE=postgres
RESOLVED_DB_TARGET_IS_LOCALHOST=NO
SANITIZED_CONFIG_FINGERPRINT=897FBCE3C66EFE0FB641D3D38BAB6671E7C991FA5EAD07F731EC1068FBC691B4
DB_TARGET_IDENTITY_GATE=PASS
WRITE_SESSION_CONFIG_MATCHES_VERIFIED_REMOTE_CONFIG=YES
```

The sanitized fingerprint was computed from SQLAlchemy's password-hidden URL rendering and discloses no credential.

## Runtime state before retry

The identity/runtime-state transaction was explicitly read-only.

```text
REMOTE_ALEMBIC_HEAD=20260818_0017
TARGET_SCAN_RUN_STATUS=COMPLETE
TARGET_PRODUCT_CANDIDATE_COUNT_BEFORE=7
TARGET_PRODUCT_CANDIDATE_TRIGGER_COUNT_BEFORE=82
TARGET_FIRST_KNOWLEDGE_BASELINE_COUNT_BEFORE=0
TARGET_ANOMALY_CONTEXT_DETAIL_COUNT_BEFORE=0
```

| Ticker | Candidate ID | Immutable triggers | candidate_first_knowledge_at |
|---|---|---:|---|
| AAPL | `e515baba-d875-40a9-8278-4db2b1eb0ba2` | 13 | `2026-08-20T10:07:16.687134Z` |
| AMZN | `10ef5e5a-2d37-42cc-b547-5ca09c6cefa1` | 10 | `2026-08-20T10:07:16.687134Z` |
| GOOGL | `8194f5ab-8726-4cde-b88a-447865e449ee` | 9 | `2026-08-20T10:07:16.687134Z` |
| META | `d8a94e79-4d74-4e17-8538-0c1ad25f2171` | 4 | `2026-08-20T10:07:16.687134Z` |
| MSFT | `65977b65-f4f1-4290-bd1b-3ac6e7a27325` | 5 | `2026-08-20T10:07:16.687134Z` |
| NVDA | `c35ed996-bc4d-43b8-906d-8ae35e0998d6` | 27 | `2026-08-20T10:07:16.687134Z` |
| TSLA | `36d7ad31-2038-4f0e-bc61-e18fb1e4bfa1` | 14 | `2026-08-20T10:07:16.687134Z` |

All candidates retained materialization version `phase2a_vnext_stage4b.product-candidate-materialization.v1` and hash `482a09a33630f81288eabca9a46dc1d75b9374310f87d267c3dc9d3dcab73ebd`.

## Mandatory zero-write preview

The accepted `Stage6BalancedContextService` was run through a no-write session proxy backed by a PostgreSQL transaction set to read-only. Service `add()`/`flush()` calls were intercepted; the real session executed zero writes. Archived raw payload, chain, trigger, Dealer/GEX, and corrected OHLC time boundaries were evaluated against each candidate's immutable first-knowledge cutoff. PostgreSQL JSONB bind processors verified SQL `NULL` for each inactive mutually exclusive payload.

| Ticker | Preview details | Trigger set match | Cutoff |
|---|---:|---|---|
| AAPL | 13 | YES | `2026-08-20T10:07:16.687134Z` |
| AMZN | 10 | YES | `2026-08-20T10:07:16.687134Z` |
| GOOGL | 9 | YES | `2026-08-20T10:07:16.687134Z` |
| META | 4 | YES | `2026-08-20T10:07:16.687134Z` |
| MSFT | 5 | YES | `2026-08-20T10:07:16.687134Z` |
| NVDA | 27 | YES | `2026-08-20T10:07:16.687134Z` |
| TSLA | 14 | YES | `2026-08-20T10:07:16.687134Z` |

```text
PREVIEW_CANDIDATE_COUNT=7
PREVIEW_DETAIL_COUNT=82
PREVIEW_LOOKAHEAD_FOUND=NO
PREVIEW_SOURCE_TIME_VIOLATION_FOUND=NO
PREVIEW_TRIGGER_SET_DRIFT_FOUND=NO
TRIGGER_SET_DRIFT_BEFORE_WRITE=NO
PREVIEW_CONTRACT_PAYLOAD_MATCH_VALID=YES
PREVIEW_EXPIRY_PAYLOAD_MATCH_VALID=YES
PREVIEW_DATABASE_WRITES=0
```

## Authorized retry transaction

Only after the code, configuration, target identity, runtime-state, and preview gates passed was the authorized retry consumed.

```text
BASELINE_CREATION_RETRY_ATTEMPTS_AUTHORIZED=1
ACTUAL_BASELINE_CREATION_RETRY_ATTEMPTS=1
BASELINE_CREATION_TRANSACTION_MODEL=ONE_TRANSACTION_ONE_COMMIT
CREATION_COMMIT_OCCURRED=YES
SECOND_RETRY_ATTEMPTED=NO
```

The write session was created from the exact already-verified engine. Within that transaction, candidate rows were locked and all runtime preconditions were rechecked. One common UTC evaluation time was supplied to the accepted service for all seven candidates. The service selected archived sources using each candidate's own immutable cutoff and flushed seven contexts plus their detail rows. After in-transaction count validation, one commit was issued.

No manual SQL DML created or modified application rows. SQL was used only for precondition and verification reads; all baseline writes were generated by the accepted service and remediated ORM.

## Persisted baselines

| Ticker | Candidate ID | ProductCandidateContext ID | Kind | Evidence cutoff | Evaluated at | Details |
|---|---|---|---|---|---|---:|
| AAPL | `e515baba-d875-40a9-8278-4db2b1eb0ba2` | `5b61b6ad-fc46-4344-a45d-cb330ee03821` | `FIRST_KNOWLEDGE_BASELINE` | `2026-08-20T10:07:16.687134Z` | `2026-08-24T02:07:20.199580Z` | 13 |
| AMZN | `10ef5e5a-2d37-42cc-b547-5ca09c6cefa1` | `2f18148d-d166-4a7d-8129-80f871a2c73c` | `FIRST_KNOWLEDGE_BASELINE` | `2026-08-20T10:07:16.687134Z` | `2026-08-24T02:07:20.199580Z` | 10 |
| GOOGL | `8194f5ab-8726-4cde-b88a-447865e449ee` | `283c78a9-9a9b-42af-a236-777143f2aa61` | `FIRST_KNOWLEDGE_BASELINE` | `2026-08-20T10:07:16.687134Z` | `2026-08-24T02:07:20.199580Z` | 9 |
| META | `d8a94e79-4d74-4e17-8538-0c1ad25f2171` | `f815bd35-ce29-4fc2-b583-1182b0604298` | `FIRST_KNOWLEDGE_BASELINE` | `2026-08-20T10:07:16.687134Z` | `2026-08-24T02:07:20.199580Z` | 4 |
| MSFT | `65977b65-f4f1-4290-bd1b-3ac6e7a27325` | `6bee560d-1201-406f-9da3-be7e857fcdaa` | `FIRST_KNOWLEDGE_BASELINE` | `2026-08-20T10:07:16.687134Z` | `2026-08-24T02:07:20.199580Z` | 5 |
| NVDA | `c35ed996-bc4d-43b8-906d-8ae35e0998d6` | `14502e13-6956-42ee-80af-a85bd1f772b9` | `FIRST_KNOWLEDGE_BASELINE` | `2026-08-20T10:07:16.687134Z` | `2026-08-24T02:07:20.199580Z` | 27 |
| TSLA | `36d7ad31-2038-4f0e-bc61-e18fb1e4bfa1` | `87964e8d-fbf3-4fff-baf4-8256cd846573` | `FIRST_KNOWLEDGE_BASELINE` | `2026-08-20T10:07:16.687134Z` | `2026-08-24T02:07:20.199580Z` | 14 |

## Post-write integrity

The post-write transaction was explicitly read-only and used the same engine. Persisted rows, not transient ORM collections, are authoritative for the counts below.

```text
TARGET_FIRST_KNOWLEDGE_BASELINE_COUNT_AFTER=7
ANOMALY_CONTEXT_DETAIL_COUNT_AFTER=82
EXPECTED_ANOMALY_CONTEXT_DETAIL_COUNT=82

ONE_BASELINE_PER_CANDIDATE=YES
DUPLICATE_BASELINE_FOUND=NO

BASELINE_LOOKAHEAD_FOUND=NO
BASELINE_SOURCE_TIME_VIOLATION_FOUND=NO
BASELINE_TRIGGER_SET_DRIFT_FOUND=NO
BASELINE_FIRST_KNOWLEDGE_CUTOFF_MISMATCH_FOUND=NO

CONTRACT_DETAIL_COUNT=68
EXPIRY_DETAIL_COUNT=14
CONTRACT_DETAIL_PAYLOAD_MATCH_VALID=YES
EXPIRY_DETAIL_PAYLOAD_MATCH_VALID=YES
DETAIL_ORPHAN_FOUND=NO
```

Persisted validation covered:

- physical and provenance cutoff equality to `candidate_first_knowledge_at`;
- `context_evaluated_at >= candidate_first_knowledge_at`;
- source first-received, vendor-observed, local-captured, price, quote, chain raw-payload, archived Dealer/GEX, and corrected OHLC dates at or before cutoff;
- exact equality between the 82 immutable trigger IDs and 82 detail trigger IDs;
- CONTRACT: `contract_snapshot IS NOT SQL NULL` and `expiry_activity_recap IS SQL NULL`;
- EXPIRY: `contract_snapshot IS SQL NULL` and `expiry_activity_recap IS NOT SQL NULL`;
- no detail lacking a parent context.

Before/after whole-row fingerprints matched for the target `scan_runs`, `product_candidates`, and `product_candidate_triggers` rows. Total counts were unchanged for every protected table:

```text
scan_runs=0 delta
product_candidates=0 delta
product_candidate_triggers=0 delta
ticker_scan_results=0 delta
expiry_observations=0 delta
contract_scan_observations=0 delta
strike_clusters=0 delta
raw_vendor_payloads=0 delta
api_usage_audit=0 delta
```

## Write and authorization ledger

```text
PRODUCT_CANDIDATE_CONTEXT_ROWS_ADDED=7
ANOMALY_CONTEXT_DETAIL_ROWS_ADDED=82
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
DEALER_GEX_SOURCE=ARCHIVE_ONLY

REMOTE_DB_SCHEMA_WRITES=0
REMOTE_APPLICATION_DATA_WRITES=AUTHORIZED_BASELINE_ONLY_CREATION_RETRY_ONLY

APPLICATION_CODE_CHANGES_DURING_RETRY=0
TEST_CODE_CHANGES_DURING_RETRY=0
MIGRATION_FILES_CHANGED_DURING_RETRY=0
WORKFLOW_CHANGES=0
SCHEDULER_CHANGES=0
COMMITS_CREATED=0
PUSHES=0
PRS_CREATED=0
MERGES=0
```

## External contact ledger

No HTTP/API URL was contacted. No Nightwatch/vendor endpoint, npm registry, GitHub endpoint, workflow, or other service was contacted.

```text
postgresql://aws-0-ap-northeast-1.pooler.supabase.com:5432/postgres
  - read-only DB target identity/runtime-state gate
  - read-only seven-candidate preview
  - one authorized atomic baseline-only creation transaction
  - read-only post-write integrity verification
```

No localhost connection was attempted in this retry. Credentials and the full database URL were never printed or stored in evidence.

## Required final fields

```text
BASELINE_ONLY_CREATION_RETRY_RESULT=PASS

FOUNDER_AUTHORIZATION=BASELINE_ONLY_CREATION_RETRY_20260824
BASELINE_CREATION_RETRY_ATTEMPTS_AUTHORIZED=1
ACTUAL_BASELINE_CREATION_RETRY_ATTEMPTS=1

TARGET_SCAN_RUN_ID=2c71e5bb-9334-4806-a195-0f8768d2d0f2
TARGET_SCAN_RUN_STATUS=COMPLETE

ACCEPTED_S4_IDENTIFIER_REMEDIATION_PRESENT=YES
ACCEPTED_POST_CANDIDATE_PARTIAL_REMEDIATION_PRESENT=YES
ACCEPTED_BASELINE_JSONB_SQL_NULL_REMEDIATION_PRESENT=YES
UNEXPECTED_APPLICATION_DIFF_FOUND=NO

RUNTIME_CONFIG_SOURCE=CANONICAL_REPOSITORY_ENVIRONMENT:F:\options-anomaly-scanner\.env
RESOLVED_DB_TARGET_HOST=aws-0-ap-northeast-1.pooler.supabase.com
RESOLVED_DB_TARGET_PORT=5432
RESOLVED_DB_TARGET_DATABASE=postgres
RESOLVED_DB_TARGET_IS_LOCALHOST=NO
DB_TARGET_IDENTITY_GATE=PASS
WRITE_SESSION_CONFIG_MATCHES_VERIFIED_REMOTE_CONFIG=YES

REMOTE_ALEMBIC_HEAD=20260818_0017

TARGET_PRODUCT_CANDIDATE_COUNT_BEFORE=7
TARGET_PRODUCT_CANDIDATE_TRIGGER_COUNT_BEFORE=82
TARGET_FIRST_KNOWLEDGE_BASELINE_COUNT_BEFORE=0
TARGET_ANOMALY_CONTEXT_DETAIL_COUNT_BEFORE=0

PREVIEW_CANDIDATE_COUNT=7
PREVIEW_DETAIL_COUNT=82
PREVIEW_LOOKAHEAD_FOUND=NO
PREVIEW_SOURCE_TIME_VIOLATION_FOUND=NO
PREVIEW_TRIGGER_SET_DRIFT_FOUND=NO
TRIGGER_SET_DRIFT_BEFORE_WRITE=NO
PREVIEW_CONTRACT_PAYLOAD_MATCH_VALID=YES
PREVIEW_EXPIRY_PAYLOAD_MATCH_VALID=YES

BASELINE_CREATION_TRANSACTION_MODEL=ONE_TRANSACTION_ONE_COMMIT

TARGET_FIRST_KNOWLEDGE_BASELINE_COUNT_AFTER=7
ANOMALY_CONTEXT_DETAIL_COUNT_AFTER=82
EXPECTED_ANOMALY_CONTEXT_DETAIL_COUNT=82

ONE_BASELINE_PER_CANDIDATE=YES
DUPLICATE_BASELINE_FOUND=NO

BASELINE_LOOKAHEAD_FOUND=NO
BASELINE_SOURCE_TIME_VIOLATION_FOUND=NO
BASELINE_TRIGGER_SET_DRIFT_FOUND=NO
BASELINE_FIRST_KNOWLEDGE_CUTOFF_MISMATCH_FOUND=NO

CONTRACT_DETAIL_PAYLOAD_MATCH_VALID=YES
EXPIRY_DETAIL_PAYLOAD_MATCH_VALID=YES
DETAIL_ORPHAN_FOUND=NO

PRODUCT_CANDIDATE_CONTEXT_ROWS_ADDED=7
ANOMALY_CONTEXT_DETAIL_ROWS_ADDED=82
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
REMOTE_APPLICATION_DATA_WRITES=AUTHORIZED_BASELINE_ONLY_CREATION_RETRY_ONLY

APPLICATION_CODE_CHANGES_DURING_RETRY=0
TEST_CODE_CHANGES_DURING_RETRY=0
MIGRATION_FILES_CHANGED_DURING_RETRY=0
WORKFLOW_CHANGES=0
SCHEDULER_CHANGES=0

COMMITS_CREATED=0
PUSHES=0
PRS_CREATED=0
MERGES=0

PRIMARY_REPORT_PATH=F:\options-anomaly-scanner-stage8\docs\evidence\stage8\NIGHTWATCH_VNEXT_STAGE8_BASELINE_ONLY_CREATION_RETRY_REPORT_20260824.md
CANONICAL_REPORT_PATH=F:\options-anomaly-scanner\docs\evidence\NIGHTWATCH_VNEXT_STAGE8_BASELINE_ONLY_CREATION_RETRY_REPORT_20260824.md
PRIMARY_REPORT_SHA256=CALCULATED_AFTER_REPORT_FINALIZATION
CANONICAL_REPORT_SHA256=CALCULATED_AFTER_REPORT_FINALIZATION
REPORT_BACKUP_BYTE_IDENTICAL=VERIFIED_AFTER_REPORT_FINALIZATION

FOURTH_MAG7_SCAN_AUTHORIZED=NO
SECOND_BASELINE_RETRY_AUTHORIZED=NO
STAGE8_OBSERVATION_RESUME_READY=YES
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

Broader Stage 8 analysis was not started. No fourth MAG7 scan or Stage 9 work was started.

# Nightwatch vNext — Controlled Live MAG7 Observation Report

Date: 2026-08-20  
Worktree: `F:\options-anomaly-scanner-stage8`  
Branch: `vnext/stage8-mag7-observation`  
HEAD/base: `3a63eaa1b9069d34199704fe31ac6466e8929d7d`  
Execution package SHA-256: `5B792CB3B4A4C38729C9C6647A739DDE827122EA7B40CD76B1F7C6C8E03F0928`

## Executive result

```text
CONTROLLED_OBSERVATION_RESULT=FAIL_SCAN
FOUNDER_AUTHORIZATION=ONE_CONTROLLED_MAG7_OBSERVATION_20260820

AUTHORIZED_SCAN_INVOCATIONS=1
ACTUAL_SCAN_INVOCATIONS=1

SCAN_RUN_ID=090359ad-9d76-49b9-8902-f28ac54a1d1b
SCAN_STATUS=FAILED
SCAN_STARTED_AT=2026-08-20T05:20:39.464759+00:00
SCAN_COMPLETED_AT=2026-08-20T05:23:08.634917+00:00

MAG7_COST_BOUND_PROVEN=YES
MAX_CONFIGURED_PAID_UNITS_FOR_ONE_SCAN=14

PAID_UNITS_BEFORE=199
PAID_UNITS_AFTER=213
OBSERVED_PAID_UNIT_DELTA=14
QUOTA_REMAINING_BEFORE=99712
QUOTA_REMAINING_AFTER=99698

NEW_PRODUCT_CANDIDATE_COUNT=0
NEW_PRODUCT_CANDIDATE_TRIGGER_COUNT=0

BASELINE_COUNT=0
BASELINE_LOOKAHEAD_FOUND=NO
BASELINE_TRIGGER_SET_DRIFT_FOUND=NO
BASELINE_SOURCE_TIME_VIOLATION_FOUND=NO

VALID_CANDIDATE_OMISSION_FOUND=NO
DEEP_DIVE_BUDGET_SUPPRESSION_FOUND=NO

PHASE2B_REFRESH_CALLS=0
DEALER_GEX_LIVE_CALLS=0
DEALER_GEX_SOURCE=ARCHIVE_ONLY

REMOTE_ALEMBIC_HEAD=20260818_0017
REMOTE_MIGRATIONS_RUN=0

STAGE8_OBSERVATION_RESUME_READY=NO
STAGE9_READY=NO
NEXT_AUTHORIZED_STAGE=NONE
```

The one authorized production scan was invoked exactly once and was not retried. All 14 bounded MAG7 source calls returned HTTP 200 and consumed 14 units, but the scanner later failed safely with SQLAlchemy `DataError`. The persisted `ScanRun.summary` contains only the sanitized failure identity `{"safe_error":"DataError"}`. The failure occurred after current activity and route selection evidence had been committed, but before the S5 structure stage completed. No second scan, repair, context refresh, live Dealer/GEX call, or baseline creation was attempted.

The three baseline-integrity fields above are `NO` only in the literal sense that no violating baseline was found: the failed scan produced no ProductCandidate and therefore no baseline sample existed to verify. They do not represent a passed real-sample baseline integrity assessment.

## Authorization and stop handling

```text
MAG7_SCAN_INVOCATIONS_AUTHORIZED=1
UNIVERSE=MAG7_ONLY
EXPECTED_PAID_COST_APPROX=14
HARD_PAID_UNIT_CAP=20
PHASE2B_PAID_REFRESH_AUTHORIZED=NO
DEALER_GEX_LIVE_CALL_AUTHORIZED=NO
SECOND_MAG7_SCAN_AUTHORIZED=NO
```

The authorized invocation was exhausted by the failed run. The execution package says that a failed scan must not be retried. Candidate materialization is defined only for `COMPLETE` scans, so the failed run did not establish a valid ProductCandidate occurrence and the zero-paid baseline step was not entered.

## Canonical evidence and package check

The attached execution package was copied byte-for-byte to:

```text
F:\options-anomaly-scanner\docs\evidence\NIGHTWATCH_VNEXT_CONTROLLED_LIVE_MAG7_OBSERVATION_EXECUTION_PACKAGE_20260820.md
```

Source and canonical copies both hash to:

```text
5B792CB3B4A4C38729C9C6647A739DDE827122EA7B40CD76B1F7C6C8E03F0928
```

Every governing file referenced by the package was present in the canonical evidence root and read completely. Hashes matched the canonical manifest or the accepted package/report evidence available for this gate. No package conflict was found.

## Runtime and repository preflight

```text
REMOTE_DB_REACHABLE=YES
REMOTE_ALEMBIC_HEAD=20260818_0017
PRODUCT_CANDIDATE_TABLE_PRESENT=YES
PRODUCT_CANDIDATE_TRIGGER_TABLE_PRESENT=YES
PRODUCT_CANDIDATE_CONTEXT_TABLE_PRESENT=YES
ANOMALY_CONTEXT_DETAIL_TABLE_PRESENT=YES
RUNNING_SCAN_COUNT_BEFORE=0
NY_MARKET_DATE=2026-08-20
XNYS_SESSION=YES

WORKTREE_HEAD_MATCHES_PACKAGE=YES
WORKTREE_BRANCH_MATCHES_PACKAGE=YES
APPLICATION_OR_MIGRATION_DIFF_BEFORE=NONE
```

The only pre-existing worktree status was the authorized untracked `docs/evidence/stage8/` report directory. There was no application, test, migration, workflow, or scheduler diff.

Sanitized configured runtime endpoint contacted for read-only preflight/readback and the authorized observation writes:

```text
postgresql://aws-0-ap-northeast-1.pooler.supabase.com:5432/postgres
```

No credential, key, password, or authorization header is included in this report.

## Cost-bound proof

The unmodified production entry point was:

```text
python -m app.cli run-mag7-scan
```

Its effective client settings and fan-out are:

```text
UNIVERSE=AAPL,MSFT,NVDA,AMZN,META,GOOGL,TSLA
TICKER_COUNT=7
PAID_ACTIVITY_ENDPOINTS_PER_TICKER=2
SCAN_CLI_MAX_RETRIES=0
SCAN_CLI_MAX_CONCURRENCY=4
INTERACTIVE_STRUCTURE_SOURCE=EXISTING_DAILY_ARCHIVE
INTERACTIVE_RADAR_SOURCE=EXISTING_PERSISTED_RADAR
PHASE2B_REFRESH_IN_SCAN_PATH=NO
LIVE_DEALER_GEX_IN_SCAN_PATH=NO
```

Formula:

```text
maximum paid units = 7 tickers ×
                     (1 expiry-breakdown + 1 options-volume) ×
                     (1 initial attempt + 0 retries)
                   = 14

14 <= HARD_PAID_UNIT_CAP 20
```

Cache reuse could only reduce the paid count. The active vNext `_structure_scan` derives contract structure from accepted persisted daily archive rows and `_radar` reads persisted Radar rows; neither adds a Nightwatch request.

## Authoritative before-state

The last locally persisted quota fact before the scan was recorded at `2026-08-19T19:47:56.460926+00:00`:

```text
PAID_UNITS_BEFORE=199
QUOTA_LIMIT_BEFORE=100000
QUOTA_REMAINING_BEFORE=99712
```

`PAID_UNITS_BEFORE` is the count of authoritative `api_usage_audit.consumed_quota IS TRUE` rows. The quota fields are the latest persisted vendor response-header facts available before the controlled scan; no separate quota/discovery request was made.

Database row counts immediately before invocation:

| Table | Before |
|---|---:|
| `scan_runs` | 6 |
| `api_usage_audit` | 247 |
| `raw_vendor_payloads` | 235 |
| `product_candidates` | 0 |
| `product_candidate_triggers` | 0 |
| `product_candidate_contexts` | 0 |
| `anomaly_context_details` | 0 |

## Controlled scan result

```text
AUTHORIZED_SCAN_INVOCATIONS=1
ACTUAL_SCAN_INVOCATIONS=1
SCAN_RUN_ID=090359ad-9d76-49b9-8902-f28ac54a1d1b
SCAN_TRIGGER=cli
SCAN_MARKET_DATE=2026-08-20
SCAN_SPECIFICATION_VERSION=phase2a_vnext_stage4b
SCAN_STARTED_AT=2026-08-20T05:20:39.464759+00:00
SCAN_COMPLETED_AT=2026-08-20T05:23:08.634917+00:00
SCAN_STATUS=FAILED
SCAN_SAFE_ERROR=DataError
SCAN_CONSUMED_QUOTA_UNITS=14
SCAN_NETWORK_ATTEMPTS=14
SCAN_CACHE_HITS=0
SCAN_FRESH_REQUESTS=14
SCAN_RETRIES=0
```

Completed persisted stages:

| Stage | Status | Evidence |
|---|---|---|
| `S0_PREFLIGHT_V11` | COMPLETE | Four required capabilities verified |
| `S2_ACTIVITY_SURFACE_V12` | COMPLETE | 7 tickers, 104 expiries |
| `S3_DISCOVERY_CONFIRMATION` | COMPLETE | 20-session 0DTE configuration identity recorded |
| `S3_VNEXT_ACTIVE_DISCOVERY` | COMPLETE | Active families were Radar, Expiry Activity, Contract Persistence |

There is no completed S5 structure stage. The persisted state shows route selection had been written before the exception: 17 expiry rows were `deep_dive_eligible`, spanning 14 expiry-activity flags and 4 Radar flags; 10 expiry rows were selected across the four allowed deep-dive tickers. No contract observation was committed for this run. This locates the failure after activity/selection and before successful structure completion, but does not establish a deeper root cause than the persisted `DataError`. No diagnostic rerun or remediation was authorized.

## External endpoint ledger

Nightwatch base URL:

```text
https://api.yehangshe.com
```

Exactly the following 14 API endpoints were contacted, once each, with HTTP 200, `attempt_count=1`, `retry_count=0`, and `consumed_quota=true`:

| Ticker | Endpoint 1 | Endpoint 2 |
|---|---|---|
| AAPL | `https://api.yehangshe.com/v1/options/expiry-breakdown/AAPL` | `https://api.yehangshe.com/v1/options/options-volume/AAPL` |
| MSFT | `https://api.yehangshe.com/v1/options/expiry-breakdown/MSFT` | `https://api.yehangshe.com/v1/options/options-volume/MSFT` |
| NVDA | `https://api.yehangshe.com/v1/options/expiry-breakdown/NVDA` | `https://api.yehangshe.com/v1/options/options-volume/NVDA` |
| AMZN | `https://api.yehangshe.com/v1/options/expiry-breakdown/AMZN` | `https://api.yehangshe.com/v1/options/options-volume/AMZN` |
| META | `https://api.yehangshe.com/v1/options/expiry-breakdown/META` | `https://api.yehangshe.com/v1/options/options-volume/META` |
| GOOGL | `https://api.yehangshe.com/v1/options/expiry-breakdown/GOOGL` | `https://api.yehangshe.com/v1/options/options-volume/GOOGL` |
| TSLA | `https://api.yehangshe.com/v1/options/expiry-breakdown/TSLA` | `https://api.yehangshe.com/v1/options/options-volume/TSLA` |

No other external HTTP/API URL was contacted. In particular:

```text
PHASE2B_REFRESH_CALLS=0
DAILY_OHLC_REFRESH_CALLS=0
STOCK_STATE_REFRESH_CALLS=0
IV_RANK_REFRESH_CALLS=0
TERM_STRUCTURE_REFRESH_CALLS=0
DEALER_GEX_LIVE_CALLS=0
```

## Post-run cost and quota

```text
PAID_UNITS_AFTER=213
QUOTA_LIMIT_AFTER=100000
QUOTA_REMAINING_AFTER=99698

OBSERVED_PAID_UNIT_DELTA=213-199=14
OBSERVED_QUOTA_REMAINING_DELTA=99712-99698=14
HARD_PAID_UNIT_CAP=20
COST_CAP_EXCEEDED=NO
```

The local usage-audit delta, the `ScanRun.consumed_quota_units`, the number of successful paid response rows, and the vendor quota-remaining delta all independently agree at 14.

## Candidate and budget verification

```text
NEW_PRODUCT_CANDIDATE_COUNT=0
NEW_PRODUCT_CANDIDATE_TRIGGER_COUNT=0
VALID_CANDIDATE_OMISSION_FOUND=NO
DEEP_DIVE_BUDGET_SUPPRESSION_FOUND=NO
```

The zero candidate count is not a `SUCCESS_NO_CANDIDATE` observation. It is the required consequence of `materialize_successful_scan_candidates` accepting only a `COMPLETE` ScanRun. Therefore no genuine eligible ProductCandidate occurrence was established for this failed run, and candidate omission cannot be assessed as a successful-sample integrity result. The persisted deep-dive selection did not change candidate identity, but the scan did not reach successful candidate materialization.

## Baseline handling and integrity

```text
BASELINE_CREATION_ATTEMPTED=NO
BASELINE_COUNT=0
FIRST_KNOWLEDGE_BASELINE_COUNT=0
REFRESH_CONTEXT_COUNT=0

BASELINE_LOOKAHEAD_FOUND=NO
BASELINE_TRIGGER_SET_DRIFT_FOUND=NO
BASELINE_SOURCE_TIME_VIOLATION_FOUND=NO

PHASE2B_REFRESH_CALLS=0
DEALER_GEX_LIVE_CALLS=0
DEALER_GEX_SOURCE=ARCHIVE_ONLY
```

Because the scan failed and produced no ProductCandidate, baseline creation was inapplicable and was not invoked. There was therefore no baseline source timestamp, OHLC bar, chain timestamp, quote timestamp, or Dealer/GEX archive timestamp to test for this run. No refresh was substituted for missing baseline evidence.

## Exact runtime delta attributable to the controlled observation

Required delta fields:

```text
SCAN_RUN_ROWS_ADDED_BY_CONTROLLED_OBSERVATION=1
PRODUCT_CANDIDATE_ROWS_ADDED_BY_CONTROLLED_OBSERVATION=0
TRIGGER_ROWS_ADDED_BY_CONTROLLED_OBSERVATION=0
BASELINE_CONTEXT_ROWS_ADDED_BY_CONTROLLED_OBSERVATION=0
ANOMALY_DETAIL_ROWS_ADDED_BY_CONTROLLED_OBSERVATION=0
```

Additional scan-linked evidence rows:

| Table | Rows attributable to ScanRun |
|---|---:|
| `api_usage_audit` | 14 |
| `raw_vendor_payloads` | 14 |
| `ticker_scan_results` | 7 |
| `expiry_observations` | 104 |
| `scan_stages` | 4 |
| `contract_scan_observations` | 0 |
| `strike_clusters` | 0 |
| `bucket_positioning_summaries` | 0 |
| `zero_dte_activity_session_snapshots` | 0 |

Post-run totals for the principal tables were `scan_runs=7`, `api_usage_audit=261`, `raw_vendor_payloads=249`, and all four Stage 5/6 candidate/context tables remained at zero.

All application-data changes above are the normal writes made by the one authorized, unmodified production scan. There was no manual SQL DML, historical repair, schema write, or separately initiated process.

## Verification notes

The targeted mock/fixture suite covering Phase 2A orchestration, vNext routes, Stage 5 candidate persistence, and Stage 6 baseline behavior displayed all 64 tests at 100%. The test runner did not terminate before the 120-second command timeout, so the command-level outcome is conservatively recorded as `TIMEOUT_AFTER_TEST_PROGRESS_100_PERCENT` rather than a clean zero-exit pass. No test contacted Nightwatch.

Final repository verification found no application, test, migration, workflow, or scheduler change. The only new files are authorized evidence reports.

## Carried ledger

```text
CURRENT_TRIGGER_FRESHNESS_MODE=CALIBRATION_REQUIRED
RADAR_OI_SCHEDULE_ACTIVATION=PENDING_ROLLOVER_EVIDENCE
CROSS_RUN_CANDIDATE_LIFECYCLE=DEFERRED_NO_AUTO_MERGE
IV_RANK_CORE_ELIGIBILITY=WITHHOLD_PENDING_PROVENANCE
ISOLATED_POSTGRES_RUNTIME_VERIFIED=NO
N1_HISTORICAL_RUNTIME_DISTRIBUTION_VERIFIED=NO
```

## Authorization ledger

```text
APPLICATION_CODE_CHANGES=0
TEST_CODE_CHANGES=0
MIGRATION_FILES_CHANGED=0
WORKFLOW_CHANGES=0
SCHEDULER_CHANGES=0

MAG7_SCAN_INVOCATIONS=1
NIGHTWATCH_REQUESTS=14
PAID_UNITS=14

PHASE2B_REFRESH_CALLS=0
DEALER_GEX_LIVE_CALLS=0

REMOTE_MIGRATIONS_RUN=0
REMOTE_DB_SCHEMA_WRITES=0
REMOTE_APPLICATION_DATA_WRITES=AUTHORIZED_CONTROLLED_OBSERVATION_ONLY

COMMITS_CREATED=0
PUSHES=0
PRS_CREATED=0
MERGES=0
```

## Final disposition

```text
CONTROLLED_OBSERVATION_RESULT=FAIL_SCAN
STAGE8_OBSERVATION_RESUME_READY=NO
STAGE9_READY=NO
NEXT_AUTHORIZED_STAGE=NONE
```

STOP. No second MAG7 scan, baseline repair, broader Stage 8 observation, or Stage 9 work was started.

# Nightwatch vNext — Second Controlled Live MAG7 Observation Report

Date: 2026-08-20
Worktree: F:/options-anomaly-scanner-stage8
Branch: vnext/stage8-mag7-observation
Base HEAD: 3a63eaa1b9069d34199704fe31ac6466e8929d7d
Execution package SHA-256: B2F22D35AB20A9AEB92C43E33CD7B1C5F0B596641C71D6EDF0B3AD3B82AFA96F

## Executive result

SECOND_CONTROLLED_OBSERVATION_RESULT=FAIL_SCAN_NEW_DEFECT
FOUNDER_AUTHORIZATION=SECOND_CONTROLLED_MAG7_OBSERVATION_20260820

SECOND_SCAN_INVOCATIONS_AUTHORIZED=1
ACTUAL_SECOND_SCAN_INVOCATIONS=1

SECOND_SCAN_RUN_ID=e9267160-503a-41c7-9bb1-8cc2b2e3d8c6
SECOND_SCAN_STATUS=PARTIAL
SECOND_SCAN_STARTED_AT=2026-08-20T06:44:35.012305+00:00
SECOND_SCAN_COMPLETED_AT=2026-08-20T06:47:47.818143+00:00
SECOND_SCAN_SAFE_ERROR=NONE
LAST_PERSISTED_STAGE=S6_POSITIONING_SUMMARY_V12

The one authorized production invocation completed with process exit code 0 and persisted terminal scanner status PARTIAL. It was not retried. PARTIAL is not one of the package's permitted success labels SUCCESS_WITH_CANDIDATES or SUCCESS_NO_CANDIDATE, and the run has no candidate materialization marker or ProductCandidate rows. It is therefore conservatively classified as FAIL_SCAN_NEW_DEFECT. Per the package, this task does not diagnose or remediate that new terminal-state outcome.

The accepted S4 remediation worked at runtime. The new 30-character S4 row was persisted successfully, all later scanner stages through S6 completed, and the prior length DataError did not recur.

## Package preservation and governing evidence

The attached execution package was copied byte-for-byte to:

F:/options-anomaly-scanner/docs/evidence/NIGHTWATCH_VNEXT_SECOND_CONTROLLED_LIVE_MAG7_OBSERVATION_EXECUTION_PACKAGE_20260820.md

Attachment and canonical package:

PACKAGE_SHA256=B2F22D35AB20A9AEB92C43E33CD7B1C5F0B596641C71D6EDF0B3AD3B82AFA96F
PACKAGE_BACKUP_BYTE_IDENTICAL=YES

Every canonical and Stage 8 worktree governing/report file named by the package was present and read completely. The diagnostic and remediation report pairs were hash-identical. No package or report conflict existed before execution.

## Code-state preflight

WORKTREE_BRANCH=vnext/stage8-mag7-observation
WORKTREE_HEAD=3a63eaa1b9069d34199704fe31ac6466e8929d7d
ACCEPTED_S4_REMEDIATION_PRESENT=YES
UNEXPECTED_APPLICATION_DIFF_FOUND=NO
GIT_DIFF_CHECK=PASS

The only tracked worktree changes before and after the observation remained:

- backend/app/scanner/v13.py — accepted stage identifier repair only
- backend/tests/test_stage4b_phase2a_vnext.py — accepted contract regression only

The active production call site contains S4_VNEXT_DEEP_BUDGET_SELECTION and does not contain the old 35-character identifier. The focused executable regression passed immediately before the scan.

APPLICATION_CODE_CHANGES_DURING_SECOND_OBSERVATION=0
TEST_CODE_CHANGES_DURING_SECOND_OBSERVATION=0
MIGRATION_FILES_CHANGED_DURING_SECOND_OBSERVATION=0
WORKFLOW_CHANGES=0
SCHEDULER_CHANGES=0

## Runtime and before-state preflight

REMOTE_ALEMBIC_HEAD=20260818_0017
PRODUCT_CANDIDATE_TABLE_PRESENT=YES
PRODUCT_CANDIDATE_TRIGGER_TABLE_PRESENT=YES
PRODUCT_CANDIDATE_CONTEXT_TABLE_PRESENT=YES
ANOMALY_CONTEXT_DETAIL_TABLE_PRESENT=YES
RUNNING_SCAN_COUNT_BEFORE=0

PRIOR_FAILED_SCAN_RUN_ID=090359ad-9d76-49b9-8902-f28ac54a1d1b
PRIOR_FAILED_RUN_STATUS=FAILED

Before-state counts:

| Table | Rows before |
|---|---:|
| scan_runs | 7 |
| scan_stages | 43 |
| api_usage_audit | 261 |
| raw_vendor_payloads | 249 |
| product_candidates | 0 |
| product_candidate_triggers | 0 |
| product_candidate_contexts | 0 |
| anomaly_context_details | 0 |

The first failed run remained FAILED after the second observation and was not mutated.

## Cost-bound and retry proof

VENDOR_FANOUT_CHANGED_BY_REMEDIATION=NO
RETRY_LOGIC_CHANGED_BY_REMEDIATION=NO
SECOND_SCAN_COST_BOUND_PROVEN=YES
MAX_CONFIGURED_PAID_UNITS_FOR_SECOND_SCAN=14

The production CLI fixes max_retries=0. The scanner uses the accepted seven-ticker MAG7 universe and exactly two paid activity endpoints per ticker:

maximum paid units = 7 tickers × 2 endpoints × 1 attempt = 14

14 is within SECOND_SCAN_HARD_PAID_UNIT_CAP=20. The accepted remediation changed only the S4 telemetry literal and its regression test, with no vendor client, fan-out, retry, budget, or universe diff.

Pre-run authoritative facts:

PAID_UNITS_BEFORE_SECOND_SCAN=213
QUOTA_LIMIT_BEFORE_SECOND_SCAN=100000
QUOTA_REMAINING_BEFORE_SECOND_SCAN=99698
QUOTA_FACT_BEFORE_AT=2026-08-20T05:22:28.791366+00:00

## One authorized production invocation

MAG7_SCAN_INVOCATIONS_THIS_TASK=1
NIGHTWATCH_REQUESTS_THIS_TASK=14
PAID_UNITS_THIS_TASK=14

Persisted run facts:

SCAN_SPECIFICATION_VERSION=phase2a_vnext_stage4b
SCAN_MARKET_DATE=2026-08-20
SCAN_CONSUMED_QUOTA_UNITS=14
SCAN_NETWORK_ATTEMPTS=14
SCAN_CACHE_HITS=0
SCAN_FRESH_REQUESTS=14
SCAN_RETRIES=0
SCAN_HTTP_200_RESPONSES=14

The invocation used the current remediated working-tree code. No fixture, threshold override, universe expansion, manual seed, second invocation, retry, refresh, or live Dealer/GEX request was used.

## Runtime S4 remediation proof

NEW_S4_STAGE_ROW_PRESENT=YES
NEW_S4_STAGE_IDENTIFIER=S4_VNEXT_DEEP_BUDGET_SELECTION
NEW_S4_STAGE_IDENTIFIER_LENGTH=30
S4_LENGTH_DATAERROR_RECURRED=NO

Persisted stage sequence:

| Stage | Status |
|---|---|
| S0_PREFLIGHT_V11 | COMPLETE |
| S2_ACTIVITY_SURFACE_V12 | COMPLETE |
| S3_DISCOVERY_CONFIRMATION | COMPLETE |
| S3_VNEXT_ACTIVE_DISCOVERY | COMPLETE |
| S4_VNEXT_DEEP_BUDGET_SELECTION | COMPLETE |
| S5_STRUCTURE_AND_RADAR | COMPLETE |
| S6_POSITIONING_SUMMARY_V12 | COMPLETE |

S4 telemetry facts:

S4_ELIGIBLE_EXPIRIES=17
S4_SELECTED_EXPIRIES=10
S4_SELECTED_TICKERS=4
S4_OPERATIONAL_TRUNCATION=YES
S4_CANDIDATE_IDENTITY_AFFECTED=NO

No DataError or safe_error was persisted for the new run.

## Candidate and baseline result

CANDIDATE_MATERIALIZED_AT=NULL
CANDIDATE_MATERIALIZATION_RULE_VERSION=NULL
CANDIDATE_MATERIALIZATION_RULE_HASH=NULL

NEW_PRODUCT_CANDIDATE_COUNT=0
NEW_PRODUCT_CANDIDATE_TRIGGER_COUNT=0
VALID_CANDIDATE_OMISSION_FOUND=NO
DEEP_DIVE_BUDGET_SUPPRESSION_FOUND=NO

No confirmed ProductCandidate omission or Deep-Dive budget suppression was found. However, because the run terminated as PARTIAL rather than one of the package's successful statuses, these NO values are not a passed successful-sample candidate-integrity result. There is no genuine persisted ProductCandidate occurrence from this run to assess.

BASELINE_CREATION_ATTEMPTED=NO
BASELINE_COUNT=0
BASELINE_LOOKAHEAD_FOUND=NO
BASELINE_TRIGGER_SET_DRIFT_FOUND=NO
BASELINE_SOURCE_TIME_VIOLATION_FOUND=NO

No baseline was created because there was no new ProductCandidate. The three baseline integrity values mean that no violating baseline was found; they do not represent a passed real-sample integrity assessment.

PHASE2B_REFRESH_CALLS=0
DEALER_GEX_LIVE_CALLS=0
DEALER_GEX_SOURCE=ARCHIVE_ONLY

## Post-run cost and quota

PAID_UNITS_AFTER_SECOND_SCAN=227
QUOTA_LIMIT_AFTER_SECOND_SCAN=100000
QUOTA_REMAINING_AFTER_SECOND_SCAN=99684
QUOTA_FACT_AFTER_AT=2026-08-20T06:46:31.529167+00:00
SECOND_SCAN_OBSERVED_PAID_UNIT_DELTA=14
COST_CAP_EXCEEDED=NO

FIRST_CONTROLLED_SCAN_PAID_UNITS=14
SECOND_CONTROLLED_SCAN_PAID_UNITS=14
CUMULATIVE_CONTROLLED_SCAN_PAID_UNITS=28

The local usage-audit delta, ScanRun counter, 14 HTTP 200 usage rows, and quota-remaining delta all agree at 14.

## Runtime delta attributable to the second observation

SCAN_RUN_ROWS_ADDED_BY_SECOND_OBSERVATION=1
PRODUCT_CANDIDATE_ROWS_ADDED_BY_SECOND_OBSERVATION=0
TRIGGER_ROWS_ADDED_BY_SECOND_OBSERVATION=0
BASELINE_CONTEXT_ROWS_ADDED_BY_SECOND_OBSERVATION=0
ANOMALY_DETAIL_ROWS_ADDED_BY_SECOND_OBSERVATION=0

Additional run-linked rows:

| Table | Rows |
|---|---:|
| scan_stages | 7 |
| api_usage_audit | 14 |
| raw_vendor_payloads | 14 |
| ticker_scan_results | 7 |
| expiry_observations | 104 |
| contract_scan_observations | 1694 |
| strike_clusters | 5 |
| bucket_positioning_summaries | 0 |

All remote application writes were the normal writes of the one Founder-authorized second production observation. There was no manual SQL DML, schema write, migration, historical repair, baseline refresh, or unrelated runtime write.

## External endpoint ledger

Runtime PostgreSQL:

- postgresql://aws-0-ap-northeast-1.pooler.supabase.com:5432/postgres — read-only pre/post queries and normal writes from the one authorized scan; credentials omitted.

Nightwatch base URL: https://api.yehangshe.com

Each endpoint below was contacted exactly once, returned HTTP 200, consumed one paid unit, used one attempt, and had zero retries:

- https://api.yehangshe.com/v1/options/expiry-breakdown/AAPL
- https://api.yehangshe.com/v1/options/options-volume/AAPL
- https://api.yehangshe.com/v1/options/expiry-breakdown/MSFT
- https://api.yehangshe.com/v1/options/options-volume/MSFT
- https://api.yehangshe.com/v1/options/expiry-breakdown/NVDA
- https://api.yehangshe.com/v1/options/options-volume/NVDA
- https://api.yehangshe.com/v1/options/expiry-breakdown/AMZN
- https://api.yehangshe.com/v1/options/options-volume/AMZN
- https://api.yehangshe.com/v1/options/expiry-breakdown/META
- https://api.yehangshe.com/v1/options/options-volume/META
- https://api.yehangshe.com/v1/options/expiry-breakdown/GOOGL
- https://api.yehangshe.com/v1/options/options-volume/GOOGL
- https://api.yehangshe.com/v1/options/expiry-breakdown/TSLA
- https://api.yehangshe.com/v1/options/options-volume/TSLA

No daily_ohlc, stock_state, iv_rank, term_structure, Dealer/GEX live, GitHub, workflow, registry, or other HTTP endpoint was contacted.

## New outcome and stop handling

Observed finding:

- finding: The new run completed all persisted scanner stages through S6, but its terminal ScanRun status is PARTIAL and no ProductCandidate occurrence was materialized.
- evidence: ScanRun e9267160-503a-41c7-9bb1-8cc2b2e3d8c6 has status PARTIAL, NULL candidate materialization markers, and zero ProductCandidate rows.
- classification: FAIL_SCAN_NEW_DEFECT
- diagnosed in this task: NO
- remediated in this task: NO
- third scan performed: NO

The task stops at this observation. It does not determine why the terminal status was PARTIAL or propose a fix.

## Carried ledger

CURRENT_TRIGGER_FRESHNESS_MODE=CALIBRATION_REQUIRED
RADAR_OI_SCHEDULE_ACTIVATION=PENDING_ROLLOVER_EVIDENCE
CROSS_RUN_CANDIDATE_LIFECYCLE=DEFERRED_NO_AUTO_MERGE
IV_RANK_CORE_ELIGIBILITY=WITHHOLD_PENDING_PROVENANCE
ISOLATED_POSTGRES_RUNTIME_VERIFIED=NO
N1_HISTORICAL_RUNTIME_DISTRIBUTION_VERIFIED=NO

## Authorization ledger

APPLICATION_CODE_CHANGES_DURING_SECOND_OBSERVATION=0
TEST_CODE_CHANGES_DURING_SECOND_OBSERVATION=0
MIGRATION_FILES_CHANGED_DURING_SECOND_OBSERVATION=0
WORKFLOW_CHANGES=0
SCHEDULER_CHANGES=0

MAG7_SCAN_INVOCATIONS_THIS_TASK=1
NIGHTWATCH_REQUESTS_THIS_TASK=14
PAID_UNITS_THIS_TASK=14

REMOTE_MIGRATIONS_RUN=0
REMOTE_DB_SCHEMA_WRITES=0
REMOTE_APPLICATION_DATA_WRITES=AUTHORIZED_SECOND_CONTROLLED_OBSERVATION_ONLY

COMMITS_CREATED=0
PUSHES=0
PRS_CREATED=0
MERGES=0

THIRD_MAG7_SCAN_AUTHORIZED=NO
STAGE8_OBSERVATION_RESUME_READY=NO
STAGE9_READY=NO
NEXT_AUTHORIZED_STAGE=NONE

STOP. No broader Stage 8 analysis, new-defect diagnosis/remediation, third MAG7 scan, or Stage 9 work was started.


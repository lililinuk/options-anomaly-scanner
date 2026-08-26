# Nightwatch vNext — Third Controlled Live MAG7 Observation Report

Date: 2026-08-20
Worktree: `F:\options-anomaly-scanner-stage8`
Branch: `vnext/stage8-mag7-observation`
Base HEAD: `3a63eaa1b9069d34199704fe31ac6466e8929d7d`
Execution package SHA-256: `4264B89BF3295588920149798DC48CEF6043CB52194248EC738FF47559D7D37F`

## Executive result

```text
THIRD_CONTROLLED_OBSERVATION_RESULT=FAIL_BASELINE_CREATION
FOUNDER_AUTHORIZATION=THIRD_CONTROLLED_MAG7_OBSERVATION_20260820

THIRD_SCAN_INVOCATIONS_AUTHORIZED=1
ACTUAL_THIRD_SCAN_INVOCATIONS=1

THIRD_SCAN_RUN_ID=2c71e5bb-9334-4806-a195-0f8768d2d0f2
THIRD_SCAN_STATUS=COMPLETE
THIRD_SCAN_SAFE_ERROR=NONE
THIRD_SCAN_STARTED_AT=2026-08-20T10:03:43.762546+00:00
THIRD_SCAN_COMPLETED_AT=2026-08-20T10:07:16.687134+00:00
```

The one Founder-authorized production MAG7 invocation completed successfully with seven
ProductCandidates and 82 qualifying triggers. Both accepted Stage 8 scanner remediations passed
their runtime proof. Two selected AMZN Deep-Dive expiries still truthfully lacked matching complete
daily-chain archives, but this optional post-candidate gap no longer promoted the run to `PARTIAL`
or suppressed ProductCandidate materialization.

The subsequent one atomic attempt to create exactly one accepted
`FIRST_KNOWLEDGE_BASELINE` for each of the seven new candidates failed with safe exception class
`IntegrityError`. The transaction was rolled back; zero baseline contexts and zero anomaly details
remain. Per the execution package, baseline creation was not retried, diagnosed, or remediated.

## Package preservation and governing evidence

The attached execution package was absent from canonical evidence and was copied byte-for-byte to:

```text
F:\options-anomaly-scanner\docs\evidence\NIGHTWATCH_VNEXT_THIRD_CONTROLLED_LIVE_MAG7_OBSERVATION_EXECUTION_PACKAGE_20260820.md
```

```text
PACKAGE_SHA256=4264B89BF3295588920149798DC48CEF6043CB52194248EC738FF47559D7D37F
PACKAGE_BACKUP_BYTE_IDENTICAL=YES
PACKAGE_CONFLICT_FOUND=NO
```

Every canonical governing/report file named by the package was present and read completely. The
canonical manifest's older `MISSING_SOURCE` notation for the Stage 8 observation package is stale:
the explicitly required file was present at its canonical full path and was read completely. No
governing file had to be reconstructed.

## Code-state preflight

```text
WORKTREE_BRANCH=vnext/stage8-mag7-observation
WORKTREE_HEAD=3a63eaa1b9069d34199704fe31ac6466e8929d7d

ACCEPTED_S4_REMEDIATION_PRESENT=YES
ACCEPTED_POST_CANDIDATE_PARTIAL_REMEDIATION_PRESENT=YES
UNEXPECTED_APPLICATION_DIFF_FOUND=NO
GIT_DIFF_CHECK=PASS
```

The only tracked worktree differences before and after the observation remained:

- `backend/app/scanner/v13.py` — accepted S4 identifier and vNext post-candidate partial fixes.
- `backend/tests/test_stage4b_phase2a_vnext.py` — accepted regressions for both fixes and carried
  candidate-before-budget behavior.

The old 35-character identifier was absent from active application/tests. Four executable focused
preflight regressions passed: S4 identifier contract, post-candidate missing-archive isolation,
pre-existing partial preservation, and seven-candidate/four-Deep-Dive budget behavior.

```text
ACTIVE_S4_IDENTIFIER=S4_VNEXT_DEEP_BUDGET_SELECTION
ACTIVE_S4_IDENTIFIER_LENGTH=30
SCAN_STAGES_STAGE_MAX_LENGTH=32
```

Final accepted remediation file hashes:

```text
V13_SHA256=E7B7E0A58EE3B30FC3AD3EA69A3E7251C2843381E39995EA27C0D0E33F035DC5
STAGE4B_TEST_SHA256=A0CD77DDACF8A7E8C0896C01715A209CE2AD90FF7996289E8AE407CD4E03186E
```

## Runtime and before-state preflight

One explicit PostgreSQL `READ ONLY` transaction proved:

```text
REMOTE_ALEMBIC_HEAD=20260818_0017
PRODUCT_CANDIDATE_TABLE_PRESENT=YES
PRODUCT_CANDIDATE_TRIGGER_TABLE_PRESENT=YES
PRODUCT_CANDIDATE_CONTEXT_TABLE_PRESENT=YES
ANOMALY_CONTEXT_DETAIL_TABLE_PRESENT=YES
RUNNING_SCAN_COUNT_BEFORE=0
```

Historical controlled runs before execution:

```text
FIRST_CONTROLLED_RUN_ID=090359ad-9d76-49b9-8902-f28ac54a1d1b
FIRST_CONTROLLED_RUN_STATUS=FAILED

SECOND_CONTROLLED_RUN_ID=e9267160-503a-41c7-9bb1-8cc2b2e3d8c6
SECOND_CONTROLLED_RUN_STATUS=PARTIAL
```

Before-state counts:

| Table | Rows before |
|---|---:|
| scan_runs | 8 |
| scan_stages | 50 |
| product_candidates | 0 |
| product_candidate_triggers | 0 |
| product_candidate_contexts | 0 |
| anomaly_context_details | 0 |
| api_usage_audit | 275 |
| raw_vendor_payloads | 263 |

## Cost-bound and quota preflight

```text
VENDOR_FANOUT_CHANGED_BY_REMEDIATIONS=NO
RETRY_LOGIC_CHANGED_BY_REMEDIATIONS=NO
UNIVERSE_CHANGED_BY_REMEDIATIONS=NO

THIRD_SCAN_COST_BOUND_PROVEN=YES
MAX_CONFIGURED_PAID_UNITS_FOR_THIRD_SCAN=14
```

The production CLI fixes `max_retries=0`. The accepted universe remains exactly seven MAG7
tickers, and the active scan makes exactly two paid activity requests per ticker:

```text
7 tickers x 2 endpoints x 1 attempt = 14 maximum paid units
14 <= THIRD_SCAN_HARD_PAID_UNIT_CAP 20
```

Authoritative persisted pre-run facts:

```text
PAID_UNITS_BEFORE_THIRD_SCAN=227
QUOTA_LIMIT_BEFORE_THIRD_SCAN=100000
QUOTA_REMAINING_BEFORE_THIRD_SCAN=99684
QUOTA_FACT_BEFORE_AT=2026-08-20T06:46:31.529167+00:00
```

The quota fact was the latest locally persisted authoritative header before execution; its
timestamp is disclosed because vendor quota activity outside this isolated run may occur between
quota facts.

## Exactly one production invocation

```text
MAG7_SCAN_INVOCATIONS_THIS_TASK=1
NIGHTWATCH_REQUESTS_THIS_TASK=14
PAID_UNITS_THIS_TASK=14

SCAN_SPECIFICATION_VERSION=phase2a_vnext_stage4b
SCAN_MARKET_DATE=2026-08-20
SCAN_CONSUMED_QUOTA_UNITS=14
SCAN_NETWORK_ATTEMPTS=14
SCAN_CACHE_HITS=0
SCAN_FRESH_REQUESTS=14
SCAN_RETRIES=0
SCAN_HTTP_200_RESPONSES=14
```

The invocation used the remediated working-tree code, accepted thresholds/scoring, fixed MAG7
universe, and normal production persistence. It was not retried. No fixture, threshold override,
manual candidate seed, second invocation, Phase 2B refresh, or Dealer/GEX live request was used.

Persisted stages:

| Stage | Status |
|---|---|
| S0_PREFLIGHT_V11 | COMPLETE |
| S2_ACTIVITY_SURFACE_V12 | COMPLETE |
| S3_DISCOVERY_CONFIRMATION | COMPLETE |
| S3_VNEXT_ACTIVE_DISCOVERY | COMPLETE |
| S4_VNEXT_DEEP_BUDGET_SELECTION | COMPLETE |
| S5_STRUCTURE_AND_RADAR | COMPLETE |
| S6_POSITIONING_SUMMARY_V12 | COMPLETE |

## Runtime proof — S4 identifier

```text
THIRD_RUN_S4_STAGE_ROW_PRESENT=YES
THIRD_RUN_S4_STAGE_IDENTIFIER=S4_VNEXT_DEEP_BUDGET_SELECTION
THIRD_RUN_S4_STAGE_IDENTIFIER_LENGTH=30
S4_LENGTH_DATAERROR_RECURRED=NO
```

S4 persisted 17 eligible expiries, 10 selected expiries, 4 selected tickers, and seven operationally
truncated expiries. Its telemetry explicitly retained `candidate_identity_affected=false`.

## Runtime proof — optional post-candidate Deep-Dive semantics

Two of ten selected Deep-Dive expiries lacked a matching archive satisfying ticker, expiration,
vendor OI date, and `chain_status=COMPLETE`:

| Ticker | Expiration | Vendor OI date | Structure result |
|---|---|---|---|
| AMZN | 2026-08-21 | 2026-08-11 | missing; no structure fabricated |
| AMZN | 2026-08-28 | 2026-08-11 | missing; no structure fabricated |

```text
THIRD_RUN_MISSING_DEEP_DIVE_STRUCTURE_COUNT=2
THIRD_RUN_MISSING_DEEP_DIVE_STRUCTURE_ITEMS=AMZN:2026-08-21:2026-08-11;AMZN:2026-08-28:2026-08-11
POST_CANDIDATE_DEEP_DIVE_ONLY_CAUSED_RUN_PARTIAL=NO
MISSING_STRUCTURE_FABRICATED=NO
```

Despite the same truthful source gaps observed in the second controlled run, the third run
completed and materialized candidates. The prior post-candidate `PARTIAL` defect did not recur.

## ProductCandidate readback

Readback was restricted to candidates linked to the new third ScanRun:

```text
NEW_PRODUCT_CANDIDATE_COUNT=7
NEW_PRODUCT_CANDIDATE_TRIGGER_COUNT=82
CANDIDATE_FIRST_KNOWLEDGE_AT=2026-08-20T10:07:16.687134+00:00
MATERIALIZATION_RULE_VERSION=phase2a_vnext_stage4b.product-candidate-materialization.v1
MATERIALIZATION_RULE_HASH=482a09a33630f81288eabca9a46dc1d75b9374310f87d267c3dc9d3dcab73ebd
```

| Ticker | Triggers | Qualifying | Supporting | Families |
|---|---:|---:|---:|---|
| AAPL | 13 | 13 | 0 | EXPIRY_ACTIVITY, RADAR_EVENT |
| AMZN | 10 | 10 | 0 | EXPIRY_ACTIVITY, RADAR_EVENT |
| GOOGL | 9 | 9 | 0 | EXPIRY_ACTIVITY, RADAR_EVENT |
| META | 4 | 4 | 0 | EXPIRY_ACTIVITY, RADAR_EVENT |
| MSFT | 5 | 5 | 0 | EXPIRY_ACTIVITY, RADAR_EVENT |
| NVDA | 27 | 27 | 0 | EXPIRY_ACTIVITY, RADAR_EVENT |
| TSLA | 14 | 14 | 0 | EXPIRY_ACTIVITY, RADAR_EVENT |

All seven MAG7 tickers materialized although only four received Deep-Dive budget and AMZN had two
missing selected structure archives.

```text
VALID_CANDIDATE_OMISSION_FOUND=NO
DEEP_DIVE_BUDGET_SUPPRESSION_FOUND=NO
DEEP_DIVE_AVAILABILITY_SUPPRESSION_FOUND=NO
```

## FIRST_KNOWLEDGE_BASELINE attempt

Before baseline creation, the new run had zero baseline rows. The accepted
`Stage6BalancedContextService` was constructed with no vendor client and called once for each of
the seven new candidate IDs in one atomic transaction. It uses
`candidate_first_knowledge_at` as `evidence_cutoff_at` and archive-only source queries.

```text
BASELINE_CREATION_ATTEMPTED=YES
BASELINE_CANDIDATES_ATTEMPTED=7
BASELINE_CREATION_SAFE_ERROR=IntegrityError
BASELINE_TRANSACTION_ROLLED_BACK=YES
BASELINE_RETRY_ATTEMPTED=NO
BASELINE_DIAGNOSIS_OR_REMEDIATION_PERFORMED=NO

BASELINE_COUNT=0
ANOMALY_CONTEXT_DETAIL_COUNT=0
```

The package requires `FAIL_BASELINE_CREATION` and no retry when this operation fails. A final
read-only transaction proved that rollback left both Stage 6 tables empty. Because no baseline was
persisted, no lookahead, trigger drift, or source-time violation was found; these `NO` values are
absence-of-violation results, not a successful baseline-integrity assessment.

```text
BASELINE_LOOKAHEAD_FOUND=NO
BASELINE_TRIGGER_SET_DRIFT_FOUND=NO
BASELINE_SOURCE_TIME_VIOLATION_FOUND=NO

PHASE2B_REFRESH_CALLS=0
DEALER_GEX_LIVE_CALLS=0
DEALER_GEX_SOURCE=ARCHIVE_ONLY
```

## Post-scan cost and quota

```text
PAID_UNITS_AFTER_THIRD_SCAN=241
QUOTA_LIMIT_AFTER_THIRD_SCAN=100000
QUOTA_REMAINING_AFTER_THIRD_SCAN=99667
QUOTA_FACT_AFTER_AT=2026-08-20T10:05:43.227963+00:00

THIRD_SCAN_OBSERVED_PAID_UNIT_DELTA=14
COST_CAP_EXCEEDED=NO

FIRST_CONTROLLED_SCAN_PAID_UNITS=14
SECOND_CONTROLLED_SCAN_PAID_UNITS=14
THIRD_CONTROLLED_SCAN_PAID_UNITS=14
CUMULATIVE_CONTROLLED_SCAN_PAID_UNITS=42
```

The authoritative per-run ScanRun counter, 14 run-linked usage rows, 14 `consumed_quota=true`
rows, 14 HTTP 200 responses, zero retries, and total locally persisted paid-unit increase from 227
to 241 all agree at 14. The older pre-run quota header fact and post-run header differ by 17; that
non-isolated header delta is not attributed to the third scan because the pre-run fact was more
than three hours old and the new run's authoritative records isolate exactly 14 units.

## Runtime delta

| Table | Before | After | Attributable delta |
|---|---:|---:|---:|
| scan_runs | 8 | 9 | +1 |
| scan_stages | 50 | 57 | +7 |
| product_candidates | 0 | 7 | +7 |
| product_candidate_triggers | 0 | 82 | +82 |
| product_candidate_contexts | 0 | 0 | 0 |
| anomaly_context_details | 0 | 0 | 0 |
| api_usage_audit | 275 | 289 | +14 |
| raw_vendor_payloads | 263 | 277 | +14 |

```text
SCAN_RUN_ROWS_ADDED_BY_THIRD_OBSERVATION=1
PRODUCT_CANDIDATE_ROWS_ADDED_BY_THIRD_OBSERVATION=7
TRIGGER_ROWS_ADDED_BY_THIRD_OBSERVATION=82
BASELINE_CONTEXT_ROWS_ADDED_BY_THIRD_OBSERVATION=0
ANOMALY_DETAIL_ROWS_ADDED_BY_THIRD_OBSERVATION=0
```

## Historical truth and code integrity

Final read-only verification preserved both historical run states:

```text
FIRST_CONTROLLED_RUN_STATUS_AFTER=FAILED
SECOND_CONTROLLED_RUN_STATUS_AFTER=PARTIAL
FIRST_CONTROLLED_RUN_MUTATED=NO
SECOND_CONTROLLED_RUN_MUTATED=NO
```

The third run remains truthfully `COMPLETE`; the failed baseline transaction did not relabel or
mutate it. Final `git status`, tracked path list, file hashes, and `git diff --check` prove the
observation introduced no application/test/migration/workflow/scheduler change.

## External endpoint ledger

Runtime PostgreSQL:

- `postgresql://aws-0-ap-northeast-1.pooler.supabase.com:5432/postgres` — credential-safe
  read-only pre/post verification, normal writes from the one authorized scan, and one rolled-back
  atomic baseline attempt; credentials omitted.

Nightwatch base URL: `https://api.yehangshe.com`

Each endpoint below was contacted exactly once, returned HTTP 200, consumed one paid unit, used one
attempt, and had zero retries:

- `https://api.yehangshe.com/v1/options/expiry-breakdown/AAPL`
- `https://api.yehangshe.com/v1/options/options-volume/AAPL`
- `https://api.yehangshe.com/v1/options/expiry-breakdown/MSFT`
- `https://api.yehangshe.com/v1/options/options-volume/MSFT`
- `https://api.yehangshe.com/v1/options/expiry-breakdown/NVDA`
- `https://api.yehangshe.com/v1/options/options-volume/NVDA`
- `https://api.yehangshe.com/v1/options/expiry-breakdown/AMZN`
- `https://api.yehangshe.com/v1/options/options-volume/AMZN`
- `https://api.yehangshe.com/v1/options/expiry-breakdown/META`
- `https://api.yehangshe.com/v1/options/options-volume/META`
- `https://api.yehangshe.com/v1/options/expiry-breakdown/GOOGL`
- `https://api.yehangshe.com/v1/options/options-volume/GOOGL`
- `https://api.yehangshe.com/v1/options/expiry-breakdown/TSLA`
- `https://api.yehangshe.com/v1/options/options-volume/TSLA`

No `daily_ohlc`, `stock_state`, `iv_rank`, `term_structure`, live Dealer/GEX, GitHub, workflow,
registry, or other HTTP endpoint was contacted.

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
APPLICATION_CODE_CHANGES_DURING_THIRD_OBSERVATION=0
TEST_CODE_CHANGES_DURING_THIRD_OBSERVATION=0
MIGRATION_FILES_CHANGED_DURING_THIRD_OBSERVATION=0
WORKFLOW_CHANGES=0
SCHEDULER_CHANGES=0

MAG7_SCAN_INVOCATIONS_THIS_TASK=1
NIGHTWATCH_REQUESTS_THIS_TASK=14
PAID_UNITS_THIS_TASK=14

REMOTE_ALEMBIC_HEAD=20260818_0017
REMOTE_MIGRATIONS_RUN=0
REMOTE_DB_SCHEMA_WRITES=0
REMOTE_APPLICATION_DATA_WRITES=AUTHORIZED_THIRD_CONTROLLED_OBSERVATION_ONLY

COMMITS_CREATED=0
PUSHES=0
PRS_CREATED=0
MERGES=0
```

## Final boundary

```text
FOURTH_MAG7_SCAN_AUTHORIZED=NO
STAGE8_OBSERVATION_RESUME_READY=NO
STAGE9_READY=NO
NEXT_AUTHORIZED_STAGE=NONE
```

The third scan authorization is exhausted. No fourth scan, broader Stage 8 analysis, baseline
retry/diagnosis/remediation, or Stage 9 work was started.

STOP.

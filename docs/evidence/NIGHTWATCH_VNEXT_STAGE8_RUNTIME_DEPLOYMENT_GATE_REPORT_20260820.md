# Nightwatch vNext — Stage 8 Runtime Deployment / Migration Gate Report

**Date:** 2026-08-20  
**Execution worktree:** `F:\options-anomaly-scanner-stage8`  
**Branch:** `vnext/stage8-mag7-observation`  
**Accepted HEAD/base:** `3a63eaa1b9069d34199704fe31ac6466e8929d7d`  
**Scope:** Remote PostgreSQL schema deployment only; no application observation or vendor call

## A. Result

```text
RUNTIME_DEPLOYMENT_RESULT=PASS
REMOTE_ALEMBIC_HEAD_BEFORE=20260815_0013
REMOTE_ALEMBIC_HEAD_AFTER=20260818_0017
STAGE8_RUNTIME_SCHEMA_READY=YES
STAGE8_OBSERVATION_RESUME_READY=YES
```

The configured runtime PostgreSQL schema was upgraded through the exact accepted linear Alembic
chain. All preflight checks passed before the single authorized migration command. Post-migration
read-only verification found every required schema object, no historical backfill, no application
row-count change, and empty new prospective Stage 5/6 tables.

Stage 8 observation was **not** resumed by this task.

## B. Governing evidence and package preservation

The deployment package was saved byte-for-byte in the canonical evidence root:

```text
PACKAGE_PATH=F:\options-anomaly-scanner\docs\evidence\NIGHTWATCH_VNEXT_STAGE8_RUNTIME_DEPLOYMENT_GATE_EXECUTION_PACKAGE_20260820.md
PACKAGE_SHA256=FD3D496A37E44F5D75475E8C6BFC448A9513A43EFE474841CB141D5C742E9F79
```

All governing files named by the package were present in the canonical evidence root, read
completely, and hash-checked against their preserved canonical values. The current Stage 8
prerequisite report was also read completely from the Stage 8 worktree.

```text
MISSING_GOVERNING_FILES=0
GOVERNING_HASH_MISMATCHES=0
```

## C. Worktree integrity

```text
WORKTREE_BRANCH=vnext/stage8-mag7-observation
WORKTREE_HEAD=3a63eaa1b9069d34199704fe31ac6466e8929d7d
REPOSITORY_ALEMBIC_HEAD=20260818_0017
ALEMBIC_SINGLE_HEAD=YES
APPLICATION_OR_MIGRATION_FILES_DIRTY=NO
GIT_DIFF_CHECK=PASS
```

Before migration, `git status --short` contained only the permitted untracked
`docs/evidence/stage8/` directory. No application, test, migration, configuration, workflow, or
scheduler file was modified, reset, cleaned, stashed, or overwritten.

## D. Alembic chain proof

Repository `alembic history --verbose`, the revision declarations, and every migration script
proved one exact path:

```text
MIGRATION_CHAIN_LINEAR=YES
MIGRATION_CHAIN=20260815_0013 -> 20260817_0014 -> 20260818_0015 -> 20260818_0016 -> 20260818_0017
```

```text
MIGRATIONS_APPLIED=[
  20260817_0014,
  20260818_0015,
  20260818_0016,
  20260818_0017
]
```

No branch, merge revision, missing revision, extra revision, stamp, downgrade, or incompatible
descendant was present.

## E. Migration semantic review

### Revision 20260817_0014

```text
REVISION=20260817_0014
DOWN_REVISION=20260815_0013
PURPOSE=Stage 3 time/knowledge integrity foundation
CREATES=2 indexes; 1 FK; 1 check constraint
ALTERS=phase2b_ticker_context_snapshots (3 nullable columns); phase2b_candidate_evaluations (3 nullable columns)
DROPS=NONE_IN_UPGRADE
APPLICATION_DATA_DML=NONE
HISTORICAL_BACKFILL=NO
DESTRUCTIVE_CHANGE=NO
```

Added source-first-receipt, freshness/provenance, pinned Radar source, and nullable evaluation
identity foundations. No historical value was inferred.

### Revision 20260818_0015

```text
REVISION=20260818_0015
DOWN_REVISION=20260817_0014
PURPOSE=Stage 4A daily-pipeline evidence identities
CREATES=zero_dte_activity_session_snapshots plus PK/FKs/checks/unique/index; daily-coverage constraints
ALTERS=daily_collection_coverage (2 nullable columns); contract_oi_daily_snapshots (1 nullable column)
DROPS=NONE_IN_UPGRADE
APPLICATION_DATA_DML=NONE
HISTORICAL_BACKFILL=NO
DESTRUCTIVE_CHANGE=NO
```

Historical coverage/OI rows remained gaps/NULL; the migration did not classify or copy legacy
0DTE rows into the new table.

### Revision 20260818_0016

```text
REVISION=20260818_0016
DOWN_REVISION=20260818_0015
PURPOSE=Stage 5 ProductCandidate persistence
CREATES=product_candidates; product_candidate_triggers; associated PK/FKs/checks/unique/indexes
ALTERS=scan_runs (3 nullable occurrence-marker columns plus all-or-none check)
DROPS=NONE_IN_UPGRADE
APPLICATION_DATA_DML=NONE
HISTORICAL_BACKFILL=NO
DESTRUCTIVE_CHANGE=NO
```

No historical scan was converted into a ProductCandidate occurrence.

### Revision 20260818_0017

```text
REVISION=20260818_0017
DOWN_REVISION=20260818_0016
PURPOSE=Stage 6 Balanced Product-Candidate context persistence
CREATES=product_candidate_contexts; anomaly_context_details; associated PK/FKs/checks/unique/indexes
ALTERS=NONE
DROPS=NONE_IN_UPGRADE
APPLICATION_DATA_DML=NONE
HISTORICAL_BACKFILL=NO
DESTRUCTIVE_CHANGE=NO
```

No legacy v1.2/v2.0/v3.1 context row was converted into a vNext baseline or refresh.

## F. Remote read-only preflight

The preflight used an explicit read-only transaction. No credential-bearing URL, username,
password, API key, or Authorization header was printed.

```text
REMOTE_DB_REACHABLE=YES
REMOTE_ALEMBIC_HEAD=20260815_0013
PUBLIC_TABLE_COUNT_BEFORE=32
REQUIRED_BASE_TABLES_PRESENT=10/10
TARGET_NEW_TABLES_PRESENT_BEFORE=0/5
TARGET_COLUMNS_PRESENT_BEFORE=0/12
TARGET_INDEX_OR_RELATION_NAME_COLLISIONS=0
TARGET_CONSTRAINT_COLLISIONS=0
SCHEMA_DRIFT_FOUND=NO
```

Required base tables and migration anchor columns existed with compatible PostgreSQL types,
including UUID FK targets, ticker/contract-symbol fields, daily coverage identity fields, and the
existing scan/context tables.

The following target tables were all absent before migration:

```text
zero_dte_activity_session_snapshots
product_candidates
product_candidate_triggers
product_candidate_contexts
anomaly_context_details
```

All target columns on existing tables, all emitted index names, and all target constraints were
absent. No partial/out-of-band migration state was found.

## G. Before-state application row-count evidence

Only aggregate counts were collected; no sensitive row contents were dumped.

| Existing application table | Rows before | Rows after |
|---|---:|---:|
| `api_usage_audit` | 247 | 247 |
| `bucket_positioning_summaries` | 104 | 104 |
| `capability_snapshots` | 282 | 282 |
| `contract_oi_daily_snapshots` | 11,290 | 11,290 |
| `contract_scan_observations` | 5,680 | 5,680 |
| `daily_collection_coverage` | 11 | 11 |
| `daily_collection_runs` | 1 | 1 |
| `daily_expiry_activity_snapshots` | 0 | 0 |
| `daily_oi_archive_runs` | 1 | 1 |
| `daily_oi_archive_tickers` | 7 | 7 |
| `dealer_gex_archive_runs` | 7 | 7 |
| `dealer_gex_snapshot_cells` | 8,326 | 8,326 |
| `dealer_gex_snapshots` | 42 | 42 |
| `expiry_observations` | 647 | 647 |
| `expiry_oi_daily_snapshots` | 105 | 105 |
| `metadata_refreshes` | 3 | 3 |
| `oi_change_radar_observations` | 550 | 550 |
| `oi_confirmation_events` | 0 | 0 |
| `option_contract_observations` | 0 | 0 |
| `phase2b_candidate_evaluations` | 4 | 4 |
| `phase2b_candidate_states` | 3 | 3 |
| `phase2b_ticker_context_snapshots` | 9 | 9 |
| `phase2b_v3_research_workspaces` | 2 | 2 |
| `position_lifecycle_events` | 0 | 0 |
| `raw_vendor_payloads` | 235 | 235 |
| `scan_runs` | 6 | 6 |
| `scan_stages` | 39 | 39 |
| `signal_detections` | 0 | 0 |
| `strike_clusters` | 9 | 9 |
| `ticker_scan_results` | 42 | 42 |
| `zero_dte_activity_daily_snapshots` | 7 | 7 |

```text
EXISTING_APPLICATION_TABLES_COMPARED=31
APPLICATION_ROW_COUNT_CHANGED_BY_MIGRATION=NO
```

## H. Offline SQL verification

PostgreSQL offline SQL was generated for exactly
`20260815_0013:20260818_0017` and read completely before the remote write.

```text
OFFLINE_UPGRADE_SQL_GENERATED=YES
OFFLINE_SQL_BEGIN_COMMIT_TRANSACTIONAL=YES
UNEXPECTED_APPLICATION_DML_FOUND=NO
UNEXPECTED_DESTRUCTIVE_DDL_FOUND=NO
```

The only DML consisted of four `UPDATE alembic_version` statements advancing the Alembic
bookkeeping revision. There was no application-table `INSERT`, `UPDATE`, or `DELETE`, no `DROP`,
no destructive rename, and no historical rewrite.

## I. Authorized migration execution

After every preflight gate passed, the only remote write command executed was:

```text
alembic upgrade 20260818_0017
```

Alembic reported four sequential upgrades and completed under PostgreSQL transactional DDL:

```text
20260815_0013 -> 20260817_0014
20260817_0014 -> 20260818_0015
20260818_0015 -> 20260818_0016
20260818_0016 -> 20260818_0017
```

No stamp, downgrade, manual DDL, manual repair, application DML, backfill, scanner, baseline POST,
context refresh, workflow, or vendor call was executed.

## J. Post-migration schema verification

Post verification used read-only catalog and aggregate queries.

```text
REMOTE_ALEMBIC_HEAD_AFTER=20260818_0017
ALEMBIC_SINGLE_HEAD=YES
PUBLIC_TABLE_COUNT_AFTER=37

PRODUCT_CANDIDATE_TABLE_PRESENT=YES
PRODUCT_CANDIDATE_TRIGGER_TABLE_PRESENT=YES
PRODUCT_CANDIDATE_CONTEXT_TABLE_PRESENT=YES
ANOMALY_CONTEXT_DETAIL_TABLE_PRESENT=YES
ZERO_DTE_ACTIVITY_SESSION_TABLE_PRESENT=YES

EXPECTED_MIGRATION_COLUMNS_MISSING=0
EXPECTED_INDEXES_MISSING_OR_INVALID=0
EXPECTED_CONSTRAINTS_MISSING_OR_UNVALIDATED=0
EXPECTED_PRIMARY_KEYS_PRESENT=YES
EXPECTED_FOREIGN_KEYS_PRESENT=YES
EXPECTED_UNIQUE_CONSTRAINTS_PRESENT=YES
EXPECTED_CHECK_CONSTRAINTS_PRESENT=YES
```

All model/migration-relevant columns were present. Every expected index was valid and every
expected PK/FK/unique/check constraint was present and validated.

## K. Historical preservation verification

Immediately after migration, before any scanner or other application process:

```text
ZERO_DTE_ACTIVITY_SESSION_ROW_COUNT=0
PRODUCT_CANDIDATE_ROW_COUNT=0
PRODUCT_CANDIDATE_TRIGGER_ROW_COUNT=0
PRODUCT_CANDIDATE_CONTEXT_ROW_COUNT=0
ANOMALY_CONTEXT_DETAIL_ROW_COUNT=0

HISTORICAL_PRODUCT_CANDIDATE_BACKFILL_FOUND=NO
HISTORICAL_CONTEXT_BACKFILL_FOUND=NO
APPLICATION_ROW_COUNT_CHANGED_BY_MIGRATION=NO
```

Nullable-field preservation on existing historical rows:

| Existing table / new field group | Rows | NULL | Non-NULL |
|---|---:|---:|---:|
| `phase2b_ticker_context_snapshots.source_first_received_at` | 9 | 9 | 0 |
| `phase2b_ticker_context_snapshots.freshness_anchor_at` | 9 | 9 | 0 |
| `phase2b_ticker_context_snapshots.source_time_provenance` | 9 | 9 | 0 |
| `phase2b_candidate_evaluations.source_first_received_at` | 4 | 4 | 0 |
| `phase2b_candidate_evaluations.source_radar_observation_id` | 4 | 4 | 0 |
| `phase2b_candidate_evaluations.evaluation_identity` | 4 | 4 | 0 |
| `daily_collection_coverage.activity_market_date` | 11 | 11 | 0 |
| `daily_collection_coverage.vendor_oi_date` | 11 | 11 | 0 |
| `contract_oi_daily_snapshots.open_interest_as_of` | 11,290 | 11,290 | 0 |
| `scan_runs.candidate_materialized_at` | 6 | 6 | 0 |
| `scan_runs.candidate_materialization_rule_version` | 6 | 6 | 0 |
| `scan_runs.candidate_materialization_rule_hash` | 6 | 6 | 0 |

Thus all six historical scan runs remained unmaterialized and no new Stage 3/4A field was
manufactured from legacy timestamps or dates.

## L. Schema-only smoke

```text
READ_ONLY_EMPTY_NEW_TABLE_SELECTS=PASS
MODEL_RELEVANT_SCHEMA_METADATA=PASS
APPLICATION_DATA_CREATED_BY_SMOKE=NO
VENDOR_CALLS_FROM_SMOKE=0
```

The empty-table counts and catalog/constraint inspection served as the permitted schema-only
smoke. No API POST or application materializer was invoked.

## M. Carried items

No carried item was incorrectly closed:

```text
CURRENT_TRIGGER_FRESHNESS_MODE=CALIBRATION_REQUIRED
RADAR_OI_SCHEDULE_ACTIVATION=PENDING_ROLLOVER_EVIDENCE
CROSS_RUN_CANDIDATE_LIFECYCLE=DEFERRED_NO_AUTO_MERGE
IV_RANK_CORE_ELIGIBILITY=WITHHOLD_PENDING_PROVENANCE
ISOLATED_POSTGRES_RUNTIME_VERIFIED=NO
N1_HISTORICAL_RUNTIME_DISTRIBUTION_VERIFIED=NO
```

This remote Supabase deployment does not satisfy the isolated-PostgreSQL carried gate.

## N. Authorization ledger

```text
APPLICATION_CODE_CHANGES=0
TEST_CODE_CHANGES=0
MIGRATION_FILES_CHANGED=0

REMOTE_MIGRATIONS_RUN=1
REMOTE_DB_SCHEMA_WRITES=AUTHORIZED_ALEMBIC_ONLY
REMOTE_APPLICATION_DATA_WRITES=0

NIGHTWATCH_REQUESTS=0
PAID_UNITS=0
WORKFLOWS_DISPATCHED=0

COMMITS_CREATED=0
PUSHES=0
PRS_CREATED=0
MERGES=0
```

External endpoint contacted:

```text
EXTERNAL_URLS_OR_API_ENDPOINTS_CONTACTED=[
  "postgresql://aws-0-ap-northeast-1.pooler.supabase.com:5432/postgres (read-only pre/post verification plus the one authorized Alembic schema migration; username/password omitted)"
]
```

No Nightwatch, HTTP(S), GitHub API, workflow, package registry, or other external endpoint was
contacted.

## O. Final boundary

```text
STAGE8_RUNTIME_SCHEMA_READY=YES
STAGE8_OBSERVATION_RESUME_READY=YES

STAGE9_READY=NO
NEXT_AUTHORIZED_STAGE=NONE
```

This PASS authorizes no automatic continuation. Stage 8 observation was not resumed, MAG7 was not
run, and Stage 9 was not started.

STOP.

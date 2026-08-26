# Nightwatch vNext — Stage 8 Runtime Deployment / Migration Gate — Execution Package

**Date:** 2026-08-20  
**Purpose:** Bring the already-configured Nightwatch runtime PostgreSQL schema from accepted runtime head `20260815_0013` to repository head `20260818_0017`, then stop.  
**Authorization:** Remote schema migration only, under the exact accepted migration chain. No scanner run, no Nightwatch call, no application-code change, no historical backfill.

## 0. Trigger

Stage 8 observation stopped correctly with:

```text
STAGE8_RESULT=HOLD_RUNTIME_PREREQUISITE
RUNTIME_DB_REACHABLE=YES
RUNTIME_DB_SCHEMA_HEAD=20260815_0013
STAGE8_RUNTIME_SCHEMA_READY=NO
RUNTIME_DEPLOYMENT_GATE_REQUIRED=YES
```

The runtime lacks:

```text
product_candidates
product_candidate_triggers
product_candidate_contexts
anomaly_context_details
```

Repository accepted head:

```text
20260818_0017
```

This package authorizes the narrow deployment gate needed before Stage 8 can resume.

---

## 1. Execution location

Use the existing Stage 8 worktree:

```text
F:\options-anomaly-scanner-stage8
branch = vnext/stage8-mag7-observation
base/HEAD = 3a63eaa1b9069d34199704fe31ac6466e8929d7d
```

Stage 8 evidence files may be uncommitted.

Do not create a new branch unless the current worktree no longer matches this accepted state.

Do not commit, push, PR, or merge.

---

## 2. Canonical evidence root

Read governing evidence directly from:

```text
F:\options-anomaly-scanner\docs\evidence
```

Read completely:

```text
F:\options-anomaly-scanner\docs\evidence\NIGHTWATCH_VNEXT_CANONICAL_EVIDENCE_MANIFEST.md

F:\options-anomaly-scanner\docs\evidence\NIGHTWATCH_SCANNER_VNEXT_INTEGRATED_SPEC_PROMPT_20260817(1).md

F:\options-anomaly-scanner\docs\evidence\NIGHTWATCH_VNEXT_STAGE3_TIME_KNOWLEDGE_INTEGRITY_CODEX_EXECUTION_PACKAGE_20260817.md

F:\options-anomaly-scanner\docs\evidence\NIGHTWATCH_VNEXT_STAGE4A_DAILY_PIPELINE_CODEX_EXECUTION_PACKAGE_20260818.md

F:\options-anomaly-scanner\docs\evidence\NIGHTWATCH_VNEXT_STAGE5_PRODUCT_CANDIDATE_PERSISTENCE_COMPLETION_REPORT_20260818.md

F:\options-anomaly-scanner\docs\evidence\NIGHTWATCH_VNEXT_STAGE6_PHASE2B_BALANCED_MODEL_COMPLETION_REPORT_20260818.md

F:\options-anomaly-scanner\docs\evidence\NIGHTWATCH_VNEXT_STAGE6_BASELINE_CUTOFF_REMEDIATION_PASS_20260820.md

F:\options-anomaly-scanner\docs\evidence\NIGHTWATCH_VNEXT_STAGE7_CANDIDATE_FIRST_DASHBOARD_COMPLETION_REPORT_20260819.md

F:\options-anomaly-scanner\docs\evidence\NIGHTWATCH_VNEXT_STAGE8_MAG7_OBSERVATION_EXECUTION_PACKAGE_20260820.md
```

Also read the current Stage 8 prerequisite report:

```text
F:\options-anomaly-scanner-stage8\docs\evidence\stage8\NIGHTWATCH_VNEXT_STAGE8_MAG7_OBSERVATION_REPORT_20260820.md
```

Do not ask the Founder to re-upload files that exist at these paths.

---

## 3. Exact migration chain

The only authorized target is:

```text
20260815_0013
    ↓
20260817_0014
    ↓
20260818_0015
    ↓
20260818_0016
    ↓
20260818_0017
```

Before any remote write, verify the actual repository Alembic graph proves this exact single linear path.

Return:

```text
REPOSITORY_ALEMBIC_HEAD=
REMOTE_ALEMBIC_HEAD=
MIGRATION_CHAIN_LINEAR=YES/NO
MIGRATION_CHAIN=
```

If the chain differs, has a branch, missing revision, extra revision, or incompatible descendant:

```text
RUNTIME_DEPLOYMENT_RESULT=HOLD_ALEMBIC_CHAIN_MISMATCH
```

STOP.

---

## 4. Migration semantic preflight

Read every migration script in the exact 0013→0017 path.

For each migration report:

```text
REVISION=
DOWN_REVISION=
PURPOSE=
CREATES=
ALTERS=
DROPS=
APPLICATION_DATA_DML=
HISTORICAL_BACKFILL=
DESTRUCTIVE_CHANGE=
```

Expected accepted semantics:

```text
0014 — Stage 3 time/knowledge integrity foundation
       additive/nullable foundation, no invented historical backfill

0015 — Stage 4A daily pipeline schema
       additive, historical gaps remain gaps

0016 — Stage 5 ProductCandidate persistence
       additive candidate/trigger tables + minimal occurrence markers
       no historical ProductCandidate reconstruction/backfill

0017 — Stage 6 Balanced context
       additive ProductCandidateContext / AnomalyContextDetail
       no historical context backfill
```

If any migration contains unexpected application-data:

```text
UPDATE
DELETE
INSERT
```

other than Alembic bookkeeping, or unexpected destructive DDL:

```text
DROP TABLE
DROP COLUMN
destructive rename
historical rewrite
```

return:

```text
RUNTIME_DEPLOYMENT_RESULT=HOLD_MIGRATION_SEMANTIC_CONFLICT
```

STOP.

---

## 5. Worktree integrity

Before migration:

```text
git rev-parse --abbrev-ref HEAD
git rev-parse HEAD
git status --short
git diff --check
python -m alembic heads
```

Expected:

```text
branch = vnext/stage8-mag7-observation
HEAD = 3a63eaa1b9069d34199704fe31ac6466e8929d7d
repository alembic head = 20260818_0017
```

Application source must be unchanged from Stage 7 acceptance.

Only Stage 8 evidence artifacts may be uncommitted.

If application/migration files are dirty:

```text
RUNTIME_DEPLOYMENT_RESULT=HOLD_DIRTY_ACCEPTED_CODE
```

STOP.

Do not reset, clean, stash, or overwrite user files.

---

## 6. Remote preflight — read-only

Use the already-configured runtime PostgreSQL connection.

Never print:

```text
username
password
full credential-bearing URL
API key
Authorization header
```

First use read-only queries to reconfirm:

```text
REMOTE_DB_REACHABLE=YES
REMOTE_ALEMBIC_HEAD=20260815_0013
```

Inspect for out-of-band schema drift/collisions for every object the 0014–0017 migrations intend to create or alter.

At minimum confirm the four vNext tables remain absent before migration:

```text
product_candidates
product_candidate_triggers
product_candidate_contexts
anomaly_context_details
```

Also inspect all other migration-target columns/tables/indexes/constraints discovered in Section 4.

If any target object is partially present in a way Alembic does not expect:

```text
RUNTIME_DEPLOYMENT_RESULT=HOLD_SCHEMA_DRIFT
```

STOP.

Do not stamp over drift.

Do not manually create missing objects.

---

## 7. Pre-migration preservation evidence

Because these migrations are approved additive migrations with no application-data backfill, collect read-only before-state evidence for every existing table altered by 0014–0017.

At minimum record:

```text
table row count
relevant pre-existing column null/non-null counts where applicable
```

For `scan_runs`, record enough read-only evidence to prove old rows do not already carry Stage 5 materialization markers.

Do not dump sensitive row contents.

If available without exposing secrets, generate a schema-only metadata snapshot or equivalent object inventory. This is optional and must not block execution if the local client does not support it.

---

## 8. Offline SQL verification

Before remote write, generate the PostgreSQL offline upgrade SQL for:

```text
20260815_0013 → 20260818_0017
```

Verify:

```text
OFFLINE_UPGRADE_SQL_GENERATED=YES
UNEXPECTED_APPLICATION_DML_FOUND=NO
UNEXPECTED_DESTRUCTIVE_DDL_FOUND=NO
```

Alembic version-table DML is migration bookkeeping and is allowed.

If unexpected DML/DDL appears, STOP.

---

## 9. Authorized remote migration

Only after all preflight gates pass, this package explicitly authorizes:

```text
alembic upgrade 20260818_0017
```

against the already-configured runtime database.

This is the only authorized remote write.

Do not run:

```text
alembic downgrade
alembic stamp
manual CREATE/ALTER
manual UPDATE/INSERT/DELETE
historical backfill
data repair
```

Do not run a scanner.

Do not call Nightwatch.

Do not trigger workflows.

If Alembic fails:

```text
RUNTIME_DEPLOYMENT_RESULT=FAIL_MIGRATION
```

Capture the sanitized error and STOP.

Do not improvise a manual fix.

---

## 10. Post-migration verification

After successful migration, verify read-only:

```text
REMOTE_ALEMBIC_HEAD=20260818_0017
ALEMBIC_SINGLE_HEAD=YES
```

Required tables:

```text
product_candidates
product_candidate_triggers
product_candidate_contexts
anomaly_context_details
```

must exist.

Verify migration/model-relevant columns, indexes, unique/check constraints and FKs expected by 0014–0017.

Return:

```text
PRODUCT_CANDIDATE_TABLE_PRESENT=YES
PRODUCT_CANDIDATE_TRIGGER_TABLE_PRESENT=YES
PRODUCT_CANDIDATE_CONTEXT_TABLE_PRESENT=YES
ANOMALY_CONTEXT_DETAIL_TABLE_PRESENT=YES
```

---

## 11. Historical preservation verification

Because Stage 5/6 are prospective:

```text
existing historical scans must NOT be converted into ProductCandidates
existing historical Phase2B rows must NOT be converted into vNext context rows
```

Immediately after migration, before any new scanner run, verify:

```text
PRODUCT_CANDIDATE_ROW_COUNT=
PRODUCT_CANDIDATE_TRIGGER_ROW_COUNT=
PRODUCT_CANDIDATE_CONTEXT_ROW_COUNT=
ANOMALY_CONTEXT_DETAIL_ROW_COUNT=
```

Expected for a runtime that previously lacked these tables:

```text
0
0
0
0
```

unless a separately authorized process legitimately wrote them after the migration completed.

Also compare pre/post row counts of existing tables altered by the migrations.

Expected:

```text
APPLICATION_ROW_COUNT_CHANGED_BY_MIGRATION=NO
HISTORICAL_PRODUCT_CANDIDATE_BACKFILL_FOUND=NO
HISTORICAL_CONTEXT_BACKFILL_FOUND=NO
```

For Stage 5 nullable occurrence markers on old `scan_runs`, verify old rows remain unmaterialized/null unless the accepted migration explicitly defines another safe value.

---

## 12. Runtime smoke — schema only

Perform only schema/read-model smoke checks that do not create application data.

Allowed:

```text
SELECT metadata
SELECT empty new tables
ORM/import/model initialization
read-only API repository calls if they perform zero writes and zero vendor calls
```

Not allowed:

```text
MAG7 scan
candidate materialization
baseline POST
context refresh
Nightwatch request
```

This gate proves deployment only.

---

## 13. Carried items

Do NOT incorrectly close:

```text
CURRENT_TRIGGER_FRESHNESS_MODE=CALIBRATION_REQUIRED
RADAR_OI_SCHEDULE_ACTIVATION=PENDING_ROLLOVER_EVIDENCE
CROSS_RUN_CANDIDATE_LIFECYCLE=DEFERRED_NO_AUTO_MERGE
IV_RANK_CORE_ELIGIBILITY=WITHHOLD_PENDING_PROVENANCE
N1_HISTORICAL_RUNTIME_DISTRIBUTION_VERIFIED=NO
```

`ISOLATED_POSTGRES_RUNTIME_VERIFIED` also remains:

```text
NO
```

unless this exact task separately used an isolated PostgreSQL runtime. The remote Supabase migration does not satisfy the isolated-PG carried gate.

---

## 14. Evidence output

Create:

```text
F:\options-anomaly-scanner-stage8\docs\evidence\stage8\NIGHTWATCH_VNEXT_STAGE8_RUNTIME_DEPLOYMENT_GATE_REPORT_20260820.md
```

Do not modify the original Stage 8 observation report.

---

## 15. Final result

Return exactly one:

```text
RUNTIME_DEPLOYMENT_RESULT=PASS
RUNTIME_DEPLOYMENT_RESULT=HOLD_ALEMBIC_CHAIN_MISMATCH
RUNTIME_DEPLOYMENT_RESULT=HOLD_MIGRATION_SEMANTIC_CONFLICT
RUNTIME_DEPLOYMENT_RESULT=HOLD_DIRTY_ACCEPTED_CODE
RUNTIME_DEPLOYMENT_RESULT=HOLD_SCHEMA_DRIFT
RUNTIME_DEPLOYMENT_RESULT=FAIL_MIGRATION
```

If PASS, return:

```text
REMOTE_ALEMBIC_HEAD_BEFORE=20260815_0013
REMOTE_ALEMBIC_HEAD_AFTER=20260818_0017

MIGRATIONS_APPLIED=[
  20260817_0014,
  20260818_0015,
  20260818_0016,
  20260818_0017
]

STAGE8_RUNTIME_SCHEMA_READY=YES
STAGE8_OBSERVATION_RESUME_READY=YES
```

Then:

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

STAGE9_READY=NO
NEXT_AUTHORIZED_STAGE=NONE
```

Do not resume Stage 8 observation automatically.

Do not run MAG7 automatically.

STOP.

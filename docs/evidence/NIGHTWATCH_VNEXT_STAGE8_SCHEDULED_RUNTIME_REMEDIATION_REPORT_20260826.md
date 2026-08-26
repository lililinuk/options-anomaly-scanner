# Nightwatch vNext — Stage 8 Scheduled Runtime Remediation Report

**Date:** 2026-08-26  
**Founder authorization:** `STAGE8_SCHEDULED_RUNTIME_REMEDIATION_20260826`  
**Execution package SHA-256:** `3DC3852CB0538B92CC30827DA025C9456A5117B23F21D9715A891EA2AACA6BDE`

## Executive result

```text
REMEDIATION_RESULT=PASS_DEPLOYED_WAITING_NATURAL_RUNTIME_PROOF
FOUNDER_AUTHORIZATION=STAGE8_SCHEDULED_RUNTIME_REMEDIATION_20260826

REMOTE_MAIN_BEFORE=55e9f96483c7edb897ff1829b63cbe84eac179a2
REMEDIATION_BRANCH=fix/stage8-scheduled-runtime-remediation
REMEDIATION_BASE=55e9f96483c7edb897ff1829b63cbe84eac179a2
REMEDIATION_COMMIT=ca4ac6c2da7c628c1749fc5cc0643bbe69980c6e
REMOTE_MAIN_AFTER=ca4ac6c2da7c628c1749fc5cc0643bbe69980c6e
```

The narrow remediation was implemented from the latest authoritative `origin/main`, verified locally with zero paid/runtime calls, committed once, and pushed normally to GitHub `main` without force. GitHub reports the Phase 2A workflow as active. The next natural schedule—not this task—must provide runtime re-proof.

## Package and repository gates

- Attached execution package was preserved byte-for-byte in canonical evidence.
- Download and canonical package SHA-256: `3DC3852CB0538B92CC30827DA025C9456A5117B23F21D9715A891EA2AACA6BDE`.
- Clean remediation worktree: `F:\options-anomaly-scanner-stage8-runtime-remediation`.
- Existing Stage 8 worktree was not reset, stashed, discarded, or edited.
- Latest remote main before work: `55e9f96483c7edb897ff1829b63cbe84eac179a2`.
- Required vNext runtime prerequisites and Alembic head `20260818_0017` were present.
- Existing schema can truthfully encode both chain-404 classes using `ExpiryOiDailySnapshot.chain_status` and structured `DailyOiArchiveTicker.details`; no schema semantic gap or migration was required.

## Authorized files

```text
AUTHORIZED_FILES_PROPOSED:
- backend/app/scanner/archive.py: classify expiry-chain 404s, preserve a single ticker lifecycle row, and recover failed transactions without masking the original error.
- backend/app/scanner/daily.py: rollback the shared session before subsequent subjobs and preserve child usage counters in the parent result.
- backend/app/cli.py: return non-zero for FAILED/PARTIAL collection summaries.
- backend/tests/test_stage4a_daily_pipeline.py: deterministic archive, transaction, counter, and non-cascade regressions.
- backend/tests/test_stage8_daily_automation_workflow.py: CLI exit and scheduler-skip regressions plus workflow invariants.
```

No file outside this list changed in the remediation commit.

## Implementation

### 1. Chain 404 semantics and ticker lifecycle

The chain request is now handled inside the per-expiry loop.

For an already-expired expiry returning HTTP 404:

- the expiry OI surface row remains preserved;
- `chain_status=EXPIRED_CHAIN_UNAVAILABLE`;
- ticker details record `classification=EXPIRED_EXPIRY_CHAIN_404`;
- no contract row or OI zero is fabricated;
- no closure is inferred;
- processing continues to remaining expiries;
- the expired 404 alone does not make otherwise complete active-chain coverage ineligible.

For an active/same-day/future expiry returning HTTP 404:

- the expiry OI surface row remains preserved;
- `chain_status=ACTIVE_CHAIN_UNAVAILABLE`;
- ticker details record `classification=ACTIVE_EXPIRY_CHAIN_404`;
- `blocks_active_coverage=true`;
- ticker status remains `PARTIAL_INCOMPLETE_CHAIN`;
- no zero or contract closure is fabricated.

The fallback ticker-level vendor-error path now rolls back first, reuses the already-persisted `archive_run_id+ticker` row when present, and inserts only when no lifecycle row exists. This removes the duplicate unique-key failure.

### 2. Transaction recovery and error truth

On an archive failure:

- the SQLAlchemy session is rolled back before final failure persistence;
- the durable archive run is reloaded and finalized safely;
- a failed finalization attempt is rolled back;
- cleanup failure does not replace an already-active original failure;
- the original exception is re-raised.

The daily parent also explicitly rolls back after a child archive exception before Radar uses the shared session. Radar therefore receives a reusable session instead of a poisoned transaction.

### 3. Usage counters

The daily parent retains the child archiver object and copies its observed `budget.consumed` and `budget.attempts` even when the child raises. The failed subjob detail also persists those observed counters. This prevents the confirmed false `0/0` summary when authoritative child observations show nonzero use.

### 4. CLI exit semantics

`archive-mag7-daily` now returns:

```text
COMPLETE -> 0
NO_NEW_DATA -> 0
FAILED -> 6
PARTIAL -> 6
legitimate pre-run scheduler skip -> 0
```

The workflow needs no shell workaround: a blocking archive result now naturally makes the GitHub step red. Existing non-trading/session-window skip handling remains green.

## Required focused-case evidence

| Case | Result |
|---|---|
| OI surface 200 + expired chain 404 + active chains 200 | PASS; expired OI preserved, later active chain completed |
| OI surface 200 + active chain 404 | PASS; active evidence remains fail-closed |
| Vendor error does not duplicate ticker lifecycle row | PASS; exactly one ticker row in both 404 branches |
| Transaction rollback leaves session reusable | PASS |
| Radar not cascade-failed by poisoned session | PASS |
| Original failure not masked by PendingRollbackError | PASS; same exception object re-raised |
| Parent counters truthful on handled failure | PASS; mocked authoritative 1 paid / 2 attempts retained |
| FAILED summary -> non-zero CLI | PASS; exit 6 |
| PARTIAL summary -> non-zero CLI | PASS; exit 6 |
| Legitimate scheduler skip -> zero CLI | PASS |
| Evening readiness blocks missing active evidence | PASS; active 404 remains partial and full existing suite passed |
| No automatic paid retry | PASS; `max_retries=0` and workflow static checks preserved |

## Verification

```text
FOCUSED_TESTS=PASS (22)
STAGE4B_STAGE5_STAGE6_STAGE7_REGRESSIONS=PASS (64)
FULL_BACKEND_TESTS=PASS (406)
RUFF=PASS
ALEMBIC_HEAD=20260818_0017
ALEMBIC_SINGLE_HEAD=YES
GIT_DIFF_CHECK=PASS
SECRET_SCAN=PASS (0 findings)
WORKFLOW_STATIC_VALIDATION=PASS
AUTHORIZED_FILE_SCOPE=PASS (5 expected, 0 unexpected)
ALL_TESTS_PASS=YES
```

Frontend lint/build was not applicable: no frontend file or frontend runtime behavior changed. The complete backend and workflow-static matrices required by the execution package were run.

## Pre-deployment acceptance

```text
DUPLICATE_TICKER_INSERT_FIXED=YES
TRANSACTION_RECOVERY_FIXED=YES
PENDING_ROLLBACK_MASKING_FIXED=YES

EXPIRED_CHAIN_404_CLASSIFICATION_IMPLEMENTED=YES
ACTIVE_CHAIN_404_CLASSIFICATION_IMPLEMENTED=YES
EXPIRED_404_FABRICATES_ZERO=NO
ACTIVE_404_FABRICATES_ZERO=NO

EXPIRED_404_BLOCKS_OTHER_EXPIRIES=NO
ACTIVE_404_FALSELY_MARKS_COMPLETE=NO

PARENT_COUNTER_TRUTHFULNESS_FIXED=YES
CLI_FALSE_GREEN_FIXED=YES

MIGRATION_REQUIRED=NO
HISTORICAL_REPAIR_PERFORMED=NO

ALL_TESTS_PASS=YES
```

## GitHub deployment and activation verification

A single commit was created:

```text
ca4ac6c2da7c628c1749fc5cc0643bbe69980c6e
fix: repair stage8 scheduled runtime failures
```

Immediately before push, `origin/main` remained at the remediation base with ahead/behind `0/0`. A normal non-force `HEAD:main` push advanced main to the remediation commit.

Read-only GitHub verification returned:

```text
workflow_id=341934128
workflow_name=Phase 2A Daily Archive and vNext Observation
workflow_path=.github/workflows/phase2a-daily-archive.yml
workflow_state=active
origin/main_contains_remediation_commit=YES
06:30_America/New_York_schedule_count=1
16:30_America/New_York_schedule_count=1
America/New_York_timezone_count=2
workflow_files_changed_by_remediation=0
```

Dealer/GEX and rollover workflows were preserved because no workflow file changed. No workflow was manually dispatched and the failed historical runtime was not rerun or repaired.

## External contact ledger

Only GitHub was contacted:

- `https://github.com/lililinuk/options-anomaly-scanner.git` — Git fetch and one normal push.
- `https://api.github.com/repos/lililinuk/options-anomaly-scanner/actions/workflows/phase2a-daily-archive.yml` — read-only active-workflow verification.

No Nightwatch endpoint, Supabase/PostgreSQL endpoint, or other external API was contacted.

## Required final fields

```text
REMEDIATION_RESULT=PASS_DEPLOYED_WAITING_NATURAL_RUNTIME_PROOF
FOUNDER_AUTHORIZATION=STAGE8_SCHEDULED_RUNTIME_REMEDIATION_20260826

REMOTE_MAIN_BEFORE=55e9f96483c7edb897ff1829b63cbe84eac179a2
REMEDIATION_BRANCH=fix/stage8-scheduled-runtime-remediation
REMEDIATION_BASE=55e9f96483c7edb897ff1829b63cbe84eac179a2
REMEDIATION_COMMIT=ca4ac6c2da7c628c1749fc5cc0643bbe69980c6e
REMOTE_MAIN_AFTER=ca4ac6c2da7c628c1749fc5cc0643bbe69980c6e

DUPLICATE_TICKER_INSERT_FIXED=YES
TRANSACTION_RECOVERY_FIXED=YES
PENDING_ROLLBACK_MASKING_FIXED=YES

EXPIRED_CHAIN_404_CLASSIFICATION_IMPLEMENTED=YES
EXPIRED_CHAIN_404_PERSISTED_SEMANTICS=ExpiryOiDailySnapshot.chain_status:EXPIRED_CHAIN_UNAVAILABLE; DailyOiArchiveTicker.details.classification:EXPIRED_EXPIRY_CHAIN_404; expired-only gap does not block otherwise complete active coverage
ACTIVE_CHAIN_404_CLASSIFICATION_IMPLEMENTED=YES
ACTIVE_CHAIN_404_PERSISTED_SEMANTICS=ExpiryOiDailySnapshot.chain_status:ACTIVE_CHAIN_UNAVAILABLE; DailyOiArchiveTicker.status:PARTIAL_INCOMPLETE_CHAIN; DailyOiArchiveTicker.details.blocks_active_coverage:true

EXPIRED_404_FABRICATES_ZERO=NO
ACTIVE_404_FABRICATES_ZERO=NO
EXPIRED_404_BLOCKS_OTHER_EXPIRIES=NO
ACTIVE_404_FALSELY_MARKS_COMPLETE=NO

PARENT_COUNTER_TRUTHFULNESS_FIXED=YES

CLI_FALSE_GREEN_FIXED=YES
FAILED_EXIT_CODE=6
PARTIAL_EXIT_CODE=6
LEGITIMATE_SKIP_EXIT_CODE=0

EVENING_READINESS_GATE_WEAKENED=NO
ACTIVE_MISSING_EVIDENCE_FAIL_CLOSED=YES

MIGRATION_REQUIRED=NO
HISTORICAL_REPAIR_PERFORMED=NO

APPLICATION_FILES_CHANGED=3
TEST_FILES_CHANGED=2
WORKFLOW_FILES_CHANGED=0
SCHEMA_FILES_CHANGED=0

FOCUSED_TESTS=PASS (22)
FULL_BACKEND_TESTS=PASS (406)
RUFF=PASS
ALEMBIC_HEAD=20260818_0017
ALEMBIC_SINGLE_HEAD=YES
GIT_DIFF_CHECK=PASS
SECRET_SCAN=PASS
ALL_TESTS_PASS=YES

NIGHTWATCH_REQUESTS_THIS_TASK=0
PAID_UNITS_THIS_TASK=0
WORKFLOW_DISPATCHES_THIS_TASK=0
REMOTE_APPLICATION_DATA_WRITES_THIS_TASK=0
REMOTE_SCHEMA_WRITES_THIS_TASK=0

COMMITS_CREATED=1
PUSHES=1
PRS_CREATED=0
MERGES=0

PHASE2A_DAILY_WORKFLOW_ACTIVE_ON_DEFAULT=YES
RADAR_OI_SCHEDULE_UNCHANGED=YES
ACTIVITY_OBSERVATION_SCHEDULE_UNCHANGED=YES

FIRST_SCHEDULED_RUNTIME_REPROOF_COMPLETE=NO

PRIMARY_REPORT_PATH=F:\options-anomaly-scanner-stage8-runtime-remediation\docs\evidence\stage8\NIGHTWATCH_VNEXT_STAGE8_SCHEDULED_RUNTIME_REMEDIATION_REPORT_20260826.md
CANONICAL_REPORT_PATH=F:\options-anomaly-scanner\docs\evidence\NIGHTWATCH_VNEXT_STAGE8_SCHEDULED_RUNTIME_REMEDIATION_REPORT_20260826.md
PRIMARY_REPORT_SHA256=FILLED_AFTER_BYTE_IDENTICAL_COPY
CANONICAL_REPORT_SHA256=FILLED_AFTER_BYTE_IDENTICAL_COPY
REPORT_BACKUP_BYTE_IDENTICAL=FILLED_AFTER_BYTE_IDENTICAL_COPY

STAGE8_STATUS=CONTINUE_OBSERVATION
STAGE9_STATUS=DESIGN_GATE_SEPARATE
NEXT_AUTHORIZED_STAGE=NONE
```

The two report hashes and byte-identity result are computed after writing this content and are returned in the task response. They cannot be embedded into the report itself without changing the report hash.

## Stop conditions preserved

```text
FIRST_SCHEDULED_RUNTIME_REPROOF_COMPLETE=NO
MANUAL_WORKFLOW_RERUN=NO
WORKFLOW_DISPATCHES_THIS_TASK=0
NIGHTWATCH_REQUESTS_THIS_TASK=0
PAID_UNITS_THIS_TASK=0
REMOTE_APPLICATION_DATA_WRITES_THIS_TASK=0
REMOTE_SCHEMA_WRITES_THIS_TASK=0
NEXT_AUTHORIZED_STAGE=NONE
```

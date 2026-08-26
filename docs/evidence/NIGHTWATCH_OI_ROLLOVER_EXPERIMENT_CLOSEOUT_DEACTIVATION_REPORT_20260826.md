# Nightwatch — OI Rollover Experiment Closeout & Scheduled Deactivation Report

**Date:** 2026-08-26  
**Founder authorization:** `OI_ROLLOVER_EXPERIMENT_CLOSEOUT_DEACTIVATION_20260826`  
**Execution package SHA-256:** `AFDAA611401F19D27065725F532AEC3CD1C3C255A908AF551A13103034ADA6B9`

## Executive result

```text
ROLLOVER_CLOSEOUT_RESULT=PASS_CLOSED_AND_SCHEDULE_DEACTIVATED
FOUNDER_AUTHORIZATION=OI_ROLLOVER_EXPERIMENT_CLOSEOUT_DEACTIVATION_20260826

REMOTE_MAIN_BEFORE=ca4ac6c2da7c628c1749fc5cc0643bbe69980c6e
REMOTE_MAIN_AFTER=988533dfbe7bcf53749bdc379be81e18893033b7
CLOSEOUT_COMMIT=988533dfbe7bcf53749bdc379be81e18893033b7
DEPLOYMENT_PATH=DIRECT_DEFAULT_PUSH
```

The completed August 2026 rollover-timing experiment is formally closed. Its accepted timing conclusion is frozen, the automatic GitHub schedule has been removed, and the existing manual `workflow_dispatch` capability remains available for a separately authorized drift investigation. No workflow was dispatched during this task.

Production Phase 2A and Dealer/GEX automation were not modified.

## Package custody and governing evidence

The attached execution package was copied byte-for-byte to:

`F:\options-anomaly-scanner\docs\evidence\NIGHTWATCH_OI_ROLLOVER_EXPERIMENT_CLOSEOUT_DEACTIVATION_EXECUTION_PACKAGE_20260826.md`

```text
SOURCE_PACKAGE_SHA256=AFDAA611401F19D27065725F532AEC3CD1C3C255A908AF551A13103034ADA6B9
CANONICAL_PACKAGE_SHA256=AFDAA611401F19D27065725F532AEC3CD1C3C255A908AF551A13103034ADA6B9
PACKAGE_BYTE_IDENTICAL=YES
PACKAGE_CONFLICT=NO
```

All mandatory canonical evidence was read completely:

- Nightwatch vNext canonical evidence manifest;
- founder-approved integrated specification;
- Stage 4A daily-pipeline execution package;
- Stage 8 daily-automation deployment-gate report;
- Stage 8 daily-automation GitHub deployment report;
- Stage 8 scheduled-runtime remediation report;
- this closeout execution package.

No governing evidence was reconstructed from memory and no paid/vendor call was used to reconfirm timing.

## Repository orientation and isolation

The canonical worktree at `F:\options-anomaly-scanner` remains an older Stage 3 checkpoint with extensive pre-existing evidence files. It was not reset, stashed, cleaned, or used to construct the deployment commit.

A clean linked worktree was created from the fetched authoritative `origin/main`:

```text
CLOSEOUT_WORKTREE=F:\options-anomaly-scanner-rollover-closeout
CLOSEOUT_BRANCH=ops/oi-rollover-experiment-closeout
LOCAL_MAIN_BEFORE=ca4ac6c2da7c628c1749fc5cc0643bbe69980c6e
REMOTE_MAIN_BEFORE=ca4ac6c2da7c628c1749fc5cc0643bbe69980c6e
WORKTREE_STATUS=CLEAN_AT_START
```

Immediately before commit/deployment, a second fetch confirmed ahead/behind `0/0`; remote main had not moved.

## Frozen experiment conclusion

### Purpose and evidence range

The experiment measured when the Nightwatch OI-change source first exposed the expected previous completed XNYS-session date, and when it later switched to a later/ahead vendor date. Its purpose was to choose a production Radar/OI collection time from observed evidence rather than inventing a cron.

Accepted evidence:

```text
DATE_RANGE_OF_SCHEDULED_RUNS=2026-08-18 through 2026-08-24
ACCEPTED_SUCCESSFUL_SCHEDULED_RUNS=50
ACCEPTED_PROBE_RECORDS=150
TICKERS=AAPL,NVDA,TSLA
ACCEPTED_XNYS_DATES=2026-08-17,2026-08-18,2026-08-19,2026-08-20,2026-08-21
ALL_TICKER_AGREEMENT=YES
SUCCESSFUL_RESPONSE_STATUS=HTTP 200
RETRY_CONTRADICTIONS=0
CONTRADICTIONS_FOUND=0
```

Observed timing:

| Expected completed XNYS date | Earliest all-ticker expected date | Last expected date | First later/ahead vendor date |
|---|---:|---:|---:|
| 2026-08-17 | 05:25:26 ET | 08:30:22 ET | 09:37:09 ET |
| 2026-08-18 | 05:26:34 ET | 09:38:45 ET | 10:02:04 ET |
| 2026-08-19 | 05:26:21 ET | 09:40:31 ET | 10:04:52 ET |
| 2026-08-20 | 05:29:16 ET | 08:32:19 ET | 09:39:34 ET |
| 2026-08-21 | 05:39:39 ET | 08:34:06 ET | 09:44:26 ET |

```text
EARLIEST_EXPECTED_DATE_AVAILABILITY=05:25:26 America/New_York
LATEST_FIRST_EXPECTED_DATE_AVAILABILITY=05:39:39 America/New_York
EARLIEST_OBSERVED_VENDOR_SWITCH=09:37:09 America/New_York

ROLLOVER_TIMING_GATE=PASS_WITH_CONSERVATIVE_SAFE_WINDOW
FROZEN_SAFE_WINDOW=06:00-08:00 America/New_York
FROZEN_PRODUCTION_CRON=06:30 America/New_York
```

The 06:30 production collection sits after the latest observed first availability and well before the earliest observed switch. The Monday observation correctly used Friday as the previous completed XNYS session.

### Closeout conclusion

```text
EXPERIMENT_PURPOSE_FULFILLED=YES
PRODUCTION_TIMING_CONCLUSION_FROZEN=YES
FURTHER_AUTOMATIC_PROBING_REQUIRED=NO
```

Reason for closeout: the planned experiment completed with sufficient repeated, all-ticker, calendar-correct evidence to support the conservative 06:00–08:00 ET window and the already-deployed 06:30 ET production cron. Continuing automatic probes would no longer serve the experiment's accepted purpose.

This is not a claim that vendor publication timing can never change. Current production timing is supported by the completed 2026-08 experiment; future material vendor-timing drift may justify a separately authorized re-open.

## Pre-change GitHub state

Read-only GitHub metadata before the edit:

```text
ROLLOVER_WORKFLOW_PATH=.github/workflows/oi-change-rollover-timing-experiment.yml
ROLLOVER_WORKFLOW_GITHUB_STATE=active
ROLLOVER_WORKFLOW_ID=335910966
ROLLOVER_SCHEDULE_TRIGGER_PRESENT_BEFORE=YES
ROLLOVER_WORKFLOW_DISPATCH_PRESENT_BEFORE=YES
ROLLOVER_LIVE_MANUAL_MODE_PRESENT=YES_EXISTING_EXPLICIT_SELECTION_REQUIRED
ROLLOVER_RUNS_CURRENTLY_QUEUED=0
ROLLOVER_RUNS_CURRENTLY_IN_PROGRESS=0

PHASE2A_DAILY_WORKFLOW_ID=341934128
PHASE2A_DAILY_WORKFLOW_STATE=active
DEALER_GEX_WORKFLOW_ID=334406303
DEALER_GEX_WORKFLOW_STATE=active
```

No queued or in-progress run was cancelled or mutated.

## Deactivation implementation

The automatic `schedule` block and its six cron entries were removed from:

`F:\options-anomaly-scanner-rollover-closeout\.github\workflows\oi-change-rollover-timing-experiment.yml`

Preserved without weakening:

- `workflow_dispatch`;
- required manual `mode` choice;
- default `dry_run`;
- existing explicit `live` option;
- hard date guard;
- secret handling;
- isolated no-database research behavior;
- artifact aggregation and secret-safety check;
- concurrency with `cancel-in-progress: false`.

The workflow was not deleted.

The repository contained a regression that explicitly required the retired August cron list. That single test was updated to assert the accepted closed state: no `schedule` or `cron`, manual dispatch present, `dry_run` default preserved, and existing explicit `live` selection preserved.

```text
WORKFLOW_FILES_CHANGED=1
TEST_FILES_CHANGED=1
APPLICATION_CODE_CHANGES=0
MIGRATION_CHANGES=0
SCANNER_LOGIC_CHANGED=NO
```

## Production automation integrity

Pre-task and post-change Git blob identities:

```text
PHASE2A_WORKFLOW_BLOB_BEFORE=5bad7bce5f6ed07f396933e0b2af5a888b86bec2
PHASE2A_WORKFLOW_BLOB_AFTER=5bad7bce5f6ed07f396933e0b2af5a888b86bec2
DEALER_GEX_WORKFLOW_BLOB_BEFORE=0135d050349e99a1251a972ae5b05d357a8969b5
DEALER_GEX_WORKFLOW_BLOB_AFTER=0135d050349e99a1251a972ae5b05d357a8969b5
```

```text
PHASE2A_WORKFLOW_CHANGED=NO
DEALER_GEX_WORKFLOW_CHANGED=NO
PRODUCTION_RADAR_TIMING_CHANGED=NO

RADAR_OI_PRODUCTION_SCHEDULE=06:30 America/New_York
ACTIVITY_OBSERVATION_SCHEDULE=16:30 America/New_York
DEALER_GEX_PRODUCTION_SCHEDULE=15:30 America/New_York
```

## Verification

All checks were local/offline:

```text
FOCUSED_ROLLOVER_AND_PRODUCTION_WORKFLOW_TESTS=PASS (34)
RUFF=PASS
YAML_PARSE=PASS
ROLLOVER_TRIGGER_KEYS=workflow_dispatch only
ROLLOVER_SCHEDULE_BLOCK_PRESENT=NO
ROLLOVER_CRON_PRESENT=NO
ROLLOVER_WORKFLOW_DISPATCH_PRESENT=YES
ROLLOVER_DRY_RUN_DEFAULT_PRESENT=YES
ROLLOVER_EXISTING_LIVE_OPTION_PRESENT=YES
PRODUCTION_WORKFLOW_BYTE_IDENTITY=PASS
GIT_DIFF_CHECK=PASS
SECRET_SCAN=PASS (0 findings)
AUTHORIZED_SCOPE_CHECK=PASS (1 workflow + 1 directly coupled regression)
ACTIONLINT=UNAVAILABLE; PyYAML parse and repository workflow tests passed
STATIC_VALIDATION_PASS=YES
```

No application/backend suite was required because application code did not change. The focused test set included the rollover research/workflow suite and the Phase 2A, Stage 8 automation, and Dealer/GEX workflow regressions.

## Commit and deployment

```text
CLOSEOUT_COMMIT=988533dfbe7bcf53749bdc379be81e18893033b7
COMMIT_SUBJECT=ops: close rollover timing experiment schedule
DEPLOYMENT_PATH=DIRECT_DEFAULT_PUSH
FORCE_PUSH=NO
REMOTE_MAIN_AFTER=988533dfbe7bcf53749bdc379be81e18893033b7
```

One normal direct `HEAD:main` push advanced GitHub main. No PR or merge commit was required.

## Post-deployment GitHub verification

GitHub still recognizes all three workflow files:

```text
ROLLOVER_WORKFLOW_EXISTS=YES
ROLLOVER_WORKFLOW_RECOGNIZED=YES
ROLLOVER_WORKFLOW_GITHUB_STATE=active
ROLLOVER_SCHEDULE_TRIGGER_PRESENT_AFTER=NO
ROLLOVER_CRON_PRESENT_AFTER=NO
ROLLOVER_WORKFLOW_DISPATCH_PRESENT_AFTER=YES
ROLLOVER_DRY_RUN_DEFAULT_PRESENT_AFTER=YES
ROLLOVER_EXISTING_LIVE_OPTION_PRESENT_AFTER=YES

ROLLOVER_AUTOMATIC_SCHEDULE_ACTIVE=NO
ROLLOVER_MANUAL_REOPEN_CAPABILITY=YES

PHASE2A_DAILY_WORKFLOW_ACTIVE=YES
DEALER_GEX_WORKFLOW_ACTIVE=YES
PHASE2A_06_30_SCHEDULE_COUNT=1
PHASE2A_16_30_SCHEDULE_COUNT=1
DEALER_GEX_15_30_SCHEDULE_COUNT=1

ROLLOVER_RUNS_CURRENTLY_QUEUED=0
ROLLOVER_RUNS_CURRENTLY_IN_PROGRESS=0
```

The workflow metadata state remains `active` because the manual workflow itself remains valid and recognized. “Automatic schedule active” is independently `NO` because the remote YAML has neither `schedule` nor `cron`.

## Cost effect

```text
FUTURE_AUTOMATIC_ROLLOVER_NIGHTWATCH_CALLS=0
FUTURE_AUTOMATIC_ROLLOVER_PAID_UNITS=0
CONDITION=no future manual dispatch
```

This closeout does not alter ordinary Phase 2A, MAG7, or Dealer/GEX production costs.

## Re-open policy

The experiment must not automatically re-enable itself.

```text
ROLLOVER_REOPEN_POLICY=SEPARATE_FOUNDER_AUTHORIZATION_REQUIRED
```

A future re-open requires separate Founder authorization and at least one of:

- production Radar/OI repeatedly fails expected-date readiness;
- vendor timing materially shifts;
- vendor/API behavior changes;
- new evidence contradicts the 06:00–08:00 ET safe window.

## External contact ledger

Only GitHub was contacted:

- `https://github.com/lililinuk/options-anomaly-scanner.git` — fetch and one normal push.
- `https://api.github.com/repos/lililinuk/options-anomaly-scanner/actions/workflows/oi-change-rollover-timing-experiment.yml` — rollover metadata and workflow id.
- `https://api.github.com/repos/lililinuk/options-anomaly-scanner/actions/workflows/335910966/runs?status=queued&per_page=100` — read-only queued runs.
- `https://api.github.com/repos/lililinuk/options-anomaly-scanner/actions/workflows/335910966/runs?status=in_progress&per_page=100` — read-only in-progress runs.
- `https://api.github.com/repos/lililinuk/options-anomaly-scanner/actions/workflows/phase2a-daily-archive.yml` — Phase 2A metadata.
- `https://api.github.com/repos/lililinuk/options-anomaly-scanner/actions/workflows/dealer-gex-archive.yml` — Dealer/GEX metadata.
- `https://api.github.com/repos/lililinuk/options-anomaly-scanner/contents/.github/workflows/oi-change-rollover-timing-experiment.yml?ref=main` — remote trigger verification.
- `https://api.github.com/repos/lililinuk/options-anomaly-scanner/contents/.github/workflows/phase2a-daily-archive.yml?ref=main` — production schedule verification.
- `https://api.github.com/repos/lililinuk/options-anomaly-scanner/contents/.github/workflows/dealer-gex-archive.yml?ref=main` — production schedule verification.

No Nightwatch, Supabase/PostgreSQL, package registry, or workflow-dispatch endpoint was contacted.

## Required final fields

```text
ROLLOVER_CLOSEOUT_RESULT=PASS_CLOSED_AND_SCHEDULE_DEACTIVATED
FOUNDER_AUTHORIZATION=OI_ROLLOVER_EXPERIMENT_CLOSEOUT_DEACTIVATION_20260826

REMOTE_MAIN_BEFORE=ca4ac6c2da7c628c1749fc5cc0643bbe69980c6e
REMOTE_MAIN_AFTER=988533dfbe7bcf53749bdc379be81e18893033b7
CLOSEOUT_COMMIT=988533dfbe7bcf53749bdc379be81e18893033b7
DEPLOYMENT_PATH=DIRECT_DEFAULT_PUSH

ROLLOVER_WORKFLOW_PATH=.github/workflows/oi-change-rollover-timing-experiment.yml
ROLLOVER_WORKFLOW_GITHUB_STATE=active
ROLLOVER_SCHEDULE_TRIGGER_PRESENT_BEFORE=YES
ROLLOVER_SCHEDULE_TRIGGER_PRESENT_AFTER=NO
ROLLOVER_WORKFLOW_DISPATCH_PRESENT_AFTER=YES
ROLLOVER_LIVE_MANUAL_MODE_PRESENT=YES_EXISTING_EXPLICIT_SELECTION_REQUIRED

EXPERIMENT_PURPOSE_FULFILLED=YES
PRODUCTION_TIMING_CONCLUSION_FROZEN=YES
FURTHER_AUTOMATIC_PROBING_REQUIRED=NO

ACCEPTED_SUCCESSFUL_SCHEDULED_RUNS=50
ACCEPTED_PROBE_RECORDS=150
ACCEPTED_XNYS_DATES=2026-08-17,2026-08-18,2026-08-19,2026-08-20,2026-08-21
EARLIEST_EXPECTED_DATE_AVAILABILITY=05:25:26 America/New_York
LATEST_FIRST_EXPECTED_DATE_AVAILABILITY=05:39:39 America/New_York
EARLIEST_OBSERVED_VENDOR_SWITCH=09:37:09 America/New_York
FROZEN_SAFE_WINDOW=06:00-08:00 America/New_York
FROZEN_PRODUCTION_CRON=06:30 America/New_York

ROLLOVER_SCHEDULE_REMOVED=YES
ROLLOVER_MANUAL_DISPATCH_PRESERVED=YES
ROLLOVER_AUTOMATIC_SCHEDULE_ACTIVE=NO
ROLLOVER_MANUAL_REOPEN_CAPABILITY=YES

ROLLOVER_RUNS_CURRENTLY_QUEUED=0
ROLLOVER_RUNS_CURRENTLY_IN_PROGRESS=0

PHASE2A_WORKFLOW_CHANGED=NO
DEALER_GEX_WORKFLOW_CHANGED=NO
PRODUCTION_RADAR_TIMING_CHANGED=NO

PHASE2A_DAILY_WORKFLOW_ACTIVE=YES
DEALER_GEX_WORKFLOW_ACTIVE=YES

FUTURE_AUTOMATIC_ROLLOVER_NIGHTWATCH_CALLS=0
FUTURE_AUTOMATIC_ROLLOVER_PAID_UNITS=0

NIGHTWATCH_REQUESTS_THIS_TASK=0
PAID_UNITS_THIS_TASK=0
WORKFLOW_DISPATCHES_THIS_TASK=0
REMOTE_DB_WRITES_THIS_TASK=0
REMOTE_SCHEMA_WRITES_THIS_TASK=0

APPLICATION_CODE_CHANGES=0
MIGRATION_CHANGES=0
WORKFLOW_FILES_CHANGED=1
TEST_FILES_CHANGED=1
STATIC_VALIDATION_PASS=YES

COMMITS_CREATED=1
PUSHES=1
PRS_CREATED=0
MERGES=0

PRIMARY_REPORT_PATH=F:\options-anomaly-scanner\docs\evidence\stage8\NIGHTWATCH_OI_ROLLOVER_EXPERIMENT_CLOSEOUT_DEACTIVATION_REPORT_20260826.md
CANONICAL_REPORT_PATH=F:\options-anomaly-scanner\docs\evidence\NIGHTWATCH_OI_ROLLOVER_EXPERIMENT_CLOSEOUT_DEACTIVATION_REPORT_20260826.md
PRIMARY_REPORT_SHA256=COMPUTED_AFTER_FINAL_BYTES
CANONICAL_REPORT_SHA256=COMPUTED_AFTER_FINAL_BYTES
REPORT_BACKUP_BYTE_IDENTICAL=VERIFIED_AFTER_FINAL_BYTES

ROLLOVER_REOPEN_POLICY=SEPARATE_FOUNDER_AUTHORIZATION_REQUIRED

STAGE8_STATUS=CONTINUE_OBSERVATION
STAGE9_STATUS=DESIGN_GATE_SEPARATE
NEXT_AUTHORIZED_STAGE=NONE
```

The report hashes are computed after the report bytes are finalized and are returned with the task result. Embedding a file's final SHA-256 inside itself would change that SHA-256.

## Stop ledger

```text
WORKFLOW_DISPATCHES_THIS_TASK=0
NIGHTWATCH_REQUESTS_THIS_TASK=0
PAID_UNITS_THIS_TASK=0
REMOTE_DB_WRITES_THIS_TASK=0
REMOTE_SCHEMA_WRITES_THIS_TASK=0
SCANNER_LOGIC_CHANGED=NO
STAGE9_STARTED=NO
NEXT_AUTHORIZED_STAGE=NONE
```

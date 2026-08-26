# Nightwatch — OI Rollover Timing Experiment Closeout & Scheduled Deactivation — Execution Package

**Date:** 2026-08-26  
**Purpose:** Formally close the completed OI-change rollover timing experiment, freeze its accepted production timing conclusion, stop its automatic scheduled probes on GitHub, and preserve manual reactivation capability for future drift investigations.  
**Founder authorization:** `OI_ROLLOVER_EXPERIMENT_CLOSEOUT_DEACTIVATION_20260826`  
**Canonical repo:** `F:\options-anomaly-scanner`  
**Canonical evidence root:** `F:\options-anomaly-scanner\docs\evidence`  
**Target workflow:** `.github/workflows/oi-change-rollover-timing-experiment.yml`

---

# 0. Founder authorization

```text
FOUNDER_AUTHORIZATION=OI_ROLLOVER_EXPERIMENT_CLOSEOUT_DEACTIVATION_20260826

EXPERIMENT_CLOSEOUT_AUTHORIZED=YES
REMOVE_AUTOMATIC_SCHEDULE_AUTHORIZED=YES
PRESERVE_MANUAL_DISPATCH_AUTHORIZED=YES
GITHUB_COMMIT_PUSH_AUTHORIZED=YES

NIGHTWATCH_REQUEST_AUTHORIZED=NO
PAID_PROBE_AUTHORIZED=NO
WORKFLOW_MANUAL_DISPATCH_AUTHORIZED=NO
REMOTE_DB_WRITE_AUTHORIZED=NO
REMOTE_SCHEMA_WRITE_AUTHORIZED=NO
SCANNER_CHANGE_AUTHORIZED=NO
PRODUCTION_RADAR_SCHEDULE_CHANGE_AUTHORIZED=NO
DEALER_GEX_WORKFLOW_CHANGE_AUTHORIZED=NO
FORWARD_OUTCOME_AUTHORIZED=NO
```

The target state is:

```text
experiment research conclusion = frozen/closed
automatic rollover experiment cron = removed/deactivated
manual workflow_dispatch = preserved for future explicit drift investigation
production Phase 2A 06:30 ET schedule = unchanged
```

---

# 1. Accepted experiment conclusion to freeze

The Stage 8 daily automation gate already established:

```text
ROLLOVER_TIMING_GATE=PASS_WITH_CONSERVATIVE_SAFE_WINDOW

RADAR_OI_PRODUCTION_SAFE_WINDOW=06:00-08:00 America/New_York
RADAR_OI_PRODUCTION_SCHEDULE=06:30 America/New_York

EVIDENCE:
50 successful scheduled experiment runs
150 AAPL/NVDA/TSLA probe records
five expected XNYS completed-session dates
all-ticker agreement
HTTP 200 on successful scheduled probes
zero retry contradictions

earliest successful expected-date availability observed ≈ 05:25 ET
latest first expected-date availability observed ≈ 05:39 ET
earliest observed vendor switch to later/ahead date ≈ 09:37 ET
```

This package must verify the exact accepted values from canonical evidence before freezing them.

Do not recompute production timing from new paid calls.

Do not move the production 06:30 ET schedule in this task.

---

# 2. Canonical evidence — mandatory reads

Read completely from full canonical paths:

```text
F:\options-anomaly-scanner\docs\evidence\NIGHTWATCH_VNEXT_CANONICAL_EVIDENCE_MANIFEST.md

F:\options-anomaly-scanner\docs\evidence\NIGHTWATCH_SCANNER_VNEXT_INTEGRATED_SPEC_PROMPT_20260817(1).md

F:\options-anomaly-scanner\docs\evidence\NIGHTWATCH_VNEXT_STAGE4A_DAILY_PIPELINE_CODEX_EXECUTION_PACKAGE_20260818.md

F:\options-anomaly-scanner\docs\evidence\NIGHTWATCH_VNEXT_STAGE8_DAILY_AUTOMATION_DEPLOYMENT_GATE_REPORT_20260825.md

F:\options-anomaly-scanner\docs\evidence\NIGHTWATCH_VNEXT_STAGE8_DAILY_AUTOMATION_GITHUB_DEPLOYMENT_REPORT_20260825.md

F:\options-anomaly-scanner\docs\evidence\NIGHTWATCH_VNEXT_STAGE8_SCHEDULED_RUNTIME_REMEDIATION_REPORT_20260826.md
```

Also inspect the current repository copy of:

```text
F:\options-anomaly-scanner\.github\workflows\oi-change-rollover-timing-experiment.yml
```

and GitHub's currently active workflow metadata.

If this execution package is attached and absent from canonical evidence, preserve it byte-for-byte as:

```text
F:\options-anomaly-scanner\docs\evidence\NIGHTWATCH_OI_ROLLOVER_EXPERIMENT_CLOSEOUT_DEACTIVATION_EXECUTION_PACKAGE_20260826.md
```

If same-name canonical content differs, do not overwrite:

```text
ROLLOVER_CLOSEOUT_RESULT=HOLD_PACKAGE_CONFLICT
```

STOP.

---

# 3. Current-state proof before edits

Fetch latest `origin/main`.

Record:

```text
REMOTE_MAIN_BEFORE=
LOCAL_MAIN_BEFORE=
WORKTREE_STATUS=
```

Inspect the current rollover workflow and return:

```text
ROLLOVER_WORKFLOW_PATH=
ROLLOVER_WORKFLOW_GITHUB_STATE=
ROLLOVER_SCHEDULE_TRIGGER_PRESENT=YES/NO
ROLLOVER_WORKFLOW_DISPATCH_PRESENT=YES/NO
ROLLOVER_LIVE_MANUAL_MODE_PRESENT=YES/NO
```

Inspect the production Phase 2A workflow and prove:

```text
PHASE2A_DAILY_WORKFLOW_PRESENT=YES
RADAR_OI_PRODUCTION_SCHEDULE=06:30 America/New_York
ACTIVITY_OBSERVATION_SCHEDULE=16:30 America/New_York
```

If production timing differs unexpectedly from accepted state:

```text
ROLLOVER_CLOSEOUT_RESULT=HOLD_PRODUCTION_SCHEDULE_DRIFT
```

STOP. Do not alter production timing.

---

# 4. Freeze the experiment evidence

Create a concise closeout section in the report that records:

```text
experiment purpose
date range of accepted evidence
successful scheduled run count
probe-record count
tickers used
XNYS dates covered
earliest expected-date availability
latest first availability
earliest observed rollover/switch
contradictions found
final production-safe window
chosen production cron
reason for closeout
```

Required conclusion:

```text
EXPERIMENT_PURPOSE_FULFILLED=YES
PRODUCTION_TIMING_CONCLUSION_FROZEN=YES
FURTHER_AUTOMATIC_PROBING_REQUIRED=NO
```

Do not claim the vendor can never change its publication timing in the future.

The correct wording is:

```text
current production timing is supported by the completed 2026-08 experiment;
future material vendor-timing drift may justify a separately authorized re-open.
```

---

# 5. Scheduled deactivation semantics

The intended deactivation is:

```text
remove automatic schedule/cron triggers
retain workflow_dispatch/manual capability
do not manually dispatch it now
```

Modify only:

```text
.github/workflows/oi-change-rollover-timing-experiment.yml
```

unless a narrow evidence/documentation file is separately required.

The resulting workflow must have:

```text
schedule trigger = absent
workflow_dispatch = present
```

Preserve safe manual defaults.

If the workflow currently exposes both dry-run and live manual modes:

```text
default manual mode must remain dry_run or equivalent safe non-live default
live/manual paid mode may remain only if it already existed and still requires explicit user selection
```

Do not add a new live mode.

Do not weaken date guards, secret handling, artifact safety, or research isolation.

Do not delete the workflow file entirely unless the current architecture cannot preserve manual capability safely; if so, HOLD for Founder decision instead.

---

# 6. Do not touch production automation

Absolutely no changes to:

```text
.github/workflows/phase2a-daily-archive.yml
.github/workflows/dealer-gex-archive.yml
```

No change to:

```text
06:30 ET Radar/OI
16:30 ET Activity/vNext observation
Dealer/GEX 15:30 ET
```

Return:

```text
PHASE2A_WORKFLOW_CHANGED=NO
DEALER_GEX_WORKFLOW_CHANGED=NO
PRODUCTION_RADAR_TIMING_CHANGED=NO
```

---

# 7. Existing queued/running rollover jobs

Inspect GitHub read-only for currently queued/in-progress rollover experiment runs.

Return:

```text
ROLLOVER_RUNS_CURRENTLY_QUEUED=
ROLLOVER_RUNS_CURRENTLY_IN_PROGRESS=
```

Do not cancel them in this task.

Reason:

```text
this package deactivates future scheduling;
it does not mutate already-started historical executions.
```

If any are running, report them as carried until natural completion/cancellation by GitHub.

---

# 8. Verification before commit

Run local/static checks:

```text
YAML parse / repository workflow validation
git diff --check
secret scan
verify only authorized workflow/evidence paths changed
verify no schedule: block remains in rollover workflow
verify workflow_dispatch remains
verify production workflows byte-identical to pre-task versions
```

No application/backend test suite is required if no application code changes.

If repository workflow tests cover the rollover file, run the relevant focused tests.

Required:

```text
ROLLOVER_SCHEDULE_REMOVED=YES
ROLLOVER_MANUAL_DISPATCH_PRESERVED=YES
PRODUCTION_WORKFLOWS_UNCHANGED=YES
STATIC_VALIDATION_PASS=YES
```

---

# 9. Commit and push to GitHub main

After all checks pass:

1. Refetch `origin/main`.
2. If remote moved, update from latest main using normal non-destructive semantics.
3. No force push.
4. Commit only the closeout/deactivation changes.
5. Push normally to `main` if allowed; otherwise use repository protection/PR policy without bypassing it.

Suggested commit subject:

```text
ops: close rollover timing experiment schedule
```

Return:

```text
CLOSEOUT_COMMIT=
DEPLOYMENT_PATH=
REMOTE_MAIN_AFTER=
```

---

# 10. Post-deployment GitHub verification

Verify through GitHub metadata/API:

```text
rollover workflow still exists
rollover workflow recognized
automatic schedule trigger absent
manual workflow_dispatch present
production Phase 2A workflow still active
Dealer/GEX workflow still active
```

Required:

```text
ROLLOVER_AUTOMATIC_SCHEDULE_ACTIVE=NO
ROLLOVER_MANUAL_REOPEN_CAPABILITY=YES
PHASE2A_DAILY_WORKFLOW_ACTIVE=YES
DEALER_GEX_WORKFLOW_ACTIVE=YES
```

Do not dispatch any workflow.

---

# 11. Cost effect

Do not estimate historical spend unless evidence supports it.

State only:

```text
future scheduled rollover probe spend after deactivation = 0
```

subject to:

```text
no manual future dispatch
```

Return:

```text
FUTURE_AUTOMATIC_ROLLOVER_NIGHTWATCH_CALLS=0
FUTURE_AUTOMATIC_ROLLOVER_PAID_UNITS=0
```

This does not affect normal Phase 2A / MAG7 / Dealer GEX production costs.

---

# 12. Re-open policy

Document a narrow future re-open condition.

A re-open should require separate Founder authorization and one of:

```text
production Radar/OI repeatedly fails expected-date readiness
vendor timing materially shifts
vendor/API behavior changes
new evidence contradicts 06:00-08:00 ET safe window
```

Do not automatically re-enable the experiment.

Return:

```text
ROLLOVER_REOPEN_POLICY=SEPARATE_FOUNDER_AUTHORIZATION_REQUIRED
```

---

# 13. Result states

Use exactly one:

```text
ROLLOVER_CLOSEOUT_RESULT=PASS_CLOSED_AND_SCHEDULE_DEACTIVATED

ROLLOVER_CLOSEOUT_RESULT=HOLD_PACKAGE_CONFLICT
ROLLOVER_CLOSEOUT_RESULT=HOLD_CODE_STATE
ROLLOVER_CLOSEOUT_RESULT=HOLD_PRODUCTION_SCHEDULE_DRIFT
ROLLOVER_CLOSEOUT_RESULT=HOLD_REMOTE_MOVED
ROLLOVER_CLOSEOUT_RESULT=HOLD_WORKFLOW_SEMANTIC_GAP

ROLLOVER_CLOSEOUT_RESULT=FAIL_STATIC_VALIDATION
ROLLOVER_CLOSEOUT_RESULT=FAIL_GITHUB_ACTIVATION_VERIFICATION
```

---

# 14. Evidence report — fixed primary + canonical rule

Create primary report:

```text
F:\options-anomaly-scanner\docs\evidence\stage8\NIGHTWATCH_OI_ROLLOVER_EXPERIMENT_CLOSEOUT_DEACTIVATION_REPORT_20260826.md
```

Create byte-identical canonical backup:

```text
F:\options-anomaly-scanner\docs\evidence\NIGHTWATCH_OI_ROLLOVER_EXPERIMENT_CLOSEOUT_DEACTIVATION_REPORT_20260826.md
```

Verify SHA-256 for both.

If same-name canonical file exists with different bytes, never overwrite:

```text
ROLLOVER_CLOSEOUT_RESULT=HOLD_REPORT_CONFLICT
```

---

# 15. Required final fields

```text
ROLLOVER_CLOSEOUT_RESULT=
FOUNDER_AUTHORIZATION=OI_ROLLOVER_EXPERIMENT_CLOSEOUT_DEACTIVATION_20260826

REMOTE_MAIN_BEFORE=
REMOTE_MAIN_AFTER=
CLOSEOUT_COMMIT=
DEPLOYMENT_PATH=

ROLLOVER_WORKFLOW_PATH=
ROLLOVER_WORKFLOW_GITHUB_STATE=
ROLLOVER_SCHEDULE_TRIGGER_PRESENT_BEFORE=
ROLLOVER_SCHEDULE_TRIGGER_PRESENT_AFTER=
ROLLOVER_WORKFLOW_DISPATCH_PRESENT_AFTER=
ROLLOVER_LIVE_MANUAL_MODE_PRESENT=

EXPERIMENT_PURPOSE_FULFILLED=
PRODUCTION_TIMING_CONCLUSION_FROZEN=
FURTHER_AUTOMATIC_PROBING_REQUIRED=

ACCEPTED_SUCCESSFUL_SCHEDULED_RUNS=
ACCEPTED_PROBE_RECORDS=
ACCEPTED_XNYS_DATES=
EARLIEST_EXPECTED_DATE_AVAILABILITY=
LATEST_FIRST_EXPECTED_DATE_AVAILABILITY=
EARLIEST_OBSERVED_VENDOR_SWITCH=
FROZEN_SAFE_WINDOW=
FROZEN_PRODUCTION_CRON=

ROLLOVER_SCHEDULE_REMOVED=
ROLLOVER_MANUAL_DISPATCH_PRESERVED=
ROLLOVER_AUTOMATIC_SCHEDULE_ACTIVE=
ROLLOVER_MANUAL_REOPEN_CAPABILITY=

ROLLOVER_RUNS_CURRENTLY_QUEUED=
ROLLOVER_RUNS_CURRENTLY_IN_PROGRESS=

PHASE2A_WORKFLOW_CHANGED=NO
DEALER_GEX_WORKFLOW_CHANGED=NO
PRODUCTION_RADAR_TIMING_CHANGED=NO

PHASE2A_DAILY_WORKFLOW_ACTIVE=
DEALER_GEX_WORKFLOW_ACTIVE=

FUTURE_AUTOMATIC_ROLLOVER_NIGHTWATCH_CALLS=0
FUTURE_AUTOMATIC_ROLLOVER_PAID_UNITS=0

NIGHTWATCH_REQUESTS_THIS_TASK=0
PAID_UNITS_THIS_TASK=0
WORKFLOW_DISPATCHES_THIS_TASK=0
REMOTE_DB_WRITES_THIS_TASK=0
REMOTE_SCHEMA_WRITES_THIS_TASK=0

APPLICATION_CODE_CHANGES=0
MIGRATION_CHANGES=0
WORKFLOW_FILES_CHANGED=
TEST_FILES_CHANGED=
STATIC_VALIDATION_PASS=

COMMITS_CREATED=
PUSHES=
PRS_CREATED=
MERGES=

PRIMARY_REPORT_PATH=
CANONICAL_REPORT_PATH=
PRIMARY_REPORT_SHA256=
CANONICAL_REPORT_SHA256=
REPORT_BACKUP_BYTE_IDENTICAL=

ROLLOVER_REOPEN_POLICY=SEPARATE_FOUNDER_AUTHORIZATION_REQUIRED

STAGE8_STATUS=CONTINUE_OBSERVATION
STAGE9_STATUS=DESIGN_GATE_SEPARATE
NEXT_AUTHORIZED_STAGE=NONE
```

STOP.

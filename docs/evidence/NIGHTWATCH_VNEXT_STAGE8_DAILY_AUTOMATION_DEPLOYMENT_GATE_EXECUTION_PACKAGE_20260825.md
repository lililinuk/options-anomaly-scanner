# Nightwatch vNext — Stage 8 Daily Automation Deployment Gate — Execution Package

**Date:** 2026-08-25  
**Purpose:** Turn Stage 8 from manual controlled observations into a durable daily automated observation pipeline that naturally accumulates O1 / O4 / O6.  
**Execution repo:** `F:\options-anomaly-scanner`  
**Stage 8 worktree:** `F:\options-anomaly-scanner-stage8`  
**Canonical evidence root:** `F:\options-anomaly-scanner\docs\evidence`

## Founder intent

Target daily chain:

```text
A. Phase 2A daily archive
   -> Expiry Activity / Radar-OI / Contract OI history
   -> grows O4

B. Daily vNext MAG7 scan
   -> ProductCandidate + immutable ProductCandidateTrigger
   -> grows O1 + O6

C. FIRST_KNOWLEDGE_BASELINE
   -> exactly one frozen baseline per new ProductCandidate
   -> makes the day a genuine Stage 8 sample

D. Dashboard reads persisted results
```

## Canonical evidence

Read completely from explicit paths, including:

```text
F:\options-anomaly-scanner\docs\evidence\NIGHTWATCH_VNEXT_CANONICAL_EVIDENCE_MANIFEST.md
F:\options-anomaly-scanner\docs\evidence\NIGHTWATCH_SCANNER_VNEXT_INTEGRATED_SPEC_PROMPT_20260817(1).md
F:\options-anomaly-scanner\docs\evidence\NIGHTWATCH_VNEXT_STAGE4A_DAILY_PIPELINE_CODEX_EXECUTION_PACKAGE_20260818.md
F:\options-anomaly-scanner\docs\evidence\NIGHTWATCH_VNEXT_STAGE4B_PHASE2A_VNEXT_CODEX_EXECUTION_PACKAGE_20260818.md
F:\options-anomaly-scanner\docs\evidence\NIGHTWATCH_VNEXT_STAGE5_PRODUCT_CANDIDATE_PERSISTENCE_COMPLETION_REPORT_20260818.md
F:\options-anomaly-scanner\docs\evidence\NIGHTWATCH_VNEXT_STAGE6_PHASE2B_BALANCED_MODEL_COMPLETION_REPORT_20260818.md
F:\options-anomaly-scanner\docs\evidence\NIGHTWATCH_VNEXT_STAGE7_CANDIDATE_FIRST_DASHBOARD_COMPLETION_REPORT_20260819.md
F:\options-anomaly-scanner\docs\evidence\NIGHTWATCH_VNEXT_STAGE8_OBSERVATION_RESUME_FIRST_GENUINE_SAMPLE_REPORT_20260824.md
F:\options-anomaly-scanner\docs\evidence\NIGHTWATCH_VNEXT_STAGE8_BASELINE_JSONB_SQL_NULL_REMEDIATION_REPORT_20260820.md
F:\options-anomaly-scanner\docs\evidence\NIGHTWATCH_VNEXT_STAGE8_BASELINE_ONLY_CREATION_RETRY_REPORT_20260824.md
```

If this package is attached and absent from canonical evidence, save it byte-for-byte as:

```text
F:\options-anomaly-scanner\docs\evidence\NIGHTWATCH_VNEXT_STAGE8_DAILY_AUTOMATION_DEPLOYMENT_GATE_EXECUTION_PACKAGE_20260825.md
```

Never overwrite conflicting canonical evidence.

## Hard boundaries

Authorized:

```text
inspect current repository/worktrees
inspect actual GitHub workflows
inspect rollover experiment evidence
read-only runtime DB queries
determine safe production timing
add/modify minimum workflow / CLI orchestration / tests needed for daily automation
run local tests/lint/workflow validation
create evidence report
```

Forbidden:

```text
real MAG7 scan
Nightwatch calls
paid units
workflow dispatch
push/merge/PR
threshold/scoring changes
numeric Persistence calibration
universe expansion
Forward Outcome computation
Phase2B paid refresh
historical rewrite
```

Required during this task:

```text
NIGHTWATCH_REQUESTS=0
PAID_UNITS=0
REMOTE_APPLICATION_DATA_WRITES=0
REMOTE_SCHEMA_WRITES=0
WORKFLOWS_DISPATCHED=0
```

## 1. Current workflow inventory

Inspect current repository, not old reports.

Return:

```text
CURRENT_WORKFLOWS=
DEALER_GEX_WORKFLOW_PATH=
ROLLOVER_EXPERIMENT_WORKFLOW_PATH=
PHASE2A_DAILY_ARCHIVE_WORKFLOW_PATH=
DAILY_VNEXT_OBSERVATION_WORKFLOW_PATH=
```

For every relevant workflow record triggers, cron/timezone, dispatch support, entrypoint, secrets, concurrency, trading-day guards, write scope, and paid-call scope.

Determine whether Stage 4A workflow plumbing already exists but is inactive.

## 2. Freeze rollover timing

Read the actual multi-day rollover experiment evidence.

Determine:

```text
latest vendor OI date by probe slot
earliest consistently safe Radar/OI production window
consistency across available experiment days
non-trading-day behavior
contradictory days
```

Return one:

```text
ROLLOVER_TIMING_GATE=PASS_CONCLUSIVE
ROLLOVER_TIMING_GATE=PASS_WITH_CONSERVATIVE_SAFE_WINDOW
ROLLOVER_TIMING_GATE=HOLD_INSUFFICIENT_EVIDENCE
ROLLOVER_TIMING_GATE=HOLD_CONTRADICTORY_EVIDENCE
```

If PASS:

```text
RADAR_OI_PRODUCTION_SAFE_WINDOW=
RADAR_OI_SCHEDULE_TIMEZONE=
RADAR_OI_SCHEDULE_EVIDENCE_BASIS=
```

Do not copy Dealer/GEX 15:30 ET unless experiment evidence independently supports it.

## 3. Phase 2A daily archive automation

Discover the accepted Stage 4A CLI/modes from current code.

The automation must accumulate:

```text
same-day canonical session-complete Expiry Activity
Radar/OI-confirmation
Contract OI archive / Contract Persistence history
```

Preserve:

```text
workflow_dispatch
server-side secrets
contents: read
concurrency
market-calendar/session guards
idempotence
append-only semantics
missing != zero
vendor time != capture time
no fabricated closure
```

This is what accumulates O4.

## 4. Daily vNext observation automation

After daily source prerequisites are eligible, run exactly one accepted vNext MAG7 production scan for MAG7.

Discover the actual production entrypoint; do not invent one.

Required semantics:

```text
accepted MAG7 universe
accepted thresholds/scoring
no blind automatic paid retry
SUCCESS_NO_CANDIDATE stays truthful
FAILED/PARTIAL never becomes zero-candidate success
```

This accumulates O1 and O6.

Return:

```text
EXPECTED_DAILY_MAG7_PAID_UNITS=
MAX_CONFIGURED_DAILY_MAG7_PAID_UNITS=
```

Do not execute the scan in this package.

## 5. Automatic FIRST_KNOWLEDGE_BASELINE

For every newly materialized ProductCandidate:

```text
create exactly one FIRST_KNOWLEDGE_BASELINE
evidence_cutoff_at = candidate_first_knowledge_at
zero paid Phase2B refresh
Dealer/GEX archive-only
```

Use the accepted Stage 6 service and accepted JSONB SQL-NULL remediation.

If current scanner already does this, prove it.
If not, add the minimum orchestration/CLI plumbing needed.

Required:

```text
SUCCESS_WITH_CANDIDATES -> one baseline per candidate
SUCCESS_NO_CANDIDATE -> zero baselines, valid genuine zero-candidate day
FAILED/PARTIAL -> no fabricated candidate/baseline success
```

## 6. Daily dependency order

Derive exact order from actual source publication semantics.

Return:

```text
DAILY_AUTOMATION_DEPENDENCY_ORDER=
DAILY_SCAN_EARLIEST_SAFE_START=
DAILY_SCAN_TIMEZONE=
```

The scan must not run before required daily evidence is eligible.

## 7. Workflow topology

Choose the minimum clear design:

```text
one multi-job workflow
or
multiple source-specific workflows with explicit dependencies
```

Base the choice on source timing, failure isolation, idempotence, cost control, and operator clarity.

Return:

```text
WORKFLOW_TOPOLOGY=
RATIONALE=
```

No Forward Outcome scheduler.

## 8. Failure semantics

Preserve truthful states as supported:

```text
SKIPPED_NON_TRADING_SESSION
SKIPPED_BEFORE_SOURCE_READY
SUCCESS
SUCCESS_NO_CANDIDATE
PARTIAL
FAILED
```

Do not continue to paid stages when prerequisite evidence is not ready.

## 9. Dashboard visibility

Do not redesign Stage 7.

Verify whether existing dashboard can truthfully show:

```text
last successful Phase 2A collection
last scan status/time
candidate date
baseline existence
quota / observation age
```

If not, return:

```text
DASHBOARD_AUTOMATION_VISIBILITY_GAP=
```

Carry it unless a tiny strictly necessary field change is within declared scope.

## 10. O1/O4/O6 coverage gate

Prove the resulting automation will accumulate:

```text
O1:
daily candidate counts
candidate-producing runs
successful zero-candidate runs

O4:
multi-observation Contract Persistence history
3/5/10 valid-observation maturation when naturally reached

O6:
candidate counts by ticker across NY market dates
trigger shares by ticker across NY market dates
```

Required:

```text
O1_AUTOMATION_COVERAGE=YES
O4_AUTOMATION_COVERAGE=YES
O6_AUTOMATION_COVERAGE=YES
```

## 11. Authorized file declaration

Before editing:

```text
AUTHORIZED_FILES_PROPOSED:
- <path>: <reason>
```

Expected categories:

```text
.github/workflows/*
minimal backend CLI/orchestration if needed
focused tests
evidence/docs
```

No scanner scoring/candidate-logic changes.

If broader scope is required, HOLD.

## 12. Verification

Run applicable offline checks:

```text
workflow tests/validation
Stage 4A tests
Stage 4B regressions
Stage 5 tests
Stage 6 baseline tests
full backend suite
Ruff
git diff --check
secret scan
```

No paid calls or remote writes.

## 13. Result

Use one:

```text
STAGE8_DAILY_AUTOMATION_GATE_RESULT=PASS_READY_TO_DEPLOY
STAGE8_DAILY_AUTOMATION_GATE_RESULT=PASS_IMPLEMENTED_PENDING_PUSH
STAGE8_DAILY_AUTOMATION_GATE_RESULT=HOLD_ROLLOVER_TIMING
STAGE8_DAILY_AUTOMATION_GATE_RESULT=HOLD_CODE_STATE
STAGE8_DAILY_AUTOMATION_GATE_RESULT=HOLD_SCOPE_EXPANSION_REQUIRED
STAGE8_DAILY_AUTOMATION_GATE_RESULT=FAIL_INTEGRITY
```

If local workflow changes are complete but not pushed:

```text
PASS_IMPLEMENTED_PENDING_PUSH
```

Do not claim GitHub deployment before commit/push to the branch GitHub schedules from.

## 14. Evidence report

Primary:

```text
F:\options-anomaly-scanner-stage8\docs\evidence\stage8\NIGHTWATCH_VNEXT_STAGE8_DAILY_AUTOMATION_DEPLOYMENT_GATE_REPORT_20260825.md
```

Canonical byte-identical backup:

```text
F:\options-anomaly-scanner\docs\evidence\NIGHTWATCH_VNEXT_STAGE8_DAILY_AUTOMATION_DEPLOYMENT_GATE_REPORT_20260825.md
```

Verify SHA-256 and never overwrite conflicts.

## 15. Required final fields

```text
STAGE8_DAILY_AUTOMATION_GATE_RESULT=

CURRENT_WORKFLOWS=
PHASE2A_DAILY_ARCHIVE_WORKFLOW_PATH=
DAILY_VNEXT_OBSERVATION_WORKFLOW_PATH=

ROLLOVER_TIMING_GATE=
RADAR_OI_PRODUCTION_SAFE_WINDOW=
RADAR_OI_SCHEDULE_TIMEZONE=
RADAR_OI_SCHEDULE_EVIDENCE_BASIS=

PHASE2A_DAILY_ARCHIVE_ENTRYPOINT=
VNEXT_MAG7_PRODUCTION_ENTRYPOINT=
FIRST_KNOWLEDGE_BASELINE_ENTRYPOINT=

WORKFLOW_TOPOLOGY=
DAILY_AUTOMATION_DEPENDENCY_ORDER=
DAILY_SCAN_EARLIEST_SAFE_START=
DAILY_SCAN_TIMEZONE=

EXPECTED_DAILY_MAG7_PAID_UNITS=
MAX_CONFIGURED_DAILY_MAG7_PAID_UNITS=

O1_AUTOMATION_COVERAGE=
O4_AUTOMATION_COVERAGE=
O6_AUTOMATION_COVERAGE=

DASHBOARD_AUTOMATION_VISIBILITY_GAP=

APPLICATION_CODE_CHANGES=
TEST_CODE_CHANGES=
WORKFLOW_FILES_CHANGED=
MIGRATION_CHANGES=0

NIGHTWATCH_REQUESTS=0
PAID_UNITS=0
REMOTE_APPLICATION_DATA_WRITES=0
REMOTE_SCHEMA_WRITES=0
WORKFLOWS_DISPATCHED=0

COMMITS_CREATED=
PUSHES=0
PRS_CREATED=0
MERGES=0

PRIMARY_REPORT_PATH=
CANONICAL_REPORT_PATH=
PRIMARY_REPORT_SHA256=
CANONICAL_REPORT_SHA256=
REPORT_BACKUP_BYTE_IDENTICAL=YES/NO

DAILY_AUTOMATION_DEPLOYED_TO_GITHUB=NO
NEXT_AUTHORIZED_STAGE=NONE
```

STOP.

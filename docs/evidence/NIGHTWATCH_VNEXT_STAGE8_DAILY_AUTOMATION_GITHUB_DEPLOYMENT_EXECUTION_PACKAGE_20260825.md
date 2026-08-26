# Nightwatch vNext — Stage 8 Daily Automation GitHub Deployment — Execution Package

**Date:** 2026-08-25  
**Purpose:** Commit, safely integrate, and deploy the already-accepted Stage 8 daily automation to the GitHub default branch so scheduled collection/observation can actually run.  
**Founder authorization:** `STAGE8_DAILY_AUTOMATION_GITHUB_DEPLOYMENT_20260825`  
**Stage 8 worktree:** `F:\options-anomaly-scanner-stage8`  
**Canonical repo:** `F:\options-anomaly-scanner`  
**Canonical evidence root:** `F:\options-anomaly-scanner\docs\evidence`

## 0. Authorization

Authorized:

```text
inspect git/GitHub state
fetch remote refs
commit accepted Stage 8 local changes
create a temporary local integration branch/worktree if needed
merge/cherry-pick using normal non-destructive Git semantics
push a deployment/integration branch
push/merge to the GitHub default branch if protection allows and all gates pass
create a PR if protection requires it
merge that PR if required checks are green and no human-review rule blocks it
verify workflow activation on the active default branch
create evidence reports
```

Not authorized:

```text
force push / force-with-lease
rewrite public history
reset/stash/discard accepted Stage 8 changes
drop any accepted remediation
manual MAG7 scan
manual workflow dispatch
Nightwatch call / paid unit
runtime Supabase write
migration
threshold/scoring/universe change
schedule-semantics change from the accepted deployment gate
Forward Outcome computation
```

This task proves deployment, not the first scheduled runtime success.

## 1. Accepted local state

```text
STAGE8_DAILY_AUTOMATION_GATE_RESULT=PASS_IMPLEMENTED_PENDING_PUSH
O1_AUTOMATION_COVERAGE=YES
O4_AUTOMATION_COVERAGE=YES
O6_AUTOMATION_COVERAGE=YES
```

Accepted workflow:

```text
F:\options-anomaly-scanner-stage8\.github\workflows\phase2a-daily-archive.yml
```

Accepted schedule semantics:

```text
06:30 America/New_York
  Daily OI archive -> Radar/OI

16:30 America/New_York
  session-complete Activity
  -> persisted-source readiness gate
  -> exactly one vNext MAG7 scan
  -> ProductCandidates / immutable triggers
  -> one FIRST_KNOWLEDGE_BASELINE per candidate
```

Expected scan cost:

```text
EXPECTED_DAILY_MAG7_PAID_UNITS=14
MAX_CONFIGURED_DAILY_MAG7_PAID_UNITS=75
```

## 2. Canonical evidence

Read completely from:

```text
F:\options-anomaly-scanner\docs\evidence\NIGHTWATCH_VNEXT_CANONICAL_EVIDENCE_MANIFEST.md
F:\options-anomaly-scanner\docs\evidence\NIGHTWATCH_SCANNER_VNEXT_INTEGRATED_SPEC_PROMPT_20260817(1).md
F:\options-anomaly-scanner\docs\evidence\NIGHTWATCH_VNEXT_STAGE4A_DAILY_PIPELINE_CODEX_EXECUTION_PACKAGE_20260818.md
F:\options-anomaly-scanner\docs\evidence\NIGHTWATCH_VNEXT_STAGE5_PRODUCT_CANDIDATE_PERSISTENCE_COMPLETION_REPORT_20260818.md
F:\options-anomaly-scanner\docs\evidence\NIGHTWATCH_VNEXT_STAGE6_PHASE2B_BALANCED_MODEL_COMPLETION_REPORT_20260818.md
F:\options-anomaly-scanner\docs\evidence\NIGHTWATCH_VNEXT_STAGE7_CANDIDATE_FIRST_DASHBOARD_COMPLETION_REPORT_20260819.md
F:\options-anomaly-scanner\docs\evidence\NIGHTWATCH_VNEXT_STAGE8_BASELINE_JSONB_SQL_NULL_REMEDIATION_REPORT_20260820.md
F:\options-anomaly-scanner\docs\evidence\NIGHTWATCH_VNEXT_STAGE8_BASELINE_ONLY_CREATION_RETRY_REPORT_20260824.md
F:\options-anomaly-scanner\docs\evidence\NIGHTWATCH_VNEXT_STAGE8_OBSERVATION_RESUME_FIRST_GENUINE_SAMPLE_REPORT_20260824.md
F:\options-anomaly-scanner\docs\evidence\NIGHTWATCH_VNEXT_STAGE8_DAILY_AUTOMATION_DEPLOYMENT_GATE_REPORT_20260825.md
```

If this package is attached and absent from canonical evidence, preserve it byte-for-byte as:

```text
F:\options-anomaly-scanner\docs\evidence\NIGHTWATCH_VNEXT_STAGE8_DAILY_AUTOMATION_GITHUB_DEPLOYMENT_EXECUTION_PACKAGE_20260825.md
```

If a same-name canonical file differs, do not overwrite:

```text
GITHUB_DEPLOYMENT_RESULT=HOLD_PACKAGE_CONFLICT
```

STOP.

## 3. Pre-deployment worktree proof

In `F:\options-anomaly-scanner-stage8`, record:

```text
git status --short
git diff --check
git rev-parse HEAD
git rev-parse --abbrev-ref HEAD
```

Prove:

```text
S4_IDENTIFIER_REMEDIATION_PRESENT=YES
POST_CANDIDATE_PARTIAL_REMEDIATION_PRESENT=YES
BASELINE_JSONB_SQL_NULL_REMEDIATION_PRESENT=YES
DAILY_AUTOMATION_IMPLEMENTATION_PRESENT=YES
UNEXPECTED_UNACCEPTED_DIFF_FOUND=NO
```

Expected accepted-change categories include:

```text
backend/app/db/models.py
backend/app/scanner/v13.py
backend/tests/test_stage4b_phase2a_vnext.py
backend/tests/test_stage6_balanced_context.py
.github/workflows/phase2a-daily-archive.yml
backend/app/cli.py
backend/app/scanner/daily.py
backend/app/scanner/daily_semantics.py
backend/app/scanner/daily_observation.py
backend/tests/test_phase2a_daily_workflow.py
backend/tests/test_daily_vnext_observation.py
backend/tests/test_stage8_daily_automation_workflow.py
```

Do not reset/stash/discard accepted changes.

## 4. Remote/default-branch identity gate

Fetch remote refs and determine the actual GitHub default branch from authoritative remote/GitHub metadata.

Return:

```text
REMOTE_NAME=
GITHUB_DEFAULT_BRANCH=
REMOTE_DEFAULT_HEAD_BEFORE=
STAGE8_LOCAL_HEAD_BEFORE=
```

Inspect active workflows on the default branch. Pre-deployment expectation:

```text
phase2a-daily-archive.yml not active on default branch
```

If already active unexpectedly, compare exact content/history before proceeding.

## 5. vNext prerequisite-lineage gate

Do not deploy the workflow onto a branch that lacks the runtime code it invokes.

Prove the default-branch relation to the accepted vNext lineage and whether it contains:

```text
app.scanner.v13.Mag7Scanner
ProductCandidate / ProductCandidateTrigger persistence
Stage6BalancedContextService.create_baseline
20260818_0017 schema code line
accepted Stage 8 runtime remediations
```

Return:

```text
DEFAULT_BRANCH_HAS_VNEXT_RUNTIME_PREREQUISITES=YES/NO
DEFAULT_BRANCH_HAS_ALEMBIC_0017_CODELINE=YES/NO
DEFAULT_BRANCH_DEPLOYMENT_RELATION=
```

Allowed safe relation classes:

```text
DEFAULT_IS_ANCESTOR_OF_STAGE8_LINE
STAGE8_LINE_IS_ANCESTOR_OF_DEFAULT
CLEAN_DIVERGENCE_MERGEABLE
```

If default lacks prerequisites and integration requires unreviewed or semantically conflicting code:

```text
GITHUB_DEPLOYMENT_RESULT=HOLD_VNEXT_INTEGRATION_REQUIRED
```

STOP. Never deploy YAML alone onto an incompatible default branch.

## 6. Commit accepted Stage 8 changes

Create logically clear commits on the Stage 8 branch.

Preferred:

```text
Commit A: accepted Stage 8 runtime remediations still uncommitted
Commit B: daily automation + workflow + focused tests
```

A single combined accepted deployment commit is permitted if separation would be artificial/unsafe.

Exclude temporary artifacts, `.env`, credentials, `node_modules`, `.next`, logs, caches.

Before commit:

```text
git diff --check
secret scan
```

Return:

```text
STAGE8_ACCEPTED_COMMITS_CREATED=
STAGE8_DEPLOYMENT_TIP=
```

## 7. Safe integration strategy

Use only non-destructive Git integration.

Preferred procedure:

1. Create a clean temporary integration branch/worktree from latest `origin/<default>`.
2. Integrate the committed Stage 8 deployment tip using a normal merge/cherry-pick sequence that preserves all accepted prerequisite commits.
3. Do not reconstruct accepted patches from memory.
4. Do not automatically resolve semantic code/schema/workflow conflicts.

Any semantic conflict:

```text
GITHUB_DEPLOYMENT_RESULT=HOLD_INTEGRATION_CONFLICT
```

STOP.

Never use force push, force-with-lease, public-history rewrite, or destructive reset.

Return:

```text
INTEGRATION_STRATEGY=
INTEGRATION_COMMIT=
INTEGRATION_CONFLICTS_FOUND=YES/NO
```

## 8. Full pre-push verification

Run against the exact integration tree intended for the default branch:

```text
focused Stage 8 automation tests
Stage 4A daily pipeline tests
Stage 4B regressions
Stage 5 ProductCandidate tests
Stage 6 baseline tests
Stage 7 relevant regressions
full backend suite
Ruff
Alembic single-head check
frontend lint/build/glossary as applicable
workflow static validation
git diff --check
secret scan
```

Required:

```text
ALL_DEPLOYMENT_TESTS_PASS=YES
ALEMBIC_HEAD=20260818_0017
ALEMBIC_SINGLE_HEAD=YES
```

No Nightwatch calls, workflow dispatches, migrations, or remote DB writes.

Failure => `GITHUB_DEPLOYMENT_RESULT=FAIL_PRE_PUSH_VERIFICATION`; do not update default branch.

## 9. Push/deploy policy

### Direct push allowed

Refetch immediately before push. If remote default moved since integration base:

```text
GITHUB_DEPLOYMENT_RESULT=HOLD_REMOTE_MOVED
```

STOP and rebuild from new head.

Otherwise use a normal non-force push.

### Branch protection blocks direct push

Push the integration branch, create a PR to default, wait for required checks, and merge only if repository policy permits and no required human review remains.

If human review is required:

```text
GITHUB_DEPLOYMENT_RESULT=HOLD_BRANCH_PROTECTION_REVIEW_REQUIRED
```

Do not bypass protection.

Return:

```text
DEPLOYMENT_PATH=DIRECT_DEFAULT_PUSH/PROTECTED_BRANCH_PR
DEPLOYMENT_BRANCH=
PR_NUMBER=
PR_URL_SAFE=
MERGE_COMMIT=
```

## 10. Post-push GitHub activation verification

Verify on the active default branch:

```text
phase2a-daily-archive.yml exists
GitHub Actions recognizes the workflow
06:30 America/New_York Radar/OI schedule present
16:30 America/New_York Activity + daily observation schedule present
workflow_dispatch remains collection-only
Dealer/GEX workflow remains intact
rollover experiment remains intact
```

Return:

```text
PHASE2A_DAILY_WORKFLOW_ACTIVE_ON_DEFAULT=YES/NO
GITHUB_WORKFLOW_RECOGNIZED=YES/NO
RADAR_OI_SCHEDULE_ACTIVE=YES/NO
ACTIVITY_OBSERVATION_SCHEDULE_ACTIVE=YES/NO
MANUAL_DISPATCH_CAN_TRIGGER_PAID_SCAN=NO
```

Do not manually dispatch anything.

## 11. Deployment != scheduled runtime proof

On deployment PASS:

```text
DAILY_AUTOMATION_DEPLOYED_TO_GITHUB=YES
FIRST_SCHEDULED_RUNTIME_PROOF_COMPLETE=NO
```

Do not claim the automation has run successfully until a naturally scheduled cycle is later observed.

## 12. Next scheduled runtime proof readiness

Report the next expected checkpoints based on actual schedule/current time:

```text
NEXT_EXPECTED_RADAR_OI_SCHEDULE=
NEXT_EXPECTED_ACTIVITY_OBSERVATION_SCHEDULE=
FIRST_SCHEDULED_RUNTIME_GATE_READY=YES/NO
```

Future runtime proof must verify:

```text
scheduled trigger fired
source readiness succeeded
paid usage stayed within expected bounds
exactly one scheduled scan for the NY date
truthful candidate/zero-candidate/failed state
one frozen baseline per new candidate
O1/O4/O6 runtime data advanced
no automatic paid retry
```

## 13. Authorization ledger

Required:

```text
MANUAL_MAG7_SCANS_RUN=0
WORKFLOW_DISPATCHES=0
NIGHTWATCH_REQUESTS_FROM_DEPLOYMENT_TASK=0
PAID_UNITS_FROM_DEPLOYMENT_TASK=0
REMOTE_DB_WRITES_FROM_DEPLOYMENT_TASK=0
REMOTE_MIGRATIONS_RUN=0
FORWARD_OUTCOME_COMPUTED=0
```

## 14. Result states

Use exactly one:

```text
GITHUB_DEPLOYMENT_RESULT=PASS_DEPLOYED
GITHUB_DEPLOYMENT_RESULT=HOLD_PACKAGE_CONFLICT
GITHUB_DEPLOYMENT_RESULT=HOLD_CODE_STATE
GITHUB_DEPLOYMENT_RESULT=HOLD_VNEXT_INTEGRATION_REQUIRED
GITHUB_DEPLOYMENT_RESULT=HOLD_INTEGRATION_CONFLICT
GITHUB_DEPLOYMENT_RESULT=HOLD_REMOTE_MOVED
GITHUB_DEPLOYMENT_RESULT=HOLD_BRANCH_PROTECTION_REVIEW_REQUIRED
GITHUB_DEPLOYMENT_RESULT=FAIL_PRE_PUSH_VERIFICATION
GITHUB_DEPLOYMENT_RESULT=FAIL_GITHUB_ACTIVATION_VERIFICATION
```

`PASS_DEPLOYED` requires the workflow to be present and recognized on the active default branch.

## 15. Evidence report

Primary:

```text
F:\options-anomaly-scanner-stage8\docs\evidence\stage8\NIGHTWATCH_VNEXT_STAGE8_DAILY_AUTOMATION_GITHUB_DEPLOYMENT_REPORT_20260825.md
```

Canonical byte-identical backup:

```text
F:\options-anomaly-scanner\docs\evidence\NIGHTWATCH_VNEXT_STAGE8_DAILY_AUTOMATION_GITHUB_DEPLOYMENT_REPORT_20260825.md
```

Verify SHA-256. Never overwrite conflicting canonical evidence.

## 16. Required final fields

```text
GITHUB_DEPLOYMENT_RESULT=
FOUNDER_AUTHORIZATION=STAGE8_DAILY_AUTOMATION_GITHUB_DEPLOYMENT_20260825

GITHUB_DEFAULT_BRANCH=
REMOTE_DEFAULT_HEAD_BEFORE=
STAGE8_LOCAL_HEAD_BEFORE=

S4_IDENTIFIER_REMEDIATION_PRESENT=
POST_CANDIDATE_PARTIAL_REMEDIATION_PRESENT=
BASELINE_JSONB_SQL_NULL_REMEDIATION_PRESENT=
DAILY_AUTOMATION_IMPLEMENTATION_PRESENT=
UNEXPECTED_UNACCEPTED_DIFF_FOUND=

DEFAULT_BRANCH_HAS_VNEXT_RUNTIME_PREREQUISITES=
DEFAULT_BRANCH_HAS_ALEMBIC_0017_CODELINE=
DEFAULT_BRANCH_DEPLOYMENT_RELATION=

STAGE8_ACCEPTED_COMMITS_CREATED=
STAGE8_DEPLOYMENT_TIP=

INTEGRATION_STRATEGY=
INTEGRATION_COMMIT=
INTEGRATION_CONFLICTS_FOUND=

ALL_DEPLOYMENT_TESTS_PASS=
ALEMBIC_HEAD=
ALEMBIC_SINGLE_HEAD=

DEPLOYMENT_PATH=
DEPLOYMENT_BRANCH=
PR_NUMBER=
PR_URL_SAFE=
MERGE_COMMIT=

PHASE2A_DAILY_WORKFLOW_ACTIVE_ON_DEFAULT=
GITHUB_WORKFLOW_RECOGNIZED=
RADAR_OI_SCHEDULE_ACTIVE=
ACTIVITY_OBSERVATION_SCHEDULE_ACTIVE=
MANUAL_DISPATCH_CAN_TRIGGER_PAID_SCAN=NO

DAILY_AUTOMATION_DEPLOYED_TO_GITHUB=
FIRST_SCHEDULED_RUNTIME_PROOF_COMPLETE=NO

NEXT_EXPECTED_RADAR_OI_SCHEDULE=
NEXT_EXPECTED_ACTIVITY_OBSERVATION_SCHEDULE=
FIRST_SCHEDULED_RUNTIME_GATE_READY=

MANUAL_MAG7_SCANS_RUN=0
WORKFLOW_DISPATCHES=0
NIGHTWATCH_REQUESTS_FROM_DEPLOYMENT_TASK=0
PAID_UNITS_FROM_DEPLOYMENT_TASK=0
REMOTE_DB_WRITES_FROM_DEPLOYMENT_TASK=0
REMOTE_MIGRATIONS_RUN=0
FORWARD_OUTCOME_COMPUTED=0

COMMITS_CREATED=
PUSHES=
PRS_CREATED=
MERGES=

PRIMARY_REPORT_PATH=
CANONICAL_REPORT_PATH=
PRIMARY_REPORT_SHA256=
CANONICAL_REPORT_SHA256=
REPORT_BACKUP_BYTE_IDENTICAL=

STAGE8_STATUS=CONTINUE_OBSERVATION
STAGE9_STATUS=DESIGN_GATE_SEPARATE
NEXT_AUTHORIZED_STAGE=NONE
```

STOP.

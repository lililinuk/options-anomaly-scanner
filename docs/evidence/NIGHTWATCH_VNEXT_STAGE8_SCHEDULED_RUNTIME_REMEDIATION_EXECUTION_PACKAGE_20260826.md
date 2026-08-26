# Nightwatch vNext — Stage 8 Scheduled Runtime Remediation — Execution Package

**Date:** 2026-08-26  
**Purpose:** Fix the two confirmed defects from the first naturally scheduled Stage 8 cycle, add explicit expired-vs-active chain-404 semantics, deploy the narrow remediation to GitHub `main`, and leave runtime re-proof to the next natural schedule.  
**Founder authorization:** `STAGE8_SCHEDULED_RUNTIME_REMEDIATION_20260826`  
**Canonical repo:** `F:\options-anomaly-scanner`  
**Current Stage 8 worktree:** `F:\options-anomaly-scanner-stage8`  
**Recommended clean remediation worktree:** `F:\options-anomaly-scanner-stage8-runtime-remediation`  
**Canonical evidence root:** `F:\options-anomaly-scanner\docs\evidence`

---

# 0. Founder authorization

```text
FOUNDER_AUTHORIZATION=STAGE8_SCHEDULED_RUNTIME_REMEDIATION_20260826

SCHEDULED_RUNTIME_REMEDIATION_AUTHORIZED=YES
CODE_CHANGES_AUTHORIZED=YES
TEST_CHANGES_AUTHORIZED=YES
GITHUB_DEPLOYMENT_AUTHORIZED=YES

MANUAL_MAG7_SCAN_AUTHORIZED=NO
WORKFLOW_DISPATCH_AUTHORIZED=NO
NIGHTWATCH_RUNTIME_RETEST_AUTHORIZED=NO
PAID_RUNTIME_RETEST_AUTHORIZED=NO
REMOTE_DB_REPAIR_AUTHORIZED=NO
REMOTE_SCHEMA_WRITE_AUTHORIZED=NO
MIGRATION_AUTHORIZED=NO
FORWARD_OUTCOME_AUTHORIZED=NO
```

The remediation must be deterministic and zero-paid. Runtime proof comes from the next natural GitHub schedule.

---

# 1. Confirmed defects to fix

Authoritative diagnostic:

```text
STAGE8_FIRST_SCHEDULED_FAILURE_DIAGNOSTIC_RESULT=PASS_ROOT_CAUSE_CONFIRMED
```

Morning run:

```text
daily_run_id=c43274fd-cb86-4004-9f1c-b88ddc33dd6a
daily_oi=FAILED
radar=FAILED

authoritative network attempts=2
authoritative paid units=1
parent counters incorrectly persisted/report 0/0
```

Confirmed causal sequence:

```text
AAPL oi-per-expiry
→ HTTP 200
→ AAPL RUNNING ticker row already exists

AAPL chain-snapshot expiration=2026-08-24
→ HTTP 404 NOT_FOUND

NightwatchError handler
→ attempts second DailyOiArchiveTicker row for same archive_run_id+AAPL
→ unique-key violation
→ transaction invalid
→ missing rollback
→ PendingRollbackError masks original defect
→ shared session poisoned
→ Radar cascades to FAILED
```

Confirmed second defect:

```text
DailyCollectionSummary(status=FAILED)
→ CLI returns process exit 0
→ GitHub falsely shows morning job green
```

Evening readiness gate was correct and must remain unchanged in principle:

```text
RADAR_COVERAGE_INCOMPLETE
→ no MAG7 scan
→ no paid scan units
→ no baselines
```

---

# 2. Additional semantic requirement — chain 404 classification

The Founder explicitly asked whether vendor `404 NOT_FOUND` means true nonexistence versus temporary unavailability and whether it should affect later decisions.

This remediation must therefore distinguish:

```text
EXPIRED_EXPIRY_CHAIN_404
vs
ACTIVE_EXPIRY_CHAIN_404
```

Evidence for the first scheduled failure:

```text
requested chain expiration = 2026-08-24
request occurred on NY market date 2026-08-25
the expiration previously existed in accepted historical evidence
```

Therefore the implementation must not equate all 404s with permanent nonexistence.

## Required semantics

### A. Expired expiry 404

When:

```text
expiration < current effective NY market date at collection time
```

and the chain endpoint returns 404:

```text
treat as expired/current-chain unavailable
do not fabricate OI=0
do not fabricate contract closure
preserve the already persisted expiry-level OI surface
persist/retain truthful non-contract-chain availability for that expiry
continue processing other expiries
do not poison the ticker transaction/session
do not make an otherwise healthy active-chain archive ineligible solely because an already-expired expiry is unavailable from the current-chain endpoint
```

This is not permission to backfill missing contract-level OI.

The historical contract-level chain for that expired session remains unavailable/missing unless independently captured earlier.

### B. Active/future expiry 404

When:

```text
expiration >= current effective NY market date
```

and chain endpoint returns 404:

```text
treat as active-chain vendor unavailability
do not fabricate zero
continue safely where architecture permits
do not duplicate ticker lifecycle rows
do not poison the SQLAlchemy session
do not silently promote incomplete active-chain coverage to COMPLETE
preserve fail-closed evening readiness if required active-chain evidence is incomplete
```

Do not invent a retry loop.

## Representation rule

Inspect the existing model/status/reason fields and use the minimum existing truthful representation.

No migration is authorized.

If there is no dedicated `EXPIRED_*` enum/status, use an existing non-complete status plus a structured existing reason/metadata field if available.

Do not create schema merely to add a label.

If truthful expired-vs-active classification cannot be represented without schema change:

```text
REMEDIATION_RESULT=HOLD_SCHEMA_SEMANTIC_GAP
```

STOP before changing schema.

---

# 3. Canonical evidence

Read completely:

```text
F:\options-anomaly-scanner\docs\evidence\NIGHTWATCH_VNEXT_CANONICAL_EVIDENCE_MANIFEST.md

F:\options-anomaly-scanner\docs\evidence\NIGHTWATCH_SCANNER_VNEXT_INTEGRATED_SPEC_PROMPT_20260817(1).md

F:\options-anomaly-scanner\docs\evidence\NIGHTWATCH_VNEXT_STAGE4A_DAILY_PIPELINE_CODEX_EXECUTION_PACKAGE_20260818.md

F:\options-anomaly-scanner\docs\evidence\NIGHTWATCH_VNEXT_STAGE8_DAILY_AUTOMATION_DEPLOYMENT_GATE_REPORT_20260825.md

F:\options-anomaly-scanner\docs\evidence\NIGHTWATCH_VNEXT_STAGE8_DAILY_AUTOMATION_GITHUB_DEPLOYMENT_REPORT_20260825.md

F:\options-anomaly-scanner\docs\evidence\NIGHTWATCH_VNEXT_STAGE8_FIRST_SCHEDULED_RUNTIME_FAILURE_DIAGNOSTIC_REPORT_20260826.md
```

If this execution package is attached and absent from canonical evidence, save it byte-for-byte as:

```text
F:\options-anomaly-scanner\docs\evidence\NIGHTWATCH_VNEXT_STAGE8_SCHEDULED_RUNTIME_REMEDIATION_EXECUTION_PACKAGE_20260826.md
```

If same-name canonical content differs, do not overwrite:

```text
REMEDIATION_RESULT=HOLD_PACKAGE_CONFLICT
```

STOP.

---

# 4. Git/worktree strategy

Do not reset, stash, or discard the existing Stage 8 worktree.

Fetch latest remote state.

Preferred safe approach:

```text
create branch from latest origin/main:
fix/stage8-scheduled-runtime-remediation

create clean worktree:
F:\options-anomaly-scanner-stage8-runtime-remediation
```

Verify latest `origin/main` contains:

```text
integration commit 55e9f96483c7edb897ff1829b63cbe84eac179a2
or a descendant thereof

vNext runtime prerequisites
Alembic 20260818_0017
Stage 8 daily automation workflow
S4 remediation
post-candidate PARTIAL remediation
JSONB SQL-NULL remediation
```

If remote `main` has moved, work from the latest remote head.

Return:

```text
REMOTE_MAIN_BEFORE=
REMEDIATION_BRANCH=
REMEDIATION_BASE=
```

---

# 5. Authorized code scope

Expected application files:

```text
backend/app/scanner/archive.py
backend/app/scanner/daily.py
backend/app/cli.py
```

Expected tests:

```text
backend/tests/test_stage4a_daily_pipeline.py
backend/tests/test_stage8_daily_automation_workflow.py
```

A narrowly necessary additional existing test file is allowed only if declared before editing.

No workflow schedule change is expected.

No migration.

No dashboard change.

No scoring/candidate logic change.

Before edits, return:

```text
AUTHORIZED_FILES_PROPOSED:
- <file>: <reason>
```

If implementation requires broader semantic changes:

```text
REMEDIATION_RESULT=HOLD_SCOPE_EXPANSION_REQUIRED
```

---

# 6. R1 — one ticker lifecycle row per archive run

Fix the `NightwatchError` path in `backend/app/scanner/archive.py`.

Required invariant:

```text
UNIQUE (archive_run_id, ticker)
→ exactly one lifecycle row for a ticker in one archive run
```

When a chain request fails after the ticker RUNNING row already exists:

```text
update/finalize the existing ticker row
DO NOT insert a second ticker row
```

The existing row must truthfully reflect the outcome under current status semantics.

Do not delete/recreate the row.

Do not silently overwrite useful provenance.

---

# 7. R2 — transaction recovery must preserve the original failure

After any database exception that invalidates the current transaction:

```text
rollback before any further persistence/cleanup operation
```

Required:

```text
original failure is not replaced by PendingRollbackError
advisory lock cleanup does not mask the original error
session is reusable after rollback
subsequent independent orchestration work does not inherit a poisoned transaction
```

In `backend/app/scanner/daily.py`, after a caught Daily OI exception:

```text
restore transaction/session usability before any independent Radar operation
```

Radar must not be reported as an independent failure merely because Daily OI poisoned the shared session.

Do not change the accepted rule that Radar and Daily OI are distinct evidence families.

---

# 8. R3 — expired vs active chain-404 behavior

Implement/tests must cover both.

## Expired 404 regression

Synthetic example:

```text
effective NY market date = 2026-08-25
OI surface includes expiry = 2026-08-24
chain_snapshot(2026-08-24) -> 404 NOT_FOUND
other active expiries -> 200
```

Required proof:

```text
duplicate ticker insert = NO
session poisoning = NO
expired expiry OI surface preserved = YES
expired expiry contract rows fabricated = NO
OI zero fabricated = NO
remaining expiries continue = YES
active-chain completeness can still become eligible if all required active expiries succeed = YES
```

The exact persisted status/reason must be documented from the actual implementation.

## Active/future 404 regression

Synthetic example:

```text
effective NY market date = 2026-08-25
active expiry = 2026-08-28
chain_snapshot(2026-08-28) -> 404 NOT_FOUND
```

Required proof:

```text
duplicate ticker insert = NO
session poisoning = NO
zero fabricated = NO
active-chain missing truthfully represented = YES
active-chain completeness falsely promoted = NO
evening readiness remains fail-closed if this evidence is required = YES
```

No paid retry loop.

---

# 9. R4 — parent usage counters must not falsely report zero

The diagnostic proved:

```text
authoritative attempts=2
authoritative paid units=1
parent counters=0/0
```

Fix only as narrowly as the current architecture permits.

Required invariant:

```text
parent DailyCollectionRun/summary must not report known vendor attempts/paid units as zero merely because the child path raised before returning its normal summary
```

Acceptable approaches:

```text
preserve child counters through handled failure
or
aggregate from authoritative in-process audit/result state already available
```

Do not issue extra API requests to calculate counters.

Do not invent counts.

If exact counters cannot be recovered safely on a particular exception path:

```text
use truthful UNKNOWN/UNRESOLVED semantics if the model permits
```

rather than false zero.

Return:

```text
PARENT_COUNTER_TRUTHFULNESS_FIXED=YES/NO
```

If no model representation can distinguish unknown from zero without schema change, explain the limitation; do not create a migration.

---

# 10. R5 — false-green CLI exit semantics

Fix:

```text
python -m app.cli archive-mag7-daily ...
```

Current defect:

```text
summary.status=FAILED
→ exit code 0
```

Required process semantics:

```text
true success / COMPLETE -> 0
NO_NEW_DATA if accepted as non-error -> 0
explicit legitimate scheduler skip -> 0

blocking FAILED -> non-zero
blocking PARTIAL -> non-zero
```

Use stable explicit exit codes consistent with current CLI conventions.

Do not make ordinary non-trading/session-window skips red.

Workflow shell must naturally show blocking archive failure as red without custom shell hacks.

Return:

```text
CLI_FALSE_GREEN_FIXED=YES/NO
FAILED_EXIT_CODE=
PARTIAL_EXIT_CODE=
LEGITIMATE_SKIP_EXIT_CODE=
```

---

# 11. Preserve evening safety gate

Do not weaken the accepted evening readiness gate.

Required:

```text
missing required active Radar/Daily OI evidence
→ no vNext MAG7 scan
→ no paid scan fanout
```

The only refinement permitted is that **already-expired chain 404s must not make otherwise complete active-chain coverage look missing**.

Active expiry missing evidence must remain fail-closed.

---

# 12. Historical rows

Do not repair/delete/rewrite the failed 2026-08-25 run.

Keep:

```text
daily_run_id=c43274fd-cb86-4004-9f1c-b88ddc33dd6a
```

as audit evidence.

No manual status corrections.

No backfill.

Return:

```text
HISTORICAL_REPAIR_PERFORMED=NO
```

---

# 13. Zero-paid verification

All verification must be local/offline/mocked.

Required focused cases:

```text
1. OI surface 200 + expired chain 404 + active chains 200
2. OI surface 200 + active chain 404
3. vendor error does not duplicate ticker lifecycle row
4. transaction rollback leaves session reusable
5. Radar not cascade-failed by poisoned session
6. original failure not masked by PendingRollbackError
7. parent counters truthful on handled failure
8. FAILED summary -> non-zero CLI
9. PARTIAL summary -> non-zero CLI
10. legitimate scheduler skip -> zero CLI
11. evening readiness still blocks missing active evidence
12. no automatic paid retry
```

Run:

```text
focused remediation tests
Stage 4A daily pipeline tests
Stage 8 daily automation workflow tests
Stage 4B regressions
Stage 5 candidate persistence tests
Stage 6 baseline tests
full backend suite
Ruff
Alembic single-head check
git diff --check
secret scan
workflow static validation
```

No Nightwatch.
No Supabase writes.
No workflow dispatch.

---

# 14. Pre-deployment acceptance fields

Before GitHub push, require:

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

If any blocking field is NO, do not push.

---

# 15. GitHub deployment

After all local gates pass:

1. Refetch `origin/main`.
2. If remote moved, integrate/rebase only with normal non-destructive semantics on the local fix branch.
3. No semantic conflict guessing.
4. Push normally to `main` if allowed; otherwise use a protected-branch PR without bypassing protection.
5. Never force push.

After deployment, verify:

```text
origin/main contains remediation commit
phase2a-daily-archive.yml remains active
06:30 ET schedule unchanged
16:30 ET schedule unchanged
Dealer GEX workflow unchanged
rollover experiment workflow unchanged
```

Do NOT dispatch any workflow.

---

# 16. Runtime proof remains natural

After successful deployment:

```text
FIRST_SCHEDULED_RUNTIME_REPROOF_COMPLETE=NO
```

Do not manually rerun the failed morning job.

Do not manually trigger MAG7.

The next natural scheduled cycle is the runtime proof.

Future runtime proof must verify:

```text
morning Daily OI does not duplicate ticker row
expired 404, if encountered, is handled truthfully
active expiry gaps remain fail-closed
Radar can run on a healthy session
GitHub status is truthful
parent usage counters are truthful
evening source readiness passes only when evidence is eligible
exactly one scheduled vNext scan if ready
one baseline per candidate
O1/O4/O6 advance
```

---

# 17. Remediation result states

Use exactly one:

```text
REMEDIATION_RESULT=PASS_DEPLOYED_WAITING_NATURAL_RUNTIME_PROOF

REMEDIATION_RESULT=PASS_IMPLEMENTED_PENDING_DEPLOYMENT

REMEDIATION_RESULT=HOLD_PACKAGE_CONFLICT
REMEDIATION_RESULT=HOLD_CODE_STATE
REMEDIATION_RESULT=HOLD_SCHEMA_SEMANTIC_GAP
REMEDIATION_RESULT=HOLD_SCOPE_EXPANSION_REQUIRED
REMEDIATION_RESULT=HOLD_INTEGRATION_CONFLICT
REMEDIATION_RESULT=HOLD_REMOTE_MOVED

REMEDIATION_RESULT=FAIL_TESTS
REMEDIATION_RESULT=FAIL_GITHUB_ACTIVATION_VERIFICATION
```

---

# 18. Evidence report

Primary:

```text
F:\options-anomaly-scanner-stage8-runtime-remediation\docs\evidence\stage8\NIGHTWATCH_VNEXT_STAGE8_SCHEDULED_RUNTIME_REMEDIATION_REPORT_20260826.md
```

If a different clean remediation worktree path is used, report the exact actual primary path.

Canonical byte-identical backup:

```text
F:\options-anomaly-scanner\docs\evidence\NIGHTWATCH_VNEXT_STAGE8_SCHEDULED_RUNTIME_REMEDIATION_REPORT_20260826.md
```

Verify SHA-256 for both.

Never overwrite differing same-name canonical evidence.

---

# 19. Required final fields

```text
REMEDIATION_RESULT=
FOUNDER_AUTHORIZATION=STAGE8_SCHEDULED_RUNTIME_REMEDIATION_20260826

REMOTE_MAIN_BEFORE=
REMEDIATION_BRANCH=
REMEDIATION_BASE=
REMEDIATION_COMMIT=
REMOTE_MAIN_AFTER=

DUPLICATE_TICKER_INSERT_FIXED=
TRANSACTION_RECOVERY_FIXED=
PENDING_ROLLBACK_MASKING_FIXED=

EXPIRED_CHAIN_404_CLASSIFICATION_IMPLEMENTED=
EXPIRED_CHAIN_404_PERSISTED_SEMANTICS=
ACTIVE_CHAIN_404_CLASSIFICATION_IMPLEMENTED=
ACTIVE_CHAIN_404_PERSISTED_SEMANTICS=

EXPIRED_404_FABRICATES_ZERO=NO
ACTIVE_404_FABRICATES_ZERO=NO
EXPIRED_404_BLOCKS_OTHER_EXPIRIES=
ACTIVE_404_FALSELY_MARKS_COMPLETE=NO

PARENT_COUNTER_TRUTHFULNESS_FIXED=

CLI_FALSE_GREEN_FIXED=
FAILED_EXIT_CODE=
PARTIAL_EXIT_CODE=
LEGITIMATE_SKIP_EXIT_CODE=

EVENING_READINESS_GATE_WEAKENED=NO
ACTIVE_MISSING_EVIDENCE_FAIL_CLOSED=YES

MIGRATION_REQUIRED=NO
HISTORICAL_REPAIR_PERFORMED=NO

APPLICATION_FILES_CHANGED=
TEST_FILES_CHANGED=
WORKFLOW_FILES_CHANGED=
SCHEMA_FILES_CHANGED=0

FOCUSED_TESTS=
FULL_BACKEND_TESTS=
RUFF=
ALEMBIC_HEAD=
ALEMBIC_SINGLE_HEAD=
GIT_DIFF_CHECK=
SECRET_SCAN=
ALL_TESTS_PASS=

NIGHTWATCH_REQUESTS_THIS_TASK=0
PAID_UNITS_THIS_TASK=0
WORKFLOW_DISPATCHES_THIS_TASK=0
REMOTE_APPLICATION_DATA_WRITES_THIS_TASK=0
REMOTE_SCHEMA_WRITES_THIS_TASK=0

COMMITS_CREATED=
PUSHES=
PRS_CREATED=
MERGES=

PHASE2A_DAILY_WORKFLOW_ACTIVE_ON_DEFAULT=
RADAR_OI_SCHEDULE_UNCHANGED=
ACTIVITY_OBSERVATION_SCHEDULE_UNCHANGED=

FIRST_SCHEDULED_RUNTIME_REPROOF_COMPLETE=NO

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

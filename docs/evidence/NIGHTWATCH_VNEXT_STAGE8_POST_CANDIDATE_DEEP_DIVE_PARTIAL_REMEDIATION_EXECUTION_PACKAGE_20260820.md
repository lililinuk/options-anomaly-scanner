# Nightwatch vNext — Stage 8 Post-Candidate Deep-Dive PARTIAL Remediation — Execution Package

**Date:** 2026-08-20  
**Purpose:** Fix the confirmed vNext defect where missing post-candidate Deep-Dive structure archives incorrectly promote the whole scan to `PARTIAL` and block ProductCandidate materialization.  
**Worktree:** `F:\options-anomaly-scanner-stage8`  
**Branch:** `vnext/stage8-mag7-observation`  
**Base HEAD:** `3a63eaa1b9069d34199704fe31ac6466e8929d7d`

## 0. Confirmed root cause

The second controlled MAG7 run:

```text
SECOND_SCAN_RUN_ID=e9267160-503a-41c7-9bb1-8cc2b2e3d8c6
SECOND_SCAN_STATUS=PARTIAL
```

completed all persisted scanner stages through S6.

The confirmed cause was:

```text
AMZN selected expiry 2026-08-21 missing complete daily-chain archive
AMZN selected expiry 2026-08-28 missing complete daily-chain archive
```

Inherited `v11._structure_scan()` set:

```text
self.partial=True
```

because complete daily-chain structure data was unavailable for those Deep-Dive expiries.

However, accepted vNext Phase 2A projection still produced:

```text
PROJECTED_PRODUCT_CANDIDATES=7
PROJECTED_ACTIVE_ANOMALIES=82
PROJECTED_QUALIFYING_TRIGGERS=82
```

This is a confirmed architecture violation:

```text
post-candidate Deep-Dive availability
must not suppress ProductCandidate existence/materialization
```

Diagnostic result:

```text
PARTIAL_DIAGNOSTIC_RESULT=ROOT_CAUSE_CONFIRMED
PARTIAL_CLASSIFICATION=BUG_PARTIAL_FROM_OPTIONAL_OR_POST_CANDIDATE_LAYER
PARTIAL_SEMANTICALLY_JUSTIFIED=NO
CANDIDATE_MATERIALIZATION_CALLED=NO
PARTIAL_STATUS_BLOCKS_MATERIALIZATION=YES
IF_RUN_IS_PARTIAL_BUT_PHASE2A_HAS_VALID_QUALIFYING_CANDIDATES_SHOULD_MATERIALIZE=YES
REMEDIATION_REQUIRED=YES
MIGRATION_REQUIRED=NO
HISTORICAL_DATA_REPAIR_REQUIRED=NO
```

## 1. Canonical evidence root

Read completely from:

```text
F:\options-anomaly-scanner\docs\evidence
```

At minimum:

```text
F:\options-anomaly-scanner\docs\evidence\NIGHTWATCH_SCANNER_VNEXT_INTEGRATED_SPEC_PROMPT_20260817(1).md
F:\options-anomaly-scanner\docs\evidence\NIGHTWATCH_VNEXT_STAGE4B_PHASE2A_VNEXT_CODEX_EXECUTION_PACKAGE_20260818.md
F:\options-anomaly-scanner\docs\evidence\NIGHTWATCH_VNEXT_STAGE5_PRODUCT_CANDIDATE_PERSISTENCE_COMPLETION_REPORT_20260818.md
F:\options-anomaly-scanner\docs\evidence\NIGHTWATCH_VNEXT_STAGE8_S4_STAGE_IDENTIFIER_REMEDIATION_REPORT_20260820.md
F:\options-anomaly-scanner\docs\evidence\NIGHTWATCH_VNEXT_SECOND_CONTROLLED_LIVE_MAG7_OBSERVATION_REPORT_20260820.md
F:\options-anomaly-scanner\docs\evidence\NIGHTWATCH_VNEXT_STAGE8_PARTIAL_TERMINAL_STATE_DIAGNOSTIC_REPORT_20260820.md
```

If this execution package is attached and absent from canonical evidence, preserve it byte-for-byte as:

```text
F:\options-anomaly-scanner\docs\evidence\NIGHTWATCH_VNEXT_STAGE8_POST_CANDIDATE_DEEP_DIVE_PARTIAL_REMEDIATION_EXECUTION_PACKAGE_20260820.md
```

If same filename exists with different content, do not overwrite; return `HOLD_PACKAGE_CONFLICT`.

## 2. Authorization boundary

Authorized application/test files:

```text
backend/app/scanner/v13.py
backend/tests/test_stage4b_phase2a_vnext.py
```

You may inspect additional files read-only.

Not authorized:

```text
Nightwatch request
MAG7 scan
Phase2B refresh
Dealer/GEX live call
remote DB write
migration
historical data repair
workflow/scheduler change
unrelated refactor
commit/push/PR/merge
```

Expected:

```text
NIGHTWATCH_REQUESTS=0
PAID_UNITS=0
REMOTE_DB_WRITES=0
MIGRATION_CREATED=NO
```

## 3. Required semantic fix

Implement the narrowest vNext-only fix so that:

```text
missing COMPLETE_DAILY_CHAIN_ARCHIVE_FOR_STRUCTURE_DEEP_DIVE
```

for selected post-candidate Deep-Dive expiries does **not** by itself make the overall vNext run `PARTIAL`.

The accepted semantics are:

```text
ProductCandidate existence is determined by active Phase 2A discovery:
- RADAR_EVENT
- EXPIRY_ACTIVITY
- CONTRACT_PERSISTENCE

Structure / Neighbor Strike / Cluster are post-candidate Deep-Dive context.

Deep-Dive budget or Deep-Dive source availability must not suppress ProductCandidate existence.
```

### Critical guardrail

Do **not** globally disable `PARTIAL`.

Do **not** change inherited v11 behavior for legacy scanner versions.

Do **not** clear legitimate pre-existing partial state caused by genuinely required/core data.

The fix must distinguish:

```text
partial state already present before vNext structure Deep-Dive
```

from:

```text
partial state introduced solely by optional/post-candidate structure Deep-Dive unavailability
```

Required behavior:

```text
If partial was already true before structure:
    preserve PARTIAL.

If structure Deep-Dive alone introduces partial because complete daily-chain archive is missing:
    preserve the structure/deep-dive availability evidence truthfully,
    but do not promote the whole vNext run to PARTIAL solely for that reason.

If another independent legitimate partial condition exists:
    preserve PARTIAL.
```

Do not fabricate structure observations where archive data is absent.

Missing remains missing.

## 4. Preserve truthful Deep-Dive availability

The remediation must not turn missing structure data into success.

For affected expiries such as:

```text
AMZN 2026-08-21
AMZN 2026-08-28
```

the persisted/derived Deep-Dive state must continue to indicate unavailable/incomplete structure evidence according to existing vocabulary.

Only the **run-level terminal status impact** is being corrected.

Return:

```text
DEEP_DIVE_MISSING_STATE_PRESERVED=YES/NO
MISSING_STRUCTURE_FABRICATED=NO
```

## 5. Candidate materialization requirement

With the diagnostic fixture/state equivalent to the second controlled run:

```text
PROJECTED_PRODUCT_CANDIDATES=7
PROJECTED_QUALIFYING_TRIGGERS=82
```

the remediated vNext flow must reach the accepted successful materialization path when no other legitimate run-level blocker exists.

Regression must prove:

```text
ProductCandidate existence is not suppressed by missing post-candidate structure archive
```

Do not manually insert candidates.

Use normal production projection/materialization logic in tests.

## 6. Required regressions

Add focused regressions covering at least:

### Case A — confirmed defect

```text
core Phase 2A discovery valid
valid ProductCandidates exist
selected Deep-Dive expiry lacks complete daily-chain archive
```

Expected:

```text
run-level PARTIAL not caused solely by this Deep-Dive condition
candidate materialization remains eligible
missing structure remains truthfully unavailable
```

### Case B — legitimate pre-existing PARTIAL

Arrange a genuine required/core-data partial condition before structure.

Expected:

```text
run remains PARTIAL
vNext structure remediation does not clear the legitimate partial
```

### Case C — candidate-before-budget invariant

Preserve existing proof that:

```text
7 qualifying ProductCandidates can exist
while only 4 tickers receive Deep-Dive budget
```

and Deep-Dive selection/availability does not suppress candidate identity.

### Case D — prior S4 identifier fix remains intact

Prove active identifier remains:

```text
S4_VNEXT_DEEP_BUDGET_SELECTION
```

and length <=32.

## 7. Verification

Run:

```text
focused remediation tests
Stage 4B focused tests
Stage 5 regressions
Stage 6 regressions
Stage 7 relevant backend regressions
full backend suite
Ruff
Alembic heads
git diff --check
```

Expected:

```text
ALEMBIC_HEAD=20260818_0017
MIGRATION_CREATED=NO
```

No live scan.

No Nightwatch call.

## 8. Historical runs remain immutable

Do not mutate either controlled run:

```text
FIRST_FAILED_RUN_ID=090359ad-9d76-49b9-8902-f28ac54a1d1b
FIRST_FAILED_RUN_STATUS=FAILED

SECOND_SCAN_RUN_ID=e9267160-503a-41c7-9bb1-8cc2b2e3d8c6
SECOND_SCAN_RUN_STATUS=PARTIAL
```

They are historical evidence and must remain truthful.

Return:

```text
FIRST_FAILED_RUN_MUTATED=NO
SECOND_PARTIAL_RUN_MUTATED=NO
```

## 9. Evidence report — primary + canonical backup

Create primary report:

```text
F:\options-anomaly-scanner-stage8\docs\evidence\stage8\NIGHTWATCH_VNEXT_STAGE8_POST_CANDIDATE_DEEP_DIVE_PARTIAL_REMEDIATION_REPORT_20260820.md
```

Also save byte-identical canonical backup:

```text
F:\options-anomaly-scanner\docs\evidence\NIGHTWATCH_VNEXT_STAGE8_POST_CANDIDATE_DEEP_DIVE_PARTIAL_REMEDIATION_REPORT_20260820.md
```

Requirements:

- primary and canonical report must be byte-identical;
- verify SHA-256 for both;
- if canonical target already has identical bytes, keep it;
- if same filename exists with different content, do not overwrite;
- return `HOLD_REPORT_CONFLICT` on conflict.

## 10. Final result

Use exactly one:

```text
STAGE8_POST_CANDIDATE_PARTIAL_REMEDIATION_RESULT=PASS
STAGE8_POST_CANDIDATE_PARTIAL_REMEDIATION_RESULT=FAIL
STAGE8_POST_CANDIDATE_PARTIAL_REMEDIATION_RESULT=HOLD
```

Return:

```text
STAGE8_POST_CANDIDATE_PARTIAL_REMEDIATION_RESULT=

ROOT_CAUSE_ADDRESSED=YES/NO

RUN_LEVEL_PARTIAL_FROM_POST_CANDIDATE_DEEP_DIVE_ONLY=BLOCKED/NOT_BLOCKED
LEGITIMATE_PREEXISTING_PARTIAL_PRESERVED=YES/NO

DEEP_DIVE_MISSING_STATE_PRESERVED=YES/NO
MISSING_STRUCTURE_FABRICATED=NO

CANDIDATE_MATERIALIZATION_ELIGIBILITY_PRESERVED=YES/NO
CANDIDATE_BEFORE_BUDGET_INVARIANT_PRESERVED=YES/NO

S4_IDENTIFIER_REMEDIATION_PRESERVED=YES/NO

APPLICATION_CODE_CHANGES=
TEST_CODE_CHANGES=
MIGRATION_CREATED=NO
ALEMBIC_HEAD=20260818_0017

FIRST_FAILED_RUN_MUTATED=NO
SECOND_PARTIAL_RUN_MUTATED=NO

NIGHTWATCH_REQUESTS=0
PAID_UNITS=0
REMOTE_DB_WRITES=0

WORKFLOW_CHANGES=0
SCHEDULER_CHANGES=0
COMMITS_CREATED=0
PUSHES=0
PRS_CREATED=0
MERGES=0

PRIMARY_REPORT_PATH=
CANONICAL_REPORT_PATH=
PRIMARY_REPORT_SHA256=
CANONICAL_REPORT_SHA256=
REPORT_BACKUP_BYTE_IDENTICAL=YES/NO

THIRD_MAG7_SCAN_AUTHORIZED=NO
STAGE8_OBSERVATION_RESUME_READY=YES/NO
STAGE9_READY=NO
NEXT_AUTHORIZED_STAGE=NONE
```

If PASS:

```text
STAGE8_OBSERVATION_RESUME_READY=YES
```

means only that the code is ready for a future separately authorized controlled observation.

Do not run it automatically.

STOP.

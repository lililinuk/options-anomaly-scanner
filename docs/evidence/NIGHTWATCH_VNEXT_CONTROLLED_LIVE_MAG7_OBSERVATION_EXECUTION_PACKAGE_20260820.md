# Nightwatch vNext — Controlled Live MAG7 Observation — Execution Package

**Date:** 2026-08-20
**Authorization:** Founder explicitly authorized one Controlled MAG7 Observation.
**Worktree:** `F:\options-anomaly-scanner-stage8`
**Branch:** `vnext/stage8-mag7-observation`
**HEAD/base:** `3a63eaa1b9069d34199704fe31ac6466e8929d7d`
**Runtime schema:** `20260818_0017`

## 1. Authorization

```text
FOUNDER_AUTHORIZATION=ONE_CONTROLLED_MAG7_OBSERVATION_20260820
MAG7_SCAN_INVOCATIONS_AUTHORIZED=1
UNIVERSE=MAG7_ONLY
EXPECTED_PAID_COST≈14
HARD_PAID_UNIT_CAP=20
PHASE2B_PAID_REFRESH_AUTHORIZED=NO
DEALER_GEX_LIVE_CALL_AUTHORIZED=NO
SECOND_MAG7_SCAN_AUTHORIZED=NO
```

Authorization is exhausted after the first MAG7 scan invocation, whether it succeeds, returns zero candidates, or fails. No automatic second scan.

## 2. Canonical evidence

Canonical root:

```text
F:\options-anomaly-scanner\docs\evidence
```

Preserve this exact package at:

```text
F:\options-anomaly-scanner\docs\evidence\NIGHTWATCH_VNEXT_CONTROLLED_LIVE_MAG7_OBSERVATION_EXECUTION_PACKAGE_20260820.md
```

If absent and this exact file is attached in the current thread, copy it byte-for-byte there. If an existing target has a different SHA-256, return `HOLD_PACKAGE_CONFLICT` and stop.

Read completely from canonical paths:

```text
F:\options-anomaly-scanner\docs\evidence\NIGHTWATCH_VNEXT_CANONICAL_EVIDENCE_MANIFEST.md
F:\options-anomaly-scanner\docs\evidence\NIGHTWATCH_SCANNER_VNEXT_INTEGRATED_SPEC_PROMPT_20260817(1).md
F:\options-anomaly-scanner\docs\evidence\NIGHTWATCH_VNEXT_STAGE5_PRODUCT_CANDIDATE_PERSISTENCE_COMPLETION_REPORT_20260818.md
F:\options-anomaly-scanner\docs\evidence\NIGHTWATCH_VNEXT_STAGE6_PHASE2B_BALANCED_MODEL_COMPLETION_REPORT_20260818.md
F:\options-anomaly-scanner\docs\evidence\NIGHTWATCH_VNEXT_STAGE6_BASELINE_CUTOFF_REMEDIATION_PASS_20260820.md
F:\options-anomaly-scanner\docs\evidence\NIGHTWATCH_VNEXT_STAGE7_CANDIDATE_FIRST_DASHBOARD_COMPLETION_REPORT_20260819.md
F:\options-anomaly-scanner\docs\evidence\NIGHTWATCH_VNEXT_STAGE8_MAG7_OBSERVATION_EXECUTION_PACKAGE_20260820.md
F:\options-anomaly-scanner\docs\evidence\NIGHTWATCH_VNEXT_STAGE8_RUNTIME_DEPLOYMENT_GATE_EXECUTION_PACKAGE_20260820.md
```

Also read:

```text
F:\options-anomaly-scanner-stage8\docs\evidence\stage8\NIGHTWATCH_VNEXT_STAGE8_RUNTIME_DEPLOYMENT_GATE_REPORT_20260820.md
```

Do not ask the Founder to re-upload files already present there.

## 3. Runtime preflight

Read-only verify:

```text
REMOTE_ALEMBIC_HEAD=20260818_0017
PRODUCT_CANDIDATE_TABLE_PRESENT=YES
PRODUCT_CANDIDATE_TRIGGER_TABLE_PRESENT=YES
PRODUCT_CANDIDATE_CONTEXT_TABLE_PRESENT=YES
ANOMALY_CONTEXT_DETAIL_TABLE_PRESENT=YES
```

If not, return:

```text
CONTROLLED_OBSERVATION_RESULT=HOLD_RUNTIME_NOT_READY
```

Do not migrate, stamp, repair, or backfill.

## 4. No implementation changes

Do not modify application code, tests, migrations, thresholds, scoring, candidate rules, Stage 5/6 semantics, dashboard, workflows, schedulers, retry logic, environment configuration, or universe.

Only Stage 8 evidence files may be created.

## 5. Cost preflight

Before any Nightwatch call, record authoritative local usage/quota facts if available:

```text
PAID_UNITS_BEFORE=
QUOTA_REMAINING_BEFORE=
```

Unknown stays `UNRESOLVED`.

Inspect the existing unmodified MAG7 path and current configured retry/fan-out behavior. Prove one invocation is bounded at or below:

```text
HARD_PAID_UNIT_CAP=20
```

Return:

```text
MAG7_COST_BOUND_PROVEN=YES/NO
MAX_CONFIGURED_PAID_UNITS_FOR_ONE_SCAN=
```

If not provable:

```text
CONTROLLED_OBSERVATION_RESULT=HOLD_BUDGET_BOUND_UNPROVEN
```

Stop before any paid call. Do not change retry logic to make it fit.

## 6. Run exactly one MAG7 scan

After all preflight gates pass, execute exactly one existing production MAG7 scan invocation using the accepted MAG7 universe and accepted thresholds.

No test fixture.
No threshold override.
No universe expansion.
No second scan.
No manual seed.

Record:

```text
AUTHORIZED_SCAN_INVOCATIONS=1
ACTUAL_SCAN_INVOCATIONS=
SCAN_RUN_ID=
SCAN_STARTED_AT=
SCAN_COMPLETED_AT=
SCAN_STATUS=
```

Truthfully preserve `SUCCESS_WITH_CANDIDATES`, `SUCCESS_NO_CANDIDATE`, or `FAILED`.

If failed: do not retry.

## 7. Authorized application writes

The normal application-data writes naturally produced by this one unmodified MAG7 scan are authorized, including the existing scan state/evidence and Stage 5 ProductCandidate/ProductCandidateTrigger materialization.

No manual SQL DML.
No historical repair.
No cross-run candidate merge.

## 8. Candidate verification

If candidates exist, read back only candidates linked to the new ScanRun.

For each report:

```text
ProductCandidate.id
ticker
candidate_first_knowledge_at
materialization rule version/hash
trigger count
qualifying trigger count
supporting trigger count
trigger families
```

Return:

```text
NEW_PRODUCT_CANDIDATE_COUNT=
NEW_PRODUCT_CANDIDATE_TRIGGER_COUNT=
VALID_CANDIDATE_OMISSION_FOUND=YES/NO
DEEP_DIVE_BUDGET_SUPPRESSION_FOUND=YES/NO
```

If scan is successful with zero candidates, expected `NEW_PRODUCT_CANDIDATE_COUNT=0`. Do not manufacture candidates.

## 9. Create frozen baseline only

For every new ProductCandidate from this one scan, create exactly one accepted Stage 6:

```text
FIRST_KNOWLEDGE_BASELINE
```

This step is authorized because baseline creation must use zero paid vendor refresh calls.

Required:

```text
evidence cutoff = candidate_first_knowledge_at
```

Do NOT run `REFRESH`.

Do NOT call the four ticker-level paid refresh sources.

Do NOT make live Dealer/GEX calls.

If a context source is unavailable by first knowledge, persist truthful missing/partial state.

If baseline creation fails for any candidate, return:

```text
CONTROLLED_OBSERVATION_RESULT=FAIL_BASELINE_CREATION
```

Do not run another MAG7 scan or manually repair the baseline.

## 10. Baseline integrity

Verify each baseline:

```text
evaluation_kind=FIRST_KNOWLEDGE_BASELINE
product_candidate_id matches
context_evaluated_at >= candidate_first_knowledge_at
trigger/detail set matches candidate trigger set
```

And verify authoritative source receipt/capture/as-of times do not exceed `candidate_first_knowledge_at`.

B1 OHLC:
- payload/source knowable by cutoff;
- bar `trading_date` not after cutoff New York trading date;
- malformed/missing bar date fails closed.

Chain:
- receipt <= cutoff;
- vendor observed / vendor OI as-of <= cutoff when known;
- quote_as_of <= cutoff when known.

Dealer/GEX:
- captured_at <= cutoff;
- vendor_observed_at <= cutoff.

Return:

```text
BASELINE_COUNT=
BASELINE_LOOKAHEAD_FOUND=YES/NO
BASELINE_TRIGGER_SET_DRIFT_FOUND=YES/NO
BASELINE_SOURCE_TIME_VIOLATION_FOUND=YES/NO
```

Any YES => `FAIL_BASELINE_INTEGRITY`. Do not fix it.

## 11. Explicitly forbidden refresh/live GEX

Verify:

```text
PHASE2B_REFRESH_CALLS=0
DEALER_GEX_LIVE_CALLS=0
DEALER_GEX_SOURCE=ARCHIVE_ONLY
```

## 12. Post-run cost

Record authoritative post-run facts:

```text
PAID_UNITS_AFTER=
QUOTA_REMAINING_AFTER=
OBSERVED_PAID_UNIT_DELTA=
```

Unknown stays `UNRESOLVED`.

If authoritative delta exceeds 20:

```text
CONTROLLED_OBSERVATION_RESULT=FAIL_COST_CAP_EXCEEDED
```

No second scan.

## 13. Runtime delta

Record before/after counts and exact rows attributable to this controlled observation:

```text
SCAN_RUN_ROWS_ADDED_BY_CONTROLLED_OBSERVATION=
PRODUCT_CANDIDATE_ROWS_ADDED_BY_CONTROLLED_OBSERVATION=
TRIGGER_ROWS_ADDED_BY_CONTROLLED_OBSERVATION=
BASELINE_CONTEXT_ROWS_ADDED_BY_CONTROLLED_OBSERVATION=
ANOMALY_DETAIL_ROWS_ADDED_BY_CONTROLLED_OBSERVATION=
```

Do not attribute unrelated concurrent rows to this run.

## 14. Result states

Use exactly one:

```text
CONTROLLED_OBSERVATION_RESULT=PASS_WITH_CANDIDATES
CONTROLLED_OBSERVATION_RESULT=PASS_NO_CANDIDATE
CONTROLLED_OBSERVATION_RESULT=FAIL_SCAN
CONTROLLED_OBSERVATION_RESULT=FAIL_BASELINE_CREATION
CONTROLLED_OBSERVATION_RESULT=FAIL_BASELINE_INTEGRITY
CONTROLLED_OBSERVATION_RESULT=FAIL_COST_CAP_EXCEEDED
CONTROLLED_OBSERVATION_RESULT=HOLD_RUNTIME_NOT_READY
CONTROLLED_OBSERVATION_RESULT=HOLD_BUDGET_BOUND_UNPROVEN
CONTROLLED_OBSERVATION_RESULT=HOLD_PACKAGE_CONFLICT
```

## 15. Evidence report

Create:

```text
F:\options-anomaly-scanner-stage8\docs\evidence\stage8\NIGHTWATCH_VNEXT_CONTROLLED_LIVE_MAG7_OBSERVATION_REPORT_20260820.md
```

Do not overwrite prior Stage 8 reports.

## 16. Final fields

Return:

```text
CONTROLLED_OBSERVATION_RESULT=
FOUNDER_AUTHORIZATION=ONE_CONTROLLED_MAG7_OBSERVATION_20260820

AUTHORIZED_SCAN_INVOCATIONS=1
ACTUAL_SCAN_INVOCATIONS=

SCAN_RUN_ID=
SCAN_STATUS=
SCAN_STARTED_AT=
SCAN_COMPLETED_AT=

MAG7_COST_BOUND_PROVEN=
MAX_CONFIGURED_PAID_UNITS_FOR_ONE_SCAN=

PAID_UNITS_BEFORE=
PAID_UNITS_AFTER=
OBSERVED_PAID_UNIT_DELTA=
QUOTA_REMAINING_BEFORE=
QUOTA_REMAINING_AFTER=

NEW_PRODUCT_CANDIDATE_COUNT=
NEW_PRODUCT_CANDIDATE_TRIGGER_COUNT=

BASELINE_COUNT=
BASELINE_LOOKAHEAD_FOUND=
BASELINE_TRIGGER_SET_DRIFT_FOUND=
BASELINE_SOURCE_TIME_VIOLATION_FOUND=

VALID_CANDIDATE_OMISSION_FOUND=
DEEP_DIVE_BUDGET_SUPPRESSION_FOUND=

PHASE2B_REFRESH_CALLS=0
DEALER_GEX_LIVE_CALLS=0

REMOTE_ALEMBIC_HEAD=20260818_0017
REMOTE_MIGRATIONS_RUN=0
```

Authorization ledger:

```text
APPLICATION_CODE_CHANGES=0
TEST_CODE_CHANGES=0
MIGRATION_FILES_CHANGED=0
WORKFLOW_CHANGES=0
SCHEDULER_CHANGES=0

MAG7_SCAN_INVOCATIONS=
NIGHTWATCH_REQUESTS=
PAID_UNITS=

REMOTE_DB_SCHEMA_WRITES=0
REMOTE_APPLICATION_DATA_WRITES=AUTHORIZED_CONTROLLED_OBSERVATION_ONLY

COMMITS_CREATED=0
PUSHES=0
PRS_CREATED=0
MERGES=0

STAGE8_OBSERVATION_RESUME_READY=YES/NO
STAGE9_READY=NO
NEXT_AUTHORIZED_STAGE=NONE
```

Do not automatically resume the broader Stage 8 observation. Do not start Stage 9. STOP.

## 17. Carried ledger

Preserve:

```text
CURRENT_TRIGGER_FRESHNESS_MODE=CALIBRATION_REQUIRED
RADAR_OI_SCHEDULE_ACTIVATION=PENDING_ROLLOVER_EVIDENCE
CROSS_RUN_CANDIDATE_LIFECYCLE=DEFERRED_NO_AUTO_MERGE
IV_RANK_CORE_ELIGIBILITY=WITHHOLD_PENDING_PROVENANCE
ISOLATED_POSTGRES_RUNTIME_VERIFIED=NO
N1_HISTORICAL_RUNTIME_DISTRIBUTION_VERIFIED=NO
```

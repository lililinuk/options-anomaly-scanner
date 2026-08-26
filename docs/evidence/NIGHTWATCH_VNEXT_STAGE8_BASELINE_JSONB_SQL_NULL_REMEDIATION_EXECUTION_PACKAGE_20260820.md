# Nightwatch vNext — Stage 8 Baseline JSONB SQL-NULL Remediation — Execution Package

**Date:** 2026-08-20  
**Purpose:** Fix the confirmed Stage 6 baseline persistence defect where Python `None` is bound as JSONB `null` instead of SQL `NULL`, violating the mutually exclusive anomaly payload check constraint.  
**Worktree:** `F:\options-anomaly-scanner-stage8`  
**Branch:** `vnext/stage8-mag7-observation`

---

# 0. Confirmed root cause

The third controlled MAG7 scan is already a valid successful scan:

```text
THIRD_SCAN_RUN_ID=2c71e5bb-9334-4806-a195-0f8768d2d0f2
THIRD_SCAN_STATUS=COMPLETE

PRODUCT_CANDIDATES=7
PRODUCT_CANDIDATE_TRIGGERS=82
```

Baseline creation failed atomically with:

```text
BASELINE_DIAGNOSTIC_RESULT=ROOT_CAUSE_CONFIRMED
BASELINE_INTEGRITYERROR_ROOT_CAUSE_IDENTIFIED=YES

FAILING_CANDIDATE_TICKER=AAPL
FAILING_FUNCTION=Stage6BalancedContextService._persist_evaluation detail INSERT/autoflush
TARGET_TABLE=anomaly_context_details
TARGET_COLUMN_OR_CONSTRAINT=ck_anomaly_context_details_anomaly_context_payload_matc_9467
DB_ERROR_CODE=23514

DEFECT_CLASS=ORM_DB_SCHEMA_MISMATCH_DEFECT
```

The exact semantic mismatch is:

```text
contract_snapshot / expiry_activity_recap
are nullable JSONB columns with mutually exclusive SQL IS NULL checks.

Current ORM:
JSONB(none_as_null=False default)

Therefore:
Python None -> JSONB null

But the DB check requires:
inactive payload -> SQL NULL
```

This makes both CONTRACT and EXPIRY detail rows invalid even though the Python object shape is correct.

The deployed DDL/check constraint is already the intended contract.

Therefore:

```text
MIGRATION_REQUIRED=NO
HISTORICAL_DATA_REPAIR_REQUIRED=NO
```

---

# 1. Canonical evidence root

Read from:

```text
F:\options-anomaly-scanner\docs\evidence
```

At minimum read completely:

```text
F:\options-anomaly-scanner\docs\evidence\NIGHTWATCH_SCANNER_VNEXT_INTEGRATED_SPEC_PROMPT_20260817(1).md

F:\options-anomaly-scanner\docs\evidence\NIGHTWATCH_VNEXT_STAGE6_PHASE2B_BALANCED_MODEL_CODEX_EXECUTION_PACKAGE_20260818.md

F:\options-anomaly-scanner\docs\evidence\NIGHTWATCH_VNEXT_STAGE6_PHASE2B_BALANCED_MODEL_COMPLETION_REPORT_20260818.md

F:\options-anomaly-scanner\docs\evidence\NIGHTWATCH_VNEXT_STAGE6_BASELINE_CUTOFF_REMEDIATION_PASS_20260820.md

F:\options-anomaly-scanner\docs\evidence\NIGHTWATCH_VNEXT_THIRD_CONTROLLED_LIVE_MAG7_OBSERVATION_REPORT_20260820.md

F:\options-anomaly-scanner\docs\evidence\NIGHTWATCH_VNEXT_STAGE8_FIRST_KNOWLEDGE_BASELINE_INTEGRITYERROR_DIAGNOSTIC_REPORT_20260820.md
```

If this execution package is attached and absent from canonical evidence, save it byte-for-byte as:

```text
F:\options-anomaly-scanner\docs\evidence\NIGHTWATCH_VNEXT_STAGE8_BASELINE_JSONB_SQL_NULL_REMEDIATION_EXECUTION_PACKAGE_20260820.md
```

If same filename exists with different bytes, do not overwrite. Return:

```text
STAGE8_BASELINE_JSONB_REMEDIATION_RESULT=HOLD_PACKAGE_CONFLICT
```

and STOP.

---

# 2. Authorized change scope

Authorized files:

```text
backend/app/db/models.py
backend/tests/test_stage6_balanced_context.py
```

You may inspect other files read-only.

Do not change anything else unless a genuinely unavoidable compile/test import adjustment is proven necessary. If so, STOP and report the required additional file instead of editing it.

Not authorized:

```text
MAG7 scan
Nightwatch request
Phase2B refresh
Dealer/GEX live call
remote DB INSERT/UPDATE/DELETE
remote baseline creation/retry
migration
historical repair
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

---

# 3. Required code fix

Apply the narrow ORM fix only to the two mutually exclusive nullable JSONB payload columns on `AnomalyContextDetail`:

```text
contract_snapshot
expiry_activity_recap
```

Required behavior:

```text
Python None -> SQL NULL
Python dict/object -> JSONB object
```

The intended implementation is equivalent to:

```python
JSONB(none_as_null=True)
```

for those two columns only, provided repository conventions support that exact form.

Do NOT:

```text
change the DB check constraint
drop or weaken the check
widen schema
make both payloads nullable in a way that bypasses entity matching
convert JSONB null to an application sentinel
change unrelated JSONB columns globally
```

The constraint must remain:

```text
CONTRACT:
  contract_snapshot IS NOT NULL
  expiry_activity_recap IS NULL

EXPIRY:
  contract_snapshot IS NULL
  expiry_activity_recap IS NOT NULL
```

---

# 4. Required regression coverage

Add executable tests proving both branches.

## Case A — CONTRACT detail

Construct a valid CONTRACT detail with:

```text
contract_snapshot = JSON object
expiry_activity_recap = Python None
```

Prove the PostgreSQL mapping/bind behavior is:

```text
contract_snapshot -> JSONB object
expiry_activity_recap -> SQL NULL
```

and therefore satisfies the deployed check semantics.

## Case B — EXPIRY detail

Construct a valid EXPIRY detail with:

```text
contract_snapshot = Python None
expiry_activity_recap = JSON object
```

Prove:

```text
contract_snapshot -> SQL NULL
expiry_activity_recap -> JSONB object
```

and therefore satisfies the deployed check semantics.

## Case C — invalid dual payload

Preserve the semantic contract that a detail cannot validly persist with both payloads active.

## Case D — invalid no payload

Preserve the semantic contract that a detail cannot validly persist with neither active payload.

## Case E — Stage 6 service regression

Exercise the accepted Stage 6 baseline detail builder/persistence shape sufficiently to prove the old `IntegrityError` condition is removed for both CONTRACT and EXPIRY details.

The test must specifically catch the JSON `null` versus SQL `NULL` distinction.

### Testing requirement

Existing SQLite/object-only tests are insufficient for this defect.

Prefer, in order:

1. existing isolated PostgreSQL test infrastructure if already available;
2. PostgreSQL dialect bind-processor assertions plus ORM/check-contract assertions;
3. local ephemeral PostgreSQL only if already supported by project tooling and requires no remote writes.

Do NOT write to the production Supabase database for testing.

Return:

```text
POSTGRES_NULL_BIND_BEHAVIOR_VERIFIED=YES/NO
CONTRACT_BRANCH_VERIFIED=YES/NO
EXPIRY_BRANCH_VERIFIED=YES/NO
```

---

# 5. Preserve all prior Stage 8 remediations

Verify no regression to:

```text
S4_VNEXT_DEEP_BUDGET_SELECTION
```

and:

```text
post-candidate Deep-Dive missing structure
must not alone promote the whole run to PARTIAL
```

Do not edit Stage 4B logic in this remediation.

Return:

```text
S4_IDENTIFIER_REMEDIATION_PRESERVED=YES/NO
POST_CANDIDATE_PARTIAL_REMEDIATION_PRESERVED=YES/NO
```

---

# 6. Preserve first-knowledge semantics

Do not alter:

```text
FIRST_KNOWLEDGE_BASELINE evidence cutoff
candidate_first_knowledge_at semantics
baseline selector cutoffs
source-first-received/vendor/local timestamp rules
```

The existing seven candidates remain reusable after this code fix because their immutable first-knowledge timestamps and historical source rows are already persisted.

This remediation does not create the baseline yet.

Return:

```text
FIRST_KNOWLEDGE_CUTOFF_LOGIC_CHANGED=NO
EXISTING_7_CANDIDATES_STILL_REUSABLE=YES/NO
```

---

# 7. Verification matrix

Run:

```text
focused new JSONB/SQL-NULL regression tests
full backend/tests/test_stage6_balanced_context.py
Stage 5 regressions
Stage 4B focused regressions
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

No vendor calls.

No runtime writes.

---

# 8. Historical runtime state remains immutable

Read-only verify:

```text
THIRD_SCAN_RUN_ID=2c71e5bb-9334-4806-a195-0f8768d2d0f2
THIRD_SCAN_STATUS=COMPLETE

PRODUCT_CANDIDATES=7
PRODUCT_CANDIDATE_TRIGGERS=82
PRODUCT_CANDIDATE_CONTEXTS=0
ANOMALY_CONTEXT_DETAILS=0
```

Do not retry baseline creation in this task.

Return:

```text
THIRD_RUN_MUTATED=NO
CANDIDATES_MUTATED=NO
TRIGGERS_MUTATED=NO
BASELINE_ROWS_ADDED=0
```

---

# 9. Evidence report — primary + canonical backup

Create primary report:

```text
F:\options-anomaly-scanner-stage8\docs\evidence\stage8\NIGHTWATCH_VNEXT_STAGE8_BASELINE_JSONB_SQL_NULL_REMEDIATION_REPORT_20260820.md
```

Also save byte-identical canonical backup:

```text
F:\options-anomaly-scanner\docs\evidence\NIGHTWATCH_VNEXT_STAGE8_BASELINE_JSONB_SQL_NULL_REMEDIATION_REPORT_20260820.md
```

Requirements:

- primary and canonical report must be byte-identical;
- verify SHA-256 for both;
- if canonical target already exists with identical bytes, keep it;
- if same filename exists with different bytes, do not overwrite;
- return `HOLD_REPORT_CONFLICT`.

---

# 10. Final result

Use exactly one:

```text
STAGE8_BASELINE_JSONB_REMEDIATION_RESULT=PASS
STAGE8_BASELINE_JSONB_REMEDIATION_RESULT=FAIL
STAGE8_BASELINE_JSONB_REMEDIATION_RESULT=HOLD
```

Return:

```text
STAGE8_BASELINE_JSONB_REMEDIATION_RESULT=

ROOT_CAUSE_ADDRESSED=YES/NO

CONTRACT_SNAPSHOT_NONE_AS_NULL=
EXPIRY_ACTIVITY_RECAP_NONE_AS_NULL=

POSTGRES_NULL_BIND_BEHAVIOR_VERIFIED=
CONTRACT_BRANCH_VERIFIED=
EXPIRY_BRANCH_VERIFIED=

CHECK_CONSTRAINT_PRESERVED=YES/NO
ORM_DB_SCHEMA_MISMATCH_RESOLVED=YES/NO

FIRST_KNOWLEDGE_CUTOFF_LOGIC_CHANGED=NO
EXISTING_7_CANDIDATES_STILL_REUSABLE=YES/NO

S4_IDENTIFIER_REMEDIATION_PRESERVED=
POST_CANDIDATE_PARTIAL_REMEDIATION_PRESERVED=

APPLICATION_CODE_CHANGES=
TEST_CODE_CHANGES=

MIGRATION_CREATED=NO
ALEMBIC_HEAD=20260818_0017

THIRD_RUN_MUTATED=NO
CANDIDATES_MUTATED=NO
TRIGGERS_MUTATED=NO
BASELINE_ROWS_ADDED=0

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

FOURTH_MAG7_SCAN_AUTHORIZED=NO
BASELINE_RETRY_AUTHORIZED=NO
STAGE8_OBSERVATION_RESUME_READY=YES/NO
STAGE9_READY=NO
NEXT_AUTHORIZED_STAGE=NONE
```

If PASS:

```text
STAGE8_OBSERVATION_RESUME_READY=YES
```

means only that the mapper/persistence defect is remediated and the existing seven candidates are ready for a separately authorized baseline-only creation step.

Do not create those baselines automatically.

Do not run a fourth MAG7 scan.

STOP.

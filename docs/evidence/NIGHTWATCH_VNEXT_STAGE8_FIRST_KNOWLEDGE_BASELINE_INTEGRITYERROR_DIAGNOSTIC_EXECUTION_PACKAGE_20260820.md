# Nightwatch vNext — Stage 8 FIRST_KNOWLEDGE_BASELINE IntegrityError Diagnostic — Execution Package

**Date:** 2026-08-20  
**Purpose:** Diagnose the confirmed Stage 8 baseline-creation failure after the third controlled MAG7 scan completed successfully and materialized seven ProductCandidates.  
**Authorization:** Zero-paid, read-only diagnostic only.  
**Worktree:** `F:\options-anomaly-scanner-stage8`  
**Branch:** `vnext/stage8-mag7-observation`

---

## 0. Trigger

The third controlled MAG7 scan itself succeeded:

```text
THIRD_SCAN_RUN_ID=2c71e5bb-9334-4806-a195-0f8768d2d0f2
THIRD_SCAN_STATUS=COMPLETE
THIRD_SCAN_SAFE_ERROR=NONE

NEW_PRODUCT_CANDIDATE_COUNT=7
NEW_PRODUCT_CANDIDATE_TRIGGER_COUNT=82
```

Both accepted scanner remediations passed runtime proof.

The subsequent attempt to create one accepted:

```text
FIRST_KNOWLEDGE_BASELINE
```

for each of the seven new candidates failed atomically:

```text
BASELINE_CREATION_SAFE_ERROR=IntegrityError
BASELINE_TRANSACTION_ROLLED_BACK=YES
BASELINE_COUNT=0
ANOMALY_CONTEXT_DETAIL_COUNT=0
```

No baseline retry, diagnosis, or remediation was performed.

This task diagnoses that `IntegrityError` only.

---

## 1. Canonical evidence root

Read governing/report evidence from:

```text
F:\options-anomaly-scanner\docs\evidence
```

At minimum read completely:

```text
F:\options-anomaly-scanner\docs\evidence\NIGHTWATCH_VNEXT_CANONICAL_EVIDENCE_MANIFEST.md

F:\options-anomaly-scanner\docs\evidence\NIGHTWATCH_SCANNER_VNEXT_INTEGRATED_SPEC_PROMPT_20260817(1).md

F:\options-anomaly-scanner\docs\evidence\NIGHTWATCH_VNEXT_STAGE5_PRODUCT_CANDIDATE_PERSISTENCE_COMPLETION_REPORT_20260818.md

F:\options-anomaly-scanner\docs\evidence\NIGHTWATCH_VNEXT_STAGE6_PHASE2B_BALANCED_MODEL_CODEX_EXECUTION_PACKAGE_20260818.md

F:\options-anomaly-scanner\docs\evidence\NIGHTWATCH_VNEXT_STAGE6_PHASE2B_BALANCED_MODEL_COMPLETION_REPORT_20260818.md

F:\options-anomaly-scanner\docs\evidence\NIGHTWATCH_VNEXT_STAGE6_BASELINE_CUTOFF_REMEDIATION_PASS_20260820.md

F:\options-anomaly-scanner\docs\evidence\NIGHTWATCH_VNEXT_THIRD_CONTROLLED_LIVE_MAG7_OBSERVATION_REPORT_20260820.md
```

If this exact diagnostic execution package is attached and absent from the canonical evidence root, save it byte-for-byte as:

```text
F:\options-anomaly-scanner\docs\evidence\NIGHTWATCH_VNEXT_STAGE8_FIRST_KNOWLEDGE_BASELINE_INTEGRITYERROR_DIAGNOSTIC_EXECUTION_PACKAGE_20260820.md
```

If the target exists with different bytes, do not overwrite. Return:

```text
BASELINE_DIAGNOSTIC_RESULT=HOLD_PACKAGE_CONFLICT
```

and STOP.

---

## 2. Hard authorization boundary

Authorized:

```text
repository/code inspection
read-only runtime DB SELECTs
read-only inspection of the third ScanRun
read-only inspection of the 7 ProductCandidates
read-only inspection of the 82 ProductCandidateTriggers
read-only inspection of source/archive rows referenced by accepted baseline selectors
read-only inspection of database catalog/schema/constraints
zero-paid local/offline reproduction
local tests that perform zero Nightwatch calls and zero remote DB writes
sanitized diagnostic evidence/report files
```

Not authorized:

```text
fourth MAG7 scan
Nightwatch request
Phase2B paid refresh
Dealer/GEX live request
remote DB INSERT/UPDATE/DELETE
remote migration/schema write
baseline retry against remote runtime
manual baseline insert
historical repair
application code edit
test code edit
migration edit
workflow/scheduler change
commit/push/PR/merge
```

Expected:

```text
NIGHTWATCH_REQUESTS=0
PAID_UNITS=0
REMOTE_DB_WRITES=0
APPLICATION_CODE_CHANGES=0
```

---

## 3. First objective — identify the exact IntegrityError

Do not stop at SQLAlchemy class name `IntegrityError`.

Trace the accepted baseline creation path used for the seven candidates.

Identify, if evidence permits:

```text
exact failing candidate
exact failing function
exact ORM flush/insert operation
exact target table
exact target column(s) or constraint
exact offending value or relationship
PostgreSQL SQLSTATE / driver error code
sanitized original DBAPI error text
```

Return:

```text
BASELINE_INTEGRITYERROR_ROOT_CAUSE_IDENTIFIED=YES/NO

FAILING_CANDIDATE_ID=
FAILING_CANDIDATE_TICKER=

FAILING_FUNCTION=
TARGET_TABLE=
TARGET_COLUMN_OR_CONSTRAINT=

DB_ERROR_CODE=
SANITIZED_DB_ERROR=
OFFENDING_VALUE_SHAPE=
```

If original `DBAPIError.orig` was not persisted and no retained log contains it, state that explicitly.

Do not fabricate an error string.

---

## 4. Trace transaction ordering

The third observation attempted all seven baselines in one atomic transaction.

Trace the actual Stage 6 baseline service write order.

At minimum determine the ordering of:

```text
ProductCandidateContext creation
flush/PK availability
AnomalyContextDetail creation
trigger/detail association
commit
```

Return:

```text
BASELINE_TRANSACTION_ORDER=
FIRST_DB_WRITE_CLASS=
FIRST_DB_FLUSH_POINT=
FAILURE_OCCURRED_BEFORE_OR_AFTER_FIRST_CONTEXT_FLUSH=
```

Determine whether the failure is caused by:

```text
missing/invalid parent ID
foreign-key ordering
unique constraint
check constraint
enum/check vocabulary
not-null violation
string length
numeric precision/scale
datetime/date violation
JSON shape
duplicate detail identity
other
```

Do not infer; prove from code/schema/evidence.

---

## 5. Inspect all seven candidate inputs

For the seven candidates from:

```text
THIRD_SCAN_RUN_ID=2c71e5bb-9334-4806-a195-0f8768d2d0f2
```

inspect all fields consumed by baseline creation.

Candidate set:

```text
AAPL
AMZN
GOOGL
META
MSFT
NVDA
TSLA
```

For each candidate report:

```text
candidate_id
ticker
candidate_first_knowledge_at
materialization rule version/hash
trigger count
baseline already exists yes/no
```

Then identify whether the exact failure would occur:

```text
on first candidate
on a particular candidate
only after multiple candidates
only when details are added
```

Return:

```text
FAILURE_SCOPE=FIRST_CANDIDATE/SPECIFIC_CANDIDATE/MULTI_CANDIDATE/DETAIL_LEVEL/UNRESOLVED
```

---

## 6. Inspect baseline target schema and ORM agreement

Compare ORM, migration, and deployed PostgreSQL schema for:

```text
product_candidate_contexts
anomaly_context_details
```

Inspect:

```text
PK
FK
unique constraints
not-null
check constraints
enum/vocabulary constraints
String lengths
Numeric precision/scale
timestamp/date types
JSONB
cascade/order semantics
```

Return:

```text
ORM_DB_SCHEMA_MISMATCH_FOUND=YES/NO
```

If YES, identify the exact mismatch.

---

## 7. Inspect baseline selector outputs before persistence

Using only already-persisted source rows and the accepted cutoff:

```text
candidate_first_knowledge_at
```

reconstruct the objects/values baseline service would attempt to persist.

For every field destined for either baseline table, check:

```text
Python type
safe value/value shape
target DB type
constraint
valid yes/no/unresolved
```

Pay particular attention to:

```text
evaluation_kind
source/availability state strings
provenance/reference identifiers
trigger identity
anomaly family
ticker
expiration
OSI / contract key
timestamps
context JSON payloads
reason/status strings
```

Return a compact violation table.

Do not change values.

---

## 8. Zero-paid reproduction

Attempt the narrowest reproduction without vendor calls or remote DB writes.

Preferred order:

1. pure object/value reconstruction;
2. local unit/service-level reproduction using existing fixtures;
3. isolated local DB only if already available and no remote endpoint is touched.

Do NOT use the production Supabase database for speculative writes, even inside a transaction intended to roll back.

Return:

```text
ZERO_PAID_BASELINE_REPRODUCTION_ATTEMPTED=YES/NO
ZERO_PAID_BASELINE_REPRODUCTION_RESULT=REPRODUCED/NOT_REPRODUCED/NOT_POSSIBLE
```

If reproduced, capture the exact sanitized exception/constraint.

---

## 9. Determine defect class

Use exactly one:

```text
BASELINE_PARENT_CHILD_ORDERING_DEFECT
BASELINE_UNIQUE_IDENTITY_DEFECT
BASELINE_SCHEMA_CONSTRAINT_DEFECT
BASELINE_ENUM_OR_STATUS_VOCABULARY_DEFECT
BASELINE_SELECTOR_NORMALIZATION_DEFECT
BASELINE_PROVENANCE_REFERENCE_DEFECT
BASELINE_DATETIME_OR_INFORMATION_TIME_PERSISTENCE_DEFECT
ORM_DB_SCHEMA_MISMATCH_DEFECT
OTHER
UNRESOLVED
```

Return:

```text
DEFECT_CLASS=
DEFECT_IS_DETERMINISTIC_WITH_SAME_INPUT=YES/NO/UNRESOLVED
BASELINE_RETRY_WITHOUT_FIX_WOULD_LIKELY_REFAIL=YES/NO/UNRESOLVED
```

Do not retry.

---

## 10. Determine remediation scope — design only

If root cause is identified, propose the smallest safe fix.

Return:

```text
REMEDIATION_REQUIRED=YES/NO/UNRESOLVED
EXPECTED_FILES_TO_CHANGE=
MIGRATION_REQUIRED=YES/NO/UNRESOLVED
HISTORICAL_DATA_REPAIR_REQUIRED=YES/NO/UNRESOLVED
```

Do not implement.

Important:

```text
the 7 ProductCandidates and 82 triggers are genuine persisted Stage 8 evidence
and must not be deleted or recreated merely because baseline creation failed.
```

If a later remediation can safely create baseline for these already-persisted candidates without a fourth MAG7 scan, say so:

```text
EXISTING_CANDIDATES_REUSABLE_FOR_BASELINE_AFTER_FIX=YES/NO/UNRESOLVED
FOURTH_SCAN_NEEDED_TO_TEST_BASELINE_FIX=YES/NO/UNRESOLVED
```

This must be based on information-time integrity, not convenience.

---

## 11. Critical first-knowledge integrity question

Determine whether the seven persisted candidates already contain sufficient immutable evidence to create their proper original:

```text
FIRST_KNOWLEDGE_BASELINE
```

after a code-only remediation, without rerunning the scanner and without using later evidence.

Verify whether accepted baseline selectors can still enforce:

```text
evidence_cutoff_at = candidate_first_knowledge_at
```

from the persisted historical sources.

Return:

```text
ORIGINAL_FIRST_KNOWLEDGE_BASELINE_STILL_RECONSTRUCTIBLE=YES/NO/UNRESOLVED
```

If YES, explain why later wall-clock execution would not launder freshness.

If NO, identify which non-backfillable input was lost.

Do not create the baseline in this diagnostic.

---

## 12. Preserve runtime truth

Read-only verify:

```text
THIRD_SCAN_RUN_ID=2c71e5bb-9334-4806-a195-0f8768d2d0f2
status=COMPLETE

ProductCandidate rows linked to run=7
ProductCandidateTrigger rows linked to run=82

ProductCandidateContext rows for those candidates=0
AnomalyContextDetail rows for those candidates=0
```

Return:

```text
THIRD_RUN_MUTATED=NO
CANDIDATES_MUTATED=NO
TRIGGERS_MUTATED=NO
BASELINE_ROWS_ADDED=0
```

No repair.

---

## 13. Evidence report — primary + canonical backup

Create primary report:

```text
F:\options-anomaly-scanner-stage8\docs\evidence\stage8\NIGHTWATCH_VNEXT_STAGE8_FIRST_KNOWLEDGE_BASELINE_INTEGRITYERROR_DIAGNOSTIC_REPORT_20260820.md
```

Also save byte-identical canonical backup:

```text
F:\options-anomaly-scanner\docs\evidence\NIGHTWATCH_VNEXT_STAGE8_FIRST_KNOWLEDGE_BASELINE_INTEGRITYERROR_DIAGNOSTIC_REPORT_20260820.md
```

Requirements:

- primary and canonical report must be byte-identical;
- verify SHA-256 for both;
- if canonical target already has identical bytes, keep it;
- if same filename exists with different bytes, do not overwrite;
- return `HOLD_REPORT_CONFLICT`.

---

## 14. Final result

Use exactly one:

```text
BASELINE_DIAGNOSTIC_RESULT=ROOT_CAUSE_CONFIRMED
BASELINE_DIAGNOSTIC_RESULT=ROOT_CAUSE_NARROWED_NOT_CONFIRMED
BASELINE_DIAGNOSTIC_RESULT=INSUFFICIENT_EVIDENCE
BASELINE_DIAGNOSTIC_RESULT=BLOCKING_SCHEMA_DEFECT_CONFIRMED
```

Return:

```text
BASELINE_DIAGNOSTIC_RESULT=

BASELINE_INTEGRITYERROR_ROOT_CAUSE_IDENTIFIED=

FAILING_CANDIDATE_ID=
FAILING_CANDIDATE_TICKER=
FAILING_FUNCTION=
TARGET_TABLE=
TARGET_COLUMN_OR_CONSTRAINT=
DB_ERROR_CODE=
SANITIZED_DB_ERROR=

FAILURE_SCOPE=
ORM_DB_SCHEMA_MISMATCH_FOUND=

ZERO_PAID_BASELINE_REPRODUCTION_ATTEMPTED=
ZERO_PAID_BASELINE_REPRODUCTION_RESULT=

DEFECT_CLASS=
DEFECT_IS_DETERMINISTIC_WITH_SAME_INPUT=
BASELINE_RETRY_WITHOUT_FIX_WOULD_LIKELY_REFAIL=

REMEDIATION_REQUIRED=
EXPECTED_FILES_TO_CHANGE=
MIGRATION_REQUIRED=
HISTORICAL_DATA_REPAIR_REQUIRED=

EXISTING_CANDIDATES_REUSABLE_FOR_BASELINE_AFTER_FIX=
FOURTH_SCAN_NEEDED_TO_TEST_BASELINE_FIX=
ORIGINAL_FIRST_KNOWLEDGE_BASELINE_STILL_RECONSTRUCTIBLE=

THIRD_RUN_MUTATED=NO
CANDIDATES_MUTATED=NO
TRIGGERS_MUTATED=NO
BASELINE_ROWS_ADDED=0

NIGHTWATCH_REQUESTS=0
PAID_UNITS=0
REMOTE_DB_WRITES=0
APPLICATION_CODE_CHANGES=0
TEST_CODE_CHANGES=0
MIGRATION_CHANGES=0
WORKFLOWS_DISPATCHED=0
COMMITS_CREATED=0
PUSHES=0
PRS_CREATED=0
MERGES=0

FOURTH_MAG7_SCAN_AUTHORIZED=NO
STAGE8_OBSERVATION_RESUME_READY=NO
STAGE9_READY=NO
NEXT_AUTHORIZED_STAGE=NONE

PRIMARY_REPORT_PATH=
CANONICAL_REPORT_PATH=
PRIMARY_REPORT_SHA256=
CANONICAL_REPORT_SHA256=
REPORT_BACKUP_BYTE_IDENTICAL=YES/NO
```

STOP.

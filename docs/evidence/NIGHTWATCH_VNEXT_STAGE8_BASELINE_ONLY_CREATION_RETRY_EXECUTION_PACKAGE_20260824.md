# Nightwatch vNext — Stage 8 Baseline-Only Creation Retry — Execution Package

**Date:** 2026-08-24  
**Purpose:** Retry the previously authorized baseline-only creation for the seven already-persisted third-run ProductCandidates, after the prior attempt failed before opening the remote runtime connection because the Stage 8 worktree lacked runtime environment configuration.  
**Authorization:** Founder explicitly authorized **Baseline-only Creation Retry**.  
**Execution worktree:** `F:\options-anomaly-scanner-stage8`  
**Branch:** `vnext/stage8-mag7-observation`  
**Runtime schema:** `20260818_0017`

---

# 0. Founder authorization

The Founder explicitly authorizes exactly **one** new baseline-only creation retry.

```text
FOUNDER_AUTHORIZATION=BASELINE_ONLY_CREATION_RETRY_20260824

BASELINE_ONLY_CREATION_RETRY_AUTHORIZED=YES
BASELINE_CREATION_RETRY_ATTEMPTS_AUTHORIZED=1

TARGET_SCAN_RUN_ID=2c71e5bb-9334-4806-a195-0f8768d2d0f2
TARGET_PRODUCT_CANDIDATE_COUNT=7
TARGET_PRODUCT_CANDIDATE_TRIGGER_COUNT=82

EVALUATION_KIND=FIRST_KNOWLEDGE_BASELINE
EVIDENCE_CUTOFF=candidate_first_knowledge_at

MAG7_SCAN_AUTHORIZED=NO
NIGHTWATCH_REQUEST_AUTHORIZED=NO
PHASE2B_REFRESH_AUTHORIZED=NO
DEALER_GEX_LIVE_CALL_AUTHORIZED=NO
FOURTH_MAG7_SCAN_AUTHORIZED=NO
```

This authorization is exhausted after the first new baseline creation attempt, regardless of success or failure.

No automatic second retry.

---

# 1. Prior failed attempt — exact cause

The previous baseline-only creation attempt did **not** reach the remote Supabase runtime.

Observed:

```text
BASELINE_ONLY_CREATION_RESULT=FAIL_BASELINE_CREATION
CREATION_SAFE_ERROR=OperationalError
DBAPI_SAFE_ERROR=psycopg.errors.ConnectionTimeout

F:\options-anomaly-scanner-stage8\.env = absent
```

The command therefore fell back to:

```text
localhost:5432/options_scanner
```

and timed out before a remote transaction existed.

Post-failure remote verification confirmed:

```text
TARGET_SCAN_RUN_STATUS=COMPLETE
PRODUCT_CANDIDATES=7
PRODUCT_CANDIDATE_TRIGGERS=82
PRODUCT_CANDIDATE_CONTEXTS=0
ANOMALY_CONTEXT_DETAILS=0
```

Therefore:

```text
NO HISTORICAL REPAIR REQUIRED
NO CANDIDATE RECREATION REQUIRED
NO FOURTH MAG7 SCAN REQUIRED
```

---

# 2. Canonical evidence root

Canonical evidence directory:

```text
F:\options-anomaly-scanner\docs\evidence
```

If this exact execution package is attached and absent from canonical evidence, save it byte-for-byte as:

```text
F:\options-anomaly-scanner\docs\evidence\NIGHTWATCH_VNEXT_STAGE8_BASELINE_ONLY_CREATION_RETRY_EXECUTION_PACKAGE_20260824.md
```

If the canonical target already exists with different bytes:

```text
BASELINE_ONLY_CREATION_RETRY_RESULT=HOLD_PACKAGE_CONFLICT
```

Do not overwrite. STOP.

Read completely at minimum:

```text
F:\options-anomaly-scanner\docs\evidence\NIGHTWATCH_VNEXT_CANONICAL_EVIDENCE_MANIFEST.md

F:\options-anomaly-scanner\docs\evidence\NIGHTWATCH_SCANNER_VNEXT_INTEGRATED_SPEC_PROMPT_20260817(1).md

F:\options-anomaly-scanner\docs\evidence\NIGHTWATCH_VNEXT_STAGE5_PRODUCT_CANDIDATE_PERSISTENCE_COMPLETION_REPORT_20260818.md

F:\options-anomaly-scanner\docs\evidence\NIGHTWATCH_VNEXT_STAGE6_PHASE2B_BALANCED_MODEL_COMPLETION_REPORT_20260818.md

F:\options-anomaly-scanner\docs\evidence\NIGHTWATCH_VNEXT_STAGE6_BASELINE_CUTOFF_REMEDIATION_PASS_20260820.md

F:\options-anomaly-scanner\docs\evidence\NIGHTWATCH_VNEXT_THIRD_CONTROLLED_LIVE_MAG7_OBSERVATION_REPORT_20260820.md

F:\options-anomaly-scanner\docs\evidence\NIGHTWATCH_VNEXT_STAGE8_FIRST_KNOWLEDGE_BASELINE_INTEGRITYERROR_DIAGNOSTIC_REPORT_20260820.md

F:\options-anomaly-scanner\docs\evidence\NIGHTWATCH_VNEXT_STAGE8_BASELINE_JSONB_SQL_NULL_REMEDIATION_REPORT_20260820.md

F:\options-anomaly-scanner\docs\evidence\NIGHTWATCH_VNEXT_STAGE8_BASELINE_ONLY_CREATION_REPORT_20260824.md
```

Do not ask the Founder to re-upload evidence already present there.

---

# 3. Hard authorization boundary

Authorized:

```text
read-only repository/code inspection
read-only runtime/environment preflight
read-only DB-target identity verification
read-only seven-candidate first-knowledge preview
exactly one baseline-only creation retry
new ProductCandidateContext rows for the seven existing candidates
new AnomalyContextDetail rows belonging to those seven baseline contexts
read-only post-write integrity verification
report/evidence creation
```

Forbidden:

```text
MAG7 scan
Nightwatch/vendor call
Phase2B REFRESH
Dealer/GEX live call
new ProductCandidate
new ProductCandidateTrigger
candidate/trigger mutation
manual SQL baseline INSERT/UPDATE
historical repair
migration/schema write
application/test code edit
workflow/scheduler edit
commit/push/PR/merge
Stage 9
second baseline retry
```

Required:

```text
MAG7_SCAN_INVOCATIONS_THIS_TASK=0
NIGHTWATCH_REQUESTS_THIS_TASK=0
PAID_UNITS_THIS_TASK=0
PHASE2B_REFRESH_CALLS=0
DEALER_GEX_LIVE_CALLS=0
```

---

# 4. Code-state preflight

Before any runtime write verify:

```text
WORKTREE=F:\options-anomaly-scanner-stage8
BRANCH=vnext/stage8-mag7-observation
```

Inspect:

```text
git rev-parse --abbrev-ref HEAD
git rev-parse HEAD
git status --short
git diff --check
```

Required:

```text
ACCEPTED_S4_IDENTIFIER_REMEDIATION_PRESENT=YES
ACCEPTED_POST_CANDIDATE_PARTIAL_REMEDIATION_PRESENT=YES
ACCEPTED_BASELINE_JSONB_SQL_NULL_REMEDIATION_PRESENT=YES
UNEXPECTED_APPLICATION_DIFF_FOUND=NO
```

Specifically verify:

```text
S4_VNEXT_DEEP_BUDGET_SELECTION

contract_snapshot = JSONB(none_as_null=True)
expiry_activity_recap = JSONB(none_as_null=True)
```

If mismatch:

```text
BASELINE_ONLY_CREATION_RETRY_RESULT=HOLD_CODE_STATE_MISMATCH
```

STOP.

Do not commit or alter code.

---

# 5. Runtime configuration source — critical correction

The retry must **not** resolve runtime configuration from:

```text
F:\options-anomaly-scanner-stage8\.env
```

because that file is absent.

Use the same canonical repository runtime environment configuration that successfully connected to the remote runtime during the prior read-only verification.

Canonical repository root:

```text
F:\options-anomaly-scanner
```

Resolve runtime DB configuration explicitly from the canonical repository configuration/environment mechanism already used successfully for remote Supabase reads.

Do not copy secrets into:

```text
Stage 8 worktree files
execution package
report
logs
stdout
git-tracked files
canonical evidence
```

Do not print:

```text
password
full DATABASE_URL
credentials
tokens
secret query parameters
```

If the exact safe canonical runtime configuration source cannot be resolved:

```text
BASELINE_ONLY_CREATION_RETRY_RESULT=HOLD_RUNTIME_CONFIG_UNRESOLVED
```

STOP before any creation attempt.

---

# 6. Mandatory DB target identity gate

This is a hard gate before the authorized creation attempt.

The exact configuration object / resolved database URL that will be used for the write session must first be fingerprinted without revealing credentials.

Expected target fingerprint:

```text
DB_TARGET_HOST=aws-0-ap-northeast-1.pooler.supabase.com
DB_TARGET_PORT=5432
DB_TARGET_DATABASE=postgres
DB_TARGET_IS_LOCALHOST=NO
```

At minimum reject:

```text
localhost
127.0.0.1
::1
options_scanner as local fallback database
```

Return:

```text
RESOLVED_DB_TARGET_HOST=
RESOLVED_DB_TARGET_PORT=
RESOLVED_DB_TARGET_DATABASE=
RESOLVED_DB_TARGET_IS_LOCALHOST=
```

Then, using the **same resolved configuration** intended for the write session, successfully open a read-only connection and verify:

```text
REMOTE_ALEMBIC_HEAD=20260818_0017
TARGET_SCAN_RUN_STATUS=COMPLETE
TARGET_PRODUCT_CANDIDATE_COUNT=7
TARGET_PRODUCT_CANDIDATE_TRIGGER_COUNT=82
TARGET_FIRST_KNOWLEDGE_BASELINE_COUNT=0
TARGET_ANOMALY_CONTEXT_DETAIL_COUNT=0
```

Return:

```text
DB_TARGET_IDENTITY_GATE=PASS/FAIL
WRITE_SESSION_CONFIG_MATCHES_VERIFIED_REMOTE_CONFIG=YES/NO
```

Required:

```text
DB_TARGET_IDENTITY_GATE=PASS
WRITE_SESSION_CONFIG_MATCHES_VERIFIED_REMOTE_CONFIG=YES
```

If not:

```text
BASELINE_ONLY_CREATION_RETRY_RESULT=HOLD_DB_TARGET_IDENTITY
```

STOP without consuming the creation attempt.

The write session must be created from the same already-verified resolved runtime configuration, not from an independently reloaded default.

---

# 7. Runtime state gate

Read target candidates by persisted ProductCandidate IDs linked to:

```text
TARGET_SCAN_RUN_ID=2c71e5bb-9334-4806-a195-0f8768d2d0f2
```

Expected tickers:

```text
AAPL
AMZN
GOOGL
META
MSFT
NVDA
TSLA
```

Expected:

```text
TARGET_PRODUCT_CANDIDATE_COUNT_BEFORE=7
TARGET_PRODUCT_CANDIDATE_TRIGGER_COUNT_BEFORE=82
TARGET_FIRST_KNOWLEDGE_BASELINE_COUNT_BEFORE=0
TARGET_ANOMALY_CONTEXT_DETAIL_COUNT_BEFORE=0
```

If any differ:

```text
BASELINE_ONLY_CREATION_RETRY_RESULT=HOLD_RUNTIME_STATE_CHANGED
```

STOP.

No candidate recreation.

---

# 8. Mandatory zero-write preview gate

Repeat the seven-candidate preview immediately before creation using the same verified remote runtime configuration.

For every candidate:

```text
evidence_cutoff_at = candidate_first_knowledge_at
```

Verify:

```text
PREVIEW_CANDIDATE_COUNT=7
PREVIEW_DETAIL_COUNT=82

PREVIEW_LOOKAHEAD_FOUND=NO
PREVIEW_SOURCE_TIME_VIOLATION_FOUND=NO
PREVIEW_TRIGGER_SET_DRIFT_FOUND=NO
TRIGGER_SET_DRIFT_BEFORE_WRITE=NO

PREVIEW_CONTRACT_PAYLOAD_MATCH_VALID=YES
PREVIEW_EXPIRY_PAYLOAD_MATCH_VALID=YES
```

Do not substitute later evidence.

If any integrity field fails:

```text
BASELINE_ONLY_CREATION_RETRY_RESULT=HOLD_FIRST_KNOWLEDGE_PREVIEW_INTEGRITY
```

STOP without creation.

If original first-knowledge context is no longer reconstructible:

```text
BASELINE_ONLY_CREATION_RETRY_RESULT=HOLD_BASELINE_NOT_RECONSTRUCTIBLE
```

STOP.

Missing context remains missing.

---

# 9. Execute exactly one baseline creation retry

Only after Sections 4–8 PASS may the one authorized creation attempt be consumed.

Create exactly one:

```text
FIRST_KNOWLEDGE_BASELINE
```

for each of the seven existing ProductCandidates, using:

```text
accepted Stage6BalancedContextService
current remediated ORM
verified remote runtime configuration
evidence_cutoff_at = candidate_first_knowledge_at
```

Do not use manual SQL DML.

Preferred transaction model remains:

```text
ONE_TRANSACTION_ONE_COMMIT
```

if supported by the existing service/session design without code changes.

Return before execution:

```text
BASELINE_CREATION_TRANSACTION_MODEL=
```

On any exception:

```text
stop immediately
do not retry
rollback active transaction where applicable
do not repair manually
```

Return:

```text
BASELINE_ONLY_CREATION_RETRY_RESULT=FAIL_BASELINE_CREATION
```

and report any actually committed rows.

---

# 10. Exact authorized write scope

Only these application rows may be added:

```text
ProductCandidateContext
AnomalyContextDetail
```

for the seven target candidates.

Must remain unchanged:

```text
scan_runs
product_candidates
product_candidate_triggers
ticker_scan_results
expiry_observations
contract_scan_observations
strike_clusters
raw_vendor_payloads
api_usage_audit
```

Return:

```text
PRODUCT_CANDIDATE_ROWS_CHANGED=0
PRODUCT_CANDIDATE_TRIGGER_ROWS_CHANGED=0
SCAN_RUN_ROWS_CHANGED=0
```

---

# 11. Post-write verification

Expected:

```text
TARGET_FIRST_KNOWLEDGE_BASELINE_COUNT_AFTER=7
ONE_BASELINE_PER_CANDIDATE=YES
DUPLICATE_BASELINE_FOUND=NO
```

Return one row per candidate with:

```text
candidate_id
ticker
candidate_first_knowledge_at
product_candidate_context_id
evaluation_kind
evidence_cutoff_at
context_evaluated_at
anomaly_detail_count
```

Verify:

```text
evaluation_kind=FIRST_KNOWLEDGE_BASELINE
evidence_cutoff_at=candidate_first_knowledge_at
context_evaluated_at >= candidate_first_knowledge_at
```

---

# 12. Persisted information-time integrity

For all seven persisted baselines verify:

```text
BASELINE_LOOKAHEAD_FOUND=NO
BASELINE_SOURCE_TIME_VIOLATION_FOUND=NO
BASELINE_TRIGGER_SET_DRIFT_FOUND=NO
BASELINE_FIRST_KNOWLEDGE_CUTOFF_MISMATCH_FOUND=NO
```

Any violation:

```text
BASELINE_ONLY_CREATION_RETRY_RESULT=FAIL_BASELINE_INTEGRITY
```

Do not delete or repair rows within this task.

---

# 13. Persisted AnomalyContextDetail integrity

Verify actual SQL-null semantics after persistence.

For CONTRACT:

```text
contract_snapshot IS NOT SQL NULL
expiry_activity_recap IS SQL NULL
```

For EXPIRY:

```text
contract_snapshot IS SQL NULL
expiry_activity_recap IS NOT SQL NULL
```

Return:

```text
ANOMALY_CONTEXT_DETAIL_COUNT_AFTER=
EXPECTED_ANOMALY_CONTEXT_DETAIL_COUNT=
CONTRACT_DETAIL_PAYLOAD_MATCH_VALID=YES/NO
EXPIRY_DETAIL_PAYLOAD_MATCH_VALID=YES/NO
DETAIL_ORPHAN_FOUND=YES/NO
```

The accepted preview produced 82 details corresponding to the 82 immutable triggers. Confirm the persisted expected count from the service semantics; do not force 82 if actual accepted mapping proves otherwise.

---

# 14. Runtime delta

Return exact deltas attributable to this retry:

```text
PRODUCT_CANDIDATE_CONTEXT_ROWS_ADDED=
ANOMALY_CONTEXT_DETAIL_ROWS_ADDED=

PRODUCT_CANDIDATE_ROWS_ADDED=0
PRODUCT_CANDIDATE_TRIGGER_ROWS_ADDED=0
SCAN_RUN_ROWS_ADDED=0
```

No concurrent unrelated write may be attributed to this task.

---

# 15. No scan / no paid call proof

Return:

```text
MAG7_SCAN_INVOCATIONS_THIS_TASK=0
NIGHTWATCH_REQUESTS_THIS_TASK=0
PAID_UNITS_THIS_TASK=0

PHASE2B_REFRESH_CALLS=0
DEALER_GEX_LIVE_CALLS=0
DEALER_GEX_SOURCE=ARCHIVE_ONLY
```

---

# 16. Result states

Use exactly one:

```text
BASELINE_ONLY_CREATION_RETRY_RESULT=PASS

BASELINE_ONLY_CREATION_RETRY_RESULT=FAIL_BASELINE_CREATION
BASELINE_ONLY_CREATION_RETRY_RESULT=FAIL_BASELINE_INTEGRITY

BASELINE_ONLY_CREATION_RETRY_RESULT=HOLD_CODE_STATE_MISMATCH
BASELINE_ONLY_CREATION_RETRY_RESULT=HOLD_RUNTIME_CONFIG_UNRESOLVED
BASELINE_ONLY_CREATION_RETRY_RESULT=HOLD_DB_TARGET_IDENTITY
BASELINE_ONLY_CREATION_RETRY_RESULT=HOLD_RUNTIME_STATE_CHANGED
BASELINE_ONLY_CREATION_RETRY_RESULT=HOLD_FIRST_KNOWLEDGE_PREVIEW_INTEGRITY
BASELINE_ONLY_CREATION_RETRY_RESULT=HOLD_BASELINE_NOT_RECONSTRUCTIBLE
BASELINE_ONLY_CREATION_RETRY_RESULT=HOLD_PACKAGE_CONFLICT
BASELINE_ONLY_CREATION_RETRY_RESULT=HOLD_REPORT_CONFLICT
```

---

# 17. Evidence report — primary + canonical backup

Create primary:

```text
F:\options-anomaly-scanner-stage8\docs\evidence\stage8\NIGHTWATCH_VNEXT_STAGE8_BASELINE_ONLY_CREATION_RETRY_REPORT_20260824.md
```

Also save byte-identical canonical backup:

```text
F:\options-anomaly-scanner\docs\evidence\NIGHTWATCH_VNEXT_STAGE8_BASELINE_ONLY_CREATION_RETRY_REPORT_20260824.md
```

Requirements:

```text
primary and canonical report byte-identical
SHA-256 verified for both
never overwrite conflicting canonical content
never include DB credentials/full DATABASE_URL
```

If same-name canonical content differs:

```text
HOLD_REPORT_CONFLICT
```

---

# 18. Required final fields

Return:

```text
BASELINE_ONLY_CREATION_RETRY_RESULT=

FOUNDER_AUTHORIZATION=BASELINE_ONLY_CREATION_RETRY_20260824
BASELINE_CREATION_RETRY_ATTEMPTS_AUTHORIZED=1
ACTUAL_BASELINE_CREATION_RETRY_ATTEMPTS=

TARGET_SCAN_RUN_ID=2c71e5bb-9334-4806-a195-0f8768d2d0f2
TARGET_SCAN_RUN_STATUS=

ACCEPTED_S4_IDENTIFIER_REMEDIATION_PRESENT=
ACCEPTED_POST_CANDIDATE_PARTIAL_REMEDIATION_PRESENT=
ACCEPTED_BASELINE_JSONB_SQL_NULL_REMEDIATION_PRESENT=
UNEXPECTED_APPLICATION_DIFF_FOUND=

RUNTIME_CONFIG_SOURCE=
RESOLVED_DB_TARGET_HOST=
RESOLVED_DB_TARGET_PORT=
RESOLVED_DB_TARGET_DATABASE=
RESOLVED_DB_TARGET_IS_LOCALHOST=
DB_TARGET_IDENTITY_GATE=
WRITE_SESSION_CONFIG_MATCHES_VERIFIED_REMOTE_CONFIG=

REMOTE_ALEMBIC_HEAD=

TARGET_PRODUCT_CANDIDATE_COUNT_BEFORE=
TARGET_PRODUCT_CANDIDATE_TRIGGER_COUNT_BEFORE=
TARGET_FIRST_KNOWLEDGE_BASELINE_COUNT_BEFORE=
TARGET_ANOMALY_CONTEXT_DETAIL_COUNT_BEFORE=

PREVIEW_CANDIDATE_COUNT=
PREVIEW_DETAIL_COUNT=
PREVIEW_LOOKAHEAD_FOUND=
PREVIEW_SOURCE_TIME_VIOLATION_FOUND=
PREVIEW_TRIGGER_SET_DRIFT_FOUND=
TRIGGER_SET_DRIFT_BEFORE_WRITE=
PREVIEW_CONTRACT_PAYLOAD_MATCH_VALID=
PREVIEW_EXPIRY_PAYLOAD_MATCH_VALID=

BASELINE_CREATION_TRANSACTION_MODEL=

TARGET_FIRST_KNOWLEDGE_BASELINE_COUNT_AFTER=
ANOMALY_CONTEXT_DETAIL_COUNT_AFTER=
EXPECTED_ANOMALY_CONTEXT_DETAIL_COUNT=

ONE_BASELINE_PER_CANDIDATE=
DUPLICATE_BASELINE_FOUND=

BASELINE_LOOKAHEAD_FOUND=
BASELINE_SOURCE_TIME_VIOLATION_FOUND=
BASELINE_TRIGGER_SET_DRIFT_FOUND=
BASELINE_FIRST_KNOWLEDGE_CUTOFF_MISMATCH_FOUND=

CONTRACT_DETAIL_PAYLOAD_MATCH_VALID=
EXPIRY_DETAIL_PAYLOAD_MATCH_VALID=
DETAIL_ORPHAN_FOUND=

PRODUCT_CANDIDATE_CONTEXT_ROWS_ADDED=
ANOMALY_CONTEXT_DETAIL_ROWS_ADDED=
PRODUCT_CANDIDATE_ROWS_ADDED=0
PRODUCT_CANDIDATE_TRIGGER_ROWS_ADDED=0
SCAN_RUN_ROWS_ADDED=0

PRODUCT_CANDIDATE_ROWS_CHANGED=0
PRODUCT_CANDIDATE_TRIGGER_ROWS_CHANGED=0
SCAN_RUN_ROWS_CHANGED=0

MAG7_SCAN_INVOCATIONS_THIS_TASK=0
NIGHTWATCH_REQUESTS_THIS_TASK=0
PAID_UNITS_THIS_TASK=0
PHASE2B_REFRESH_CALLS=0
DEALER_GEX_LIVE_CALLS=0

REMOTE_DB_SCHEMA_WRITES=0
REMOTE_APPLICATION_DATA_WRITES=AUTHORIZED_BASELINE_ONLY_CREATION_RETRY_ONLY

APPLICATION_CODE_CHANGES_DURING_RETRY=0
TEST_CODE_CHANGES_DURING_RETRY=0
MIGRATION_FILES_CHANGED_DURING_RETRY=0
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
SECOND_BASELINE_RETRY_AUTHORIZED=NO
STAGE8_OBSERVATION_RESUME_READY=YES/NO
STAGE9_READY=NO
NEXT_AUTHORIZED_STAGE=NONE
```

If and only if:

```text
BASELINE_ONLY_CREATION_RETRY_RESULT=PASS
```

then:

```text
STAGE8_OBSERVATION_RESUME_READY=YES
```

This indicates the third controlled scan now has genuine ProductCandidate + frozen first-knowledge baseline samples.

Do not automatically begin broader Stage 8 analysis.

Do not run a fourth MAG7 scan.

Do not begin Stage 9.

STOP.

---

# 19. Carried ledger

Preserve:

```text
CURRENT_TRIGGER_FRESHNESS_MODE=CALIBRATION_REQUIRED
RADAR_OI_SCHEDULE_ACTIVATION=PENDING_ROLLOVER_EVIDENCE
CROSS_RUN_CANDIDATE_LIFECYCLE=DEFERRED_NO_AUTO_MERGE
IV_RANK_CORE_ELIGIBILITY=WITHHOLD_PENDING_PROVENANCE
ISOLATED_POSTGRES_RUNTIME_VERIFIED=NO
N1_HISTORICAL_RUNTIME_DISTRIBUTION_VERIFIED=NO
```

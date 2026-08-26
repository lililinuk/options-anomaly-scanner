# Nightwatch vNext — Stage 8 Baseline JSONB SQL-NULL Remediation Report

**Date:** 2026-08-24  
**Execution package date:** 2026-08-20  
**Worktree:** `F:\options-anomaly-scanner-stage8`  
**Branch:** `vnext/stage8-mag7-observation`  
**Base HEAD:** `3a63eaa1b9069d34199704fe31ac6466e8929d7d`

## Executive result

```text
STAGE8_BASELINE_JSONB_REMEDIATION_RESULT=PASS
ROOT_CAUSE_ADDRESSED=YES
```

The narrow ORM remediation is complete. Only `AnomalyContextDetail.contract_snapshot` and
`AnomalyContextDetail.expiry_activity_recap` now use `JSONB(none_as_null=True)`. Python `None`
therefore binds as SQL `NULL`, while Python dictionaries remain JSONB objects. The deployed
mutually exclusive payload check is unchanged and remains authoritative.

No migration, runtime write, baseline retry, MAG7 scan, Nightwatch request, historical repair,
workflow, scheduler, commit, push, PR, or merge was performed.

## Package and governing evidence

The attached remediation package was preserved byte-for-byte at:

`F:\options-anomaly-scanner\docs\evidence\NIGHTWATCH_VNEXT_STAGE8_BASELINE_JSONB_SQL_NULL_REMEDIATION_EXECUTION_PACKAGE_20260820.md`

```text
PACKAGE_SHA256=690EF04AB67F5EA9B9EE4B2E4D730496497D693F920B7E807669C1CC5A93956D
PACKAGE_BACKUP_BYTE_IDENTICAL=YES
PACKAGE_CONFLICT_FOUND=NO
```

The execution package and every required governing/report file were read completely from their
explicit canonical paths:

- `NIGHTWATCH_SCANNER_VNEXT_INTEGRATED_SPEC_PROMPT_20260817(1).md`
- `NIGHTWATCH_VNEXT_STAGE6_PHASE2B_BALANCED_MODEL_CODEX_EXECUTION_PACKAGE_20260818.md`
- `NIGHTWATCH_VNEXT_STAGE6_PHASE2B_BALANCED_MODEL_COMPLETION_REPORT_20260818.md`
- `NIGHTWATCH_VNEXT_STAGE6_BASELINE_CUTOFF_REMEDIATION_PASS_20260820.md`
- `NIGHTWATCH_VNEXT_THIRD_CONTROLLED_LIVE_MAG7_OBSERVATION_REPORT_20260820.md`
- `NIGHTWATCH_VNEXT_STAGE8_FIRST_KNOWLEDGE_BASELINE_INTEGRITYERROR_DIAGNOSTIC_REPORT_20260820.md`
- `NIGHTWATCH_VNEXT_STAGE8_BASELINE_JSONB_SQL_NULL_REMEDIATION_EXECUTION_PACKAGE_20260820.md`

## Authorized scope and code change

```text
AUTHORIZED_REMEDIATION_FILES:
- backend/app/db/models.py: set SQL-NULL binding only for the two mutually exclusive nullable JSONB payloads
- backend/tests/test_stage6_balanced_context.py: PostgreSQL bind/check and Stage 6 builder regressions
```

Before editing, the only tracked worktree differences were the two accepted earlier Stage 8
remediations in `backend/app/scanner/v13.py` and
`backend/tests/test_stage4b_phase2a_vnext.py`. No unexpected diff existed.

The application change is exactly:

```python
contract_snapshot = mapped_column(JSONB(none_as_null=True))
expiry_activity_recap = mapped_column(JSONB(none_as_null=True))
```

No other JSONB mapping changed. The migration and deployed check constraint were not edited.
Authorized remediation diff statistics:

```text
backend/app/db/models.py: 6 lines added, 2 removed
backend/tests/test_stage6_balanced_context.py: 110 lines added, 0 removed
```

## PostgreSQL bind and constraint proof

The new tests use the actual ORM column types with SQLAlchemy's PostgreSQL dialect bind processor.
They prove:

| Entity branch | `contract_snapshot` | `expiry_activity_recap` | Check result |
|---|---|---|---|
| CONTRACT | dictionary -> JSONB object | Python `None` -> SQL `NULL` | valid |
| EXPIRY | Python `None` -> SQL `NULL` | dictionary -> JSONB object | valid |
| either entity, both active | JSONB object | JSONB object | invalid |
| either entity, neither active | SQL `NULL` | SQL `NULL` | invalid |

The ORM check constraint still contains all four required clauses:

```text
contract_snapshot IS NOT NULL
expiry_activity_recap IS NULL
contract_snapshot IS NULL
expiry_activity_recap IS NOT NULL
```

The Stage 6 service-level regression constructs the accepted mixed trigger fixture through
`Stage6BalancedContextService._persist_evaluation`. Both CONTRACT details bind their inactive
expiry recap as SQL NULL, and the EXPIRY detail binds its inactive contract snapshot as SQL NULL.
This directly removes the deterministic PostgreSQL 23514 condition without weakening payload/entity
matching.

```text
CONTRACT_SNAPSHOT_NONE_AS_NULL=TRUE
EXPIRY_ACTIVITY_RECAP_NONE_AS_NULL=TRUE
POSTGRES_NULL_BIND_BEHAVIOR_VERIFIED=YES
CONTRACT_BRANCH_VERIFIED=YES
EXPIRY_BRANCH_VERIFIED=YES
CHECK_CONSTRAINT_PRESERVED=YES
ORM_DB_SCHEMA_MISMATCH_RESOLVED=YES
```

## First-knowledge and existing candidate preservation

No confirmation service, selector, cutoff, timestamp, or provenance code changed. Baseline still
uses immutable `candidate_first_knowledge_at` as `evidence_cutoff_at`; raw source, chain, Dealer/GEX,
and corrected OHLC NY-date fail-closed rules remain unchanged.

The seven genuine third-run candidates and 82 immutable triggers therefore remain suitable for a
separately authorized baseline-only creation operation. Later execution time cannot introduce later
evidence because accepted selectors retain the original first-knowledge cutoff. This remediation
did not create or retry any baseline.

```text
FIRST_KNOWLEDGE_CUTOFF_LOGIC_CHANGED=NO
EXISTING_7_CANDIDATES_STILL_REUSABLE=YES
BASELINE_RETRY_AUTHORIZED=NO
```

## Prior Stage 8 remediations preserved

The existing Stage 8 scanner files were not edited during this remediation. Their SHA-256 values
remain identical to the accepted third-observation evidence:

```text
backend/app/scanner/v13.py=E7B7E0A58EE3B30FC3AD3EA69A3E7251C2843381E39995EA27C0D0E33F035DC5
backend/tests/test_stage4b_phase2a_vnext.py=A0CD77DDACF8A7E8C0896C01715A209CE2AD90FF7996289E8AE407CD4E03186E
```

Stage 4B regression execution reconfirmed:

- active identifier `S4_VNEXT_DEEP_BUDGET_SELECTION`, length 30 <= 32;
- missing optional/post-candidate structure archive alone leaves the vNext run COMPLETE and permits
  seven candidates / 82 triggers;
- a legitimate pre-existing PARTIAL remains PARTIAL;
- candidate-before-Deep-Dive-budget behavior remains intact.

```text
S4_IDENTIFIER_REMEDIATION_PRESERVED=YES
POST_CANDIDATE_PARTIAL_REMEDIATION_PRESERVED=YES
```

## Verification matrix

All commands used an empty Nightwatch key, in-memory SQLite where a database setting was required,
`PYTHONDONTWRITEBYTECODE=1`, and disabled pytest/Ruff caches. No automated test contacted an
external API.

```text
Focused new JSONB/SQL-NULL regressions:
python -B -m pytest tests/test_stage6_balanced_context.py -k "jsonb_uses_sql_null or binds_inactive_payloads_as_sql_null" -p no:cacheprovider -q
RESULT=PASS (2 passed)

Full Stage 6:
python -B -m pytest tests/test_stage6_balanced_context.py -p no:cacheprovider -q
RESULT=PASS (29 passed)

Stage 5 + Stage 4B + Stage 7 relevant backend regressions:
python -B -m pytest tests/test_stage5_product_candidate_persistence.py tests/test_stage4b_phase2a_vnext.py tests/test_stage7_candidate_dashboard.py -p no:cacheprovider -q
RESULT=PASS (35 passed)

Full backend:
python -B -m pytest -p no:cacheprovider
RESULT=PASS (384 passed)

Ruff:
python -B -m ruff check --no-cache .
RESULT=PASS

Alembic heads:
python -B -m alembic heads
RESULT=PASS (20260818_0017, single head)

Frontend lint:
npm run lint
RESULT=PASS

Frontend production build:
npm run build
RESULT=PASS

Git whitespace validation:
git diff --check
RESULT=PASS
```

Frontend dependencies were installed with `npm ci --offline --ignore-scripts` from the existing
local cache. Generated `frontend/node_modules`, `frontend/.next`, and
`frontend/tsconfig.tsbuildinfo` were removed after successful verification. No registry endpoint was
contacted.

```text
MIGRATION_CREATED=NO
ALEMBIC_HEAD=20260818_0017
WORKFLOW_CHANGES=0
SCHEDULER_CHANGES=0
```

## Runtime truth — read-only verification

One explicit PostgreSQL `BEGIN READ ONLY` transaction verified the current runtime without exposing
credentials:

```text
THIRD_SCAN_RUN_ID=2c71e5bb-9334-4806-a195-0f8768d2d0f2
THIRD_SCAN_STATUS=COMPLETE
PRODUCT_CANDIDATES=7
PRODUCT_CANDIDATE_TRIGGERS=82
PRODUCT_CANDIDATE_CONTEXTS_FOR_RUN=0
ANOMALY_CONTEXT_DETAILS_FOR_RUN=0
PRODUCT_CANDIDATE_CONTEXTS_TOTAL=0
ANOMALY_CONTEXT_DETAILS_TOTAL=0
REMOTE_ALEMBIC_HEAD=20260818_0017

THIRD_RUN_MUTATED=NO
CANDIDATES_MUTATED=NO
TRIGGERS_MUTATED=NO
BASELINE_ROWS_ADDED=0
```

External endpoint ledger for this remediation:

- `postgresql://aws-0-ap-northeast-1.pooler.supabase.com:5432/postgres` — one credential-safe,
  explicit read-only verification transaction; zero writes.
- Nightwatch/vendor HTTP endpoints — none.
- npm registry, GitHub, workflows, or other external URLs — none.

## Authorization ledger

```text
APPLICATION_CODE_CHANGES=1
APPLICATION_CODE_CHANGE_PATHS=backend/app/db/models.py
TEST_CODE_CHANGES=1
TEST_CODE_CHANGE_PATHS=backend/tests/test_stage6_balanced_context.py

MIGRATION_CREATED=NO
REMOTE_DB_WRITES=0
NIGHTWATCH_REQUESTS=0
PAID_UNITS=0

WORKFLOW_CHANGES=0
SCHEDULER_CHANGES=0
COMMITS_CREATED=0
PUSHES=0
PRS_CREATED=0
MERGES=0
```

## Final package fields

```text
STAGE8_BASELINE_JSONB_REMEDIATION_RESULT=PASS

ROOT_CAUSE_ADDRESSED=YES

CONTRACT_SNAPSHOT_NONE_AS_NULL=TRUE
EXPIRY_ACTIVITY_RECAP_NONE_AS_NULL=TRUE

POSTGRES_NULL_BIND_BEHAVIOR_VERIFIED=YES
CONTRACT_BRANCH_VERIFIED=YES
EXPIRY_BRANCH_VERIFIED=YES

CHECK_CONSTRAINT_PRESERVED=YES
ORM_DB_SCHEMA_MISMATCH_RESOLVED=YES

FIRST_KNOWLEDGE_CUTOFF_LOGIC_CHANGED=NO
EXISTING_7_CANDIDATES_STILL_REUSABLE=YES

S4_IDENTIFIER_REMEDIATION_PRESERVED=YES
POST_CANDIDATE_PARTIAL_REMEDIATION_PRESERVED=YES

APPLICATION_CODE_CHANGES=1
TEST_CODE_CHANGES=1

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

FOURTH_MAG7_SCAN_AUTHORIZED=NO
BASELINE_RETRY_AUTHORIZED=NO
STAGE8_OBSERVATION_RESUME_READY=YES
STAGE9_READY=NO
NEXT_AUTHORIZED_STAGE=NONE
```

`STAGE8_OBSERVATION_RESUME_READY=YES` means only that the mapper defect is fixed and the existing
seven candidates are ready for a separately authorized baseline-only creation step. This task did
not create those baselines and authorizes no subsequent stage.

STOP.

# Nightwatch vNext — Stage 8 FIRST_KNOWLEDGE_BASELINE IntegrityError Diagnostic Report

**Date:** 2026-08-20  
**Mode:** zero-paid, read-only diagnostic  
**Worktree:** `F:\options-anomaly-scanner-stage8`  
**Branch:** `vnext/stage8-mag7-observation`

## Executive result

```text
BASELINE_DIAGNOSTIC_RESULT=ROOT_CAUSE_CONFIRMED
BASELINE_INTEGRITYERROR_ROOT_CAUSE_IDENTIFIED=YES
```

The Stage 6 detail mapper uses ordinary `JSONB` for two mutually exclusive nullable
payload columns. SQLAlchemy's default is `none_as_null=False`, so Python `None` is bound as the
JSONB value `null`, not SQL `NULL`. The deployed check constraint uses `IS NULL` to require the
opposite payload column to be absent. Consequently every constructed CONTRACT or EXPIRY detail
violates the constraint even though its Python object shape appears correct.

The first affected row is AAPL trigger
`0c559666-bc6c-47e4-aad5-3d3709ec8f70` (`AAPL260812P00307500`), a CONTRACT detail. Its
`expiry_activity_recap=None` becomes JSONB `null`; PostgreSQL therefore evaluates
`expiry_activity_recap IS NULL` as false and rejects the row.

This diagnostic performed no baseline retry, remote insert, migration, scanner invocation,
Nightwatch request, application edit, or historical repair.

## Governing evidence and package preservation

The attached execution package was absent from canonical evidence and was copied byte-for-byte to:

`F:\options-anomaly-scanner\docs\evidence\NIGHTWATCH_VNEXT_STAGE8_FIRST_KNOWLEDGE_BASELINE_INTEGRITYERROR_DIAGNOSTIC_EXECUTION_PACKAGE_20260820.md`

Attachment and canonical package SHA-256:

```text
4096265C2B4D56D74E64888D3469CCFF54B08D8EB82132F19D0849471ABA1C79
```

The following governing/report files were read completely from canonical evidence:

- `NIGHTWATCH_VNEXT_CANONICAL_EVIDENCE_MANIFEST.md`
- `NIGHTWATCH_SCANNER_VNEXT_INTEGRATED_SPEC_PROMPT_20260817(1).md`
- `NIGHTWATCH_VNEXT_STAGE5_PRODUCT_CANDIDATE_PERSISTENCE_COMPLETION_REPORT_20260818.md`
- `NIGHTWATCH_VNEXT_STAGE6_PHASE2B_BALANCED_MODEL_CODEX_EXECUTION_PACKAGE_20260818.md`
- `NIGHTWATCH_VNEXT_STAGE6_PHASE2B_BALANCED_MODEL_COMPLETION_REPORT_20260818.md`
- `NIGHTWATCH_VNEXT_STAGE6_BASELINE_CUTOFF_REMEDIATION_PASS_20260820.md`
- `NIGHTWATCH_VNEXT_THIRD_CONTROLLED_LIVE_MAG7_OBSERVATION_REPORT_20260820.md`
- `NIGHTWATCH_VNEXT_STAGE8_FIRST_KNOWLEDGE_BASELINE_INTEGRITYERROR_DIAGNOSTIC_EXECUTION_PACKAGE_20260820.md`

No governing evidence was missing or conflicting.

## Exact failure

```text
FAILING_CANDIDATE_ID=e515baba-d875-40a9-8278-4db2b1eb0ba2
FAILING_CANDIDATE_TICKER=AAPL

FAILING_FUNCTION=Stage6BalancedContextService._persist_evaluation detail INSERT/autoflush
TARGET_TABLE=anomaly_context_details
TARGET_COLUMN_OR_CONSTRAINT=ck_anomaly_context_details_anomaly_context_payload_matc_9467

DB_ERROR_CODE=23514
SANITIZED_DB_ERROR=CHECK VIOLATION on ck_anomaly_context_details_anomaly_context_payload_matc_9467; original DBAPIError.orig text was not persisted and no retained log containing it was found
OFFENDING_VALUE_SHAPE=CONTRACT detail with contract_snapshot JSON object and expiry_activity_recap Python None bound as JSONB null rather than SQL NULL
```

`23514` is the PostgreSQL SQLSTATE for check-constraint violation. It is established here from the
exact deployed constraint and deterministically reproduced bind behavior; the original driver error
object/text was not retained, so no purported original wording is quoted.

The deployed constraint is semantically:

```sql
(anomaly_entity_type = 'CONTRACT'
 AND contract_snapshot IS NOT NULL
 AND expiry_activity_recap IS NULL)
OR
(anomaly_entity_type = 'EXPIRY'
 AND contract_snapshot IS NULL
 AND expiry_activity_recap IS NOT NULL)
```

The model maps both `contract_snapshot` and `expiry_activity_recap` as default `JSONB`. Direct
inspection of each model column's PostgreSQL bind processor proved:

| Column | `none_as_null` | Python `None` binds as | SQL `IS NULL` |
|---|---:|---|---:|
| `contract_snapshot` | false | JSON text `null` | false |
| `expiry_activity_recap` | false | JSON text `null` | false |

This makes the constraint unsatisfiable for the objects produced by `_detail`: CONTRACT details
receive a JSON object plus JSON `null`; EXPIRY details receive JSON `null` plus a JSON object.

## Transaction ordering

```text
BASELINE_TRANSACTION_ORDER=load candidate and frozen triggers -> select cutoff-eligible archives -> add ProductCandidateContext -> explicit context flush/PK -> construct and add AnomalyContextDetail rows -> associate each detail with context -> ORM-query autoflushes pending details as needed -> final explicit detail flush -> outer commit
FIRST_DB_WRITE_CLASS=ProductCandidateContext
FIRST_DB_FLUSH_POINT=Stage6BalancedContextService._persist_evaluation immediately after session.add(context)
FAILURE_OCCURRED_BEFORE_OR_AFTER_FIRST_CONTEXT_FLUSH=AFTER_FIRST_CONTEXT_FLUSH
```

The context row itself satisfies its FK, allowed evaluation kind, time-order, string-length,
not-null, JSON serialization, and unique-baseline requirements. The context table was empty, so no
baseline unique-key collision existed. After the context flush, the first AAPL CONTRACT detail is
pending. Construction of the next CONTRACT detail performs an ORM read in `_deep_dive`; with the
normal Session's autoflush enabled, that read can surface the check violation before the final
explicit flush. Whether surfaced by that autoflush or the final flush, the rejected operation is
the first detail INSERT and the same constraint is deterministic.

The failure is not parent/child ordering, missing FK, duplicate identity, string length, numeric
precision, datetime ordering, enum vocabulary, or source availability. It is a JSON-null versus
SQL-NULL ORM/constraint contract mismatch.

## Seven candidate inputs

All candidates have immutable first knowledge
`2026-08-20T10:07:16.687134+00:00`, materialization version
`phase2a_vnext_stage4b.product-candidate-materialization.v1`, and hash
`482a09a33630f81288eabca9a46dc1d75b9374310f87d267c3dc9d3dcab73ebd`.

| Ticker | Candidate ID | Triggers | Baseline existed before/after diagnostic |
|---|---|---:|---|
| AAPL | `e515baba-d875-40a9-8278-4db2b1eb0ba2` | 13 | NO / NO |
| AMZN | `10ef5e5a-2d37-42cc-b547-5ca09c6cefa1` | 10 | NO / NO |
| GOOGL | `8194f5ab-8726-4cde-b88a-447865e449ee` | 9 | NO / NO |
| META | `d8a94e79-4d74-4e17-8538-0c1ad25f2171` | 4 | NO / NO |
| MSFT | `65977b65-f4f1-4290-bd1b-3ac6e7a27325` | 5 | NO / NO |
| NVDA | `c35ed996-bc4d-43b8-906d-8ae35e0998d6` | 27 | NO / NO |
| TSLA | `36d7ad31-2038-4f0e-bc61-e18fb1e4bfa1` | 14 | NO / NO |

Read-only counts proved 82 trigger rows and 82 distinct trigger IDs: 68 CONTRACT and 14 EXPIRY.
The recorded/insertion order is AAPL through TSLA as listed above. Since every detail has exactly
one Python-`None` mutually exclusive JSON field, the failure occurs on the first candidate when its
first detail is flushed.

```text
FAILURE_SCOPE=FIRST_CANDIDATE
```

## ORM, migration, and deployed schema

Runtime catalog inspection proved:

```text
REMOTE_ALEMBIC_HEAD=20260818_0017
PRODUCT_CANDIDATE_CONTEXT_ROWS=0
ANOMALY_CONTEXT_DETAIL_ROWS=0
NON_INTERNAL_TRIGGERS_ON_STAGE6_TABLES=0
RLS_POLICIES_ON_STAGE6_TABLES=0
RULES_ON_STAGE6_TABLES=0
```

PKs, FKs, unique indexes, nullability, varchar lengths, timestamptz/date types, JSONB columns, and
check expressions match migration `20260818_0017` and the ORM's declared DDL. There is no deployed
DDL drift. There is, however, a semantic ORM/DB mismatch: nullable JSONB columns use
`none_as_null=False`, while the declared/deployed check requires SQL NULL for the inactive payload.

```text
ORM_DB_SCHEMA_MISMATCH_FOUND=YES
ORM_DB_SCHEMA_MISMATCH=JSONB Python None serializes to JSON null but anomaly_context_payload_matches_entity requires SQL NULL
```

## Selector-output reconstruction and compact violation table

The accepted selectors and builders were executed for all seven candidates inside explicit
PostgreSQL `READ ONLY` transactions. A no-write session adapter delegated only reads and intercepted
`add`/`flush`; no INSERT was issued. All 7 contexts and all 82 details were reconstructed.

| Destination | Field/value shape | Target contract | Result |
|---|---|---|---|
| context | `FIRST_KNOWLEDGE_BASELINE` (24 chars) | varchar(32), allowed check | valid |
| context | spec/config/hash lengths 20/32/64 | varchar(64/96/64) | valid |
| context | evaluated time >= first knowledge | time-order check | valid |
| context | parent candidate FK | persisted candidate | valid |
| context | five JSON payloads | non-null JSONB | valid and strict-JSON serializable |
| detail | 82 distinct persisted trigger FKs | FK + context/trigger unique | valid |
| detail | entity values CONTRACT/EXPIRY | allowed check | valid |
| detail | anomaly identity max length 20 | varchar(128) | valid |
| detail | active payload Python object | JSONB `IS NOT NULL` | valid |
| detail | inactive payload Python `None` | must be SQL `NULL` | **invalid: binds as JSONB `null`** |
| detail | remaining JSON payloads | non-null JSONB | valid and strict-JSON serializable |

For each candidate the builder reached the expected two logical flush points and produced exactly
its persisted trigger count. No other invalid or unresolved destination field was found.

## Zero-paid reproduction

```text
ZERO_PAID_BASELINE_REPRODUCTION_ATTEMPTED=YES
ZERO_PAID_BASELINE_REPRODUCTION_RESULT=REPRODUCED
```

Two complementary offline checks reproduced the defect without the production database:

1. The actual model column's PostgreSQL dialect bind processor returned JSON text `null` for Python
   `None`, with `none_as_null=false`; applying the deployed check expression therefore yields false.
2. An in-memory SQLAlchemy table with the same JSON columns and check constraint raised
   `IntegrityError` when inserting the sanitized CONTRACT shape `{contract_snapshot: object,
   expiry_activity_recap: None}`. Constraint: `anomaly_context_payload_matches_entity`.

Focused existing Stage 6 tests were also run with an in-memory SQLite database, no Nightwatch key,
disabled pytest cache, and zero external calls:

```text
python -m pytest tests/test_stage6_balanced_context.py -p no:cacheprovider -q
27 passed
```

Their passing status explains why this escaped: current tests use recording/object harnesses and do
not assert the database distinction between JSON `null` and SQL NULL on the mutually exclusive
payload constraint.

## Defect class and remediation design

```text
DEFECT_CLASS=ORM_DB_SCHEMA_MISMATCH_DEFECT
DEFECT_IS_DETERMINISTIC_WITH_SAME_INPUT=YES
BASELINE_RETRY_WITHOUT_FIX_WOULD_LIKELY_REFAIL=YES

REMEDIATION_REQUIRED=YES
EXPECTED_FILES_TO_CHANGE=backend/app/db/models.py; backend/tests/test_stage6_balanced_context.py
MIGRATION_REQUIRED=NO
HISTORICAL_DATA_REPAIR_REQUIRED=NO
```

The narrow design is to make the two mutually exclusive JSONB mappings persist Python `None` as
SQL NULL (for example, explicit `JSONB(none_as_null=True)`) and add a real persistence regression
covering both CONTRACT and EXPIRY branches plus the check constraint. The deployed DDL is already
the intended contract, so widening, dropping, or changing the check constraint is unnecessary.
This report does not implement that design.

## Original first-knowledge baseline remains reconstructible

```text
EXISTING_CANDIDATES_REUSABLE_FOR_BASELINE_AFTER_FIX=YES
FOURTH_SCAN_NEEDED_TO_TEST_BASELINE_FIX=NO
ORIGINAL_FIRST_KNOWLEDGE_BASELINE_STILL_RECONSTRUCTIBLE=YES
```

The seven ProductCandidates and all 82 immutable triggers remain persisted. For every trigger,
`source_first_received_at`, `vendor_observed_at`, and `local_captured_at` are null or no later than
the candidate's immutable first-knowledge timestamp. The Stage 6 service derives
`evidence_cutoff_at` from that stored timestamp, not from invocation time.

Read-only source reconstruction found:

- AAPL, AMZN, GOOGL, META, NVDA, and TSLA each retain one cutoff-eligible row for all four archive
  sources (`daily_ohlc`, `stock_state`, `iv_rank`, `term_structure`).
- MSFT truthfully has no cutoff-eligible row for those four sources; accepted baseline semantics
  preserve these as `NOT_YET_AVAILABLE`, so no future evidence is needed or substituted.
- Each ticker retains five eligible archive-only Dealer/GEX snapshots; latest observed/captured
  times are before first knowledge.
- The accepted OHLC sanitizer still excludes bars after the cutoff NY trading date and fails closed
  on missing/malformed trading dates.

A later wall-clock invocation after the mapper fix cannot launder freshness because every raw
payload selector requires `received_at <= candidate_first_knowledge_at` and
`observed_at <= candidate_first_knowledge_at` when present; Dealer/GEX and chain selectors apply
equivalent vendor/local/quote cutoffs. Missing-at-cutoff evidence remains missing. No fourth scan or
paid refresh is required to create the original baselines from these persisted candidates.

## Runtime truth and authorization ledger

Final read-only verification preserved:

```text
THIRD_SCAN_RUN_ID=2c71e5bb-9334-4806-a195-0f8768d2d0f2
THIRD_SCAN_STATUS=COMPLETE
THIRD_SCAN_SAFE_ERROR=NONE
PRODUCT_CANDIDATES=7
PRODUCT_CANDIDATE_TRIGGERS=82
PRODUCT_CANDIDATE_CONTEXTS=0
ANOMALY_CONTEXT_DETAILS=0

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
```

External endpoints contacted during this diagnostic:

- `postgresql://aws-0-ap-northeast-1.pooler.supabase.com:5432/postgres` — credential-safe,
  explicit `READ ONLY` catalog/evidence queries only.
- Nightwatch/vendor HTTP endpoints — none.

## Final package fields

```text
BASELINE_DIAGNOSTIC_RESULT=ROOT_CAUSE_CONFIRMED
BASELINE_INTEGRITYERROR_ROOT_CAUSE_IDENTIFIED=YES

FAILING_CANDIDATE_ID=e515baba-d875-40a9-8278-4db2b1eb0ba2
FAILING_CANDIDATE_TICKER=AAPL
FAILING_FUNCTION=Stage6BalancedContextService._persist_evaluation detail INSERT/autoflush
TARGET_TABLE=anomaly_context_details
TARGET_COLUMN_OR_CONSTRAINT=ck_anomaly_context_details_anomaly_context_payload_matc_9467
DB_ERROR_CODE=23514
SANITIZED_DB_ERROR=CHECK VIOLATION; original DBAPIError.orig text unavailable

FAILURE_SCOPE=FIRST_CANDIDATE
ORM_DB_SCHEMA_MISMATCH_FOUND=YES

ZERO_PAID_BASELINE_REPRODUCTION_ATTEMPTED=YES
ZERO_PAID_BASELINE_REPRODUCTION_RESULT=REPRODUCED

DEFECT_CLASS=ORM_DB_SCHEMA_MISMATCH_DEFECT
DEFECT_IS_DETERMINISTIC_WITH_SAME_INPUT=YES
BASELINE_RETRY_WITHOUT_FIX_WOULD_LIKELY_REFAIL=YES

REMEDIATION_REQUIRED=YES
EXPECTED_FILES_TO_CHANGE=backend/app/db/models.py; backend/tests/test_stage6_balanced_context.py
MIGRATION_REQUIRED=NO
HISTORICAL_DATA_REPAIR_REQUIRED=NO

EXISTING_CANDIDATES_REUSABLE_FOR_BASELINE_AFTER_FIX=YES
FOURTH_SCAN_NEEDED_TO_TEST_BASELINE_FIX=NO
ORIGINAL_FIRST_KNOWLEDGE_BASELINE_STILL_RECONSTRUCTIBLE=YES

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
```

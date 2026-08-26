# Nightwatch vNext — Stage 8 S4 Stage-Identifier Length Remediation Report

Date: 2026-08-20

## Result

```text
STAGE8_S4_REMEDIATION_RESULT=PASS
```

The confirmed S4 telemetry-persistence failure was remediated within the existing `scan_stages.stage VARCHAR(32)` contract. No database schema, migration, runtime data, financial logic, budget behavior, workflow, scheduler, or universe was changed.

## Repository state and authorized scope

```text
WORKTREE=F:\options-anomaly-scanner-stage8
BRANCH=vnext/stage8-mag7-observation
BASE_HEAD=3a63eaa1b9069d34199704fe31ac6466e8929d7d
```

```text
AUTHORIZED_REMEDIATION_FILES:
- backend/app/scanner/v13.py: replace the single over-length active vNext S4 telemetry identifier
- backend/tests/test_stage4b_phase2a_vnext.py: add executable stage-identifier contract regression coverage
```

No other application, test, migration, workflow, or scheduler file was changed by this remediation.

## Confirmed call site and identifier inventory

The failing write originates in `app.scanner.v13.Mag7Scanner._select_dual()`, which calls the inherited `app.scanner.service.Mag7Scanner._stage()` telemetry persistence path after S4 selection state is committed.

Before editing, repository inspection found one active Stage 4 vNext stage identifier written by the v13 path:

| Call site | Identifier | Length | Contract |
|---|---|---:|---:|
| `backend/app/scanner/v13.py` — `Mag7Scanner._select_dual()` | `S4_VNEXT_DEEP_DIVE_BUDGET_SELECTION` | 35 | `VARCHAR(32)` |

The historical `S4_DUAL_SELECTION` and `S4_SELECTION` identifiers in older scanner implementations were not renamed.

## Remediation

```text
OLD_STAGE_IDENTIFIER=S4_VNEXT_DEEP_DIVE_BUDGET_SELECTION
NEW_STAGE_IDENTIFIER=S4_VNEXT_DEEP_BUDGET_SELECTION
OLD_IDENTIFIER_LENGTH=35
NEW_IDENTIFIER_LENGTH=30
TARGET_MAX_LENGTH=32
```

The replacement remains S4-prefixed and explicitly attributable to vNext Deep-Dive budget selection while fitting the existing column. The database column was not widened.

## Regression coverage

Added `test_active_stage4_vnext_stage_identifiers_fit_scan_stage_contract`. The test:

- executes the production `Mag7Scanner._select_dual()` path;
- captures the identifier sent to `_stage()`;
- proves the repaired identifier is exactly `S4_VNEXT_DEEP_BUDGET_SELECTION`;
- proves its length is 30;
- reads the maximum length from `ScanStage.__table__.c.stage.type.length`;
- proves every active vNext S4 identifier emitted by the exercised path is S4/vNext-prefixed and no longer than the ORM/database contract.

The existing Stage 4B semantic regression `test_production_projection_keeps_seven_persistence_candidates_before_budget` remains unchanged and passes. It continues to prove that seven qualifying ProductCandidates exist before only four tickers are selected for Deep-Dive analytics; budget selection therefore does not suppress ProductCandidate existence.

```text
ACTIVE_STAGE_IDENTIFIER_LENGTHS_VALID=YES
DATAERROR_REPRODUCTION_AFTER_FIX=NO
```

The post-fix result is based on deterministic local execution of the exact S4 selection call site and its ORM length contract. No live scan or remote insert was performed.

## Verification

| Verification | Result |
|---|---|
| Focused remediation regression | PASS — 1 passed |
| Stage 4B focused tests | PASS — 16 passed |
| Stage 5 regressions | PASS — 14 passed |
| Stage 6 regressions | PASS — 27 passed |
| Stage 7 relevant backend regressions | PASS — 3 passed |
| Full backend suite | PASS — 380 passed |
| Ruff | PASS — all checks passed (`--no-cache`) |
| Alembic heads | PASS — `20260818_0017 (head)` |
| `git diff --check` | PASS |

Ruff was run with `--no-cache` after its first invocation could not create `.ruff_cache` in the restricted Stage 8 worktree. The successful no-cache run performed the same lint checks without modifying that worktree cache.

```text
MIGRATION_CREATED=NO
ALEMBIC_HEAD=20260818_0017
```

## Runtime failed-run integrity

A read-only PostgreSQL transaction was used to re-check the authorized failed run. The transaction was explicitly set to `READ ONLY`, then rolled back and closed.

```text
SCAN_RUN_ID=090359ad-9d76-49b9-8902-f28ac54a1d1b
STATUS=FAILED
CANDIDATE_MATERIALIZED_AT=NULL
CANDIDATE_MATERIALIZATION_RULE_VERSION=NULL
CANDIDATE_MATERIALIZATION_RULE_HASH=NULL
PRODUCT_CANDIDATE_ROWS=0
FIRST_KNOWLEDGE_BASELINE_ROWS=0
FAILED_RUN_MUTATED=NO
```

No historical row was repaired or altered.

## External contact ledger

Exact endpoints contacted during this remediation:

- PostgreSQL `localhost:5432`: one unsuccessful connection attempt caused by the Stage 8 worktree falling back to its local default before the canonical runtime environment was explicitly loaded; no transaction was established.
- PostgreSQL `aws-0-ap-northeast-1.pooler.supabase.com:5432/postgres`: one successful read-only verification transaction.
- Nightwatch/API HTTP endpoints: none.

```text
NIGHTWATCH_REQUESTS=0
PAID_UNITS=0
REMOTE_DB_WRITES=0
```

## Change and authorization ledger

```text
APPLICATION_CODE_CHANGES=1
TEST_CODE_CHANGES=1
MIGRATION_CREATED=NO
WORKFLOW_CHANGES=0
SCHEDULER_CHANGES=0

SECOND_MAG7_SCAN_AUTHORIZED=NO
STAGE8_OBSERVATION_RESUME_READY=YES
STAGE9_READY=NO
NEXT_AUTHORIZED_STAGE=NONE
```

`STAGE8_OBSERVATION_RESUME_READY=YES` means the narrow code remediation and regression verification passed. It does not authorize or start another MAG7 scan, paid call, deployment, or Stage 9 activity.


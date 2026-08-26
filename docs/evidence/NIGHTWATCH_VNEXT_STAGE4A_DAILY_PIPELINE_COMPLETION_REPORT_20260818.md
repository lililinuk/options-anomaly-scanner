# Nightwatch Scanner vNext — Stage 4A Daily Data Pipeline Completion Report

**Date:** 2026-08-18  
**Stage:** 4A — Daily Data Pipeline

## A. RESULT

```text
STAGE4A_RESULT=PASS_WITH_CARRIED_ITEMS
```

## B. PREFLIGHT

```text
BRANCH=vnext/stage4a-daily-pipeline
HEAD_BASE=4f0edba28dc6939e1d60ba176d0281189e5ee67d
WORKTREE=F:\options-anomaly-scanner-stage4a
CLEAN_AT_START=YES
```

Stage 2/3 changes were present. No Stage 4B implementation was present.

## C. FILES CHANGED

- `.github/workflows/phase2a-daily-archive.yml` — durable Activity schedule and manual-only Radar/OI mode.
- `backend/alembic/versions/20260818_0015_stage4a_daily_pipeline.py` — additive Stage 4A migration.
- `backend/app/cli.py` — Activity/Radar-OI modes and scheduled invocation identity.
- `backend/app/db/models.py` — explicit coverage dates, versioned 0DTE storage, contract OI as-of.
- `backend/app/scanner/archive.py` — contract OI as-of persistence.
- `backend/app/scanner/daily.py` — source-separated modes, session guard, coverage semantics, canonical 0DTE writes.
- `backend/app/scanner/daily_semantics.py` — XNYS session planning and 0DTE classifications.
- `backend/app/scanner/parsers.py` — per-contract/vendor chain OI timestamp parsing.
- `backend/app/scanner/v12.py` — provisional interactive writes and canonical-only baseline reads.
- `backend/tests/test_stage4a_daily_pipeline.py` — G12/G25/E1/calendar/idempotence tests.
- `backend/tests/test_phase2a_daily_workflow.py` — workflow safety tests.

Dealer/GEX workflow: unchanged.

## D. COVERAGE SEMANTICS (E1)

New nullable fields:

- `activity_market_date` — Activity/XNYS session identity only.
- `vendor_oi_date` — Radar vendor OI date only.

Legacy `observation_date` remains for read compatibility. Historical rows were not backfilled or guessed. New writes set exactly one explicit field, enforced by database constraints.

## E. 0DTE (G12)

```text
PROVISIONAL_INTRADAY_BEHAVIOR=Interactive scans append PROVISIONAL_INTRADAY rows to versioned Stage 4A storage.
CANONICAL_SESSION_COMPLETE_BEHAVIOR=Daily Activity writes CANONICAL_SESSION_COMPLETE only after the authoritative XNYS close and matching vendor activity date; actual session_close_at is preserved.
LEGACY_AMBIGUOUS_BEHAVIOR=Accepted legacy-table rows remain unchanged and classify as LEGACY_OR_AMBIGUOUS.
CANONICAL_BASELINE_FILTER=Only prior CANONICAL_SESSION_COMPLETE rows from versioned Stage 4A storage enter the clean 20-observation baseline.
```

Provisional and canonical observations can coexist. Early-close, weekend, holiday, idempotence, and missing-data behavior are tested.

## F. CONTRACT OI AS-OF (G25)

```text
PARSER=Reads per-contract open_interest_as_of; uses the vendor chain-level open_interest_as_of when explicitly supplied for the chain.
PERSISTENCE=Stores nullable ContractOiDailySnapshot.open_interest_as_of separately from vendor_oi_date, vendor_oi_as_of, and local/raw receipt provenance.
READ_PATH=The normalized contract snapshot exposes the preserved field without substituting expiry dates or local capture time.
ABSENT_VALUE=NULL
```

Different contracts can retain different as-of timestamps. No expiry-date fallback was added.

## G. DAILY WORKFLOW (G19)

```text
WORKFLOW_FILE=.github/workflows/phase2a-daily-archive.yml
ACTIVITY_SCHEDULE_OR_GUARD=16:30 America/New_York weekday trigger plus authoritative backend XNYS non-trading-day and actual-session-close guard
RADAR_OI_COLLECTION_MODE=workflow_dispatch/manual --mode radar-oi only
RADAR_OI_SCHEDULE_ACTIVATION=PENDING_ROLLOVER_EVIDENCE
ROLLOVER_EVIDENCE_USED=Deployment machinery/report inspected; no committed results artifact or founder-accepted publication window exists
```

No speculative Radar/OI cron was activated.

## H. MIGRATION

```text
MIGRATION_CREATED=YES
ALEMBIC_HEAD=20260818_0015
ISOLATED_POSTGRES_RUNTIME_VERIFIED=NO
REMOTE_MIGRATION_RUN=NO
```

Single-head check passed. Offline PostgreSQL upgrade and downgrade SQL generation passed. No local PostgreSQL listener was available.

## I. TESTS

- Full backend: `319 passed`
- Focused Stage 4A/Stage 2/3 regressions: `86 passed`
- Ruff: passed
- Workflow YAML parsing/static validation: passed
- Alembic single-head and offline upgrade/downgrade: passed
- Frontend lint: passed
- Frontend production build: passed
- `git diff --check`: passed

## J. CARRIED ITEMS

- Radar/OI production timing remains pending founder-accepted rollover evidence.
- Isolated PostgreSQL runtime migration smoke remains unverified because no local instance was available.
- Stage 3 carried item `MIGRATION_RUNTIME_POSTGRES_VERIFIED=NO` remains.

## K. DIFF

```text
FILES_CHANGED=11
LINES_ADDED=822
LINES_REMOVED=42
WORKFLOW_FILES=1
MIGRATION_FILES=1
```

## L. AUTHORIZATION COMPLIANCE

```text
NIGHTWATCH_REQUESTS=0
PAID_UNITS=0
REMOTE_DB_WRITES=0
REMOTE_MIGRATIONS_RUN=0
WORKFLOWS_DISPATCHED=0
COMMITS_CREATED=0
PUSHES=0
PRS_CREATED=0
MERGES=0
```

External contact ledger: `npm ci` contacted the configured npm registry, `https://registry.npmjs.org/`, for lockfile-defined packages. No Nightwatch, application API, GitHub API, or remote database endpoint was contacted.

## M. SPEC IMPACT

```text
REOPEN_PHASE2A_VNEXT=NO
SPEC_AMENDMENT_REQUIRED=NO
STAGE_ORDER_CHANGE_REQUIRED=NO
```

## N. NEXT ACTION

```text
NEXT_AUTHORIZED_STAGE=NONE
```

# Nightwatch Scanner vNext — Stage 4B Phase 2A vNext — Completion Report

**Date:** 2026-08-18  
**Authorized scope:** Stage 4B only  
**Worktree:** `F:\options-anomaly-scanner-stage4b`

## A. RESULT

```text
STAGE4B_RESULT=PASS_WITH_CARRIED_ITEMS
```

Stage 4B is complete without a schema migration, Nightwatch request, remote database write,
workflow dispatch, commit, push, PR, or merge. Carried items are the explicitly deferred stages
and the founder-owned calibration of a numeric Persistence current-trigger freshness window.

## B. PREFLIGHT

```text
BRANCH=vnext/stage4b-phase2a-vnext
BASE_HEAD=4f0edba28dc6939e1d60ba176d0281189e5ee67d
WORKTREE=F:\options-anomaly-scanner-stage4b
CLEAN_AT_START=YES
```

- Repository root, branch, HEAD, and clean start matched the package exactly.
- Accepted Stage 2/3 changes were present in the 21-path checkpoint commit.
- Alembic had the single accepted `20260817_0014` head before and after implementation.
- No Stage 4A migration, workflow, canonical-EOD implementation, or daily-pipeline date split was
  present or added.

## C. ACTIVE ARCHITECTURE

```text
ACTIVE_DISCOVERY=[
 RADAR_EVENT,
 EXPIRY_ACTIVITY,
 CONTRACT_PERSISTENCE
]

REMOVED_ACTIVE_DISCOVERY=[
 EXPIRY_PERSISTENCE,
 STRUCTURAL_COLD_START,
 Evidence_Breadth
]

CANDIDATE_ENTITY=TICKER_PRODUCT_PROJECTION
ANOMALY_ENTITY=CONTRACT_OR_EXPIRY
PERSISTED_PRODUCT_CANDIDATE_CREATED=NO
```

New vNext scan rows no longer write legacy Discovery Score, Discovery Source, confirmation bonus,
or Evidence Breadth as active semantics. Removed routes cannot qualify a current candidate.

## D. PERSISTENCE

```text
NO_LOOKAHEAD_BOUND=ContractOiDailySnapshot.vendor_oi_date <= ExpiryObservation.vendor_oi_date, with a second domain analysis_date filter
WINDOW_SPAN_METADATA=window_first_observation_date, window_last_observation_date, valid_observation_count, analysis_date, no_lookahead_bound
CURRENT_TRIGGER_FRESHNESS_MODE=CALIBRATION_REQUIRED
FRESHNESS_CONFIG_VERSIONING=2026-08-18.calibration-required.v1 plus effective policy snapshot in scan configuration and contract read metadata
```

- The 3/5/10 anchors and thresholds are unchanged.
- A future OI observation cannot enter or alter an earlier Contract Persistence result.
- Persistence analytics remain computed and visible.
- With no founder-approved numeric window, Persistence cannot independently create a current
  Product Candidate. When another active anomaly qualifies the ticker, the Persistence anomaly is
  retained beneath the ticker as supporting evidence marked `not a current trigger`.
- A future explicitly configured value uses the named
  `MAX_VENDOR_OBSERVATION_AGE_CALENDAR_DAYS` mode and its own config version; no numeric value was
  invented in this tranche.

## E. EXPIRY ACTIVITY / 0DTE

- Expiry Activity independently qualifies the ticker projection without fabricating a contract.
- 0DTE remains a special calibration method inside Expiry Activity.
- 0DTE serialization now reports `ZERO_DTE_HISTORICAL_CALIBRATION` and its actual robust-deviation
  and historical-percentile components instead of the non-0DTE balanced/share-neighbor basis.
- Non-0DTE serialization exposes the actual comparable-neighbor volume ratio used by scoring,
  together with peer count, quality, median, and DTEs. The raw cross-expiry ratio is separated as
  descriptive-only, and missing comparators remain `NULL`.

## F. STRUCTURE / CLUSTER

- Structure, Neighbor Strike, and Cluster are serialized only as post-candidate Deep-Dive context.
- Sub-threshold Structure remains descriptive context with
  `structure_positive_evidence=false`.
- Only `VALID_CLUSTER` and `STRONG_CLUSTER` appear as positive cluster context or positioning
  labels; `INVALID_CLUSTER` remains preserved but is not positive evidence.
- Missing cluster concentration/liquidity components and missing net-change inputs remain `NULL`
  rather than analytical zero.
- Contract quote availability and `quote_as_of` are exposed from the complete daily chain archive.

## G. LEGACY CLEANUP

- Expiry Persistence and Structural Cold Start historical columns/data were not deleted or
  rewritten, but they cannot qualify vNext candidates.
- Evidence Breadth / `MULTI_EVIDENCE` is absent from vNext qualification and candidate projection.
- Legacy v1.2/v1.3 score summaries remain readable only inside an explicitly labeled
  `legacy_phase2a` API block and are not used by the vNext candidate projection.
- The working architecture identity is the non-numeric `phase2a_vnext_stage4b`; no unapproved
  production specification number was assigned.

## H. CANDIDATE PROJECTION

- The API builds an in-memory/domain Product Candidate projection grouped deterministically by
  ticker.
- Radar contract anomalies and Expiry Activity expiry anomalies independently qualify a ticker.
- Configured-current Contract Persistence can qualify a ticker; in the safe default it remains
  supporting/calibration-required evidence only.
- Every active anomaly for a qualified ticker is retained under `anomalies`, with separate
  `anomaly_count` and `qualifying_anomaly_count`.
- All seven MAG7 tickers can be represented. No top-4, 12-slot, ticker score, candidate score, or
  conviction score is used. Existing 4×3 chain-loading limits remain an explicitly logged
  Deep-Dive budget mechanism and do not affect candidate identity.

## I. MIGRATION

```text
MIGRATION_CREATED=NO
MIGRATION_COORDINATION_REQUIRED=NO
```

Existing nullable columns and JSON evidence/read-model fields were sufficient.

## J. TESTS

```text
python -m pytest -p no:cacheprovider
RESULT=PASS (319 passed)

python -m ruff check --no-cache app tests
RESULT=PASS

npm run test:glossary
RESULT=PASS

npm run lint
RESULT=PASS

npm run build
RESULT=PASS (Next.js production build and TypeScript passed)

python -m alembic heads
RESULT=PASS (20260817_0014 is the sole head)

git diff --check
RESULT=PASS
```

The first frontend build attempt used a temporary dependency junction and Turbopack rejected the
out-of-root symlink before compilation. Dependencies were then installed from the local npm cache
with `npm ci --offline --ignore-scripts`; the normal production build passed. Temporary
`node_modules` and `.next` directories were removed afterward.

## K. CARRIED ITEMS

1. Founder calibration/approval of a numeric Contract Persistence freshness window.
2. Stage 4A daily scheduling, canonical 0DTE storage/classification, contract
   `open_interest_as_of`, coverage-date split, and Stage 4A migration ownership.
3. Stage 5 persisted `ProductCandidate` / `ProductCandidateTrigger` entities and immutable
   candidate first-knowledge materialization.
4. Stage 6 Phase 2B Balanced Model.
5. Stage 7 full Candidate-first dashboard redesign; Stage 4B made only semantic compatibility
   changes required for truthful output.
6. Historical removed-route data and accepted old evaluations remain read-only and unrevised.

## L. DIFF

```text
FILES_CHANGED=17
LINES_ADDED=1041
LINES_REMOVED=185
MIGRATION_FILES=0
WORKFLOW_FILES=0
```

Counts describe the Stage 4B worktree diff only; this requested completion-report backup is stored
in the original worktree and is not part of that diff.

## M. AUTHORIZATION COMPLIANCE

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

```text
EXTERNAL_URLS_OR_API_ENDPOINTS_CONTACTED=[]
```

All npm dependency installation used `--offline`; automated tests used fixtures, mocks, and
in-process test clients.

## N. SPEC IMPACT

```text
REOPEN_PHASE2A_VNEXT=NO
SPEC_AMENDMENT_REQUIRED=NO
STAGE_ORDER_CHANGE_REQUIRED=NO
```

## O. NEXT ACTION

```text
NEXT_AUTHORIZED_STAGE=NONE
```

STOP. Stage 5 and Stage 6 were not started.

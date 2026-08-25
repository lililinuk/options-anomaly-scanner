# Nightwatch Scanner vNext — Stage 5 Product Candidate Persistence Completion Report

**Date:** 2026-08-18
**Stage:** 5 — Product Candidate Persistence
**Worktree:** `F:\options-anomaly-scanner-stage5`

## A. Executive result

```text
STAGE5_RESULT=PASS_WITH_CARRIED_ITEMS
```

Stage 5 prospectively persists the accepted Stage 4 ticker projection as immutable candidate
occurrences and active-family trigger rows. It adds no Phase 2A eligibility rule, score, threshold,
cross-run lifecycle, Stage 6 context, Forward Outcome, dashboard redesign, workflow, or vendor call.

## B. Preflight and repository orientation

```text
REPO_ROOT=F:\options-anomaly-scanner-stage5
BRANCH=vnext/stage5-product-candidate-persistence
HEAD_BEFORE=84b27b46311c35006def006621fe534b96c690d1
HEAD_AFTER=84b27b46311c35006def006621fe534b96c690d1
WORKTREE_CLEAN_AT_START=YES
INTEGRATED_STAGE4_BASE_PRESENT=YES
ALEMBIC_HEAD_BEFORE=20260818_0015
```

Repository orientation:

- Integrated Stage 4 head: `84b27b46311c35006def006621fe534b96c690d1`.
- Authoritative successful scan identity: immutable `ScanRun.id`.
- Successful scan write path: active `app.scanner.v13.Mag7Scanner` inherits the v11 `execute` /
  `_finish_v11` path; only `status=COMPLETE` invokes Stage 5 materialization.
- Stage 4 candidate projection entry point: `_v13_sections` using the shared
  `load_stage4_candidate_projection` path.
- Candidate grouping function: unchanged `group_product_candidates`.
- Radar source identity: `OiChangeRadarObservation.id`, explicit raw payload and request IDs.
- Expiry Activity source identity: `ExpiryObservation.id`, preserving its raw payload/request list.
- Persistence source identity: `ContractScanObservation.id`, including the accepted untruncated,
  deduplicated Persistence evidence selection.
- Stage 3 first-knowledge foundation: `CandidateFirstKnowledge` set-once UTC contract.
- Migration predecessor: `20260818_0015`.
- Current API read path: `GET /api/v1/scans/mag7/latest`; it remains read-only and delegates to the
  same Stage 4 projection implementation. Backend candidate repository/read serialization is
  additive and ordered.

The Stage 4A/4B execution-package files named by the opening prompt were not present in the
provided downloads, attachments, or accepted Stage 4 worktrees. The Founder-provided direct
integration result, accepted Stage 4A/4B completion reports, complete integrated spec, complete
Stage 3 package, complete Stage 5 package, and integrated repository state were available and
consistent.

## C. Authorized files changed

- `backend/app/db/models.py` — candidate/trigger models and immutable scan occurrence marker.
- `backend/alembic/versions/20260818_0016_stage5_product_candidate_persistence.py` — one additive
  Stage 5 migration.
- `backend/app/scanner/candidate_projection.py` — shared accepted Stage 4 projection and provenance.
- `backend/app/scanner/candidate_persistence.py` — idempotent materializer and ordered read support.
- `backend/app/scanner/v11.py` — successful-scan-only, same-transaction materialization hook and
  rollback before failure recording.
- `backend/app/api/routes/scans.py` — delegation to the shared projection; GET remains read-only.
- `backend/tests/test_stage5_product_candidate_persistence.py` — Stage 5 focused proofs.
- This completion report.

No frontend, workflow, scheduler, scoring, threshold, Dealer/GEX, Stage 6, or Forward Outcome file
was changed.

## D. Candidate occurrence and first knowledge

```text
PRODUCT_CANDIDATE_PERSISTED=YES
CANDIDATE_FIRST_KNOWLEDGE_PHYSICAL=YES
CANDIDATE_MATERIALIZATION_IDENTITY=ScanRun.id+ticker+phase2a_vnext_stage4b.product-candidate-materialization.v1
CROSS_RUN_CANDIDATE_LIFECYCLE=DEFERRED_NO_AUTO_MERGE

CANDIDATE_FIRST_KNOWLEDGE_IMMUTABLE=YES
CREATED_AT_USED_AS_FIRST_KNOWLEDGE=NO
EVENT_DATE_USED_AS_FIRST_KNOWLEDGE=NO
LATER_TRIGGER_CAN_REDATE_CANDIDATE=NO
```

`ScanRun.completed_at` is captured once immediately before the successful candidate
materialization transaction and becomes that occurrence's UTC knowledge cutoff only if candidate
materialization succeeds. The scan occurrence marker, candidate first knowledge, source scan,
rule version, and SHA-256 rule/configuration hash are set once. A failure rolls back candidate
writes before the run is recorded as failed.

A completed occurrence with zero candidates still receives the materialization marker. This keeps
a later replay from rebuilding an old zero-candidate occurrence using future database state.

## E. Trigger persistence and provenance

```text
PRODUCT_CANDIDATE_TRIGGER_PERSISTED=YES
TRIGGER_SOURCE_IDENTITY_PRESERVED=YES
SOURCE_FIRST_RECEIVED_PRESERVED=YES
VENDOR_LOCAL_TIME_SEPARATION_PRESERVED=YES
EXPIRY_TRIGGER_FABRICATES_CONTRACT=NO

FULL_ANOMALY_POOL_PERSISTED=YES
QUALIFYING_ANOMALY_COUNT_PRESERVED=YES
SUPPORTING_PERSISTENCE_DISTINGUISHED=YES
```

Only `RADAR_EVENT`, `EXPIRY_ACTIVITY`, and `CONTRACT_PERSISTENCE` can be persisted. Database checks
bind Radar/Persistence to contract entities and Expiry Activity to an expiry entity with the
matching explicit source FK. Every row preserves its normalized source-evidence identity, source
observation ID, raw payload/request IDs, event date, trigger first knowledge, first receipt,
vendor observation, local capture, qualification flag, first-knowledge membership, specification,
rule/configuration provenance, and audit creation time. Composite source-time detail is retained in
JSON without substituting local time for missing vendor time.

All initial active anomalies under a candidate are persisted, including supporting
`CALIBRATION_REQUIRED` Persistence with `qualifies_candidate=false`. Supporting-only Persistence
cannot create a candidate.

## F. Idempotence, no-lookahead, and read behavior

```text
CANDIDATE_REPLAY_DUPLICATION_FOUND=NO
TRIGGER_REPLAY_DUPLICATION_FOUND=NO
GET_CAUSES_CANDIDATE_WRITES=NO

LOGICAL_INPUT_ROWS=2
PERSISTED_LOGICAL_TRIGGER_ROWS=1
```

The scan marker freezes even a zero-row occurrence. Same-occurrence replay verifies stored
rule/hash and candidate identity, then reads persisted rows. It does not rebuild from later source
state. Trigger uniqueness is candidate + active family + authoritative source-evidence identity;
conflicting replay fails closed. Future receipt/capture/trigger knowledge timestamps cannot enter
the first-knowledge trigger set.

Backend read support returns candidate identity plus an ordered full trigger list. Repeated GET
proofs perform no `add`, `flush`, `commit`, or materializer call.

## G. Population proof

```text
QUALIFYING_TICKERS=7
PERSISTED_PRODUCT_CANDIDATE_COUNT=7
DEEP_DIVE_SELECTED_TICKER_COUNT=4
OMITTED_VALID_PRODUCT_CANDIDATES=0

PERSISTED_TRIGGER_COUNT=8
PERSISTED_QUALIFYING_TRIGGER_COUNT=7
```

The deterministic focused fixture materializes all seven MAG7 Product Candidates before the
four-ticker Deep-Dive budget. The eighth trigger is supporting Persistence and does not change the
seven qualifying-anomaly count.

## H. Migration and historical policy

```text
MIGRATION_CREATED=YES
ALEMBIC_HEAD=20260818_0016
ALEMBIC_SINGLE_HEAD=YES
HISTORICAL_BACKFILL_PERFORMED=NO
ISOLATED_POSTGRES_RUNTIME_VERIFIED=NO
REMOTE_MIGRATION_RUN=NO
```

Migration `20260818_0016` adds three nullable occurrence-marker columns to `scan_runs`, then creates
`product_candidates` and `product_candidate_triggers` with FKs, unique constraints, active-family /
entity/source consistency checks, and access-path indexes. It contains no historical data insert,
update, repair, or inferred first-knowledge value. Offline PostgreSQL upgrade and downgrade SQL
generation passed. No `psql`, PostgreSQL server, Docker, or Podman runtime was available.

## I. Test and verification evidence

- Focused Stage 5: passed — 14 tests.
- Stage 4A/4B focused regressions: passed.
- Stage 2/3 and Phase 2B predecessor regressions: passed.
- Full backend: passed — 349 tests.
- Ruff: passed.
- Alembic heads: passed — `20260818_0016` only.
- Offline PostgreSQL upgrade SQL: passed.
- Offline PostgreSQL downgrade `20260818_0016:20260818_0015` SQL: passed.
- Frontend glossary/null-safety: passed — 39 legacy columns, 128 documented fields.
- Frontend lint: passed.
- Frontend production build/TypeScript: passed.
- `git diff --check`: passed.

Frontend dependencies were installed from the local npm cache with
`npm ci --offline --ignore-scripts`. The temporary `frontend/node_modules` and `frontend/.next`
directories were removed after verification.

## J. Preserved boundaries and carried items

```text
PHASE2A_SCORING_CHANGED=NO
STAGE6_BALANCED_MODEL_STARTED=NO
FORWARD_OUTCOME_STARTED=NO
DASHBOARD_REDESIGN_STARTED=NO

CURRENT_TRIGGER_FRESHNESS_MODE=CALIBRATION_REQUIRED
RADAR_OI_SCHEDULE_ACTIVATION=PENDING_ROLLOVER_EVIDENCE
```

Carried items:

1. Founder calibration/approval of a numeric Contract Persistence current-trigger freshness
   window — future calibration gate after sufficient real accumulated data.
2. Radar/OI production schedule activation — rollover evidence gate.
3. Isolated PostgreSQL runtime migration verification — future isolated local PostgreSQL gate.
4. Cross-run candidate close/reopen/re-entry lifecycle — deferred; no auto-merge or timeout was
   invented.

## K. Diff summary

```text
FILES_CHANGED=8
LINES_ADDED=2098
LINES_REMOVED=289
MIGRATION_FILES=1
WORKFLOW_FILES=0
FRONTEND_FILES=0
```

## L. Authorization compliance

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

EXTERNAL_URLS_OR_API_ENDPOINTS_CONTACTED=[]
```

No external application, API, vendor, registry, GitHub, or database endpoint was contacted. The npm
install was explicitly offline and used only the pre-existing local cache.

## M. Final boundary

```text
REOPEN_PHASE2A_VNEXT=NO
REOPEN_PHASE2B_MODEL_B=NO
SPEC_AMENDMENT_REQUIRED=NO
STAGE_ORDER_CHANGE_REQUIRED=NO

STAGE6_READY=YES
NEXT_AUTHORIZED_STAGE=NONE
```

STOP. Stage 6 was not started.

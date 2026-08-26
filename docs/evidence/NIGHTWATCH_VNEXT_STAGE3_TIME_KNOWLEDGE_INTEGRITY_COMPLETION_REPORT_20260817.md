# Nightwatch Scanner vNext — Stage 3 Time / Knowledge Integrity Foundation — Completion Report

**Date:** 2026-08-17  
**Stage:** 3 — TIME / KNOWLEDGE INTEGRITY FOUNDATION

## A. EXECUTIVE RESULT

```text
STAGE3_RESULT = PASS_WITH_CARRIED_ITEMS
```

Stage 3 Time / Knowledge Integrity Foundation is implemented and verified. Stage 2 G1/G2 remains intact. No Stage 4A/4B or later-stage implementation was performed.

## B. PREFLIGHT / REPOSITORY ORIENTATION

```text
REPO_ROOT=F:\options-anomaly-scanner
BRANCH=fix/oi-change-rollover-workflow-context
HEAD_BEFORE=8a2573f406d1011bc06970a34cf26e506bf29e97
HEAD_AFTER=8a2573f406d1011bc06970a34cf26e506bf29e97
WORKTREE_STATE=DIRTY
```

Pre-existing state was preserved:

- Accepted uncommitted Stage 2 G1/G2 changes.
- Pre-existing `frontend/next-env.d.ts` change, restored byte-for-byte after Next.js build.
- Pre-existing untracked evidence/specification documents.
- No reset, checkout, clean, stash, revert, commit, or line-ending normalization.

Stage 2 predecessor status:

- G1: present and verified.
- G2: present; no `captured_at` or `ny_market_date` reassignment remains.
- Focused Stage 2 regression: 32 passed.
- Frontend G1 proxy regression: 5 passed.

Stage 3 files:

- `backend/app/db/models.py`
- `backend/alembic/versions/20260817_0014_stage3_time_knowledge_integrity.py`
- `backend/app/ingestion/raw.py`
- `backend/app/confirmation/provenance.py`
- `backend/app/confirmation/service.py`
- `backend/app/confirmation/workspace_v3.py`
- `backend/app/persistence/metadata.py`
- `backend/app/scanner/daily.py`
- `backend/app/scanner/archive.py`
- `backend/app/scanner/service.py`
- `backend/app/dealer_archive/service.py`
- `backend/tests/test_stage3_time_integrity.py`
- `backend/tests/test_phase2b_orchestration.py`
- `backend/tests/test_phase2b_v3_workspace.py`

Architecture remains separated as transport → immutable raw ingestion → normalization/analytics → persistence → API. Existing Phase 2B v1.2/v2.0/v3.1 layers remain readable and append-only.

## C. TIME FIELD INVENTORY

| Current field | Actual semantic | Target semantic | Action |
|---|---|---|---|
| `RawVendorPayload.received_at` | Local immutable raw receipt | `source_first_received_at` authority | Keep/reuse |
| `RawVendorPayload.observed_at` | Previously mixed vendor/local values | Vendor-provided timestamp or NULL | Retain column; rename ingestion API |
| Radar `captured_at` | Original local capture | Local capture identity | Keep immutable |
| Radar `ny_market_date` | NY date at original capture | Capture/run market date | Keep immutable |
| `ScanRun.started_at` | UTC run start | Run start | Keep |
| `ScanRun.market_date` | NY calendar date | Market-session/date identity | Keep; trading-day work remains Stage 4B |
| `ContractScanObservation.observed_at` | Local scan observation/evaluation time | Local analytical observation | Keep |
| `ExpiryObservation.observed_at` | Local scan observation/evaluation time | Local analytical observation | Keep |
| Context `created_at` | DB context materialization time | Materialization time only | Keep; removed from freshness |
| Phase 2B source `as_of` fields | Vendor-provided dates/timestamps | Vendor observation only | Preserve explicitly |
| Evaluation `evaluated_at` | Context evaluation time | `context_evaluated_at` | Keep and label explicitly in API |
| New `source_first_received_at` | Earliest linked authoritative raw receipt | Immutable first receipt | Add nullable |
| New `freshness_anchor_at` | Conservative source-aware cache anchor | Freshness authority | Add nullable |
| New `source_time_provenance` | Per-source vendor/local/receipt identities | Explicit provenance | Add nullable |
| New `evaluation_identity` | Baseline/refresh identity | Persisted identity | Add nullable |

## D. MIGRATION / SCHEMA CHANGES

Migration head is now `20260817_0014`.

Added to `phase2b_ticker_context_snapshots`:

- Nullable `source_first_received_at`.
- Nullable `freshness_anchor_at`.
- Nullable `source_time_provenance` JSONB.
- `(ticker, freshness_anchor_at)` index.

Added to `phase2b_candidate_evaluations`:

- Nullable `source_first_received_at`.
- Nullable `source_radar_observation_id` FK.
- Nullable `evaluation_identity`.
- Check constraint permitting only `FIRST_KNOWLEDGE_BASELINE`, `REFRESH`, or legacy NULL.
- `(contract_symbol, evaluation_identity)` index.

No historical `UPDATE`, guessed default, rename, replacement, or destructive upgrade operation exists. Offline PostgreSQL upgrade and downgrade SQL compiled successfully. Runtime migration execution was skipped because no isolated local PostgreSQL database was available; no remote database was contacted.

## E. SOURCE FIRST RECEIPT

`RawVendorPayload.received_at` remains the authority.

- `(source, request_id)` remains the explicit source identity.
- Repeated ingestion of identical evidence returns the preserved row.
- Receipt time cannot advance during reprocessing.
- Conflicting evidence under the same identity raises an error rather than overwriting history.
- Distinct source identities receive distinct receipt times.
- Missing linkage remains NULL/UNRESOLVED.

## F. VENDOR / LOCAL TIME SEPARATION

The raw-ingestion API now accepts `vendor_observed_at`, not ambiguous `observed_at`.

- Only explicit timezone-aware vendor timestamps are parsed.
- Date-only or absent values do not become vendor timestamps.
- Local capture comes from immutable `received_at`.
- Per-source provenance records `vendor_observed_at`, `local_captured_at`, and `source_first_received_at` separately.
- Heatmap workspace logic no longer falls back from missing vendor `generated_at` to local capture time.
- Stage 3-touched API output exposes explicit `time_provenance`.

## G. REPROCESS FRESHNESS

Prior behavior used context-row `created_at`, allowing preserved stale payloads to appear fresh after reprocessing.

New behavior:

- Cache lookup uses `freshness_anchor_at`.
- Successful source freshness uses vendor observation time when available, otherwise original authoritative receipt.
- Unavailable requests retain an explicitly labeled local request-attempt anchor while the feature remains `UNAVAILABLE`.
- Reprocessing preserves original source provenance and receipt-based age.
- Missing provenance never becomes fresh from `created_at`.
- Existing freshness thresholds were not changed.

## H. BASELINE / REFRESH IDENTITY

- Identity is persisted and constrained.
- Current exact-contract refresh workflow creates `REFRESH`.
- Future baseline creation can explicitly use `FIRST_KNOWLEDGE_BASELINE`.
- Identity cannot be mutated after it is known.
- Baseline and refresh records can coexist through append-only context/evaluation rows.
- Legacy rows remain NULL rather than being auto-promoted.
- Exact Radar source linkage prevents evaluation-time rebinding to a different Radar row after source selection.

## I. CANDIDATE FIRST-KNOWLEDGE FOUNDATION

```text
CANDIDATE_FIRST_KNOWLEDGE_FOUNDATION=INTERFACE_FOUNDATION_IMPLEMENTED_PHYSICAL_STORAGE_STAGE5
```

An immutable `CandidateFirstKnowledge` contract now represents:

- Nullable/unknown history.
- Set-once UTC first-knowledge time.
- Required materialization-rule version.
- Preservation against later anomaly arrivals or rule versions.

Physical persistence is deferred because no correct ProductCandidate record exists yet. No `ProductCandidate` or `ProductCandidateTrigger` entity was created.

## J. HISTORICAL DATA TREATMENT

```text
AUTHORITATIVE
- Existing RawVendorPayload.received_at
- Prospectively parsed vendor timestamps
- New exact source Radar linkage

RECONSTRUCTED
- New reprocessed context rows may derive receipt/freshness from preserved linked raw rows
- Original legacy rows are not modified

NULL_UNRESOLVED
- Legacy Stage 3 columns
- Missing/broken raw linkage
- Missing vendor timestamps
- Historical ProductCandidate first knowledge

SUSPECT
- Previously overwritten G2 Radar identity where raw linkage cannot recover it
- Existing 0DTE and G9-carried suspect history remains unchanged
```

No remote repair or historical bulk backfill occurred.

## K. TEST EVIDENCE

- Complete backend suite: **309 passed**.
- Stage 3 focused suite: **38 passed**.
- Stage 2 G1/G2 focused regression: **32 passed**.
- Frontend proxy regression: **5 passed**.
- Ruff across backend app/tests: passed.
- Frontend ESLint: passed.
- Frontend production build and TypeScript: passed.
- Alembic head check: `20260817_0014`.
- Offline PostgreSQL upgrade SQL: passed.
- Offline PostgreSQL downgrade SQL: passed.
- `git diff --check`: passed.

`npm test` does not exist; the actual proxy suite was run directly with Node. A compile-only attempt encountered pre-existing unwritable `__pycache__` directories, but executable imports, Ruff, and all test suites passed.

## L. CARRIED ITEMS

- Physical ProductCandidate first knowledge: Stage 5.
- Frozen ProductCandidate baseline materialization: Stage 5/6.
- Historical first-knowledge DB sampling: later DB-capable read-only proof.
- IV Rank vendor semantics: `WITHHOLD_PENDING_PROVENANCE`.
- N1 runtime heatmap distribution/removal: Stage 6.
- 0DTE classification/counts: Stage 4A.
- G9-contaminated persistence history: later research-sample exclusion.
- T1–T6 definitions: later governed evidence work.
- Runtime migration test: future isolated local/test PostgreSQL environment.

## M. OUT-OF-SCOPE FINDINGS

Intentionally unchanged:

- Phase 2A discovery/scoring/freshness rules.
- Daily scheduler and canonical 0DTE pipeline.
- Contract OI semantics.
- Structure/Cluster/Neighbor Ratio.
- Phase 2B Balanced Model and live heatmap removal.
- Candidate-first dashboard.
- Forward Outcome, Actionability, and Trade Expression.
- Dealer/GEX scheduler.
- Existing financial thresholds and weights.

## N. DIFF SUMMARY

```text
stage3 files changed: 14
lines added: 726
lines removed: 40
migration files: 1
workflow files: 0
frontend files: 0
```

The count excludes accepted Stage 2 G2 lines already present in `daily.py`. `frontend/next-env.d.ts` was restored to its exact preflight SHA-256.

## O. AUTHORIZATION COMPLIANCE

```text
NIGHTWATCH_REQUESTS=0
PAID_UNITS=0
REMOTE_DB_WRITES=0
REMOTE_MIGRATIONS_RUN=0
WORKFLOWS_DISPATCHED=0
COMMITS_CREATED=0
PUSHES=0
PRS_CREATED=0
```

External URLs/API endpoints contacted: **none**. `http://backend.invalid` appeared only as an inert mocked test value.

## P. SPEC IMPACT

```text
REOPEN_PHASE2A_VNEXT=NO
REOPEN_PHASE2B_MODEL_B=NO
SPEC_AMENDMENT_REQUIRED=NO
STAGE_ORDER_CHANGE_REQUIRED=NO
```

## Q. NEXT ACTION

```text
NEXT_AUTHORIZED_STAGE = NONE
```

Stage 4A / 4B may be recommended after founder review, but neither is authorized by this Stage 3 package.

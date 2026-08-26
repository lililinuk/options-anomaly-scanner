# Nightwatch Scanner vNext — Stage 1 Read-Only Repository Proof Gate — Evidence Report

**Date:** 2026-08-17
**Authorizing package:** STAGE 1 EXECUTION PACKAGE (founder-issued, this conversation)
**Baseline:** `NIGHTWATCH_SCANNER_VNEXT_INTEGRATED_SPEC_PROMPT_20260817.md` — v0.1 FOUNDER APPROVED
**Method note:** All code evidence read from read-only staged copies of the repository working tree (byte-identical mtimes verified against the files used by the 2026-08-17 reviews). Git inspection used `--no-optional-locks` and per-command `-c safe.directory` (no config written). Database connectivity was tested by TCP reachability only; no SQL session was established. `.env` was parsed machine-side only to extract host/port for the reachability test; no credential value was printed or persisted.

---

## 1. EXECUTIVE VERDICT

```text
STAGE1_VERDICT = PROCEED_WITH_CARRIED_UNRESOLVED_ITEMS
```

No architecture/integrity blocker was found. Every code-path claim underlying the approved spec was re-confirmed at current HEAD. All items that could not be completed are DB-evidence items blocked solely by database unreachability from this environment (postgres ports closed outbound) — they are carried as UNRESOLVED / REQUIRES_LATER_PROOF, exactly as the spec permits, and none of them invalidates a vNext assumption. No HOLD condition was met.

---

## 2. PREFLIGHT

```text
STAGE1_HEAD=8a2573f406d1011bc06970a34cf26e506bf29e97
STAGE1_BRANCH=fix/oi-change-rollover-workflow-context
PREEXISTING_WORKTREE_STATE=DIRTY
DB_READ_ACCESS=NO
NIGHTWATCH_CALLS_AUTHORIZED=NO
```

- Repository root: `F:\options-anomaly-scanner` (mounted read/write; treated read-only).
- Dirty state is **pre-existing and content-neutral**: 24 modified files are pure line-ending (CRLF/LF) noise — `git diff --numstat` shows insertions = deletions for every file (total 332/332); plus 6 untracked docs (evidence/spec markdown, including the approved integrated spec at `docs/specifications/NIGHTWATCH_SCANNER_VNEXT_INTEGRATED_SPEC_PROMPT_20260817.md`). Nothing was cleaned, stashed, or touched.
- **Difference vs the 2026-08-17 review baseline (1e29c92):** HEAD is 3 commits ahead, on a branch: `10c575c` (rollover timing experiment deploy), `4f7b5e1` (merge PR #1), `8a2573f` (workflow-safe prior-artifact path fix). These touch only `app/research/`, `.github/workflows/oi-change-rollover-timing-experiment.yml`, and docs. **Every Phase 2A/2B module cited by the reviews is byte-identical** (mtime match verified for all 30+ staged files) → all review line numbers remain valid at current HEAD.
- DB connectivity: DNS for the configured DB host resolves; TCP 5432 and 6543 are **blocked outbound** from this environment (443 open). Per package rules, no workaround was attempted; all DB-evidence items are classified below.
- Nightwatch: no process was started, no application endpoint was called, no vendor request was made.

---

## 3. N1 — DEAD PHASE 2B DEALER HEATMAP CALL

**A. Code-path proof (CONFIRMED at current HEAD):**

- Definition: `backend/app/confirmation/service.py:65-71` — `Phase2bContextService.ENDPOINTS` includes `("dealer_heatmap", "/v1/derived/heatmap/{ticker}/snapshot", {"format": "full"})`.
- When called: every **fresh** ticker-context fetch during `refresh-phase2b-context` (CLI `cli.py:51-61` → `refresh_contracts` → `_fetch_ticker_context`, service.py:231-316). Cache reuse (service.py:139-152) suppresses the call only within `min(five freshness settings)` of a prior same-spec/config context.
- Failure handling: `NightwatchError` → `statuses["dealer_heatmap"] = {status, availability: "UNAVAILABLE", error_code, captured_at, request_id}` (service.py:269-278); `normalize_heatmap_payload` marks any source status ≥400 as `availability="UNAVAILABLE"` (domain.py:327-334).
- Archive fallback: v3 workspace prefers `best_archived_surface_at_or_before(ticker, as_of=evaluation.evaluated_at)` (workspace_v3.py:565-570) with no-lookahead vendor+capture time bounds (`dealer_archive/repository.py`) — so displayed GEX structure comes from the archive when the live fetch failed.
- Corroborating project evidence: handoff §70 records vendor `HTTP 400 VALIDATION_ERROR` for this exact endpoint+`format=full` shape; dealer archive was fixed to `params=None` on 2026-08-14, **the Phase 2B path was not**. `docs/vendor/NIGHTWATCH_CAPABILITIES.md` documents heatmap snapshot cost 1 unit.

**B. DB evidence:** `endpoint_statuses['dealer_heatmap']` distribution — **NEEDS_DB_EVIDENCE** (DB unreachable; SELECT-only query specified for later: status/availability counts, date range, tickers).

**Verdict:**

```text
N1_DEAD_HEATMAP = PARTIALLY_CONFIRMED
(code-path CONFIRMED + documented vendor rejection of the identical request
shape; runtime endpoint_statuses distribution pending DB access)

SAFE_VNEXT_ACTION_IF_CONFIRMED =
REMOVE_PHASE2B_LIVE_HEATMAP_CALL_AND_USE_ARCHIVE_ONLY
(not implemented; Stage 6 scope)
```

---

## 4. IV RANK PROVENANCE (D2)

- **Trace:** endpoint `/v1/volatility/iv-rank/{ticker}` (service.py:68) → parse `data.iv_rank`, `data.date`, `data.as_of`, `classification=None` (service.py:283-288) → persisted in `Phase2bTickerContextSnapshot.iv_rank` JSON with raw_payload_ids + source_request_ids on the same row → displayed via `state_v2.build_volatility_state` (`iv_rank`, `iv_rank_vendor_date`, `iv_rank_as_of`) and the v3 workspace volatility block.
- **Entity:** `IV_RANK_ENTITY=TICKER` — path parameter is ticker only; no expiry/contract dimension anywhere in the trace. **VERIFIED.**
- **Vendor semantics:** repository contains **no authoritative definition** of what is ranked, over what historical window, or on what scale. `docs/vendor/NIGHTWATCH_CAPABILITIES.md:39` lists `volatility.iv_rank` as DISCOVER-CONFIRMED only; handoff §58 calls it "raw vendor IV Rank" without definition. Per the package's critical rule, semantics are **not** inferred from the field name.
- **Time identity:** vendor `date`/`as_of` are captured verbatim when present and kept separate from local `created_at`; no vendor→local fallback exists on this specific field (the mixed-key fallback is heatmap-specific). Whether the vendor actually populates `date`/`as_of` in stored rows requires raw-payload inspection → pending DB.
- **Provenance linkage:** schema-level linkage to raw payload + request id **exists**; row-level verification pending DB.

```text
IV_RANK_ENTITY=TICKER
IV_RANK_VENDOR_SEMANTICS=UNVERIFIED
IV_RANK_TIME_PROVENANCE=PARTIAL
VNEXT_CORE_ELIGIBILITY=WITHHOLD_PENDING_PROVENANCE
```

Remaining read-only proof (later, DB or vendor-doc based): raw iv-rank payload field inventory + value range, and an authoritative vendor definition. No Phase 2B change made.

---

## 5. FIRST-KNOWLEDGE RECONSTRUCTABILITY (G3)

**A. Timestamp semantics (write-path verified, not name-inferred):**

| Field | Actual semantic | Evidence |
|---|---|---|
| `RawVendorPayload.received_at` | local first receipt of a vendor payload; append-only; never mutated | models.py:75; ingestion path |
| `RawVendorPayload.observed_at` | vendor-provided observation time where parsed | models.py:74 |
| Radar `observation_date` / `previous_date` | authoritative **vendor** dates | daily.py radar parse; audit §7 confirmed |
| Radar `captured_at` / `ny_market_date` | **MUTATED in place** on re-evaluation (`row.captured_at = utc_now()`) — unreliable as first receipt | daily.py:596-597 |
| `ScanRun.started_at` | local run start (authoritative for scan-discovered evidence) | models.py:31 |
| `ScanRun.market_date` | local NY calendar day, **no trading-day check** | core/time.py:24-25 |
| `ContractScanObservation.observed_at` / `ExpiryObservation.observed_at` | scan-time `utc_now()`, append-only per run | v11.py:485 |
| `Phase2bCandidateEvaluation.evaluated_at` | evaluation time; one row per (context, contract); "at detection" fields rebind to the **latest** radar row at evaluation time | service.py:321-343, 329-333 |
| `ZeroDteActivityDailySnapshot` | carries `scan_run_id` XOR `daily_run_id` origin linkage + raw payload id | models.py:470-471; v12.py:362; daily.py:411-412 |

**B. Representative sampling:** **NEEDS_DB_EVIDENCE** → each sample classification carried as UNRESOLVED / REQUIRES_LATER_PROOF. No timestamps were reconstructed or written.

**C. Route-level conclusion (code/schema basis, sampling pending):**

```text
RADAR_FIRST_KNOWLEDGE_RECONSTRUCTABILITY = RECONSTRUCTABLE_WITH_PROVENANCE*
  vendor observation_date + RawVendorPayload.received_at chain survive
  append-only; *rows whose original captured_at was overwritten (G2) and
  whose raw linkage is broken degrade to PARTIAL/UNRESOLVED

EXPIRY_ACTIVITY_FIRST_KNOWLEDGE_RECONSTRUCTABILITY = RECONSTRUCTABLE_WITH_PROVENANCE
  observed_at + scan_run linkage, append-only, no known mutation path

CONTRACT_PERSISTENCE_FIRST_KNOWLEDGE_RECONSTRUCTABILITY = PARTIAL
  underlying archive vendor dates authoritative, but "when the candidate rule
  was actually satisfiable" is complicated by unbounded lookback (G8) and the
  lookahead window defect (G9); affected evaluations are identifiable but not
  first-knowledge-authoritative

HISTORICAL_PRODUCT_CANDIDATE_FIRST_KNOWLEDGE = PARTIAL
  the entity never existed historically; reconstruction is possible only
  per-anomaly where the chains above survive; anything else stays
  NULL / UNRESOLVED per the approved spec — this is acceptable, not a blocker
```

---

## 6. 0DTE HISTORICAL CLASSIFICATION (G12)

**A. Schema/code proof (CONFIRMED at current HEAD):**

- Interactive scan write: `v12.py:343-369` — `ZeroDteActivityDailySnapshot(scan_run_id=self.run.id, …)`, first-writer-wins (existence check v12.py:351-358, keyed ticker+observation_date).
- Daily collector write: `daily.py:390-424` — `scan_run_id=None, daily_run_id=self.pipeline.run.id`, skips if a row already exists (daily.py:401-408) — i.e. an earlier intraday interactive snapshot **blocks** the daily one.
- Rows carry `raw_payload_id`, `source_request_id`, and run FKs; runs carry `started_at`.

**Key Stage-1 finding:** origin is **authoritatively classifiable from run linkage** — `scan_run_id NOT NULL` ⇒ interactive-scan origin (intraday-risk); `daily_run_id NOT NULL` ⇒ daily-collector origin. No clock-guessing needed. However, collector origin ≠ proven session-complete EOD: there is **no session-completeness flag**, and the daily job is manually invoked (G19), so its execution time is unconstrained. Full "CANONICAL_EOD" proof therefore needs run `started_at` vs session close per row — a later SELECT-only analysis.

**B. Historical counts:**

```text
0DTE_ROWS_TOTAL=NEEDS_DB_EVIDENCE
0DTE_PROVABLE_EOD=NEEDS_DB_EVIDENCE
0DTE_PROVABLE_INTRADAY=NEEDS_DB_EVIDENCE
0DTE_AMBIGUOUS=NEEDS_DB_EVIDENCE
```

**Verdict:**

```text
HISTORICAL_0DTE_BASELINE_TRUST = PARTIALLY_CLASSIFIABLE
(schema-level classification proven possible; row counts pending DB)
```

Recommendation (not performed): future Stage 4A migration marks interactive-origin rows `PROVISIONAL_INTRADAY` → `SUSPECT / CALIBRATION_INELIGIBLE`; daily-origin rows evaluated against session close; unresolvable rows `SUSPECT`. No row modified now.

---

## 7. PHASE 2B CURRENT-HEAD RECONSTRUCTION

- **A. Layers (CONFIRMED):** L1 `Phase2bTickerContextSnapshot` + `Phase2bCandidateEvaluation` (`signal_spec_v1.2_phase2b`, confirmation/config.py:11); L2 `Phase2bCandidateState` (`signal_spec_v2.0_phase2b`, state_v2.py:21); L3 `Phase2bV3ResearchWorkspace` (`signal_spec_v3.1_phase2b`, workspace_v3.py:23). Exact model names as listed.
- **B. Entry gate (CONFIRMED):** `_candidate_source` (service.py:116-137) requires a radar row with `deep_dive_eligible=True` **and** a chain snapshot; otherwise silently returns None. Therefore at current HEAD: CONTRACT_PERSISTENCE-only exact contracts → **cannot enter Phase 2B**; EXPIRY_ACTIVITY-only / expiry anomalies → **cannot enter Phase 2B** (additionally UI-guarded: only `entity_type === "CONTRACT"` opens a workspace, enforced by check-glossary.mjs:68-70).
- **C. Shared ticker context (CONFIRMED):** candidates grouped by ticker; one context serves all contracts of the ticker. Cache key = (ticker, spec version, config version, config hash) with freshness `created_at >= now − min(5 freshness settings)` (service.py:139-152). Freshness basis = **local `created_at`**.
- **D. Reprocess freshness (CONFIRMED):** `_reprocess_ticker_context` (service.py:162-220) re-normalizes preserved raw OHLC + old dealer heatmap into a **new row stamped `created_at=utc_now()`**, which then satisfies the created_at-based freshness check → stale vendor evidence can present as fresh. (Reprocessed rows are identifiable via `endpoint_statuses.daily_ohlc_reprocessing.source=PRESERVED_RAW_PAYLOAD`.)
- **E. Chain reuse (CONFIRMED):** `ContractOiDailySnapshot` persists per-contract bid/ask/IV/delta/gamma/theta/vega/charm/underlying + `quote_as_of`/`greeks_as_of` (archive.py:264-291); the evaluation already reads it with zero API calls (service.py:334-338, 359-390). **vNext B4 fields (contract IV, Delta, bid/ask, spread) are servable from archived chain data shared per ticker-expiry, with no per-contract calls.**
- **F. Manual refresh cost path (from code only, nothing executed):**

```text
CURRENT_PHASE2B_ENDPOINTS=[
  GET /v1/stocks/ohlc/{ticker}?candle_size=1d,
  GET /v1/stocks/stock-state/{ticker},
  GET /v1/volatility/iv-rank/{ticker},
  GET /v1/volatility/term-structure/{ticker},
  GET /v1/derived/heatmap/{ticker}/snapshot?format=full   ← documented-invalid shape
]
CURRENT_EXPECTED_CALLS_PER_FRESH_TICKER=5
(5 network attempts; 4 expected-successful paid calls + 1 expected-400;
whether a 400 consumes a paid unit is not locally provable — carried item)
```

---

## 8. AUDIT DEFECT CURRENT-HEAD MATRIX

All review line numbers re-verified valid at HEAD 8a2573f (cited modules byte-identical to review baseline).

| ID | Current status | Evidence | Planned stage still correct? |
|---|---|---|---|
| G1 | CONFIRMED_CURRENT_HEAD | `mag7-scan/route.ts:11` GET catch → 200 `{scan:null,results:[]}` | YES — S2 |
| G2 | CONFIRMED_CURRENT_HEAD | `daily.py:596-597` in-place `captured_at`/`ny_market_date` overwrite | YES — S2 |
| G3 | CONFIRMED_CURRENT_HEAD | `service.py:117-124, 329-333` latest-radar rebind | YES — S3 |
| G4 | CONFIRMED_CURRENT_HEAD | `service.py:206,310`; `workspace_v3.py:215` `generated_at or capture_timestamp` | YES — S3 |
| G5 | CONFIRMED_CURRENT_HEAD | `service.py:139-152` + `162-220` | YES — S3 |
| G7 | CONFIRMED_CURRENT_HEAD | `core/time.py:24-25` no trading-day check; `v11.py:486-488` scan-day DTE on vendor-dated data | YES — S4B |
| G8 | CONFIRMED_CURRENT_HEAD | `v13.py:284-299` unbounded lookback trigger | YES — S4B |
| G9 | CONFIRMED_CURRENT_HEAD | `v11.py:414-428` history query lacks `vendor_oi_date <=` bound | YES — S4B |
| G10 | CONFIRMED_CURRENT_HEAD | `history.py:42-45` last-N compression; span dates not persisted | YES — S4B |
| G11 | CONFIRMED_CURRENT_HEAD | `v13.py:126-137` two-key basis → 0DTE rows "BALANCED/0/0" | YES — S4B |
| G12 | CONFIRMED_CURRENT_HEAD (code) + NEEDS_DB_EVIDENCE (extent) | `v12.py:351-358`; `daily.py:401-408` | YES — S4A |
| G13 | CONFIRMED_CURRENT_HEAD | `scoring.py:460-462` comparable ratio unpersisted (`v12.py:265-268` stores median/count/dtes/quality only); glossary:79 wrong (OI + comparable) | YES — S4B |
| G14 | CONFIRMED_CURRENT_HEAD | `scans.py:584-593` INVALID cluster → CALL/PUT_STRUCTURE | YES — S4B |
| G15 | CONFIRMED_CURRENT_HEAD (code present; obsoleted by target arch) | `state_v2.py:204-217` | YES — obsoleted at S6; gating at S4B/S6 |
| G16 | CONFIRMED_CURRENT_HEAD | `service.py:351-356, 412-416` top-5 clusters unfiltered | YES — S6 |
| G17 | CONFIRMED_CURRENT_HEAD | `workspace_v3.py:308-310` tautological BIAS; `276-280` no magnitude | YES — S6 |
| G18 | CONFIRMED_CURRENT_HEAD | `workspace_v3.py:163` float equality; `domain.py:430-437` missing-strike distance 0 | YES — S6 |
| G19 | CONFIRMED_CURRENT_HEAD | `.github/workflows/` = dealer-gex + rollover only; README:47 requires external SGT-12:00 invocation | YES — S4A |
| G20 | CONFIRMED_CURRENT_HEAD | payload carries `started_at/consumed_quota_units` (scans.py:224-239); dashboard renders neither (grep: no match) | YES — S7 |
| G21 | CONFIRMED_CURRENT_HEAD | `scans.py:74-81` silent v1.2 fallback; `99-106, 214-216` discovery_score-driven blocks | YES — S4B/S7 |
| G22/N1 | CONFIRMED (code) / NEEDS_DB_EVIDENCE (runtime) | §3 above | YES — S6 (after DB proof) |
| G23/N2 | CONFIRMED_CURRENT_HEAD | `service.py:116-137` | YES — S6 |
| G24 | CONFIRMED_CURRENT_HEAD | CLI-only refresh (`cli.py:51-71`); 404 dead end (`scans.py:250-259`); expiry-only unclickable | YES — S6/S7 |
| G25 | CONFIRMED_CURRENT_HEAD | `parsers.py:398-401` parses `open_interest_as_of`; `archive.py:264-291` drops it; contract rows inherit expiry `vendor_oi_date` | YES — S4A |
| G26 | CONFIRMED_CURRENT_HEAD | `clusters.py:236-245` zero-fill; `v11.py:465` quote_supplied = bid OR ask; `config.py:26-29` Asia/Singapore 12:00 archive → overnight quotes | YES — S4B |
| G27 | CONFIRMED_CURRENT_HEAD | glossary:55 (volume_oi_ratio as current), :66 (`<10` vs actual `<3`, history.py:32-39), :79 (neighbor_ratio "OI/comparable"), :86 (premium-weighted center vs OI-weighted clusters.py:267-269), :88 (LADDER); check-glossary.mjs = presence/string checks only | YES — S7 |
| G29 | CONFIRMED_CURRENT_HEAD | `scans.py:567-581` full zero_dte_status in API; dashboard: no zero_dte rendering (grep) | YES — S7 |
| G30 | CONFIRMED_CURRENT_HEAD | dashboard file unchanged since review (mtime match); candidates section remains last | YES — S7 |
| E1 | CONFIRMED_CURRENT_HEAD | `daily.py:369` (ACTIVITY = NY market date) vs `daily.py:624-629` (RADAR = vendor observation_date) under one column | YES — S4A |
| E2 | CONFIRMED_CURRENT_HEAD | `scans.py:270-289` latest-date-per-ticker + NULL-premium-as-0 sort | YES — S7 (labeling) |

**Not re-verified this stage (presentation sub-details):** status-dot color palette (globals.css not staged) — carried as a Stage 7 display item; does not affect any stage assignment.

---

## 9. T1–T6

```text
T1_T6_DEFINITION_SOURCE=NOT_AVAILABLE
```

The exact authoritative T1–T6 query definitions are **not present in the repository**: the only files mentioning them are the 2026-08-17 Phase 2B review and the integrated spec (both reference their existence; the originating Phase 2A architecture review was delivered in chat and never committed). Per package rules they were **not** fabricated from memory. Additionally, all six require SELECT access to the database, which is unreachable from this environment.

```text
T1=UNRESOLVED   T2=UNRESOLVED   T3=UNRESOLVED
T4=UNRESOLVED   T5=UNRESOLVED   T6=UNRESOLVED
```

Carried recommendation: commit the authoritative T1–T6 definitions into `docs/` before or during Stage 4B so they become runnable in a DB-capable read-only session.

---

## 10. SPEC IMPACT

- Does any finding require reopening Phase 2A vNext? **NO.**
- Does any finding require reopening Phase 2B Model B? **NO.**
- Does any finding change the approved Stage order? **NO.** (One positive note: the 0DTE origin-linkage finding in §6 makes Stage 4A's SUSPECT-marking migration *easier* than assumed.)
- Does any finding require an amendment to the integrated spec? **NO amendment required.** Two non-normative annotations are suggested at the next spec revision: (a) record that current HEAD is `8a2573f` on a branch ahead of the review baseline with only research/workflow deltas; (b) record that `ZeroDteActivityDailySnapshot` origin is classifiable via `scan_run_id`/`daily_run_id`.

---

## 11. CARRIED UNRESOLVED ITEMS

Later implementation packages must preserve the following as NULL / UNRESOLVED / SUSPECT / VALIDATE-FIRST:

1. **N1 runtime distribution** — dealer_heatmap endpoint_statuses counts: REQUIRES_LATER_PROOF (SELECT-only, DB-capable session) before the Stage 6 call removal is marked "proven" rather than "code-confirmed".
2. **IV Rank** — `WITHHOLD_PENDING_PROVENANCE`; raw-payload field inventory + authoritative vendor definition outstanding; display (if any) must carry provenance-unverified marking until then.
3. **First-knowledge sampling** — per-sample reconstruction classification (Proof 3B): REQUIRES_LATER_PROOF; reconstructed anchors, when later computed, must be marked RECONSTRUCTED and never overwrite anything.
4. **G2 overwritten history** — radar rows whose original `captured_at`/`ny_market_date` were overwritten are **permanently UNRESOLVED** for first-receipt purposes (recoverable only where RawVendorPayload linkage survives).
5. **0DTE row counts** — EOD/intraday/ambiguous tallies: REQUIRES_LATER_PROOF; interactive-origin rows are presumptive `SUSPECT / CALIBRATION_INELIGIBLE` until classified.
6. **G9-affected persistence evaluations** — historical scores computed with possible lookahead: excluded from any future clean research sample; never rewritten.
7. **T1–T6** — definitions to be committed, then run read-only.
8. **GEX BIAS/RISK wording, IV topology states, 40-gate fallback consequence, execution-quality gating** — all VALIDATE-FIRST per the approved spec.
9. **Paid-unit consumption of HTTP 400 responses** — not locally provable; do not assume zero-cost failure in budget planning.

---

## 12. AUTHORIZATION COMPLIANCE

```text
NIGHTWATCH_REQUESTS=0
PAID_UNITS=0
DB_WRITES=0
CODE_CHANGES=0
REPO_CHANGES=0
```

Notes: no application process was started; no scanner/scan/refresh/archive/backfill/workflow was invoked; git was used with `--no-optional-locks` and per-invocation `-c` flags only; the DB reachability check was a TCP connect attempt (no SQL, no authentication handshake completed); `.env` was parsed only to extract host/port for that check, with no credential printed, logged, or retained; the pre-existing dirty worktree was left untouched.

---

## 13. NEXT ACTION

```text
NEXT_AUTHORIZED_STAGE = NONE
```

Stage 2 is recommended but NOT authorized by this Stage 1 package.
Return this report to the founder for review and a separate Stage 2
authorization.

---

*Evidence sourced from: read-only staged working-tree copies (30+ files, mtime-verified against review baseline), `git --no-optional-locks` inspection on the device, `docs/vendor/NIGHTWATCH_CAPABILITIES.md`, README.md, `.github/workflows/`, and the four governing documents. No fix, migration, write, or vendor call was performed.*

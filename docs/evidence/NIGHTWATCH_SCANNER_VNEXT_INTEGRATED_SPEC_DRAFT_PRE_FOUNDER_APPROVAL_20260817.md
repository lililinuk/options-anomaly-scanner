# Nightwatch Options Anomaly Scanner — vNext Integrated Spec Prompt

**Date:** 2026-08-17
**Status:** `DRAFT v0.1 — PENDING FOUNDER REVIEW`
**Authorization state:** This document authorizes **nothing yet**. No code change, no DB write, no paid Nightwatch call may be performed on the basis of this draft. Upon founder approval it becomes the working architecture baseline; each implementation stage still requires its own scoped execution package.
**Working names:** `Phase 2A vNext` / `Phase 2B vNext (Balanced Product-Candidate Context Model)`. Production spec version numbers (e.g. `signal_spec_v2.0_phase2a`, `signal_spec_v4.0_phase2b`) are **not assigned** until the migration/versioning plan is reviewed.

**This document integrates:**

1. `PHASE2A_VNEXT_DECISION_HANDOFF_20260817.md` — founder-approved Phase 2A architecture (normative; restated, not reopened)
2. `NIGHTWATCH_SCANNER_INDEPENDENT_AUDIT_20260817.md` — code-verified defect inventory
3. `NIGHTWATCH_OPTIONS_ANOMALY_SCANNER_HANDOFF_20260815` — implemented baseline reference
4. Claude Phase 2B Fresh Review (`docs/evidence/PHASE2B_FRESH_INDEPENDENT_ARCHITECTURE_REVIEW_20260817.md`)
5. Engineer Phase 2B Fresh Review (2026-08-17)
6. Founder decisions D1–D8 resolving all divergences between the two reviews (§0.2)
7. The Research-Loop / Live-Loop dual-loop clarification of the Forward Outcome boundary (§8)

Where the two reviews agreed, this spec records the shared conclusion. Where they diverged, the founder decision log below is authoritative.

---

# PART 0 — Decision Provenance

## 0.1 Both-review consensus (double-confirmed, adopted without further debate)

- Phase 2A vNext has **no critical technical incompatibility**; it is not reopened anywhere in this spec.
- Phase 2B v3.1 must not be extended as-is; it is also not discarded — content mostly survives, the frame is rebuilt.
- **Model B — Balanced** is the Phase 2B architecture, with five conceptual blocks (§5).
- `candidate_first_knowledge_at` is immutable; later re-evaluation can never rewrite first knowledge.
- `STABILIZATION_BIAS` / `DOWNSIDE_ACCELERATION_RISK` are removed as labels (tautological / no magnitude); raw GEX node values remain.
- Gamma / Theta / Vega leave Phase 2B display (still archived with chain snapshots; they are Trade Expression inputs).
- Evidence Breadth / `MULTI_EVIDENCE` is removed. Structure / Neighbor-Strike (merged) / Cluster are Phase 2A Deep-Dive context, VALID-gated in any positive display.
- Dealer/GEX daily archive and its scheduler are untouched.
- Dashboard becomes Candidate-first with an explicit availability state machine.
- Ticker-level context is shared once per Product Candidate; no per-anomaly repeated API calls.
- Forward Outcome anchors on `candidate_first_knowledge_at`, never on mutable `evaluated_at` or bare `event_date`.
- No new thresholds, weights, rankings, universal scores, or directional inference anywhere in this spec. `VALIDATE-FIRST` marks everything that would need outcome evidence.

## 0.2 Founder decision log — 2026-08-17 (authoritative for all review divergences)

| # | Question | Founder decision | Encoding in this spec |
|---|---|---|---|
| D1 | Shorter/longer expiry IV + local IV topology: core or expanded? | **Engineer version — demote to EXPANDED CONTEXT** | §5.3: candidate-expiry IV is core; shorter/longer nodes + topology retained as expandable secondary display (data still derives from the same single term-structure payload) |
| D2 | IV Rank | **Engineer version — VALIDATE-FIRST** | §5.3 + §10 Stage 1: read-only proof of vendor semantics / entity / timestamps required; keep as raw core only if proven; until then displayed with provenance-unverified marking or withheld |
| D3 | Implied Move | **KEEP-OPTIONAL** | §5.3: vendor-provided value, descriptive, optional display; never self-derived into an expected-range verdict |
| D4 | Empty-state fix timing | **Claude version — immediate stop-bleed** | §10 Stage 2: availability state machine + honest proxy errors ship before any vNext implementation |
| D5 | Vendor/local timestamp separation + reprocess freshness repair timing | **Engineer version — standalone foundation stage** | §10 Stage 3: Time/Knowledge Integrity foundation lands **before** Phase 2A vNext implementation and before significant new candidate history accumulates |
| D6 | Daily pipeline vs Phase 2A vNext ordering | **Parallel — Claude version** | §10 Stage 4A ∥ 4B: run in parallel; the daily pipeline must not land **later** than Phase 2A vNext (every missed day is a permanent gap) |
| D7 | Research Readiness | **Claude version — SIMPLIFY** | §5.6: per-layer availability facts kept; `CONTEXT_COMPLETE/PARTIAL/LIMITED` composite removed; execution readiness no longer requires Greeks |
| D8 | Trend State / Adjacent Expiry Context | **OPTIONAL** | §5.2 / §5.4: both become optional secondary display. Underlying raw fields (close, SMA20/50; adjacent-expiry raw cells) remain persisted. *Interpretation note for founder review: D8 was answered as a single "optional" covering both items; if Trend State should instead stay core, strike this note and move it back in §5.2.* |

---

# PART 1 — Semantic Red Lines (unchanged, non-negotiable)

```text
missing ≠ zero
Call ≠ bullish            Put ≠ bearish
OI increase ≠ bought-to-open
Premium ≠ one order ≠ directional conviction
positive/negative GEX ≠ market direction
UNRESOLVED ≠ Neutral
PERSISTENT_BUILD / DECLINE ≠ trade direction
Radar ≠ complete option universe (vendor-ranked changed-contract subset)
no universal anomaly / ticker / conviction score
no BUY / SELL
no Actionability labels before empirical validation
no rewriting of accepted historical evidence
append-only + spec/config version + hash at every layer
UTC persistence · NY market-calendar semantics · no-lookahead
```

---

# PART 2 — Candidate = Product/Ticker Model

## 2.1 Entity separation

```text
ANOMALY ENTITY        exact contract or expiry        (analytical trigger)
PRODUCT CANDIDATE     ticker / product                (user-facing research object)
```

All qualifying anomalies are stored (full anomaly pool). Anomalies are grouped by ticker into Product Candidates. Nothing is discarded because a ticker already qualified.

## 2.2 First-class persistence (adopted from engineer review)

Product Candidate becomes a **persisted research entity**, not a frontend grouping:

```text
ProductCandidate
    ticker
    candidate_first_knowledge_at      (immutable)
    materialization rule version
    status / lifecycle fields

ProductCandidateTrigger
    → references contract anomalies (Radar, Contract Persistence)
    → references expiry anomalies (Expiry Activity)
    each with its own anomaly identity, evidence time layer, and source ids
```

One Product Candidate references many triggers. Existing exact-contract Phase 2B evaluations are never deleted; the new entity layer is additive.

## 2.3 MAG7 allocation rules (vNext, restated)

No Top-N ticker ranking, no Ticker Score, no forcing of 12 slots. If four tickers qualify, the dashboard shows four candidates. The 4 tickers × 3 expiries mechanism, if retained at all, is an internal budget mechanism — never the candidate definition. Truncation, when applied for budget, must be logged (no silent drops).

---

# PART 3 — Phase 2A vNext (frozen founder decisions, restated — NOT reopened)

## 3.1 Active discovery/confirmation families

```text
RADAR_EVENT            exact contract   Core Discovery
EXPIRY_ACTIVITY        expiry           Core Discovery
  └── 0DTE             special calibration method inside Expiry Activity
CONTRACT_PERSISTENCE   exact contract   Core Confirmation + Slow-Burn Discovery
```

Removed / sunset from active discovery: `EXPIRY_PERSISTENCE`, `STRUCTURAL_COLD_START`, Evidence Breadth count. Historical data retained read-only.

## 3.2 Structure / Cluster

Deep-Dive context computed after candidate existence (production already computes them post-selection). Neighbor-Strike is a Structure component, not separate vocabulary. Positive display requires VALID/STRONG state; `INVALID_CLUSTER` and sub-threshold Structure never render as positive evidence.

## 3.3 Contract Persistence freshness (vNext STEP 3, restated)

Current-candidate triggering must satisfy an **explicit, configurable, versioned, no-lookahead** recency rule. Do **not** pick 5/7/10/20 days now; the initial default is conservative, explicitly marked `CALIBRATION_REQUIRED`, and revisited only with accumulated real data.

## 3.4 Route priority

Internal engineering mechanism only (budget, chain loading, deterministic ordering). Never presented as analytical evidence.

---

# PART 4 — First Knowledge / Time & Knowledge Integrity Model

## 4.1 Seven time identities (required on every context-bearing record)

```text
event_date                    market/vendor evidence date of the anomaly
source_first_received_at      immutable first receipt of the source-evidence identity
candidate_first_knowledge_at  immutable; first moment admissible evidence materialized
                              the Product Candidate under then-current rules
context_evaluated_at          when a Phase 2B context snapshot was computed
price_as_of                   as-of of the price observation used
vendor_observed_at            vendor's analytical observation timestamp (NULL if absent)
local_captured_at             local transport capture time
```

## 4.2 Integrity rules

- `candidate_first_knowledge_at` and `source_first_received_at` are immutable. Re-evaluation creates a new `context_evaluated_at`; it never rewrites first knowledge.
- Vendor time never silently falls back to local time under one unlabeled field. Two fields, always.
- Backfill/reprocess never overwrites capture identity and never makes stale vendor evidence look fresh (cache freshness keys on vendor as-of / source identity, not on DB row `created_at`).
- Phase 2B evaluations carry an explicit identity: `FIRST_KNOWLEDGE_BASELINE` vs later `REFRESH` — distinct rows, both preserved.
- Unreconstructible history stays `NULL / UNRESOLVED`. No guessed historical timestamps, ever.

## 4.3 Frozen First-Knowledge Research Snapshot (adopted from engineer review)

At candidate materialization, the Phase 2B baseline context is **frozen** as the research snapshot for future Forward Outcome work. Inputs proven non-backfillable (contract IV, spreads, IV Rank if validated) are captured prospectively at this moment, reusing already-loaded chain data — no per-contract API calls. Later refreshes never replace the baseline.

---

# PART 5 — Phase 2B vNext — Balanced Product-Candidate Context Model

## 5.0 One-sentence purpose

> Phase 2B provides a time-correct, non-directional, minimum-sufficient market-context snapshot for each Product/Ticker Candidate — shared at ticker level, detailed per anomaly — sufficient to understand the environment in which its anomalies occurred and to support later Forward Outcome research, without deciding whether or how to trade.

## 5.1 Structure: one evaluation layer, two entity levels

The v1.2-context → v2.0-state → v3.1-workspace stack is replaced by a **single additive evaluation layer**:

```text
ProductCandidateContext        (ticker level, one per candidate evaluation)
    └── AnomalyContextDetail   (one per referenced anomaly; contract or expiry)
```

Entry point is the Product Candidate with its full trigger list — this fixes the current radar-only gate (`confirmation/service.py:116-137`): persistence-only contracts and expiry anomalies are first-class. Old v1.2/v2.0/v3.1 tables are preserved read-only.

## 5.2 Block B1 — Underlying Price Context  [ticker level, shared]

```text
CORE      latest canonical regular close · 1D/5D/20D returns ·
          SMA20 / SMA50 · ATR14
DERIVED   distance-to-SMA (display-computed from stored fields)
OPTIONAL  20-session high/low · Trend State (D8: factual shorthand,
          secondary display; UPTREND/DOWNTREND/MIXED/UNKNOWN semantics unchanged)
```

Canonical regular-session policy, gap/ambiguity flags, and coverage quality carry over from the current implementation unchanged. No `Price Bullish/Bearish`, ever.

## 5.3 Block B2 — Volatility Context  [ticker level shared; expiry anchoring derived]

```text
CORE      candidate-expiry IV (per anomaly expiry, derived from one shared
          term-structure payload) · contract IV (anomaly level, from chain reuse)
VALIDATE-FIRST (D2)
          IV Rank — read-only proof of vendor entity/semantics/timestamps
          required (Stage 1) before it is core; raw value only, no LOW/MID/HIGH
OPTIONAL (D3)
          Implied Move — vendor value, descriptive only
EXPANDED (D1)
          nearest shorter / longer expiry IV nodes · local term topology
          (LOCAL_PEAK / LOCAL_TROUGH / RISING / FALLING / FLAT_OR_EQUAL /
          INCOMPLETE) — retained, computed from the same payload at zero cost,
          shown only in expanded view; not mandatory core content
```

API shape: `iv_rank` + `term_structure` remain one call each per qualifying ticker.

## 5.4 Block B3 — Dealer/GEX Structural Context  [ticker surface; anomaly-expiry anchored; ARCHIVE-ONLY]

```text
SOURCE    existing daily Dealer/GEX archive exclusively.
          The Phase 2B dealer_heatmap endpoint call (format=full,
          confirmation/service.py:70) is REMOVED after Stage 1 proof —
          it is the request shape documented to return HTTP 400.
          Zero incremental paid calls.

CORE      spot · anchor expiry (per anomaly expiry) ·
          Primary Floor / Primary Upper Positive-GEX Node /
          Immediate Below-Floor Node — raw strike + net GEX values + sign

OPTIONAL (D8)
          Adjacent Expiry Context — same-strike cross-expiry comparison,
          secondary display; float tolerance comparison replaces exact
          equality; single-available-negative vs both-negative distinguished

REMOVED AS LABELS
          STABILIZATION_BIAS · DOWNSIDE_ACCELERATION_RISK
          (tautological / no magnitude; zero information loss — the raw
          node values remain). Any future BIAS/RISK wording is
          VALIDATE-FIRST behind Forward Outcome evidence.

ARCHIVE   full surface kept in the archive (GEX Evolution prerequisite);
          per-candidate display limited to anchor ± adjacent; optional
          drill-down only. No-lookahead anchored query semantics
          (vendor_observed_at AND captured_at <= as_of) unchanged.
```

## 5.5 Block B4 — Anomaly-Specific Option Snapshot  [anomaly level]

```text
CONTRACT anomaly
    identity (contract / expiration / right / strike / DTE with anchor-date
    stated) · strike location vs spot (USD, %, ATR-normalized) ·
    contract IV · Delta (moneyness descriptor) ·
    bid / ask / spread% — descriptive, labeled with quote as-of
    Deep-Dive references: Structure / Cluster — VALID/STRONG only

EXPIRY anomaly
    expiry activity evidence recap · expiry-anchored B2/B3 views ·
    no fabricated contract-level data

EXCLUDED from Phase 2B display
    Gamma / Theta / Vega (Trade Expression inputs; still archived) ·
    execution-quality scoring labels (raw spread suffices; any
    executability gate is future Actionability, VALIDATE-FIRST)
```

Chain-context sharing rule (engineer review, adopted): all anomalies in the same ticker-expiry share one chain-context load; nothing is fetched per contract.

## 5.6 Block B5 — Provenance / Time / Data Quality  [candidate + anomaly level]

- The seven time identities of §4.1, rendered per §7.4.
- Per-layer availability facts (price / volatility / dealer / execution / positioning provenance): `AVAILABLE / PARTIAL / UNAVAILABLE / NOT_YET_AVAILABLE` — missing is never a penalty, never a score.
- **D7:** the `CONTEXT_COMPLETE/PARTIAL/LIMITED` composite is removed; execution availability no longer requires Greeks.
- Provenance carries raw payload ids, request ids, spec+config version+hash, dealer snapshot source + time-eligibility — same discipline as v3.1, single layer.

## 5.7 API cost model

```text
Per qualifying Product Candidate ticker:
    daily_ohlc          1
    stock_state         1
    iv_rank             1   (status per D2 pending Stage 1 proof)
    term_structure      1
    dealer_heatmap      0   (archive-only; dead call removed)
    ─────────────────────
    total               4   (v3.1: 5, one of them dead)

Per anomaly: 0 additional paid calls (chain reuse per ticker-expiry).
At 50–100 tickers: Phase 2B cost ∝ qualifying candidates/day, not universe
size. Universe-proportional costs (daily pipeline, dealer archive) belong to
the Universe Expansion Design Gate, not to Phase 2B.
```

---

# PART 6 — Daily Data / Operational Architecture

No single universal schedule; each source follows its own publication semantics, with freshness visible in the dashboard health strip.

```text
1. Same-day / EOD expiry activity   → one canonical session-complete snapshot;
   intraday observations allowed as PROVISIONAL_INTRADAY but excluded from the
   canonical 20-observation 0DTE baseline (fixes first-writer contamination)

2. Radar / OI confirmation          → collected per vendor publication /
   rollover timing, informed by the existing 0817 rollover-timing experiment
   evidence; NOT copied blindly from the 15:30 GEX schedule

3. Contract OI archive              → complete-chain gate · missing ≠ 0 ·
   no fabricated closure · vendor date separate from capture time ·
   contract-level open_interest_as_of retained (stop discarding it) ·
   DailyCollectionCoverage.observation_date split into activity-date vs
   vendor-OI-date fields (one meaning per field)

4. Dealer/GEX archive               → unchanged; scheduler untouched

5. Non-backfillable Phase 2B inputs → frozen prospectively at candidate
   first-knowledge time (§4.3); chain reuse only, no added calls

Automation: archive-mag7-daily gets a durable GitHub Actions workflow
(same operational pattern as dealer-gex-archive; timing per source, per #2).
```

---

# PART 7 — Candidate-First Dashboard (information architecture, not styling)

## 7.1 First screen

```text
① SYSTEM / DATA HEALTH
   DB · last scan (@time, consumed units) · Phase 2A daily collection last
   success · GEX archive last vendor observation · quota (+ observation age)

② TODAY'S PRODUCT CANDIDATES
   One card per ticker:  first-known time · Why-Found badges with evidence
   time layer:  SAME-DAY (Expiry Activity) · OI-CONFIRMED (Radar, vendor
   dates shown) · MULTI-OBSERVATION (Persistence, window first/last dates)
   MAG7: all qualifying candidates, no ranking, no filler
```

## 7.2 Candidate page

```text
Candidate header (ticker · first knowledge · context evaluated · price as-of
· freshness)
→ Why Found (anomaly list grouped by time layer; no breadth counts)
→ Shared Ticker Context (B1 price · B2 volatility · B3 GEX — shown once,
  regardless of anomaly count)
→ Anomaly Details (B4; contract anomalies expandable; expiry anomalies have
  their own view — no dead ends)
→ Deep Dive (Structure/Cluster, VALID-gated)
→ Supporting / audit data (raw tables, provenance, request ids, raw GEX,
  JSON) — always below the decision layer
Hierarchy: Conclusion → Explanation → Evidence → Raw audit data.
```

## 7.3 Availability state machine (superset of both reviews)

```text
Run-level:      DB_OFFLINE · NOT_RUN · RUNNING · FAILED ·
                SUCCESS_NO_CANDIDATE · SUCCESS_WITH_CANDIDATES
Feature-level:  HISTORY_IMMATURE (x/y shown) · FEATURE_UNAVAILABLE
                (explained, e.g. 0DTE baseline insufficient) · STALE_DATA

Only SUCCESS_NO_CANDIDATE may say "no qualifying candidate today."
The proxy never converts backend failure into HTTP 200 + empty payload.
```

## 7.4 Time display rules

Fixed America/New_York display + UTC tooltip; every timestamp labeled with its identity type (event / vendor observed / first received / first knowledge / evaluated / captured). "Event happened at T, system knew at T+1" must be visible.

## 7.5 Operational transparency

Run-Scan button states cost (~14 paid calls) and exactly which tables it does and does not refresh (Radar comes from daily collection). Phase 2B context refresh gets an in-UI entry point with cost disclosure (4 calls/ticker) — no CLI dead ends.

---

# PART 8 — Forward Outcome Boundary: Research Loop vs Live Loop

The stage sequence `Phase 2B → Forward Outcome → Actionability → Trade Expression` is **build/dependency order, not runtime data flow**. Live trading never consumes future data. The operating model is two loops over one data foundation:

```text
RESEARCH LOOP (offline, retrospective)
    historical Product Candidates + frozen first-knowledge snapshots
        ↓ T+1 / T+3 / T+5 elapse naturally
    Forward Outcome measurement (direction-neutral first:
    T+N close returns, max upside/downside excursion)
        ↓
    Actionability calibration: which evidence configurations retained
    usable edge AFTER the system actually knew?
        ↓
    versioned, validated Actionability rules
                    │ rules deploy down; samples flow back up
                    ▼
LIVE LOOP (daily, as-of information only)
    Universe → Phase 2A → Product Candidate (first knowledge frozen)
    → Phase 2B frozen snapshot (all inputs as-of ≤ now)
    → apply CALIBRATED rules → NOT_ACTIONABLE / WATCH / ACTIONABLE
    → Trade Expression (entry / invalidation / risk)
    → today's candidate becomes a research sample at T+N
    → rolling walk-forward validation; recalibrate on drift (versioned)
```

Boundary rules:

- Phase 2B never absorbs Actionability or Trade Expression. Until calibration completes, the live system is a **daily research shortlist with a human decision-maker** — decision support, not signals.
- Train/serve information parity is the entire reason for §4: features used in calibration must be computable, with identical information content, at live decision time. Detection-anchor drift or lookahead in the training data produces inflated backtest edge and live failure.
- Direction remains UNRESOLVED: first-round Actionability research answers "does structure resolve / does it move", not "which way". Directional theses (and MFE/MAE semantics) are a separate later calibration and may never validate. Early actionable expressions may be non-directional. Nothing in this spec pre-decides that question.
- No second scheduler is created merely for Forward Outcome; the design gate (existing 2026-08-15 document) decides data capture.

---

# PART 9 — Consolidated Defect Remediation Plan

IDs: G* = Claude review matrix; E* = engineer-review-only items; N* = new code-verified findings. Classifications final per founder decisions D4/D5/D6.

| Stage | ID | Defect | Final classification |
|---|---|---|---|
| S2 stop-bleed | G1 | Empty-state conflation; proxy returns 200 on backend failure (`route.ts:11`) | FIX_BEFORE_VNEXT (D4) |
| S2 stop-bleed | G2 | Radar backfill rewrites historical `captured_at`/`ny_market_date` (`daily.py:596-597`) | FIX_BEFORE_VNEXT; overwritten history unrepairable → UNRESOLVED |
| S3 time foundation | G3 | "At detection" rebinds to latest radar event (`service.py:117-124,329-333`) | Foundation (D5); hard gate before Forward Outcome; reconstructed anchors marked RECONSTRUCTED |
| S3 time foundation | G4 | Vendor/local mixed under one key (`service.py:206,310`; `workspace_v3.py:215`) | Foundation (D5); unknown vendor time stays NULL |
| S3 time foundation | G5 | Reprocess launders stale vendor data as fresh (`service.py:162-220`) | Foundation (D5); freshness keys on source identity/time |
| S3 time foundation | — | Baseline-vs-refresh evaluation identity | Foundation (§4.2) |
| S4A pipeline | G19 | archive-mag7-daily has no scheduler | FIX_WITH_DAILY_PIPELINE |
| S4A pipeline | G12 | 0DTE baseline contaminated by intraday first-writer (`v12.py:351-357`) | FIX_WITH_DAILY_PIPELINE; unmarked old snapshots flagged SUSPECT, excluded from calibration, not deleted |
| S4A pipeline | G25 | Chain `open_interest_as_of` discarded; contract OI inherits expiry-level date (`parsers.py:401`; `archive.py:264-291`) | FIX_WITH_DAILY_PIPELINE |
| S4A pipeline | E1 | `DailyCollectionCoverage.observation_date` has two meanings (`daily.py:369` vs `485`) | FIX_WITH_DAILY_PIPELINE |
| S4B 2A vNext | G8 | Persistence unbounded lookback trigger (`v13.py:284-299`) | FIX_WITH_PHASE2A_VNEXT (§3.3) |
| S4B 2A vNext | G9 | Persistence window can include future snapshots (`v11.py:414-428`) | FIX_WITH_PHASE2A_VNEXT; hard gate before Forward Outcome; contaminated evaluations excluded from clean sample, not rewritten |
| S4B 2A vNext | G10 | Window calendar-gap invisibility (`history.py:45`) | FIX_WITH_PHASE2A_VNEXT (expose span dates; no invented gap threshold) |
| S4B 2A vNext | G11 | 0DTE Score Basis wrong attribution (`v13.py:126-137`) | FIX_WITH_PHASE2A_VNEXT |
| S4B 2A vNext | G13 | Neighbor Ratio display ≠ scoring comparator; glossary wrong | FIX_WITH_PHASE2A_VNEXT; missing historical comparators stay NULL |
| S4B 2A vNext | G14/G15 | INVALID_CLUSTER as positive structure; presence inflation | Display VALID-gating FIX_WITH_PHASE2A_VNEXT; breadth inflation OBSOLETED (breadth removed) |
| S4B 2A vNext | G26 | Cluster zero-fill vs NULL discipline; quote-as-of labeling | FIX_WITH_PHASE2A_VNEXT (align to NULL discipline; label quote time; anchors untouched) |
| S4B 2A vNext | G21 | Legacy v1.2 discovery score leaks through API; silent fallback | Isolate/mark legacy now; block removed at candidate-first API rebuild |
| S4B 2A vNext | G7 | Local-clock market_date, no trading-day check; dual DTE identity | FIX_WITH_PHASE2A_VNEXT; every DTE/date states its anchor; complete before Forward Outcome |
| S6 2B vNext | N1/G22 | Dead `format=full` heatmap call (`service.py:70`) | NEEDS_READ_ONLY_PROOF (Stage 1) → remove; archive-only |
| S6 2B vNext | N2/G23 | Phase 2B entry gate radar-only (`service.py:116-137`) | FIX_WITH_PHASE2B_REDESIGN (entry = candidate + trigger list) |
| S6 2B vNext | G16 | Evaluation ingests top-5 clusters unfiltered (`service.py:351-356`) | FIX_WITH_PHASE2B_REDESIGN (VALID only) |
| S6 2B vNext | G17 | GEX tautological labels (`workspace_v3.py:276-314`) | FIX_WITH_PHASE2B_REDESIGN (de-label per §5.4) |
| S6 2B vNext | G18 | Adjacent-expiry float equality; `nearest()` missing-strike distance 0 | FIX_WITH_PHASE2B_REDESIGN |
| S6 2B vNext | G24 | EXPIRY_ONLY dead end; CLI-only context refresh | FIX_WITH_PHASE2B_REDESIGN |
| S6 2B vNext | N5 | Readiness requires Greeks; composite readiness | Resolved by D7 (§5.6) |
| S7 dashboard | G6 | Browser-local time rendering unlabeled | FIX_WITH_DASHBOARD (§7.4) |
| S7 dashboard | G20 | No last-scan/consumption/quota-age; Run-Scan behavior opaque | FIX_WITH_DASHBOARD (§7.5) |
| S7 dashboard | G27 | Glossary stale/misleading group; check script presence-only | FIX_WITH_DASHBOARD (glossary rebuilt against target architecture; semantic spot-checks) |
| S7 dashboard | G29 | 0DTE status panel missing; percentile-fallback consequence undisclosed | FIX_WITH_DASHBOARD; 40-gate itself VALIDATE-FIRST |
| S7 dashboard | G30 | Engine-first layout; time layers invisible | FIX_WITH_DASHBOARD (§7.1–7.2) |
| S7 dashboard | E2 | Radar table hidden scope (latest-date-per-ticker, top-15, NULL-premium sort) | Label table scope with candidate UI; DEFER beyond labeling |
| Deferred | G28 | Env-var mismatch; unauthenticated scan POST | DEFER — mandatory pre-public-deployment checklist |
| Deferred | E3 | Deep-dive budget cap | DEFER — ops mechanism, never candidate definition (§2.3) |
| Deferred | — | Overnight-quote-driven Structure liquidity recalibration | VALIDATE-FIRST (label the quote time now, per G26; no re-anchoring) |
| Obsoleted | — | Expiry Persistence / Structural Cold Start active-route defects | OBSOLETED_BY_NEW_ARCHITECTURE; data retained |

---

# PART 10 — Implementation Stage Plan (no implementation authorized by this draft)

```text
Stage 0   FREEZE — founder approves this spec; it becomes the baseline.
          Spec version numbers still deferred to the migration plan review.

Stage 1   READ-ONLY REPOSITORY PROOF GATE  (0 writes · 0 paid calls · 0 code)
          · N1: DB endpoint_statuses proof of the dead heatmap call
          · D2: IV Rank vendor entity / semantics / timestamp provenance
          · G3: first-detection anchor reconstructability sampling
          · G12: can existing 0DTE snapshots distinguish intraday vs EOD?
          · Phase 2B schema keys, evaluation identity, chain reuse path,
            cache/reprocess behavior, paid-call behavior of manual refresh
          · audit defects still reproduce at current HEAD
          · Phase 2A review legacy queries T1–T6 where still relevant

Stage 2   STOP-BLEED  (D4)
          · G1 availability state machine + honest proxy errors
          · G2 stop backfill in-place mutation (additive versioned rows)

Stage 3   TIME / KNOWLEDGE INTEGRITY FOUNDATION  (D5)
          · immutable source_first_received_at + candidate_first_knowledge_at
          · vendor/local separation (G4) · reprocess freshness fix (G5)
          · baseline-vs-refresh evaluation identity
          · additive migrations only; no guessed historical timestamps
          Must land BEFORE significant new candidate history accumulates.

Stage 4A ∥ 4B   PARALLEL  (D6 — 4A must not land later than 4B)
          4A DAILY PIPELINE (PART 6; G19, G12, G25, E1)
          4B PHASE 2A vNext (PART 3; G7–G11, G13–G15, G21, G26)

Stage 5   PRODUCT CANDIDATE PERSISTENCE LAYER (§2.2)
          ProductCandidate + ProductCandidateTrigger; first-knowledge anchor.

Stage 6   PHASE 2B vNext — BALANCED MODEL (PART 5; N1, N2, G16–G18, G24)
          Single evaluation layer; old three layers read-only preserved.

Stage 7   CANDIDATE-FIRST DASHBOARD (PART 7; G6, G20, G27, G29, G30, E2)

Stage 8   MAG7 OBSERVATION PERIOD — no universe expansion
          Observe: candidates/day · anomalies/candidate · route frequencies ·
          persistence maturation · context completeness · ticker concentration
          · chain reuse rate · Phase 2B API cost · freshness failure rate.

Stage 9   CANDIDATE FORWARD OUTCOME DESIGN GATE
          Only after candidate + time semantics are stable. Sample key =
          ProductCandidate + candidate_first_knowledge_at + frozen baseline
          context. Direction-neutral metrics first (T+1/3/5 close returns,
          max upside/downside excursion). Reuses the 2026-08-15 design-gate
          document. Precondition: G3 and G9 closed.
```

Execution discipline: every stage ships as scoped packages (authorized-file lists, verification reports, additive migrations, no rewriting accepted history), consistent with the project's governed package workflow.

---

# PART 11 — Do Not Change Yet (merged)

1. Radar material gate ($150k / 2,500) — versioned, unvalidated design hypothesis; unchanged.
2. All scoring anchors and gates (persistence 3/5/10 anchors, activity 60/40 + 40-gate, structure/cluster anchors + 65-gate, 0DTE 70/30, fallback cap) — unchanged until outcome evidence.
3. No invented persistence freshness window — explicit configurable semantics first, calibrate later (§3.3).
4. 0DTE same-ticker 20-observation self-baseline model — design stays; only contamination + presentation fixed.
5. Dealer/GEX archive, scheduler, and no-lookahead query semantics — untouched.
6. No Ticker Score · no Phase 2B composite score · no Conviction Score · no direction inference · no BUY/SELL · no Actionability labels.
7. No second scheduler merely for Forward Outcome.
8. No universe expansion (Universe Expansion Design Gate is separate).
9. No deletion of historical Expiry Persistence / Structural Cold Start / accepted evaluations / old Phase 2B layers — read-only retention.
10. No rewriting accepted history; no guessed first-knowledge timestamps (NULL/UNRESOLVED when unreconstructible).
11. Budget & concurrency protections (75 units/scan, advisory locks) — unchanged.
12. REST + server-side key + same-origin proxy + single Supabase project — unchanged.
13. oi-change rollover-timing experiment — continues independently; its evidence feeds PART 6 #2.

---

# PART 12 — Founder Review Checklist for This Draft

Approving this document means approving:

- [ ] D1–D8 encodings (§0.2) — especially the D8 interpretation note (Trend State optional?)
- [ ] Five-block Phase 2B composition with CORE / OPTIONAL / EXPANDED split (PART 5)
- [ ] ProductCandidate + ProductCandidateTrigger as first-class persisted entities (§2.2)
- [ ] Frozen First-Knowledge Research Snapshot semantics (§4.3)
- [ ] Archive-only Dealer/GEX + removal of the dead heatmap call after Stage 1 proof (§5.4)
- [ ] Consolidated defect plan and stage assignments (PART 9)
- [ ] Stage plan order: 1 → 2 → 3 → (4A ∥ 4B) → 5 → 6 → 7 → 8 → 9 (PART 10)
- [ ] Research-Loop / Live-Loop boundary statement (PART 8)
- [ ] Do-Not-Change list (PART 11)

Nothing is implemented until this draft is approved and Stage 1 (read-only proof gate) has produced its evidence report.

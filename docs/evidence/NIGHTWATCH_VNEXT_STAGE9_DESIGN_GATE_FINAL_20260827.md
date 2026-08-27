# NIGHTWATCH vNext — Stage 9 Design Gate Final
## Offline Research / Forward Outcome

**Date:** 2026-08-27  
**Status:** FOUNDER-LOCKED DESIGN  
**Implementation authorization:** YES — proceed in sequence **Stage 9A → review → Stage 9B → review → Stage 9C**.

## Canonical repository
- Repo: `F:\options-anomaly-scanner`
- Branch at authorization: `main`
- Commit at authorization: `c364183fff98d74e1d79f78a38a4fb07f94493f9`
- Canonical evidence: `F:\options-anomaly-scanner\docs\evidence`

## 1. Stage 9 boundary
Stage 9 is **Offline Research / Forward Outcome**.

Trading Dashboard and Research must remain separated:
- Trading: current/as-of Price, IV, Dealer/GEX, active anomalies; refreshable.
- Research: immutable `ProductCandidate` occurrence, immutable `candidate_first_knowledge_at`, frozen `FIRST_KNOWLEDGE_BASELINE`, qualifying historical triggers, and later direction-neutral Forward Outcomes.
- Current Trading Context must never overwrite the frozen baseline.
- Live scanner/ranking/current candidate evaluation must never consume the current candidate's Forward Outcome.

## 2. Research unit and admission
One Research Sample = **one ProductCandidate occurrence**.

Identity:
- `ProductCandidate.id`
- `candidate_first_knowledge_at`
- frozen `FIRST_KNOWLEDGE_BASELINE`

Ticker alone is never the sample key. No arbitrary cross-run merge.

A candidate with 27 qualifying contracts is still one Research Sample; those contracts are features/triggers.

Base Research Population:
- all valid ProductCandidate occurrences produced by contemporaneous Phase 2A qualification;
- no second admission filter based on B1/B2/B3/B4, Trend, IV, GEX, Deep Dive, DTE, premium, trigger count, or later outcome.

## 3. Primary Research Population
Primary statistics use only ProductCandidates produced by the **canonical scheduled production vNext scan**.

Current production intent:
- ~06:30 ET: Daily OI / Radar archive — no canonical ProductCandidate materialization
- ~15:30 ET: Dealer GEX archive — no canonical ProductCandidate materialization
- ~16:30 ET: Activity archive + readiness + exactly one canonical scheduled vNext scan — ProductCandidate materialization

Preserve but exclude from primary aggregation:
- manual
- controlled live observation
- diagnostic
- remediation/test
- developer rerun
- other non-canonical run origins

Do not infer origin from timestamps alone.

## 4. Historical trigger retention
A qualifying trigger does not disappear from Research when its contract or expiry becomes inactive or expires.

Once included in a ProductCandidate's first-knowledge evidence, it remains immutable historical evidence.

The Research Sample exists when the candidate forms; it does not wait for contract expiry. Forward outcomes may initially be `NOT_YET_MATURE`.

Merely appearing on the Trading Dashboard is insufficient; the contract/expiry must have been a qualifying first-knowledge trigger.

## 5. Reference Price
Founder-locked:

`REFERENCE_PRICE_POLICY = PRIOR_COMPLETED_REGULAR_CLOSE`

This is a standardized research reference, never an Entry Price, Detection Price, or Executable Price.

Rules:
- premarket or intraday first-known: latest completed XNYS regular-session Close before the current session;
- after official close first-known: same-day completed Close only if known as-of first knowledge;
- non-trading day: most recent completed XNYS Close;
- early close: use actual XNYS official close, never hardcode 16:00 ET.

## 6. T+1 / T+3 / T+5 clock
Use XNYS trading sessions, not calendar days. Weekends/holidays do not count; early-close sessions do count.

If candidate first-known before the current session close:
- T+1 = current session Close
- T+3 = third valid XNYS session Close beginning with T+1
- T+5 = fifth valid XNYS session Close beginning with T+1

If first-known after close:
- Reference = same-day completed Close
- T+1 = next valid XNYS session Close

Canonical example:
- First known: Aug 20 2026 06:07 ET
- Reference: Aug 19 Close
- T+1: Aug 20
- T+3: Aug 24
- T+5: Aug 26

A date reaching Aug 26 does not make T+5 mature until Aug 26 regular-session Close exists.

## 7. Direction-neutral outcomes
Direction remains `UNRESOLVED`.

Do not use bullish/bearish outcomes or MFE/MAE labels.

For Reference Close `R` and future session closes `C1...CN`:
- `T+N Close Return = CN / R - 1`
- `Max Upside through T+N = max(C1...CN) / R - 1`
- `Max Downside through T+N = min(C1...CN) / R - 1`

Stage 9 v1 uses **Close-path extremes only**. Do not use Daily High/Low.

Required horizons:
- T+1/T+3/T+5 Close Return
- Max Upside through T+1/T+3/T+5
- Max Downside through T+1/T+3/T+5

## 8. Price basis / corporate actions
Reference and all T+N prices must use the **same corporate-action-consistent price basis**.

Stage 9A must inspect actual OHLC schema/provider semantics. If a consistent adjusted basis is provable, use it with provenance. If not, fail closed; do not mix raw/adjusted prices or fabricate returns.

## 9. Maturity
At minimum:
- `NOT_YET_MATURE`
- `MATURE_AVAILABLE`
- `MATURE_MISSING_DATA`
- `INVALID_SAMPLE`

Missing/pending is never zero.

## 10. Research Workspace IA
Same existing Nightwatch Dashboard project; Research is a separated workspace/page family, not a separate app.

Stage 9C planned pages:
1. Research Overview
2. Cohort Analysis
3. Historical Samples
4. Research Sample Detail

Research pages must visibly state: `RESEARCH — RETROSPECTIVE DATA`.

Sample Detail separates:
- **WHAT WE KNEW THEN**: identity, first knowledge, reference, frozen B1/B2/B3/B4, qualifying historical triggers, timing/provenance.
- **WHAT HAPPENED AFTER**: T+1/T+3/T+5 target sessions, maturity, close return, max upside/downside, outcome provenance/version.

## 11. Cohort methodology — v1 descriptive only
Stage 9 v1 is descriptive Research. It does not issue:
- Actionability verdicts
- Win/Success Rate
- Good/Bad Trade
- bullish/bearish accuracy
- iid p-values/significance claims
- automatic calibration conclusions

True multi-factor Actionability Calibration is later.

### Primary grouping
**Ticker**:
- AAPL, AMZN, GOOGL, META, MSFT, NVDA, TSLA
- plus All MAG7 summary

Ticker-specific views avoid hidden domination by a high-frequency ticker. All-MAG7 summary must show per-ticker sample composition.

### Secondary dimensions
**Route Composition**:
- HAS_RADAR
- HAS_EXPIRY_ACTIVITY
- HAS_CONTRACT_PERSISTENCE
- mutually exclusive groups:
  - RADAR_ONLY
  - EXPIRY_ONLY
  - PERSISTENCE_ONLY
  - RADAR + EXPIRY
  - RADAR + PERSISTENCE
  - EXPIRY + PERSISTENCE
  - RADAR + EXPIRY + PERSISTENCE

**DTE Bucket**:
Reuse the Scanner's existing canonical semantics:
- VERY SHORT
- SHORT
- MEDIUM

Do not invent Stage 9 thresholds.

**Trigger Count**:
Preserve raw qualifying trigger count. Do not hardcode buckets yet. Inspect historical scheduled-production trigger-count distribution first; later choose natural, versioned boundaries.

### Future dimensions
Keep the model extensible for later Trend, IV/term structure, Dealer/GEX, premium, OI change magnitude, structure/cluster, and other B1/B2/B3/B4 features. Do not expose them all in v1.

## 12. Repeated ticker occurrences / defensive dedup
Canonical scheduled candidates on consecutive dates are all preserved as descriptive samples. Stage 9 v1 does not assume iid independence.

Defensive only:
`OUTCOME_WINDOW_KEY = ticker + reference_session + T1_session + T3_session + T5_session`

If an abnormal duplicate canonical production occurrence maps to the same outcome window:
- preserve all occurrences;
- count one in primary aggregates;
- earliest `candidate_first_knowledge_at`, then ProductCandidate.id, is deterministic fallback.

This is a safety net, not normal methodology.

## 13. Scheduler / cost
Founder-locked:

`SECOND_FORWARD_OUTCOME_SCHEDULER = NO`

Priority:
1. reuse preserved historical OHLC;
2. due-only refresh when maturity is due and OHLC is missing;
3. one distinct ticker fetch shared by all due samples for that ticker;
4. if automation is later needed, attach to existing daily workflow.

Stage 9A must make zero paid Nightwatch calls.

## 14. Implementation sequence
### Stage 9A — Forward Outcome Foundation
Methodology foundation, schema/provenance, XNYS calendar mapping, reference policy, maturity, outcome formulas, production-origin classification, firewall, tests.

No Research UI. No historical outcome materialization/backfill. No new scheduler. No paid API calls.

### Stage 9B — Outcome Materialization & Maturity
Only after 9A acceptance:
- materialize historical matured samples
- reuse preserved OHLC
- due-only missing-OHLC refresh
- one ticker/one fetch/shared due samples
- append-only/versioned outcomes

### Stage 9C — Research Workspace
Only after 9B acceptance:
- Overview
- Cohort Analysis
- Historical Samples
- Sample Detail

No live Actionability feedback yet.

## 15. Implementation-time capability checks
These are not additional Founder product decisions, but Stage 9A must resolve them by repository inspection:
1. exact existing VERY SHORT / SHORT / MEDIUM thresholds/source;
2. actual OHLC corporate-action semantics;
3. exact run-origin metadata for canonical scheduled production vs manual/controlled/diagnostic;
4. exchange-aware XNYS calendar dependency/support.

If any cannot be established without guessing, fail closed and report the bounded gap.

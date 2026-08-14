# Phase 2B v3 — Directional Research Bias Calibration Gate

Date context: 2026-08-14  
Starting Git SHA: `eb2b2be87e56effb85537e1e6f1a55785dc043eb`  
Accepted specifications: `signal_spec_v1.3_phase2a`, `signal_spec_v1.2_phase2b`,
`signal_spec_v2.0_phase2b`

## Executive conclusion

Only one current evidence family has accepted directional semantics: `PRICE_ACTION`. Positioning
importance is deliberately non-directional; IV and Dealer/GEX directional mappings are not
established; Execution and Research Readiness answer different questions.

The smallest safe Phase 2B v3 is therefore a **Price Directional Bias**, not a broad multi-factor
Model Research Bias:

```text
UPTREND   -> BULLISH
DOWNTREND -> BEARISH
MIXED     -> NEUTRAL
UNKNOWN   -> INSUFFICIENT_EVIDENCE

bias_label              = PRICE_DIRECTIONAL_BIAS
bias_basis              = PRICE_ACTION_ONLY
directional_family_count = 1 when Price is usable, otherwise 0
```

Reserve the broader `MODEL_RESEARCH_BIAS` label until a second genuinely independent directional
family is empirically and semantically accepted. If that field must exist before then, its honest
value is `INSUFFICIENT_EVIDENCE`, while `PRICE_DIRECTIONAL_BIAS` remains visible and useful.

This recommendation is a semantic design only. No production v3 logic, schema, API, UI, glossary,
or trade-expression layer is implemented by this gate.

## Git / Safety

- Repository began clean at the accepted Phase 2B v2 commit.
- Only this evidence report is changed.
- No production source, database schema, Alembic migration, API, Dashboard, glossary, Phase 2A,
  Phase 2B v1.x, or Phase 2B v2 calculation changed.
- Diagnostics were read-only PostgreSQL queries executed inline; no temporary file remains.
- No Nightwatch request was made and no paid quota unit was consumed.
- No secret, database URL, API key, or Authorization header was printed or persisted.
- Final quality and Git results are recorded at delivery because this report is part of the
  documentation-only commit.

## Direction Semantics

Future v3 must keep two different facts:

| Concept | Meaning | Current/future states |
| --- | --- | --- |
| Observed Flow Direction | Economic intent of the actual option activity | remains `UNRESOLVED` |
| Price Directional Bias | Direction supported by the accepted underlying price structure | `BULLISH`, `BEARISH`, `NEUTRAL`, `INSUFFICIENT_EVIDENCE` |
| Reserved Model Research Bias | Future conclusion across multiple accepted independent directional families | currently `INSUFFICIENT_EVIDENCE` |

`UNRESOLVED` does not mean neutral. It means the initiating transaction may have been bought,
written, spread, hedged, or otherwise multi-leg and cannot be inferred from present data.

## Observed Flow Direction vs Model Research Bias

This representation is semantically valid:

```text
Contract: NVDA 220C
Observed Flow Direction: UNRESOLVED
Price Directional Bias: BULLISH
Bias Basis: PRICE_ACTION_ONLY
```

The first field describes an unobserved actor's economic intent. The second describes the scanner's
independent reading of accepted price structure. Neither field rewrites the other.

The superseded `LONG_CALL_THESIS`, `SHORT_CALL_THESIS`, `LONG_PUT_THESIS`, and
`SHORT_PUT_THESIS` design is rejected for v3. Directional research precedes trade expression.

## Directional Evidence State Definitions

| State | Stable meaning |
| --- | --- |
| `BULLISH_SUPPORT` | The accepted dimension rule supports upward underlying-price direction. |
| `BEARISH_SUPPORT` | The accepted dimension rule supports downward underlying-price direction. |
| `NEUTRAL` | Usable evidence does not favor either direction under the accepted rule. |
| `UNKNOWN` | The dimension may contain directional information, but semantics, calibration, or data quality are insufficient. |
| `NON_DIRECTIONAL` | The dimension intentionally answers another question and is not a direction input. |

`UNKNOWN` and `NON_DIRECTIONAL` must never be merged. `NEUTRAL` also must not be used as a synonym
for missing evidence.

## Auditability Design

The smallest future production audit object should contain selected normalized scalars plus
references to immutable evidence, not duplicate large raw payloads:

```yaml
dimension: PRICE
directional_state: BULLISH_SUPPORT
primary_reason_code: PRICE_UPTREND
secondary_reason_codes: []
rule_id: directional_price_trend
rule_version: v1
source_fields: [latest_regular_close_usd, sma_20, sma_50, trend]
raw_values:
  latest_regular_close_usd: 224.09
  sma_20: 208.3825
  sma_50: 206.2618
source_evidence_refs:
  phase2b_candidate_state_id: ...
  ticker_context_id: ...
source_timestamp: 2026-08-12
source_quality: AVAILABLE_WITH_GAPS
specification_version: signal_spec_v3.0_phase2b
```

Recommended persistent fields are `dimension`, state, primary reason, optional secondary reasons,
rule ID/version, source field names, the few scalar values used by the rule, immutable source IDs,
timestamp, quality, and specification version. Human-readable text should come from a versioned
reason-code registry so wording fixes do not mutate evidence.

Every state—including `UNKNOWN` and `NON_DIRECTIONAL`—requires a reason. Multiple causes remain
ordered as primary semantic cause and secondary data-quality cause.

## Reason-Code Recommendation

Use this compact initial vocabulary:

| Reason code | Role |
| --- | --- |
| `PRICE_UPTREND` | Bullish price structure. |
| `PRICE_DOWNTREND` | Bearish price structure. |
| `PRICE_MIXED` | Usable price structure does not favor one side. |
| `PRICE_DATA_UNAVAILABLE` | Price direction cannot be evaluated. |
| `PRICE_SUBSIGNAL_CONFLICT` | Secondary audit note when a return sign opposes Trend. |
| `POSITIONING_INTENT_UNOBSERVED` | Positioning is relevant but not directional. |
| `IV_DIRECTIONAL_MAPPING_NOT_ESTABLISHED` | IV Rank has no accepted price-direction mapping. |
| `TERM_IV_DIRECTIONAL_MAPPING_NOT_ESTABLISHED` | Term topology has no accepted price-direction mapping. |
| `TERM_TOPOLOGY_INCOMPLETE` | Secondary data-coverage note. |
| `IMPLIED_MOVE_IS_MAGNITUDE_ONLY` | Implied move has no sign. |
| `GEX_DIRECTIONAL_MAPPING_NOT_ESTABLISHED` | Exact GEX sign is not bullish/bearish evidence. |
| `DEALER_SOURCE_UNAVAILABLE` | Dealer evidence was not available. |
| `DEALER_SOURCE_DEGRADED` | Secondary source-quality limitation. |
| `EXECUTION_NOT_DIRECTIONAL` | Liquidity and Greeks describe execution/exposure. |
| `RESEARCH_READINESS_NOT_DIRECTIONAL` | Readiness describes coverage only. |
| `ONLY_ONE_ACCEPTED_DIRECTIONAL_FAMILY` | Broad model bias is withheld. |
| `INSUFFICIENT_DIRECTIONAL_EVIDENCE` | No accepted usable directional family. |
| `CONFLICTING_DIRECTIONAL_EVIDENCE` | Reserved for future conflict between independent families. |

This is intentionally small. Do not create reason codes for every raw field.

## Price Direction

The direct mapping is safe for production **as a current price-structure interpretation**, not as a
prediction and not as flow intent:

| Accepted Price Trend | Directional state | Bias label | Reason |
| --- | --- | --- | --- |
| `UPTREND` | `BULLISH_SUPPORT` | `BULLISH` | `PRICE_UPTREND` |
| `DOWNTREND` | `BEARISH_SUPPORT` | `BEARISH` | `PRICE_DOWNTREND` |
| `MIXED` | `NEUTRAL` | `NEUTRAL` | `PRICE_MIXED` |
| `UNKNOWN` | `UNKNOWN` | `INSUFFICIENT_EVIDENCE` | `PRICE_DATA_UNAVAILABLE` |

The audit must show latest valid regular close, SMA20, SMA50, trend, price quality, source date, and
the exact ordering rule. `MIXED` means the accepted SMA-ordering rule favors neither direction; it
does not claim a market will remain flat.

## Price Subsignal Correlation / Conflict

Returns and Trend originate from the same canonical regular-session price series. They are
subsignals inside one `PRICE_ACTION` family, never independent votes.

Current 46-candidate distributions are candidate-weighted because each ticker context is shared by
its contracts:

| Metric | Positive | Negative | Zero/unavailable |
| --- | ---: | ---: | ---: |
| 1-session return sign | 20 | 26 | 0 |
| 5-session return sign | 21 | 25 | 0 |
| 20-session return sign | 17 | 29 | 0 |

| Trend comparison | Agreement | Opposite sign | MIXED Trend |
| --- | ---: | ---: | ---: |
| Trend vs 1-session return | 21 | 15 | 10 |
| Trend vs 5-session return | 20 | 16 | 10 |
| Trend vs 20-session return | 36 | 0 | 10 |

- 25/46 candidates with directional Trend have at least one return horizon opposing Trend: AMZN 6,
  GOOGL 7, META 2, and TSLA 10.
- 11/46—NVDA candidates—have all three return signs aligned with Trend.
- 10/46—AAPL candidates—have `MIXED` Trend even though all three returns are negative.
- Thus 35/46 are either mixed at the accepted Trend level or contain at least one return conflict.

Recommendation: keep Price Trend authoritative in v3. Persist returns as audit context and attach
`PRICE_SUBSIGNAL_CONFLICT` when applicable. Do not change Trend, count votes, or invent weights.
Distance to SMA20/SMA50 is raw context because the same averages already define Trend.

## Positioning Role

Positioning direction is `NON_DIRECTIONAL`, reason `POSITIONING_INTENT_UNOBSERVED`.

Call/Put identity, Premium, ΔOI, relative OI change, Volume, Trades, Structure, Persistence, Cluster,
and `SINGLE_EVIDENCE`/`MULTI_EVIDENCE` establish relevance or structural support. None observes
whether the initiating economic position was long, short, spread, or hedge. Explicitly rejected:

```text
Call -> bullish
Put -> bearish
Call + positive ΔOI -> bullish
Put + positive ΔOI -> bearish
```

Positioning remains prominent in the user experience:

```text
Price Directional Bias: BULLISH
Positioning Relevance: MULTI_EVIDENCE
Observed Flow Direction: UNRESOLVED
```

This says the option activity deserves attention while price structure currently leans upward. It
does not say the option activity itself was bullish.

## Volatility Direction Feasibility

- IV Rank directional state: `UNKNOWN`, reason `IV_DIRECTIONAL_MAPPING_NOT_ESTABLISHED`.
- Term topology directional state: `UNKNOWN`, reason
  `TERM_IV_DIRECTIONAL_MAPPING_NOT_ESTABLISHED`.
- Implied move directional state: `NON_DIRECTIONAL`, reason
  `IMPLIED_MOVE_IS_MAGNITUDE_ONLY`.

High/low IV Rank and `LOCAL_PEAK`/`LOCAL_TROUGH`/rising/falling topology cannot safely become
bullish or bearish. An `UNKNOWN` audit should still expose IV Rank, term shape, node IVs, implied
move, quality, and dates rather than hide them.

## Dealer/GEX Direction Feasibility

Dealer/GEX direction is `UNKNOWN`. `POSITIVE_NET_GEX` and `NEGATIVE_NET_GEX` describe the sign of an
exact vendor number only. Current semantics do not establish price direction, support/resistance,
pinning, acceleration, or gamma-flip behavior.

- With an exact cell, primary reason is `GEX_DIRECTIONAL_MAPPING_NOT_ESTABLISHED`; degraded quality
  is secondary `DEALER_SOURCE_DEGRADED`.
- With no usable source, primary reason is `DEALER_SOURCE_UNAVAILABLE`; the audit also notes that a
  directional mapping would remain unestablished even if data were present.

A later dedicated GEX research phase could investigate `VOLATILITY_DAMPENING`,
`VOLATILITY_AMPLIFYING`, `PINNING_RISK`, and `STRUCTURE_UNCLEAR`. Those are path/volatility states,
not Bullish/Bearish direction, and require complete-source semantics and outcome calibration.

## Execution Role

Execution direction is `NON_DIRECTIONAL`, reason `EXECUTION_NOT_DIRECTIONAL`. Bid, ask, midpoint,
spread, liquidity state, OI, Delta, Gamma, Theta, Vega, and Charm describe contract exposure and
execution environment. Positive Call Delta or negative Put Delta is the exposure of a hypothetical
long contract, not evidence about the unobserved Radar-side position or future stock direction.

Keep existing Phase 2A execution viability visible and add no threshold in this gate.

## Research Readiness Role

Research Readiness direction is `NON_DIRECTIONAL`, reason
`RESEARCH_READINESS_NOT_DIRECTIONAL`. `CONTEXT_COMPLETE`, `CONTEXT_PARTIAL`, and
`CONTEXT_LIMITED` describe evidence availability, not market direction or confidence.

## Independent Directional Evidence Families

| Family | Current directional role | Independent accepted family? |
| --- | --- | --- |
| `PRICE_ACTION` | Directional through accepted Price Trend | Yes—one family |
| `POSITIONING` | `NON_DIRECTIONAL` | No |
| `VOLATILITY` | `UNKNOWN`; semantics unestablished | No |
| `DEALER_GEX` | `UNKNOWN`; semantics unestablished | No |
| `EXECUTION` | `NON_DIRECTIONAL` | No |
| `RESEARCH_READINESS` | `NON_DIRECTIONAL` | No |

Current accepted independent directional family count is exactly **one**, not four price fields and
not six context dimensions.

## Design A — Price-Based Bias

Design A maps accepted Price Trend directly to Bullish/Bearish/Neutral/Insufficient and records
`basis=PRICE_ACTION_ONLY`, `directional_family_count=1`.

Advantages: useful, deterministic, complete for 46/46 current candidates, and easily audited.
Risk: the label `MODEL_RESEARCH_BIAS` sounds multi-factor even though only price contributes.

Current Design A distribution: BULLISH 17, BEARISH 19, NEUTRAL 10,
INSUFFICIENT_EVIDENCE 0.

## Design B — Multi-Family Requirement

Design B requires at least two independent accepted directional families for a Bullish/Bearish
overall Model Research Bias. With only Price Action available, all 46 current candidates become
`MODEL_RESEARCH_BIAS=INSUFFICIENT_EVIDENCE`, reason
`ONLY_ONE_ACCEPTED_DIRECTIONAL_FAMILY`, while their Price Direction remains visible.

Advantages: strong semantic discipline and no suggestion of multi-factor evidence. Risk: the broad
top-level field adds no discrimination with current data.

## Recommended Bias Design

Recommend a constrained third design:

1. Implement `PRICE_DIRECTIONAL_BIAS` using Design A's direct mapping.
2. Display `basis=PRICE_ACTION_ONLY` and directional family count beside it.
3. Keep each other dimension's directional state and audit visible.
4. Reserve `MODEL_RESEARCH_BIAS` for a later version with at least two accepted independent
   directional families; if exposed now, return `INSUFFICIENT_EVIDENCE` under Design B.

This gives traders an intuitive directional conclusion without implying a multi-factor model. It
also creates a clean upgrade path: adding a future family will not silently change what an old
`PRICE_DIRECTIONAL_BIAS` meant.

Preferred user-facing label: **Price Directional Bias**. `Market Directional Context` is less
precise, and `Directional Research Bias` still sounds broader than the current evidence basis.

## Dataset Diagnostic

The universe matches the Dashboard's latest-per-ticker Radar query at vendor observation date
2026-08-12. Expiry-only rows are excluded.

| Coverage | Result |
| --- | ---: |
| Contract-level candidates | 46 |
| Unique contract tickers | 6: AAPL, AMZN, GOOGL, META, NVDA, TSLA |
| Usable Price Context | 46/46 |
| Price Trend | UPTREND 17; DOWNTREND 19; MIXED 10; UNKNOWN 0 |
| Positioning provenance | 46/46 Radar events; SINGLE 30; MULTI 16 |
| Raw IV Rank | 46/46; six unique ticker values |
| Exact term node | 24/46 |
| Complete three-node topology | 12/46 |
| Dealer exact cell | 11/46, all degraded NVDA |
| Dealer unavailable | 35/46 |
| Execution bid/ask/spread/Greeks | 46/46 |
| Reconstructable Research Readiness | COMPLETE 0; PARTIAL 24; LIMITED 22 |

All 46 have insufficient OI history; accepted contract and expiry persistence scores are absent.
Evidence timestamps are asynchronous and several contracts are expired, so this is a semantics
sample, not an outcome or predictive calibration sample.

## Feature Classification Table

| Feature | Classification | Production interpretation |
| --- | --- | --- |
| Price Trend | DIRECTIONAL — THRESHOLD_FREE | Sole accepted Price directional rule. |
| Return 1D | DIRECTIONAL — REQUIRES_CALIBRATION | Correlated Price subsignal; audit only in minimal v3. |
| Return 5D | DIRECTIONAL — REQUIRES_CALIBRATION | Correlated Price subsignal; audit only in minimal v3. |
| Return 20D | DIRECTIONAL — REQUIRES_CALIBRATION | Correlated Price subsignal; audit only in minimal v3. |
| Distance to SMA20 | RAW_CONTEXT_ONLY | Already embedded in Trend relationship; no double count. |
| Distance to SMA50 | RAW_CONTEXT_ONLY | Already embedded in Trend relationship; no double count. |
| Strike distance % | RAW_CONTEXT_ONLY | Contract location relative to spot. |
| Strike distance ATR | RAW_CONTEXT_ONLY | Contract location scaled by price volatility. |
| Call / Put | NON_DIRECTIONAL | Trade side/economic intent is unobserved. |
| Premium | NON_DIRECTIONAL | Positioning relevance, not price direction. |
| ΔOI / relative OI change | NON_DIRECTIONAL | Change exists; opening side and strategy unknown. |
| Structure | NON_DIRECTIONAL | OI concentration/relevance. |
| Persistence | NON_DIRECTIONAL | Multi-session OI positioning relevance. |
| Cluster | NON_DIRECTIONAL | Same-side strike structure. |
| IV Rank | DIRECTIONAL_SEMANTICS_NOT_ESTABLISHED | No accepted underlying-direction mapping. |
| Term topology | DIRECTIONAL_SEMANTICS_NOT_ESTABLISHED | Volatility shape is not price direction. |
| Implied move | NON_DIRECTIONAL | Magnitude only. |
| Exact GEX sign | DIRECTIONAL_SEMANTICS_NOT_ESTABLISHED | Exact numeric sign only. |
| GEX numeric magnitude | DIRECTIONAL_SEMANTICS_NOT_ESTABLISHED | No normalized predictive mapping. |
| Vendor GEX row rank | DIRECTIONAL_SEMANTICS_NOT_ESTABLISHED | Vendor ordinal context only. |
| Spread | NON_DIRECTIONAL | Execution viability. |
| Delta | NON_DIRECTIONAL | Contract exposure conditional on a position side. |
| Gamma | NON_DIRECTIONAL | Contract exposure curvature. |
| Theta | NON_DIRECTIONAL | Contract time exposure. |
| Vega | NON_DIRECTIONAL | Contract volatility exposure. |
| Research Readiness | NON_DIRECTIONAL | Data coverage only. |

## Candidate Directional Contribution Table

Signs are raw return signs. `Pos`, `Vol`, `GEX`, `Exec`, and `Ready` are dimension directional
states—not evidence availability. `A` is Design A Price-based bias; `B` is Design B broad model
bias. Audit reason shorthand is the row's `PRICE_*` reason plus the common dimension reasons below.

| Ticker | Contract | Trend | 1D | 5D | 20D | Price | Pos | Vol | GEX | Exec | Ready | A | B | Audit |
| --- | --- | --- | ---: | ---: | ---: | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| TSLA | `TSLA260812C00335000` | DOWNTREND | - | + | - | BEARISH_SUPPORT | NON_DIRECTIONAL | UNKNOWN | UNKNOWN | NON_DIRECTIONAL | NON_DIRECTIONAL | BEARISH | INSUFFICIENT_EVIDENCE | PRICE_DOWNTREND; CONFLICT |
| NVDA | `NVDA261016P00220000` | UPTREND | + | + | + | BULLISH_SUPPORT | NON_DIRECTIONAL | UNKNOWN | UNKNOWN | NON_DIRECTIONAL | NON_DIRECTIONAL | BULLISH | INSUFFICIENT_EVIDENCE | PRICE_UPTREND |
| TSLA | `TSLA260812P00335000` | DOWNTREND | - | + | - | BEARISH_SUPPORT | NON_DIRECTIONAL | UNKNOWN | UNKNOWN | NON_DIRECTIONAL | NON_DIRECTIONAL | BEARISH | INSUFFICIENT_EVIDENCE | PRICE_DOWNTREND; CONFLICT |
| TSLA | `TSLA260812C00332500` | DOWNTREND | - | + | - | BEARISH_SUPPORT | NON_DIRECTIONAL | UNKNOWN | UNKNOWN | NON_DIRECTIONAL | NON_DIRECTIONAL | BEARISH | INSUFFICIENT_EVIDENCE | PRICE_DOWNTREND; CONFLICT |
| NVDA | `NVDA260904C00215000` | UPTREND | + | + | + | BULLISH_SUPPORT | NON_DIRECTIONAL | UNKNOWN | UNKNOWN | NON_DIRECTIONAL | NON_DIRECTIONAL | BULLISH | INSUFFICIENT_EVIDENCE | PRICE_UPTREND |
| TSLA | `TSLA260814C00335000` | DOWNTREND | - | + | - | BEARISH_SUPPORT | NON_DIRECTIONAL | UNKNOWN | UNKNOWN | NON_DIRECTIONAL | NON_DIRECTIONAL | BEARISH | INSUFFICIENT_EVIDENCE | PRICE_DOWNTREND; CONFLICT |
| TSLA | `TSLA260812C00340000` | DOWNTREND | - | + | - | BEARISH_SUPPORT | NON_DIRECTIONAL | UNKNOWN | UNKNOWN | NON_DIRECTIONAL | NON_DIRECTIONAL | BEARISH | INSUFFICIENT_EVIDENCE | PRICE_DOWNTREND; CONFLICT |
| NVDA | `NVDA260821C00220000` | UPTREND | + | + | + | BULLISH_SUPPORT | NON_DIRECTIONAL | UNKNOWN | UNKNOWN | NON_DIRECTIONAL | NON_DIRECTIONAL | BULLISH | INSUFFICIENT_EVIDENCE | PRICE_UPTREND |
| TSLA | `TSLA260812C00337500` | DOWNTREND | - | + | - | BEARISH_SUPPORT | NON_DIRECTIONAL | UNKNOWN | UNKNOWN | NON_DIRECTIONAL | NON_DIRECTIONAL | BEARISH | INSUFFICIENT_EVIDENCE | PRICE_DOWNTREND; CONFLICT |
| NVDA | `NVDA260814P00220000` | UPTREND | + | + | + | BULLISH_SUPPORT | NON_DIRECTIONAL | UNKNOWN | UNKNOWN | NON_DIRECTIONAL | NON_DIRECTIONAL | BULLISH | INSUFFICIENT_EVIDENCE | PRICE_UPTREND |
| NVDA | `NVDA260814P00225000` | UPTREND | + | + | + | BULLISH_SUPPORT | NON_DIRECTIONAL | UNKNOWN | UNKNOWN | NON_DIRECTIONAL | NON_DIRECTIONAL | BULLISH | INSUFFICIENT_EVIDENCE | PRICE_UPTREND |
| META | `META260812P00607500` | DOWNTREND | + | - | - | BEARISH_SUPPORT | NON_DIRECTIONAL | UNKNOWN | UNKNOWN | NON_DIRECTIONAL | NON_DIRECTIONAL | BEARISH | INSUFFICIENT_EVIDENCE | PRICE_DOWNTREND; CONFLICT |
| AAPL | `AAPL260812C00305000` | MIXED | - | - | - | NEUTRAL | NON_DIRECTIONAL | UNKNOWN | UNKNOWN | NON_DIRECTIONAL | NON_DIRECTIONAL | NEUTRAL | INSUFFICIENT_EVIDENCE | PRICE_MIXED |
| META | `META260812C00612500` | DOWNTREND | + | - | - | BEARISH_SUPPORT | NON_DIRECTIONAL | UNKNOWN | UNKNOWN | NON_DIRECTIONAL | NON_DIRECTIONAL | BEARISH | INSUFFICIENT_EVIDENCE | PRICE_DOWNTREND; CONFLICT |
| AAPL | `AAPL260812C00307500` | MIXED | - | - | - | NEUTRAL | NON_DIRECTIONAL | UNKNOWN | UNKNOWN | NON_DIRECTIONAL | NON_DIRECTIONAL | NEUTRAL | INSUFFICIENT_EVIDENCE | PRICE_MIXED |
| AAPL | `AAPL260812P00305000` | MIXED | - | - | - | NEUTRAL | NON_DIRECTIONAL | UNKNOWN | UNKNOWN | NON_DIRECTIONAL | NON_DIRECTIONAL | NEUTRAL | INSUFFICIENT_EVIDENCE | PRICE_MIXED |
| NVDA | `NVDA260821C00217500` | UPTREND | + | + | + | BULLISH_SUPPORT | NON_DIRECTIONAL | UNKNOWN | UNKNOWN | NON_DIRECTIONAL | NON_DIRECTIONAL | BULLISH | INSUFFICIENT_EVIDENCE | PRICE_UPTREND |
| NVDA | `NVDA260814C00225000` | UPTREND | + | + | + | BULLISH_SUPPORT | NON_DIRECTIONAL | UNKNOWN | UNKNOWN | NON_DIRECTIONAL | NON_DIRECTIONAL | BULLISH | INSUFFICIENT_EVIDENCE | PRICE_UPTREND |
| TSLA | `TSLA260814P00330000` | DOWNTREND | - | + | - | BEARISH_SUPPORT | NON_DIRECTIONAL | UNKNOWN | UNKNOWN | NON_DIRECTIONAL | NON_DIRECTIONAL | BEARISH | INSUFFICIENT_EVIDENCE | PRICE_DOWNTREND; CONFLICT |
| NVDA | `NVDA260814P00215000` | UPTREND | + | + | + | BULLISH_SUPPORT | NON_DIRECTIONAL | UNKNOWN | UNKNOWN | NON_DIRECTIONAL | NON_DIRECTIONAL | BULLISH | INSUFFICIENT_EVIDENCE | PRICE_UPTREND |
| TSLA | `TSLA260814P00327500` | DOWNTREND | - | + | - | BEARISH_SUPPORT | NON_DIRECTIONAL | UNKNOWN | UNKNOWN | NON_DIRECTIONAL | NON_DIRECTIONAL | BEARISH | INSUFFICIENT_EVIDENCE | PRICE_DOWNTREND; CONFLICT |
| NVDA | `NVDA261016P00180000` | UPTREND | + | + | + | BULLISH_SUPPORT | NON_DIRECTIONAL | UNKNOWN | UNKNOWN | NON_DIRECTIONAL | NON_DIRECTIONAL | BULLISH | INSUFFICIENT_EVIDENCE | PRICE_UPTREND |
| NVDA | `NVDA260814C00217500` | UPTREND | + | + | + | BULLISH_SUPPORT | NON_DIRECTIONAL | UNKNOWN | UNKNOWN | NON_DIRECTIONAL | NON_DIRECTIONAL | BULLISH | INSUFFICIENT_EVIDENCE | PRICE_UPTREND |
| AAPL | `AAPL260814C00307500` | MIXED | - | - | - | NEUTRAL | NON_DIRECTIONAL | UNKNOWN | UNKNOWN | NON_DIRECTIONAL | NON_DIRECTIONAL | NEUTRAL | INSUFFICIENT_EVIDENCE | PRICE_MIXED |
| NVDA | `NVDA260814C00222500` | UPTREND | + | + | + | BULLISH_SUPPORT | NON_DIRECTIONAL | UNKNOWN | UNKNOWN | NON_DIRECTIONAL | NON_DIRECTIONAL | BULLISH | INSUFFICIENT_EVIDENCE | PRICE_UPTREND |
| AMZN | `AMZN260814P00272500` | UPTREND | - | - | + | BULLISH_SUPPORT | NON_DIRECTIONAL | UNKNOWN | UNKNOWN | NON_DIRECTIONAL | NON_DIRECTIONAL | BULLISH | INSUFFICIENT_EVIDENCE | PRICE_UPTREND; CONFLICT |
| AAPL | `AAPL260812P00307500` | MIXED | - | - | - | NEUTRAL | NON_DIRECTIONAL | UNKNOWN | UNKNOWN | NON_DIRECTIONAL | NON_DIRECTIONAL | NEUTRAL | INSUFFICIENT_EVIDENCE | PRICE_MIXED |
| GOOGL | `GOOGL260812P00347500` | DOWNTREND | + | - | - | BEARISH_SUPPORT | NON_DIRECTIONAL | UNKNOWN | UNKNOWN | NON_DIRECTIONAL | NON_DIRECTIONAL | BEARISH | INSUFFICIENT_EVIDENCE | PRICE_DOWNTREND; CONFLICT |
| AAPL | `AAPL260814C00310000` | MIXED | - | - | - | NEUTRAL | NON_DIRECTIONAL | UNKNOWN | UNKNOWN | NON_DIRECTIONAL | NON_DIRECTIONAL | NEUTRAL | INSUFFICIENT_EVIDENCE | PRICE_MIXED |
| AMZN | `AMZN260812C00275000` | UPTREND | - | - | + | BULLISH_SUPPORT | NON_DIRECTIONAL | UNKNOWN | UNKNOWN | NON_DIRECTIONAL | NON_DIRECTIONAL | BULLISH | INSUFFICIENT_EVIDENCE | PRICE_UPTREND; CONFLICT |
| AAPL | `AAPL260812C00310000` | MIXED | - | - | - | NEUTRAL | NON_DIRECTIONAL | UNKNOWN | UNKNOWN | NON_DIRECTIONAL | NON_DIRECTIONAL | NEUTRAL | INSUFFICIENT_EVIDENCE | PRICE_MIXED |
| TSLA | `TSLA260814C00350000` | DOWNTREND | - | + | - | BEARISH_SUPPORT | NON_DIRECTIONAL | UNKNOWN | UNKNOWN | NON_DIRECTIONAL | NON_DIRECTIONAL | BEARISH | INSUFFICIENT_EVIDENCE | PRICE_DOWNTREND; CONFLICT |
| AMZN | `AMZN260814C00272500` | UPTREND | - | - | + | BULLISH_SUPPORT | NON_DIRECTIONAL | UNKNOWN | UNKNOWN | NON_DIRECTIONAL | NON_DIRECTIONAL | BULLISH | INSUFFICIENT_EVIDENCE | PRICE_UPTREND; CONFLICT |
| GOOGL | `GOOGL260812C00350000` | DOWNTREND | + | - | - | BEARISH_SUPPORT | NON_DIRECTIONAL | UNKNOWN | UNKNOWN | NON_DIRECTIONAL | NON_DIRECTIONAL | BEARISH | INSUFFICIENT_EVIDENCE | PRICE_DOWNTREND; CONFLICT |
| GOOGL | `GOOGL260812C00352500` | DOWNTREND | + | - | - | BEARISH_SUPPORT | NON_DIRECTIONAL | UNKNOWN | UNKNOWN | NON_DIRECTIONAL | NON_DIRECTIONAL | BEARISH | INSUFFICIENT_EVIDENCE | PRICE_DOWNTREND; CONFLICT |
| GOOGL | `GOOGL260812C00355000` | DOWNTREND | + | - | - | BEARISH_SUPPORT | NON_DIRECTIONAL | UNKNOWN | UNKNOWN | NON_DIRECTIONAL | NON_DIRECTIONAL | BEARISH | INSUFFICIENT_EVIDENCE | PRICE_DOWNTREND; CONFLICT |
| AMZN | `AMZN261016C00310000` | UPTREND | - | - | + | BULLISH_SUPPORT | NON_DIRECTIONAL | UNKNOWN | UNKNOWN | NON_DIRECTIONAL | NON_DIRECTIONAL | BULLISH | INSUFFICIENT_EVIDENCE | PRICE_UPTREND; CONFLICT |
| GOOGL | `GOOGL260814C00357500` | DOWNTREND | + | - | - | BEARISH_SUPPORT | NON_DIRECTIONAL | UNKNOWN | UNKNOWN | NON_DIRECTIONAL | NON_DIRECTIONAL | BEARISH | INSUFFICIENT_EVIDENCE | PRICE_DOWNTREND; CONFLICT |
| AMZN | `AMZN260812C00277500` | UPTREND | - | - | + | BULLISH_SUPPORT | NON_DIRECTIONAL | UNKNOWN | UNKNOWN | NON_DIRECTIONAL | NON_DIRECTIONAL | BULLISH | INSUFFICIENT_EVIDENCE | PRICE_UPTREND; CONFLICT |
| TSLA | `TSLA260812C00345000` | DOWNTREND | - | + | - | BEARISH_SUPPORT | NON_DIRECTIONAL | UNKNOWN | UNKNOWN | NON_DIRECTIONAL | NON_DIRECTIONAL | BEARISH | INSUFFICIENT_EVIDENCE | PRICE_DOWNTREND; CONFLICT |
| AAPL | `AAPL260814C00312500` | MIXED | - | - | - | NEUTRAL | NON_DIRECTIONAL | UNKNOWN | UNKNOWN | NON_DIRECTIONAL | NON_DIRECTIONAL | NEUTRAL | INSUFFICIENT_EVIDENCE | PRICE_MIXED |
| GOOGL | `GOOGL260812P00340000` | DOWNTREND | + | - | - | BEARISH_SUPPORT | NON_DIRECTIONAL | UNKNOWN | UNKNOWN | NON_DIRECTIONAL | NON_DIRECTIONAL | BEARISH | INSUFFICIENT_EVIDENCE | PRICE_DOWNTREND; CONFLICT |
| AAPL | `AAPL260812C00312500` | MIXED | - | - | - | NEUTRAL | NON_DIRECTIONAL | UNKNOWN | UNKNOWN | NON_DIRECTIONAL | NON_DIRECTIONAL | NEUTRAL | INSUFFICIENT_EVIDENCE | PRICE_MIXED |
| GOOGL | `GOOGL260812C00360000` | DOWNTREND | + | - | - | BEARISH_SUPPORT | NON_DIRECTIONAL | UNKNOWN | UNKNOWN | NON_DIRECTIONAL | NON_DIRECTIONAL | BEARISH | INSUFFICIENT_EVIDENCE | PRICE_DOWNTREND; CONFLICT |
| AAPL | `AAPL260814P00295000` | MIXED | - | - | - | NEUTRAL | NON_DIRECTIONAL | UNKNOWN | UNKNOWN | NON_DIRECTIONAL | NON_DIRECTIONAL | NEUTRAL | INSUFFICIENT_EVIDENCE | PRICE_MIXED |
| AMZN | `AMZN260814P00262500` | UPTREND | - | - | + | BULLISH_SUPPORT | NON_DIRECTIONAL | UNKNOWN | UNKNOWN | NON_DIRECTIONAL | NON_DIRECTIONAL | BULLISH | INSUFFICIENT_EVIDENCE | PRICE_UPTREND; CONFLICT |

Common audit reasons for every row: `POSITIONING_INTENT_UNOBSERVED`,
`IV_DIRECTIONAL_MAPPING_NOT_ESTABLISHED`, `TERM_IV_DIRECTIONAL_MAPPING_NOT_ESTABLISHED`,
`EXECUTION_NOT_DIRECTIONAL`, `RESEARCH_READINESS_NOT_DIRECTIONAL`, and—for Design B—
`ONLY_ONE_ACCEPTED_DIRECTIONAL_FAMILY`. NVDA uses GEX primary
`GEX_DIRECTIONAL_MAPPING_NOT_ESTABLISHED` plus secondary `DEALER_SOURCE_DEGRADED`; other ticker
rows use primary `DEALER_SOURCE_UNAVAILABLE`.

## NVDA Example + Audit Drilldown

Contract: `NVDA260821C00220000`

```text
Observed Flow Direction: UNRESOLVED
Price Direction: BULLISH_SUPPORT
Positioning Direction: NON_DIRECTIONAL
Volatility Direction: UNKNOWN
Dealer/GEX Direction: UNKNOWN
Execution Direction: NON_DIRECTIONAL
Research Readiness Direction: NON_DIRECTIONAL

Design A Price Directional Bias: BULLISH
Basis: PRICE_ACTION_ONLY
Directional Family Count: 1

Design B Model Research Bias: INSUFFICIENT_EVIDENCE
Reason: ONLY_ONE_ACCEPTED_DIRECTIONAL_FAMILY
```

### PRICE = BULLISH_SUPPORT

```yaml
primary_reason_code: PRICE_UPTREND
rule: latest_regular_close > SMA20 > SMA50
latest_regular_close_usd: 224.09
sma_20: 208.3825
sma_50: 206.2618
return_1d: +3.0299%
return_5d: +2.2215%
return_20d: +5.4541%
price_quality: AVAILABLE_WITH_GAPS
coverage_quality: VALID_WITH_GAPS
source_trading_date: 2026-08-12
```

All return signs align, but they remain correlated audit subsignals, not three additional families.

### VOLATILITY = UNKNOWN

```yaml
primary_reason_code: IV_DIRECTIONAL_MAPPING_NOT_ESTABLISHED
secondary_reason_codes: [TERM_IV_DIRECTIONAL_MAPPING_NOT_ESTABLISHED]
iv_rank: 32.4659
iv_rank_vendor_date: 2026-08-12
term_topology: LOCAL_PEAK
candidate_iv: 0.33103896
shorter_iv: 0.31939136
longer_iv: 0.31160612
candidate_minus_shorter: 0.01164760
candidate_minus_longer: 0.01943284
candidate_minus_neighbor_mean: 0.01554022
implied_move_usd: 7.8519
implied_move_pct: 3.5282%
```

Available IV structure is useful, but no accepted rule converts it to underlying direction.

### DEALER/GEX = UNKNOWN

```yaml
primary_reason_code: GEX_DIRECTIONAL_MAPPING_NOT_ESTABLISHED
secondary_reason_codes: [DEALER_SOURCE_DEGRADED]
exact_cell_status: EXACT_MATCH
gex_sign: POSITIVE_NET_GEX
net_gex_usd: 59652544
call_gex_usd: 59166863
put_gex_usd: 485681
row_net_gex_usd: 81553764
row_abs_gex_usd: 121659202
vendor_row_rank: 1
source_quality: AVAILABLE_DEGRADED
generated_at: 2026-08-13T09:41:13.889185441Z
```

The positive exact value remains factual. It is not Bullish support.

Positioning remains `MULTI_EVIDENCE` (Radar + Structure 70.722), persistence is not yet available,
Execution is available, and Readiness is `CONTEXT_PARTIAL` because Dealer quality is degraded.

## TSLA Example + Audit Drilldown

Contract: `TSLA260814C00335000`

```text
Observed Flow Direction: UNRESOLVED
Price Direction: BEARISH_SUPPORT
Positioning Direction: NON_DIRECTIONAL
Volatility Direction: UNKNOWN
Dealer/GEX Direction: UNKNOWN
Execution Direction: NON_DIRECTIONAL
Research Readiness Direction: NON_DIRECTIONAL

Design A Price Directional Bias: BEARISH
Basis: PRICE_ACTION_ONLY
Directional Family Count: 1

Design B Model Research Bias: INSUFFICIENT_EVIDENCE
Reason: ONLY_ONE_ACCEPTED_DIRECTIONAL_FAMILY
```

### PRICE = BEARISH_SUPPORT

```yaml
primary_reason_code: PRICE_DOWNTREND
secondary_reason_codes: [PRICE_SUBSIGNAL_CONFLICT]
rule: latest_regular_close < SMA20 < SMA50
latest_regular_close_usd: 327.51
sma_20: 333.6230
sma_50: 374.3896
return_1d: -1.5925%
return_5d: +1.8535%
return_20d: -16.9726%
price_quality: AVAILABLE_WITH_GAPS
coverage_quality: VALID_WITH_GAPS
source_trading_date: 2026-08-12
```

The positive 5-session return is an audit conflict but does not overturn or vote against the
accepted Trend rule.

### VOLATILITY / DEALER = UNKNOWN

```yaml
volatility_primary: IV_DIRECTIONAL_MAPPING_NOT_ESTABLISHED
volatility_secondary:
  - TERM_IV_DIRECTIONAL_MAPPING_NOT_ESTABLISHED
  - TERM_TOPOLOGY_INCOMPLETE
iv_rank: 1.0913
candidate_iv: 0.40568449
shorter_iv: null
longer_iv: 0.30914328
term_topology: INCOMPLETE
implied_move_pct: 1.6126%

dealer_primary: DEALER_SOURCE_UNAVAILABLE
dealer_semantic_note: GEX_DIRECTIONAL_MAPPING_NOT_ESTABLISHED
candidate_cell_status: UNAVAILABLE
gex_sign: UNKNOWN
source_quality: UNAVAILABLE
availability_reason: VALIDATION_ERROR
```

Positioning is `SINGLE_EVIDENCE` Radar, Execution is available, and Readiness is
`CONTEXT_PARTIAL` because Dealer is unavailable.

## Audit UI Feasibility

Future UI can use one expandable state row per dimension:

```text
VOLATILITY                     UNKNOWN   [Why?]
```

Expansion sections:

1. **Why?** state plus primary/secondary reason codes and registry text;
2. **Rule** rule ID/version and whether it evaluated or was unavailable;
3. **Evidence Used** normalized field names and immutable evidence references;
4. **Raw Values** only relevant scalar values;
5. **Data Quality** availability/degraded/truncated status;
6. **Timestamp** source observation/as-of;
7. **Specification Version** exact v3 spec.

No large raw payload needs duplication; retain a link to preserved raw evidence.

## Future Trade Expression Boundary

V3 must not select Long Call, Short Put, Call Spread, Long Put, Put Spread, or Short Call and must
not output BUY, SELL, HIGH CONVICTION, or similar language.

After directional research is accepted, a later Trade Expression layer may combine explicit
directional bias with IV context, term structure, DTE, Delta, Theta, Vega, liquidity, strike
distance, and risk/reward to choose a hypothetical structure. Direction and option strategy remain
separate decisions.

## Proposed Minimal Phase 2B v3 Production Model

No implementation is made here. Recommended future object:

```yaml
observed_flow_direction: UNRESOLVED

directional_research:
  price:
    state: BULLISH_SUPPORT
    audit: {...}
  positioning:
    state: NON_DIRECTIONAL
    relevance: MULTI_EVIDENCE
    audit: {...}
  volatility:
    state: UNKNOWN
    audit: {...}
  dealer_gex:
    state: UNKNOWN
    audit: {...}
  execution:
    state: NON_DIRECTIONAL
    audit: {...}
  research_readiness:
    state: NON_DIRECTIONAL
    context_state: CONTEXT_PARTIAL
    audit: {...}

price_directional_bias: BULLISH
bias_basis: PRICE_ACTION_ONLY
directional_family_count: 1

model_research_bias: INSUFFICIENT_EVIDENCE
model_bias_reason: ONLY_ONE_ACCEPTED_DIRECTIONAL_FAMILY
```

Future production should use immutable `signal_spec_v3.0_phase2b`, append-only results, explicit
rule versions, and evidence references. That specification is proposed, not created by this gate.

## Unsupported Interpretations

Do not implement or infer:

- Call = bullish or Put = bearish;
- positive ΔOI plus Call/Put as direction;
- Premium, Structure, Persistence, Cluster, or evidence breadth as direction;
- high/low IV Rank as bullish/bearish;
- term `LOCAL_PEAK`, `LOCAL_TROUGH`, rising, or falling as price direction;
- implied move as signed direction;
- positive/negative GEX as bullish/bearish, support/resistance, pinning, or acceleration;
- option Delta as market direction;
- Context Complete/Partial/Limited as direction or confidence;
- returns/Trend/SMA distances as multiple independent votes;
- majority vote, weights, Bullish Score, Bearish Score, confidence percentage, or conviction;
- observed flow intent from the scanner's independent Price Directional Bias;
- any option strategy or execution recommendation.

## Nightwatch Ledger

| Item | Result |
| --- | ---: |
| Nightwatch endpoints contacted | none |
| Nightwatch calls | 0 |
| Network attempts | 0 |
| Paid units consumed | 0 |
| Market-data refresh | not performed |

All evidence came from existing persisted PostgreSQL rows.

## Open Issues

1. Only `PRICE_ACTION` has accepted directional semantics; broad multi-family Model Research Bias is
   not yet supported.
2. Return horizons are correlated with Trend and conflict on 25 directional-trend candidates; their
   production role beyond audit context requires explicit outcome calibration.
3. No forward-return or outcome dataset was evaluated, so predictive accuracy, thresholds, weights,
   probabilities, and confidence claims are unsupported.
4. IV and GEX may support future non-price-directional volatility/path states, but source semantics,
   completeness, and outcomes require dedicated research.
5. Dealer evidence is degraded for NVDA and unavailable for the other five contract tickers.
6. Persistent OI history remains insufficient, and current evidence timestamps are asynchronous.
7. Phase 2B v3 production logic and Phase 2B v4 remain unimplemented by design.

# Phase 2B v2 — Trade Setup State Calibration Gate

Date context: 2026-08-14

Starting Git SHA: `e3748a52c5b43ff9692be53f36a0bbaad6c84818`

Accepted specifications: `signal_spec_v1.3_phase2a`, `signal_spec_v1.1_phase2b`

## Executive conclusion

The smallest defensible Phase 2B v2 is a set of independent, factual states—not a score:

1. positioning evidence families and breadth;
2. existing Price Trend plus raw strike-distance context;
3. threshold-free local Term IV topology when all three nodes exist;
4. exact candidate-cell GEX sign when an exact cell exists;
5. existing execution/liquidity treatment plus raw Greeks;
6. explicit research-readiness coverage.

The sample does **not** justify Near/Far, IV Rank LOW/MID/HIGH, materially elevated IV, dominant
GEX, bullish/bearish confirmation, or any weighted composite. `DIRECTION = UNRESOLVED` remains
authoritative.

## Git / Safety

- Starting SHA: `e3748a52c5b43ff9692be53f36a0bbaad6c84818`.
- This gate changes no production source, schema, migration, API contract, Dashboard, glossary,
  Phase 2A behavior, or Phase 2B v1.1 calculation.
- No Phase 2A scan, MAG7 scan, Daily Archive, chain call, RV, volatility-stats, skew, Standard GEX,
  0DTE Dealer GEX, or earnings call was made.
- All calls used the existing server-side client, concurrency 1, retries 0. No secret or
  Authorization header was printed or persisted.
- Temporary diagnostic scripts were removed after producing this report.
- The development database gained five immutable v1.1 ticker context snapshots and their usage/raw
  evidence. No candidate state, v2 state, score, threshold, or schema was persisted.
- Repository validation after diagnostics: backend `pytest` passed 180 tests; Ruff passed; frontend
  ESLint passed; the glossary/null-safety check passed; and the Next.js production build passed.
  Pytest emitted only a sandbox permission warning for its optional cache write.
- `.env`, `backend/.env`, and `frontend/.env` resolve to the repository's `.env` ignore rule. An
  exact-value comparison (without printing either value) found zero occurrences of the local
  `DATABASE_URL` and `NIGHTWATCH_API_KEY` values in all tracked files and zero in tracked frontend
  files. No migration file changed.

## What “confirmation” means

Three meanings must remain separate:

**Positioning Confirmation** means independent positioning evidence families agree that a
contract/expiry deserves attention—for example Radar plus persistence, or Radar plus separately
derived structural concentration. It does not resolve whether the economic position is long,
short, spread, or hedge.

**Market Context** means price, IV, Dealer/GEX, and execution data describe the environment around
the positioning. These layers can agree, disagree, or be missing; none is automatically a
confirmation of the initiating trade.

**Trade Direction Confirmation** requires economic-intent evidence that the current data does not
contain. Call/Put identity, positive ΔOI, trend, Premium, IV, and GEX sign cannot supply that missing
intent. Phase 2B v2 therefore must not claim directional confirmation.

## Dataset Coverage

The authoritative current Dashboard query contains two different entity types. Keeping them
separate is essential.

| Coverage item | Result |
| --- | ---: |
| Total Deep Dive rows | 72 |
| Contract-level candidates | 46 |
| Expiry-only route candidates | 26 |
| Unique contracts | 46 |
| Unique ticker/expiry pairs across all rows | 31 |
| Distinct expiration dates across all rows | 8 |
| Contract-candidate ticker/expiry pairs | 14 |
| Contract-candidate distinct expiration dates | 5 |
| Unique tickers across all rows | 7 |
| Contract-candidate tickers | 6: AAPL, AMZN, GOOGL, META, NVDA, TSLA |

Expiry-only rows lack contract, right, strike, contract liquidity, Greeks, and exact candidate-cell
identity. They remain valid Phase 2A route observations but are excluded from contract-state
distributions rather than being fabricated into contracts. MSFT appears only in this expiry-only
subset, so no MSFT Phase 2B ticker context was fetched.

Before this gate, Phase 2B v1.1 coverage was one ticker snapshot and one candidate evaluation:
`NVDA260821C00220000`. After the diagnostic fetch, ticker snapshot coverage is 6/6 contract
tickers; candidate evaluation coverage remains 1/46 because this gate did not create production
v2 evaluations.

| Contract-level layer | Coverage |
| --- | ---: |
| Usable Price Context | 46/46 |
| Raw IV Rank | 46/46, representing 6 unique ticker values |
| Exact candidate Term node | 24/46 |
| Complete shorter/candidate/longer topology | 12/46 |
| Exact candidate Heatmap cell | 11/46, all NVDA |
| Degraded Heatmap | 11/46, all NVDA |
| Unavailable Heatmap | 35/46 across the other five tickers |
| Bid/ask, computed spread, and Greeks | 46/46 |
| Some persisted history observation count | 31/46 |
| Accepted persistence score | 0/46 |
| History confidence | 46/46 `INSUFFICIENT` |

Key limitations are temporal and cross-sectional: Radar observations are from 2026-08-12; chain
quote/Greek evidence ranges from 2026-08-07 through 2026-08-11; ticker context is mostly as of
2026-08-13; many candidates expired on 2026-08-12. This is a state-model design sample, not a
synchronous market snapshot and not an outcome sample.

## Positioning Depth

All 46 contract candidates are versioned Radar Material Events with `COMPLETE` archive evidence
and `RADAR_EVENT` trigger source. Premium, ΔOI, relative OI change, and volume/trades from a single
Radar record count as **one** evidence family, not several.

- Contract persistence score available: 0/46.
- Expiry persistence score available: 0/46.
- Exact cluster membership: 2/46, both AAPL puts.
- Separate Contract Positioning Structure Score present: 16/46.
- `SINGLE_EVIDENCE`: 30/46.
- `MULTI_EVIDENCE`: 16/46, from Radar plus structural/cluster evidence.
- Evidence-family count distribution: 1 family = 30; 2 families = 16; no candidate has 3+.
- History confidence is `INSUFFICIENT` for every candidate. Thirty-one have only one persisted
  history observation; fifteen have no populated observation count.

This supports a transparent breadth state, but not a new Positioning Score. `MULTI_EVIDENCE`
means multiple evidence families deserve review; it does not mean stronger trade direction.

### Per-candidate positioning supplement

Relative OI change is stored as a ratio (for example `0.0721` is about 7.21%). “Structure” is the
existing Contract Positioning Structure Score. Cluster is exact stored cluster membership.

| Contract | Relative OI change | Structure | Cluster | History | Evidence families | Breadth |
| --- | ---: | ---: | --- | --- | ---: | --- |
| `TSLA260812C00335000` | 1.4702 | 58.164 | ABSENT | INSUFFICIENT | 2 | MULTI_EVIDENCE |
| `NVDA261016P00220000` | 0.5903 | — | ABSENT | INSUFFICIENT | 1 | SINGLE_EVIDENCE |
| `TSLA260812P00335000` | 11.7139 | 35.625 | ABSENT | INSUFFICIENT | 2 | MULTI_EVIDENCE |
| `TSLA260812C00332500` | 1.8217 | 44.257 | ABSENT | INSUFFICIENT | 2 | MULTI_EVIDENCE |
| `NVDA260904C00215000` | 0.8333 | — | ABSENT | INSUFFICIENT | 1 | SINGLE_EVIDENCE |
| `TSLA260814C00335000` | 0.1859 | — | ABSENT | INSUFFICIENT | 1 | SINGLE_EVIDENCE |
| `TSLA260812C00340000` | 1.1599 | 58.928 | ABSENT | INSUFFICIENT | 2 | MULTI_EVIDENCE |
| `NVDA260821C00220000` | 0.0721 | 70.722 | ABSENT | INSUFFICIENT | 2 | MULTI_EVIDENCE |
| `TSLA260812C00337500` | 1.5395 | 42.261 | ABSENT | INSUFFICIENT | 2 | MULTI_EVIDENCE |
| `NVDA260814P00220000` | 0.9687 | — | ABSENT | INSUFFICIENT | 1 | SINGLE_EVIDENCE |
| `NVDA260814P00225000` | 0.8534 | — | ABSENT | INSUFFICIENT | 1 | SINGLE_EVIDENCE |
| `META260812P00607500` | 49.4407 | 21.190 | ABSENT | INSUFFICIENT | 2 | MULTI_EVIDENCE |
| `AAPL260812C00305000` | 4.5854 | 48.648 | ABSENT | INSUFFICIENT | 2 | MULTI_EVIDENCE |
| `META260812C00612500` | 7.3312 | 32.946 | ABSENT | INSUFFICIENT | 2 | MULTI_EVIDENCE |
| `AAPL260812C00307500` | 1.4389 | 53.204 | ABSENT | INSUFFICIENT | 2 | MULTI_EVIDENCE |
| `AAPL260812P00305000` | 0.4962 | 74.400 | PRESENT | INSUFFICIENT | 2 | MULTI_EVIDENCE |
| `NVDA260821C00217500` | 1.6284 | 30.482 | ABSENT | INSUFFICIENT | 2 | MULTI_EVIDENCE |
| `NVDA260814C00225000` | 0.0820 | — | ABSENT | INSUFFICIENT | 1 | SINGLE_EVIDENCE |
| `TSLA260814P00330000` | 1.2866 | — | ABSENT | INSUFFICIENT | 1 | SINGLE_EVIDENCE |
| `NVDA260814P00215000` | 0.1578 | — | ABSENT | INSUFFICIENT | 1 | SINGLE_EVIDENCE |
| `TSLA260814P00327500` | 2.2781 | — | ABSENT | INSUFFICIENT | 1 | SINGLE_EVIDENCE |
| `NVDA261016P00180000` | 0.4205 | — | ABSENT | INSUFFICIENT | 1 | SINGLE_EVIDENCE |
| `NVDA260814C00217500` | 0.7952 | — | ABSENT | INSUFFICIENT | 1 | SINGLE_EVIDENCE |
| `AAPL260814C00307500` | 0.6124 | — | ABSENT | INSUFFICIENT | 1 | SINGLE_EVIDENCE |
| `NVDA260814C00222500` | 0.7801 | — | ABSENT | INSUFFICIENT | 1 | SINGLE_EVIDENCE |
| `AMZN260814P00272500` | 1.1750 | — | ABSENT | INSUFFICIENT | 1 | SINGLE_EVIDENCE |
| `AAPL260812P00307500` | 1.0111 | 78.435 | PRESENT | INSUFFICIENT | 2 | MULTI_EVIDENCE |
| `GOOGL260812P00347500` | 7.0079 | — | ABSENT | INSUFFICIENT | 1 | SINGLE_EVIDENCE |
| `AAPL260814C00310000` | 0.3063 | — | ABSENT | INSUFFICIENT | 1 | SINGLE_EVIDENCE |
| `AMZN260812C00275000` | 2.2877 | — | ABSENT | INSUFFICIENT | 1 | SINGLE_EVIDENCE |
| `AAPL260812C00310000` | 1.2846 | 50.098 | ABSENT | INSUFFICIENT | 2 | MULTI_EVIDENCE |
| `TSLA260814C00350000` | 0.2718 | — | ABSENT | INSUFFICIENT | 1 | SINGLE_EVIDENCE |
| `AMZN260814C00272500` | 5.0449 | — | ABSENT | INSUFFICIENT | 1 | SINGLE_EVIDENCE |
| `GOOGL260812C00350000` | 9.1929 | — | ABSENT | INSUFFICIENT | 1 | SINGLE_EVIDENCE |
| `GOOGL260812C00352500` | 3.0993 | — | ABSENT | INSUFFICIENT | 1 | SINGLE_EVIDENCE |
| `GOOGL260812C00355000` | 3.0115 | — | ABSENT | INSUFFICIENT | 1 | SINGLE_EVIDENCE |
| `AMZN261016C00310000` | 0.3296 | — | ABSENT | INSUFFICIENT | 1 | SINGLE_EVIDENCE |
| `GOOGL260814C00357500` | 20.3074 | — | ABSENT | INSUFFICIENT | 1 | SINGLE_EVIDENCE |
| `AMZN260812C00277500` | 1.1945 | — | ABSENT | INSUFFICIENT | 1 | SINGLE_EVIDENCE |
| `TSLA260812C00345000` | 1.0476 | 36.776 | ABSENT | INSUFFICIENT | 2 | MULTI_EVIDENCE |
| `AAPL260814C00312500` | 0.3453 | — | ABSENT | INSUFFICIENT | 1 | SINGLE_EVIDENCE |
| `GOOGL260812P00340000` | 7.6819 | — | ABSENT | INSUFFICIENT | 1 | SINGLE_EVIDENCE |
| `AAPL260812C00312500` | 0.6312 | 40.815 | ABSENT | INSUFFICIENT | 2 | MULTI_EVIDENCE |
| `GOOGL260812C00360000` | 1.4782 | — | ABSENT | INSUFFICIENT | 1 | SINGLE_EVIDENCE |
| `AAPL260814P00295000` | 0.8454 | — | ABSENT | INSUFFICIENT | 1 | SINGLE_EVIDENCE |
| `AMZN260814P00262500` | 2.2114 | — | ABSENT | INSUFFICIENT | 1 | SINGLE_EVIDENCE |

## Price / Strike Context

All 46 candidates have a usable v1.1 canonical regular-session Price Context. Candidate-weighted
Price Trend counts are UPTREND 17, DOWNTREND 19, MIXED 10, UNKNOWN 0. Nine candidates inherit a
no-gap `AVAILABLE` ticker series (GOOGL/META); 37 inherit `AVAILABLE_WITH_GAPS`. These are
descriptive ticker states, never trade-direction states.

Absolute strike distance in ATR units uses a linear percentile convention at index
`(n - 1) × p`:

| Statistic | abs(strike distance ATR) |
| --- | ---: |
| n | 46 |
| min | 0.0053 |
| p25 | 0.3071 |
| median | 0.5939 |
| p75 | 0.8848 |
| p90 | 1.1285 |
| max | 5.5824 |

Diagnostic cumulative counts: ≤0.25 ATR 7; ≤0.50 ATR 17; ≤1.00 ATR 37; ≤2.00 ATR 44; >2.00
ATR 2. The distribution shows that distance is informative, but this one small, clustered sample
cannot justify production `NEAR_SPOT`/`MODERATE_DISTANCE`/`FAR_FROM_SPOT` cutoffs. Keep the signed
raw distance and require versioned configuration before adding such states.

## Volatility / Term IV

### IV Rank

IV Rank is ticker-level, so calibration uses six unique ticker values rather than weighting NVDA
or AAPL by their candidate counts.

| Ticker | IV Rank |
| --- | ---: |
| AAPL | 37.3743 |
| AMZN | 18.5510 |
| GOOGL | 16.9247 |
| META | 31.3842 |
| NVDA | 32.4659 |
| TSLA | 1.0913 |

Distribution: min 1.0913; p25 17.3313; median 24.9676; p75 32.1955; max 37.3743. Diagnostic
ranges contain 3 tickers in 0–20, 3 in 20–40, and 0 in each of 40–60, 60–80, and 80–100.

Conclusion: `INSUFFICIENT_SAMPLE_FOR_CALIBRATION`. Six tickers occupying only the lower two
diagnostic ranges cannot justify LOW/MID/HIGH thresholds.

### Local Term IV topology

Comparison uses only an absolute floating-point tolerance of `1e-12`, solely to make equality
deterministic. It is not a financial threshold.

| Topology | Candidates |
| --- | ---: |
| LOCAL_PEAK | 2 |
| LOCAL_TROUGH | 1 |
| RISING_THROUGH_CANDIDATE | 2 |
| FALLING_THROUGH_CANDIDATE | 7 |
| FLAT_OR_EQUAL | 0 |
| INCOMPLETE | 34 |

Although 24 candidates have an exact candidate-expiry node, only 12 have both shorter and longer
nodes needed for topology. Topology is therefore threshold-free and implementable with explicit
`INCOMPLETE`, but coverage is limited.

Signed IV differences (vendor values are decimal IV units):

| Difference | n | min | p25 | median | p75 | p90 | max |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Candidate − shorter | 12 | -0.08214 | -0.08214 | -0.05453 | 0.00001 | 0.01048 | 0.01165 |
| Candidate − longer | 24 | -0.04435 | 0.05246 | 0.06412 | 0.08473 | 0.09654 | 0.09654 |
| Candidate − available-neighbour mean | 24 | -0.02219 | -0.00934 | 0.04015 | 0.08473 | 0.09654 | 0.09654 |

Across the 36 available individual neighbour comparisons, absolute difference distribution is min
0.000012; p25 0.01943; median 0.06412; p75 0.08214; p90 0.09063; max 0.09654. This wide range
shows topology and magnitude are different dimensions. Any future “materially elevated” label
requires a configured, versioned threshold and more representative data.

## Dealer / GEX

The diagnostic refresh returned HTTP 400 `VALIDATION_ERROR` for Dealer Heatmap on AAPL, AMZN,
GOOGL, META, and TSLA. Their 35 candidates are `UNKNOWN`; missing cells are not zero. The 11 NVDA
candidates reuse a persisted Heatmap explicitly marked vendor state `degraded`; all 11 happened to
have exact cells.

Exact-cell sign counts: POSITIVE_NET_GEX 7; NEGATIVE_NET_GEX 4; ZERO_NET_GEX 0; UNKNOWN 35.
These labels describe the sign of the returned number only. They do not mean support, resistance,
bullish, or bearish.

Exact candidate-cell net GEX (n=11): min -15,769,680; p25 -2,338,189; median 6,910,511; p75
28,251,278; p90 33,704,507; max 59,652,544. Absolute values: min 2,175,617; p25 4,628,967;
median 15,769,680; p75 28,251,278; p90 33,704,507; max 59,652,544.

Normalization diagnostics, available only for the same 11 degraded NVDA rows:

| Quantity | Mathematical status | n | min | p25 | median | p75 | p90 | max |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `abs(cell net) / row absolute GEX` | valid for returned row; not a complete-surface share | 11 | 0.0596 | 0.1502 | 0.3009 | 0.4457 | 0.5101 | 0.8259 |
| `candidate row abs / top-ranked row abs` | valid within returned vendor-ranked rows only | 11 | 0.0636 | 0.2772 | 0.3354 | 0.7895 | 1.0000 | 1.0000 |
| Vendor row rank | raw vendor field; interpretable without cross-ticker USD comparison | 11 | 1 | — | — | — | — | 18 |

The first ratio combines an expiry×strike cell numerator with a ticker-wide row aggregate and must
not be called a complete-universe market share. Both ratios are unsafe as production states while
the only sample is one degraded ticker. Keep exact cell values, sign, and vendor rank as raw
context; defer normalized magnitude states.

## Execution

All 46 candidates have persisted bid, ask, midpoint, spread, Delta, Gamma, Theta, Vega, and Charm.
Spread percent distribution is p25 2.4267%, median 3.8370%, p75 8.1522%, p90 12.0238%, max
28.5714%. These are descriptive; this gate defines no new liquidity cutoff.

Absolute Delta distribution: min 0.0307; p25 0.1631; median 0.3687; p75 0.5384; p90 0.6162;
max 0.8101.

| Absolute Delta diagnostic range | Count |
| --- | ---: |
| 0–0.10 | 5 |
| 0.10–0.20 | 10 |
| 0.20–0.35 | 6 |
| 0.35–0.65 | 21 |
| 0.65–0.80 | 3 |
| 0.80–0.90 | 1 |
| 0.90–1.00 | 0 |

Existing Phase 2A spread/liquidity hard-rejection and risk-flag semantics should be reused. Phase
2B v2 may expose bid/ask/mid/spread and Greeks as raw context, but should not duplicate thresholds
or create a new execution score.

## Data Quality / Research Readiness

The diagnostic simulation treats six core layers independently: positioning, usable Price
Context, IV Rank, exact candidate Term node, exact/non-degraded Dealer candidate evidence, and
liquidity/Greeks. `CONTEXT_COMPLETE` requires all; exactly one unavailable/degraded layer is
`CONTEXT_PARTIAL`; two or more are `CONTEXT_LIMITED`. This is coverage only, not alpha.

| Proposed readiness state | Candidates |
| --- | ---: |
| CONTEXT_COMPLETE | 0 |
| CONTEXT_PARTIAL | 24 |
| CONTEXT_LIMITED | 22 |

No candidate is complete because all Heatmap evidence is either unavailable or degraded. The state
is feasible if its checklist and version are persisted; it must never be displayed as good/bad
trade quality.

Shared ticker timestamps:

| Ticker | Latest regular date | Price quality | Stock State as-of | OHLC as-of | IV/Term as-of | Heatmap |
| --- | --- | --- | --- | --- | --- | --- |
| AAPL | 2026-08-12 | AVAILABLE_WITH_GAPS | 2026-08-13 21:20:11Z | 2026-08-12 04:00Z | 2026-08-13 | unavailable, HTTP 400 |
| AMZN | 2026-08-13 | AVAILABLE_WITH_GAPS | 2026-08-13 21:19:38Z | 2026-08-13 04:00Z | 2026-08-13 | unavailable, HTTP 400 |
| GOOGL | 2026-08-13 | AVAILABLE | 2026-08-13 21:20:02Z | 2026-08-13 04:00Z | 2026-08-13 | unavailable, HTTP 400 |
| META | 2026-08-13 | AVAILABLE | 2026-08-13 21:18:54Z | 2026-08-13 04:00Z | 2026-08-13 | unavailable, HTTP 400 |
| NVDA | 2026-08-12 | AVAILABLE_WITH_GAPS | 2026-08-13 09:25:04Z | 2026-08-12 04:00Z | 2026-08-12 | degraded, generated 2026-08-13 09:41Z |
| TSLA | 2026-08-12 | AVAILABLE_WITH_GAPS | 2026-08-13 21:20:35Z | 2026-08-13 04:00Z | 2026-08-13 | unavailable, HTTP 400 |

## Threshold-Free Attributes

The following factual diagnostic representation is supported:

- Positioning: `RADAR_EVENT`; `PERSISTENCE_PRESENT` or `NOT_YET_AVAILABLE`;
  `STRUCTURE_PRESENT`/`ABSENT`; `CLUSTER_PRESENT`/`ABSENT`; `SINGLE_EVIDENCE`/`MULTI_EVIDENCE`.
- Price: accepted `UPTREND`/`DOWNTREND`/`MIXED`/`UNKNOWN`; raw signed strike distance percent and
  ATR distance.
- Term IV: `LOCAL_PEAK`, `LOCAL_TROUGH`, `RISING_THROUGH_CANDIDATE`,
  `FALLING_THROUGH_CANDIDATE`, `FLAT_OR_EQUAL`, or `INCOMPLETE`.
- Dealer: `POSITIVE_NET_GEX`, `NEGATIVE_NET_GEX`, `ZERO_NET_GEX`, or `UNKNOWN`, only for exact
  cells; raw vendor row rank.
- Execution: existing accepted liquidity state/flags plus raw spread and Greeks.
- Data: `CONTEXT_COMPLETE`, `CONTEXT_PARTIAL`, or `CONTEXT_LIMITED` with a visible layer checklist.

No attribute is combined into an overall score or direction.

## Pattern Frequency

The most common threshold-free combinations are:

| RADAR + Price + Term + GEX | Count |
| --- | ---: |
| RADAR_EVENT + DOWNTREND + INCOMPLETE + UNKNOWN | 19 |
| RADAR_EVENT + MIXED + INCOMPLETE + UNKNOWN | 10 |
| RADAR_EVENT + UPTREND + FALLING_THROUGH_CANDIDATE + POSITIVE_NET_GEX | 6 |
| RADAR_EVENT + UPTREND + INCOMPLETE + UNKNOWN | 5 |
| RADAR_EVENT + UPTREND + RISING_THROUGH_CANDIDATE + NEGATIVE_NET_GEX | 2 |
| RADAR_EVENT + UPTREND + LOCAL_PEAK + POSITIVE_NET_GEX | 1 |
| RADAR_EVENT + UPTREND + LOCAL_PEAK + NEGATIVE_NET_GEX | 1 |
| RADAR_EVENT + UPTREND + FALLING_THROUGH_CANDIDATE + NEGATIVE_NET_GEX | 1 |
| RADAR_EVENT + UPTREND + LOCAL_TROUGH + UNKNOWN | 1 |

These frequencies mostly reflect ticker-level shared context and missing Heatmap/expired-term
coverage. They contain no profitability information and must not be optimized into thresholds.

## Compact Candidate Table

Abbreviations: `—` unavailable; Term shape uses its full threshold-free name; GEX sign is exact-cell
only. Signed Dist ATR retains strike minus current Stock State price. Persist is the existing
Contract Persistent Positioning score, unavailable for all candidates.

| Ticker | Contract | Expiry/DTE | R/Strike | Premium | ΔOI | Struct | Trend | Dist ATR | IV Rank | Term shape | Term IV | GEX sign | Rank | Spread | abs Δ | Readiness |
| --- | --- | --- | --- | ---: | ---: | ---: | --- | ---: | ---: | --- | ---: | --- | ---: | ---: | ---: | --- |
| TSLA | `TSLA260812C00335000` | 2026-08-12 / 0 | C / 335.0 | $38,075,053 | 5,978 | 58.164 | DOWNTREND | -0.594 | 1.091 | INCOMPLETE | — | UNKNOWN | — | 1.55% | 0.390 | CONTEXT_LIMITED |
| NVDA | `NVDA261016P00220000` | 2026-10-16 / 65 | P / 220.0 | $28,822,280 | 20,068 | — | UPTREND | -0.477 | 32.466 | RISING_THROUGH_CANDIDATE | 0.3784 | NEGATIVE_NET_GEX | 1 | 2.38% | 0.354 | CONTEXT_PARTIAL |
| TSLA | `TSLA260812P00335000` | 2026-08-12 / 0 | P / 335.0 | $21,129,124 | 4,545 | 35.625 | DOWNTREND | -0.594 | 1.091 | INCOMPLETE | — | UNKNOWN | — | 3.59% | 0.604 | CONTEXT_LIMITED |
| TSLA | `TSLA260812C00332500` | 2026-08-12 / 0 | C / 332.5 | $20,880,082 | 3,126 | 44.257 | DOWNTREND | -0.822 | 1.091 | INCOMPLETE | — | UNKNOWN | — | 1.65% | 0.528 | CONTEXT_LIMITED |
| NVDA | `NVDA260904C00215000` | 2026-09-04 / 23 | C / 215.0 | $16,272,340 | 3,344 | — | UPTREND | -1.115 | 32.466 | FALLING_THROUGH_CANDIDATE | 0.4021 | POSITIVE_NET_GEX | 7 | 2.36% | 0.601 | CONTEXT_PARTIAL |
| TSLA | `TSLA260814C00335000` | 2026-08-14 / 2 | C / 335.0 | $14,541,482 | 2,665 | — | DOWNTREND | -0.594 | 1.091 | INCOMPLETE | 0.4057 | UNKNOWN | — | 1.24% | 0.414 | CONTEXT_PARTIAL |
| TSLA | `TSLA260812C00340000` | 2026-08-12 / 0 | C / 340.0 | $12,170,468 | 5,470 | 58.928 | DOWNTREND | -0.138 | 1.091 | INCOMPLETE | — | UNKNOWN | — | 1.44% | 0.175 | CONTEXT_LIMITED |
| NVDA | `NVDA260821C00220000` | 2026-08-21 / 9 | C / 220.0 | $10,434,044 | 4,531 | 70.722 | UPTREND | -0.477 | 32.466 | LOCAL_PEAK | 0.3310 | POSITIVE_NET_GEX | 1 | 2.56% | 0.479 | CONTEXT_PARTIAL |
| TSLA | `TSLA260812C00337500` | 2026-08-12 / 0 | C / 337.5 | $9,944,161 | 2,939 | 42.261 | DOWNTREND | -0.366 | 1.091 | INCOMPLETE | — | UNKNOWN | — | 0.84% | 0.269 | CONTEXT_LIMITED |
| NVDA | `NVDA260814P00220000` | 2026-08-14 / 2 | P / 220.0 | $8,765,631 | 6,813 | — | UPTREND | -0.477 | 32.466 | FALLING_THROUGH_CANDIDATE | 0.3685 | POSITIVE_NET_GEX | 1 | 2.30% | 0.583 | CONTEXT_PARTIAL |
| NVDA | `NVDA260814P00225000` | 2026-08-14 / 2 | P / 225.0 | $8,731,270 | 4,475 | — | UPTREND | 0.162 | 32.466 | FALLING_THROUGH_CANDIDATE | 0.3685 | POSITIVE_NET_GEX | 2 | 4.88% | 0.759 | CONTEXT_PARTIAL |
| META | `META260812P00607500` | 2026-08-12 / 0 | P / 607.5 | $8,325,733 | 2,917 | 21.190 | DOWNTREND | 0.675 | 31.384 | INCOMPLETE | — | UNKNOWN | — | 9.52% | 0.810 | CONTEXT_LIMITED |
| AAPL | `AAPL260812C00305000` | 2026-08-12 / 0 | C / 305.0 | $7,043,130 | 11,280 | 48.648 | MIXED | 0.005 | 37.374 | INCOMPLETE | — | UNKNOWN | — | 1.89% | 0.582 | CONTEXT_LIMITED |
| META | `META260812C00612500` | 2026-08-12 / 0 | C / 612.5 | $6,688,939 | 3,387 | 32.946 | DOWNTREND | 0.906 | 31.384 | INCOMPLETE | — | UNKNOWN | — | 9.71% | 0.149 | CONTEXT_LIMITED |
| AAPL | `AAPL260812C00307500` | 2026-08-12 / 0 | C / 307.5 | $6,370,913 | 5,993 | 53.204 | MIXED | 0.270 | 37.374 | INCOMPLETE | — | UNKNOWN | — | 3.13% | 0.296 | CONTEXT_LIMITED |
| AAPL | `AAPL260812P00305000` | 2026-08-12 / 0 | P / 305.0 | $6,315,083 | 2,845 | 74.400 | MIXED | 0.005 | 37.374 | INCOMPLETE | — | UNKNOWN | — | 6.61% | 0.446 | CONTEXT_LIMITED |
| NVDA | `NVDA260821C00217500` | 2026-08-21 / 9 | C / 217.5 | $5,809,073 | 7,821 | 30.482 | UPTREND | -0.796 | 32.466 | LOCAL_PEAK | 0.3310 | NEGATIVE_NET_GEX | 9 | 1.98% | 0.572 | CONTEXT_PARTIAL |
| NVDA | `NVDA260814C00225000` | 2026-08-14 / 2 | C / 225.0 | $5,770,572 | 4,571 | — | UPTREND | 0.162 | 32.466 | FALLING_THROUGH_CANDIDATE | 0.3685 | POSITIVE_NET_GEX | 2 | 3.13% | 0.172 | CONTEXT_PARTIAL |
| TSLA | `TSLA260814P00330000` | 2026-08-14 / 2 | P / 330.0 | $5,651,476 | 3,035 | — | DOWNTREND | -1.050 | 1.091 | INCOMPLETE | 0.4057 | UNKNOWN | — | 1.94% | 0.445 | CONTEXT_PARTIAL |
| NVDA | `NVDA260814P00215000` | 2026-08-14 / 2 | P / 215.0 | $5,311,554 | 2,706 | — | UPTREND | -1.115 | 32.466 | FALLING_THROUGH_CANDIDATE | 0.3685 | NEGATIVE_NET_GEX | 7 | 2.68% | 0.341 | CONTEXT_PARTIAL |
| TSLA | `TSLA260814P00327500` | 2026-08-14 / 2 | P / 327.5 | $5,140,493 | 3,440 | — | DOWNTREND | -1.278 | 1.091 | INCOMPLETE | 0.4057 | UNKNOWN | — | 3.73% | 0.379 | CONTEXT_PARTIAL |
| NVDA | `NVDA261016P00180000` | 2026-10-16 / 65 | P / 180.0 | $5,056,945 | 20,543 | — | UPTREND | -5.582 | 32.466 | RISING_THROUGH_CANDIDATE | 0.3784 | NEGATIVE_NET_GEX | 18 | 3.59% | 0.091 | CONTEXT_PARTIAL |
| NVDA | `NVDA260814C00217500` | 2026-08-14 / 2 | C / 217.5 | $4,881,267 | 3,511 | — | UPTREND | -0.796 | 32.466 | FALLING_THROUGH_CANDIDATE | 0.3685 | POSITIVE_NET_GEX | 9 | 2.32% | 0.542 | CONTEXT_PARTIAL |
| AAPL | `AAPL260814C00307500` | 2026-08-14 / 2 | C / 307.5 | $4,272,797 | 6,873 | — | MIXED | 0.270 | 37.374 | INCOMPLETE | 0.2599 | UNKNOWN | — | 5.78% | 0.392 | CONTEXT_PARTIAL |
| NVDA | `NVDA260814C00222500` | 2026-08-14 / 2 | C / 222.5 | $4,213,035 | 6,122 | — | UPTREND | -0.158 | 32.466 | FALLING_THROUGH_CANDIDATE | 0.3685 | POSITIVE_NET_GEX | 6 | 2.67% | 0.270 | CONTEXT_PARTIAL |
| AMZN | `AMZN260814P00272500` | 2026-08-14 / 2 | P / 272.5 | $4,098,952 | 3,391 | — | UPTREND | 0.725 | 18.551 | INCOMPLETE | 0.3270 | UNKNOWN | — | 6.45% | 0.503 | CONTEXT_PARTIAL |
| AAPL | `AAPL260812P00307500` | 2026-08-12 / 0 | P / 307.5 | $3,515,258 | 4,635 | 78.435 | MIXED | 0.270 | 37.374 | INCOMPLETE | — | UNKNOWN | — | 10.69% | 0.629 | CONTEXT_LIMITED |
| GOOGL | `GOOGL260812P00347500` | 2026-08-12 / 0 | P / 347.5 | $3,197,370 | 5,354 | — | DOWNTREND | 0.094 | 16.925 | INCOMPLETE | — | UNKNOWN | — | 28.57% | 0.128 | CONTEXT_LIMITED |
| AAPL | `AAPL260814C00310000` | 2026-08-14 / 2 | C / 310.0 | $3,073,137 | 3,270 | — | MIXED | 0.534 | 37.374 | INCOMPLETE | 0.2599 | UNKNOWN | — | 6.06% | 0.257 | CONTEXT_PARTIAL |
| AMZN | `AMZN260812C00275000` | 2026-08-12 / 0 | C / 275.0 | $3,052,401 | 2,990 | — | UPTREND | 0.976 | 18.551 | INCOMPLETE | — | UNKNOWN | — | 3.64% | 0.289 | CONTEXT_LIMITED |
| AAPL | `AAPL260812C00310000` | 2026-08-12 / 0 | C / 310.0 | $2,829,126 | 6,698 | 50.098 | MIXED | 0.534 | 37.374 | INCOMPLETE | — | UNKNOWN | — | 8.70% | 0.124 | CONTEXT_LIMITED |
| TSLA | `TSLA260814C00350000` | 2026-08-14 / 2 | C / 350.0 | $2,768,499 | 4,831 | — | DOWNTREND | 0.773 | 1.091 | INCOMPLETE | 0.4057 | UNKNOWN | — | 3.11% | 0.128 | CONTEXT_PARTIAL |
| AMZN | `AMZN260814C00272500` | 2026-08-14 / 2 | C / 272.5 | $2,646,164 | 3,486 | — | UPTREND | 0.725 | 18.551 | INCOMPLETE | 0.3270 | UNKNOWN | — | 3.95% | 0.498 | CONTEXT_PARTIAL |
| GOOGL | `GOOGL260812C00350000` | 2026-08-12 / 0 | C / 350.0 | $2,436,508 | 4,146 | — | DOWNTREND | 0.304 | 16.925 | INCOMPLETE | — | UNKNOWN | — | 7.95% | 0.736 | CONTEXT_LIMITED |
| GOOGL | `GOOGL260812C00352500` | 2026-08-12 / 0 | C / 352.5 | $2,284,756 | 5,588 | — | DOWNTREND | 0.513 | 16.925 | INCOMPLETE | — | UNKNOWN | — | 14.90% | 0.655 | CONTEXT_LIMITED |
| GOOGL | `GOOGL260812C00355000` | 2026-08-12 / 0 | C / 355.0 | $2,214,046 | 4,189 | — | DOWNTREND | 0.723 | 16.925 | INCOMPLETE | — | UNKNOWN | — | 7.41% | 0.564 | CONTEXT_LIMITED |
| AMZN | `AMZN261016C00310000` | 2026-10-16 / 65 | C / 310.0 | $1,596,923 | 2,559 | — | UPTREND | 4.500 | 18.551 | LOCAL_TROUGH | 0.3006 | UNKNOWN | — | 5.88% | 0.187 | CONTEXT_PARTIAL |
| GOOGL | `GOOGL260814C00357500` | 2026-08-14 / 2 | C / 357.5 | $1,480,387 | 15,657 | — | DOWNTREND | 0.932 | 16.925 | INCOMPLETE | 0.3143 | UNKNOWN | — | 5.13% | 0.478 | CONTEXT_PARTIAL |
| AMZN | `AMZN260812C00277500` | 2026-08-12 / 0 | C / 277.5 | $1,450,543 | 4,539 | — | UPTREND | 1.228 | 18.551 | INCOMPLETE | — | UNKNOWN | — | 8.22% | 0.147 | CONTEXT_LIMITED |
| TSLA | `TSLA260812C00345000` | 2026-08-12 / 0 | C / 345.0 | $1,301,640 | 2,708 | 36.776 | DOWNTREND | 0.318 | 1.091 | INCOMPLETE | — | UNKNOWN | — | 4.26% | 0.067 | CONTEXT_LIMITED |
| AAPL | `AAPL260814C00312500` | 2026-08-14 / 2 | C / 312.5 | $1,023,273 | 2,629 | — | MIXED | 0.799 | 37.374 | INCOMPLETE | 0.2599 | UNKNOWN | — | 10.71% | 0.160 | CONTEXT_PARTIAL |
| GOOGL | `GOOGL260812P00340000` | 2026-08-12 / 0 | P / 340.0 | $743,424 | 5,362 | — | DOWNTREND | -0.535 | 16.925 | INCOMPLETE | — | UNKNOWN | — | 18.18% | 0.031 | CONTEXT_LIMITED |
| AAPL | `AAPL260812C00312500` | 2026-08-12 / 0 | C / 312.5 | $685,752 | 2,685 | 40.815 | MIXED | 0.799 | 37.374 | INCOMPLETE | — | UNKNOWN | — | 13.33% | 0.043 | CONTEXT_LIMITED |
| GOOGL | `GOOGL260812C00360000` | 2026-08-12 / 0 | C / 360.0 | $538,432 | 2,816 | — | DOWNTREND | 1.142 | 16.925 | INCOMPLETE | — | UNKNOWN | — | 3.09% | 0.359 | CONTEXT_LIMITED |
| AAPL | `AAPL260814P00295000` | 2026-08-14 / 2 | P / 295.0 | $245,777 | 4,297 | — | MIXED | -1.053 | 37.374 | INCOMPLETE | 0.2599 | UNKNOWN | — | 8.22% | 0.092 | CONTEXT_PARTIAL |
| AMZN | `AMZN260814P00262500` | 2026-08-14 / 2 | P / 262.5 | $202,211 | 3,578 | — | UPTREND | -0.282 | 18.551 | INCOMPLETE | 0.3270 | UNKNOWN | — | 25.00% | 0.103 | CONTEXT_PARTIAL |

All rows have trigger `RADAR_EVENT`, material-event status yes, persistence unavailable, and
history confidence `INSUFFICIENT`; those invariant columns are stated once instead of repeated.

## Threshold Review

| Future state/quantity | Classification | Reason |
| --- | --- | --- |
| Existing Price Trend | THRESHOLD_FREE — IMPLEMENTABLE | Already accepted, descriptive, and complete in this sample. |
| Local Term IV topology | THRESHOLD_FREE — IMPLEMENTABLE | Pure ordering with deterministic floating tolerance and explicit INCOMPLETE. |
| Exact GEX sign | THRESHOLD_FREE — IMPLEMENTABLE | Describes only the sign of an exact returned cell. |
| Raw vendor row rank | THRESHOLD_FREE — IMPLEMENTABLE | Vendor-supplied ordinal; retain quality/provenance. |
| Trigger-source/evidence-family breadth | THRESHOLD_FREE — IMPLEMENTABLE | Counts independent families, not fields within Radar. |
| Context availability/readiness | THRESHOLD_FREE — IMPLEMENTABLE | Checklist coverage only; version its layer requirements. |
| Near/moderate/far strike | REQUIRES_CONFIGURED_THRESHOLD | The observed ATR distribution does not define financial cutoffs. |
| Low/mid/high IV Rank | REQUIRES_CONFIGURED_THRESHOLD | Only six tickers and no observations above 40. |
| Material local IV elevation/depression | REQUIRES_CONFIGURED_THRESHOLD | Topology and magnitude are distinct; magnitude varies widely. |
| Dominant GEX magnitude/concentration | REQUIRES_CONFIGURED_THRESHOLD | Cross-ticker USD is not comparable and only degraded NVDA ratios exist. |
| New tight/wide spread state | REQUIRES_CONFIGURED_THRESHOLD | Reuse accepted Phase 2A treatment; do not duplicate ad hoc cutoffs. |
| Bullish/bearish or trade-direction confirmation | NOT_READY | Economic intent is unavailable. |
| Support/resistance, call wall, put wall, gamma flip | NOT_READY | Runtime semantics/completeness do not establish these labels. |
| Rich/cheap IV | NOT_READY | No accepted IV-vs-RV basis or calibrated thresholds. |
| Predictive/profitable setup pattern | NOT_READY | No forward-return or outcome evidence was used. |

## Conditional Thesis Feasibility

A future user-specified thesis such as `LONG_CALL_THESIS`, `SHORT_CALL_THESIS`,
`LONG_PUT_THESIS`, or `SHORT_PUT_THESIS` is safer than guessing direction from Radar. The thesis
would be explicit user input with its own provenance; Price/IV/GEX could then be described as
supporting, conflicting, or unknown **conditional on that supplied thesis**.

This should be deferred until the thesis vocabulary, evidence mappings, missing-data behavior, and
configuration versioning are reviewed. Absence of a thesis must remain `THESIS_UNSPECIFIED`, and
the scanner's observed direction must remain `UNRESOLVED`. Conditional evaluation must never be
written back as inferred Radar intent.

## Recommended Phase 2B v2 Production Model

No production implementation is made by this gate. Recommended smallest model:

| Dimension | Proposed states/context | Recommendation |
| --- | --- | --- |
| A. Positioning | trigger families; persistence/structure/cluster presence; SINGLE/MULTI_EVIDENCE | IMPLEMENT NOW as factual provenance/breadth; retain existing accepted numeric scores separately. |
| B. Price | existing Trend; signed strike distance % and ATR | IMPLEMENT NOW for Trend; REMAIN RAW NUMERIC CONTEXT for distance; DEFER Near/Far labels. |
| C. Volatility | local topology + INCOMPLETE; raw IV Rank and signed neighbour differences | IMPLEMENT NOW for topology; REMAIN RAW NUMERIC CONTEXT for IV Rank/magnitude; DEFER LOW/HIGH and materiality. |
| D. Dealer/GEX | exact-cell sign/UNKNOWN; quality; raw cell/row values and vendor rank | IMPLEMENT NOW for exact sign and quality; REMAIN RAW NUMERIC CONTEXT for rank/values; DEFER normalization states. |
| E. Execution | existing Phase 2A liquidity treatment; bid/ask/mid/spread and Greeks | IMPLEMENT NOW by reuse; REMAIN RAW NUMERIC CONTEXT for Greeks; no duplicate score. |
| F. Data readiness | COMPLETE/PARTIAL/LIMITED plus explicit layer checklist | IMPLEMENT NOW as non-alpha coverage, with versioned requirements. |
| Direction | UNRESOLVED | KEEP unchanged. |

The UI should present these as independent rows, not concatenate them into a single “setup quality”
or color-coded directional verdict.

## NVDA Example — `NVDA260821C00220000`

```text
WHY FOUND
  RADAR_EVENT
  Material Event: YES
  Premium: $10,434,044
  ΔOI: +4,531
  Relative OI Change: 0.07211294 (~7.21%)

POSITIONING
  Evidence Breadth: MULTI_EVIDENCE
  Structure Score: 70.722
  Contract Persistence: NOT_YET_AVAILABLE
  Expiry Persistence: NOT_YET_AVAILABLE
  Exact Cluster Membership: ABSENT
  History Confidence: INSUFFICIENT

PRICE
  Current Stock State: 223.7347, PREMARKET, 2026-08-13T09:25:04Z
  Latest Regular Close: 224.09, trading date 2026-08-12
  Trend: UPTREND
  Strike Distance: -1.6693%; -0.4767 ATR
  Price Quality: AVAILABLE_WITH_GAPS

VOLATILITY
  IV Rank: 32.4659 (raw; no LOW/MID/HIGH label)
  Candidate Term IV: 0.33103896
  Local Shape: LOCAL_PEAK
  Candidate − shorter: +0.01164760
  Candidate − longer: +0.01943284
  Candidate − neighbour mean: +0.01554022

DEALER / GEX
  Exact Cell: YES, but Heatmap is DEGRADED
  Net / Call / Put GEX: 59,652,544 / 59,166,863 / 485,681
  Sign: POSITIVE_NET_GEX
  Candidate Row Net / Abs: 81,553,764 / 121,659,202
  Vendor Row Rank: 1
  abs(cell net) / row abs: 0.4903 (diagnostic only)
  Row abs / top-row abs: 1.0000 (diagnostic only)

EXECUTION
  Bid / Ask / Mid: 3.85 / 3.95 / 3.90
  Spread: $0.10; 2.5641%
  Delta / Gamma: 0.4787 / 0.0369
  Theta / Vega / Charm: -0.2247 / 14.4368 / -1.0396

DATA QUALITY
  CONTEXT_PARTIAL
  Limitation: exact Dealer evidence exists but vendor Heatmap state is degraded

DIRECTION
  UNRESOLVED
```

Nothing in this representation establishes whether the Call was bought, written, part of a spread,
or a hedge. `UPTREND`, `LOCAL_PEAK`, and `POSITIVE_NET_GEX` are independent context facts.

## Nightwatch Call Ledger

Pre-gate quota remaining: 99,839 of 100,000. Post-gate: 99,815. Paid-unit delta: 24.

The first normal production CLI attempt completed the five TSLA context requests, then hit an
existing null-shape bug while evaluating the candidate because unavailable Heatmap data was stored
with `cells = null`. Its transaction—including usage audit—rolled back. The four successful paid
TSLA calls reduced quota by four; the Heatmap request was non-paid and its HTTP 400 result was
immediately reproduced by the diagnostic harness. No partial candidate evaluation persisted.

The temporary harness then fetched one context set for each missing ticker AAPL, AMZN, GOOGL,
META, and TSLA and committed after each ticker. NVDA was not called; its accepted persisted v1.1
context was reused.

| Endpoint | Ticker calls | HTTP result | Paid units |
| --- | ---: | --- | ---: |
| `/v1/stocks/ohlc/{ticker}?candle_size=1d` | 6 | 200 × 6 | 6 |
| `/v1/stocks/stock-state/{ticker}` | 6 | 200 × 6 | 6 |
| `/v1/volatility/iv-rank/{ticker}` | 6 | 200 × 6 | 6 |
| `/v1/volatility/term-structure/{ticker}` | 6 | 200 × 6 | 6 |
| `/v1/derived/heatmap/{ticker}/snapshot?format=full` | 6 | 400 × 6 | 0 |
| **Total** | **30 attempts** | **24 × 200; 6 × 400** | **24** |

Ticker call counts are AAPL 5, AMZN 5, GOOGL 5, META 5, TSLA 10 (the rolled-back initial set plus
the persisted diagnostic set), and NVDA 0. Retry count is 0. Concurrency is 1. No other Nightwatch
endpoint was contacted.

## Open Issues

1. Dealer Heatmap `format=full` returned HTTP 400 `VALIDATION_ERROR` for five tickers. The existing
   production evaluation also assumes iterable `cells`/`row_stacks` and raises `TypeError` when an
   unavailable context stores them as null. This gate documents but does not fix that production
   issue.
2. The only exact GEX sample is 11 cells from one degraded NVDA surface; GEX magnitude or
   normalization calibration is not ready.
3. Only 12/46 candidates have complete three-node Term topology, and IV Rank has only six ticker
   observations concentrated below 40.
4. Accepted persistence evidence is absent and all candidate histories are insufficient, so
   positioning confirmation breadth is structurally limited.
5. Candidate/context timestamps are not synchronous and several contracts are already expired.
6. No outcome data or forward return was used; predictive claims and threshold optimization remain
   unsupported.

Phase 2B v2 production logic and Phase 2B v3 were not started.

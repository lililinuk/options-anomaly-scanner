# Signal Specification: Phase 2B v1 Confirmation Context

Immutable identifier: `signal_spec_v1.0_phase2b`

Accepted Phase 2A dependency: `signal_spec_v1.3_phase2a`

## Boundary

Phase 2B describes the environment surrounding an already-selected Phase 2A Deep Dive
candidate. It does not alter discovery, eligibility, thresholds, scores, archive data, or
historical Phase 2A observations. It produces no Confirmation, Conviction, Tradeability,
BUY/SELL, or bullish/bearish score. Every v1 candidate has `direction=UNRESOLVED`.

## Acquisition and immutability

Only tickers with selected candidates may be fetched. One ticker snapshot is shared by all
candidate contracts for that ticker. The maximum fresh request set is daily OHLC, Stock State,
IV Rank, Term Structure, and multi-expiry Dealer Heatmap. Phase 2A chain evidence is reused.

Freshness rules and the at-spot tolerance are supplied by versioned server configuration. Each
ticker snapshot and candidate evaluation stores the specification version, configuration
version/hash, effective configuration, source timestamps, and raw evidence references. A refresh
appends a new snapshot; it does not update an earlier evaluation.

## Daily price context

The canonical series is valid only when every returned `trading_date` has exactly one
`session=regular` row. A duplicate or missing regular row makes the policy
`DAILY_SESSION_POLICY_UNRESOLVED`; price-history metrics remain null. Raw evidence is preserved.
OHLC split adjustment is always labelled `UNCONFIRMED` in v1.

Given canonical closes `C[t]`:

- `return_Nd = C[t] / C[t-N] - 1`, for N=1, 5, 20.
- `SMA_N = arithmetic mean of the last N closes`, for N=20, 50.
- `distance_to_smaN_pct = C[t] / SMA_N - 1`.
- rolling high/low are the maximum high/minimum low over the last 20 sessions.
- true range is `max(high-low, abs(high-previous_close), abs(low-previous_close))`.
- `ATR14` is the arithmetic mean of the latest 14 true ranges and requires 15 rows.

Missing history yields null; no rescaling occurs. Trend is `UPTREND` when
`price > SMA20 > SMA50`, `DOWNTREND` when `price < SMA20 < SMA50`, otherwise `MIXED`.
If either moving average is unavailable, trend is `UNKNOWN`. This is descriptive, not predictive.

Stock State is separate from historical chain spot. `session_change_pct = current/previous-1`
when both inputs exist. For contract strike `K` and current stock-state price `S`:

- `strike_distance_usd = K-S`
- `strike_distance_pct = K/S-1`
- `strike_distance_atr = (K-S)/ATR14`, when ATR14 exists.

`AT_SPOT_APPROX` uses the persisted configurable absolute percentage tolerance; otherwise the
state is `ABOVE_SPOT` or `BELOW_SPOT`. None has directional meaning.

## Volatility context

Vendor one-year IV Rank is exposed as its raw numeric value with vendor date/as-of; no LOW/MID/
HIGH state is created. Contract IV remains distinct.

Raw term nodes are preserved. Candidate matching requires exact expiration equality. The nearest
shorter and longer DTE nodes are selected deterministically, and raw IV differences are exposed.
No interpolation or curve classification occurs. Contract IV minus expiry-node IV is labelled
`CONTRACT_IV_VS_EXPIRY_NODE_CONTEXT`; the measures are not asserted to be conceptually identical.
Vendor implied move is magnitude context only.

## Dealer/GEX context

The sole primary candidate-level source is multi-expiry Dealer Heatmap. Quality is:

- `INCOMPLETE_OR_TRUNCATED` when truncation is true;
- `AVAILABLE_DEGRADED` when vendor state is degraded;
- `AVAILABLE` for other returned evidence;
- `UNAVAILABLE` without data.

An exact candidate cell requires both expiration and numeric strike equality in one returned
cell. Missing sparse cells remain null and have status `NOT_PRESENT`; axis membership is
insufficient. Candidate strike row-stack evidence is separately labelled ticker-wide/multi-expiry.
Top five rows use vendor rank. Nearest positive/negative rows use only returned row-net values.
They are not support/resistance. No complete-surface concentration is calculated in v1.

## Reused Phase 2A context

Bid, ask, midpoint, spread, IV, delta, gamma, theta, vega, charm, OI, strike, expiration, right,
historical spot, archive state, Radar evidence/config, positioning structure/persistence, expiry
persistence/activity, and clusters come from persisted Phase 2A evidence. Phase 2B never
recalculates Phase 2A eligibility.

## Availability and deferred scope

Sections explicitly distinguish `AVAILABLE`, `PARTIAL`, `UNAVAILABLE`,
`INSUFFICIENT_HISTORY`, and `DEGRADED`; null never renders as zero. Endpoint failure cannot erase
the underlying candidate.

Deferred from production v1: IV-vs-RV states, risk-reversal interpretation, Event Risk, Standard
GEX candidate interpretation, and 0DTE Dealer GEX. These fields remain unavailable/research-only.

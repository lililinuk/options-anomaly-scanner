# Phase 2B v1.1 — Valid Regular-Session Price Series

Specification identifier: `signal_spec_v1.1_phase2b`

Status: accepted implementation amendment. This document is additive and does not rewrite
`signal_spec_v1.0_phase2b` or any persisted v1.0 evidence.

## Scope

This amendment changes only Phase 2B Price Context normalization and calculations. Phase 2A,
Radar, positioning, expiry activity, volatility, Dealer/GEX, liquidity, Greeks, and direction
semantics are unchanged. Direction remains `UNRESOLVED`.

## Canonical session policy

The versioned policy identifier is `VALID_REGULAR_SESSION_OBSERVATIONS`.

For each `trading_date`:

- exactly one row whose `session` is `regular` becomes a valid observation;
- no regular row becomes `MISSING_REGULAR_OBSERVATION` and is excluded;
- more than one regular row becomes `AMBIGUOUS_REGULAR_OBSERVATION` and is excluded.

Premarket and postmarket rows are never substitutes. Valid observations are ordered by trading
date. A missing or ambiguous date does not invalidate surrounding observations.

Persisted context includes raw bar count, distinct trading-date count, valid count, missing and
ambiguous counts and dates, oldest/latest valid regular date, policy, coverage quality, and the
effective calculation basis. `VALID_WITH_GAPS` means the complete configured feature set can be
calculated despite excluded dates. `COMPLETE_FOR_WINDOW` requires enough observations and no
excluded dates. Feature availability remains independent of the overall state.

## Versioned windows and formulas

The effective config snapshot and hash contain return windows `[1, 5, 20]`, SMA windows
`[20, 50]`, ATR window `14`, and rolling range window `20`.

Let `C0` be the latest valid regular-session close. A return for window `N` requires `N + 1`
valid observations and is:

`return_N = C0 / close_N_valid_observations_back - 1`

SMA20 and SMA50 are arithmetic means of the latest 20 and 50 valid closes. The rolling high and
low are the extrema of regular-session high/low values across the latest 20 valid observations.

For sequential valid observations:

`TR_t = max(high_t - low_t, abs(high_t - close_(t-1)), abs(low_t - close_(t-1)))`

ATR14 is the arithmetic mean of the latest 14 True Range observations and therefore requires 15
valid price observations. It is not Wilder smoothing.

Distance to SMA uses the latest valid regular close. Trend is `UPTREND` when
`latest close > SMA20 > SMA50`, `DOWNTREND` when `latest close < SMA20 < SMA50`, `MIXED` for
other complete combinations, and `UNKNOWN` if inputs are absent.

## Current versus historical price

Stock State is an independently timestamped current observation and is never inserted into the
historical daily series. Strike distance uses current Stock State:

- `strike_distance_usd = strike - current_price`
- `strike_distance_pct = strike / current_price - 1`
- `strike_distance_atr = (strike - current_price) / ATR14`, when both inputs exist.

The existing versioned `AT_SPOT_APPROX` tolerance remains unchanged.

## Null and adjustment semantics

Each metric is `NULL` only when its own required observations or values are absent. One absent
feature cannot null unrelated features. OHLC split-adjustment semantics remain `UNCONFIRMED`;
calculations remain available with this limitation explicitly disclosed.

## Evidence immutability

v1.1 appends a new ticker context and candidate evaluation with the v1.1 specification/config
identity. It may deterministically renormalize an already preserved raw OHLC payload, without a
new vendor request. Existing v1.0 rows are never updated or deleted.

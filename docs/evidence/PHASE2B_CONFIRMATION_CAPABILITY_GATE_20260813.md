# Phase 2B Confirmation Data Capability Validation Gate

Date: 2026-08-13  
Starting Git SHA: `f859ef7359325a7127bc4f7db12e037141ced7a7`  
Accepted Phase 2A specification: `signal_spec_v1.3_phase2a`

## Scope and outcome

This was a runtime capability validation only. No Phase 2B confirmation layer,
financial score, threshold, directional inference, production dashboard behavior,
database schema, migration, Phase 2A calculation, scan, or Daily Archive behavior was
changed.

The smallest evidence-based Phase 2B v1 is:

- transparent underlying price context, subject to an explicit daily-session policy;
- vendor IV Rank as an independent, unscored fact;
- raw expiry term-structure nodes, including an exact candidate-expiry node;
- multi-expiry Dealer Heatmap as the primary GEX source, while retaining its degraded-state
  and completeness caveats;
- existing Phase 2A liquidity, Greeks, archive, Radar, and positioning evidence without
  refetching it.

RV-vs-IV classification, skew interpretation, event risk, and 0DTE dealer structure should
be deferred. Direction remains `UNRESOLVED`.

## Safety controls

- Ticker: NVDA only.
- Candidate: `NVDA260821C00220000`.
- Existing server-side `NightwatchClient` used for every authenticated probe.
- Concurrency: 1.
- Retries: 0.
- No polling of 202 materializations.
- No MAG7 scan and no Daily Archive run.
- No browser-to-Nightwatch request.
- No API key, Authorization header, database credential, or secret was printed or stored.
- A temporary local diagnostic harness was removed after the probes. Only this report is
  retained.

## Existing persisted candidate authority

The database, rather than the approximate values in the task description, supplied the
candidate facts below.

| Evidence | Exact persisted value |
|---|---:|
| Radar date | 2026-08-12 |
| Premium | USD 10,434,044.0000 |
| OI Diff | +4,531 |
| OI Change | 0.07211294 |
| Volume | 24,458 |
| Trades | 2,887 |
| Deep-dive scope | `FULL_DEEP_DIVE_ELIGIBLE` |
| Effective threshold profile | `2026-08-13.v1` |
| Chain vendor date | 2026-08-11 |
| Expiration / right / strike | 2026-08-21 / C / 220.000000 |
| OI | 62,832 |
| Bid / ask | 3.850000 / 3.950000 |
| IV | 0.29730000 |
| Delta / gamma | 0.47870000 / 0.0369000000 |
| Theta / vega / charm | -0.22470000 / 14.43680000 / -1.03960000 |
| Underlying spot | 218.940000 |
| Quote and Greeks as-of | 2026-08-11T20:00:00.657Z |
| Underlying as-of | 2026-08-12T08:31:09.787Z |
| Archive status | `COMPLETE` |
| Contract Positioning Structure score | 70.722 |
| Contract/expiry Persistent Positioning | not present for this candidate |
| History state | `INSUFFICIENT` |

No additional Nightwatch request is needed for bid, ask, IV, delta, gamma, theta, vega,
charm, spot, OI, strike, expiration, right, archive completeness, Radar evidence, or the
existing positioning structures.

## Discovery and runtime capability table

`/v1/discover` reported 94 of 94 capabilities available. The OpenAPI document identified
itself as `GEX Heatmap Data API`, version `0.2.0-dealer-mvp-registry`.

| Purpose | Discover capability | Runtime path | Availability | Runtime result |
|---|---|---|---|---|
| Daily/hourly OHLC | `stocks.ohlc` | `/v1/stocks/ohlc/{ticker}` | available, on-demand, weight 1 | 200 |
| Latest stock state | `stocks.stock_state` | `/v1/stocks/stock-state/{ticker}` | available, on-demand, weight 1 | 200 |
| IV Rank | `volatility.iv_rank` | `/v1/volatility/iv-rank/{ticker}` | available, on-demand, weight 1 | 200 |
| IV term structure | `volatility.term_structure` | `/v1/volatility/term-structure/{ticker}` | available, on-demand, weight 1 | 200 |
| Realized vs implied series | `volatility.realized` | `/v1/volatility/realized/{ticker}` | available, on-demand, weight 1 | 200 |
| Volatility stats | `volatility.stats` | `/v1/volatility/stats/{ticker}` | available, on-demand, weight 1 | 200 |
| 25-delta risk reversal | `volatility.risk_reversal_skew` | `/v1/volatility/risk-reversal-skew/{ticker}` | available, on-demand, weight 1 | 200 |
| Multi-expiry Dealer Heatmap | `derived.dealer_heatmap_snapshot` | `/v1/derived/heatmap/{ticker}/snapshot` | available, working-set, weight 1 | 200 |
| Standard GEX history | `derived.standard_gex_history` | `/v1/derived/standard-gex/{ticker}/history` | available, working-set, weight 1 | 200 |
| 0DTE Dealer GEX | `derived.dealer_gex_snapshot` | `/v1/derived/dealer-gex/{ticker}/snapshot` | available, working-set, weight 1 | 200 |

The OpenAPI candle-size enum is `1m`, `5m`, `10m`, `15m`, `30m`, `1h`, `4h`, `1d`, and
`1w`. None of the probed endpoints returned 202.

## Underlying Price Capability

### Daily OHLC

- Capability/path: `stocks.ohlc`, `GET /v1/stocks/ohlc/NVDA?candle_size=1d`.
- HTTP: 200.
- Returned data keys: `ticker`, `candle_size`, `as_of`, `total_bars`, `returned_bars`,
  `truncated`, and `bars`.
- Bar keys: `trading_date`, `bar_start`, `bar_end`, `session`, `open_usd`, `high_usd`,
  `low_usd`, `close_usd`, `volume_shares`, and `total_volume_shares`.
- Coverage observed: 756 total bars; newest 400 returned; response marked `truncated`.
- Returned range: 2026-01-30 through 2026-08-12.
- Latest response as-of: 2026-08-12T04:00:00.000Z.
- The representative first and last `1d` records both reported `session=postmarket`.
  Therefore `1d` must not automatically be treated as one regular-session close per trading
  date without an explicit session-selection/deduplication policy.
- Split-adjustment semantics were not present in the OpenAPI operation or runtime payload.
  They remain unconfirmed.
- Practical history: the returned 400 bars are enough for 50-session calculations after a
  validated session policy. The endpoint reported a larger 756-bar source set, but no range
  or pagination parameter was exposed for this operation.
- Quota: 1 paid unit.

### Hourly OHLC

- Request: `GET /v1/stocks/ohlc/NVDA?candle_size=1h`.
- HTTP: 200.
- Coverage observed: 2,500 total bars; newest 400 returned; response marked `truncated`.
- Returned range: 2026-07-09T08:00:00Z through 2026-08-13T00:00:00Z.
- Bar fields match daily OHLC; `bar_start` and `bar_end` are explicit UTC timestamps and
  `session` identifies premarket/regular/postmarket context.
- The 400 returned hourly bars are usable for near-term 1h structure. A 4h series is also a
  documented candle size, but was not separately called because the 1h probe was sufficient
  to validate intraday schema and local 4h aggregation feasibility.
- Quota: 1 paid unit.

### Latest stock state

- Capability/path: `stocks.stock_state`, `GET /v1/stocks/stock-state/NVDA`.
- HTTP: 200.
- Exact returned keys: `ticker`, `open_usd`, `high_usd`, `low_usd`, `close_usd`,
  `prev_close_usd`, `volume_shares`, `total_volume_shares`, `session`, `as_of`.
- Observed values: close 224.05, previous close 224.09, premarket session,
  as-of 2026-08-13T08:39:16.000Z.
- No explicit `session_change` field was returned; it can be calculated transparently from
  close and previous close if later specified.
- It is materially fresher than the persisted option-chain spot (2026-08-12T08:31:09.787Z)
  and is therefore useful as a separately timestamped latest state. It must not overwrite the
  immutable chain-observation spot.
- Quota: 1 paid unit.

### Price feature feasibility

| Proposed feature | Classification | Evidence/condition |
|---|---|---|
| `return_1d` | FEASIBLE | close and trading date available; requires canonical daily-session selection |
| `return_5d` | FEASIBLE | sufficient returned history |
| `return_20d` | FEASIBLE | sufficient returned history |
| `sma_20` | FEASIBLE | sufficient close history |
| `sma_50` | FEASIBLE | sufficient close history |
| `distance_to_sma20_pct` | FEASIBLE | latest canonical close plus SMA20 |
| `distance_to_sma50_pct` | FEASIBLE | latest canonical close plus SMA50 |
| `rolling_high_20` | FEASIBLE | high and date available |
| `rolling_low_20` | FEASIBLE | low and date available |
| `atr_14` | FEASIBLE | high, low, close and prior close available |
| `strike_distance_pct` | FEASIBLE | persisted strike plus timestamped stock price |
| `strike_distance_atr` | FEASIBLE | persisted strike plus locally calculated ATR14 |

The proposed `UPTREND` / `DOWNTREND` / `MIXED` descriptive state is mathematically feasible
from these fields and is not predictive. It is not implementation-ready until Phase 2B
specifies which daily session is authoritative and how unconfirmed split adjustment is
handled.

**Price Context status: `PARTIALLY_READY`.** The history and fields are sufficient, but the
daily-session and split-adjustment semantics must be made explicit before production use.

## Volatility Context

### IV Rank

- Capability/path: `volatility.iv_rank`, `GET /v1/volatility/iv-rank/NVDA`.
- HTTP: 200; no 202.
- Schema: `ticker`, `date`, `iv_rank`, `as_of`.
- Runtime value: date 2026-08-12, IV Rank 32.4659,
  as-of 2026-08-12T18:35:19.966Z.
- OpenAPI describes a one-year 0-100 IV Rank. The precise underlying IV construction is not
  disclosed in the operation or payload.
- Missing-data behavior was not exercised and is therefore not inferred.
- Candidate-expiry mapping: none; it is ticker-level.
- Quota: 1 paid unit.
- Classification: `READY_FOR_PHASE2B_V1` as a raw vendor value. LOW/MID/HIGH thresholds
  remain a separate versioned configuration decision.

### Term Structure

- Capability/path: `volatility.term_structure`,
  `GET /v1/volatility/term-structure/NVDA`.
- HTTP: 200; no 202.
- Schema: `ticker`, `date`, `nodes`, `as_of`; each node has `expiry`, `dte`,
  `implied_vol_pct`, `implied_move_usd`, `implied_move_pct`.
- Runtime coverage: 23 nodes from expiry 2026-08-12 (DTE 0) through 2028-12-15
  (DTE 856); as-of 2026-08-12T04:00:00.000Z.
- Exact candidate node: expiry 2026-08-21, DTE 9, implied vol
  0.3310389567749655, implied move USD 7.85191163037332, implied move
  0.0352815461793696.
- No ATM definition and no contango/flat/backwardation/mixed vendor classification were
  returned. These must not be invented.
- Quota: 1 paid unit.
- Classification: `READY_FOR_PHASE2B_V1` for raw nodes and transparent neighbouring-expiry
  comparisons; categorical curve states require a later versioned specification.

### RV vs IV / volatility stats

Two non-redundant probes were necessary because the latest daily realized-series row did not
contain an RV value.

- `GET /v1/volatility/realized/NVDA`: HTTP 200, 251 rows from 2025-08-13 through
  2026-08-12. Row keys are `date`, `price_usd`, `implied_vol_pct`,
  `realized_vol_pct`, and `unshifted_rv_date`; response as-of
  2026-08-12T04:00:00.000Z. The latest row had IV 0.386 and null RV/null
  `unshifted_rv_date`; the oldest representative row showed IV 0.436, RV 0.275928,
  and `unshifted_rv_date=2025-09-11`.
- `GET /v1/volatility/stats/NVDA`: HTTP 200. Keys are `ticker`, `date`, `iv_pct`,
  `iv_low_pct`, `iv_high_pct`, `iv_rank`, `rv_pct`, `rv_low_pct`, `rv_high_pct`,
  `as_of`. Runtime snapshot: IV 0.386, IV low/high 0.313/0.551, IV Rank 32.4659,
  RV 0.391941, RV low/high 0.219718/0.471371, date/as-of
  2026-08-12 / 2026-08-12T04:00:00.000Z.
- A numeric IV-minus-RV difference is locally computable, but the runtime/OpenAPI evidence
  did not disclose the RV lookback or establish tenor equivalence between the IV and RV
  measures. No `iv_rv_spread` field was returned.
- Quota: 2 paid units total.
- Classification: `DEFER` for CHEAP/NEUTRAL/RICH Phase 2B states until lookback/tenor
  semantics and versioned state thresholds are defined. The raw snapshot may be retained as
  research evidence.

### 25-delta risk-reversal skew

- Capability/path: `volatility.risk_reversal_skew`,
  `GET /v1/volatility/risk-reversal-skew/NVDA`.
- HTTP: 200; no 202.
- Schema: `ticker`, `rows`, `as_of`; each row has `date`, `delta`, `risk_reversal`.
- Runtime coverage: 12 rows from 2026-07-28 through 2026-08-12, all representative rows
  at delta 25; latest `risk_reversal=-0.198188601295333`;
  as-of 2026-08-12T04:00:00.000Z.
- The response exposed neither call/put component IVs, expiration/tenor, nor sign convention.
  It therefore cannot safely say whether downside or upside protection was dearer.
- Quota: 1 paid unit.
- Classification: `DEFER` / `NOT_READY_FOR_PHASE2B_V1`.

No 0-100 volatility score was designed. `LOW/MID/HIGH`, curve-state, and
`CHEAP/NEUTRAL/RICH` thresholds were not selected.

## GEX / Dealer Structure

### Multi-expiry Dealer Heatmap

- Capability/path: `derived.dealer_heatmap_snapshot`,
  `GET /v1/derived/heatmap/NVDA/snapshot?format=full`.
- HTTP: 200; no 202.
- Top-level data keys: `ticker`, `generated_at`, `session_date_et`, `market_status`,
  `state`, `spot_usd`, `expirations`, `strikes_usd`, `cells`, `row_stacks`, `scale`.
- Cell keys: `strike_usd`, `expiration`, `net_dealer_gex_usd`, `call_gex_usd`,
  `put_gex_usd`.
- Row-stack keys: `strike_usd`, `row_net_wall_gex_usd`, `row_abs_wall_gex_usd`, `rank`.
- Units are explicitly USD in field names.
- Runtime snapshot: generated 2026-08-13T08:44:38.98124378Z,
  session date ET 2026-08-13, market closed, `state=degraded`, spot 224.09.
- Coverage: 11 expiration-axis values from 2026-08-14 through 2026-10-16;
  101 strike-axis values from 45 through 400; 771 cells; 101 row stacks.
- Candidate expiry 2026-08-21 is explicitly present in the expiration axis and candidate
  strike 220 is explicitly present in the strike axis. The 220 row stack was rank 1 with
  `row_net_wall_gex_usd=82,544,535` and `row_abs_wall_gex_usd=122,784,681`.
- The safe diagnostic summary did not retain the exact 2026-08-21-by-220 joint cell, and the
  771 cells do not form a complete 11-by-101 Cartesian matrix. Axis membership must not be
  upgraded to a claim that the joint cell exists until checked from preserved evidence in a
  future implementation run.
- The response included a `_meta.truncated` field, but its value was not retained in the safe
  summary. Together with `state=degraded`, completeness is not established.
- The response does not directly name support, resistance, gamma flip, Call Wall, or Put
  Wall. Row ranks and GEX values objectively permit transparent magnitude/distance
  calculations after completeness and node-selection rules are specified; they do not
  establish directional intent.
- Quota: 1 paid unit.

Feasibility from verified schema:

| Proposed quantity | Result |
|---|---|
| Candidate strike GEX | PARTIALLY FEASIBLE — strike axis exists; candidate joint cell was not retained |
| Nearest major positive/negative node | FEASIBLE after a versioned, transparent “major” selection rule |
| Distance from spot | FEASIBLE; spot and strike are present |
| Distance from candidate strike | FEASIBLE; candidate strike is persisted |
| Local GEX concentration | PARTIALLY FEASIBLE; formula and completeness handling must be specified |
| Candidate-expiration GEX structure | PARTIALLY FEASIBLE; expiry exists, but degraded/sparse completeness must be handled |

### Standard GEX

- Capability/path: `derived.standard_gex_history`,
  `GET /v1/derived/standard-gex/NVDA/history?limit=10`.
- HTTP: 200; no 202.
- Response: an array of 10 records; record keys are `snapshot_at`, `ticker`,
  `market_status`, `is_stale`, `total_gex_usd`, `spot_usd`.
- Observed time range: 2026-08-12T19:49:05.891Z through
  2026-08-12T20:00:03.783Z, newest first.
- It is ticker-wide history. It returned no expiration, strike, call GEX, put GEX, or
  candidate mapping.
- Units: USD.
- Quota: 1 paid unit.
- Usefulness: useful for time-series context of ticker-total GEX, but not for candidate strike
  or expiration confirmation.

### 0DTE Dealer GEX

- Capability/path: `derived.dealer_gex_snapshot`,
  `GET /v1/derived/dealer-gex/NVDA/snapshot?format=full`.
- HTTP: 200; no 202.
- Schema: `ticker`, `snapshot_at`, `session_date_et`, `state`, `spot_usd`, `strikes`,
  `summary`. Strike keys are `strike_usd`, `net_gex_usd`, `call_gex_usd`,
  `put_gex_usd`, `node_type`.
- Runtime coverage: 13 strikes from 207.5 through 260; snapshot
  2026-08-12T20:00:00.166Z; market-closed state; spot 224.14.
- The vendor summary directly returned total GEX, king/gatekeeper strikes and values,
  gamma flip, call/put walls, major positive/negative strikes and values, and positive/
  negative counts. These are vendor fields, not locally invented classifications.
- Quota: 1 paid unit.
- Scope limitation: this capability is 0DTE/dealer-active and returned no expiration field.
  It is not applicable to the 2026-08-21 candidate and must only be considered when the
  Deep Dive candidate itself is 0DTE.

**Recommendation: `DEALER_HEATMAP_PRIMARY`.** It is the only verified source with both
multi-expiry and strike dimensions relevant to the candidate. Standard GEX may remain a
separate ticker-total time-series context; it must not be blended as if it were the same
quantity. 0DTE Dealer GEX is candidate-inapplicable here.

## Event Risk

Discovery/OpenAPI exposed the following relevant names:

- `fundamentals.earnings_afterhours`: latest reporting session, market-wide;
- `fundamentals.earnings_premarket`: latest reporting session, market-wide;
- `fundamentals.earnings_estimates`: analyst estimates, on-demand;
- `fundamentals.earnings_history`: historical;
- `fundamentals.stock_earnings`: earnings-event price/straddle behavior, on-demand.

The reporting-session calendars are not demonstrated to be forward-looking, and the other
descriptions do not establish an authoritative upcoming per-ticker event date with BMO/AMC
timing and horizon. No event endpoint was called.

`EVENT_RISK_RUNTIME_CAPABILITY = NOT_CONFIRMED`

This does not block the other Phase 2B layers.

## Existing Phase 2A data reusable without new calls

| Existing input | Reuse status |
|---|---|
| Bid / ask and spread inputs | reuse persisted chain evidence |
| IV and delta | reuse persisted chain evidence |
| Gamma, theta, vega, charm | reuse persisted chain evidence |
| Spot at chain observation | reuse immutably with its own as-of |
| OI, strike, expiration, right | reuse persisted normalized contract |
| Contract Positioning Structure | reuse existing derived state |
| Contract Persistent Positioning | reuse when present; candidate currently has none |
| Expiry Persistent Positioning | reuse when present; candidate currently has none |
| Call/Put cluster information | reuse when present; candidate expiry currently has none |
| Archive completeness | reuse `COMPLETE` state |
| Radar evidence and effective threshold profile | reuse immutable evaluated event/run evidence |

Fresh stock-state spot must be stored/displayed separately from the historical chain spot;
it must not rewrite detection history.

## Exact Nightwatch call ledger and quota

External host contacted: `https://api.yehangshe.com`. No other external host was contacted.

| # | Method/path and safe parameters | HTTP | Attempts | Retries | Remaining after | Request ID |
|---:|---|---:|---:|---:|---:|---|
| 1 | `GET /v1/discover` | 200 | 1 | 0 | body reported 99,854 | `req_3ef3281fb005867a7da9aa3d` |
| 2 | `GET /v1/openapi.json` | 200 | 1 | 0 | zero-quota; no header retained | not retained by typed OpenAPI helper |
| 3 | `GET /v1/stocks/ohlc/NVDA?candle_size=1d` | 200 | 1 | 0 | 99,854 | `req_7553221b72b64169781a589b` |
| 4 | `GET /v1/stocks/ohlc/NVDA?candle_size=1h` | 200 | 1 | 0 | 99,853 | `req_bb280cc33c9d2a79bb86176e` |
| 5 | `GET /v1/stocks/stock-state/NVDA` | 200 | 1 | 0 | 99,852 | `req_6297aad316a29e9eb426b7ca` |
| 6 | `GET /v1/volatility/iv-rank/NVDA` | 200 | 1 | 0 | 99,851 | `req_661e8e172015a6d201a125b6` |
| 7 | `GET /v1/volatility/term-structure/NVDA` | 200 | 1 | 0 | 99,850 | `req_66e1fbb2e1598e8671ec1c52` |
| 8 | `GET /v1/volatility/realized/NVDA` | 200 | 1 | 0 | 99,849 | `req_3fc91c7be06a3dc8ba07864e` |
| 9 | `GET /v1/volatility/stats/NVDA` | 200 | 1 | 0 | 99,848 | `req_9d64f47a325a4f5305715636` |
| 10 | `GET /v1/volatility/risk-reversal-skew/NVDA` | 200 | 1 | 0 | 99,847 | `req_ce00d46bb6cec9932a7ffd1c` |
| 11 | `GET /v1/derived/heatmap/NVDA/snapshot?format=full` | 200 | 1 | 0 | 99,846 | `req_529b22d0ab82d1effb121a47` |
| 12 | `GET /v1/derived/standard-gex/NVDA/history?limit=10` | 200 | 1 | 0 | 99,845 | `req_3b38101d718685f34b5b75f8` |
| 13 | `GET /v1/derived/dealer-gex/NVDA/snapshot?format=full` | 200 | 1 | 0 | 99,844 | `req_ee11d2b774e6835bda576c84` |

Quota accounting:

- Last persisted pre-validation quota: 99,855 of 100,000.
- `/discover` response body reported 99,854, while the first paid response also reported
  99,854. The provider/client therefore treated `/discover` and `/openapi.json` as zero-unit
  calls despite the one-unit discrepancy between the older persisted pre-observation and the
  discover body.
- Paid requests: 11.
- Paid units consumed: 11.
- Post-validation remaining: 99,844 of 100,000.
- Total HTTP network attempts: 13.
- HTTP retries: 0.
- 202 polls: 0.

Two local command argument-parsing failures occurred before any HTTP request and are not
network attempts or quota events.

## Recommended minimal Phase 2B v1 scope

| Layer | Recommendation | Evidence-based reason |
|---|---|---|
| 1. Price Context | IMPLEMENT NOW | OHLC fields/history are sufficient; first specify canonical daily session and adjustment caveat |
| 2. IV Rank | IMPLEMENT NOW | direct one-year 0-100 vendor field with date/as-of; keep raw until thresholds are versioned |
| 3. Term Structure | IMPLEMENT NOW | exact candidate-expiry node and neighbouring expiries are available; do not invent curve labels |
| 4. IV vs RV | DEFER | current snapshot exists, but RV lookback and IV/RV tenor equivalence are undisclosed |
| 5. Skew | DEFER | 25-delta series exists, but sign, tenor, and component semantics are missing |
| 6. Dealer/GEX Structure | IMPLEMENT NOW | heatmap has candidate-relevant expiry/strike axes; surface degraded/completeness state and keep standard GEX separate |
| 7. Event Risk | DEFER | authoritative forward-looking per-ticker event runtime capability not confirmed |
| 8. Existing Liquidity/Greeks | IMPLEMENT NOW | already persisted with observation timestamps; no vendor refetch needed |
| 9. Existing Positioning Structure | IMPLEMENT NOW | reuse accepted Phase 2A outputs and immutable threshold/config evidence |

“IMPLEMENT NOW” here is a recommendation for the later Phase 2B implementation task; no
implementation was performed in this gate.

## Explicitly rejected assumptions

- A Call Radar event is not evidence of bullish intent.
- Positive OI Diff does not reveal whether calls were bought, written, spread, or hedged.
- Large premium is positioning significance, not direction.
- Rising price does not resolve the economic direction of the option trade.
- Positive or negative GEX is not, by itself, a BUY/SELL or BULLISH/BEARISH signal.
- The term-structure endpoint does not supply an ATM definition or curve class.
- Negative risk reversal is not interpreted without a documented sign convention and tenor.
- `1d` OHLC records are not assumed to be one regular-session record per date.
- OHLC is not assumed split-adjusted.
- Heatmap expiry-axis and strike-axis membership do not prove that a sparse joint cell exists.
- A degraded heatmap is not assumed complete.
- Standard GEX is not assumed to contain strike/expiry structure.
- 0DTE Dealer GEX is not generalized to non-0DTE candidates.
- Reporting-session earnings calendars are not assumed forward-looking.
- No confirmation, conviction, Tradeability, BUY/SELL, or directional score is justified.

For `NVDA260821C00220000`:

`POSITIONING SIGNIFICANCE = MATERIAL`  
`DIRECTION = UNRESOLVED`

## Blockers and open issues

1. Specify and version the authoritative session/deduplication policy for the `1d` OHLC
   response; confirm split-adjustment semantics.
2. Preserve the exact candidate heatmap cell in a future implementation evidence record and
   define behavior for `state=degraded`, sparse cells, and truncation/completeness metadata.
3. Obtain authoritative RV lookback/tenor semantics before classifying IV versus RV.
4. Obtain risk-reversal sign, expiration/tenor, and component definitions before using skew.
5. Confirm a forward-looking per-ticker event calendar before adding Event Risk.
6. Define all descriptive-state thresholds as runtime-configurable, versioned configuration;
   historical evaluations must retain the effective config version and must not be rewritten.

None of these blockers changes or invalidates the accepted Phase 2A v1.3 implementation.

## Repository validation

- Backend: `python -m pytest -p no:cacheprovider` — 152 passed.
- Ruff: `python -m ruff check --no-cache .` — all checks passed.
- Frontend ESLint: `npm run lint` — passed.
- Frontend production build: `npm run build` — passed; Next.js generated all six routes.
- `git diff --check` — passed.
- Production source changes — zero.
- Alembic migration changes — zero; migration head remains
  `20260813_0008_phase2a_v13_three_routes.py`.
- `.env`, `backend/.env`, and `frontend/.env.local` are covered by repository ignore rules.
- Tracked Nightwatch-secret pattern scan found no secret. Database URI-shaped strings found
  in tracked non-Markdown files were reviewed and are only localhost/example configuration
  defaults and test fixtures (`change-me`, `password`, or `private-password`), not the local
  development credential.
- No Authorization header was included in diagnostic evidence or persisted by the diagnostic
  harness. Authenticated capability responses were summarized in memory and were not written
  to production persistence.

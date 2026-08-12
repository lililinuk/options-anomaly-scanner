# Vendor Capability Validation Gate — 2026-08-12

## Scope and safety boundary

This is an NVDA-only runtime schema probe from accepted commit
`4bb3f8261c49e88cb58635ceaf5764e55a7760b8`. It does not change production code,
scoring, thresholds, scan selection, persistence schema, migrations, dashboard behavior, or
Phase 2A/2B design. No complete MAG7 scan was run.

The probe reused the existing server-side Nightwatch client with concurrency `1` and retries `0`.
The API key remained wrapped as a server-side secret. Authorization headers, raw responses, and
request identifiers were not written to this report. Temporary diagnostic harnesses were removed
after the safe summaries below were captured.

One initial `/v1/discover` attempt was blocked before an HTTP response by the local filesystem/network
sandbox. The authorized run then made 11 HTTP requests with no retries. Including that failed
transport attempt, the task used 12 network attempts, below the limit of 25.

## Quota evidence

| Item | Observed value |
|---|---:|
| Pre-validation monthly remaining | 99,993 |
| Post-validation monthly remaining | 99,987 |
| Paid units consumed from quota headers | 6 |
| Successful/accepted Nightwatch HTTP responses | 11 |
| Transport attempts including the pre-HTTP sandbox failure | 12 |
| Retry attempts | 0 |
| Account monthly limit | 100,000 |
| Account rate limit | 60/minute |

`/v1/discover` and `/v1/openapi.json` did not consume paid quota. The six-unit decrease occurred
across the data probes. The final chain completion re-read did not reduce remaining quota. The two
contract-history endpoints returned `202`; no polling was performed.

## Discovery and OpenAPI gate

Authenticated `/v1/discover` returned HTTP 200 with top-level keys `data` and `_meta`, 187 confirmed
capabilities, and all eight requested option capabilities marked available:

- `options.expiry_breakdown`
- `options.oi_per_expiry`
- `options.oi_per_strike`
- `options.oi_change`
- `options.options_volume`
- `options.chain_snapshot`
- `options.contract_intraday`
- `options.contract_daily`

Unauthenticated `/v1/openapi.json` returned HTTP 200 with top-level keys `openapi`, `info`, `servers`,
`paths`, and `components`. Every requested route was present. OpenAPI confirmed that chain snapshot
requires one `expiration`, contract daily requires `from` and `to`, and contract intraday has no
query parameter. OpenAPI describes expected operations; the runtime responses below are the field
authority for this report.

## Endpoint results

### A — `options.expiry_breakdown`

- Request: `GET /v1/options/expiry-breakdown/NVDA`
- Result: HTTP 200; one request
- Top-level keys: `data`, `_meta`
- Data keys: `as_of`, `expiries`
- Array: 23 expiry objects
- Representative safe object shape: `{expiry: date, chains: int, open_interest: int, volume: int}`
- Metadata keys included `request_id`, `cache_hit`, `truncated`, `data_freshness_seconds`, and
  rate/quota metadata.
- Critical support: expiration, expiry total volume, expiry total OI.
- Critical absence: ticker in the body, Call/Put volume, Call/Put OI. The returned `as_of` did not
  yield a usable non-null temporal sample, so its observation time is ambiguous.

### B — `options.oi_per_expiry`

- Request: `GET /v1/options/oi-per-expiry/NVDA`
- Result: HTTP 200; one request
- Data keys: `as_of`, `expiries`
- Array: 23 expiry objects
- Representative safe object shape:
  `{expiry: date, date: date, call_oi: int, put_oi: int}`
- Vendor time: `as_of=2026-08-11T04:00:00.000Z`; row date `2026-08-11`.
- Critical support: expiry, Call OI, Put OI, and total expiry OI by exact side sum.
- Critical absence: volume and ticker in the body.

### C — `options.oi_per_strike`

- Request: `GET /v1/options/oi-per-strike/NVDA`
- Result: HTTP 200; one request
- Data keys: `as_of`, `strikes`
- Array: 273 strike objects
- Representative safe object shape:
  `{strike_usd: number, date: date, call_oi: int, put_oi: int}`
- Vendor time: `as_of=2026-08-11T04:00:00.000Z`; row date `2026-08-11`.
- Critical support: ticker-wide side-specific OI by strike.
- Critical absence: expiration, contract identifier, contract volume, and ticker in the body. This
  cannot by itself produce expiry-specific strike clusters.

### D — `options.oi_change`

- Request: `GET /v1/options/oi-change/NVDA`
- Result: HTTP 200; one request
- Data keys: `as_of`, `contracts`
- Array: 50 ranked contract objects
- Representative safe object shape: `{option_symbol: OSI-like string, date: date, prev_date: date,
  prev_oi: int, oi: int, oi_diff: int, oi_change: number, volume: int, trades: int,
  avg_price_usd: number, last_bid_usd: number, last_ask_usd: number, last_fill_usd: number,
  premium_usd: number, rank: int}`
- Vendor time: `as_of=2026-08-11T04:00:00.000Z`; record date `2026-08-11`; previous date supplied.
- Critical support: contract identifier, previous OI, current absolute OI, absolute OI delta, relative
  OI change, record dates, volume/trades, quote/fill observations, and premium for returned records.
- Critical absence: separate right, strike, and expiration fields; IV, Greeks, and underlying spot.
  The OSI-like identifier encodes right/expiration/strike, but those are not separate vendor fields.
- Universe finding: this is not a complete NVDA contract universe. It returned 50 ranked records,
  while the single probed expiry alone contained 132 contracts. It is therefore a changed/ranked
  subset and is unsafe as a total-OI or OI-share denominator.

### E — `options.options_volume`

- Request: `GET /v1/options/options-volume/NVDA`
- Result: HTTP 200; one request
- Data keys: `as_of`, `day`; `day` is one object rather than an array.
- Representative safe fields: `date`, `call_volume`, `put_volume`, `call_open_interest`,
  `put_open_interest`, bid/ask-side call/put volumes, call/put/net/bullish/bearish premiums, and
  3/7/30-day average Call/Put volume.
- Vendor time: `as_of=2026-08-11T04:00:00.000Z`; day date `2026-08-11`.
- Critical support: ticker-day Call Volume, Put Volume, Call OI, Put OI; ticker-day totals are safely
  derivable by summing the two sides.
- Critical absence: expiration granularity, contract rows, and ticker in the body.

### F — `options.chain_snapshot`

- Requests: `GET /v1/options/chain-snapshot/NVDA?expiration=2026-08-12`; two requests total. The
  expiration was selected from the already returned `oi_per_expiry` response. The second request
  captured completion indicators omitted by the first safe summary and did not reduce quota.
- Result: HTTP 200 on both requests.
- Data keys: `ticker`, `expiration`, `roots`, `contracts`, `total_contracts`, `snapshot_at`,
  `open_interest_as_of`, `quote_as_of`, `greeks_as_of`, `underlying_as_of`,
  `underlying_price_usd`.
- Array: 132 contracts; `total_contracts=132`; `_meta.truncated=false`; 66 calls and 66 puts.
- Representative safe contract shape: `{contract_symbol: OSI-like string, expiration: date,
  right: C|P, strike_usd: number, open_interest: int, bid_usd: number, ask_usd: number,
  implied_vol_pct: number, delta: number, gamma: number, theta: number, vega: number,
  charm: number}`.
- Every returned contract contained `open_interest`; zero contracts contained a `volume` field.
- Vendor times: snapshot/quote/Greeks `2026-08-11T20:00:02.164Z`, OI
  `2026-08-11T10:30:22.156Z`, and underlying `2026-08-12T00:00:00.567Z`.
- Critical support: complete contract list for the requested expiry, Call/Put identity, strike,
  current OI, quotes/spread inputs, IV, delta/other Greeks, and underlying spot.
- Critical absence: contract volume, prior OI, OI delta, last trade, and directly supplied midpoint.

### G — `options.contract_intraday`

- Request: `GET /v1/options/contract-intraday/NVDA260812P00390000`; one request. The contract was
  selected from the returned chain rather than invented.
- Result: HTTP 202.
- Top-level keys: `data`, `_meta`; no bar array was returned.
- Metadata keys: `status`, `hint`, `retry_after_seconds`, `request_id`.
- No polling was performed. Minute timestamps, volume semantics, OHLC, trades, VWAP, interval, and
  timezone semantics remain unverified.

### H — `options.contract_daily`

- Request: `GET /v1/options/contract-daily/NVDA260812P00390000` with `from=2026-07-22` and
  `to=2026-08-12`; one request. The range ended on the New York market date because the chain
  temporal helper did not expose a generic `as_of` field.
- Result: HTTP 202.
- Top-level keys: `data`, `_meta`; no daily bar array was returned.
- Metadata keys: `status`, `hint`, `retry_after_seconds`, `request_id`.
- No polling was performed. Per-contract daily history fields therefore remain unverified.

## Capability matrix

The matrix describes values at the named semantic level. For example, an aggregate strike in C is
not counted as a contract-level strike. `NOT_TESTED` for G/H means the capability was invoked, but
the only response was `202` without data rows.

Abbreviations: A expiry breakdown; B OI per expiry; C OI per strike; D OI change; E options volume;
F chain snapshot; G contract intraday; H contract daily.

### Ticker / expiry level

| Field | A | B | C | D | E | F | G | H |
|---|---|---|---|---|---|---|---|---|
| ticker in payload | NOT_PRESENT | NOT_PRESENT | NOT_PRESENT | NOT_PRESENT | NOT_PRESENT | SUPPORTED | NOT_TESTED | NOT_TESTED |
| expiration | SUPPORTED | SUPPORTED | NOT_PRESENT | NOT_PRESENT | NOT_PRESENT | SUPPORTED | NOT_TESTED | NOT_TESTED |
| DTE or date sufficient to calculate DTE | SUPPORTED | SUPPORTED | NOT_PRESENT | NOT_PRESENT | NOT_PRESENT | SUPPORTED | NOT_TESTED | NOT_TESTED |
| total volume at scope | SUPPORTED | NOT_PRESENT | NOT_PRESENT | NOT_PRESENT | SUPPORTED | NOT_PRESENT | NOT_TESTED | NOT_TESTED |
| total OI at scope | SUPPORTED | SUPPORTED | AMBIGUOUS | NOT_PRESENT | SUPPORTED | SUPPORTED | NOT_TESTED | NOT_TESTED |
| Call volume at scope | NOT_PRESENT | NOT_PRESENT | NOT_PRESENT | NOT_PRESENT | SUPPORTED | NOT_PRESENT | NOT_TESTED | NOT_TESTED |
| Put volume at scope | NOT_PRESENT | NOT_PRESENT | NOT_PRESENT | NOT_PRESENT | SUPPORTED | NOT_PRESENT | NOT_TESTED | NOT_TESTED |
| Call OI at scope | NOT_PRESENT | SUPPORTED | AMBIGUOUS | NOT_PRESENT | SUPPORTED | SUPPORTED | NOT_TESTED | NOT_TESTED |
| Put OI at scope | NOT_PRESENT | SUPPORTED | AMBIGUOUS | NOT_PRESENT | SUPPORTED | SUPPORTED | NOT_TESTED | NOT_TESTED |
| vendor as-of / observation date | AMBIGUOUS | SUPPORTED | SUPPORTED | SUPPORTED | SUPPORTED | SUPPORTED | NOT_TESTED | NOT_TESTED |
| source timestamp | AMBIGUOUS | SUPPORTED | SUPPORTED | SUPPORTED | SUPPORTED | SUPPORTED | NOT_TESTED | NOT_TESTED |

C supplies Call/Put OI by strike without expiration. Its ticker total could only be inferred by
summing a complete response, so ticker/expiry-level use is marked `AMBIGUOUS`. E totals are exact
sums of its side fields. F expiry OI and side OI are safe sums for this response because
`returned_contract_count == total_contracts` and `truncated=false`.

### Contract level

| Field | A | B | C | D | E | F | G | H |
|---|---|---|---|---|---|---|---|---|
| contract identifier | NOT_PRESENT | NOT_PRESENT | NOT_PRESENT | SUPPORTED | NOT_PRESENT | SUPPORTED | NOT_TESTED | NOT_TESTED |
| expiration | NOT_PRESENT | NOT_PRESENT | NOT_PRESENT | AMBIGUOUS | NOT_PRESENT | SUPPORTED | NOT_TESTED | NOT_TESTED |
| option right / Call-Put identity | NOT_PRESENT | NOT_PRESENT | NOT_PRESENT | AMBIGUOUS | NOT_PRESENT | SUPPORTED | NOT_TESTED | NOT_TESTED |
| strike | NOT_PRESENT | NOT_PRESENT | NOT_PRESENT | AMBIGUOUS | NOT_PRESENT | SUPPORTED | NOT_TESTED | NOT_TESTED |
| volume | NOT_PRESENT | NOT_PRESENT | NOT_PRESENT | SUPPORTED | NOT_PRESENT | NOT_PRESENT | NOT_TESTED | NOT_TESTED |
| OI | NOT_PRESENT | NOT_PRESENT | NOT_PRESENT | SUPPORTED | NOT_PRESENT | SUPPORTED | NOT_TESTED | NOT_TESTED |
| previous OI | NOT_PRESENT | NOT_PRESENT | NOT_PRESENT | SUPPORTED | NOT_PRESENT | NOT_PRESENT | NOT_TESTED | NOT_TESTED |
| current OI | NOT_PRESENT | NOT_PRESENT | NOT_PRESENT | SUPPORTED | NOT_PRESENT | SUPPORTED | NOT_TESTED | NOT_TESTED |
| delta OI | NOT_PRESENT | NOT_PRESENT | NOT_PRESENT | SUPPORTED | NOT_PRESENT | NOT_PRESENT | NOT_TESTED | NOT_TESTED |
| bid | NOT_PRESENT | NOT_PRESENT | NOT_PRESENT | SUPPORTED | NOT_PRESENT | SUPPORTED | NOT_TESTED | NOT_TESTED |
| ask | NOT_PRESENT | NOT_PRESENT | NOT_PRESENT | SUPPORTED | NOT_PRESENT | SUPPORTED | NOT_TESTED | NOT_TESTED |
| last | NOT_PRESENT | NOT_PRESENT | NOT_PRESENT | SUPPORTED | NOT_PRESENT | NOT_PRESENT | NOT_TESTED | NOT_TESTED |
| midpoint directly supplied | NOT_PRESENT | NOT_PRESENT | NOT_PRESENT | NOT_PRESENT | NOT_PRESENT | NOT_PRESENT | NOT_TESTED | NOT_TESTED |
| IV | NOT_PRESENT | NOT_PRESENT | NOT_PRESENT | NOT_PRESENT | NOT_PRESENT | SUPPORTED | NOT_TESTED | NOT_TESTED |
| delta | NOT_PRESENT | NOT_PRESENT | NOT_PRESENT | NOT_PRESENT | NOT_PRESENT | SUPPORTED | NOT_TESTED | NOT_TESTED |
| other Greeks | NOT_PRESENT | NOT_PRESENT | NOT_PRESENT | NOT_PRESENT | NOT_PRESENT | SUPPORTED | NOT_TESTED | NOT_TESTED |
| underlying spot | NOT_PRESENT | NOT_PRESENT | NOT_PRESENT | NOT_PRESENT | NOT_PRESENT | SUPPORTED | NOT_TESTED | NOT_TESTED |

D's `option_symbol` is OSI-like and can encode expiration, right, and strike, but those are not
separate fields; they remain `AMBIGUOUS` pending an explicit vendor contract-format guarantee.
D's quote fields are specifically last bid/ask/fill observations, not a synchronized chain quote.

### Intraday level

| Field | A | B | C | D | E | F | G | H |
|---|---|---|---|---|---|---|---|---|
| timestamp | NOT_PRESENT | NOT_PRESENT | NOT_PRESENT | NOT_PRESENT | NOT_PRESENT | NOT_PRESENT | NOT_TESTED | NOT_TESTED |
| interval | NOT_PRESENT | NOT_PRESENT | NOT_PRESENT | NOT_PRESENT | NOT_PRESENT | NOT_PRESENT | NOT_TESTED | NOT_TESTED |
| volume | NOT_PRESENT | NOT_PRESENT | NOT_PRESENT | NOT_PRESENT | NOT_PRESENT | NOT_PRESENT | NOT_TESTED | NOT_TESTED |
| volume is per-bar | NOT_PRESENT | NOT_PRESENT | NOT_PRESENT | NOT_PRESENT | NOT_PRESENT | NOT_PRESENT | NOT_TESTED | NOT_TESTED |
| volume is cumulative | NOT_PRESENT | NOT_PRESENT | NOT_PRESENT | NOT_PRESENT | NOT_PRESENT | NOT_PRESENT | NOT_TESTED | NOT_TESTED |
| OHLC | NOT_PRESENT | NOT_PRESENT | NOT_PRESENT | NOT_PRESENT | NOT_PRESENT | NOT_PRESENT | NOT_TESTED | NOT_TESTED |
| trade count | NOT_PRESENT | NOT_PRESENT | NOT_PRESENT | NOT_PRESENT | NOT_PRESENT | NOT_PRESENT | NOT_TESTED | NOT_TESTED |
| price / VWAP fields | NOT_PRESENT | NOT_PRESENT | NOT_PRESENT | NOT_PRESENT | NOT_PRESENT | NOT_PRESENT | NOT_TESTED | NOT_TESTED |
| timezone / as-of semantics | NOT_PRESENT | NOT_PRESENT | NOT_PRESENT | NOT_PRESENT | NOT_PRESENT | NOT_PRESENT | NOT_TESTED | NOT_TESTED |

## Call / Put finding

1. **Aggregate Call Volume / Put Volume:** supported at ticker-day scope by
   `options.options_volume`. No tested aggregate endpoint supplied those sides per expiry.
2. **Aggregate Call OI / Put OI:** supported per expiry by `options.oi_per_expiry`, per strike by
   `options.oi_per_strike`, and at ticker-day scope by `options.options_volume`.
3. **Chain Call/Put identity:** supported by explicit `right`; the complete response had 66 C and
   66 P records.
4. **Chain contract volume:** not present on any of the 132 contracts.
5. **Chain contract OI:** supported on every contract.

Call/Put Volume cannot be derived from this chain because contract volume is absent. Call/Put OI
can safely be derived for the probed expiry by summing `open_interest` grouped by `right`, because
the response was explicitly complete (`132 == total_contracts`, `truncated=false`). No derivation
was implemented.

## OI Memory finding

`options.oi_change` returns 50 ranked records with `option_symbol`, `prev_oi`, current `oi`, absolute
`oi_diff`, relative `oi_change`, `date`, `prev_date`, and a top-level `as_of`. Absolute OI, delta OI,
and observation dates are therefore present for the returned records.

The payload is category **B: only a changed/ranked subset**, not a complete per-contract universe.
The proof is structural: a ticker-wide response contained only 50 ranked records while one NVDA
expiry alone contained 132 complete chain contracts. It must not be used as the denominator for
total OI or OI Share.

For a future Daily OI Memory design, the runtime-verified safe source is the daily-dated
`options.oi_per_expiry` snapshot, persisted by its vendor `date`/`as_of` and expiry. The OI-change
subset can serve as contract-level change evidence or confirmation only. Nothing was implemented.

## OI Share finding

`options.oi_per_expiry` is the best verified source for both inputs:

- `expiry_oi = call_oi + put_oi` for one returned expiry;
- `ticker_total_oi = sum(expiry_oi)` across the explicitly selected expiry scope.

It supplied 23 expiries with row date `2026-08-11` and exact `as_of=2026-08-11T04:00:00.000Z`.
Reliable daily expiry OI snapshots are therefore obtainable. A future OI Share Change is data-
feasible only after separately designed, validated daily snapshot persistence exists; this task did
not add that memory or any formula.

## Chain finding

The live chain is **partially sufficient**, not sufficient for the existing Phase 2A analytical
pipeline as a whole:

- Contract Anomaly engine: **PARTIALLY SUPPORTED**. Identity, right, strike, OI, quotes, IV, Greeks,
  and spot are supported; volume-driven components are not.
- Call/Put symmetric analysis: **PARTIALLY SUPPORTED**. Structural OI/quote/Greek analysis is
  symmetric, but symmetric contract-volume analysis is unavailable.
- Strike Cluster engine: **PARTIALLY SUPPORTED**. Right and strike ladders are complete, but the
  existing cluster's volume/premium concentration and volume-weighted behavior lack inputs.

Existing Phase 2A Contract Score input assessment:

| Input | Finding | Runtime evidence |
|---|---|---|
| Volume/OI | UNSUPPORTED | Chain has OI but no contract volume. |
| Estimated Premium | UNSUPPORTED | Chain has bid/ask but neither volume nor last; current traded premium cannot be estimated safely. |
| Historical Abnormality prerequisites | UNSUPPORTED | No current chain volume and the daily-history call returned only `202`; no usable per-contract series was observed. |
| Liquidity / spread | SUPPORTED | `bid_usd` and `ask_usd` are present; midpoint/spread can be derived locally. |
| Moneyness / delta | SUPPORTED | Strike, explicit delta, and underlying spot are present. |
| Call/Put identity | SUPPORTED | Explicit `right` on all contracts. |

The premium and volume fields on the 50-record OI-change subset do not repair the chain contract
universe because the dataset is incomplete and its observation semantics differ.

## Intraday finding

The one `contract_intraday` response did not provide one-minute history; it returned HTTP 202 with
materialization metadata and no bars. Accordingly, minute timestamps, interval, OHLC, trade count,
price/VWAP, timezone, and whether volume is per-bar or cumulative are not runtime-verified.

Active minutes, first/last activity time, largest five-minute share, top-three five-minute-window
share, and DISTRIBUTED/CONCENTRATED/REPEATED descriptive analysis are **not safely calculable from
the observed response**. Intraday Burst is also unsupported until a completed payload and its volume
semantics are validated. No polling, metric implementation, or predictive claim was made.

## Recommended Phase 2A Amendment inputs (recommendation only)

These labels are evidence recommendations, not implemented changes. `KEEP` means verified at the
required scope; `MOVE TO DEEP-DIVE` means useful only in a bounded secondary flow; `RESEARCH-ONLY`
means promising but not runtime-complete; `UNSUPPORTED` means the required live field was absent or
unverified.

| Input | Recommendation | Evidence boundary |
|---|---|---|
| Total Volume | KEEP | Per-expiry total in A; ticker-day side totals in E. |
| Total OI | KEEP | Per-expiry total in A and side totals in B. |
| Volume Share | KEEP | A provides comparable per-expiry volumes. |
| OI Share | KEEP | B provides daily side OI for all returned expiries. |
| Call Volume | UNSUPPORTED | Available ticker-day in E, not per expiry or in chain. |
| Put Volume | UNSUPPORTED | Available ticker-day in E, not per expiry or in chain. |
| Call OI | KEEP | B provides per-expiry Call OI. |
| Put OI | KEEP | B provides per-expiry Put OI. |
| Volume Skew | UNSUPPORTED | No verified per-expiry Call/Put volume source. |
| OI Skew | KEEP | B provides both OI sides per expiry. |
| OI Change | MOVE TO DEEP-DIVE | D is a useful ranked changed-contract subset, not a universe denominator. |
| OI Share Change | RESEARCH-ONLY | Daily B snapshots make it feasible only after a separately designed memory layer. |
| Volume/OI | UNSUPPORTED | F lacks contract volume. |
| Premium | RESEARCH-ONLY | D has premium for a changed subset; F lacks traded volume/last. |
| Spread | KEEP | F has bid and ask. |
| Delta | KEEP | F has explicit delta and underlying spot. |
| Intraday Burst | RESEARCH-ONLY | G returned `202`; completed bar and volume semantics are unverified. |
| Intraday Activity Profile | RESEARCH-ONLY | G returned no bars; descriptive inputs remain unverified. |

## External request ledger

| Endpoint | HTTP responses | Result |
|---|---:|---|
| `/v1/discover` | 1 | 200; plus one pre-HTTP transport failure |
| `/v1/openapi.json` | 1 | 200 |
| `/v1/options/expiry-breakdown/NVDA` | 1 | 200 |
| `/v1/options/oi-per-expiry/NVDA` | 1 | 200 |
| `/v1/options/oi-per-strike/NVDA` | 1 | 200 |
| `/v1/options/oi-change/NVDA` | 1 | 200 |
| `/v1/options/options-volume/NVDA` | 1 | 200 |
| `/v1/options/chain-snapshot/NVDA?expiration=2026-08-12` | 2 | 200, 200 |
| `/v1/options/contract-intraday/NVDA260812P00390000` | 1 | 202 |
| `/v1/options/contract-daily/NVDA260812P00390000?from=2026-07-22&to=2026-08-12` | 1 | 202 |

No `/v1/health` call, paid scanner endpoint beyond the table, complete MAG7 scan, browser-to-Nightwatch
request, or automated-test live call occurred.

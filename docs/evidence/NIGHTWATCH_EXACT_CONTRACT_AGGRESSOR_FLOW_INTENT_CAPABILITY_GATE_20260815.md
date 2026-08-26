# Nightwatch Exact-Contract Aggressor / Flow Intent Capability Gate — 2026-08-15

## 1. Executive conclusion

**Gate result: B — `EXACT_CONTRACT_AGGRESSOR_DATA_USABLE_BUT_MUST_BE_ARCHIVED`.**

Nightwatch exposes useful exact-contract aggressor evidence through two public REST endpoints:

- `contract-intraday` returns exact-contract, one-minute bid/ask/mid/no-side Volume and Premium fields, but only the latest 150 stored bars were returned in both controlled observations. The returned 150 bars were 150 of 369 and later 150 of 332 total bars, so this is not a full-session series.
- `contract-volume-profile` returns a latest-day, price-bucketed full-volume partition with `ask_volume`, `bid_volume`, `mid_volume`, and aggregate `multi_volume` / `sweep_volume` context. It returned no Premium fields, but the price buckets make a diagnostic `price_usd × volume × 100` calculation possible.

The current public OpenAPI exposes no date, start, end, cursor, offset, limit, page, session, before, or after parameter for either endpoint. During this gate, the same endpoint changed from an older 2026-08-11 stored session to 2026-08-14 after a background refresh. Once the latest-day projection rolls, the prior response cannot be selected again through the documented contract. A future research layer must therefore preserve the T-day payload before it rolls.

The data is sufficient to justify a future **research-only, probabilistic** Flow Intent layer, subject to archival and calibration. It is not sufficient to change production `Observed Flow Direction = UNRESOLVED`, and this gate makes no such change.

### Founder summary

```text
Gate result:
B. EXACT_CONTRACT_AGGRESSOR_DATA_USABLE_BUT_MUST_BE_ARCHIVED

Can get exact-contract ask/bid Volume?
YES
(full latest-day price-bucket aggregate; latest-150-bars intraday detail)

Can get exact-contract ask/bid Premium?
PARTIAL
(explicit fields on latest 150 intraday bars; no full-day Premium fields)

Full day?
PARTIAL
(full-day Volume profile; intraday bar/Premium series is partial)

Historical/backfillable?
NO

Can T-day data be paired with T+1 ΔOI without same-day archive?
UNRESOLVED

Sweep/Block/Multileg public API?
PARTIAL
(Sweep and aggregate Multi confirmed; Block and leg linkage not found)

Live Nightwatch API HTTP requests:
9 successful requests

Paid units:
4

Production changes:
0
```

## 2. Scope and safety boundary

This was a read-only capability gate. It did not:

- change scoring, thresholds, selector logic, or Flow Direction semantics;
- add a Flow Intent model, label, or probability;
- add a migration, table, scheduler, API route, or dashboard element;
- run MAG7, Daily OI Archive, or Dealer/GEX archive;
- call more than one exact contract;
- print or persist an API key, Authorization header, database credential, or raw secret;
- commit or push.

The only repository change is this evidence report.

## 3. Repository preflight / current authority

Observed before the gate:

| Item | Value |
|---|---|
| Branch | `main` |
| HEAD | `1e29c92956b39f005dab0c4eb163150ee12a0c9d` |
| Locally known `origin/main` | `1e29c92956b39f005dab0c4eb163150ee12a0c9d` |
| Tracked modifications | none |
| Staged changes | none |
| Pre-existing untracked files | `docs/evidence/PHASE2A_SIGNAL_ANATOMY_READ_ONLY_HANDOFF_VERIFICATION_20260815.md`; `docs/evidence/PHASE2B_V31_FIRST_REAL_GITHUB_SCHEDULED_RUN_CLOSEOUT_20260815.md` |
| Working tree | dirty only because of the two pre-existing untracked files |

Those two files were preserved and not edited.

### Current transport

The production transport is the server-side [`NightwatchClient`](../../backend/app/nightwatch/client.py), backed by `httpx.AsyncClient` and defaulting to `https://api.yehangshe.com`. The API key remains a Pydantic `SecretStr` loaded by the backend settings path. Browser code uses the existing same-origin backend proxy and does not call Nightwatch directly.

`/v1/health`, `/v1/discover`, and `/v1/openapi.json` are registered as zero-quota paths in the client. Runtime data calls are observed without retaining Authorization headers.

### Existing repository support

| Capability / concept | Existing state before this gate |
|---|---|
| `options.contract_intraday` capability | Present in capability registry and vendor capability documentation |
| Intraday REST route | Present in a legacy scanner service path |
| Intraday parser | Legacy `intraday_metrics` reads generic Volume and price/VWAP inputs; it does not parse aggressor-side fields |
| Current v1.3 production scanner | Uses `Mag7Scanner` from `backend/app/scanner/v13.py`; v1.1/v1.2/v1.3 paths leave legacy intraday fields null and make zero intraday requests |
| `contract-volume-profile` support | No client wrapper, capability registry entry, parser, fixture, model, or test found |
| Bid/ask-side Volume or Premium fields | No parser, model, fixture, test, or production consumer found |
| Sweep / Block / Multileg fields | No production parser, model, fixture, test, or consumer found |

The current production path therefore consumes none of the newly observed aggressor-side fields. The legacy intraday drilldown does not make them production evidence.

## 4. Zero-quota discovery

The live OpenAPI was read from `GET /v1/openapi.json` and reported:

| Field | Value |
|---|---|
| OpenAPI | `3.1.0` |
| Title | `GEX Heatmap Data API` |
| Version | `0.3.0-dealer-response-schema` |

Authenticated zero-quota `GET /v1/discover` confirmed both commands as available:

| Command | Available | Coverage | Scope | Tool | Weight |
|---|---:|---|---|---|---:|
| `options.contract_intraday` | true | `on-demand` | `derived:read` | `dataset_query` | 1 |
| `options.contract_volume_profile` | true | `on-demand` | `derived:read` | `dataset_query` | 1 |

The current public OpenAPI names the operations but describes a successful response only as `object payload`; it supplies no component response schema. Runtime evidence was therefore required to answer the field-level gate.

## 5. Endpoint / capability matrix

| Question | Contract intraday | Contract volume profile |
|---|---|---|
| Method / route | `GET /v1/options/contract-intraday/{contract}` | `GET /v1/options/contract-volume-profile/{contract}` |
| Required parameter | path `contract: string` | path `contract: string` |
| Other documented parameters | none | none |
| Discover command | `options.contract_intraday` | `options.contract_volume_profile` |
| Discover weight | 1 | 1 |
| Documented description | Intraday 1-minute bars for one contract; on-demand materialization | Latest-day volume profile for one contract; on-demand materialization |
| Explicit activity date | `data.as_of`; per-bar `start_time` | `data.as_of`; per-level `date` |
| Bid/ask Volume | yes, per returned bar | yes, per price bucket |
| Bid/ask Premium | yes, per returned bar | no explicit Premium fields |
| Mid / no-side | `volume_mid_side`, `volume_no_side`, and corresponding Premium fields | `mid_volume`; no distinct no-side field observed |
| Complex context | `volume_multi`, `volume_stock_multi` | `multi_volume`, `sweep_volume`, `floor_volume`, `cross_volume` |
| Full session | no: latest 150 of `total_bars` | latest-day totals reconciled exactly to the profile's side partition |
| Historical selector / pagination | none | none |
| Materialization observed in this gate | HTTP 200 immediately | HTTP 200 immediately |

## 6. Exact runtime response schemas

Controlled exact contract:

```text
NVDA260821C00220000
```

Both endpoints use the normal top-level envelope:

```text
data: object
_meta: object
```

Observed `_meta` keys included `cache_hit`, `data_freshness_seconds`, `notice`, `quota_remaining_pct`, `rate_limit_remaining`, `request_id`, and `truncated`. Request IDs were deliberately not retained in this report.

### 6.1 `contract-intraday`

Observed `data` schema:

| Field | Runtime type | Sample nullability |
|---|---|---|
| `as_of` | ISO-8601 string | non-null |
| `contract_symbol` | string | non-null |
| `total_bars` | integer | non-null |
| `bars` | array of objects | non-null |

Every bar in the two 150-row observations contained these fields. None was null in either sample:

| Field | Runtime JSON type(s) |
|---|---|
| `start_time` | string |
| `open_usd` | integer or number |
| `high_usd` | integer or number |
| `low_usd` | integer or number |
| `close_usd` | integer or number |
| `avg_price_usd` | integer or number |
| `iv_high` | number |
| `iv_low` | number |
| `volume_ask_side` | integer |
| `volume_bid_side` | integer |
| `volume_mid_side` | integer |
| `volume_no_side` | integer |
| `premium_ask_side` | integer |
| `premium_bid_side` | integer |
| `premium_mid_side` | integer |
| `premium_no_side` | integer |
| `volume_multi` | integer |
| `volume_stock_multi` | integer |

The bars arrived newest-first in the first response; consumers must not infer ascending order.

### 6.2 `contract-volume-profile`

Observed `data` schema:

| Field | Runtime type | Sample nullability |
|---|---|---|
| `as_of` | ISO-8601 string | non-null |
| `contract_symbol` | string | non-null |
| `levels` | array of objects | non-null |

Every one of the 248 first-observation levels and 165 refreshed levels contained these fields. None was null:

| Field | Runtime JSON type(s) |
|---|---|
| `date` | string (`YYYY-MM-DD`) |
| `price_usd` | integer or number |
| `volume` | integer |
| `transactions` | integer |
| `ask_volume` | integer |
| `bid_volume` | integer |
| `mid_volume` | integer |
| `multi_volume` | integer |
| `sweep_volume` | integer |
| `floor_volume` | integer |
| `cross_volume` | integer |

No explicit Premium field was returned by this endpoint.

## 7. Bid / ask-side semantics

Field availability is runtime-confirmed. Public API reference pages name the endpoints but do not define how the vendor classifies ask, bid, and mid trades.

The vendor guidance supplied with this gate states that these fields classify **where a trade occurred relative to bid/ask**, rather than reporting quote `bid_size` / `ask_size`. Under that supplied semantic:

```text
Ask-side dominant
= activity classified at/near the ask
= buyer-initiated / buyer-aggressed activity

Bid-side dominant
= activity classified at/near the bid
= seller-initiated / seller-aggressed activity
```

This does not establish opening or closing intent:

```text
Ask-side != automatically Buy to Open
Bid-side != automatically Sell to Open
```

The runtime and public schema do not expose BTO/STO/BTC/STC. The future inference can only become probabilistically stronger after joining T-day aggressor evidence to later OI creation/retention and complex-trade context.

Evidence-strength qualification: the fields and numeric behavior are runtime-confirmed; the buyer-/seller-aggressed mapping is supported by the vendor guidance supplied for this gate, but is not defined in the current public OpenAPI text. A production specification should obtain a stable vendor contract for that classification rule.

## 8. Premium unit semantics

### Classification

```text
UNIT_SEMANTICS_UNCONFIRMED
```

The public OpenAPI does not state currency, multiplier, rounding, or calculation methodology. Runtime evidence is nevertheless strongly consistent with integer USD option Premium already including the standard 100 multiplier.

For the refreshed 2026-08-14 latest-150-bar response:

| Diagnostic | Value |
|---|---:|
| Classified Volume | 2,710 contracts |
| Reported side Premium total | $1,899,372 |
| Sum of `avg_price_usd × classified bar volume × 100` | $1,899,577 |
| Difference | $205 |
| Relative difference | 0.0108% |

The small difference is consistent with aggregation/rounding and with side-specific executions not necessarily sharing the whole-bar average price. It is not a formal unit declaration.

For the same 2026-08-14 session, the full volume profile produced:

| Diagnostic derivation | Value |
|---|---:|
| `sum(price_usd × volume × 100)` | $5,234,305 |
| Ask-derived | $1,975,342 |
| Bid-derived | $2,064,120 |
| Mid-derived | $1,194,843 |
| Ask + Bid + Mid derived | $5,234,305 |

This derivation is diagnostic only. It was not added to production.

## 9. Full-session versus latest-150 coverage

Two observations independently showed partial intraday coverage:

| Observation | `as_of` | `total_bars` | Returned | Missing active bars | Earliest returned | Latest returned |
|---|---|---:|---:|---:|---|---|
| Initial, stale value | `2026-08-11T19:59:00Z` | 369 | 150 | 219 (59.3%) | `17:15:00Z` | `19:59:00Z` |
| Refreshed value | `2026-08-14T19:59:00Z` | 332 | 150 | 182 (54.8%) | `17:00:00Z` | `19:59:00Z` |

In August, New York is UTC-4. The refreshed returned window therefore began at 13:00 ET. A regular 09:30–16:00 session contains 390 clock minutes, so approximately the first 210 minutes (3.5 hours, 53.8% of the session clock) were absent. The 150 returned active bars occupied the final 180 clock minutes.

Classification:

```text
PARTIAL_LATEST_150_BARS
```

`_meta.truncated` was false, but `total_bars > len(bars)` directly proves the returned series was incomplete. Coverage logic must use the explicit count relationship and timestamps, not `_meta.truncated` alone.

The same-day volume profile supplied all 7,171 refreshed contracts and partitioned them exactly:

```text
ask_volume  2,695
bid_volume  2,837
mid_volume  1,639
total       7,171
```

The latest-150 intraday bars contained 2,710 classified contracts, or 37.8% of the profile total. Thus the profile can provide a full latest-day Volume-side aggregate while intraday timing and explicit Premium remain partial.

## 10. Historical / backfill capability

Neither target endpoint exposes a selector or pagination parameter beyond the contract path. The public OpenAPI was searched for date, start, end, cursor, offset, limit, page, session, before, and after parameters on these operations; none exists.

The separate `contract-daily` endpoint has `from` / `to`, but it is not an aggressor-side backfill and does not repair the missing bid/ask history.

Classification:

```text
LATEST_ONLY_NO_BACKFILL
```

The initial runtime response returned a stale 2026-08-11 value with a notice that a background refresh had been requested. A later read returned 2026-08-14. There was no parameter with which to ask for 2026-08-11 after the projection rolled. This is direct operational evidence that a consumer-controlled archive is required.

## 11. T versus T+1 temporal usability

The endpoint behavior observed on Saturday 2026-08-15 is consistent with “most recently stored latest day,” but one weekend observation cannot determine:

1. whether T remains available throughout T+1 premarket;
2. the exact moment T+1 replaces T after regular trading begins;
3. whether vendor OI / `oi_change` has updated early enough to complete the join before that roll;
4. whether a stale response may refresh asynchronously during the proposed join window.

Classification:

```text
Can T-day data be paired with T+1 ΔOI without same-day archive? UNRESOLVED
```

The safe design assumption is **no** until a timed observation proves otherwise. Capture T after close; do not make correctness depend on a T+1 premarket race between OI availability and latest-day projection rollover.

## 12. Sweep / Block / Multileg public API availability

| Concept | Classification | Evidence / limitation |
|---|---|---|
| Sweep | `PUBLIC_API_CONFIRMED` | `sweep_volume` is present per volume-profile price bucket |
| Multileg / complex aggregate | `PUBLIC_API_CONFIRMED` | `multi_volume`, `volume_multi`, and `volume_stock_multi` are present |
| Individual leg linkage | `NOT_FOUND` | No order/trade/leg identifier or linked-leg array was observed |
| Block | `NOT_FOUND` | No block field was found; `floor_volume` must not be silently renamed “block” |
| Spread | `NOT_FOUND` | Multi volume may contain complex activity, but no explicit spread classification was observed |
| `trade_type` / condition | `NOT_FOUND` | No per-trade record or classification field was observed |
| Explicit `aggressor` label | `NOT_FOUND` | Side is encoded in aggregated ask/bid/mid fields, not an explicit per-trade label |
| Signed Premium | `NOT_FOUND` | Premium is split into non-negative side buckets; no signed field was observed |

Sweep and Multi are useful caveats for a future model, but the current response does not identify which specific trade legs produced those totals. The aggregate fields may overlap the ask/bid/mid partition and must not be added as if they were mutually exclusive Volume.

## 13. Diagnostic side shares

Refreshed 2026-08-14 latest-150-bar totals used a denominator that includes ask, bid, mid, and no-side activity:

```text
total returned classified Volume
= ask + bid + mid + no-side
= 898 + 1,338 + 474 + 0
= 2,710

total returned classified Premium
= $629,690 + $938,787 + $330,895 + $0
= $1,899,372
```

| Measure | Share of all returned classified activity | Share of ask+bid only |
|---|---:|---:|
| Ask Volume | 33.14% | 40.16% |
| Bid Volume | 49.37% | 59.84% |
| Mid Volume | 17.49% | excluded only in this second denominator |
| Ask Premium | 33.15% | 40.15% |
| Bid Premium | 49.43% | 59.85% |
| Mid Premium | 17.42% | excluded only in this second denominator |

This sample is bid-side dominant within the returned partial window. It does not establish Sell to Open, economic direction, or a trade recommendation.

## 14. Reconciliation with existing Radar evidence

Accepted historical Radar evidence for the selected contract was approximately:

```text
activity date  2026-08-11
Volume         24,458
Premium        $10,434,044
Trades         2,887
ΔOI            +4,531
Current OI     62,832
```

The first volume-profile response was dated 2026-08-11 and its `sum(level.volume)` was exactly 24,458.

```text
Volume reconciliation: RECONCILES_CLOSELY (exact equality)
```

That initial full level set was not retained, so this gate cannot safely reconstruct its price-weighted Premium after the endpoint rolled. The later diagnostic response was dated 2026-08-14 and therefore must not be compared numerically to the 2026-08-11 Radar Premium.

```text
Premium reconciliation: DATE_MISMATCH / UNRESOLVED
Trade-count reconciliation: UNRESOLVED
```

No new `oi_change` call was made merely to force a same-date comparison.

## 15. Flow Intent feasibility assessment

A future research model can plausibly use this evidence chain:

```text
exact contract option side
+ archived T-day ask/bid/mid Volume profile
+ archived T-day latest-150 timing and explicit Premium sides
+ T+1 ΔOI
+ OI Retention Proxy
+ Sweep / Multi aggregate caveats
+ existing Persistence / Structure context
```

What the data can support:

- buyer- versus seller-aggressed activity as a probabilistic observation;
- full latest-day side Volume at exact-contract / price-bucket level;
- partial-session timing and explicit side Premium;
- a research distinction between ask/bid imbalance, subsequent OI creation, and complex-activity contamination.

What it cannot directly support:

- observed BTO/STO/BTC/STC;
- certain long/short Call or Put opening intent;
- complete intraday Premium timing for the first portion of the session;
- historical studies without first building a no-lookahead archive;
- leg-resolved spread reconstruction;
- a production probability or threshold without forward-outcome calibration.

Production remains:

```text
Observed Flow Direction = UNRESOLVED
```

## 16. Minimum future archive concept — not implemented

Because the classification is B, a future archive should minimally preserve:

- exact contract symbol and explicit option identity;
- New York activity/session date and vendor `as_of` separately;
- UTC capture timestamp;
- immutable raw response evidence or content-addressed raw payload reference;
- `total_bars`, returned bar count, first/last timestamps, and coverage classification;
- all bid/ask/mid/no-side Volume and Premium fields;
- price-profile levels and Sweep/Multi/Floor/Cross aggregates without assuming they are exclusive;
- vendor freshness notice, cache/truncation metadata, request provenance, and specification version;
- idempotency keyed by contract + vendor session date + endpoint + evidence version;
- an explicit later join to T+1 OI evidence without overwriting the T-day capture.

The safe capture point is T after close. A T+1 premarket re-read can be studied as redundancy, not treated as the only archive opportunity until the rollover window is proven.

No archive, table, migration, or scheduler was implemented in this gate.

## 17. Unresolved items

1. The public API contract does not explicitly declare Premium currency, multiplier, or rounding method; runtime evidence strongly supports USD ×100 but the required classification remains `UNIT_SEMANTICS_UNCONFIRMED`.
2. The public API docs do not define the exact quote-classification algorithm or tolerances for ask, bid, mid, and no-side.
3. T+1 premarket persistence, T+1 regular-session rollover time, and OI-update timing were not observable in this single Saturday gate.
4. The first 2026-08-11 price-level set was not retained, so its derived Premium could not be reconciled after the endpoint rolled.
5. `multi_volume`, `sweep_volume`, `floor_volume`, and aggressor-side totals have no published overlap/exclusivity contract.
6. No public block field or individual complex-trade leg linkage was found.
7. The meaning of `_meta.truncated=false` when `total_bars > len(bars)` needs vendor clarification; consumers must use the explicit counts meanwhile.

## 18. Request / quota ledger

### Nightwatch API

| Endpoint | Successful HTTP requests | Statuses | Paid units |
|---|---:|---|---:|
| `GET https://api.yehangshe.com/v1/openapi.json` | 1 | 200 | 0 |
| `GET https://api.yehangshe.com/v1/discover` | 4 | 200, 200, 200, 200 | 0 |
| `GET https://api.yehangshe.com/v1/options/contract-intraday/NVDA260821C00220000` | 2 | 200, 200 | 2 |
| `GET https://api.yehangshe.com/v1/options/contract-volume-profile/NVDA260821C00220000` | 2 | 200, 200 | 2 |
| **Total** | **9** | all successful HTTP responses were 200 | **4** |

There were zero HTTP retries and zero materialization follow-ups. Before the successful OpenAPI read, one sandboxed PowerShell attempt failed before receiving an HTTP response; it consumed no observed quota. The two bounded probe batches moved authenticated discover quota from 99,799 → 99,797 and 99,797 → 99,795 respectively.

No health, OI-change, chain, MAG7, Daily OI, Dealer/GEX, or unrelated paid endpoint was called.

### Public documentation URLs actually fetched

- `https://docs.yehangshe.com/llms.txt`
- `https://docs.yehangshe.com/volatility/iv-term-structure` (a search-discovery result; not used as capability authority)
- `https://docs.yehangshe.com/api-reference/intraday-1-minute-bars-for-a-single-option-contract-on-demand-materialization.md`
- `https://docs.yehangshe.com/api-reference/latest-day-volume-profile-for-a-single-option-contract-on-demand-materialization.md`
- `https://docs.yehangshe.com/api/domains/options.md`
- `https://docs.yehangshe.com/api/changelog.md`

Several direct browser opens were refused by the browser safety layer before an HTTP fetch; they are not counted as contacted URLs or Nightwatch requests.

## 19. Repository verification

The documentation-only change was verified without live calls from automated tests:

| Check | Result |
|---|---|
| Backend `python -m pytest` | 273 passed |
| Frontend `npm run lint` | passed |
| Frontend `npm run build` | passed |

Pytest emitted one sandbox warning because it could not write `.pytest_cache`; no test failed, and the warning did not affect application behavior.

## 20. Next step only

Run one deliberately timed, read-only temporal observation on a liquid exact contract at:

```text
T after close
T+1 after the vendor OI update but before 09:30 America/New_York
T+1 shortly after regular trading begins
```

Record only the returned session date, freshness, and rollover behavior, and request written vendor clarification for Premium units, quote-side classification, overlap semantics, and `truncated` versus `total_bars`. Use that result to freeze an archive specification. Do not build the archive or Flow Intent model until that follow-up gate is separately authorized.

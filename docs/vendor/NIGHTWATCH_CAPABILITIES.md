# Nightwatch Capabilities

Reviewed on 2026-08-10 from the official Nightwatch documentation and unauthenticated OpenAPI metadata. Runtime availability is account-specific: only an authenticated `GET /v1/discover` response is authoritative.

## Evidence labels

- **DOCUMENTED**: present in official docs and/or OpenAPI. This does not establish availability for this account.
- **DISCOVER-CONFIRMED**: returned as enabled/available by `/v1/discover` for the configured key.

An ignored local `.env` contained a configured key. Two zero-quota discovery reads were made: the first exposed the live envelope mismatch safely, and the second confirmed the capability detail shape. No account identity or secret value was retained or printed.

## Metadata contract

| Capability | Path | Evidence |
| --- | --- | --- |
| Health | `GET /v1/health` | DOCUMENTED; zero quota |
| Account capability registry | `GET /v1/discover` | DOCUMENTED and called; zero quota |
| OpenAPI 3.1 metadata | `GET /v1/openapi.json` | DOCUMENTED; zero quota; fetched successfully |

The fetched OpenAPI reported title `GEX Heatmap Data API` and version `0.2.0-dealer-mvp-registry`.

## Research capabilities

The requested entries below were both **DOCUMENTED** and **DISCOVER-CONFIRMED** on 2026-08-10. Availability must still be refreshed at runtime rather than treated as a permanent entitlement.

| Command / dataset | REST path | Notes |
| --- | --- | --- |
| `options.chain_snapshot` | `/v1/options/chain-snapshot/{ticker}` | DISCOVER-CONFIRMED; one required `expiration`; never all expirations in one call |
| `options.expiry_breakdown` | `/v1/options/expiry-breakdown/{ticker}` | DISCOVER-CONFIRMED |
| `options.oi_change` | `/v1/options/oi-change/{ticker}` | DISCOVER-CONFIRMED |
| `options.oi_per_expiry` | `/v1/options/oi-per-expiry/{ticker}` | DISCOVER-CONFIRMED |
| `options.oi_per_strike` | `/v1/options/oi-per-strike/{ticker}` | DISCOVER-CONFIRMED |
| `options.options_volume` | `/v1/options/options-volume/{ticker}` | DISCOVER-CONFIRMED |
| `options.volume_oi_per_expiry` | `/v1/options/volume-oi-per-expiry/{ticker}` | DISCOVER-CONFIRMED |
| `options.contract_daily` | `/v1/options/contract-daily/{contract}` | DISCOVER-CONFIRMED |
| `options.contract_intraday` | `/v1/options/contract-intraday/{contract}` | DISCOVER-CONFIRMED |
| `options.contract_greeks_series` | `/v1/options/contract-greeks-series/{contract}` | DISCOVER-CONFIRMED |
| `options.optionable_tickers` | `/v1/options/optionable-tickers` | DISCOVER-CONFIRMED |
| `volatility.iv_rank` | `/v1/volatility/iv-rank/{ticker}` | DISCOVER-CONFIRMED |
| `volatility.term_structure` | `/v1/volatility/term-structure/{ticker}` | DISCOVER-CONFIRMED |
| `volatility.anomaly` | `/v1/volatility/anomaly/{ticker}` | DISCOVER-CONFIRMED; vendor measure, not our final signal |
| `volatility.anomaly_top` | `/v1/volatility/anomaly-top` | DISCOVER-CONFIRMED |
| `market.oi_change` | `/v1/market/oi-change` | DISCOVER-CONFIRMED |

Runtime finding (2026-08-12): `volume-oi-per-expiry` returned `data.expiries[]` records
with `expiry`, total `volume`, and total `oi`, but no Call/Put split. The parser therefore
preserves side fields as null and scores only available concentration/neighbor evidence;
it never converts an unavailable side into zero.
| `market.movers` | `/v1/market/movers` | DISCOVER-CONFIRMED |
| Dealer GEX snapshot | `/v1/derived/dealer-gex/{ticker}/snapshot` | DISCOVER-CONFIRMED as `derived.dealer_gex_snapshot`; documented cost 1 unit |
| Dealer GEX history | `/v1/derived/dealer-gex/{ticker}/history` | DISCOVER-CONFIRMED as `derived.dealer_gex_history`; 1 unit/page |
| Dealer Heatmap snapshot | `/v1/derived/heatmap/{ticker}/snapshot` | DISCOVER-CONFIRMED as `derived.dealer_heatmap_snapshot`; 1 unit |
| Dealer Heatmap cell history | `/v1/derived/heatmap/{ticker}/cell-history` | DISCOVER-CONFIRMED as `derived.dealer_heatmap_cell_history`; 1 unit/page |

OpenAPI and discover also listed many adjacent datasets. They are not automatically included in Phase 1 scan scope; this table intentionally records only the capabilities requested for the product foundation.

At discovery time, response headers reported monthly quota limit `100000`, remaining `100000`, and account rate limit `60` requests/minute. The second response reported rate-limit remaining `59`. The quota reset header was `2026-09-01T00:00:00-04:00`. These observations are time-sensitive metadata, not configuration defaults.

## Quota and transport behavior

Official documentation describes a 100,000-unit monthly subscription quota and 60 account requests/minute, with a separate 200 requests/minute IP ceiling. Code does not assume those values: it captures `X-Quota-Limit`, `X-Quota-Remaining`, `X-Quota-Reset-At`, `X-RateLimit-Limit`, `X-RateLimit-Remaining`, `X-RateLimit-Reset`, `Retry-After`, and `X-Request-ID` at runtime.

Successful HTTP 200 data requests generally consume endpoint weight. Metadata endpoints above are documented weight zero. HTTP 429 is retryable with `Retry-After`; logical 4xx errors are not retried. Authorization headers are never included in usage records.

## Data caveats

- Open interest is lagged; it is not true real-time intraday position data and cannot identify whether a participant opened or closed.
- A chain snapshot requires one expiration.
- A first materialization may return 202; future orchestration should perform quota-aware, bounded follow-up without treating it as a signal.
- The API catalog evolves. Reconcile OpenAPI for shape and `/discover` for account authority rather than assuming undocumented paths.

## Official sources

- <https://docs.yehangshe.com/api/introduction>
- <https://docs.yehangshe.com/api/authentication>
- <https://docs.yehangshe.com/api/quota-and-rate-limits>
- <https://docs.yehangshe.com/api/catalog>
- <https://docs.yehangshe.com/api/domains/options>
- <https://docs.yehangshe.com/api/domains/volatility>
- <https://docs.yehangshe.com/api/domains/market>
- <https://docs.yehangshe.com/api/dealer-gex>
- <https://docs.yehangshe.com/api/dealer-heatmap-snapshot>
- <https://api.yehangshe.com/v1/openapi.json>

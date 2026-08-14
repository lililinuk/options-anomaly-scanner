# Phase 2B v3.1 Dealer/GEX Fresh Capture Recovery Gate

Date: 2026-08-14

Starting SHA: `b7955b6428b4a67eed52bc33325a1984e120b7fb`

Recovery implementation SHA: `5b8389894f0fd7c4a5f5e9b1cf39182d159285d3`

Final repository SHA: the docs-only commit containing this file is listed in the final handoff;
a Git commit cannot contain its own hash.

Specification: `signal_spec_v3.1_phase2b`

## Result

The recovery gate passed. Omitting the unvalidated `format=full` query parameter recovered the
existing Dealer/GEX archive transport for all seven MAG7 tickers. Every controlled response was
HTTP 200, `AVAILABLE`, non-truncated, and persisted through the accepted v3.1 archive path.

Operational classification:

`READY_FOR_SCHEDULED_ACCUMULATION`

This means the archive transport and persistence path are ready to accumulate new vendor
observations. It does not mean that the durable external scheduler has been configured. No
in-process scheduler was activated.

No migration, GEX structural rule, evolution state, Actionability logic, Phase 2A behavior, or
Phase 3 behavior was added or changed.

## Root cause

The accepted archive configuration set:

```text
DealerGexArchiveConfig.endpoint_format = "full"
```

`DealerGexArchiver._capture_ticker` then unconditionally constructed:

```text
params={"format": self.config.endpoint_format}
```

and recorded raw evidence under an endpoint ending in `?format=full`. This is why the previous
controlled URLs contained that query parameter. The live vendor endpoint rejected the request with
HTTP 400 `VALIDATION_ERROR`.

A second compatibility issue was found in the archive normalizer: it reused the Phase 2B context
normalizer, which required both `cells` and `row_stacks`. The demonstrated valid default payload
contains `cells` but does not require `row_stacks`.

The recovery changes are limited to:

- `endpoint_format` now defaults to null configuration state meaning “omit the parameter”;
- transport passes `params=None`, not an empty/null format value;
- raw evidence records the endpoint without a query string;
- archive-specific normalization accepts the verified cells-only response shape;
- the request profile and surface schema identity are versioned as
  `nightwatch_dealer_heatmap_default_v1` under config `2026-08-14.v3.1.1`.

No alternative format enum value was guessed.

## Request before and after

Before:

```text
GET /v1/derived/heatmap/{ticker}/snapshot?format=full
```

After:

```text
GET /v1/derived/heatmap/{ticker}/snapshot
```

The production request sends no `format` key at all. It does not send `format=full`, an empty
string, or null.

## Normalization semantics

The verified response shape is accepted directly:

```text
data:
  ticker
  generated_at
  session_date_et
  spot_usd
  expirations[]
  cells[]:
    strike_usd
    expiration
    net_dealer_gex_usd
_meta:
  request_id
  cache_hit
  data_freshness_seconds
  truncated
  rate_limit_remaining
  quota_remaining_pct
```

`data.generated_at` remains the analytical observation timestamp. Local `captured_at` remains
transport provenance only. Missing Call/Put GEX fields remain SQL NULL; they are not required for a
usable net-GEX surface. Numeric zero remains zero.

`_meta.truncated=false` is preserved as an explicit completeness fact. `true` remains unusable. A
missing or invalid truncation flag is distinguishable and produces degraded quality rather than
silently becoming false.

## Controlled NVDA validation

Archive run: `20cd7e65-9bcf-48a6-8593-82a41c222800`

| Field | Result |
|---|---|
| Request | `GET /v1/derived/heatmap/NVDA/snapshot` |
| HTTP | 200 |
| Vendor generated_at | `2026-08-13T19:55:00Z` |
| session_date_et | `2026-08-13` |
| Spot | `225.33` |
| Expirations | 11 |
| Cells | 220 |
| truncated | false |
| Source quality | `AVAILABLE` |
| Analytical result | new snapshot persisted |
| Network attempts | 1 |
| Retries | 0 |
| Paid units | 1 |
| Quota limit | 100000 |
| Quota before / after | 99814 / 99813 |
| Rate limit / remaining | 60 / 59 |

Because NVDA succeeded and read-back passed, the gate continued to the remaining six tickers. NVDA
was not called again.

## Remaining MAG7 validation

Archive run: `38373138-5a56-4ff5-9d9d-f61f56847e90`

| Ticker | HTTP | generated_at | Session | Spot | Expirations | Cells | Truncated | Quality | Result | Quota after |
|---|---:|---|---|---:|---:|---:|---|---|---|---:|
| AAPL | 200 | 2026-08-13T19:55:00Z | 2026-08-13 | 305.24 | 12 | 240 | false | AVAILABLE | new | 99812 |
| MSFT | 200 | 2026-08-13T19:55:00Z | 2026-08-13 | 496.84 | 12 | 240 | false | AVAILABLE | new | 99811 |
| AMZN | 200 | 2026-08-13T19:55:00Z | 2026-08-13 | 265.08 | 12 | 238 | false | AVAILABLE | new | 99810 |
| META | 200 | 2026-08-13T19:55:00Z | 2026-08-13 | 594.86 | 12 | 240 | false | AVAILABLE | new | 99809 |
| GOOGL | 200 | 2026-08-13T19:55:00Z | 2026-08-13 | 346.32 | 12 | 240 | false | AVAILABLE | new | 99808 |
| TSLA | 200 | 2026-08-13T19:55:00Z | 2026-08-13 | 340.03 | 12 | 240 | false | AVAILABLE | new | 99807 |

The six-ticker pass used six network attempts, zero retries, and six paid units.

## Persistence read-back

- Successful analytical snapshots added: 7.
- Distinct analytical observation identities: 7.
- Normalized cells added: 1,658.
- Call GEX NULL cells: 1,658.
- Put GEX NULL cells: 1,658.
- Source quality: 7 `AVAILABLE`, 0 degraded, 0 truncated.
- Raw payloads preserved: 7.
- Persisted raw endpoints with query strings: 0.
- Persisted endpoint-parameter objects: seven empty objects.
- Previous HTTP 400 unavailable snapshots retained: 7.
- Total current archive attempt snapshots across the failed and recovered gates: 14.

No duplicate live request was made to test replay. Automated idempotency tests prove that repeated
captures with the same ticker, vendor `generated_at`, and versioned request profile reuse the
existing analytical identity and do not increase history coverage.

## History API read-back

Persisted-only route:

```text
GET /api/v1/dealer-gex/history
```

returned HTTP 200 and `unavailable_is_zero=false`.

| Ticker | Distinct valid | First observation | Latest observation | Usable | Degraded | Unavailable attempts |
|---|---:|---|---|---:|---:|---:|
| AAPL | 1 | 2026-08-13T19:55:00Z | 2026-08-13T19:55:00Z | 1 | 0 | 1 |
| MSFT | 1 | 2026-08-13T19:55:00Z | 2026-08-13T19:55:00Z | 1 | 0 | 1 |
| NVDA | 1 | 2026-08-13T19:55:00Z | 2026-08-13T19:55:00Z | 1 | 0 | 1 |
| AMZN | 1 | 2026-08-13T19:55:00Z | 2026-08-13T19:55:00Z | 1 | 0 | 1 |
| META | 1 | 2026-08-13T19:55:00Z | 2026-08-13T19:55:00Z | 1 | 0 | 1 |
| GOOGL | 1 | 2026-08-13T19:55:00Z | 2026-08-13T19:55:00Z | 1 | 0 | 1 |
| TSLA | 1 | 2026-08-13T19:55:00Z | 2026-08-13T19:55:00Z | 1 | 0 | 1 |

## Quota ledger

- Total live requests: 7.
- Total network attempts: 7.
- Total retries: 0.
- Paid units consumed: 7.
- Quota limit: 100000.
- Pre-validation remaining: 99814.
- Post-validation remaining: 99807.
- Rate limit: 60; each returned response reported 59 remaining.
- Vendor `_meta.quota_remaining_pct`: 99.8%.
- Vendor `_meta.cache_hit`: false for every response.

## Nightwatch call ledger

Exactly these seven endpoints were called, once each and without query parameters:

1. `https://api.yehangshe.com/v1/derived/heatmap/NVDA/snapshot`
2. `https://api.yehangshe.com/v1/derived/heatmap/AAPL/snapshot`
3. `https://api.yehangshe.com/v1/derived/heatmap/MSFT/snapshot`
4. `https://api.yehangshe.com/v1/derived/heatmap/AMZN/snapshot`
5. `https://api.yehangshe.com/v1/derived/heatmap/META/snapshot`
6. `https://api.yehangshe.com/v1/derived/heatmap/GOOGL/snapshot`
7. `https://api.yehangshe.com/v1/derived/heatmap/TSLA/snapshot`

No other Nightwatch endpoint was contacted. Automated tests made no live calls.

## Tests and quality gates

- Affected archive/normalization/API/no-lookahead suite: 44 passed.
- Full backend suite: 254 passed.
- Ruff: all checks passed using `--no-cache` because the pre-existing cache directory is not
  writable in the sandbox.
- NVDA dry-run: passed with zero network attempts, zero paid units, and zero persistence writes.
- PostgreSQL snapshot/cell/raw/API-usage read-back: passed.
- Persisted-only FastAPI history read-back: HTTP 200, passed.
- Alembic current/head: `20260814_0012` / `20260814_0012`.
- New migration: none.
- Frontend code changed: no; frontend rebuild was not required by this gate.

Regression coverage proves:

- the default request path omits `format` entirely;
- neither the outbound request nor raw endpoint contains `?format=full`;
- cells-only payloads are accepted without `row_stacks`;
- Call/Put GEX absence remains null;
- numeric zero remains zero;
- explicit false, true, and missing truncation states remain distinct;
- vendor `generated_at` controls analytical identity;
- same observation replay is idempotent;
- no-lookahead requires both vendor and capture timestamps at/before candidate evaluation;
- ticker failures remain isolated.

## Security

- `.env` remains Git-ignored.
- Exact local database URL/API-key matches in tracked files: 0.
- Exact secret matches in frontend: 0.
- Direct frontend Nightwatch references: 0.
- Persisted Authorization-header fields/references: 0.
- No credential, database URL, password, API key, or Authorization value appears in CLI output or
  this report.

## Scheduler status

Transport classification: `READY_FOR_SCHEDULED_ACCUMULATION`.

The documented target remains 15:30 `America/New_York`, once per valid XNYS session. The external
durable scheduler is not configured or activated by this repository task. No in-process scheduler
was added.

## Open issues

1. Each ticker currently has only one valid vendor observation, so no time-series evolution can be
   calibrated yet.
2. External scheduler deployment remains an operational prerequisite.
3. GEX Evolution Calibration, Actionability, and Phase 3 remain explicitly out of scope.

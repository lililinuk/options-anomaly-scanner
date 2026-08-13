# Phase 2A v1.3 Implementation Report

Date: 2026-08-13
Specification: `signal_spec_v1.3_phase2a`
Scope: three-route discovery, contract-event-first dashboard, and daily Activity/Radar archive. No
Phase 2B, BUY/SELL, directional inference, lifecycle inference, GEX trading logic, or Tradeability
Score was added.

## Git

- Implementation starting SHA: `8258157518abec2f9b2dd7468a28c9e1bab4350c`.
- The preceding diagnostic document was closed in documentation-only commit
  `8258157518abec2f9b2dd7468a28c9e1bab4350c`.
- Final implementation commit SHA: recorded in the completion response after this report is
  committed.
- Accepted v1.0/v1.1/v1.2 history and prior migrations were not rewritten.

## Specification and three-route architecture

The v1.3 primary workflow persists/exposes independent route states for `RADAR_EVENT`,
`PERSISTENT_POSITIONING`, and `EXPIRY_ACTIVITY`, plus explicit `STRUCTURAL_COLD_START`. Route
priority governs presentation and finite chain-analysis resources only. The system neither averages
the routes nor produces a cross-route conviction score. Historical v1.2 Discovery Score data remains
available under its original specification but is absent from the primary v1.3 dashboard.

Deep Dive selection accepts any route. A `(ticker, expiration)` is selected once and retains all
trigger sources, so multiple Radar contracts, expiry activity, and persistence do not reload the same
archived chain.

## Radar Material Event and threshold versioning

The initial active server-side profile is:

```yaml
profile_id: radar_material_event
version: 2026-08-13.v1
enabled: true
min_premium_usd: 150000
min_abs_oi_diff: 2500
calibration_review_sessions: 20
```

The evaluator accepts a `RadarThresholdProfile`; it contains no Premium or OI numeric threshold.
Runtime values come from environment-backed Settings. Every daily run and Radar observation stores:

- profile ID and immutable version;
- complete effective values as JSON;
- deterministic configuration hash.

Consequently, activating a later profile never rewrites historical eligibility. JSON snapshots allow
future profile-specific threshold fields without a schema redesign. The 2,500 threshold is documented
as a rounded diagnostic calibration from p75 absolute OI Diff ≈2,648, not a universal market truth;
review is required after at least 20 distinct valid Radar sessions.

Relative OI Change is display context only. `LOW_OI_BASE` is retained for `previous_oi < 100`.
Archive joins use exact contract-symbol equality only. Unmatched events remain visible as `UNJOINED`;
incomplete chains cannot produce complete-universe structure. Exact complete 0–90 DTE events may
enter Deep Dive, 91–180 DTE is `LONG_DTE_RADAR_WATCH`, and outside-scope/unmatched events remain
evidence without fabricated metadata.

## Daily data pipeline

`python -m app.cli archive-mag7-daily` is the external-scheduler entry point for three isolated
logical jobs:

1. backwards-compatible Daily OI Archive;
2. MAG7 `expiry_breakdown` + `options_volume` Activity Snapshot;
3. MAG7 `oi_change` Radar coverage.

Each subjob records truthful independent status; a failure yields `PARTIAL` when other work succeeds.
Activity uniqueness is ticker + expiration + New York observation session. Radar uniqueness is
ticker + exact contract symbol + vendor observation date. Coverage rows allow safe missing-ticker
backfill. Capture timestamp, vendor date/as-of, and New York market date are distinct fields. No
in-process scheduler, Redis, or Celery was introduced; documented scheduling remains Asia/Singapore
12:00 through an external durable scheduler.

The controlled helper `python -m app.cli backfill-mag7-radar` locally evaluates accepted persisted
Radar evidence before fetching only missing latest-date ticker coverage. Interactive
`run-mag7-scan` reuses the latest persisted Radar and makes no `oi_change` call.

## Persistent Positioning and Expiry Activity

Accepted v1.2 formulas and thresholds remain unchanged. Contract Persistent eligibility is 65 with
valid history. Fewer than three OI observations remains NULL and is displayed as collection progress,
not zero. Build/decline wording is non-directional.

Same-Day Expiry Activity keeps the v1.2 threshold of 40 and existing 0DTE/non-0DTE calibration.
Third-Friday `Monthly OPEX` is explicitly `INFERRED`, weight zero. Score Basis exposes Volume Share
Points, Neighbor Points, and `VOLUME_SHARE_DOMINATED` / `NEIGHBOR_DOMINATED` / `BALANCED`; it does
not change the numerical Same-Day score.

## Dashboard and field guide

The fixed browser → Next.js `/api/mag7-scan` → FastAPI path now renders:

1. Latest Contract Events (top 15 by Premium then absolute ΔOI; inspect-all plus ticker, Premium,
   absolute ΔOI, DTE, and right filters);
2. Persistent Positioning;
3. Unusual Expiry Activity;
4. Deep Dive / Research Candidates with transparent trigger sources.

Unjoined and incomplete Radar evidence remains visible. The dashboard states that Premium is
aggregate contract activity evidence, not proof of one order. The zh-TW field guide includes Radar
Material Event, Premium, ΔOI, relative OI Change, Persistent Positioning, Expiry Activity, Monthly
OPEX, Score Basis, Trigger Sources, Radar archive matching, and threshold profile versioning.

Browser QA confirmed all four headings, default filters 150,000/2,500, populated Radar rows,
`UNJOINED`, exact-joined DTE/right/strike, OPEX badges, Neighbor-dominated labels, no universal
Discovery Score heading, and no console errors. Browser code contains no Nightwatch host/key and the
observed server log contained only our FastAPI status/latest routes.

## Database

- PostgreSQL dialect confirmed: `postgresql` / Alembic `PostgresqlImpl`.
- Migration applied: `20260812_0007 -> 20260813_0008`.
- Alembic current/head: `20260813_0008 (head)`.
- New tables verified: `daily_collection_runs`, `daily_collection_coverage`,
  `daily_expiry_activity_snapshots`.
- Route/config/join fields were added without modifying old migrations or old specification rows.

## Controlled validation

### Radar-only backfill

- Vendor observation date: 2026-08-12.
- Coverage: 50 rows each for AAPL, AMZN, GOOGL, META, MSFT, NVDA, TSLA; 350 latest-date rows.
- Only missing coverage was requested: NVDA, META, TSLA once each.
- Material Events: 68.
- Exact archive matches: 46.
- 0–90 DTE Deep Dive eligible: 46.
- 91–180 DTE watch: 0.
- Unmatched: 22.
- Incomplete-chain cases: 0.

Top 15 by Premium (USD), with ΔOI / OI Change / Volume / Trades:

| # | Ticker | Contract | Premium | ΔOI | OI Change | Volume | Trades | Scope |
|---:|---|---|---:|---:|---:|---:|---:|---|
| 1 | TSLA | TSLA260812C00335000 | 38,075,053 | 5,978 | 147.02% | 138,392 | 38,333 | Full Deep Dive |
| 2 | NVDA | NVDA261016P00220000 | 28,822,280 | 20,068 | 59.03% | 20,817 | 239 | Full Deep Dive |
| 3 | NVDA | NVDA260812C00220000 | 21,935,903 | 10,539 | 97.84% | 162,316 | 29,232 | Unjoined |
| 4 | NVDA | NVDA260812P00217500 | 21,457,297 | 8,720 | 154.23% | 160,227 | 30,687 | Unjoined |
| 5 | TSLA | TSLA260812P00335000 | 21,129,124 | 4,545 | 1,171.39% | 46,668 | 7,876 | Full Deep Dive |
| 6 | TSLA | TSLA260812C00332500 | 20,880,082 | 3,126 | 182.17% | 59,995 | 16,951 | Full Deep Dive |
| 7 | TSLA | TSLA261016P00330000 | 18,907,634 | 5,802 | 125.99% | 9,232 | 155 | Unjoined |
| 8 | AAPL | AAPL271217C00310000 | 16,430,134 | 3,549 | 140.61% | 3,667 | 193 | Unjoined |
| 9 | NVDA | NVDA260904C00215000 | 16,272,340 | 3,344 | 83.33% | 14,008 | 484 | Full Deep Dive |
| 10 | NVDA | NVDA260812C00217500 | 14,787,895 | 3,836 | 36.15% | 71,887 | 13,128 | Unjoined |
| 11 | TSLA | TSLA260814C00335000 | 14,541,482 | 2,665 | 18.59% | 32,065 | 8,238 | Full Deep Dive |
| 12 | NVDA | NVDA260812P00220000 | 13,848,923 | 3,439 | 63.01% | 58,602 | 12,495 | Unjoined |
| 13 | TSLA | TSLA260812C00340000 | 12,170,468 | 5,470 | 115.99% | 91,758 | 27,702 | Full Deep Dive |
| 14 | NVDA | NVDA260812C00222500 | 10,499,935 | 14,657 | 72.94% | 132,859 | 23,730 | Unjoined |
| 15 | NVDA | NVDA260821C00220000 | 10,434,044 | 4,531 | 7.21% | 24,458 | 2,887 | Full Deep Dive |

### Controlled v1.3 interactive scan

- Run: `19e04fae-4d43-4760-961d-f528ebf6bd84`, status `PARTIAL` due accepted archive
  completeness/data truth, not a hidden failure.
- Requests: 7 `expiry_breakdown`, 7 `options_volume`, 0 `oi_change`, 0 chain archive.
- Route candidates: Radar-only 3, Expiry-Activity-only 8, multiple routes 7,
  Structural-Cold-Start-only 8, Persistent-only 0 (history is insufficient; not manufactured).
- Unique route candidates: 26 expiries across 7 tickers; 17 eligible contracts.
- Deep Dive chain loads: 10 unique selected ticker/expiry pairs; deduplicated loads: 10.
- Contracts analyzed from archived chains: 1,826; clusters: 5.

Current inferred monthly expiry 2026-08-21 retained its original Same-Day scores. Examples:

| Ticker | Same-Day | Volume Share Points | Neighbor Points | Basis | OPEX |
|---|---:|---:|---:|---|---|
| AAPL | 61.898 | 21.898 | 40.000 | NEIGHBOR_DOMINATED | INFERRED |
| AMZN | 67.287 | 27.287 | 40.000 | NEIGHBOR_DOMINATED | INFERRED |
| GOOGL | 66.726 | 26.726 | 40.000 | NEIGHBOR_DOMINATED | INFERRED |
| META | 64.056 | 24.056 | 40.000 | NEIGHBOR_DOMINATED | INFERRED |
| MSFT | 75.626 | 35.626 | 40.000 | BALANCED | INFERRED |
| NVDA | 44.256 | 19.326 | 24.930 | BALANCED | INFERRED |
| TSLA | 52.754 | 12.754 | 40.000 | NEIGHBOR_DOMINATED | INFERRED |

OPEX context changed no score.

## Nightwatch call ledger and quota

Actual calls during controlled validation:

- `/v1/options/oi-change/NVDA`: 1
- `/v1/options/oi-change/META`: 1
- `/v1/options/oi-change/TSLA`: 1
- `/v1/options/expiry-breakdown/{ticker}`: 7 (one per MAG7)
- `/v1/options/options-volume/{ticker}`: 7 (one per MAG7)

No chain snapshot, OI-per-expiry, contract-intraday, contract-daily, metadata, or other Nightwatch
endpoint was called. Radar backfill consumed 3 paid units; interactive activity validation consumed
14. Quota moved from inferred 99,872 before Radar backfill to 99,869, then to 99,855 after activity
validation. Network attempts and paid units were both 17 total; no retries occurred.

## Quality and security

- Ruff: pass.
- v1.3 tests: 17 passed; full backend suite reached 152/152 passed assertions (100%). On this Windows
  host, the Python process remained alive after pytest completion and the command wrapper timed out;
  no test failed, and this teardown/process-exit issue is recorded below.
- Frontend ESLint: pass.
- Frontend production build: pass.
- Glossary completeness: 20 legacy visible columns and 91 documented fields; pass.
- PostgreSQL read-back and Alembic current/head: pass.
- Browser dashboard QA: pass.
- `.env` remains ignored. Search found only placeholder variables in `.env.example`.
- No real DATABASE_URL, Nightwatch key, Authorization header, or frontend secret is committed or
  persisted. Browser calls only same-origin Next.js proxies; FastAPI status/latest routes contact no
  vendor.

## Open issues

1. The Windows test environment completes all 152 assertions but its Python process does not exit
   before the command timeout. This appears to be an environment/plugin teardown issue; it does not
   change assertion results, but should be isolated before CI adopts this exact Windows environment.
2. The controlled scan remains `PARTIAL` where accepted archive completeness is partial; unknown data
   remains unknown and was not coerced to complete.
3. Persistent-only contract candidates remain zero because the available complete OI history is still
   insufficient. The dashboard reports collection progress instead of inventing results.

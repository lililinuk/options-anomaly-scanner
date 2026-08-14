# Phase 2B v3.1 Dealer/GEX Time-Series Archive — Implementation Report

Date: 2026-08-14

Starting commit: `6fcde7a6b4c43fcc4e449598ad439dc101897f5f`

Implementation commit: `571cb55521b3b2385c6641c90467284890de6074`

Specification: `signal_spec_v3.1_phase2b`

## Outcome

Phase 2B v3.1 的 production archive infrastructure 已完成並套用到真實 development PostgreSQL。
系統現在可以用 append-only、vendor-time-aware 的模型保存完整 multi-expiry Dealer/GEX surface，
逐 ticker 隔離失敗，並讓新的 v3.1 candidate workspace 在 no-lookahead 規則下選擇適用 snapshot。

唯一一次 controlled fresh MAG7 capture 依規格執行，但 Nightwatch 對七個 ticker 全部回傳 HTTP
400 `VALIDATION_ERROR`。因此本次沒有建立任何可用 GEX surface、沒有 snapshot cells，也沒有假裝
time-series baseline 已存在。HTTP 400 responses 未消耗 paid quota。

本次沒有實作 Actionability Score、BUY/SELL、buyer/seller flow inference、GEX 方向分數、
BUILDING/DECAYING/MIGRATING production state、Phase 3，亦未改變 Phase 2A selection/scoring。

## Git

- Starting SHA: `6fcde7a6b4c43fcc4e449598ad439dc101897f5f`
- Implementation SHA: `571cb55521b3b2385c6641c90467284890de6074`
- Report docs-only commit: 本檔提交後於最終 handoff 列出；Git commit 不能自我包含自己的 SHA。
- Accepted history was not rewritten.
- Production implementation changed 22 files and added one Alembic revision.

## Specification and preserved history

- Active additive spec: `signal_spec_v3.1_phase2b`.
- `signal_spec_v3.0_phase2b` workspaces remain immutable historical evidence.
- V3.1 workspace uniqueness remains source v2 state plus specification version, so v3.1 appends a
  new row and does not update v3.0.
- Dealer/GEX structural rules and their anchor-expiry plus nearest-previous/nearest-next scope remain
  unchanged.

Documentation:

- `docs/specifications/SIGNAL_SPECIFICATION_PHASE2B_V3_1.md`
- `docs/specifications/PHASE2B_V31_ORCHESTRATION.md`

## Archive architecture

Added separated modules for:

- XNYS trading-session planning;
- versioned archive configuration;
- strict full-surface normalization and source quality;
- append-only PostgreSQL persistence/read-back;
- sequential, budget-bounded Nightwatch orchestration.

Source qualities are:

- `AVAILABLE`
- `AVAILABLE_DEGRADED`
- `INCOMPLETE_OR_TRUNCATED`
- `UNAVAILABLE`

Only the first two qualities may persist analytical cells. Numeric zero is preserved; missing
Call/Put/net GEX remains null. Truncated, malformed, timestamp-less, and unavailable payloads never
become zero surfaces.

## Database and migration

- Database engine verified: PostgreSQL 17.6.
- Migration applied: `20260814_0011 -> 20260814_0012`.
- Alembic current: `20260814_0012 (head)`.
- Alembic head: `20260814_0012 (head)`.
- Alembic drift check: `No new upgrade operations detected.`

New tables verified by PostgreSQL inspection:

1. `dealer_gex_archive_runs`
2. `dealer_gex_snapshots`
3. `dealer_gex_snapshot_cells`

Verified uniqueness:

- run: `ny_market_date + intended_capture_slot + scope_key`;
- analytical snapshot: versioned `observation_identity`;
- per-run attempt: `archive_run_id + ticker`;
- cell: `snapshot_id + expiration + strike`.

Analytical identity hashes ticker, actual vendor observation timestamp, `format=full`, and the
versioned surface schema. It is not ticker plus calendar date, so future independent intraday slots
remain possible. A replay of the same vendor observation cannot count as a second analytical point.

## Schedule and CLI

Command:

```text
python -m app.cli capture-dealer-gex-archive
python -m app.cli capture-dealer-gex-archive --ticker NVDA
python -m app.cli capture-dealer-gex-archive --dry-run
python -m app.cli capture-dealer-gex-archive --scheduled
```

Configured schedule target is `15:30 America/New_York`, once per XNYS trading session. No
in-process scheduler was added. Deployment must invoke the CLI through a durable external
scheduler. XNYS holidays/weekends are skipped. If 15:30 is after an early close, the run records
`SKIPPED_TARGET_AFTER_EARLY_CLOSE`.

Dry-run validation result:

- session status: `DRY_RUN_READY`;
- MAG7 tickers planned: 7;
- network attempts: 0;
- paid units: 0;
- database writes: 0.

## Failure handling and quota ledger

- Capture order: AAPL, MSFT, NVDA, AMZN, META, GOOGL, TSLA.
- Concurrency: 1.
- Retries: 0.
- Maximum network attempts: 7 for the default MAG7 run.
- Maximum consumed paid units: 7 for the default MAG7 run.
- A ticker failure is committed as an explicit unavailable attempt and processing continues.
- Successful earlier tickers would not be rolled back by a later vendor failure.
- Authorization headers are never passed to the persistence layer.

`api_usage_audit` retains endpoint, request time, HTTP status, latency, quota/rate metadata where
supplied, safe request IDs, attempt count, retry count, and consumed-quota semantics.

## Controlled fresh MAG7 capture

Archive run ID: `4f7a068d-2461-49e6-a200-9b185fad688d`

Request shape for every ticker:

```text
GET /v1/derived/heatmap/{ticker}/snapshot?format=full
```

| Ticker | HTTP | Quality | Safe error | Vendor timestamp | Expiries | Cells | Attempts | Retries | Paid units |
|---|---:|---|---|---|---:|---:|---:|---:|---:|
| AAPL | 400 | UNAVAILABLE | VALIDATION_ERROR | unavailable | 0 | 0 | 1 | 0 | 0 |
| MSFT | 400 | UNAVAILABLE | VALIDATION_ERROR | unavailable | 0 | 0 | 1 | 0 | 0 |
| NVDA | 400 | UNAVAILABLE | VALIDATION_ERROR | unavailable | 0 | 0 | 1 | 0 | 0 |
| AMZN | 400 | UNAVAILABLE | VALIDATION_ERROR | unavailable | 0 | 0 | 1 | 0 | 0 |
| META | 400 | UNAVAILABLE | VALIDATION_ERROR | unavailable | 0 | 0 | 1 | 0 | 0 |
| GOOGL | 400 | UNAVAILABLE | VALIDATION_ERROR | unavailable | 0 | 0 | 1 | 0 | 0 |
| TSLA | 400 | UNAVAILABLE | VALIDATION_ERROR | unavailable | 0 | 0 | 1 | 0 | 0 |

Aggregate result:

- run status: `PARTIAL`;
- tickers attempted: 7;
- tickers succeeded: 0;
- tickers failed: 7;
- network attempts: 7;
- retries: 0;
- paid units consumed: 0;
- quota before/after: unavailable because the 400 responses did not supply quota-remaining
  metadata;
- snapshots persisted: 7 unavailable attempts;
- analytical observations: 0;
- snapshot cells: 0.

Prior preserved Phase 2B context showed an older NVDA `AVAILABLE_DEGRADED` heatmap with a vendor
timestamp and 771 normalized cells. The fresh NVDA request returned HTTP 400, so there are not two
distinct successful v3.1 archive snapshots to compare. No GEX evolution or level-change claim is
made.

## History coverage and diagnostic API

Added persisted read route:

```text
GET /api/v1/dealer-gex/history
```

It never calls Nightwatch. Real PostgreSQL-backed FastAPI read-back returned:

| Ticker | Distinct valid observations | Unavailable attempts |
|---|---:|---:|
| AAPL | 0 | 1 |
| MSFT | 0 | 1 |
| NVDA | 0 | 1 |
| AMZN | 0 | 1 |
| META | 0 | 1 |
| GOOGL | 0 | 1 |
| TSLA | 0 | 1 |

The response explicitly reports `unavailable_is_zero=false`. No analytical dashboard behavior or
frontend vendor transport was added.

## Candidate workspace temporal rules

New v3.1 workspaces select the latest usable archive snapshot only if both the vendor observation
timestamp and local capture timestamp are no later than the candidate evaluation timestamp. This
prevents look-ahead. The selected snapshot/raw/request/timestamps are preserved in provenance.

If no temporally eligible archive snapshot exists, the preserved source-aligned ticker context is
used. Even though the archive stores a complete multi-expiry surface, current candidate analysis
still uses only anchor plus nearest previous/next expiration.

## Tests and quality gates

- Backend: `252 passed`.
- Ruff: `All checks passed!` using `--no-cache` because the pre-existing cache directory is not
  writable in the sandbox.
- Alembic current/head: `20260814_0012` / `20260814_0012`.
- Alembic autogenerate drift: none.
- PostgreSQL schema/read-back: passed.
- Archive dry-run: passed with 0 calls/0 units.
- Real archive read-back: passed for 1 run, 7 attempt snapshots, 0 cells.
- FastAPI history read-back: passed.
- Frontend ESLint: passed.
- Frontend production build: passed (Next.js 16.3.0; 7 routes generated).
- Automated live Nightwatch calls: 0; fixtures/mocks enforce this.

Tests cover source-quality normalization, real zero versus null, timestamp authority, truncation,
malformed cells, replay identity, database uniqueness, XNYS weekend/early-close behavior,
no-lookahead selection, anchor/adjacent scope, partial vendor failure, sequential attempts, zero
retries, dry-run side effects, and persisted-only API diagnostics.

## Nightwatch call ledger

Exactly seven Nightwatch requests were made, once each:

1. `https://api.yehangshe.com/v1/derived/heatmap/AAPL/snapshot?format=full`
2. `https://api.yehangshe.com/v1/derived/heatmap/MSFT/snapshot?format=full`
3. `https://api.yehangshe.com/v1/derived/heatmap/NVDA/snapshot?format=full`
4. `https://api.yehangshe.com/v1/derived/heatmap/AMZN/snapshot?format=full`
5. `https://api.yehangshe.com/v1/derived/heatmap/META/snapshot?format=full`
6. `https://api.yehangshe.com/v1/derived/heatmap/GOOGL/snapshot?format=full`
7. `https://api.yehangshe.com/v1/derived/heatmap/TSLA/snapshot?format=full`

No discover, health, OpenAPI, chain, scan, paid option-data, or other Nightwatch endpoint was called
during this task.

## Security

- `.env` remains Git-ignored.
- Exact local `DATABASE_URL` and Nightwatch secret fingerprint matches in tracked files: 0.
- Exact secret matches in frontend: 0.
- Frontend direct Nightwatch URL/endpoint references: 0.
- Persisted Authorization-header fields/references: 0.
- CLI and report contain no database URL, password, API key, or Authorization value.

## Open issues

1. The controlled fresh request shape that previously produced an NVDA surface now returns HTTP
   400 `VALIDATION_ERROR` for all MAG7 tickers. Vendor/account behavior must be clarified before a
   valid time-series baseline can begin.
2. History coverage is therefore 0 valid observations per ticker. This is a truthful cold-start,
   not a zero GEX surface.
3. The durable 15:30 America/New_York external scheduler is documented but must be configured in
   deployment infrastructure; no unsafe in-process scheduler was activated.
4. Future labels, GEX evolution research, Actionability, and Phase 3 remain deliberately blocked
   behind a later calibration gate.

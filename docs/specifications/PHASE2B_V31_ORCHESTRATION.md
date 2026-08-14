# Phase 2B v3.1 Dealer/GEX Archive Orchestration

Specification: `signal_spec_v3.1_phase2b`

## Durable schedule

The backend does not start an in-process scheduler. A durable external scheduler must invoke:

```text
python -m app.cli capture-dealer-gex-archive --scheduled
```

once per XNYS trading session at approximately `15:30 America/New_York`. The configured clock is a
trigger; the vendor `generated_at` timestamp is the observation authority. The job uses the XNYS
exchange calendar. Weekends and exchange holidays are skipped. When 15:30 is later than an early
session close, the run records `SKIPPED_TARGET_AFTER_EARLY_CLOSE` rather than manufacturing a
capture after the close.

Example cron configuration (the scheduler must support `CRON_TZ`):

```text
CRON_TZ=America/New_York
30 15 * * 1-5 cd /deployment/options-anomaly-scanner/backend && python -m app.cli capture-dealer-gex-archive --scheduled
```

The exchange-calendar gate remains authoritative even though cron is weekday-based. Disable
overlap and monitor the command exit code. Do not add Celery, Redis, or an application background
thread solely for this archive.

## Manual and diagnostic use

```text
python -m app.cli capture-dealer-gex-archive
python -m app.cli capture-dealer-gex-archive --ticker NVDA
python -m app.cli capture-dealer-gex-archive --dry-run
```

Manual and scheduled executions share the same normalization and persistence path. `--dry-run`
checks the XNYS session plan and produces no database or network side effect. Ticker arguments are
restricted to the configured MAG7 universe.

## Failure and budget semantics

Tickers are attempted sequentially once, with `max_retries=0` and `max_concurrency=1`. One ticker
failure is recorded as unavailable and does not roll back successful ticker snapshots. The job
stops before its configured network-attempt or paid-unit bound and marks unattempted tickers
explicitly. API usage auditing stores endpoint, status, latency, quota/rate metadata, request IDs,
and attempt counts; it never stores an Authorization header.

The intended slot plus market date plus capture scope makes a run invocation idempotent. A replayed
vendor timestamp/surface identity also reuses its existing analytical snapshot, so it cannot count
as another time-series observation.

## Read paths

```text
Nightwatch full Dealer heatmap
  -> raw_vendor_payloads
  -> dealer_gex_archive_runs
  -> dealer_gex_snapshots
  -> dealer_gex_snapshot_cells
  -> GET /api/v1/dealer-gex/history
```

The history route reads PostgreSQL only. It is a small operational diagnostic, not an analytical
dashboard model, and never triggers Nightwatch transport.

For a new candidate workspace:

```text
eligible archived snapshot at/before candidate source time
  -> anchor expiry + nearest previous/next only
  -> immutable signal_spec_v3.1_phase2b workspace
```

No historical v3.0 workspace is rewritten.

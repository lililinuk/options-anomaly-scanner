# Scan Orchestration — Phase 2A v1.2

Specification: `signal_spec_v1.2_phase2a`

## Workflow A — Daily OI Archive

CLI: `python -m app.cli archive-mag7-oi`

The archive is an idempotent backend job protected by a PostgreSQL advisory lock. Configuration is
enabled at `Asia/Singapore` 12:00 with max DTE 180, but the repository deliberately contains no
in-process scheduler: deployment must invoke the CLI once daily using a durable external scheduler.
The trigger clock does not define data dates.

For each MAG7 ticker the job:

1. requests `oi-per-expiry` and reads its vendor date/as-of;
2. skips as `NO_NEW_VENDOR_OI_SNAPSHOT` when that ticker/date already exists;
3. writes the complete 0–180 DTE expiry OI surface and side/total shares;
4. requests one chain snapshot per scoped expiration;
5. accepts and persists contracts only when not truncated and returned count equals total count;
6. preserves raw evidence and marks incomplete expiry chains without fabricating contracts.

Budgets are 250 consumed units and 350 network attempts. A hard stop is
`PARTIAL_ARCHIVE_BUDGET_LIMIT`; unattempted/incomplete expiries are explicit. The job persists run,
ticker, and expiry completeness plus all usage evidence. Same-date replay never overwrites or adds
duplicate normalized snapshots.

## Workflow B — MAG7 Same-Day Scan

CLI: `python -m app.cli run-mag7-scan`; dashboard: fixed backend-only `POST /api/v1/scans/mag7`.
The browser calls only Next.js `/api/mag7-scan` and never Nightwatch.

1. S0 validates PostgreSQL, capability snapshots, budget, and New York market date.
2. S2 requests `expiry-breakdown` and `options-volume` once per ticker; raw evidence and ticker-only
   context are persisted.
3. S3 persists one idempotent DTE-0 activity snapshot per ticker/vendor activity date. DTE 0 uses
   only the previous 20 valid sessions; nonzero DTE uses bounded comparable current-session peers.
4. Discovery preserves the primary track and applies only a small meaningful-secondary confirmation
   bonus. Eligibility is evaluated on the underlying tracks before ranking.
5. S4 selects at most four tickers and one strongest eligible expiry in each 0–90 DTE bucket.
6. S5 reads the latest valid complete chain from PostgreSQL, calculates contract structure and
   persistence, requests one ranked OI Change Radar payload per selected ticker, and builds same-side
   OI clusters.
7. S6 persists bucket summaries and safe dashboard fields, including the full score distribution,
   ranked eligible expiries, and DTE-0 baseline status.

The interactive budget remains 75 consumed units and 100 attempts. It never rebuilds the daily
0–180 archive and never calls contract intraday. Thirty-minute raw reuse remains available for fresh
same-day endpoints. Radar absence is neutral.

Raw vendor responses are persisted before normalized/derived rows. Every v1.2 run snapshots its
configuration and carries `signal_spec_v1.2_phase2a`; v1.0 and v1.1 records remain immutable evidence.

## Scheduling requirement

Use a durable platform scheduler (cron, systemd timer, managed job scheduler, or equivalent) to run
the archive CLI at configured Singapore local time. Overlap must be disabled, process exit must be
observed, and retries must invoke the same idempotent command. No Celery/Redis or unsafe application
background task was added.

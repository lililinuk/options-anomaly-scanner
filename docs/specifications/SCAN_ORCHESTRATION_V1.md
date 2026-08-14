# Scan Orchestration — Phase 2A v1.3

Specification: `signal_spec_v1.3_phase2a`

Accepted v1.2 runs retain their original specification and universal Discovery Score for historical
diagnostics only. New v1.3 routing never rewrites or uses that score as the primary selector.

## Workflow 0 — Three-job daily collection

CLI: `python -m app.cli archive-mag7-daily`

At the externally scheduled Asia/Singapore 12:00 trigger, the orchestrator runs Daily OI Archive,
Daily Activity (`expiry_breakdown` plus `options_volume`), and Daily Radar (`oi_change`) across the
required MAG7 coverage. Subjobs are isolated and the parent reports `COMPLETE`, `PARTIAL`, or
`FAILED` truthfully. Activity identity is ticker + expiry + New York observation session. Radar
identity is ticker + exact contract symbol + vendor observation date. Persisted legacy Radar raw
evidence can be locally evaluated under v1.3 without a network call before missing ticker/date
coverage is backfilled.

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
   persistence, reuses latest persisted OI Change Radar evidence, and builds same-side OI clusters.
7. S6 persists bucket summaries and safe dashboard fields, including the full score distribution,
   ranked eligible expiries, and DTE-0 baseline status.

The interactive budget remains 75 consumed units and 100 attempts. It never rebuilds the daily
0–180 archive and never calls contract intraday. Thirty-minute raw reuse remains available for fresh
same-day endpoints. Radar absence is neutral.

Raw vendor responses are persisted before normalized/derived rows. Every v1.3 run snapshots its
configuration and carries `signal_spec_v1.3_phase2a`; v1.0, v1.1, and v1.2 remain immutable.

## Three-route selection

Radar Event, contract/expiry Persistent Positioning, Expiry Activity, and explicit Structural Cold
Start independently create eligibility. Reasons remain in `trigger_sources`; the same ticker/expiry
chain is loaded at most once. Radar ranks by Premium then absolute ΔOI. Exact archive matching is
literal string equality. Unmatched/incomplete evidence stays visible but cannot fabricate structure.
Monthly OPEX inference and Same-Day Score Basis are display context with score weight zero.

## Phase 2B v2 database-only state build

Phase 2B v2 state materialization is documented in
`docs/specifications/PHASE2B_V2_ORCHESTRATION.md`. It reads preserved evidence, never becomes part of
the daily Nightwatch collection jobs, and does not change Phase 2A route selection.

## Phase 2B v3 database-only research workspace

Phase 2B v3 materialization is documented in
`docs/specifications/PHASE2B_V3_ORCHESTRATION.md`. It is an idempotent PostgreSQL-only projection
over a source-aligned v1 evaluation, v2 state, and preserved ticker Heatmap. It adds the versioned
`v3_research_workspace` API property and cannot initiate Nightwatch transport or change Phase 2A
route selection.

## Phase 2B v3.1 Dealer/GEX archive

The additive archive is documented in
`docs/specifications/PHASE2B_V31_ORCHESTRATION.md`. A durable external scheduler invokes one
sequential MAG7 capture near `15:30 America/New_York` on XNYS sessions. The archive has independent
seven-attempt/seven-unit bounds, zero retries, per-ticker failure isolation, vendor-time
observation identity, and no retention deletion. It does not run during an interactive MAG7 scan.

New v3.1 workspaces may read a usable archived surface only when vendor and capture timestamps are
both no later than the candidate evaluation. Historical v3.0 rows remain unchanged, and the
candidate Dealer analysis remains anchor plus nearest previous/next expiry.

## Scheduling requirement

Use a durable platform scheduler (cron, systemd timer, managed job scheduler, or equivalent) to run
the archive CLI at configured Singapore local time. Overlap must be disabled, process exit must be
observed, and retries must invoke the same idempotent command. No Celery/Redis or unsafe application
background task was added.

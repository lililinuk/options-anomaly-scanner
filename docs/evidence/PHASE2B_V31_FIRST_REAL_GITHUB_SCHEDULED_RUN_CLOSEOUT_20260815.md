# Phase 2B v3.1 — First Real GitHub Scheduled Run Closeout

Date: 2026-08-15

## Classification

- `FIRST_REAL_SCHEDULED_RUN_VERIFIED`
- `GITHUB_SCHEDULER_DEPLOYED`
- `DEALER_GEX_DAILY_ACCUMULATION_ENABLED`

All required operational conditions passed. This was a read-only closeout. The workflow
was not rerun and no additional Nightwatch request was made.

## GitHub scheduled run

| Field | Verified value |
| --- | --- |
| Workflow | `Dealer GEX Daily Archive` |
| Workflow run ID | `31835955699` |
| Run attempt | 1 |
| Event | `schedule` |
| Branch | `main` |
| Executed SHA | `1e29c92956b39f005dab0c4eb163150ee12a0c9d` |
| Run created/started | `2026-08-14T20:01:40Z` |
| Job start | `2026-08-14T20:01:44Z` |
| Capture step | `2026-08-14T20:02:07Z`–`20:02:25Z` |
| Job completion | `2026-08-14T20:02:30Z` |
| Run completion/update | `2026-08-14T20:02:31Z` |
| Run/job conclusion | `success` / `success` |
| Capture step conclusion | `success` |
| Capture step exit code | 0, established by the successful non-continue-on-error step |

At closeout, local `HEAD`, local `origin/main`, and the executed workflow SHA all matched
`1e29c92956b39f005dab0c4eb163150ee12a0c9d`.

The safe CLI summary was:

| Field | Value |
| --- | ---: |
| `archive_run_id` | `8c265174-2c85-4ef4-b4b7-8cde9e7b6ea2` |
| Status | `COMPLETE` |
| Market date | `2026-08-14` |
| Intended slot | `15:30` |
| Tickers attempted | 7 |
| Tickers succeeded | 7 |
| Tickers failed | 0 |
| Reused observations | 0 |
| Network attempts | 7 |
| Retries | 0 |
| Paid units | 7 |
| Quota remaining before | 99,807 |
| Quota remaining after | 99,800 |

## Request-shape verification

Persisted evidence for all seven ticker attempts confirms:

- schema/request profile: `nightwatch_dealer_heatmap_default_v1`;
- config version: `2026-08-14.v3.1.1`;
- specification version: `signal_spec_v3.1_phase2b`;
- endpoint format in run configuration: null/omitted;
- persisted endpoint paths contain no query string;
- persisted endpoint parameters are `{}`;
- no `format` parameter is present;
- no `format=full` path is present;
- `observations_reused=0`, so the historical `PARTIAL` summary was not reused.

The seven actual persisted request paths were:

- `/v1/derived/heatmap/AAPL/snapshot`
- `/v1/derived/heatmap/MSFT/snapshot`
- `/v1/derived/heatmap/NVDA/snapshot`
- `/v1/derived/heatmap/AMZN/snapshot`
- `/v1/derived/heatmap/META/snapshot`
- `/v1/derived/heatmap/GOOGL/snapshot`
- `/v1/derived/heatmap/TSLA/snapshot`

No Nightwatch request was made during this closeout; these paths came only from the
already persisted scheduled-run evidence and sanitized GitHub logs.

## PostgreSQL run read-back

The exact new execution run is present with:

- trigger: `external_scheduler`;
- status: `COMPLETE`;
- started: `2026-08-14T20:02:09.304917Z`;
- completed: `2026-08-14T20:02:24.139497Z`;
- market timezone: `America/New_York`;
- usable snapshots: 7;
- degraded, incomplete, and unavailable snapshots: 0;
- HTTP successes/failures: 7/0;
- analytical observations reused: 0.

| Ticker | HTTP | Quality | Vendor `generated_at` UTC | Expirations | Cells | Analytical result |
| --- | ---: | --- | --- | ---: | ---: | --- |
| AAPL | 200 | `AVAILABLE` | `2026-08-14T19:55:00Z` | 12 | 237 | New/PERSISTED |
| AMZN | 200 | `AVAILABLE` | `2026-08-14T19:55:00Z` | 13 | 237 | New/PERSISTED |
| GOOGL | 200 | `AVAILABLE` | `2026-08-14T19:55:00Z` | 13 | 238 | New/PERSISTED |
| META | 200 | `AVAILABLE` | `2026-08-14T19:55:00Z` | 13 | 242 | New/PERSISTED |
| MSFT | 200 | `AVAILABLE` | `2026-08-14T19:55:00Z` | 13 | 241 | New/PERSISTED |
| NVDA | 200 | `AVAILABLE` | `2026-08-14T19:55:00Z` | 11 | 218 | New/PERSISTED |
| TSLA | 200 | `AVAILABLE` | `2026-08-14T19:55:00Z` | 13 | 241 | New/PERSISTED |

The run added exactly seven analytical snapshots and 1,654 cells.

## Current Dealer/GEX history coverage

Execution attempts do not inflate valid history coverage. Each ticker has exactly two
distinct analytical identities, corresponding to two distinct vendor observation times.

| Ticker | Valid observations | First vendor observation UTC | Latest vendor observation UTC | Usable | Unavailable attempts |
| --- | ---: | --- | --- | ---: | ---: |
| AAPL | 2 | `2026-08-13T19:55:00Z` | `2026-08-14T19:55:00Z` | 2 | 1 |
| AMZN | 2 | `2026-08-13T19:55:00Z` | `2026-08-14T19:55:00Z` | 2 | 1 |
| GOOGL | 2 | `2026-08-13T19:55:00Z` | `2026-08-14T19:55:00Z` | 2 | 1 |
| META | 2 | `2026-08-13T19:55:00Z` | `2026-08-14T19:55:00Z` | 2 | 1 |
| MSFT | 2 | `2026-08-13T19:55:00Z` | `2026-08-14T19:55:00Z` | 2 | 1 |
| NVDA | 2 | `2026-08-13T19:55:00Z` | `2026-08-14T19:55:00Z` | 2 | 1 |
| TSLA | 2 | `2026-08-13T19:55:00Z` | `2026-08-14T19:55:00Z` | 2 | 1 |

Database totals are now:

- execution runs: 4;
- all snapshots/attempt evidence: 21;
- analytical snapshots: 14;
- distinct analytical identities: 14;
- analytical cells: 3,312.

Before this scheduled run, the verified totals were 3 runs, 14 snapshots, 7 analytical
snapshots, and 1,658 cells. The exact increases of +1, +7, +7, and +1,654 match the new
run, with no sign of execution-attempt inflation or analytical duplication.

## Historical evidence preservation

Historical failed run `4f7a068d-2461-49e6-a200-9b185fad688d` remains unchanged:

- trigger: `cli`;
- config version: `2026-08-14.v3.1`;
- status: `PARTIAL`;
- started/completed: `2026-08-14T11:29:46.197394Z` /
  `2026-08-14T11:30:10.990177Z`;
- snapshots: 7;
- HTTP 400 snapshots: 7;
- `UNAVAILABLE` snapshots: 7;
- cells: 0.

The accepted recovery evidence also remains intact across two original CLI runs:

- run `20cd7e65-9bcf-48a6-8593-82a41c222800`: 1 analytical snapshot, 220 cells;
- run `38373138-5a56-4ff5-9d9d-f61f56847e90`: 6 analytical snapshots, 1,438 cells.

Together these are the previously verified seven recovery snapshots and 1,658 cells.
No historical row was deleted, converted, or reassigned to the new scheduled run.

## Schedule timing

- Configured target: 15:30 `America/New_York`.
- GitHub scheduled run start: 16:01:40 EDT on 2026-08-14.
- Start delay from intended slot: 31 minutes 40 seconds.
- Capture step start: 16:02:07 EDT.
- Vendor `generated_at` for every ticker: 15:55:00 EDT.
- Vendor observation delay from intended slot: 25 minutes.

The vendor observation predates the workflow start by 6 minutes 40 seconds and is the
authoritative observation timestamp. This gate does not alter the configured schedule.

## Security

- Exact local `DATABASE_URL` and `NIGHTWATCH_API_KEY` values were absent from the complete
  GitHub run logs.
- `.env` exists, remains Git-ignored, and was not modified.
- Neither secret value exists in tracked files.
- Frontend files contain neither secret variable name nor secret value.
- Frontend contains no direct Nightwatch endpoint/transport.
- Persisted raw payloads and endpoint parameters for this run contain zero Authorization
  fields.
- No credential value, fingerprint, Authorization header, signed log URL, or secret was
  included in this report.

## Closeout contact ledger

No workflow or Nightwatch call was initiated during closeout.

Read-only GitHub REST paths were each accessed twice: once for operational evidence and
once for exact secret-value log verification.

- `GET /repos/lililinuk/options-anomaly-scanner/actions/workflows/dealer-gex-archive.yml/runs?event=schedule&branch=main&per_page=10`
- `GET /repos/lililinuk/options-anomaly-scanner/actions/runs/31835955699`
- `GET /repos/lililinuk/options-anomaly-scanner/actions/runs/31835955699/jobs?per_page=100`
- `GET /repos/lililinuk/options-anomaly-scanner/actions/runs/31835955699/logs`

The logs endpoint followed GitHub's managed download redirect in memory. Its ephemeral
signed target URL was deliberately not recorded or exposed. The development PostgreSQL
database was contacted through the existing ignored configuration for read-only
persisted evidence queries; its connection URL was not printed.

## Scope confirmation

No GEX Evolution logic, Actionability, Phase 3, dashboard behavior, schema, migration,
workflow, scheduler configuration, or production code was changed.

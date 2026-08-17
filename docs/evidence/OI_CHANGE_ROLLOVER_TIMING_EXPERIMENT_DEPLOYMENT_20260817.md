# Nightwatch OI Change Rollover Timing Experiment — Deployment Evidence

Date: 2026-08-17
Status: **IMPLEMENTED LOCALLY — DEPLOYMENT VERIFICATION PENDING**

## 1. Purpose

This temporary, isolated research workflow measures when Nightwatch
`GET /v1/options/oi-change/{ticker}` first exposes the most recently completed XNYS
session for NVDA, AAPL, and TSLA.

It distinguishes:

- `event_date`: vendor `observation_date`;
- `first_seen_at`: earliest experiment probe that observed that date;
- `exact_vendor_publication_time`: unknown.

The experiment does not infer option or underlying direction and does not change Scanner
semantics.

## 2. Safety boundary

- Dedicated GitHub Actions workflow and concurrency group.
- Exactly three tickers, requested sequentially.
- Nightwatch client `max_concurrency=1`, `max_retries=0`.
- Only `/v1/options/oi-change/{ticker}` is called.
- No database URL is provided to the workflow.
- No database model, session, migration, Scanner orchestration, API route, or dashboard is
  imported or invoked.
- Raw responses and contract symbols are not written to artifacts.
- Only compact freshness metadata is retained in GitHub Actions artifacts.
- The API secret remains the existing server-side `NIGHTWATCH_API_KEY` GitHub secret.

## 3. Repository preflight

- Starting branch: `main`.
- Starting HEAD: `1e29c92956b39f005dab0c4eb163150ee12a0c9d`.
- `origin/main` matched local HEAD after `git fetch origin --prune`.
- Existing untracked evidence files were preserved.
- Existing workflow inventory contained only `.github/workflows/dealer-gex-archive.yml`.
- The Dealer/GEX workflow already maps `secrets.NIGHTWATCH_API_KEY`.

## 4. Files changed

- `.github/workflows/oi-change-rollover-timing-experiment.yml`
- `backend/app/research/__init__.py`
- `backend/app/research/oi_change_rollover.py`
- `backend/tests/test_oi_change_rollover_research.py`
- this evidence report

No existing production file or existing workflow was edited.

## 5. Architecture

The probe module has two commands:

1. `probe`: applies the hard date guard and either exits with zero requests or performs three
   sequential OI-change requests, then writes safe per-run JSON/CSV.
2. `aggregate`: combines the current safe result with prior default-branch experiment artifacts,
   deduplicates by GitHub run/attempt/ticker, and produces cumulative CSV/Markdown.

Prior-artifact download uses the GitHub Actions API and the run-scoped GitHub token with
`actions: read`. A transient aggregation download failure cannot destroy the current probe; a
later run can recover all unexpired artifacts.

## 6. Schedule

August 2026 uses EDT (`UTC-04:00`).

| New York | UTC cron |
|---|---|
| 05:00 | `0 9-13 * * 1-5` (09:00 member) |
| 06:00 | `0 9-13 * * 1-5` (10:00 member) |
| 07:00 | `0 9-13 * * 1-5` (11:00 member) |
| 08:00 | `0 9-13 * * 1-5` (12:00 member) |
| 09:00 | `0 9-13 * * 1-5` (13:00 member) |
| 09:25 | `25 13 * * 1-5` |
| 09:45 | `45 13 * * 1-5` |
| 10:15 | `15 14 * * 1-5` |
| 10:45 | `45 14 * * 1-5` |
| 11:15 | `15 15 * * 1-5` |

Cron is only a trigger. The Python process independently enforces New York experiment dates.

## 7. Experiment dates and XNYS semantics

Target source sessions:

`2026-08-17`, `2026-08-18`, `2026-08-19`, `2026-08-20`, `2026-08-21`.

Approved probe dates:

`2026-08-18`, `2026-08-19`, `2026-08-20`, `2026-08-21`, `2026-08-24`.

For an approved probe date, the expected date is the authoritative XNYS previous session. This
maps Monday 2026-08-24 to Friday 2026-08-21 and never substitutes the previous calendar day.
Outside the approved set, including after 2026-08-24, live mode exits zero with no Nightwatch
request.

## 8. Safe stored metadata contract

Each ticker record contains GitHub run identity, UTC and New York request times, HTTP/result
state, attempts/retries, row count, distinct current/previous vendor dates, latest-date quality
counts and rank range, expected XNYS date, freshness state, signed trading-session lag, and safe
post-request quota remaining when available.

It does not contain authorization headers, API keys, raw payloads, or individual contract rows.

Freshness states are `CURRENT`, `STALE`, `AHEAD_OR_UNEXPECTED`, `UNAVAILABLE`, and
`AMBIGUOUS`. HTTP, transport, empty, and parsing failures remain explicit and are never treated as
stale.

## 9. First-seen and cross-ticker semantics

For each ticker and target date, cumulative aggregation derives the last stale probe and first
current probe. The publication interval is `(last_stale_probe_at, first_seen_at]`; it is not an
exact publication timestamp.

Requests for all three tickers occur sequentially within a workflow run. Therefore
`SIMULTANEOUS_WITHIN_PROBE_RESOLUTION` means the three first-current observations occurred in the
same GitHub run/attempt, not at the identical microsecond. Otherwise the state is `STAGGERED`,
`INCOMPLETE`, or `UNRESOLVED`.

## 10. Artifacts and visibility

Each run uploads a unique 45-day artifact:

`oi-change-rollover-probe-<run_id>-<run_attempt>`

containing:

- `probe_results.json`;
- `probe_results.csv`;
- `oi_change_rollover_cumulative.csv`;
- `oi_change_rollover_summary.md`.

The workflow also renders current and cumulative safe summaries through
`$GITHUB_STEP_SUMMARY`.

## 11. API and quota ceiling

The scheduled ceiling is:

`3 tickers × 10 slots × 5 probe dates = 150 Nightwatch requests`.

The code neither assumes 50 response rows nor infers exact paid units from quota-remaining
metadata. No scheduler can make a request after the final approved date because of the internal
guard.

## 12. Production-isolation proof

- Production database migrations: 0.
- Production database write paths: 0.
- Phase 2A/2B changes: 0.
- Scoring, thresholds, selection, Dealer/GEX, API, and dashboard changes: 0.
- Existing Dealer/GEX workflow changes: 0.
- Shared concurrency groups: 0.

The unit suite inspects the research module and workflow to prevent database imports, database
configuration, unrelated scheduler coupling, and secret leakage.

## 13. Local verification

- Targeted research tests: **22 passed**.
- Ruff for new module/tests: **passed**.
- Local dry run: **DRY_RUN, 0 requests**.
- Local live-mode date-guard check on New York 2026-08-16: **SKIPPED_DATE_GUARD, 0 requests**.
- Workflow YAML parse: **passed; 6 cron entries**.
- Full backend suite: **295 passed**.
- Frontend lint: **passed**.
- Frontend production build: **passed**.

## 14. Deployment record

- Implementation branch: `research/oi-change-rollover-timing`
- Implementation commit: `PENDING`
- PR URL: `PENDING`
- Merge SHA: `PENDING`
- Workflow name: `Nightwatch OI Change Rollover Timing Experiment`
- Workflow path: `.github/workflows/oi-change-rollover-timing-experiment.yml`
- Workflow ID: `PENDING`
- Default-branch presence: `PENDING`
- Workflow enabled state: `PENDING`
- Dry-run verification run ID: `PENDING`
- Live verification run ID/result: `PENDING`

## 15. Temporary end state

Self-disable is not configured because it would require broader workflow write permission. The
hard date guard is authoritative: every invocation outside the five approved New York dates exits
successfully with zero Nightwatch requests. The workflow can be manually disabled after artifact
review without urgency or risk of post-window quota use.

## 16. External contact and write ledger

Implementation preflight contacted only the configured GitHub git remote to fetch `origin`.
No Nightwatch endpoint was contacted during implementation or local tests. No database endpoint
was contacted. Local generated verification artifacts were written only to the operating-system
temporary directory.

## 17. Conclusion

Deployment conclusion and operational state: **PENDING REMOTE DEPLOYMENT VERIFICATION**.

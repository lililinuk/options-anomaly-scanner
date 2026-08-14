# Phase 2B v3.1 — Dealer/GEX Scheduled Run Identity & Retry Recovery

Date: 2026-08-15

## Status

`READY_FOR_SECOND_GITHUB_MANUAL_VALIDATION`

This is an implementation and database gate only. The GitHub Actions workflow was not
executed, and no live Nightwatch request was made. This report does not claim
`GITHUB_SCHEDULER_DEPLOYED`.

## Git

- Accepted code baseline: `fc050d8fcacc495293fd66f4892ff3d4afbf241f`
- Forensic evidence commit: `8dfb4c8ed1a5a6e7ac671d534f7fa48a8c40f81e`
- Actual clean implementation starting HEAD: `8dfb4c8ed1a5a6e7ac671d534f7fa48a8c40f81e`
- Implementation commit: `ed2133344474510f495107b3b6c42aa4aab70b56`
- The accepted code baseline remains an ancestor of the implementation commit.
- No history was rewritten or force-pushed.

## Root cause

The accepted forensic diagnosis classified the first GitHub manual run as
`ROOT_CAUSE_CONFIRMED_REQUEST_SHAPE`, with the critical qualification that the runner
made zero new Nightwatch requests. The archive service found historical run
`4f7a068d-2461-49e6-a200-9b185fad688d` by logical slot alone and returned its old
`PARTIAL` summary. That historical attempt used the retired `format=full` profile, so
the GitHub log displayed its seven historical HTTP 400 results and counters even though
the current no-format transport was never reached.

## Old model

`dealer_gex_archive_runs` previously enforced one row for:

`ny_market_date + intended_capture_slot + scope_key`

The service also looked up a run using only those three values and reused it regardless
of terminal status or request/config profile. Consequently, one `PARTIAL`, failed,
pre-slot, or old-profile attempt could permanently consume a logical production slot.
The run row was serving as both logical-slot identity and execution-attempt identity.

## New model

Logical scheduled slot and execution attempt are now separate concepts:

- A logical slot is still described by NY market date, intended slot, and scope.
- Each invocation that needs to execute creates an append-only run with its existing UUID
  primary key as the execution-attempt identity.
- Multiple `PARTIAL`, `FAILED`, skipped, and later successful attempts may coexist for the
  same logical slot.
- The historical failure row is never mutated into the later success.
- A non-unique lookup index covers market date, slot, scope, and status.

A prior run suppresses capture only when all of these are true:

- status is `COMPLETE` and completion time exists;
- NY market date, intended slot, and scope match;
- financial specification version matches;
- config version and config hash match the active request profile;
- execution started at or after the authoritative intended-slot timestamp.

`PARTIAL`, `FAILED`, incomplete, old-profile, and pre-slot runs never suppress an eligible
capture. The config hash includes the endpoint-format setting; therefore the retired
`format=full` profile is not equivalent to the current omitted-format profile.

Analytical observation identity remains independent and unchanged. A replay with the
same versioned vendor observation identity reuses the existing analytical snapshot and
cells. A new execution attempt therefore cannot inflate history coverage merely because
it received the same vendor `generated_at` again.

## Concurrency protection

Execution-level protection remains deliberately small:

- GitHub Actions uses concurrency group `dealer-gex-daily-archive` with
  `cancel-in-progress: false`.
- The backend obtains its existing PostgreSQL advisory lock before creating a new run or
  making a vendor request.
- Equivalent `COMPLETE` suppression is checked once before the lock and again after the
  lock, closing the check/capture race.
- Failure to acquire the lock stops before the Nightwatch client is called.
- Versioned analytical `observation_identity` remains the final persistence defense.

No queue, Redis, worker framework, or new scheduler was introduced.

## Scheduled target-time semantics

The `external_scheduler` path now enforces the configured 15:30
`America/New_York` target:

- weekend/holiday: existing `SKIPPED_NON_TRADING_SESSION`;
- early close before the target: existing `SKIPPED_TARGET_AFTER_EARLY_CLOSE`;
- invocation before 15:30: `SKIPPED_BEFORE_TARGET_SLOT`, a successful operational skip
  with zero Nightwatch calls and zero paid units;
- a later post-slot invocation is not suppressed by that skip and may capture normally.

The skip is persisted as truthful execution evidence, is not `COMPLETE`, and does not
consume the later production slot. The CLI treats this calendar/time skip as non-fatal.
New scheduled runs retain `trigger=external_scheduler`; historical trigger values are
unchanged.

## Migration

- Previous revision: `20260814_0012`
- New revision/head: `20260815_0013`
- Removed constraint: `uq_dealer_gex_run_market_date_slot_scope`
- Added non-unique index: `ix_dealer_gex_run_slot_status`
- Added columns: none
- Deleted or rewritten data: none

The downgrade path does not delete retry attempts. It refuses to restore the legacy
unique constraint when multiple attempts exist for a slot; transactional DDL preserves
the current schema if that safety check fails.

Real development PostgreSQL validation:

- database implementation: PostgreSQL 17.6
- current revision: `20260815_0013`
- head revision: `20260815_0013`
- `alembic check`: `No new upgrade operations detected.`
- old unique constraint count: 0
- new lookup index count: 1

## Regression matrix

| Case | Evidence | Result |
| --- | --- | --- |
| A | Historical `PARTIAL`, same profile | PASS — new execution attempt allowed |
| B | Historical `FAILED`, same profile | PASS — new execution attempt allowed |
| C | Historical `PARTIAL`, old `format=full` profile | PASS — current no-format attempt executes |
| D | Historical `COMPLETE`, old profile | PASS — current profile is not suppressed |
| E | Historical post-slot `COMPLETE`, equivalent current profile | PASS — reused with zero client calls and no new run |
| F | Same vendor observation identity across attempts | PASS — snapshot/cells reused and coverage remains one |
| G | Scheduled invocation before target | PASS — explicit skip, zero client calls |
| H | Post-slot invocation after pre-slot skip | PASS — new run allowed and mocked capture reached |
| I | Concurrent equivalent invocation | PASS — advisory-lock rejection makes zero client calls; post-lock recheck also tested |
| J | Historical rows across migration | PASS — all verified counts and old failure evidence preserved |

The tests also prove that a current retry sends the mocked transport:

`GET /v1/derived/heatmap/{ticker}/snapshot`

with `params=None`. No `format` key, empty value, null query value, or `format=full` query
is generated.

## Database evidence

Safe counts immediately before and after migration were identical:

| Entity | Before | After |
| --- | ---: | ---: |
| Archive runs | 3 | 3 |
| All snapshots | 14 | 14 |
| Analytical snapshots | 7 | 7 |
| Snapshot cells | 1,658 | 1,658 |

Historical run `4f7a068d-2461-49e6-a200-9b185fad688d` remains:

- status: `PARTIAL`
- snapshots: 7
- HTTP 400 snapshots: 7
- `UNAVAILABLE` snapshots: 7

The seven accepted analytical recovery snapshots and all 1,658 cells remain present.
No runtime capture was performed as part of database verification.

The persisted-only history path remains unchanged. It filters analytical history by
`is_analytical_observation`; unavailable attempts remain distinguishable from real zero,
and repeated execution attempts cannot increase distinct valid coverage unless a new
versioned analytical observation is actually persisted.

## Tests and quality gates

- Targeted archive identity, workflow, and API tests: PASS (44 tests)
- Full backend suite: PASS (`273 passed`)
- Ruff over `app`, `tests`, and `alembic`: PASS
- Alembic real PostgreSQL upgrade: PASS
- Alembic current/head: PASS (`20260815_0013`)
- Alembic drift check: PASS
- PostgreSQL preservation/read-back: PASS
- Git diff whitespace check: PASS
- Frontend files changed: none
- Automated live Nightwatch calls: 0
- Paid Nightwatch units: 0

## Security

- `.env` exists locally and remains Git-ignored.
- `DATABASE_URL` is present and non-empty locally, and its value is absent from every
  tracked file.
- `NIGHTWATCH_API_KEY` is present and non-empty locally, and its value is absent from
  every tracked file.
- No secret value, credential fingerprint, or Authorization header was written to this
  report or persisted by the change.
- Authorization construction remains isolated to the server-side Nightwatch transport.
- Frontend files contain neither secret variable and no frontend Nightwatch request was
  introduced.
- `.env` was not modified.

## External contact ledger

- Development PostgreSQL configured by the ignored `.env`: contacted for migration,
  Alembic drift inspection, and safe read-back only.
- Nightwatch API endpoints: none.
- GitHub Actions workflow runs: none.

## Next checkpoint

A second GitHub manual validation may be authorized separately at or after the 15:30
America/New_York target. Until that controlled run succeeds, deployment closure must not
be claimed.

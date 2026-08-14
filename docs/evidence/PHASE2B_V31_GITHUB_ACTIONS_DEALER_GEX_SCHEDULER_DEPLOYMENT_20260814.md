# Phase 2B v3.1 GitHub Actions Dealer/GEX Scheduler Deployment Gate

Date: 2026-08-14

## A. Workflow Implementation

### Repository checkpoint

- Starting SHA: `45d3d7e369e1cd597a4cceaa4804e5b8e0209622`
- Implementation SHA: recorded in the completion response after this report is committed.
- Local branch observed: `main`
- Git remote: none configured in this checkout.
- GitHub default branch: not remotely verifiable until a remote is configured.

### Workflow contract

- Workflow path: `.github/workflows/dealer-gex-archive.yml`
- Workflow name: `Dealer GEX Daily Archive`
- Scheduled trigger: `30 15 * * 1-5`
- Timezone: `America/New_York`
- Manual trigger: `workflow_dispatch`
- Runner: `ubuntu-latest`
- Python: `3.10`, matching the backend's declared `>=3.10` support and local project convention.
- Backend working directory: `backend`
- Dependency installation: `python -m pip install .`
- CLI invocation: `python -m app.cli capture-dealer-gex-archive --scheduled`
- Permissions: `contents: read`; no repository or deployment write permissions are granted.
- Concurrency group: `dealer-gex-daily-archive`
- Cancellation: `cancel-in-progress: false`; a new trigger does not cancel a valid running archive.
- Timeout: 15 minutes. This is conservative relative to the accepted sequential, retry-free,
  maximum-seven-request capture while preventing an indefinitely hung runner.

GitHub's scheduler is only the durable trigger. Existing application XNYS calendar logic remains
authoritative for weekends, holidays, early closes, and target-slot eligibility. No exchange
calendar or Dealer/GEX business logic is duplicated in YAML.

### Required GitHub secrets

Only these repository Secret names are required:

- `DATABASE_URL`
- `NIGHTWATCH_API_KEY`

The workflow injects them as environment variables. It contains no values, secret-bearing command
arguments, database URL, Authorization header, or direct Nightwatch request. The preflight reports
only a missing variable name and exits before dependency installation or the archive CLI, so
Nightwatch cannot be called when required runtime configuration is absent.

### Exit and persistence semantics

- `COMPLETE` and `DRY_RUN_READY`: exit 0.
- `SKIPPED_NON_TRADING_SESSION` and `SKIPPED_TARGET_AFTER_EARLY_CLOSE`: exit 0 because these are
  valid calendar decisions, not infrastructure failures.
- `PARTIAL`, `EMPTY`, concurrent execution, and `SKIPPED_DISABLED`: nonzero exit, preserving
  operational visibility. Successful ticker rows committed before a partial outcome remain intact.
- SQLAlchemy, Nightwatch transport, runtime, or configuration failures: exit 5.
- Database archive idempotency remains the final race/replay guard; the workflow adds no competing
  persistence path.

### Static validation

- Workflow YAML safe-load and contract assertions: PASS.
- Scheduled CLI dry-run: `DRY_RUN_READY`; 0 network attempts; 0 paid units.
- Backend tests: 262 passed. One local pytest cache write warning was emitted because the existing
  `.pytest_cache` directory was not writable; test execution and results were unaffected.
- Ruff: PASS (`app` and `tests`).
- `git diff --check`: PASS.
- `.env` ignore check: PASS.
- Exact local `DATABASE_URL` / `NIGHTWATCH_API_KEY` values found in tracked files: 0.
- Migration changes: 0.
- Frontend changes: 0; no browser Nightwatch transport was introduced.
- Live Nightwatch calls: 0.
- Nightwatch paid units: 0.

### External contacts during implementation

No Nightwatch endpoint, PostgreSQL server, or GitHub Actions workflow run was contacted. Official
documentation was consulted at:

- `https://docs.github.com/en/actions/reference/workflows-and-actions/workflow-syntax`
- `https://github.com/actions/checkout/releases`
- `https://github.com/actions/setup-python/releases`

### Required manual GitHub setup

1. Configure a Git remote for the target GitHub repository if this checkout is the deployment
   source.
2. Push the workflow commit to the GitHub repository's actual default branch.
3. Configure repository secrets named `DATABASE_URL` and `NIGHTWATCH_API_KEY` directly in GitHub.
4. Confirm to Codex that both Secret names exist; do not send their values in chat.
5. Run exactly one manual `workflow_dispatch` validation, then verify PostgreSQL/history through
   the accepted read paths without making an extra Nightwatch call.

Implementation checkpoint classification:

`AWAITING_GITHUB_SECRET_CONFIGURATION`

The workflow has been implemented and validated offline. It has not been deployed or manually
executed on GitHub, so `GITHUB_SCHEDULER_DEPLOYED` and
`DEALER_GEX_DAILY_ACCUMULATION_ENABLED` are not claimed.

## B. Manual GitHub Deployment Validation

Status: `NOT_RUN`

Reason: `AWAITING_GITHUB_SECRET_CONFIGURATION`

This section must be appended only after the Founder confirms both repository Secret names and one
manual workflow execution completes. The closeout must record the manual trigger, executed
branch/SHA, timing and job status, safe CLI/archive result, ticker success/failure counts,
PostgreSQL/history read-back, new-versus-reused vendor observation result, paid units, and log
secret-safety verification.

After the first real scheduled event, a separate operational closeout must verify that the event was
triggered by `schedule`, the approximate slot corresponds to 15:30 America/New_York, the CLI session
classification is correct, the archive/history rows and MAG7 attempt results are present, replay did
not duplicate analytical observations, quota consumption is recorded, and logs contain no secrets.

No GEX Evolution Calibration, Actionability, Dashboard change, Phase 2A change, Phase 3 work, or
database migration was performed in this gate.

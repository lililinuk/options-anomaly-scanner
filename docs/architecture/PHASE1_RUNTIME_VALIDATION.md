# Phase 1 Runtime Validation

## Closeout status — 2026-08-10

The accepted Phase 1 baseline is commit `013e9e9cbe071626a0f5a441f35a528947a6274c`.

Runtime infrastructure was probed before any installation or configuration change:

- no `psql` or `pg_isready` command is installed;
- no Windows PostgreSQL service is registered;
- no process is listening on local port 5432;
- no common PostgreSQL installation directory was found;
- neither Docker nor Podman is installed.

Therefore Alembic could not be applied to a real PostgreSQL development database in this closeout. No SQLite or mock database is represented as PostgreSQL validation, and no system software was installed implicitly.

The manual refresh command was executed against this blocked environment. Its PostgreSQL preflight failed with a sanitized message and exit code 2 before any Nightwatch endpoint was contacted.

## Exact blocking prerequisite

Provide one non-production PostgreSQL 14+ instance by either:

1. installing/starting local PostgreSQL, creating a development database/user, and putting its SQLAlchemy URL in the ignored root `.env`; or
2. installing Docker, running `docker compose up -d postgres`, and setting the matching `DATABASE_URL` in `.env`.

Do not commit `.env` or place credentials on command lines that may be logged.
`DATABASE_CONNECT_TIMEOUT_SECONDS` defaults to five seconds so unavailable development infrastructure fails safely before any metadata request.

## Completion commands once PostgreSQL is available

```powershell
cd backend
python -m alembic upgrade head
python -m app.cli refresh-metadata
```

The second command is the persistence smoke test: Nightwatch `/discover` response → typed parser → normalized capabilities → PostgreSQL transaction → verified read-back. It exits before contacting Nightwatch if the database preflight fails.

Expected schema additions from revision `20260810_0002` are:

- `metadata_refreshes`
- `capability_snapshots`
- `api_usage_audit.quota_limit`
- `api_usage_audit.rate_limit`
- `api_usage_audit.retry_count`

The automated suite uses mocked Nightwatch responses only. No financial scoring, directional signals, lifecycle inference, GEX trading logic, or tradeability calculation is part of this runtime work.

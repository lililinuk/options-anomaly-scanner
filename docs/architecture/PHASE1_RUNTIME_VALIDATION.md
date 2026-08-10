# Phase 1 Runtime Validation

## Validated closeout status — 2026-08-10

The accepted Phase 1 commits remain unchanged:

- `013e9e9cbe071626a0f5a441f35a528947a6274c`
- `976de3a825f5390507163aa8d294b86640f0b5e2`

The ignored local `.env` now supplies a non-production Supabase PostgreSQL URI. Provider URIs using `postgres://` or `postgresql://` are normalized in memory to `postgresql+psycopg://`, selecting the repository's installed Psycopg 3 driver without rewriting or displaying the secret.

Connectivity and schema were validated against PostgreSQL 17.6 in the `public` schema. Alembic current and head both reported `20260810_0002`. The following tables were confirmed through PostgreSQL catalog inspection:

- `alembic_version`
- `api_usage_audit`
- `capability_snapshots`
- `metadata_refreshes`
- `option_contract_observations`
- `position_lifecycle_events`
- `raw_vendor_payloads`
- `scan_runs`
- `signal_detections`

## Runtime commands

```powershell
cd backend
python -m alembic upgrade head
python -m app.cli refresh-metadata
```

The second command is the persistence smoke test: Nightwatch `/discover` response → typed parser → normalized capabilities → PostgreSQL transaction → verified read-back. It exits before contacting Nightwatch if the database preflight fails.

Schema additions from revision `20260810_0002` were verified as applied:

- `metadata_refreshes`
- `capability_snapshots`
- `api_usage_audit.quota_limit`
- `api_usage_audit.rate_limit`
- `api_usage_audit.retry_count`

## Persistence smoke result

One zero-quota `GET /v1/discover` call produced and verified:

- one `metadata_refreshes` row;
- 94 `capability_snapshots` rows, all with coverage metadata;
- one `/v1/discover` `api_usage_audit` row;
- one raw evidence row with a verified SHA-256 digest;
- linked client, vendor, raw, and source request IDs;
- quota `100000/100000`, rate limit `59/60`, HTTP 200, zero retries, and `consumed_quota=false`;
- timezone-aware observation timestamps.

The persisted raw and normalized JSON contained no Authorization, bearer token, or key-shaped fields. The relevant tables have no authorization/password column. Replaying the persisted source response through the repository returned `created=false`; all four row counts remained unchanged.

## Status path

The complete PostgreSQL → FastAPI → fixed Next.js `/api/system-status` proxy → dashboard path was run locally. FastAPI and the proxy reported database connected, Nightwatch connected, latest capability timestamp, quota/rate metadata, and latest HTTP 200. The rendered dashboard displayed those values with no console warning/error and no Nightwatch URL in the DOM.

The automated suite continues to use mocked Nightwatch responses only. No financial scoring, directional signals, lifecycle inference, GEX trading logic, or tradeability calculation is part of this runtime work.

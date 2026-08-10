# System Architecture

## Purpose and boundary

Options Anomaly Scanner is a research and decision-support system. Phase 1 builds a traceable ingestion and presentation foundation; it does not identify directional trades or implement unusual-options formulas.

## Data flow

```text
Nightwatch REST API
  -> backend Nightwatch transport
  -> raw ingestion (immutable vendor payload + digest)
  -> normalization (vendor-neutral observations)
  -> future hierarchical analytics
  -> PostgreSQL
  -> FastAPI (our application contract)
  -> Next.js dashboard
```

The browser calls only our FastAPI API. It never authenticates to or calls Nightwatch directly. Server configuration stores the Nightwatch key as a secret value and the frontend has no key variable.

## Backend modules

- `app/nightwatch`: HTTP transport, typed envelopes, capability registry, quota-header parsing, retry classification, structured errors, concurrency control, request IDs, and usage events.
- `app/ingestion`: writes raw source evidence before any lossy transformation.
- `app/normalization`: defines immutable vendor-neutral option observations.
- `app/metadata`: coordinates the explicit `/discover` refresh flow without scheduling it.
- `app/analytics`: reserved for future hierarchical analysis. It contains no formulas in Phase 1.
- `app/scanner`: reserved for scan orchestration. Scheduling is disabled.
- `app/db` and `app/persistence`: SQLAlchemy models, sessions, append-only historical records, and repositories.
- `app/api`: FastAPI routes consumed by the dashboard.
- `app/config`: environment-backed validated settings. Refresh interval and concurrency are configurable.

Dependencies point inward: API routes and orchestration may compose services; vendor transport does not know about normalized models or financial analytics.

## PostgreSQL role

PostgreSQL is the system of record for:

1. scan runs and their configuration snapshot;
2. raw vendor payloads, request identity, source timestamps, and SHA-256 digest;
3. normalized contract observations linked back to raw evidence;
4. external API usage and quota metadata;
5. future immutable detections and append-only lifecycle events.

The manual metadata transaction writes one raw `/discover` response, one deduplicated API-usage row, one immutable refresh header, and its normalized capability rows. `source_request_id` uniqueness makes replay of the same response idempotent. A successful command performs a count-based database read-back before reporting success.

Every persisted timestamp uses `timestamp with time zone`. Application code canonicalizes instants to UTC. Market-session dates are calculated with `America/New_York`; host-local time is never market truth.

Detection facts (`dte_at_detection`, `bucket_at_detection`) are immutable history. Dynamic values (`current_dte`, `current_bucket`) will be calculated separately and must not overwrite them. Signal age is a different concept from DTE.

## Raw, normalized, and derived separation

- **Raw** is the untouched response evidence, stored with endpoint, request IDs, received/observed timestamps, context, and content digest.
- **Normalized** is a stable vendor-neutral interpretation that links to its raw payload.
- **Derived** will contain documented, reproducible calculations and explicit evidence references.

This separation permits replay, audit, correction of a normalizer without losing source evidence, and exact attribution of future signal decisions.

## API quota strategy

- Treat `/v1/discover`, `/v1/health`, and `/v1/openapi.json` as documented zero-quota metadata endpoints.
- Make capability availability depend on `/v1/discover`; documentation alone never enables a command for an account.
- Capture endpoint/command, timestamp, ticker, expiration, status, quota-consumption classification, remaining quota/rate limit, request IDs, latency, attempts, and error code.
- Never persist request headers or Authorization values.
- Bound concurrency through configuration.
- Retry only safe request methods on transient network errors and documented retryable statuses. Honor `Retry-After`; do not retry logical 4xx failures.
- Cache metadata according to a configurable refresh interval. Scan cadence will also be configuration-driven when scheduling is added.
- Estimate scan cost later by aggregating `api_usage_audit`, not by hiding vendor calls inside analytics.

OI is lagged source data, not real-time participant identity. One Nightwatch chain snapshot covers one expiration, so future orchestration must plan calls explicitly and account for quota before fan-out.

## Dashboard role

The Next.js application presents our persisted/reconciled state through FastAPI: status, scan history, quota state, candidate research, ticker detail, and lifecycle history. Its fixed same-origin `/api/system-status` proxy calls only FastAPI; it cannot accept or construct arbitrary Nightwatch paths. FastAPI's status route reads PostgreSQL and never contacts Nightwatch. Phase 1 is a responsive shell with truthful empty and disabled states. Final trading charts and interaction design are out of scope.

## Manual metadata refresh

From `backend/`, run `python -m app.cli refresh-metadata`. The command:

1. verifies PostgreSQL connectivity before any external request;
2. makes one authenticated, zero-quota `GET /v1/discover` request;
3. parses and normalizes capability identifiers, availability, coverage, weight, and safe source metadata;
4. atomically persists raw evidence, API usage, and capability snapshot rows;
5. reads the snapshot back and prints only counts, quota/rate metadata, retry count, and request ID.

No scheduler invokes this command. No browser route can trigger it.

## Future scheduling design

A later scheduler will enqueue idempotent scan runs from configurable US-market-session rules and permit manual runs through the same orchestration path. It should:

- calculate sessions in `America/New_York`;
- snapshot configuration on every run;
- preflight account capabilities and remaining quota;
- budget calls by endpoint, ticker, and expiration;
- cap worker concurrency;
- support replay/recovery without overwriting historical rows;
- expose run state through FastAPI.

No scheduler, production polling, or deployment topology is implemented in Phase 1.

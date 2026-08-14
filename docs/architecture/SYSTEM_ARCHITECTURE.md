# System Architecture

## Phase 2B v2 research-state layer

The v2 layer is database-only and sits after preserved Phase 2A provenance and immutable Phase 2B
v1.x context normalization:

```text
Phase 2A evidence ─┐
                   ├─> Phase 2B v2 pure state builder
Phase 2B v1.x ctx ─┘          │
                              v
                  phase2b_candidate_states (append-only)
                              │
                              v
FastAPI candidate confirmation -> fixed Next.js proxy -> dashboard
```

Vendor transport does not enter the v2 builder. Positioning, price, volatility, Dealer/GEX,
execution, and readiness remain separate JSON state objects. Expiry-only rows stop before the
contract-state builder. The browser never receives credentials and never calls Nightwatch.

## Phase 2A runtime extension

The accepted Phase 1 transport → raw ingestion → normalization → persistence boundary remains unchanged. Phase 2A adds a versioned scanner configuration and pure analytics layer, an explicit eight-stage manual orchestrator, append-only scanner entities, fixed FastAPI scan routes, a fixed Next.js proxy, and dashboard/read-only field-guide presentation. Nightwatch remains backend-only. The application-process scan runner is suitable for manual development use but is not a durable production queue.

Phase 2A v1.2 separates a durable-scheduler-invoked, idempotent Daily OI Archive job from the manual
same-day scan. The archive writes complete 0–180 DTE expiry/contract OI sessions. Interactive scans
reuse that archive and independently refresh expiry activity and ticker-day context. The repository
does not run an in-process scheduler; deployment must invoke `python -m app.cli archive-mag7-oi` at
the configured Asia/Singapore trigger time.

The interactive workflow also persists one valid DTE-0 activity snapshot per ticker/vendor activity
date. DTE 0 reads only its previous 20 snapshots; nonzero DTE uses bounded same-bucket peers.
Discovery confirmation is derived after these independent evidence tracks, while eligibility remains
based on their original uncombined thresholds.

Phase 2A v1.3 adds three independent discovery routes: `RADAR_EVENT`,
`PERSISTENT_POSITIONING`, and `EXPIRY_ACTIVITY`. Route priority controls presentation and finite
chain-analysis resources only; no cross-route score or average exists. The externally scheduled
`python -m app.cli archive-mag7-daily` runs OI Archive, Activity Snapshot, and OI Change Radar as
independent subjobs. Interactive scans reuse the latest persisted Radar evidence.

Radar materiality uses a runtime-injected profile. The evaluator contains no Premium or OI numeric
threshold. Each daily run and Radar event stores the profile ID, immutable version, effective values,
and configuration hash. Future profile variants fit the JSON snapshot without a schema redesign;
changing an active profile never recalculates historical rows.

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
# Phase 2B v3 research projection

The Phase 2B v3 workspace is a read/derive/persist layer over immutable v1/v2 evidence. The
transport layer is not imported by `app.confirmation.workspace_v3`; the CLI reads PostgreSQL only.
Normalized GEX structural results reference the existing ticker context and raw evidence IDs rather
than duplicating the full vendor payload. FastAPI exposes the result additively, and the Next.js
browser surface uses only the fixed backend proxy.

# Phase 2B v3.1 Dealer/GEX archive

The independent `app.dealer_archive` layers separate XNYS session planning, full-surface
normalization, append-only PostgreSQL persistence, and sequential Nightwatch orchestration. A
durable external scheduler invokes the CLI; FastAPI does not run a background scheduler. Usable
surfaces are stored as snapshot plus expiration/strike cells, while incomplete and unavailable
attempts remain explicit and cannot become a zero surface.

New v3.1 candidate workspaces query the archive repository with both vendor-time and capture-time
cutoffs. This database read does not import or invoke transport. The full archive supports future
calibration, but current candidate analysis remains anchor plus nearest previous/next expiry and
does not compute outcomes or actionability.

# Phase 2B v3.1 GitHub Actions First Manual Run — Forensic Diagnosis

Date: 2026-08-15

## Classification

**A. `ROOT_CAUSE_CONFIRMED_REQUEST_SHAPE`**

Qualification: GitHub Actions itself made **zero new Nightwatch requests**. It reused an earlier
pre-recovery `PARTIAL` archive run whose requests used `?format=full`. That stale result caused
exit code 4.

## Executed revision

- Workflow run: `31819527578`
- Event: `workflow_dispatch`
- Branch: `main`
- Executed SHA: `fc050d8fcacc495293fd66f4892ff3d4afbf241f`
- Expected SHA matched: YES
- Recovery SHA `45d3d7e369e1cd597a4cceaa4804e5b8e0209622` is an ancestor: YES
- Local and `origin/main` remained at the executed SHA during diagnosis.
- Working tree was clean before this evidence document was created.

## Executed transport source

At the executed SHA:

- `endpoint_format` defaults to `None`.
- Active production config does not set `endpoint_format`.
- Service constructs `request_parameters=None`.
- Client receives `params=None`.
- Schema profile is `nightwatch_dealer_heatmap_default_v1`.
- Default config version is `2026-08-14.v3.1.1`.
- No literal `format=full` production implementation exists.

There is a generic conditional builder for `?format={endpoint_format}`, but it is used only when a
caller programmatically supplies a non-null `endpoint_format`. No Settings field or environment
variable maps to it.

## What the GitHub run actually did

The capture step began at approximately `2026-08-14T16:29:24Z`.

The returned archive run had this persisted identity:

- Archive run ID: `4f7a068d-2461-49e6-a200-9b185fad688d`
- Trigger: `cli`, not `external_scheduler`
- Started: `2026-08-14T11:29:46Z`
- Completed: `2026-08-14T11:30:10Z`
- Config version: `2026-08-14.v3.1`
- Schema profile: `nightwatch_dealer_heatmap_full_v1`
- Persisted `endpoint_format`: historical full-format profile
- Status: `PARTIAL`

This row existed approximately five hours before the GitHub job. The service's idempotency lookup
matched the same:

- NY market date;
- intended capture slot;
- MAG7 scope key.

It therefore returned the existing run summary before creating a new run or calling Nightwatch.

Consequently:

- New GitHub Nightwatch attempts: **0**.
- Displayed `network_attempts=7`: counters from the reused old run.
- Displayed HTTP 400 results: snapshots from the reused old run.
- Exit code 4: current CLI correctly treated the reused `PARTIAL` status as failure.

## Exact request answer

The failed GitHub execution itself called neither request shape because it made no Nightwatch
request.

The earlier persisted run it reused called:

```text
GET /v1/derived/heatmap/{ticker}/snapshot?format=full
```

The accepted recovery profile remains:

```text
GET /v1/derived/heatmap/{ticker}/snapshot
```

with no query parameters.

## Persisted attempt evidence

| Ticker | HTTP | Persisted path | Query in path field | Parameter keys | Safe error | Profile |
|---|---:|---|---|---|---|---|
| AAPL | 400 | `/v1/derived/heatmap/AAPL/snapshot` | No | `format` | `VALIDATION_ERROR`; message not persisted | `2026-08-14.v3.1` / `nightwatch_dealer_heatmap_full_v1` |
| MSFT | 400 | `/v1/derived/heatmap/MSFT/snapshot` | No | `format` | `VALIDATION_ERROR`; message not persisted | same |
| NVDA | 400 | `/v1/derived/heatmap/NVDA/snapshot` | No | `format` | `VALIDATION_ERROR`; message not persisted | same |
| AMZN | 400 | `/v1/derived/heatmap/AMZN/snapshot` | No | `format` | `VALIDATION_ERROR`; message not persisted | same |
| META | 400 | `/v1/derived/heatmap/META/snapshot` | No | `format` | `VALIDATION_ERROR`; message not persisted | same |
| GOOGL | 400 | `/v1/derived/heatmap/GOOGL/snapshot` | No | `format` | `VALIDATION_ERROR`; message not persisted | same |
| TSLA | 400 | `/v1/derived/heatmap/TSLA/snapshot` | No | `format` | `VALIDATION_ERROR`; message not persisted | same |

The persisted endpoint column stores the path separately, hence it contains no `?`. The persisted
parameter object and historical config prove that the HTTP client added the `format=full` query
parameter.

- Raw error payloads persisted: **0**.
- API usage observations and unavailable snapshots were persisted.
- Safe vendor error message: not persisted.
- Safe vendor error code: `VALIDATION_ERROR`.

## Configuration resolution

Endpoint construction is influenced by:

- `NIGHTWATCH_BASE_URL`: host only; defaults to the accepted vendor base URL.
- `DEALER_GEX_ENDPOINT_TEMPLATE`: fixed path template.
- MAG7 ticker universe: supplies the ticker path segment.
- `DealerGexArchiveConfig.endpoint_format`: optional query parameter, not environment-backed.

The workflow supplies only:

- `DATABASE_URL`
- `NIGHTWATCH_API_KEY`

It supplies no base-URL, endpoint-format, archive-profile, or Dealer/GEX override variable.

The local `.env` also contains none of those optional endpoint/archive override keys. Absence of
`.env` on GitHub therefore does not change request construction.

## Runtime secret configuration

- `NIGHTWATCH_API_KEY` existed and was non-empty during the job: **YES**.
- `DATABASE_URL` existed and was non-empty during the job: **YES**.

This is proven by the successful required-configuration step. It does not prove or disprove API-key
validity because the GitHub runner made no Nightwatch request.

No secret value, prefix, suffix, length, hash, Authorization header, or database connection string
was inspected or recorded.

## Material profile differences

| Property | Reused old run | Executed recovery source |
|---|---|---|
| Request query | `format=full` | none |
| Parameters | `format` key | `params=None` |
| Config version | `2026-08-14.v3.1` | `2026-08-14.v3.1.1` |
| Schema profile | `nightwatch_dealer_heatmap_full_v1` | `nightwatch_dealer_heatmap_default_v1` |
| Trigger | `cli` | would be `external_scheduler` for a new run |
| Request time | `11:29–11:30Z` | no GitHub request |
| Raw payloads | none for HTTP errors | not applicable |

## Safety record

- Code modified during diagnosis: NO.
- Secrets modified during diagnosis: NO.
- Database rows modified during diagnosis: NO.
- GitHub workflow rerun: NO.
- Nightwatch calls made during diagnosis: 0.
- PostgreSQL access: transaction-read-only.
- Authorization headers or secrets exposed: NO.

External read-only contacts during diagnosis:

- GitHub Actions run metadata and logs for
  `https://github.com/lililinuk/options-anomaly-scanner/actions/runs/31819527578`.
- The configured development PostgreSQL database through the existing application session factory;
  its credential-bearing address is intentionally not recorded.

No Nightwatch endpoint was contacted.

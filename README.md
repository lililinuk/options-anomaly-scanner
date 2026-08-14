# Options Anomaly Scanner

Production-oriented research infrastructure for evidence-backed US equity-options positioning research. The current immutable financial specification is `signal_spec_v1.3_phase2a`; it uses independent Radar Event, Persistent Positioning, and Expiry Activity discovery routes without a universal cross-route score. Accepted v1.0/v1.1/v1.2 history remains immutable.

## Architecture

```text
Nightwatch REST API -> Python transport -> raw ingestion -> PostgreSQL
                                            |                 |
                                      normalization      FastAPI -> Next.js
                                            |
                              versioned Phase 2A analytics
```

The browser talks only to FastAPI. Nightwatch credentials and calls remain in the backend.

## Backend setup

Python 3.10+ and PostgreSQL 14+ are supported.

```powershell
cd backend
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -e ".[dev]"
Copy-Item ..\.env.example ..\.env
python -m alembic upgrade head
python -m uvicorn app.main:app --reload
```

After migrations are applied, the supported manual operations are:

```powershell
cd backend
python -m app.cli refresh-metadata
python -m app.cli archive-mag7-oi
python -m app.cli archive-mag7-daily
python -m app.cli capture-dealer-gex-archive --dry-run
python -m app.cli capture-dealer-gex-archive
python -m app.cli run-mag7-scan
```

`refresh-metadata` calls only the metadata discovery route. `archive-mag7-oi` remains the backwards-compatible idempotent OI archive. `archive-mag7-daily` independently runs Daily OI, Daily Activity, and Daily OI Change Radar subjobs. `run-mag7-scan` refreshes expiry activity and reuses persisted OI, Radar, and Persistent evidence; it does not call OI Change Radar or rebuild the archive. None of these commands prints the API key.

`capture-dealer-gex-archive` is the independent Phase 2B v3.1 append-only full-surface Dealer/GEX capture. It runs MAG7 sequentially with zero retries, accepts `--ticker NVDA` for a bounded diagnostic, and never computes a trading recommendation or actionability result.

The repository intentionally does not run a durable in-process scheduler. Deployment must invoke `archive-mag7-daily` externally at `Asia/Singapore` 12:00 and `capture-dealer-gex-archive --scheduled` near `America/New_York` 15:30 on XNYS sessions. Capture time, vendor observation date/as-of, and New York market date are stored separately; same vendor observations do not duplicate history.

Run tests:

```powershell
cd backend
python -m pytest
```

If Docker is available, `docker compose up -d postgres` starts the optional development database. Docker is not required; an ordinary local or remote PostgreSQL instance works with `DATABASE_URL`.

## Frontend setup

```powershell
cd frontend
npm install
npm run dev
```

Validation:

```powershell
npm run lint
npm run build
```

Set `BACKEND_INTERNAL_URL` to this project's FastAPI URL. The browser requests the fixed same-origin `/api/system-status` route; Next.js proxies that request to FastAPI. Never put a Nightwatch key or Nightwatch base URL in a public frontend variable.

## Configuration

Copy `.env.example` to `.env` at the repository root. Pydantic validates backend settings. Radar thresholds are runtime configuration under a profile ID and immutable version. Every event/run stores the profile identity, effective values, and configuration hash, so activating a new version never rewrites historical eligibility. The JSON snapshot permits future profile shapes without a schema redesign. Secrets remain server-side.

See [system architecture](docs/architecture/SYSTEM_ARCHITECTURE.md), [signal specification](docs/specifications/SIGNAL_SPECIFICATION_V1.md), [scan orchestration](docs/specifications/SCAN_ORCHESTRATION_V1.md), [signal scope](docs/specifications/SIGNAL_ENGINE_SCOPE.md), and [vendor capabilities](docs/vendor/NIGHTWATCH_CAPABILITIES.md).

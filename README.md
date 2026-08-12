# Options Anomaly Scanner

Production-oriented research infrastructure for evidence-backed US equity-options positioning research. The current immutable financial specification is `signal_spec_v1.1_phase2a`; it separates same-day expiry activity from daily OI positioning history and does not infer investor direction or Tradeability.

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
python -m app.cli run-mag7-scan
```

`refresh-metadata` calls only the metadata discovery route. `archive-mag7-oi` is the idempotent 0–180 DTE daily OI archive job and uses the vendor OI observation date as its identity. `run-mag7-scan` refreshes the current activity surface and reuses the latest valid archive; it does not rebuild the archive. None of these commands prints the API key.

The repository intentionally does not run a durable in-process scheduler. Production deployment must invoke `archive-mag7-oi` externally at the configured `Asia/Singapore` trigger time; vendor date/as-of remains authoritative, and same-date runs skip without duplicating history.

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

Copy `.env.example` to `.env` at the repository root. Pydantic validates backend settings. Financial thresholds, component anchors, request budgets, universe, and archive trigger settings are versioned configuration. Secrets remain server-side.

See [system architecture](docs/architecture/SYSTEM_ARCHITECTURE.md), [signal specification](docs/specifications/SIGNAL_SPECIFICATION_V1.md), [scan orchestration](docs/specifications/SCAN_ORCHESTRATION_V1.md), [signal scope](docs/specifications/SIGNAL_ENGINE_SCOPE.md), and [vendor capabilities](docs/vendor/NIGHTWATCH_CAPABILITIES.md).

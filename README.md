# Options Anomaly Scanner

Production-oriented research infrastructure for detecting unusual US equity-options positioning and, in later phases, ranking tradeable candidates. Phase 1 establishes the data, API, observability, and dashboard foundation. It deliberately contains no financial scoring formulas or directional trade signals.

## Architecture

```text
Nightwatch REST API -> Python transport -> raw ingestion -> PostgreSQL
                                            |                 |
                                      normalization      FastAPI -> Next.js
                                            |
                                  future analytics engine
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

After migrations are applied, refresh zero-quota account metadata manually:

```powershell
cd backend
python -m app.cli refresh-metadata
```

This command preflights PostgreSQL, calls only `GET /v1/discover`, stores the raw response, normalized capability snapshot, and API-usage observation, then verifies read-back. It is never scheduled automatically and never prints the API key.

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

Copy `.env.example` to `.env` at the repository root. Pydantic validates backend settings. The future scan cadence, DTE bucket rules, thresholds, and weights are configuration concerns; production scheduling and financial logic are intentionally not implemented in Phase 1.

See [system architecture](docs/architecture/SYSTEM_ARCHITECTURE.md), [runtime validation](docs/architecture/PHASE1_RUNTIME_VALIDATION.md), [signal scope](docs/specifications/SIGNAL_ENGINE_SCOPE.md), and [vendor capabilities](docs/vendor/NIGHTWATCH_CAPABILITIES.md).

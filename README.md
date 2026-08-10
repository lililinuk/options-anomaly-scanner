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

Set `NEXT_PUBLIC_API_BASE_URL` to this project's FastAPI URL. Never put a Nightwatch key or Nightwatch base URL in a public frontend variable.

## Configuration

Copy `.env.example` to `.env` at the repository root. Pydantic validates backend settings. The future scan cadence, DTE bucket rules, thresholds, and weights are configuration concerns; production scheduling and financial logic are intentionally not implemented in Phase 1.

See [system architecture](docs/architecture/SYSTEM_ARCHITECTURE.md), [signal scope](docs/specifications/SIGNAL_ENGINE_SCOPE.md), and [vendor capabilities](docs/vendor/NIGHTWATCH_CAPABILITIES.md).


from types import SimpleNamespace

from fastapi.testclient import TestClient
from sqlalchemy.exc import SQLAlchemyError

from app.api.routes.scans import _max_numeric
from app.db.session import get_db_session
from app.main import app
from app.scanner.service import ConcurrentScanError


def test_application_health_is_utc_and_does_not_contact_vendor() -> None:
    response = TestClient(app).get("/api/v1/health")

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "ok"
    assert payload["checked_at"].endswith("Z")


def test_system_status_is_truthful_phase_one_placeholder() -> None:
    refresh = SimpleNamespace(detected_at=None, observed_at="2026-08-10T12:00:00Z")
    usage = SimpleNamespace(
        http_status=200,
        quota_limit=100000,
        quota_remaining=99999,
        rate_limit=60,
        rate_limit_remaining=58,
    )

    class FakeSession:
        def __init__(self) -> None:
            self.values = iter([refresh, usage])
            self.scalar_statements = []

        def execute(self, _statement):  # type: ignore[no-untyped-def]
            return None

        def scalar(self, _statement):  # type: ignore[no-untyped-def]
            self.scalar_statements.append(_statement)
            return next(self.values)

    session = FakeSession()
    app.dependency_overrides[get_db_session] = lambda: session
    try:
        response = TestClient(app).get("/api/v1/system/status")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json() == {
        "scanner_status": "not_scheduled",
        "latest_scan_at": None,
        "nightwatch_status": "connected",
        "latest_capability_refresh_at": "2026-08-10T12:00:00Z",
        "quota_limit": 100000,
        "quota_remaining": 99999,
        "rate_limit": 60,
        "rate_limit_remaining": 58,
        "latest_request_status": 200,
        "database_status": "connected",
        "scheduling_enabled": False,
    }
    assert "/v1/discover" not in str(session.scalar_statements[1])


def test_system_status_reports_database_unavailable_without_vendor_call() -> None:
    class OfflineSession:
        def execute(self, _statement):  # type: ignore[no-untyped-def]
            raise SQLAlchemyError("fixture database offline")

    app.dependency_overrides[get_db_session] = lambda: OfflineSession()
    try:
        response = TestClient(app).get("/api/v1/system/status")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json()["database_status"] == "unavailable"
    assert response.json()["nightwatch_status"] == "unknown"


def test_latest_mag7_scan_has_safe_empty_state() -> None:
    class EmptySession:
        def scalar(self, _statement):  # type: ignore[no-untyped-def]
            return None

    app.dependency_overrides[get_db_session] = lambda: EmptySession()
    try:
        response = TestClient(app).get("/api/v1/scans/mag7/latest")
    finally:
        app.dependency_overrides.clear()
    assert response.status_code == 200
    assert response.json() == {"scan": None, "results": []}


def test_latest_scan_numeric_summary_ignores_unavailable_values() -> None:
    assert _max_numeric([None, 82, None]) == 82.0
    assert _max_numeric([None, None]) is None


def test_concurrent_mag7_scan_is_rejected(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    async def conflict(*_args, **_kwargs):  # type: ignore[no-untyped-def]
        raise ConcurrentScanError("already running")

    monkeypatch.setattr("app.api.routes.scans.Mag7Scanner.execute", conflict)
    app.dependency_overrides[get_db_session] = lambda: object()
    try:
        response = TestClient(app).post("/api/v1/scans/mag7")
    finally:
        app.dependency_overrides.clear()
    assert response.status_code == 409
    assert "already running" in response.json()["detail"]

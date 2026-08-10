from fastapi.testclient import TestClient

from app.main import app


def test_application_health_is_utc_and_does_not_contact_vendor() -> None:
    response = TestClient(app).get("/api/v1/health")

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "ok"
    assert payload["checked_at"].endswith("Z")


def test_system_status_is_truthful_phase_one_placeholder() -> None:
    response = TestClient(app).get("/api/v1/system/status")

    assert response.status_code == 200
    assert response.json() == {
        "scanner_status": "not_scheduled",
        "latest_scan_at": None,
        "nightwatch_status": "not_checked",
        "quota_remaining": None,
        "scheduling_enabled": False,
    }


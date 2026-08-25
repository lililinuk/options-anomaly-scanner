from datetime import date, datetime, timezone
from types import SimpleNamespace
from uuid import uuid4

from fastapi.testclient import TestClient
from sqlalchemy.exc import SQLAlchemyError

from app.api.routes.scans import _distribution, _max_numeric, _radar_status, _run_state
from app.db.session import get_db_session
from app.main import app
from app.scanner.service import ConcurrentScanError


def test_application_health_is_utc_and_does_not_contact_vendor() -> None:
    with TestClient(app) as client:
        response = client.get("/api/v1/health")

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "ok"
    assert payload["checked_at"].endswith("Z")


def test_candidate_confirmation_reads_persisted_context_only(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    expected = {
        "candidate": {"contract_symbol": "NVDA260821C00220000", "direction": "UNRESOLVED"},
        "dealer": {
            "availability": "UNAVAILABLE",
            "candidate_heatmap_cell_status": "UNAVAILABLE",
            "candidate_net_gex_usd": None,
            "row_stack_status": "ROW_UNAVAILABLE",
            "row_net_gex_usd": None,
            "vendor_row_rank": None,
        },
        "specification_version": "signal_spec_v1.2_phase2b",
    }
    monkeypatch.setattr(
        "app.api.routes.scans.latest_candidate_context", lambda _session, _symbol: expected
    )
    app.dependency_overrides[get_db_session] = lambda: object()
    try:
        with TestClient(app) as client:
            response = client.get(
                "/api/v1/scans/candidates/NVDA260821C00220000/confirmation"
            )
    finally:
        app.dependency_overrides.clear()
    assert response.status_code == 200
    assert response.json() == expected


def test_candidate_confirmation_missing_context_is_404(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    monkeypatch.setattr(
        "app.api.routes.scans.latest_candidate_context", lambda _session, _symbol: None
    )
    app.dependency_overrides[get_db_session] = lambda: object()
    try:
        with TestClient(app) as client:
            response = client.get("/api/v1/scans/candidates/MISSING/confirmation")
    finally:
        app.dependency_overrides.clear()
    assert response.status_code == 404


def test_system_status_is_truthful_phase_one_placeholder() -> None:
    refresh = SimpleNamespace(detected_at=None, observed_at="2026-08-10T12:00:00Z")
    usage = SimpleNamespace(
        http_status=200,
        quota_limit=100000,
        quota_remaining=99999,
        rate_limit=60,
        rate_limit_remaining=58,
    )
    scan = SimpleNamespace(
        status="COMPLETE",
        started_at=datetime(2026, 8, 19, 19, 0, tzinfo=timezone.utc),
        completed_at=datetime(2026, 8, 19, 19, 2, tzinfo=timezone.utc),
        consumed_quota_units=14,
    )
    daily = SimpleNamespace(
        completed_at=datetime(2026, 8, 19, 20, 10, tzinfo=timezone.utc),
        ny_market_date=date(2026, 8, 19),
    )
    dealer = SimpleNamespace(
        vendor_observed_at=datetime(2026, 8, 19, 19, 30, tzinfo=timezone.utc),
        captured_at=datetime(2026, 8, 19, 19, 31, tzinfo=timezone.utc),
    )

    class FakeSession:
        def __init__(self) -> None:
            self.values = iter([refresh, usage, scan, daily, dealer])
            self.scalar_statements = []

        def execute(self, _statement):  # type: ignore[no-untyped-def]
            return None

        def scalar(self, _statement):  # type: ignore[no-untyped-def]
            self.scalar_statements.append(_statement)
            return next(self.values)

    session = FakeSession()
    app.dependency_overrides[get_db_session] = lambda: session
    try:
        with TestClient(app) as client:
            response = client.get("/api/v1/system/status")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json() == {
        "scanner_status": "COMPLETE",
        "latest_scan_at": "2026-08-19T19:02:00Z",
        "latest_scan_status": "COMPLETE",
        "latest_scan_started_at": "2026-08-19T19:00:00Z",
        "latest_scan_completed_at": "2026-08-19T19:02:00Z",
        "latest_scan_consumed_quota_units": 14,
        "nightwatch_status": "connected",
        "latest_capability_refresh_at": "2026-08-10T12:00:00Z",
        "quota_limit": 100000,
        "quota_remaining": 99999,
        "rate_limit": 60,
        "rate_limit_remaining": 58,
        "latest_request_status": 200,
        "database_status": "connected",
        "scheduling_enabled": False,
        "daily_collection_last_success_at": "2026-08-19T20:10:00Z",
        "daily_collection_market_date": "2026-08-19",
        "dealer_archive_last_vendor_observed_at": "2026-08-19T19:30:00Z",
        "dealer_archive_last_captured_at": "2026-08-19T19:31:00Z",
    }
    assert "/v1/discover" not in str(session.scalar_statements[1])


def test_system_status_reports_database_unavailable_without_vendor_call() -> None:
    class OfflineSession:
        def execute(self, _statement):  # type: ignore[no-untyped-def]
            raise SQLAlchemyError("fixture database offline")

    app.dependency_overrides[get_db_session] = lambda: OfflineSession()
    try:
        with TestClient(app) as client:
            response = client.get("/api/v1/system/status")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json()["database_status"] == "unavailable"
    assert response.json()["nightwatch_status"] == "unknown"


def test_latest_mag7_scan_has_safe_empty_state() -> None:
    class EmptySession:
        def scalar(self, _statement):  # type: ignore[no-untyped-def]
            return None

        def scalars(self, _statement):  # type: ignore[no-untyped-def]
            return []

    app.dependency_overrides[get_db_session] = lambda: EmptySession()
    try:
        with TestClient(app) as client:
            response = client.get("/api/v1/scans/mag7/latest")
    finally:
        app.dependency_overrides.clear()
    assert response.status_code == 200
    payload = response.json()
    assert payload["run_state"] == "NOT_RUN"
    assert payload["scan"] is None
    assert payload["legacy_phase2a"] is None
    assert payload["specification_version"] == "phase2a_vnext_stage4b"
    assert payload["architecture"] == {
        "active_discovery": ["RADAR_EVENT", "EXPIRY_ACTIVITY", "CONTRACT_PERSISTENCE"],
        "removed_active_discovery": [
            "EXPIRY_PERSISTENCE",
            "STRUCTURAL_COLD_START",
            "EVIDENCE_BREADTH",
        ],
        "candidate_entity": "TICKER_PRODUCT_PROJECTION",
        "anomaly_entity": "CONTRACT_OR_EXPIRY",
        "persisted_product_candidate_created": False,
    }
    assert payload["research_candidates"] == []
    assert payload["anomaly_pool"] == []
    assert payload["route_counts"] == {
        "radar_events": 0,
        "expiry_activity": 0,
        "contract_persistence_current_triggers": 0,
        "contract_persistence_analytics": 0,
        "product_candidates": 0,
    }
    assert payload["persistence_current_trigger_freshness"]["mode"] == (
        "CALIBRATION_REQUIRED"
    )


def test_scan_run_state_distinguishes_success_failure_running_and_not_run() -> None:
    assert _run_state(None, candidate_count=0) == "NOT_RUN"
    assert _run_state(SimpleNamespace(status="RUNNING"), candidate_count=0) == "RUNNING"
    assert _run_state(SimpleNamespace(status="FAILED"), candidate_count=0) == "FAILED"
    assert _run_state(SimpleNamespace(status="PARTIAL"), candidate_count=1) == "FAILED"
    assert (
        _run_state(SimpleNamespace(status="COMPLETE"), candidate_count=0)
        == "SUCCESS_NO_CANDIDATE"
    )
    assert (
        _run_state(SimpleNamespace(status="COMPLETE"), candidate_count=1)
        == "SUCCESS_WITH_CANDIDATES"
    )


def test_latest_scan_numeric_summary_ignores_unavailable_values() -> None:
    assert _max_numeric([None, 82, None]) == 82.0
    assert _max_numeric([None, None]) is None


def test_radar_status_distinguishes_absence_from_not_tested() -> None:
    assert _radar_status("NVDA", {"NVDA"}, {"NVDA"}) == "OBSERVED"
    assert _radar_status("META", {"META"}, set()) == "NOT_OBSERVED"
    assert _radar_status("MSFT", set(), set()) == "NOT_TESTED"


def test_discovery_distribution_counts_unavailable_and_cold_start() -> None:
    def row(score, *, same=None, persistent=None, status=None, cold=False):  # type: ignore[no-untyped-def]
        return SimpleNamespace(
            dte_at_detection=1,
            discovery_score=score,
            same_day_activity_score=same,
            persistent_positioning_score=persistent,
            same_day_baseline_status=status,
            structural_cold_start_eligible=cold,
        )

    result = _distribution([
        row(95, same=95), row(85, same=85), row(70, persistent=70),
        row(50, same=50), row(20, same=20),
        row(None, status="INSUFFICIENT"), row(None, cold=True),
    ])
    assert result == {
        "total_expiries": 7, "scored_expiries": 5, "normal_eligible_expiries": 4,
        "discovery_90_plus": 1, "discovery_80_89": 1, "discovery_65_79": 1,
        "discovery_40_64": 1, "discovery_below_40": 1,
        "unavailable": 2, "cold_start": 2,
    }


def test_concurrent_mag7_scan_is_rejected(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    async def conflict(*_args, **_kwargs):  # type: ignore[no-untyped-def]
        raise ConcurrentScanError("already running")

    monkeypatch.setattr("app.api.routes.scans.Mag7Scanner.execute", conflict)
    app.dependency_overrides[get_db_session] = lambda: object()
    try:
        with TestClient(app) as client:
            response = client.post("/api/v1/scans/mag7")
    finally:
        app.dependency_overrides.clear()
    assert response.status_code == 409
    assert "already running" in response.json()["detail"]


def test_dealer_gex_history_api_reads_persisted_diagnostics_only(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    run = SimpleNamespace(
        id=uuid4(), status="PARTIAL",
        started_at=datetime(2026, 8, 14, 19, 30, tzinfo=timezone.utc),
        completed_at=datetime(2026, 8, 14, 19, 31, tzinfo=timezone.utc),
        ny_market_date=date(2026, 8, 14), intended_capture_slot="15:30",
        market_timezone="America/New_York", tickers_attempted=7,
        tickers_succeeded=6, tickers_failed=1, network_attempts=7,
        consumed_quota_units=6, specification_version="signal_spec_v3.1_phase2b",
    )
    monkeypatch.setattr(
        "app.api.routes.dealer_gex.dealer_gex_history_coverage",
        lambda _session, tickers: [
            {"ticker": ticker, "distinct_valid_observations": 1} for ticker in tickers
        ],
    )
    app.dependency_overrides[get_db_session] = lambda: SimpleNamespace(
        scalar=lambda _statement: run
    )
    try:
        with TestClient(app) as client:
            response = client.get("/api/v1/dealer-gex/history")
    finally:
        app.dependency_overrides.clear()
    assert response.status_code == 200
    payload = response.json()
    assert payload["archive"]["consumed_quota_units"] == 6
    assert len(payload["history_coverage"]) == 7
    assert payload["semantics"]["unavailable_is_zero"] is False
    assert payload["semantics"]["analysis_labels_computed"] is False

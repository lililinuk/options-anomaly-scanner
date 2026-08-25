from __future__ import annotations

import inspect
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from types import SimpleNamespace
from uuid import UUID, uuid4

import pytest
from fastapi.testclient import TestClient

import app.scanner.v11 as scanner_v11
from app.api.routes.scans import latest_mag7_scan
from app.db.models import ProductCandidate, ProductCandidateTrigger, ScanRun
from app.db.session import get_db_session
from app.main import app
from app.scanner.candidate_persistence import (
    MATERIALIZATION_RULE_VERSION,
    materialize_successful_scan_candidates,
    persist_candidate_projection,
    product_candidate_public,
)
from app.scanner.candidate_projection import Stage4CandidateProjection
from app.scanner.vnext import group_product_candidates

UTC = timezone.utc
MATERIALIZED_AT = datetime(2026, 8, 18, 20, 30, tzinfo=UTC)


class MemorySession:
    def __init__(self) -> None:
        self.candidates: list[ProductCandidate] = []
        self.scalar_calls = 0
        self.scalars_calls = 0
        self.write_calls = 0

    def add(self, row: object) -> None:
        self.write_calls += 1
        if isinstance(row, ProductCandidate):
            self.candidates.append(row)

    def flush(self) -> None:
        self.write_calls += 1

    def commit(self) -> None:
        self.write_calls += 1

    def rollback(self) -> None:
        return None

    def scalar(self, _statement: object) -> None:
        self.scalar_calls += 1
        return None

    def scalars(self, statement: object) -> list[object]:
        self.scalars_calls += 1
        if "FROM product_candidates" in str(statement):
            return list(self.candidates)
        return []


def _run(*, status: str = "COMPLETE") -> ScanRun:
    return ScanRun(
        id=uuid4(),
        trigger="test",
        status=status,
        started_at=MATERIALIZED_AT - timedelta(minutes=5),
        completed_at=MATERIALIZED_AT if status == "COMPLETE" else None,
        configuration_snapshot={
            "version": "phase2a_vnext_stage4b",
            "active_discovery_families": [
                "RADAR_EVENT",
                "EXPIRY_ACTIVITY",
                "CONTRACT_PERSISTENCE",
            ],
            "persistence_current_trigger": {
                "mode": "CALIBRATION_REQUIRED",
                "config_version": "2026-08-18.calibration-required.v1",
            },
        },
        specification_version="phase2a_vnext_stage4b",
        market_date=date(2026, 8, 18),
        summary={},
    )


def _anomaly(
    ticker: str,
    family: str,
    *,
    qualifies: bool,
    source_id: UUID | None = None,
    observed_at: datetime = MATERIALIZED_AT - timedelta(minutes=1),
    deep_dive_selected: bool = False,
) -> dict[str, object]:
    source_id = source_id or uuid4()
    is_expiry = family == "EXPIRY_ACTIVITY"
    is_radar = family == "RADAR_EVENT"
    identity = "2026-08-21" if is_expiry else f"{ticker}260821C00100000"
    return {
        "ticker": ticker,
        "evidence_family": family,
        "anomaly_entity": "EXPIRY" if is_expiry else "CONTRACT",
        "anomaly_identity": identity,
        "evidence_date": "2026-08-18",
        "qualifies_current_candidate": qualifies,
        "source_evidence_identity": (
            f"expiry_observation:{source_id}"
            if is_expiry
            else f"oi_change_radar_observation:{source_id}"
            if is_radar
            else f"contract_scan_observation:{source_id}"
        ),
        "source_radar_observation_id": str(source_id) if is_radar else None,
        "source_expiry_observation_id": str(source_id) if is_expiry else None,
        "source_contract_observation_id": (
            str(source_id) if not is_expiry and not is_radar else None
        ),
        "source_raw_payload_id": None,
        "trigger_first_knowledge_at": observed_at,
        "source_first_received_at": observed_at - timedelta(minutes=2),
        "vendor_observed_at": observed_at - timedelta(minutes=3),
        "local_captured_at": observed_at - timedelta(minutes=2),
        "source_ids": {
            "raw_payload_ids": [],
            "source_request_ids": [f"request-{source_id}"],
        },
        "source_time_provenance": {},
        "specification_version": "phase2a_vnext_stage4b",
        "current_trigger_freshness": (
            {"mode": "CALIBRATION_REQUIRED", "state": "CALIBRATION_REQUIRED"}
            if family == "CONTRACT_PERSISTENCE"
            else None
        ),
        "deep_dive_selected_for_current_run": deep_dive_selected,
    }


def _projection(anomalies: list[dict[str, object]]) -> Stage4CandidateProjection:
    return Stage4CandidateProjection(
        radar_rows=[],
        persistence_rows=[],
        persistence_analytics=[],
        activity_rows=[],
        anomaly_pool=anomalies,
        product_candidates=group_product_candidates(anomalies),
    )


def test_seven_candidates_persist_before_four_ticker_deep_dive_budget() -> None:
    tickers = ("AAPL", "AMZN", "GOOGL", "META", "MSFT", "NVDA", "TSLA")
    anomalies = [
        _anomaly(
            ticker,
            "EXPIRY_ACTIVITY",
            qualifies=True,
            deep_dive_selected=index < 4,
        )
        for index, ticker in enumerate(tickers)
    ]
    anomalies.append(
        _anomaly("NVDA", "CONTRACT_PERSISTENCE", qualifies=False)
    )
    projection = _projection(anomalies)
    session = MemorySession()
    run = _run()

    persisted = persist_candidate_projection(
        session,
        run,
        projection,
        materialized_at=MATERIALIZED_AT,
    )

    assert len(projection.product_candidates) == 7
    assert sum(
        bool(row.get("deep_dive_selected_for_current_run")) for row in anomalies
    ) == 4
    assert len(persisted) == 7
    assert sum(len(candidate.triggers) for candidate in persisted) == 8
    assert sum(
        trigger.qualifies_candidate
        for candidate in persisted
        for trigger in candidate.triggers
    ) == 7
    assert all(
        candidate.candidate_first_knowledge_at == MATERIALIZED_AT
        for candidate in persisted
    )
    nvda = next(candidate for candidate in persisted if candidate.ticker == "NVDA")
    supporting = next(
        trigger
        for trigger in nvda.triggers
        if trigger.evidence_family == "CONTRACT_PERSISTENCE"
    )
    assert supporting.qualifies_candidate is False
    assert supporting.provenance["current_trigger_freshness"]["mode"] == (
        "CALIBRATION_REQUIRED"
    )


def test_supporting_persistence_alone_materializes_no_candidate_but_freezes_occurrence() -> None:
    anomalies = [_anomaly("AAPL", "CONTRACT_PERSISTENCE", qualifies=False)]
    projection = _projection(anomalies)
    session = MemorySession()
    run = _run()

    persisted = persist_candidate_projection(
        session,
        run,
        projection,
        materialized_at=MATERIALIZED_AT,
    )

    assert projection.product_candidates == []
    assert persisted == []
    assert run.candidate_materialized_at == MATERIALIZED_AT
    assert run.candidate_materialization_rule_version == MATERIALIZATION_RULE_VERSION


def test_candidate_and_trigger_replay_are_idempotent_and_ignore_later_evidence() -> None:
    first = _anomaly("NVDA", "EXPIRY_ACTIVITY", qualifies=True)
    session = MemorySession()
    run = _run()
    persisted = persist_candidate_projection(
        session,
        run,
        _projection([first]),
        materialized_at=MATERIALIZED_AT,
    )
    candidate_id = persisted[0].id
    trigger_ids = [row.id for row in persisted[0].triggers]
    writes_before_replay = session.write_calls

    replayed = materialize_successful_scan_candidates(
        session,
        run,
        materialized_at=MATERIALIZED_AT,
    )

    assert [row.id for row in replayed] == [candidate_id]
    assert [row.id for row in replayed[0].triggers] == trigger_ids
    assert session.write_calls == writes_before_replay
    assert replayed[0].candidate_first_knowledge_at == MATERIALIZED_AT
    assert all(row.present_at_first_knowledge for row in replayed[0].triggers)


def test_duplicate_logical_trigger_input_persists_once_and_conflict_fails_closed() -> None:
    source_id = uuid4()
    logical = _anomaly(
        "MSFT",
        "EXPIRY_ACTIVITY",
        qualifies=True,
        source_id=source_id,
    )
    session = MemorySession()
    persisted = persist_candidate_projection(
        session,
        _run(),
        _projection([logical, dict(logical)]),
        materialized_at=MATERIALIZED_AT,
    )
    assert len(persisted[0].triggers) == 1

    conflicting = dict(logical)
    conflicting["anomaly_identity"] = "2026-08-28"
    with pytest.raises(ValueError, match="Conflicting replay"):
        persist_candidate_projection(
            MemorySession(),
            _run(),
            _projection([logical, conflicting]),
            materialized_at=MATERIALIZED_AT,
        )


def test_first_knowledge_and_trigger_identity_are_immutable() -> None:
    run = _run()
    persisted = persist_candidate_projection(
        MemorySession(),
        run,
        _projection([_anomaly("META", "EXPIRY_ACTIVITY", qualifies=True)]),
        materialized_at=MATERIALIZED_AT,
    )
    candidate = persisted[0]
    trigger = candidate.triggers[0]

    with pytest.raises(ValueError, match="candidate_first_knowledge_at is immutable"):
        candidate.candidate_first_knowledge_at = MATERIALIZED_AT + timedelta(hours=1)
    with pytest.raises(ValueError, match="source_evidence_identity is immutable"):
        trigger.source_evidence_identity = f"expiry_observation:{uuid4()}"
    with pytest.raises(ValueError, match="candidate_materialized_at is immutable"):
        run.candidate_materialized_at = MATERIALIZED_AT + timedelta(hours=1)
    assert candidate.candidate_first_knowledge_at == MATERIALIZED_AT
    assert trigger.present_at_first_knowledge is True


def test_future_trigger_is_rejected_from_first_knowledge_set() -> None:
    future = _anomaly(
        "TSLA",
        "EXPIRY_ACTIVITY",
        qualifies=True,
        observed_at=MATERIALIZED_AT + timedelta(days=1),
    )
    with pytest.raises(ValueError, match="Future trigger evidence"):
        persist_candidate_projection(
            MemorySession(),
            _run(),
            _projection([future]),
            materialized_at=MATERIALIZED_AT,
        )


def test_contract_and_expiry_source_provenance_remain_distinct() -> None:
    radar_source = uuid4()
    expiry_source = uuid4()
    radar = _anomaly("AAPL", "CONTRACT_PERSISTENCE", qualifies=True, source_id=radar_source)
    expiry = _anomaly("AAPL", "EXPIRY_ACTIVITY", qualifies=True, source_id=expiry_source)
    persisted = persist_candidate_projection(
        MemorySession(),
        _run(),
        _projection([radar, expiry]),
        materialized_at=MATERIALIZED_AT,
    )
    triggers = {row.evidence_family: row for row in persisted[0].triggers}

    assert triggers["EXPIRY_ACTIVITY"].anomaly_entity_type == "EXPIRY"
    assert triggers["EXPIRY_ACTIVITY"].source_expiry_observation_id == expiry_source
    assert triggers["EXPIRY_ACTIVITY"].source_contract_observation_id is None
    assert triggers["CONTRACT_PERSISTENCE"].anomaly_entity_type == "CONTRACT"
    assert triggers["CONTRACT_PERSISTENCE"].source_contract_observation_id == radar_source
    assert triggers["CONTRACT_PERSISTENCE"].source_expiry_observation_id is None
    assert triggers["CONTRACT_PERSISTENCE"].source_first_received_at is not None
    assert triggers["CONTRACT_PERSISTENCE"].vendor_observed_at is not None
    assert triggers["CONTRACT_PERSISTENCE"].local_captured_at is not None


def test_all_and_only_active_trigger_families_persist() -> None:
    anomalies = [
        _anomaly("AAPL", "RADAR_EVENT", qualifies=True),
        _anomaly("AAPL", "EXPIRY_ACTIVITY", qualifies=True),
        _anomaly("AAPL", "CONTRACT_PERSISTENCE", qualifies=False),
        {
            **_anomaly("AAPL", "CONTRACT_PERSISTENCE", qualifies=True),
            "evidence_family": "STRUCTURAL_COLD_START",
        },
    ]
    projection = _projection(anomalies)
    assert len(projection.product_candidates[0]["anomalies"]) == 3
    persisted = persist_candidate_projection(
        MemorySession(),
        _run(),
        projection,
        materialized_at=MATERIALIZED_AT,
    )
    assert {row.evidence_family for row in persisted[0].triggers} == {
        "RADAR_EVENT",
        "EXPIRY_ACTIVITY",
        "CONTRACT_PERSISTENCE",
    }


def test_failed_or_running_scan_cannot_materialize_candidates() -> None:
    for status in ("FAILED", "RUNNING", "PARTIAL"):
        session = MemorySession()
        run = _run(status=status)
        assert materialize_successful_scan_candidates(
            session,
            run,
            materialized_at=MATERIALIZED_AT,
        ) == []
        assert run.candidate_materialized_at is None
        assert session.write_calls == 0


def test_success_no_candidate_is_frozen_and_replay_stays_empty() -> None:
    session = MemorySession()
    run = _run()

    assert materialize_successful_scan_candidates(
        session,
        run,
        materialized_at=MATERIALIZED_AT,
    ) == []
    writes_after_first = session.write_calls
    assert run.candidate_materialized_at == MATERIALIZED_AT
    assert materialize_successful_scan_candidates(
        session,
        run,
        materialized_at=MATERIALIZED_AT,
    ) == []
    assert session.write_calls == writes_after_first


def test_get_latest_is_read_only_across_repeated_requests() -> None:
    class EmptyReadSession(MemorySession):
        def scalar(self, _statement: object) -> None:
            return None

        def scalars(self, _statement: object) -> list[object]:
            return []

    session = EmptyReadSession()
    app.dependency_overrides[get_db_session] = lambda: session
    try:
        with TestClient(app) as client:
            assert client.get("/api/v1/scans/mag7/latest").status_code == 200
            assert client.get("/api/v1/scans/mag7/latest").status_code == 200
    finally:
        app.dependency_overrides.clear()
    assert session.write_calls == 0
    assert "materialize_successful_scan_candidates" not in inspect.getsource(
        latest_mag7_scan
    )


def test_backend_read_support_returns_ordered_full_trigger_provenance() -> None:
    anomalies = [
        _anomaly("GOOGL", "CONTRACT_PERSISTENCE", qualifies=False),
        _anomaly("GOOGL", "EXPIRY_ACTIVITY", qualifies=True),
    ]
    candidate = persist_candidate_projection(
        MemorySession(),
        _run(),
        _projection(anomalies),
        materialized_at=MATERIALIZED_AT,
    )[0]
    payload = product_candidate_public(candidate)

    assert payload["ticker"] == "GOOGL"
    assert payload["candidate_first_knowledge_at"] == MATERIALIZED_AT
    assert [row["evidence_family"] for row in payload["triggers"]] == [
        "EXPIRY_ACTIVITY",
        "CONTRACT_PERSISTENCE",
    ]
    assert payload["triggers"][1]["qualifies_candidate"] is False
    assert payload["triggers"][1]["source_ids"]["source_request_ids"]


def test_stage5_schema_is_additive_and_migration_has_no_historical_backfill() -> None:
    assert ProductCandidate.__table__.c.candidate_first_knowledge_at.nullable is False
    assert ProductCandidateTrigger.__table__.c.trigger_first_knowledge_at.nullable is False
    assert ProductCandidateTrigger.__table__.c.vendor_observed_at.nullable is True
    assert ProductCandidateTrigger.__table__.c.source_first_received_at.nullable is True
    migration = (
        Path(__file__).parents[1]
        / "alembic"
        / "versions"
        / "20260818_0016_stage5_product_candidate_persistence.py"
    ).read_text(encoding="utf-8")
    assert 'revision: str = "20260818_0016"' in migration
    assert 'down_revision: str | None = "20260818_0015"' in migration
    assert "op.create_table(" in migration
    assert "op.execute(" not in migration
    assert "UPDATE " not in migration.upper()
    assert "INSERT " not in migration.upper()


def test_authoritative_finish_calls_materializer_only_for_complete(monkeypatch) -> None:
    calls: list[tuple[object, datetime]] = []

    def record(_session: object, run: ScanRun, *, materialized_at: datetime) -> list[object]:
        calls.append((run.id, materialized_at))
        return []

    monkeypatch.setattr(scanner_v11, "materialize_successful_scan_candidates", record)
    for status in ("COMPLETE", "PARTIAL"):
        run = _run(status="COMPLETE")
        session = MemorySession()
        scanner = SimpleNamespace(
            run=run,
            budget=SimpleNamespace(consumed=0, attempts=0),
            cache_hits=0,
            fresh_requests=0,
            session=session,
            _sync_counters=lambda: None,
        )
        scanner_v11.Mag7Scanner._finish_v11(
            scanner,
            status,
            [],
            [],
            [],
            [],
            0,
            0.0,
        )
    assert len(calls) == 1
    assert calls[0][1].tzinfo is not None

from __future__ import annotations

from datetime import date, datetime, timezone
from types import SimpleNamespace
from uuid import uuid4

import pytest

from app.scanner import daily_observation
from app.scanner.config import UNIVERSE
from app.scanner.daily_observation import (
    DailyObservationNotReady,
    expected_previous_xnys_session,
    load_daily_observation_readiness,
    run_daily_vnext_observation,
)
from app.scanner.daily_semantics import radar_oi_schedule_plan


class FakeSession:
    def __init__(self, scalar_batches: list[list[object]], scalar_value: object = None) -> None:
        self.scalar_batches = iter(scalar_batches)
        self.scalar_value = scalar_value
        self.commits = 0

    def scalars(self, _statement: object) -> list[object]:
        return next(self.scalar_batches)

    def scalar(self, _statement: object) -> object:
        return self.scalar_value

    def commit(self) -> None:
        self.commits += 1


def ticker_rows() -> list[SimpleNamespace]:
    return [SimpleNamespace(ticker=ticker) for ticker in UNIVERSE]


def test_expected_previous_session_uses_xnys_over_weekend() -> None:
    assert expected_previous_xnys_session(date(2026, 8, 24)) == date(2026, 8, 21)


def test_scheduled_radar_oi_is_bounded_to_evidence_backed_window() -> None:
    before = radar_oi_schedule_plan(datetime(2026, 8, 24, 9, 59, tzinfo=timezone.utc))
    ready = radar_oi_schedule_plan(datetime(2026, 8, 24, 10, 30, tzinfo=timezone.utc))
    after = radar_oi_schedule_plan(datetime(2026, 8, 24, 12, 1, tzinfo=timezone.utc))
    assert (before.should_collect, before.status) == (False, "SKIPPED_BEFORE_SOURCE_READY")
    assert (ready.should_collect, ready.status) == (True, "READY")
    assert (after.should_collect, after.status) == (False, "SKIPPED_AFTER_SAFE_WINDOW")


def test_scheduled_radar_oi_skips_xnys_holiday() -> None:
    plan = radar_oi_schedule_plan(datetime(2026, 9, 7, 10, 30, tzinfo=timezone.utc))
    assert (plan.should_collect, plan.status) == (False, "SKIPPED_NON_TRADING_SESSION")


def test_readiness_requires_complete_activity_radar_and_daily_oi() -> None:
    session = FakeSession([ticker_rows(), ticker_rows(), ticker_rows()])
    readiness = load_daily_observation_readiness(
        session, evaluated_at=datetime(2026, 8, 24, 21, tzinfo=timezone.utc)
    )
    assert readiness.market_date == date(2026, 8, 24)
    assert readiness.expected_vendor_oi_date == date(2026, 8, 21)
    assert readiness.activity_tickers == tuple(sorted(UNIVERSE))
    assert readiness.radar_tickers == tuple(sorted(UNIVERSE))
    assert readiness.oi_archive_tickers == tuple(sorted(UNIVERSE))


def test_readiness_fails_closed_before_scan_when_source_is_missing() -> None:
    session = FakeSession([ticker_rows()[:-1], ticker_rows(), ticker_rows()])
    with pytest.raises(DailyObservationNotReady, match="ACTIVITY_COVERAGE_INCOMPLETE"):
        load_daily_observation_readiness(
            session, evaluated_at=datetime(2026, 8, 24, 21, tzinfo=timezone.utc)
        )


def test_readiness_forbids_automatic_retry_for_same_market_date() -> None:
    session = FakeSession([ticker_rows(), ticker_rows(), ticker_rows()], scalar_value=uuid4())
    with pytest.raises(DailyObservationNotReady, match="NO_AUTOMATIC_RETRY"):
        load_daily_observation_readiness(
            session, evaluated_at=datetime(2026, 8, 24, 21, tzinfo=timezone.utc)
        )


@pytest.mark.asyncio
async def test_complete_scan_creates_one_archived_baseline_per_candidate(monkeypatch) -> None:
    candidate_ids = [uuid4(), uuid4()]
    created: list[object] = []

    monkeypatch.setattr(
        daily_observation, "load_daily_observation_readiness", lambda *_a, **_k: None
    )

    class Scanner:
        def __init__(self, _session: object, _client: object) -> None:
            pass

        async def execute(self, *, trigger: str) -> SimpleNamespace:
            assert trigger == "scheduled_daily"
            return SimpleNamespace(
                scan_run_id=uuid4(),
                status="COMPLETE",
                consumed_quota_units=14,
                network_attempts=14,
            )

    class Baselines:
        def __init__(self, _session: object) -> None:
            pass

        def create_baseline(self, candidate_id: object) -> object:
            created.append(candidate_id)
            return SimpleNamespace(id=uuid4())

    monkeypatch.setattr(daily_observation, "Mag7Scanner", Scanner)
    monkeypatch.setattr(
        daily_observation,
        "load_product_candidates_for_scan",
        lambda *_a: [SimpleNamespace(id=value) for value in candidate_ids],
    )
    monkeypatch.setattr(daily_observation, "Stage6BalancedContextService", Baselines)
    session = FakeSession([])
    summary = await run_daily_vnext_observation(session, object())
    assert summary.observation_status == "COMPLETE"
    assert summary.candidate_count == 2
    assert summary.baseline_count == 2
    assert created == candidate_ids
    assert session.commits == 1


@pytest.mark.asyncio
async def test_noncomplete_scan_never_attempts_baseline(monkeypatch) -> None:
    monkeypatch.setattr(
        daily_observation, "load_daily_observation_readiness", lambda *_a, **_k: None
    )

    class Scanner:
        def __init__(self, _session: object, _client: object) -> None:
            pass

        async def execute(self, *, trigger: str) -> SimpleNamespace:
            assert trigger == "scheduled_daily"
            return SimpleNamespace(
                scan_run_id=uuid4(),
                status="PARTIAL",
                consumed_quota_units=14,
                network_attempts=14,
            )

    monkeypatch.setattr(daily_observation, "Mag7Scanner", Scanner)
    monkeypatch.setattr(
        daily_observation,
        "load_product_candidates_for_scan",
        lambda *_a: pytest.fail("candidate loading must be skipped"),
    )
    summary = await run_daily_vnext_observation(FakeSession([]), object())
    assert summary.observation_status == "PARTIAL"
    assert summary.baseline_count == 0


@pytest.mark.asyncio
async def test_complete_zero_candidate_scan_is_truthful_success(monkeypatch) -> None:
    monkeypatch.setattr(
        daily_observation, "load_daily_observation_readiness", lambda *_a, **_k: None
    )

    class Scanner:
        def __init__(self, _session: object, _client: object) -> None:
            pass

        async def execute(self, *, trigger: str) -> SimpleNamespace:
            return SimpleNamespace(
                scan_run_id=uuid4(),
                status="COMPLETE",
                consumed_quota_units=14,
                network_attempts=14,
            )

    monkeypatch.setattr(daily_observation, "Mag7Scanner", Scanner)
    monkeypatch.setattr(daily_observation, "load_product_candidates_for_scan", lambda *_a: [])
    summary = await run_daily_vnext_observation(FakeSession([]), object())
    assert summary.observation_status == "SUCCESS_NO_CANDIDATE"
    assert summary.candidate_count == 0
    assert summary.baseline_count == 0

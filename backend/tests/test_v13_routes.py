from datetime import date, datetime, timezone
from decimal import Decimal
from inspect import getsource
from types import SimpleNamespace
from uuid import uuid4

import pytest

from app.api.routes.scans import _deep_dive_public
from app.db.models import DailyCollectionCoverage, OiChangeRadarObservation
from app.scanner.daily import (
    DailyRadarCollector,
    daily_pipeline_status,
    missing_coverage_tickers,
)
from app.scanner.v13 import (
    RadarThresholdProfile,
    deduplicate_deep_dive_requests,
    evaluate_radar_material_event,
    is_standard_monthly_expiry,
    radar_scope,
    resolve_route_state,
    same_day_score_basis,
)


@pytest.fixture
def profile() -> RadarThresholdProfile:
    return RadarThresholdProfile(
        profile_id="test-profile",
        version="test-v1",
        enabled=True,
        min_premium_usd=Decimal("150000"),
        min_abs_oi_diff=2500,
        calibration_review_sessions=20,
    )


@pytest.mark.parametrize(
    ("premium", "oi_diff", "eligible", "reason"),
    [
        (149999, 2500, False, "PREMIUM_BELOW_PROFILE_MINIMUM"),
        (150000, 2499, False, "ABS_OI_DIFF_BELOW_PROFILE_MINIMUM"),
        (150000, 2500, True, "RADAR_MATERIAL_EVENT"),
        (150000, -2500, True, "RADAR_MATERIAL_EVENT"),
        (None, 2500, False, "MISSING_PREMIUM"),
        (150000, None, False, "MISSING_OI_DIFF"),
    ],
)
def test_versioned_radar_gate(
    profile: RadarThresholdProfile,
    premium: int | None,
    oi_diff: int | None,
    eligible: bool,
    reason: str,
) -> None:
    result = evaluate_radar_material_event(
        premium_usd=premium,
        oi_diff=oi_diff,
        previous_oi=100,
        profile=profile,
    )
    assert result.eligible is eligible
    assert result.reason == reason


def test_relative_change_is_not_an_eligibility_input_and_low_base_is_context(
    profile: RadarThresholdProfile,
) -> None:
    result = evaluate_radar_material_event(
        premium_usd=150000,
        oi_diff=2500,
        previous_oi=99,
        profile=profile,
    )
    assert result.eligible
    assert result.risk_flags == ("LOW_OI_BASE",)
    assert "relative" not in getsource(evaluate_radar_material_event)


def test_profile_snapshot_is_versioned_and_hashes_effective_values(
    profile: RadarThresholdProfile,
) -> None:
    changed = RadarThresholdProfile(
        profile_id=profile.profile_id,
        version="test-v2",
        enabled=True,
        min_premium_usd=Decimal("175000"),
        min_abs_oi_diff=profile.min_abs_oi_diff,
        calibration_review_sessions=profile.calibration_review_sessions,
    )
    assert profile.snapshot()["min_premium_usd"] == "150000"
    assert profile.configuration_hash != changed.configuration_hash
    source = getsource(evaluate_radar_material_event)
    assert "150000" not in source
    assert "2500" not in source


@pytest.mark.parametrize(
    ("dte", "matched", "complete", "expected"),
    [
        (30, True, True, "FULL_DEEP_DIVE_ELIGIBLE"),
        (120, True, True, "LONG_DTE_RADAR_WATCH"),
        (181, True, True, "OUTSIDE_ARCHIVE_SCOPE"),
        (30, True, False, "INCOMPLETE_CHAIN"),
        (None, False, False, "UNJOINED"),
    ],
)
def test_radar_archive_scope(
    dte: int | None, matched: bool, complete: bool, expected: str
) -> None:
    assert radar_scope(dte=dte, exact_match=matched, chain_complete=complete) == expected


def test_independent_routes_do_not_require_a_universal_score() -> None:
    radar_only = resolve_route_state(radar_event=True)
    persistent_only = resolve_route_state(contract_persistence=True)
    activity_only = resolve_route_state(expiry_activity=True)
    multiple = resolve_route_state(radar_event=True, expiry_activity=True)
    cold_only = resolve_route_state(structural_cold_start=True)
    assert radar_only.trigger_sources == ("RADAR_EVENT",)
    assert persistent_only.trigger_sources == ("CONTRACT_PERSISTENCE",)
    assert activity_only.trigger_sources == ("EXPIRY_ACTIVITY",)
    assert multiple.trigger_sources == ("RADAR_EVENT", "EXPIRY_ACTIVITY")
    assert cold_only.trigger_sources == ()
    assert cold_only.deep_dive_eligible is False
    assert resolve_route_state(expiry_persistence=True).deep_dive_eligible is False


def test_deep_dive_chain_requests_are_deduplicated_and_keep_sources() -> None:
    expiry = date(2026, 9, 18)
    result = deduplicate_deep_dive_requests(
        [
            ("NVDA", expiry, "RADAR_EVENT"),
            ("NVDA", expiry, "EXPIRY_ACTIVITY"),
            ("NVDA", expiry, "CONTRACT_PERSISTENCE"),
        ]
    )
    assert len(result) == 1
    assert result[("NVDA", expiry)] == [
        "RADAR_EVENT",
        "EXPIRY_ACTIVITY",
        "CONTRACT_PERSISTENCE",
    ]


def test_opex_inference_and_score_basis_are_descriptive_only() -> None:
    assert is_standard_monthly_expiry(date(2026, 8, 21))
    assert not is_standard_monthly_expiry(date(2026, 8, 28))
    assert same_day_score_basis(
        {"expiry_volume_share": 30, "comparable_expiry_volume_neighbor_ratio": 10}
    ) == (30.0, 10.0, "VOLUME_SHARE_DOMINATED")
    assert same_day_score_basis(
        {"expiry_volume_share": 10, "comparable_expiry_volume_neighbor_ratio": 30}
    ) == (10.0, 30.0, "NEIGHBOR_DOMINATED")
    assert same_day_score_basis(
        {"expiry_volume_share": 20, "comparable_expiry_volume_neighbor_ratio": 15}
    ) == (20.0, 15.0, "BALANCED")
    assert same_day_score_basis(
        {"robust_historical_deviation": 70, "historical_percentile": 30}, dte=0
    ) == (None, None, "ZERO_DTE_HISTORICAL_CALIBRATION")


def test_daily_backfill_and_subjob_truth() -> None:
    assert missing_coverage_tickers({"AAPL", "MSFT"}) == (
        "NVDA",
        "AMZN",
        "META",
        "GOOGL",
        "TSLA",
    )
    assert daily_pipeline_status(["COMPLETE", "FAILED", "COMPLETE"]) == "PARTIAL"
    assert daily_pipeline_status(["FAILED", "FAILED", "FAILED"]) == "FAILED"
    assert daily_pipeline_status(["COMPLETE", "NO_NEW_DATA", "COMPLETE"]) == "COMPLETE"


def test_radar_re_evaluation_preserves_original_capture_identity(
    profile: RadarThresholdProfile,
) -> None:
    captured_at = datetime(2026, 8, 13, 12, 0, tzinfo=timezone.utc)
    original_market_date = date(2026, 8, 13)
    row = SimpleNamespace(
        ticker="NVDA",
        contract_symbol="NVDA260821C00220000",
        observation_date=date(2026, 8, 13),
        premium=Decimal("175000"),
        delta_oi=3000,
        previous_oi=1000,
        volume=5000,
        trades=50,
        captured_at=captured_at,
        ny_market_date=original_market_date,
        source_request_id="fixture-radar-request",
    )

    class BackfillSession:
        def __init__(self) -> None:
            self.scalar_results = iter([[row], [], [], []])
            self.added: list[object] = []

        def scalars(self, _statement):  # type: ignore[no-untyped-def]
            return next(self.scalar_results)

        def scalar(self, _statement):  # type: ignore[no-untyped-def]
            return None

        def add(self, item: object) -> None:
            self.added.append(item)

        def commit(self) -> None:
            return None

    session = BackfillSession()
    pipeline = SimpleNamespace(
        session=session,
        run=SimpleNamespace(id=uuid4(), ny_market_date=date(2026, 8, 17)),
        profile=profile,
    )

    DailyRadarCollector(pipeline)._backfill_existing_observations()

    assert row.captured_at == captured_at
    assert row.ny_market_date == original_market_date
    assert row.material_event_eligible is True
    assert len(session.added) == 1
    assert isinstance(session.added[0], DailyCollectionCoverage)


@pytest.mark.asyncio
async def test_new_radar_evidence_persists_once_and_reprocessing_is_idempotent(
    monkeypatch: pytest.MonkeyPatch,
    profile: RadarThresholdProfile,
) -> None:
    observation_date = date(2026, 8, 14)
    item = SimpleNamespace(
        symbol="NVDA260821C00220000",
        observation_date=observation_date,
        previous_date=date(2026, 8, 13),
        previous_oi=1000,
        current_oi=4000,
        delta_oi=3000,
        relative_change=3.0,
        volume=5000,
        trades=50,
        average_price=7.0,
        premium=175000,
        rank=1,
        last_bid=6.9,
        last_ask=7.1,
        last_fill=7.0,
    )

    class RadarSession:
        def __init__(self) -> None:
            # First run: no coverage, no identity match, no archive, no structure.
            # Second run: existing COMPLETE coverage suppresses duplicate persistence.
            self.scalar_results = iter([None, None, None, None, uuid4()])
            self.added: list[object] = []

        def scalars(self, _statement):  # type: ignore[no-untyped-def]
            return []

        def scalar(self, _statement):  # type: ignore[no-untyped-def]
            return next(self.scalar_results)

        def add(self, value: object) -> None:
            self.added.append(value)

        def commit(self) -> None:
            return None

        def rollback(self) -> None:
            return None

    session = RadarSession()
    result = SimpleNamespace(
        payload={"fixture": True},
        vendor_request_id=None,
        request_id="fixture-radar-request",
    )
    raw = SimpleNamespace(id=uuid4())

    async def fetch(*_args, **_kwargs):  # type: ignore[no-untyped-def]
        return result, raw

    pipeline = SimpleNamespace(
        session=session,
        run=SimpleNamespace(id=uuid4(), ny_market_date=date(2026, 8, 17)),
        profile=profile,
        fetch=fetch,
    )
    collector = DailyRadarCollector(pipeline)
    monkeypatch.setattr(collector, "_backfill_existing_observations", lambda: None)
    monkeypatch.setattr(collector, "_target_tickers", lambda: ("NVDA",))
    monkeypatch.setattr("app.scanner.daily.parse_oi_change_radar", lambda _payload: [item])

    first = await collector.execute()
    second = await collector.execute()

    radar_rows = [value for value in session.added if isinstance(value, OiChangeRadarObservation)]
    coverage_rows = [value for value in session.added if isinstance(value, DailyCollectionCoverage)]
    assert first.rows_persisted == 1
    assert second.rows_persisted == 0
    assert len(radar_rows) == 1
    assert len(coverage_rows) == 1
    assert radar_rows[0].captured_at is not None
    assert radar_rows[0].ny_market_date == date(2026, 8, 17)


def test_expiry_only_deep_dive_row_is_explicit_and_has_no_contract_state() -> None:
    expiry = SimpleNamespace(
        deep_dive_eligible=True,
        ticker="MSFT",
        expiration=date(2026, 8, 21),
        trigger_sources=["EXPIRY_ACTIVITY"],
        persistent_positioning_score=None,
        same_day_activity_score=Decimal("72"),
        selected_for_deep_scan=False,
    )
    result = _deep_dive_public([], [], [expiry])
    assert result == [{
        "entity_type": "EXPIRY_ONLY",
        "ticker": "MSFT",
        "contract_or_expiry": "2026-08-21",
        "expiration": "2026-08-21",
        "trigger_sources": ["EXPIRY_ACTIVITY"],
        "radar_premium_usd": None,
        "radar_oi_diff": None,
        "persistent_score": None,
        "expiry_activity_score": 72.0,
        "structure_score": None,
        "archive_completeness": "NOT_LOADED",
        "risk_flags": [],
    }]

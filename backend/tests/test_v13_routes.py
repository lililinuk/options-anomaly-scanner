from datetime import date
from decimal import Decimal
from inspect import getsource

import pytest

from app.scanner.daily import daily_pipeline_status, missing_coverage_tickers
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
    assert cold_only.deep_dive_eligible


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
        "CONTRACT_PERSISTENCE",
        "EXPIRY_ACTIVITY",
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

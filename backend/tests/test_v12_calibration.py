from dataclasses import dataclass
from datetime import date, timedelta

import pytest

from app.scanner.scoring import (
    ComparableExpiry,
    comparable_nonzero_expiry_peers,
    discovery_eligible,
    discovery_with_confirmation,
    zero_dte_activity_score,
)
from app.scanner.selection import select_dual_discovery


def test_zero_dte_requires_twenty_prior_valid_sessions_and_keeps_raw_stats() -> None:
    history = [0.20 + index / 1000 for index in range(19)]
    result = zero_dte_activity_score(0.50, history)
    assert result.score is None
    assert result.status == "INSUFFICIENT"
    assert result.observation_count == 19
    assert result.mean is not None and result.median is not None and result.mad is not None


def test_zero_dte_missing_current_share_is_never_scored() -> None:
    result = zero_dte_activity_score(None, [0.20] * 20)
    assert result.score is None
    assert result.status == "CURRENT_OBSERVATION_UNAVAILABLE"
    assert result.observation_count == 20


def test_exactly_twenty_prior_sessions_excludes_current_and_enables_score() -> None:
    history = [0.10 + index * 0.01 for index in range(20)]
    result = zero_dte_activity_score(0.50, history)
    assert result.observation_count == 20
    assert result.score is not None
    assert result.mean == pytest.approx(sum(history) / 20)
    assert result.median == pytest.approx(0.195)
    assert result.mad == pytest.approx(0.05)
    assert result.percentile == 1
    assert result.robust_deviation == pytest.approx((0.50 - 0.195) / (1.4826 * 0.05))
    assert result.score == 100


def test_valid_session_history_ignores_calendar_gaps_by_construction() -> None:
    dates = [date(2026, 7, 1) + timedelta(days=index * 2) for index in range(20)]
    shares = [0.20 + index / 1000 for index, _date in enumerate(dates)]
    assert zero_dte_activity_score(0.25, shares).observation_count == 20


def test_extreme_prior_observation_does_not_dominate_robust_baseline() -> None:
    history = [0.20] * 10 + [0.21] * 9 + [0.99]
    result = zero_dte_activity_score(0.30, history)
    assert result.mean > 0.24
    assert result.median == pytest.approx(0.205)
    assert result.mad == pytest.approx(0.005)
    assert result.robust_deviation is not None and result.robust_deviation > 4


def test_zero_mad_uses_fixed_scale_percentile_fallback_without_rescaling() -> None:
    result = zero_dte_activity_score(0.20, [0.20] * 20)
    assert result.robust_deviation is None
    assert result.method == "HISTORICAL_PERCENTILE_FALLBACK"
    assert result.basis == 30
    assert result.score == 30
    assert result.missing == ("robust_historical_deviation",)


@pytest.mark.parametrize(
    ("deviation", "expected"), [(1.0, 0), (1.5, 15), (2.0, 30), (3.0, 50), (4.0, 70)]
)
def test_robust_deviation_component_anchors(deviation: float, expected: float) -> None:
    history = [0.10] * 10 + [0.20] * 10
    current = 0.15 + deviation * 1.4826 * 0.05
    result = zero_dte_activity_score(current, history)
    assert result.components["robust_historical_deviation"] == pytest.approx(expected)


@pytest.mark.parametrize(
    ("current", "expected"), [(0.20, 0), (0.255, 10), (0.275, 20), (0.285, 25), (0.50, 30)]
)
def test_historical_percentile_anchors(current: float, expected: float) -> None:
    history = [0.10 + index * 0.01 for index in range(20)]
    result = zero_dte_activity_score(current, history)
    assert result.components["historical_percentile"] == pytest.approx(expected)


@pytest.mark.parametrize(
    ("target", "candidate_dtes", "expected_quality"),
    [(4, [0, 1, 2, 5, 7, 8], "DISTANCE_COMPARABLE"),
     (18, [0, 8, 12, 16, 20, 24, 30, 31], "DISTANCE_COMPARABLE"),
     (60, [0, 31, 46, 55, 65, 74, 80, 91], "DISTANCE_COMPARABLE")],
)
def test_nonzero_peer_buckets_exclude_zero_and_enforce_distance(
    target: int, candidate_dtes: list[int], expected_quality: str
) -> None:
    row = ComparableExpiry(target, 100)
    candidates = [row, *(ComparableExpiry(dte, 50) for dte in candidate_dtes)]
    result = comparable_nonzero_expiry_peers(row, candidates)
    assert 0 not in result.dtes
    assert result.count <= 4
    assert result.quality == expected_quality


def test_peer_selector_prefers_same_verified_type_and_requires_two() -> None:
    target = ComparableExpiry(14, 100, "WEEKLY")
    candidates = [
        target,
        ComparableExpiry(13, 50, "MONTHLY"),
        ComparableExpiry(15, 40, "WEEKLY"),
        ComparableExpiry(16, 60, "WEEKLY"),
        ComparableExpiry(17, 70, "WEEKLY"),
        ComparableExpiry(18, 80, "WEEKLY"),
        ComparableExpiry(19, 90, "WEEKLY"),
    ]
    result = comparable_nonzero_expiry_peers(target, candidates)
    assert result.count == 4
    assert result.dtes == (15, 16, 17, 18)
    assert result.quality == "SAME_VERIFIED_TYPE"
    insufficient_target = ComparableExpiry(6, 100)
    insufficient = comparable_nonzero_expiry_peers(
        insufficient_target, [insufficient_target, ComparableExpiry(7, 50)]
    )
    assert insufficient.ratio is None and insufficient.quality == "INSUFFICIENT"


def test_zero_dte_is_not_applicable_to_ordinary_peer_scoring() -> None:
    zero = ComparableExpiry(0, 1000)
    result = comparable_nonzero_expiry_peers(zero, [zero, ComparableExpiry(1, 10)])
    assert result.ratio is None and result.quality == "NOT_APPLICABLE"


@pytest.mark.parametrize(
    ("same", "persistent", "score", "bonus", "source", "breadth"),
    [(90, None, 90, 0, "SAME_DAY", 1),
     (None, 87, 87, 0, "PERSISTENT", 1),
     (None, None, None, 0, "NONE", 0),
     (90, 20, 90, 0, "SAME_DAY", 1),
     (72, 55, 75, 3, "BOTH", 2),
     (75, 65, 81, 6, "BOTH", 2),
     (88, 84, 98, 10, "BOTH", 2),
     (98, 90, 100, 10, "BOTH", 2)],
)
def test_discovery_confirmation_rules(
    same: float | None, persistent: float | None, score: float | None,
    bonus: float, source: str, breadth: int,
) -> None:
    result = discovery_with_confirmation(same, persistent)
    assert result.score == score
    assert result.confirmation_bonus == bonus
    assert result.source == source and result.evidence_breadth == breadth


def test_confirmation_bonus_cannot_create_eligibility_and_cold_start_has_no_score() -> None:
    combined = discovery_with_confirmation(39, 39)
    assert combined.score == 39
    assert discovery_eligible(39, 39, False) is False
    cold = discovery_with_confirmation(None, None)
    assert discovery_eligible(None, None, True) is True
    assert cold.score is None and cold.source == "NONE"


@dataclass
class Expiry:
    ticker: str
    bucket_at_detection: str
    same_day_activity_score: float | None
    persistent_positioning_score: float | None
    discovery_score: float | None
    structural_cold_start_eligible: bool = False


def test_ticker_selection_ignores_unscored_high_volume_zero_dte() -> None:
    cold_zero = Expiry("NVDA", "VERY_SHORT", None, None, None)
    scored_nonzero = Expiry("NVDA", "VERY_SHORT", 60, None, 60)
    assert select_dual_discovery([cold_zero, scored_nonzero]) == [scored_nonzero]

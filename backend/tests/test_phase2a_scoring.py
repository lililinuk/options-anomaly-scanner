from datetime import date

import pytest

from app.models.signals import DteBucket, bucket_for_dte
from app.scanner.scoring import (
    ContractInput,
    expiry_type,
    neighbor_ratio,
    piecewise,
    preliminary_expiry_score,
    robust_z_score,
    safe_ratio,
    score_contract,
    skew,
)


@pytest.mark.parametrize(
    ("dte", "bucket"),
    [
        (0, DteBucket.VERY_SHORT),
        (7, DteBucket.VERY_SHORT),
        (8, DteBucket.SHORT),
        (30, DteBucket.SHORT),
        (31, DteBucket.MEDIUM),
        (90, DteBucket.MEDIUM),
        (91, DteBucket.LONG),
        (180, DteBucket.LONG),
        (181, None),
    ],
)
def test_phase2a_dte_boundaries(dte: int, bucket: DteBucket | None) -> None:
    assert bucket_for_dte(dte) == bucket


def test_piecewise_interpolates_and_caps() -> None:
    assert piecewise(0.25, ((0.2, 10), (0.3, 20))) == pytest.approx(15)
    assert piecewise(99, ((0.2, 10), (0.3, 20))) == 20


def test_zero_denominators_are_unavailable() -> None:
    assert safe_ratio(3, 0) is None
    assert skew(0, 0) is None


def test_volume_oi_uses_one_as_low_denominator_and_caps() -> None:
    score = score_contract(ContractInput(100_000, 0, 5_000_000, 0.05, 0.5))
    assert score.components["relative_activity"] == 20
    assert "LOW_OI_BASE" in score.flags


def test_missing_history_rescales_instead_of_scoring_zero() -> None:
    score = score_contract(ContractInput(10_000, 100, 5_000_000, 0.05, 0.5))
    assert "HISTORY_INSUFFICIENT" in score.flags
    assert score.basis == 65
    assert score.score == 100
    assert score.candidate


def test_candidate_requires_basis_at_least_sixty() -> None:
    score = score_contract(ContractInput(10_000, 100, 5_000_000, None, None, quote_supplied=False))
    assert score.score >= 65
    assert score.basis < 60
    assert not score.candidate


def test_spread_over_fifty_percent_is_hard_reject() -> None:
    assert (
        score_contract(ContractInput(1000, 100, 100_000, 0.5001, 0.5)).hard_reject
        == "SPREAD_OVER_50_PERCENT"
    )


def test_lotto_risk_is_flag_not_rejection() -> None:
    score = score_contract(ContractInput(1000, 50, 100_000, 0.10, 0.09))
    assert "LOTTO_RISK" in score.flags
    assert score.hard_reject is None


def test_neighbor_median_and_expiry_type_evidence() -> None:
    assert neighbor_ratio(300, [100, 200]) == (2.0, "NEIGHBOR")
    assert neighbor_ratio(300, []) == (None, "INSUFFICIENT")
    assert expiry_type(date(2026, 8, 21)) == ("STANDARD_MONTHLY", "INFERRED")
    assert expiry_type(date(2026, 8, 21), "weekly") == ("WEEKLY", "VENDOR")


def test_preliminary_score_rescales_missing_neighbor() -> None:
    score, basis, missing, _ = preliminary_expiry_score(0.5, None, 0.7)
    assert score == 100
    assert basis == 70
    assert missing == ["neighbor_oi_anomaly"]


def test_robust_z_requires_ten_observations_and_uses_mad() -> None:
    assert robust_z_score(20, range(9)) is None
    assert robust_z_score(20, range(10)) is not None

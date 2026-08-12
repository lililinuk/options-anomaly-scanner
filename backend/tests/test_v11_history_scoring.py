from dataclasses import dataclass
from datetime import date, timedelta

import pytest

from app.scanner.history import OiHistoryPoint, contract_persistence, expiry_persistence
from app.scanner.scoring import contract_structure_score, same_day_activity_score
from app.scanner.selection import select_dual_discovery
from app.scanner.v11 import group_contract_histories


def _points(values: list[int], shares: list[float] | None = None) -> list[OiHistoryPoint]:
    start = date(2026, 8, 1)
    return [
        OiHistoryPoint(start + timedelta(days=index), value, shares[index] if shares else None)
        for index, value in enumerate(values)
    ]


def test_first_contract_observation_does_not_assume_zero() -> None:
    result = contract_persistence(_points([100]), current_same_side_expiry_oi=1000)
    assert result.score is None
    assert result.features["delta_oi_1"] is None
    assert result.features["first_observation"] is True


def test_two_contract_observations_produce_own_delta_without_false_close() -> None:
    result = contract_persistence(_points([100, 140]), current_same_side_expiry_oi=1000)
    assert result.features["delta_oi_1"] == 40
    assert result.score is None
    absent_next_day = contract_persistence(_points([100, 140]), current_same_side_expiry_oi=1000)
    assert "closed" not in absent_next_day.features


def test_expiry_share_change_is_percentage_point_difference() -> None:
    result = expiry_persistence(_points([100, 120, 140], [0.08, 0.15, 0.24]))
    window = result.features["windows"]["3"]
    assert window["oi_share_change"] == pytest.approx(0.16)
    assert result.state == "PERSISTENT_BUILD"
    assert result.history_confidence == "LOW"


def test_3_5_10_windows_and_max_winner_are_independent() -> None:
    result = expiry_persistence(_points(
        [100, 105, 110, 120, 130, 145, 160, 180, 210, 250],
        [0.05, 0.052, 0.055, 0.06, 0.07, 0.08, 0.10, 0.13, 0.17, 0.25],
    ))
    assert set(result.features["windows"]) == {"3", "5", "10"}
    scores = {int(key): value["score"] for key, value in result.features["windows"].items()}
    assert result.score == max(scores.values())
    assert result.winning_window == max(scores, key=scores.get)  # type: ignore[arg-type]
    assert result.history_confidence == "FULL"


def test_decline_and_directional_persistence() -> None:
    result = expiry_persistence(_points([200, 180, 160, 140, 120], [0.2, 0.18, 0.16, 0.14, 0.12]))
    assert result.state == "PERSISTENT_DECLINE"
    assert result.features["windows"]["5"]["decline_persistence"] == 1


def test_same_day_fixed_scale_does_not_rescale_missing_component() -> None:
    score = same_day_activity_score(0.50, None)
    assert score.score == 60
    assert score.basis == 60
    assert score.missing == ("comparable_expiry_volume_neighbor_ratio",)


def test_structure_score_has_no_volume_premium_history_or_intraday_dependency() -> None:
    score = contract_structure_score(
        oi_share=0.20, neighbor_ratio=5, spread_pct=0.05, delta=0.5,
        quote_supplied=True,
    )
    assert score.score == 100 and score.classification == "EXTREME_STRUCTURE"
    assert set(score.components) == {
        "same_side_expiry_oi_concentration", "neighbor_strike_oi_anomaly",
        "liquidity_quality", "moneyness_delta_quality",
    }
    assert contract_structure_score(
        oi_share=0.20, neighbor_ratio=5, spread_pct=0.51, delta=0.05,
        quote_supplied=True,
    ).hard_reject == "SPREAD_OVER_50_PERCENT"


@dataclass
class Expiry:
    ticker: str
    bucket_at_detection: str
    same_day_activity_score: float
    persistent_positioning_score: float | None
    discovery_score: float
    structural_cold_start_eligible: bool = False


def test_dual_discovery_same_day_persistent_both_and_caps() -> None:
    rows = []
    for index, ticker in enumerate(("A", "B", "C", "D", "E")):
        rows.extend([
            Expiry(
                ticker, "VERY_SHORT", 40 if index != 1 else 10,
                70 if index != 0 else None, 90 - index,
            ),
            Expiry(ticker, "SHORT", 45, 70, 80-index),
            Expiry(ticker, "MEDIUM", 10, None, 30, structural_cold_start_eligible=True),
            Expiry(ticker, "LONG", 100, 100, 100),
        ])
    selected = select_dual_discovery(rows)
    assert len({row.ticker for row in selected}) == 4
    assert all(row.bucket_at_detection != "LONG" for row in selected)
    assert all(
        sum(row.ticker == ticker and row.bucket_at_detection == bucket for row in selected) <= 1
        for ticker in "ABCDE"
        for bucket in ("VERY_SHORT", "SHORT", "MEDIUM")
    )


def test_contract_histories_are_grouped_for_batched_runtime_lookup() -> None:
    rows = [
        type("Row", (), {"contract_symbol": symbol})()
        for symbol in ("A", "B", "A", "C", "B")
    ]
    grouped = group_contract_histories(rows)  # type: ignore[arg-type]
    assert {key: len(value) for key, value in grouped.items()} == {"A": 2, "B": 2, "C": 1}

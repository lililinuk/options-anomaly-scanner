from dataclasses import dataclass
from decimal import Decimal

from app.scanner.clusters import ClusterContract, build_clusters
from app.scanner.scoring import premium_weighted_strike
from app.scanner.selection import select_deep_expiries


@dataclass
class Expiry:
    ticker: str
    bucket_at_detection: str
    preliminary_score: float
    marker: str


def test_selection_caps_four_tickers_and_one_expiry_per_bucket() -> None:
    rows = [
        Expiry(ticker, bucket, score, f"{ticker}-{bucket}-{score}")
        for ticker, score in zip("ABCDEFG", range(100, 93, -1), strict=True)
        for bucket in ("VERY_SHORT", "VERY_SHORT", "SHORT", "MEDIUM", "LONG")
    ]
    selected = select_deep_expiries(rows)
    assert len({row.ticker for row in selected}) == 4
    assert len(selected) == 12
    assert all(
        sum(row.ticker == ticker and row.bucket_at_detection == bucket for row in selected) <= 1
        for ticker in "ABCDEFG"
        for bucket in ("VERY_SHORT", "SHORT", "MEDIUM")
    )
    assert not any(row.bucket_at_detection == "LONG" for row in selected)


def _contract(
    identifier: str, strike: int, premium: float = 100_000, spot: int = 100
) -> ClusterContract:
    return ClusterContract(
        identifier, Decimal(str(strike)), 1000, 100, premium, 80, 15, Decimal(str(spot))
    )


def test_cluster_allows_one_gap_and_rejects_span_over_twenty_percent() -> None:
    ladder = [Decimal(value) for value in (90, 95, 100, 105, 110, 125)]
    clusters = build_clusters(
        candidates=[_contract("a", 90), _contract("b", 100)],
        full_strike_ladder=ladder,
        side_volume=3000,
        side_premium=300_000,
    )
    assert len(clusters) == 1
    assert clusters[0].components["strike_coherence"] == 5
    split = build_clusters(
        candidates=[_contract("a", 90), _contract("c", 125)],
        full_strike_ladder=ladder,
        side_volume=3000,
        side_premium=300_000,
    )
    assert split == []


def test_call_and_put_inputs_are_never_merged_and_center_is_premium_weighted() -> None:
    ladder = [Decimal(95), Decimal(100)]
    calls = build_clusters(
        candidates=[_contract("c1", 95, 100), _contract("c2", 100, 300)],
        full_strike_ladder=ladder,
        side_volume=2000,
        side_premium=400,
    )
    puts = build_clusters(
        candidates=[_contract("p1", 95), _contract("p2", 100)],
        full_strike_ladder=ladder,
        side_volume=2000,
        side_premium=200_000,
    )
    assert len(calls) == len(puts) == 1
    assert premium_weighted_strike([(Decimal(95), 100), (Decimal(100), 300)]) == Decimal("98.75")
    assert calls[0].score >= 65

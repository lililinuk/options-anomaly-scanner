from decimal import Decimal

from app.scanner.clusters import PositioningClusterContract, build_positioning_clusters


def _row(identifier: str, strike: int, oi: int = 100) -> PositioningClusterContract:
    return PositioningClusterContract(
        id=identifier, strike=Decimal(strike), open_interest=oi,
        structure_score=80, liquidity_points=15, spot=Decimal(100),
        persistent_score=70, persistent_state="PERSISTENT_BUILD",
        net_oi_changes={"3": 10},
    )


def test_cluster_is_oi_based_and_has_no_volume_or_premium_input() -> None:
    result = build_positioning_clusters(
        candidates=[_row("a", 95, 300), _row("b", 100, 200)],
        full_strike_ladder=[Decimal(95), Decimal(100)], same_side_expiry_oi=600,
    )[0]
    assert result.oi_share == 500 / 600
    assert set(result.components) == {
        "constituent_structural_strength", "same_side_expiry_oi_concentration",
        "strike_coherence", "liquidity",
    }
    assert result.persistent_build_count == 2


def test_call_and_put_cluster_inputs_are_run_separately() -> None:
    calls = build_positioning_clusters(
        candidates=[_row("c1", 95), _row("c2", 100)],
        full_strike_ladder=[Decimal(95), Decimal(100)], same_side_expiry_oi=500,
    )
    puts = build_positioning_clusters(
        candidates=[_row("p1", 95), _row("p2", 100)],
        full_strike_ladder=[Decimal(95), Decimal(100)], same_side_expiry_oi=500,
    )
    assert len(calls) == len(puts) == 1
    assert {row.id for row in calls[0].contracts}.isdisjoint({row.id for row in puts[0].contracts})

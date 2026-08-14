from types import SimpleNamespace

import pytest

from app.confirmation.state_v2 import (
    PHASE2B_V2_SPEC_VERSION,
    build_dealer_state,
    build_positioning_state,
    build_research_readiness,
    build_volatility_state,
    classify_gex_sign,
    classify_term_topology,
    latest_v2_state,
)
from app.db.models import Phase2bCandidateState


@pytest.mark.parametrize(
    ("shorter", "candidate", "longer", "expected"),
    [
        (0.30, 0.40, 0.35, "LOCAL_PEAK"),
        (0.40, 0.30, 0.35, "LOCAL_TROUGH"),
        (0.30, 0.35, 0.40, "RISING_THROUGH_CANDIDATE"),
        (0.40, 0.35, 0.30, "FALLING_THROUGH_CANDIDATE"),
        (0.30, 0.30, 0.40, "FLAT_OR_EQUAL"),
        (0.30, 0.30 + 1e-13, 0.40, "FLAT_OR_EQUAL"),
        (None, 0.35, 0.40, "INCOMPLETE"),
        (0.30, 0.35, None, "INCOMPLETE"),
    ],
)
def test_term_topology_is_exact_threshold_free_and_handles_missing_neighbors(
    shorter: float | None,
    candidate: float,
    longer: float | None,
    expected: str,
) -> None:
    assert classify_term_topology(shorter, candidate, longer) == expected


def test_term_state_preserves_raw_nodes_differences_and_implied_move() -> None:
    result = build_volatility_state(
        {"value": 32.4659, "vendor_date": "2026-08-13"},
        {
            "availability": "AVAILABLE",
            "exact_match_status": "EXACT_MATCH",
            "candidate_node": {
                "expiry": "2026-08-21",
                "implied_move_usd": 7.8,
                "implied_move_pct": 0.035,
            },
            "nearest_shorter_node": {
                "expiry": "2026-08-14",
                "implied_vol_pct": 0.31939136,
            },
            "nearest_longer_node": {
                "expiry": "2026-08-28",
                "implied_vol_pct": 0.31160612,
            },
            "candidate_term_iv": 0.33103896,
            "candidate_iv_minus_shorter": 0.01164760,
            "candidate_iv_minus_longer": 0.01943284,
            "vendor_date": "2026-08-13",
        },
    )
    assert result["topology"] == "LOCAL_PEAK"
    assert result["iv_rank"] == 32.4659
    assert result["candidate_iv_minus_neighbor_mean"] == pytest.approx(0.01554022)
    assert result["implied_move_usd"] == 7.8


@pytest.mark.parametrize(
    ("status", "value", "expected"),
    [
        ("EXACT_MATCH", 1, "POSITIVE_NET_GEX"),
        ("EXACT_MATCH", -1, "NEGATIVE_NET_GEX"),
        ("EXACT_MATCH", 0, "ZERO_NET_GEX"),
        ("NOT_PRESENT", 1, "UNKNOWN"),
        ("UNAVAILABLE", None, "UNKNOWN"),
        ("EXACT_MATCH", None, "UNKNOWN"),
    ],
)
def test_gex_sign_uses_only_exact_candidate_cell(
    status: str, value: float | None, expected: str
) -> None:
    assert classify_gex_sign(
        {"candidate_heatmap_cell_status": status, "candidate_net_gex_usd": value}
    ) == expected


def test_degraded_exact_gex_is_factual_but_quality_remains_separate() -> None:
    result = build_dealer_state(
        {
            "quality": "AVAILABLE_DEGRADED",
            "candidate_heatmap_cell_status": "EXACT_MATCH",
            "candidate_net_gex_usd": 59652544,
        }
    )
    assert result["sign"] == "POSITIVE_NET_GEX"
    assert result["source_quality"] == "AVAILABLE_DEGRADED"


def test_legacy_exact_cell_shape_remains_compatible_without_flattened_values() -> None:
    result = build_dealer_state(
        {
            "quality": "AVAILABLE_DEGRADED",
            "candidate_heatmap_cell_status": "EXACT_MATCH",
            "candidate_cell": {
                "net_dealer_gex_usd": 59652544,
                "call_gex_usd": 59166863,
                "put_gex_usd": 485681,
            },
        }
    )
    assert result["sign"] == "POSITIVE_NET_GEX"
    assert result["candidate_net_gex_usd"] == 59652544


def test_positioning_counts_each_evidence_family_once() -> None:
    state = build_positioning_state(
        {
            "radar_material_event": True,
            "premium_usd": 3_100_000,
            "oi_diff": 4_900,
            "volume": 5_000,
            "trades": 300,
            "structure_score": 70.722,
            "contract_persistence": None,
            "expiry_persistence": None,
        },
        trigger_sources=["RADAR_EVENT"],
        contract_history_confidence="INSUFFICIENT",
        contract_history_count=1,
        expiry_history_confidence="INSUFFICIENT",
        expiry_history_count=1,
    )
    assert state["evidence_family_count"] == 2
    assert state["evidence_breadth"] == "MULTI_EVIDENCE"
    assert state["presence_states"] == {
        "radar_event": "RADAR_EVENT_PRESENT",
        "contract_persistence": "CONTRACT_PERSISTENCE_NOT_YET_AVAILABLE",
        "expiry_persistence": "EXPIRY_PERSISTENCE_NOT_YET_AVAILABLE",
        "structure": "STRUCTURE_PRESENT",
        "cluster": "CLUSTER_ABSENT",
    }


def test_positioning_exact_cluster_membership_and_persistence_are_distinct_families() -> None:
    state = build_positioning_state(
        {"contract_persistence": 72, "expiry_persistence": 80},
        trigger_sources=[],
        exact_cluster_membership=[{"cluster_id": "safe-id"}],
    )
    assert state["evidence_family_count"] == 3
    assert state["presence_states"]["radar_event"] == "RADAR_EVENT_ABSENT"
    assert state["presence_states"]["cluster"] == "CLUSTER_PRESENT"


def _ready_layers() -> tuple[dict, dict, dict, dict, dict]:
    positioning = {"evidence_family_count": 1}
    price = {"availability": "AVAILABLE_WITH_GAPS"}
    volatility = {
        "iv_rank": 32,
        "iv_rank_vendor_date": "2026-08-13",
        "exact_match_status": "EXACT_MATCH",
        "candidate_iv": 0.33,
        "topology": "INCOMPLETE",
    }
    dealer = {
        "candidate_cell_status": "EXACT_MATCH",
        "sign": "POSITIVE_NET_GEX",
        "source_quality": "AVAILABLE",
    }
    execution = {"availability": "AVAILABLE", "bid": 1, "ask": 1.1, "delta": 0.4}
    return positioning, price, volatility, dealer, execution


def test_readiness_exact_term_node_is_ready_even_when_topology_incomplete() -> None:
    result = build_research_readiness(*_ready_layers())
    assert result["state"] == "CONTEXT_COMPLETE"
    assert result["layers"]["candidate_term"]["status"] == "READY"


def test_readiness_one_degraded_layer_is_partial_and_two_missing_is_limited() -> None:
    inputs = list(_ready_layers())
    inputs[3] = {**inputs[3], "source_quality": "AVAILABLE_DEGRADED"}
    partial = build_research_readiness(*inputs)
    assert partial["state"] == "CONTEXT_PARTIAL"
    assert partial["layers"]["dealer_gex"]["status"] == "DEGRADED"

    inputs[2] = {**inputs[2], "iv_rank": None}
    limited = build_research_readiness(*inputs)
    assert limited["state"] == "CONTEXT_LIMITED"
    assert limited["missing_or_degraded_count"] == 2


def test_unavailable_dealer_is_unknown_and_not_zero() -> None:
    result = build_dealer_state(
        {
            "quality": "UNAVAILABLE",
            "candidate_heatmap_cell_status": "UNAVAILABLE",
            "candidate_net_gex_usd": None,
        }
    )
    assert result["sign"] == "UNKNOWN"
    assert result["candidate_net_gex_usd"] is None


def test_v2_spec_is_new_and_directional_scoring_terms_are_absent() -> None:
    assert PHASE2B_V2_SPEC_VERSION == "signal_spec_v2.0_phase2b"
    serialized = str(build_positioning_state({}, trigger_sources=[])).lower()
    for forbidden in ("tradeability", "conviction", "bullish", "bearish"):
        assert forbidden not in serialized


def test_candidate_state_has_idempotent_source_evaluation_spec_uniqueness() -> None:
    unique_columns = {
        tuple(column.name for column in constraint.columns)
        for constraint in Phase2bCandidateState.__table__.constraints
        if constraint.__class__.__name__ == "UniqueConstraint"
    }
    assert ("candidate_evaluation_id", "specification_version") in unique_columns


def test_latest_v2_api_shape_preserves_six_dimensions_and_versions() -> None:
    row = SimpleNamespace(
        positioning_state={"evidence_breadth": "SINGLE_EVIDENCE"},
        price_state={"trend": "UPTREND"},
        volatility_state={"topology": "LOCAL_PEAK"},
        dealer_gex_state={"sign": "POSITIVE_NET_GEX"},
        execution_state={"availability": "AVAILABLE"},
        research_readiness={"state": "CONTEXT_PARTIAL"},
        phase2a_provenance={"candidate_evaluation_id": "safe-id"},
        direction="UNRESOLVED",
        specification_version=PHASE2B_V2_SPEC_VERSION,
        source_context_specification_version="signal_spec_v1.2_phase2b",
        config_version="v2-test",
        config_hash="safe-hash",
        topology_rule_version="topology-v1",
        readiness_rule_version="readiness-v1",
        evaluated_at=SimpleNamespace(isoformat=lambda: "2026-08-14T00:00:00+00:00"),
    )
    session = SimpleNamespace(scalar=lambda _statement: row)
    result = latest_v2_state(session, "SAFE")  # type: ignore[arg-type]
    assert result is not None
    assert result["direction"] == "UNRESOLVED"
    assert result["positioning"]["evidence_breadth"] == "SINGLE_EVIDENCE"
    assert result["research_readiness"]["state"] == "CONTEXT_PARTIAL"

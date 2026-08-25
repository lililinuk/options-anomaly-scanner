from datetime import date
from types import SimpleNamespace
from uuid import uuid4

import pytest

from app.confirmation.workspace_v3 import (
    ADJACENT_EXPIRY_RULE_VERSION,
    BELOW_FLOOR_PATH_RULE_VERSION,
    PHASE2B_V3_SPEC_VERSION,
    PRIMARY_FLOOR_RULE_VERSION,
    PRIMARY_UPPER_NODE_RULE_VERSION,
    build_dealer_gex_structure,
    build_workspace_payload,
    latest_v3_workspace,
)
from app.db.models import Phase2bV3ResearchWorkspace


def _cell(expiration: str, strike: float, net: float) -> dict:
    return {
        "expiration": expiration,
        "strike_usd": strike,
        "net_dealer_gex_usd": net,
        "call_gex_usd": net,
        "put_gex_usd": 0,
    }


def _heatmap(
    anchor_cells: list[tuple[float, float]],
    *,
    previous: tuple[float, float] | None = None,
    next_node: tuple[float, float] | None = None,
    quality: str = "AVAILABLE",
) -> dict:
    cells = [_cell("2026-08-21", strike, net) for strike, net in anchor_cells]
    if previous is not None:
        cells.append(_cell("2026-08-19", *previous))
    if next_node is not None:
        cells.append(_cell("2026-08-24", *next_node))
    return {
        "availability": quality,
        "spot_usd": 225,
        "generated_at": "2026-08-14T00:00:00Z",
        "cells": cells,
    }


def test_dealer_structure_does_not_label_local_capture_as_vendor_time() -> None:
    heatmap = {
        **_heatmap([(220, 100), (230, 20)]),
        "generated_at": None,
        "capture_timestamp": "2026-08-14T00:05:00Z",
    }

    result = build_dealer_gex_structure(
        heatmap,
        anchor_expiration=date(2026, 8, 21),
        spot=225,
    )

    assert result["source_timestamp"] is None


def test_primary_floor_selects_largest_positive_below_spot_only() -> None:
    result = build_dealer_gex_structure(
        _heatmap([(210, 20), (217.5, -500), (220, 100), (230, 1_000)]),
        anchor_expiration="2026-08-21",
    )
    assert result["primary_floor"]["strike_usd"] == 220
    assert result["primary_floor"]["net_dealer_gex_usd"] == 100
    assert result["primary_upper_positive_gex_node"]["strike_usd"] == 230


def test_no_positive_floor_or_upper_is_never_fabricated() -> None:
    result = build_dealer_gex_structure(
        _heatmap([(210, -20), (220, 0), (230, -10)]),
        anchor_expiration="2026-08-21",
    )
    assert result["primary_floor"] is None
    assert result["floor_state"] == "NO_POSITIVE_FLOOR_IDENTIFIED"
    assert result["primary_upper_positive_gex_node"] is None


def test_immediate_lower_node_and_conditional_break_risk() -> None:
    result = build_dealer_gex_structure(
        _heatmap([(210, 10), (215, 30), (217.5, -5), (220, 100), (230, 20)]),
        anchor_expiration="2026-08-21",
    )
    assert result["immediate_below_floor_node"]["strike_usd"] == 217.5
    assert result["below_floor_structure"] == "NEGATIVE_GEX_IMMEDIATELY_BELOW"
    assert result["floor_break_condition"] == "DOWNSIDE_ACCELERATION_RISK"
    assert result["floor_hold_condition"] == "STABILIZATION_BIAS"
    assert [node["strike_usd"] for node in result["nearby_lower_nodes"]][:3] == [
        217.5, 215, 210
    ]


def test_positive_immediate_lower_node_does_not_trigger_break_risk() -> None:
    result = build_dealer_gex_structure(
        _heatmap([(217.5, 5), (220, 100)]), anchor_expiration="2026-08-21"
    )
    assert result["floor_break_condition"] == "NOT_IDENTIFIED"
    assert result["below_floor_structure"] == "NOT_IDENTIFIED"


def test_missing_immediate_lower_node_is_handled() -> None:
    result = build_dealer_gex_structure(
        _heatmap([(220, 100)]), anchor_expiration="2026-08-21"
    )
    assert result["immediate_below_floor_node"] is None
    assert result["floor_break_condition"] == "NOT_IDENTIFIED"


@pytest.mark.parametrize(
    ("previous", "next_node", "expected"),
    [
        ((220, 1), (220, 2), "ALIGNED"),
        ((220, 1), None, "PARTIALLY_ALIGNED"),
        ((220, 1), (220, -2), "MIXED"),
        ((220, -1), (220, -2), "NOT_ALIGNED"),
        ((220, 0), (220, -2), "NOT_ALIGNED"),
        (None, None, "UNAVAILABLE"),
    ],
)
def test_adjacent_expiry_context_is_lightweight_and_zero_is_real(
    previous: tuple[float, float] | None,
    next_node: tuple[float, float] | None,
    expected: str,
) -> None:
    result = build_dealer_gex_structure(
        _heatmap([(217.5, -5), (220, 100)], previous=previous, next_node=next_node),
        anchor_expiration="2026-08-21",
    )
    assert result["adjacent_expiry_context"]["state"] == expected
    assert result["primary_floor"]["strike_usd"] == 220


@pytest.mark.parametrize(
    ("quality", "available"),
    [
        ("AVAILABLE", True),
        ("AVAILABLE_DEGRADED", True),
        ("INCOMPLETE_OR_TRUNCATED", False),
        ("UNAVAILABLE", False),
    ],
)
def test_dealer_source_quality_controls_structure_without_fake_zero(
    quality: str, available: bool
) -> None:
    result = build_dealer_gex_structure(
        _heatmap([(220, 100)], quality=quality), anchor_expiration="2026-08-21"
    )
    assert result["source_quality"] == quality
    assert (result["availability"] == "AVAILABLE") is available
    if not available:
        assert result["primary_floor"] is None
        assert result["spot_usd"] is None
        assert result["adjacent_expiry_context"]["state"] == "UNAVAILABLE"


def test_workspace_role_separation_preserves_contract_and_timestamp_semantics() -> None:
    evaluation = SimpleNamespace(
        id=uuid4(), ticker="NVDA", contract_symbol="NVDA260821C00220000",
        expiration=date(2026, 8, 21), right="C", strike=220,
        dte_at_detection=9, direction="UNRESOLVED",
        phase2a_evidence={
            "premium_usd": 10_430_000, "volume": 24_458, "trades": 2_887,
            "oi_diff": 4_531, "relative_oi_change": 0.0777,
            "radar_observation_date": "2026-08-13",
        },
        source_timestamps={"chain": "2026-08-12", "chain_quote": "2026-08-13T20:00:00Z"},
        specification_version="signal_spec_v1.2_phase2b",
    )
    context = SimpleNamespace(
        id=uuid4(),
        dealer_heatmap=_heatmap([(217.5, -5), (220, 100), (230, 20)]),
        stock_state={"current_price_usd": 225},
        raw_payload_ids=["raw-safe"], source_request_ids=["request-safe"],
        source_timestamps={"heatmap": "2026-08-14T00:00:00Z"},
    )
    state = SimpleNamespace(
        id=uuid4(), specification_version="signal_spec_v2.0_phase2b",
        positioning_state={"evidence_breadth": "MULTI_EVIDENCE"},
        price_state={"trend": "UPTREND", "latest_regular_close_usd": 225,
                     "sma_20": 210, "sma_50": 200},
        volatility_state={"topology": "LOCAL_PEAK"},
        execution_state={"open_interest": 62_832, "bid": 3.85, "ask": 3.95},
    )
    contract = SimpleNamespace(id=uuid4(), bucket_at_detection="VERY_SHORT")
    result = build_workspace_payload(evaluation, context, state, contract=contract)
    assert result["specification_version"] == PHASE2B_V3_SPEC_VERSION
    assert result["contract_identity"]["expiration"] == "2026-08-21"
    assert result["contract_identity"]["dte_at_detection"] == 9
    assert result["contract_identity"]["bucket_at_detection"] == "VERY_SHORT"
    activity = result["opportunity_positioning"]["contract_activity"]
    oi = result["opportunity_positioning"]["open_interest"]
    assert activity["premium_activity_usd"] == 10_430_000
    assert activity["volume"] == 24_458 and activity["trades"] == 2_887
    assert oi["delta_oi"] == 4_531 and oi["current_oi"] == 62_832
    assert oi["radar_observation_date"] != oi["chain_observation_date"]
    flow = result["opportunity_positioning"]["observed_flow_direction"]
    assert flow["state"] == "UNRESOLVED"
    assert flow["interpretation"] == "PROVENANCE_WARNING_NOT_NEUTRAL"
    assert "direction" not in result["trade_structure"]["volatility"]


def test_workspace_model_is_append_only_per_source_v2_state_and_spec() -> None:
    unique_columns = {
        tuple(column.name for column in constraint.columns)
        for constraint in Phase2bV3ResearchWorkspace.__table__.constraints
        if constraint.__class__.__name__ == "UniqueConstraint"
    }
    assert ("source_v2_state_id", "specification_version") in unique_columns


def test_latest_v3_api_shape_is_additive_and_versioned() -> None:
    row = SimpleNamespace(
        specification_version=PHASE2B_V3_SPEC_VERSION,
        contract_identity={"contract_symbol": "SAFE"},
        opportunity_positioning={"observed_flow_direction": {"state": "UNRESOLVED"}},
        underlying_price={"trend": "MIXED"},
        volatility_context={"topology": "LOCAL_PEAK"},
        dealer_gex_structure={"primary_floor": None},
        execution_context={"availability": "AVAILABLE"},
        provenance={"source_v2_state_id": "safe"},
        primary_floor_rule_version=PRIMARY_FLOOR_RULE_VERSION,
        primary_upper_node_rule_version=PRIMARY_UPPER_NODE_RULE_VERSION,
        below_floor_path_rule_version=BELOW_FLOOR_PATH_RULE_VERSION,
        adjacent_expiry_rule_version=ADJACENT_EXPIRY_RULE_VERSION,
        config_version="v3-test", config_hash="safe-hash",
        created_at=SimpleNamespace(isoformat=lambda: "2026-08-14T00:00:00+00:00"),
    )
    session = SimpleNamespace(scalar=lambda _statement: row)
    result = latest_v3_workspace(session, "SAFE")  # type: ignore[arg-type]
    assert result is not None
    assert result["specification_version"] == PHASE2B_V3_SPEC_VERSION
    assert result["trade_structure"]["dealer_gex"]["primary_floor"] is None
    assert result["rule_versions"]["primary_floor"] == PRIMARY_FLOOR_RULE_VERSION


def test_v3_contains_no_trade_recommendation_or_new_score() -> None:
    serialized = str(
        build_dealer_gex_structure(
            _heatmap([(217.5, -5), (220, 100)]), anchor_expiration="2026-08-21"
        )
    ).lower()
    for forbidden in ("buy", "sell", "long call", "short put", "gex score"):
        assert forbidden not in serialized

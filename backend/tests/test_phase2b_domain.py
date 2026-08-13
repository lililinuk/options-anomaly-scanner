from datetime import date
from decimal import Decimal

import pytest

from app.confirmation.domain import (
    calculate_price_context,
    canonical_regular_daily,
    evaluate_heatmap,
    map_term_structure,
    normalize_stock_state,
    strike_location,
)


def bars(count: int, *, descending: bool = False) -> list[dict[str, object]]:
    result: list[dict[str, object]] = []
    for index in range(count):
        close = float(200 - index if descending else 100 + index)
        result.append(
            {
                "trading_date": f"2026-06-{index + 1:02d}",
                "session": "regular",
                "open_usd": close - 0.5,
                "high_usd": close + 1,
                "low_usd": close - 1,
                "close_usd": close,
            }
        )
    return result


def test_regular_session_grouping_ignores_other_sessions() -> None:
    rows = [
        {"trading_date": "2026-08-12", "session": "premarket", "close_usd": 99},
        {"trading_date": "2026-08-12", "session": "regular", "close_usd": 100},
        {"trading_date": "2026-08-12", "session": "postmarket", "close_usd": 101},
    ]
    selected, policy = canonical_regular_daily(rows)
    assert policy == "REGULAR_SESSION_ONLY"
    assert [row["close_usd"] for row in selected] == [100]


@pytest.mark.parametrize(
    "rows",
    [
        [
            {"trading_date": "2026-08-12", "session": "regular"},
            {"trading_date": "2026-08-12", "session": "regular"},
        ],
        [{"trading_date": "2026-08-12", "session": "postmarket"}],
    ],
)
def test_duplicate_or_missing_regular_session_is_unresolved(rows) -> None:  # type: ignore[no-untyped-def]
    selected, policy = canonical_regular_daily(rows)
    assert selected == []
    assert policy == "DAILY_SESSION_POLICY_UNRESOLVED"


def test_price_features_are_deterministic_and_preserve_adjustment_caveat() -> None:
    result = calculate_price_context({"data": {"as_of": "2026-08-12T04:00:00Z", "bars": bars(60)}})
    assert result["availability"] == "AVAILABLE"
    assert result["return_1d"] == pytest.approx(159 / 158 - 1)
    assert result["return_5d"] == pytest.approx(159 / 154 - 1)
    assert result["return_20d"] == pytest.approx(159 / 139 - 1)
    assert result["sma_20"] == pytest.approx(sum(range(140, 160)) / 20)
    assert result["sma_50"] == pytest.approx(sum(range(110, 160)) / 50)
    assert result["rolling_high_20"] == 160
    assert result["rolling_low_20"] == 139
    assert result["atr_14"] == 2
    assert result["distance_to_sma20_pct"] == pytest.approx(159 / result["sma_20"] - 1)
    assert result["trend"] == "UPTREND"
    assert result["price_adjustment_semantics"] == "UNCONFIRMED"


def test_insufficient_histories_keep_missing_values_null() -> None:
    nineteen = calculate_price_context({"data": {"bars": bars(19)}})
    forty_nine = calculate_price_context({"data": {"bars": bars(49)}})
    assert nineteen["sma_20"] is None
    assert nineteen["return_20d"] is None
    assert forty_nine["sma_20"] is not None
    assert forty_nine["sma_50"] is None
    assert forty_nine["trend"] == "UNKNOWN"
    assert forty_nine["availability"] == "INSUFFICIENT_HISTORY"


def test_price_trend_states() -> None:
    assert calculate_price_context({"data": {"bars": bars(60)}})["trend"] == "UPTREND"
    downtrend = calculate_price_context({"data": {"bars": bars(60, descending=True)}})
    assert downtrend["trend"] == "DOWNTREND"
    mixed = bars(60)
    mixed[-1]["close_usd"] = 130.0
    assert calculate_price_context({"data": {"bars": mixed}})["trend"] == "MIXED"
    assert calculate_price_context({"data": {"bars": []}})["trend"] == "UNKNOWN"


def test_stock_state_and_strike_distance_do_not_replace_missing_with_zero() -> None:
    state = normalize_stock_state(
        {"data": {"close_usd": 200, "prev_close_usd": 198, "session": "premarket"}}
    )
    assert state["session_change_pct"] == pytest.approx(200 / 198 - 1)
    assert state["session"] == "PREMARKET"
    location = strike_location(
        strike=Decimal("220"), current_price=200, atr14=5,
        tolerance_pct=Decimal("0.0025"),
    )
    assert location == {
        "availability": "AVAILABLE", "strike_distance_usd": 20,
        "strike_distance_pct": pytest.approx(0.1), "strike_distance_atr": 4,
        "state": "ABOVE_SPOT",
    }
    unavailable = strike_location(
        strike=220, current_price=None, atr14=None, tolerance_pct=Decimal("0.0025")
    )
    assert unavailable["strike_distance_pct"] is None


def test_term_structure_exact_and_neighbours_keep_contract_iv_separate() -> None:
    result = map_term_structure(
        {"data": {"date": "2026-08-12", "nodes": [
            {"expiry": "2026-08-14", "dte": 2, "implied_vol_pct": 0.40},
            {"expiry": "2026-08-21", "dte": 9, "implied_vol_pct": 0.33,
             "implied_move_usd": 7.8, "implied_move_pct": 0.035},
            {"expiry": "2026-08-28", "dte": 16, "implied_vol_pct": 0.35},
        ]}},
        candidate_expiration=date(2026, 8, 21), contract_iv=0.2973,
    )
    assert result["exact_match_status"] == "EXACT_MATCH"
    assert result["nearest_shorter_node"]["expiry"] == "2026-08-14"
    assert result["nearest_longer_node"]["expiry"] == "2026-08-28"
    assert result["candidate_iv_minus_shorter"] == pytest.approx(-0.07)
    assert result["candidate_iv_minus_longer"] == pytest.approx(-0.02)
    assert result["contract_iv"] == 0.2973
    assert result["candidate_term_iv"] == 0.33
    assert result["curve_classification"] is None


def test_missing_term_node_is_explicit_and_not_interpolated() -> None:
    result = map_term_structure(
        {"data": {"nodes": [{"expiry": "2026-08-14", "dte": 2,
                              "implied_vol_pct": 0.4}]}},
        candidate_expiration=date(2026, 8, 21), contract_iv=0.3,
    )
    assert result["exact_match_status"] == "NOT_PRESENT"
    assert result["candidate_node"] is None
    assert result["candidate_term_iv"] is None


def test_heatmap_requires_exact_joint_cell_and_preserves_sparse_missing() -> None:
    payload = {"data": {
        "state": "degraded", "spot_usd": 224, "generated_at": "2026-08-13T08:00:00Z",
        "cells": [
            {"expiration": "2026-08-21", "strike_usd": 215, "net_dealer_gex_usd": 1},
            {"expiration": "2026-08-28", "strike_usd": 220, "net_dealer_gex_usd": 2},
        ],
        "row_stacks": [
            {"strike_usd": 220, "row_net_wall_gex_usd": 10,
             "row_abs_wall_gex_usd": 20, "rank": 1},
            {"strike_usd": 225, "row_net_wall_gex_usd": -5,
             "row_abs_wall_gex_usd": 5, "rank": 2},
        ],
    }, "_meta": {"truncated": False}}
    result = evaluate_heatmap(
        payload, expiration=date(2026, 8, 21), strike=220, current_price=224
    )
    assert result["quality"] == "AVAILABLE_DEGRADED"
    assert result["candidate_heatmap_cell_status"] == "NOT_PRESENT"
    assert result["candidate_cell"] is None
    assert result["candidate_row_stack"]["rank"] == 1
    assert result["top_vendor_ranked_rows"][0]["distance_from_candidate_strike_usd"] == 0
    assert result["nearest_negative_net_row"]["strike_usd"] == 225
    assert result["complete_surface_concentration"] is None


def test_heatmap_exact_cell_and_truncation_quality() -> None:
    cell = {"expiration": "2026-08-21", "strike_usd": 220,
            "net_dealer_gex_usd": 3, "call_gex_usd": 4, "put_gex_usd": -1}
    result = evaluate_heatmap(
        {"data": {"cells": [cell], "row_stacks": []}, "_meta": {"truncated": True}},
        expiration=date(2026, 8, 21), strike=Decimal("220.000000"), current_price=224,
    )
    assert result["quality"] == "INCOMPLETE_OR_TRUNCATED"
    assert result["candidate_heatmap_cell_status"] == "EXACT_MATCH"
    assert result["candidate_cell"] == cell


def test_no_iv_rv_skew_gex_score_or_support_labels_exist() -> None:
    result = evaluate_heatmap(
        {"data": {"cells": [], "row_stacks": []}},
        expiration=date(2026, 8, 21), strike=220, current_price=224,
    )
    serialized = str(result).lower()
    assert "support" not in serialized
    assert "resistance" not in serialized
    assert "gex_score" not in serialized

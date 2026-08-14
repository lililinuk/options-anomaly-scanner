from datetime import date, timedelta
from decimal import Decimal

import pytest

from app.confirmation.domain import (
    calculate_price_context,
    canonical_regular_daily,
    evaluate_heatmap,
    map_term_structure,
    normalize_heatmap_payload,
    normalize_stock_state,
    strike_location,
)


def bars(count: int, *, descending: bool = False) -> list[dict[str, object]]:
    result: list[dict[str, object]] = []
    for index in range(count):
        close = float(200 - index if descending else 100 + index)
        trading_date = date(2026, 1, 2) + timedelta(days=index)
        result.append(
            {
                "trading_date": trading_date.isoformat(),
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
    series = canonical_regular_daily(rows)
    assert series.policy == "VALID_REGULAR_SESSION_OBSERVATIONS"
    assert [row["close_usd"] for row in series.observations] == [100]
    assert series.raw_bar_count == 3
    assert series.distinct_trading_date_count == 1
    assert series.missing_regular_dates == ()
    assert series.ambiguous_regular_dates == ()


def test_missing_and_duplicate_dates_do_not_invalidate_surrounding_rows() -> None:
    rows = [
        {"trading_date": "2026-08-10", "session": "regular", "close_usd": 100},
        {"trading_date": "2026-08-11", "session": "postmarket", "close_usd": 101},
        {"trading_date": "2026-08-12", "session": "premarket", "close_usd": 102},
        {"trading_date": "2026-08-13", "session": "regular", "close_usd": 103},
        {"trading_date": "2026-08-13", "session": "regular", "close_usd": 104},
        {"trading_date": "2026-08-14", "session": "regular", "close_usd": 105},
    ]
    series = canonical_regular_daily(list(reversed(rows)))
    assert [row["trading_date"] for row in series.observations] == [
        "2026-08-10",
        "2026-08-14",
    ]
    assert series.missing_regular_dates == ("2026-08-11", "2026-08-12")
    assert series.ambiguous_regular_dates == ("2026-08-13",)


def test_price_features_are_deterministic_and_preserve_adjustment_caveat() -> None:
    rows = bars(60)
    rows.insert(31, {"trading_date": "2025-12-31", "session": "postmarket"})
    result = calculate_price_context(
        {"data": {"as_of": "2026-08-12T04:00:00Z", "bars": rows}}
    )
    assert result["availability"] == "AVAILABLE_WITH_GAPS"
    assert result["coverage_quality"] == "VALID_WITH_GAPS"
    assert result["valid_regular_session_count"] == 60
    assert result["missing_regular_date_count"] == 1
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


@pytest.mark.parametrize(
    ("count", "present", "missing"),
    [
        (1, (), ("return_1d", "sma_20", "atr_14")),
        (5, ("return_1d",), ("return_5d", "sma_20", "atr_14")),
        (14, ("return_5d",), ("atr_14", "sma_20")),
        (15, ("atr_14",), ("sma_20",)),
        (20, ("sma_20", "rolling_high_20"), ("return_20d", "sma_50")),
        (21, ("return_20d",), ("sma_50",)),
        (49, ("sma_20", "atr_14"), ("sma_50",)),
        (50, ("sma_50", "return_20d", "atr_14"), ()),
    ],
)
def test_partial_histories_have_per_feature_nulls(
    count: int, present: tuple[str, ...], missing: tuple[str, ...]
) -> None:
    result = calculate_price_context({"data": {"bars": bars(count)}})
    for name in present:
        assert result[name] is not None
    for name in missing:
        assert result[name] is None
    if count < 50:
        assert result["trend"] == "UNKNOWN"


def test_valid_observation_indexing_skips_calendar_gap_without_off_by_one() -> None:
    rows = bars(21)
    rows.insert(10, {"trading_date": "2026-01-01", "session": "postmarket"})
    result = calculate_price_context({"data": {"bars": list(reversed(rows))}})
    assert result["return_1d"] == pytest.approx(120 / 119 - 1)
    assert result["return_5d"] == pytest.approx(120 / 115 - 1)
    assert result["return_20d"] == pytest.approx(120 / 100 - 1)
    assert result["sma_20"] == pytest.approx(sum(range(101, 121)) / 20)
    assert result["rolling_high_20"] == 121
    assert result["rolling_low_20"] == 100
    assert result["atr_14"] == 2


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


def test_strike_location_states_tolerance_and_missing_atr() -> None:
    below = strike_location(
        strike=190, current_price=200, atr14=None, tolerance_pct=Decimal("0.0025")
    )
    at_spot = strike_location(
        strike=200.4, current_price=200, atr14=5, tolerance_pct=Decimal("0.0025")
    )
    assert below["state"] == "BELOW_SPOT"
    assert below["strike_distance_atr"] is None
    assert at_spot["state"] == "AT_SPOT_APPROX"


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
    assert result["availability"] == "AVAILABLE_DEGRADED"
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
    assert result["row_stack_status"] == "ROW_NOT_PRESENT"


def test_degraded_exact_cell_and_row_preserve_vendor_values() -> None:
    cell = {
        "expiration": "2026-08-21", "strike_usd": 220,
        "net_dealer_gex_usd": 59652544,
        "call_gex_usd": 59166863,
        "put_gex_usd": 485681,
    }
    row = {
        "strike_usd": 220,
        "row_net_wall_gex_usd": 81553764,
        "row_abs_wall_gex_usd": 121659202,
        "rank": 1,
    }
    result = evaluate_heatmap(
        {"data": {"state": "degraded", "cells": [cell], "row_stacks": [row]}},
        expiration=date(2026, 8, 21), strike=220, current_price=224,
    )
    assert result["availability"] == "AVAILABLE_DEGRADED"
    assert result["candidate_heatmap_cell_status"] == "EXACT_MATCH"
    assert result["row_stack_status"] == "ROW_EXACT_MATCH"
    assert result["candidate_cell"] == cell
    assert result["candidate_row_stack"] == row
    assert result["candidate_net_gex_usd"] == 59652544
    assert result["candidate_call_gex_usd"] == 59166863
    assert result["candidate_put_gex_usd"] == 485681
    assert result["row_net_gex_usd"] == 81553764
    assert result["row_abs_gex_usd"] == 121659202
    assert result["vendor_row_rank"] == 1


@pytest.mark.parametrize(
    "data",
    [
        {"cells": None, "row_stacks": []},
        {"cells": [], "row_stacks": None},
        {"cells": None, "row_stacks": None},
        {"row_stacks": []},
        {"cells": []},
        {"cells": {}, "row_stacks": []},
        {"cells": [], "row_stacks": "not-a-collection"},
        {"cells": [None], "row_stacks": []},
    ],
)
def test_heatmap_nullable_omitted_or_malformed_collections_are_unavailable(
    data: dict[str, object],
) -> None:
    result = evaluate_heatmap(
        {"data": data},
        expiration=date(2026, 8, 21),
        strike=220,
        current_price=224,
    )
    assert result["availability"] == "UNAVAILABLE"
    assert result["candidate_heatmap_cell_status"] == "UNAVAILABLE"
    assert result["row_stack_status"] == "ROW_UNAVAILABLE"
    assert result["candidate_cell"] is None
    assert result["candidate_row_stack"] is None
    assert result["candidate_net_gex_usd"] is None
    assert result["candidate_call_gex_usd"] is None
    assert result["candidate_put_gex_usd"] is None
    assert result["row_net_gex_usd"] is None
    assert result["row_abs_gex_usd"] is None
    assert result["vendor_row_rank"] is None


def test_http_400_heatmap_normalizes_to_safe_structured_unavailable_state() -> None:
    normalized = normalize_heatmap_payload(
        None,
        source_status={
            "status": 400,
            "availability": "UNAVAILABLE",
            "error_code": "VALIDATION_ERROR",
            "captured_at": "2026-08-14T01:02:03Z",
        },
    )
    assert normalized["availability"] == "UNAVAILABLE"
    assert normalized["availability_reason"] == "VALIDATION_ERROR"
    assert normalized["source_http_status"] == 400
    assert normalized["source_error_code"] == "VALIDATION_ERROR"
    assert normalized["cells"] == []
    assert normalized["row_stacks"] == []

    result = evaluate_heatmap(
        {"data": normalized},
        expiration=date(2026, 8, 21),
        strike=220,
        current_price=224,
    )
    assert result["availability"] == "UNAVAILABLE"
    assert result["source_http_status"] == 400
    assert result["candidate_heatmap_cell_status"] == "UNAVAILABLE"


def test_empty_valid_surface_is_not_unavailable_or_exact_cell_missing() -> None:
    result = evaluate_heatmap(
        {"data": {"cells": [], "row_stacks": []}},
        expiration=date(2026, 8, 21),
        strike=220,
        current_price=224,
    )
    assert result["availability"] == "AVAILABLE"
    assert result["candidate_heatmap_cell_status"] == "NOT_PRESENT"
    assert result["row_stack_status"] == "ROW_NOT_PRESENT"


def test_unavailable_not_present_and_exact_zero_gex_remain_distinct() -> None:
    unavailable = evaluate_heatmap(
        None, expiration=date(2026, 8, 21), strike=220, current_price=224
    )
    missing = evaluate_heatmap(
        {"data": {"cells": [], "row_stacks": []}},
        expiration=date(2026, 8, 21), strike=220, current_price=224,
    )
    zero = evaluate_heatmap(
        {"data": {"cells": [{
            "expiration": "2026-08-21", "strike_usd": 220,
            "net_dealer_gex_usd": 0, "call_gex_usd": 0, "put_gex_usd": 0,
        }], "row_stacks": [{
            "strike_usd": 220, "row_net_wall_gex_usd": 0,
            "row_abs_wall_gex_usd": 0, "rank": 4,
        }]}},
        expiration=date(2026, 8, 21), strike=220, current_price=224,
    )
    assert unavailable["candidate_heatmap_cell_status"] == "UNAVAILABLE"
    assert unavailable["candidate_net_gex_usd"] is None
    assert missing["candidate_heatmap_cell_status"] == "NOT_PRESENT"
    assert missing["candidate_net_gex_usd"] is None
    assert zero["candidate_heatmap_cell_status"] == "EXACT_MATCH"
    assert zero["candidate_net_gex_usd"] == 0
    assert zero["row_stack_status"] == "ROW_EXACT_MATCH"
    assert zero["row_net_gex_usd"] == 0


def test_no_iv_rv_skew_gex_score_or_support_labels_exist() -> None:
    result = evaluate_heatmap(
        {"data": {"cells": [], "row_stacks": []}},
        expiration=date(2026, 8, 21), strike=220, current_price=224,
    )
    serialized = str(result).lower()
    assert "support" not in serialized
    assert "resistance" not in serialized
    assert "gex_score" not in serialized

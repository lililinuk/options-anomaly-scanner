from __future__ import annotations

from collections import defaultdict
from datetime import date
from decimal import Decimal
from typing import Any

from app.core.time import market_date, utc_now


def _number(value: Any) -> float | None:
    if value is None or isinstance(value, bool):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def canonical_regular_daily(bars: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], str]:
    """Return one regular-session row per date, or preserve uncertainty explicitly."""

    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for bar in bars:
        trading_date = bar.get("trading_date")
        if isinstance(trading_date, str):
            grouped[trading_date].append(bar)
    if not grouped:
        return [], "DAILY_SESSION_POLICY_UNRESOLVED"
    selected: list[dict[str, Any]] = []
    for _trading_date, rows in grouped.items():
        regular = [row for row in rows if str(row.get("session", "")).lower() == "regular"]
        if len(regular) != 1:
            return [], "DAILY_SESSION_POLICY_UNRESOLVED"
        selected.append(regular[0])
    selected.sort(key=lambda row: str(row["trading_date"]))
    return selected, "REGULAR_SESSION_ONLY"


def _return(closes: list[float], periods: int) -> float | None:
    if len(closes) <= periods or closes[-periods - 1] == 0:
        return None
    return closes[-1] / closes[-periods - 1] - 1


def _mean(values: list[float], length: int) -> float | None:
    return sum(values[-length:]) / length if len(values) >= length else None


def _atr(rows: list[dict[str, Any]], length: int = 14) -> float | None:
    if len(rows) < length + 1:
        return None
    true_ranges: list[float] = []
    for index in range(1, len(rows)):
        high = _number(rows[index].get("high_usd"))
        low = _number(rows[index].get("low_usd"))
        previous_close = _number(rows[index - 1].get("close_usd"))
        if high is None or low is None or previous_close is None:
            return None
        true_ranges.append(max(high - low, abs(high - previous_close), abs(low - previous_close)))
    return sum(true_ranges[-length:]) / length


def calculate_price_context(payload: dict[str, Any]) -> dict[str, Any]:
    data = payload.get("data") if isinstance(payload.get("data"), dict) else payload
    bars = data.get("bars") if isinstance(data, dict) else None
    bars = bars if isinstance(bars, list) else []
    canonical, policy = canonical_regular_daily([row for row in bars if isinstance(row, dict)])
    base: dict[str, Any] = {
        "availability": "UNAVAILABLE" if not bars else "PARTIAL",
        "daily_session_policy": policy,
        "price_adjustment_semantics": "UNCONFIRMED",
        "vendor_as_of": data.get("as_of") if isinstance(data, dict) else None,
        "canonical_observation_count": len(canonical),
        "return_1d": None,
        "return_5d": None,
        "return_20d": None,
        "sma_20": None,
        "sma_50": None,
        "distance_to_sma20_pct": None,
        "distance_to_sma50_pct": None,
        "rolling_high_20": None,
        "rolling_low_20": None,
        "atr_14": None,
        "trend": "UNKNOWN",
    }
    if not canonical:
        return base
    closes = [_number(row.get("close_usd")) for row in canonical]
    highs = [_number(row.get("high_usd")) for row in canonical]
    lows = [_number(row.get("low_usd")) for row in canonical]
    if any(value is None for value in closes):
        return base
    numeric_closes = [float(value) for value in closes if value is not None]
    latest = numeric_closes[-1]
    sma20 = _mean(numeric_closes, 20)
    sma50 = _mean(numeric_closes, 50)
    base.update(
        {
            "availability": "AVAILABLE" if len(canonical) >= 50 else "INSUFFICIENT_HISTORY",
            "latest_trading_date": canonical[-1].get("trading_date"),
            "latest_regular_close_usd": latest,
            "return_1d": _return(numeric_closes, 1),
            "return_5d": _return(numeric_closes, 5),
            "return_20d": _return(numeric_closes, 20),
            "sma_20": sma20,
            "sma_50": sma50,
            "distance_to_sma20_pct": latest / sma20 - 1 if sma20 else None,
            "distance_to_sma50_pct": latest / sma50 - 1 if sma50 else None,
            "rolling_high_20": max(float(v) for v in highs[-20:] if v is not None)
            if len(highs) >= 20 and all(v is not None for v in highs[-20:])
            else None,
            "rolling_low_20": min(float(v) for v in lows[-20:] if v is not None)
            if len(lows) >= 20 and all(v is not None for v in lows[-20:])
            else None,
            "atr_14": _atr(canonical),
        }
    )
    if sma20 is not None and sma50 is not None:
        if latest > sma20 > sma50:
            base["trend"] = "UPTREND"
        elif latest < sma20 < sma50:
            base["trend"] = "DOWNTREND"
        else:
            base["trend"] = "MIXED"
    return base


def normalize_stock_state(payload: dict[str, Any]) -> dict[str, Any]:
    data = payload.get("data") if isinstance(payload.get("data"), dict) else payload
    current = _number(data.get("close_usd"))
    previous = _number(data.get("prev_close_usd"))
    return {
        "availability": "AVAILABLE" if current is not None else "UNAVAILABLE",
        "current_price_usd": current,
        "previous_close_usd": previous,
        "session_change_pct": current / previous - 1 if current is not None and previous else None,
        "session": str(data.get("session")).upper() if data.get("session") else None,
        "volume_shares": data.get("volume_shares"),
        "total_volume_shares": data.get("total_volume_shares"),
        "as_of": data.get("as_of"),
    }


def strike_location(
    *, strike: Decimal | float, current_price: float | None, atr14: float | None,
    tolerance_pct: Decimal,
) -> dict[str, Any]:
    if current_price is None or current_price == 0:
        return {
            "availability": "UNAVAILABLE", "strike_distance_usd": None,
            "strike_distance_pct": None, "strike_distance_atr": None, "state": None,
        }
    distance = float(strike) - current_price
    distance_pct = float(strike) / current_price - 1
    state = "AT_SPOT_APPROX" if abs(distance_pct) <= float(tolerance_pct) else (
        "ABOVE_SPOT" if distance > 0 else "BELOW_SPOT"
    )
    return {
        "availability": "AVAILABLE", "strike_distance_usd": distance,
        "strike_distance_pct": distance_pct,
        "strike_distance_atr": distance / atr14 if atr14 else None, "state": state,
    }


def map_term_structure(
    payload: dict[str, Any], *, candidate_expiration: date, contract_iv: float | None
) -> dict[str, Any]:
    data = payload.get("data") if isinstance(payload.get("data"), dict) else payload
    nodes = [row for row in data.get("nodes", []) if isinstance(row, dict)]
    target = candidate_expiration.isoformat()
    exact = next((row for row in nodes if row.get("expiry") == target), None)
    candidate_dte = int(exact["dte"]) if exact and exact.get("dte") is not None else None
    if candidate_dte is None:
        candidate_dte = max(0, (candidate_expiration - market_date(utc_now())).days)
    shorter = max(
        (row for row in nodes if isinstance(row.get("dte"), int) and row["dte"] < candidate_dte),
        key=lambda row: row["dte"], default=None,
    )
    longer = min(
        (row for row in nodes if isinstance(row.get("dte"), int) and row["dte"] > candidate_dte),
        key=lambda row: row["dte"], default=None,
    )
    candidate_iv = _number(exact.get("implied_vol_pct")) if exact else None
    shorter_iv = _number(shorter.get("implied_vol_pct")) if shorter else None
    longer_iv = _number(longer.get("implied_vol_pct")) if longer else None
    return {
        "availability": "AVAILABLE" if nodes else "UNAVAILABLE",
        "vendor_date": data.get("date"), "as_of": data.get("as_of"),
        "exact_match_status": "EXACT_MATCH" if exact else "NOT_PRESENT",
        "candidate_node": exact, "nearest_shorter_node": shorter, "nearest_longer_node": longer,
        "candidate_iv_minus_shorter": candidate_iv - shorter_iv
        if candidate_iv is not None and shorter_iv is not None else None,
        "candidate_iv_minus_longer": candidate_iv - longer_iv
        if candidate_iv is not None and longer_iv is not None else None,
        "contract_iv": contract_iv, "candidate_term_iv": candidate_iv,
        "contract_iv_minus_expiry_node": contract_iv - candidate_iv
        if contract_iv is not None and candidate_iv is not None else None,
        "comparison_label": "CONTRACT_IV_VS_EXPIRY_NODE_CONTEXT",
        "curve_classification": None,
    }


def evaluate_heatmap(
    payload: dict[str, Any], *, expiration: date, strike: Decimal | float,
    current_price: float | None,
) -> dict[str, Any]:
    data = payload.get("data") if isinstance(payload.get("data"), dict) else payload
    meta = payload.get("_meta") if isinstance(payload.get("_meta"), dict) else {}
    cells = [row for row in data.get("cells", []) if isinstance(row, dict)]
    rows = [row for row in data.get("row_stacks", []) if isinstance(row, dict)]
    target_expiry, target_strike = expiration.isoformat(), float(strike)
    exact = next(
        (row for row in cells if row.get("expiration") == target_expiry
         and _number(row.get("strike_usd")) == target_strike), None,
    )
    candidate_row = next(
        (row for row in rows if _number(row.get("strike_usd")) == target_strike), None
    )
    truncated = bool(meta.get("truncated") or data.get("truncated"))
    vendor_state = data.get("state")
    quality = "INCOMPLETE_OR_TRUNCATED" if truncated else (
        "AVAILABLE_DEGRADED" if str(vendor_state).lower() == "degraded" else
        "AVAILABLE" if data else "UNAVAILABLE"
    )
    ranked = sorted(rows, key=lambda row: (row.get("rank") is None, row.get("rank", 10**9)))[:5]
    top_rows = [
        {
            **row,
            "distance_from_spot_usd": _number(row.get("strike_usd")) - current_price
            if current_price is not None and _number(row.get("strike_usd")) is not None else None,
            "distance_from_candidate_strike_usd": _number(row.get("strike_usd")) - target_strike
            if _number(row.get("strike_usd")) is not None else None,
        }
        for row in ranked
    ]
    positive = [row for row in rows if (_number(row.get("row_net_wall_gex_usd")) or 0) > 0]
    negative = [row for row in rows if (_number(row.get("row_net_wall_gex_usd")) or 0) < 0]

    def nearest(available: list[dict[str, Any]]) -> dict[str, Any] | None:
        if current_price is None:
            return None
        return min(
            available,
            key=lambda row: abs((_number(row.get("strike_usd")) or current_price) - current_price),
            default=None,
        )

    return {
        "availability": "DEGRADED" if quality != "AVAILABLE" and data else quality,
        "quality": quality, "vendor_state": vendor_state, "generated_at": data.get("generated_at"),
        "session_date_et": data.get("session_date_et"), "market_status": data.get("market_status"),
        "spot_usd": _number(data.get("spot_usd")), "truncated": truncated,
        "cell_count": len(cells), "row_count": len(rows),
        "candidate_heatmap_cell_status": "EXACT_MATCH" if exact else "NOT_PRESENT",
        "candidate_cell": exact, "candidate_row_stack": candidate_row,
        "top_vendor_ranked_rows": top_rows,
        "nearest_positive_net_row": nearest(positive),
        "nearest_negative_net_row": nearest(negative),
        "complete_surface_concentration": None,
    }

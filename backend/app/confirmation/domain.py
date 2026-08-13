from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
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


@dataclass(frozen=True)
class CanonicalDailySeries:
    observations: tuple[dict[str, Any], ...]
    raw_bar_count: int
    distinct_trading_date_count: int
    missing_regular_dates: tuple[str, ...]
    ambiguous_regular_dates: tuple[str, ...]
    policy: str = "VALID_REGULAR_SESSION_OBSERVATIONS"

    @property
    def valid_observation_count(self) -> int:
        return len(self.observations)


def canonical_regular_daily(bars: list[dict[str, Any]]) -> CanonicalDailySeries:
    """Keep every unambiguous regular row and flag only the unusable dates."""

    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for bar in bars:
        trading_date = bar.get("trading_date")
        if isinstance(trading_date, str):
            grouped[trading_date].append(bar)
    selected: list[dict[str, Any]] = []
    missing: list[str] = []
    ambiguous: list[str] = []
    for trading_date, rows in grouped.items():
        regular = [row for row in rows if str(row.get("session", "")).lower() == "regular"]
        if len(regular) == 1:
            selected.append(regular[0])
        elif not regular:
            missing.append(trading_date)
        else:
            ambiguous.append(trading_date)
    selected.sort(key=lambda row: str(row["trading_date"]))
    return CanonicalDailySeries(
        observations=tuple(selected),
        raw_bar_count=len(bars),
        distinct_trading_date_count=len(grouped),
        missing_regular_dates=tuple(sorted(missing)),
        ambiguous_regular_dates=tuple(sorted(ambiguous)),
    )


def _return(closes: list[float | None], periods: int) -> float | None:
    if (
        len(closes) <= periods
        or closes[-1] is None
        or closes[-periods - 1] in {None, 0}
    ):
        return None
    return float(closes[-1]) / float(closes[-periods - 1]) - 1


def _mean(values: list[float | None], length: int) -> float | None:
    window = values[-length:]
    return sum(value for value in window if value is not None) / length if (
        len(window) == length and all(value is not None for value in window)
    ) else None


def _atr(rows: list[dict[str, Any]], length: int = 14) -> float | None:
    if len(rows) < length + 1:
        return None
    window = rows[-(length + 1) :]
    true_ranges: list[float] = []
    for index in range(1, len(window)):
        high = _number(window[index].get("high_usd"))
        low = _number(window[index].get("low_usd"))
        previous_close = _number(window[index - 1].get("close_usd"))
        if high is None or low is None or previous_close is None:
            return None
        true_ranges.append(max(high - low, abs(high - previous_close), abs(low - previous_close)))
    return sum(true_ranges[-length:]) / length


def calculate_price_context(
    payload: dict[str, Any],
    *,
    return_windows: tuple[int, ...] = (1, 5, 20),
    sma_windows: tuple[int, ...] = (20, 50),
    atr_window: int = 14,
    rolling_range_window: int = 20,
) -> dict[str, Any]:
    data = payload.get("data") if isinstance(payload.get("data"), dict) else payload
    bars = data.get("bars") if isinstance(data, dict) else None
    bars = bars if isinstance(bars, list) else []
    canonical = canonical_regular_daily([row for row in bars if isinstance(row, dict)])
    observations = list(canonical.observations)
    has_gaps = bool(canonical.missing_regular_dates or canonical.ambiguous_regular_dates)
    required_history = max(
        [window + 1 for window in return_windows]
        + list(sma_windows)
        + [atr_window + 1, rolling_range_window]
    )
    coverage_quality = (
        "UNAVAILABLE"
        if not observations
        else "INSUFFICIENT_HISTORY"
        if len(observations) < required_history
        else "VALID_WITH_GAPS"
        if has_gaps
        else "COMPLETE_FOR_WINDOW"
    )
    base: dict[str, Any] = {
        "availability": "UNAVAILABLE" if not observations else "PARTIAL",
        "daily_session_policy": canonical.policy,
        "price_adjustment_semantics": "UNCONFIRMED",
        "vendor_as_of": data.get("as_of") if isinstance(data, dict) else None,
        "raw_bar_count": canonical.raw_bar_count,
        "distinct_trading_date_count": canonical.distinct_trading_date_count,
        "canonical_observation_count": canonical.valid_observation_count,
        "valid_regular_session_count": canonical.valid_observation_count,
        "missing_regular_date_count": len(canonical.missing_regular_dates),
        "ambiguous_regular_date_count": len(canonical.ambiguous_regular_dates),
        "missing_regular_dates": list(canonical.missing_regular_dates),
        "ambiguous_regular_dates": list(canonical.ambiguous_regular_dates),
        "oldest_valid_regular_date": (
            observations[0].get("trading_date") if observations else None
        ),
        "latest_valid_regular_date": (
            observations[-1].get("trading_date") if observations else None
        ),
        "coverage_quality": coverage_quality,
        "calculation_basis": {
            "observation_unit": "VALID_REGULAR_SESSION_OBSERVATION",
            "return_windows": list(return_windows),
            "return_indexing": "latest_close / close_N_valid_observations_back - 1",
            "sma_windows": list(sma_windows),
            "atr_window": atr_window,
            "atr_method": "ARITHMETIC_MEAN_TRUE_RANGE",
            "rolling_range_window": rolling_range_window,
        },
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
    if not observations:
        return base
    closes = [_number(row.get("close_usd")) for row in observations]
    highs = [_number(row.get("high_usd")) for row in observations]
    lows = [_number(row.get("low_usd")) for row in observations]
    latest = closes[-1]
    returns = {window: _return(closes, window) for window in return_windows}
    smas = {window: _mean(closes, window) for window in sma_windows}
    sma20 = smas.get(20)
    sma50 = smas.get(50)
    rolling_high = (
        max(float(value) for value in highs[-rolling_range_window:] if value is not None)
        if len(highs) >= rolling_range_window
        and all(value is not None for value in highs[-rolling_range_window:])
        else None
    )
    rolling_low = (
        min(float(value) for value in lows[-rolling_range_window:] if value is not None)
        if len(lows) >= rolling_range_window
        and all(value is not None for value in lows[-rolling_range_window:])
        else None
    )
    atr = _atr(observations, atr_window)
    feature_values = [*returns.values(), *smas.values(), rolling_high, rolling_low, atr]
    available_count = sum(value is not None for value in feature_values)
    availability = (
        "UNAVAILABLE"
        if latest is None
        else "AVAILABLE_WITH_GAPS"
        if available_count == len(feature_values) and has_gaps
        else "AVAILABLE"
        if available_count == len(feature_values)
        else "PARTIAL"
        if available_count
        else "INSUFFICIENT_HISTORY"
    )
    base.update(
        {
            "availability": availability,
            "latest_trading_date": observations[-1].get("trading_date"),
            "latest_regular_close_usd": latest,
            "return_1d": returns.get(1),
            "return_5d": returns.get(5),
            "return_20d": returns.get(20),
            "sma_20": sma20,
            "sma_50": sma50,
            "distance_to_sma20_pct": (
                latest / sma20 - 1 if latest is not None and sma20 else None
            ),
            "distance_to_sma50_pct": (
                latest / sma50 - 1 if latest is not None and sma50 else None
            ),
            "rolling_high_20": rolling_high if rolling_range_window == 20 else None,
            "rolling_low_20": rolling_low if rolling_range_window == 20 else None,
            "atr_14": atr if atr_window == 14 else None,
        }
    )
    if latest is not None and sma20 is not None and sma50 is not None:
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

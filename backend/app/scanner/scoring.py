from __future__ import annotations

import statistics
from collections.abc import Iterable, Sequence
from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal

from app.models.signals import DteBucket, bucket_for_dte, calendar_dte
from app.scanner.config import COMPONENT_MAX, SCORE_ANCHORS


def piecewise(value: float, anchors: Sequence[tuple[float, float]]) -> float:
    """Capped piecewise-linear interpolation over validated configuration anchors."""
    if not anchors:
        raise ValueError("At least one interpolation anchor is required")
    if value <= anchors[0][0]:
        return float(anchors[0][1])
    for (x0, y0), (x1, y1) in zip(anchors, anchors[1:], strict=False):
        if value <= x1:
            return float(y0 + (value - x0) / (x1 - x0) * (y1 - y0))
    return float(anchors[-1][1])


def safe_ratio(numerator: float | int | None, denominator: float | int | None) -> float | None:
    if numerator is None or denominator in (None, 0):
        return None
    return float(numerator) / float(denominator)


def skew(call_value: float | int | None, put_value: float | int | None) -> float | None:
    if call_value is None or put_value is None or call_value + put_value == 0:
        return None
    return (float(call_value) - float(put_value)) / (float(call_value) + float(put_value))


def normalized_score(
    components: dict[str, tuple[float, float] | None],
) -> tuple[float, float, list[str]]:
    available = {key: value for key, value in components.items() if value is not None}
    basis = sum(value[1] for value in available.values())
    earned = sum(value[0] for value in available.values())
    missing = sorted(set(components) - set(available))
    return (round(earned / basis * 100, 3) if basis else 0.0, basis, missing)


def expiry_type(expiration: date, vendor_type: str | None = None) -> tuple[str, str]:
    if vendor_type:
        return vendor_type.upper(), "VENDOR"
    third_friday = expiration.weekday() == 4 and 15 <= expiration.day <= 21
    return ("STANDARD_MONTHLY" if third_friday else "OTHER", "INFERRED")


def neighbor_ratio(current_oi: int, peer_oi: Iterable[int]) -> tuple[float | None, str]:
    peers = [value for value in peer_oi if value >= 0]
    if not peers:
        return None, "INSUFFICIENT"
    baseline = statistics.median(peers)
    if baseline <= 0:
        return None, "INSUFFICIENT"
    return current_oi / baseline, "NEIGHBOR"


def robust_z_score(value: float, history: Iterable[float]) -> float | None:
    observations = [float(item) for item in history]
    if len(observations) < 10:
        return None
    median = statistics.median(observations)
    mad = statistics.median(abs(item - median) for item in observations)
    if mad == 0:
        return None
    return 0.6745 * (value - median) / mad


def preliminary_expiry_score(
    volume_share: float | None, neighbor: float | None, volume_skew: float | None
) -> tuple[float, float, list[str], dict[str, float]]:
    values = {
        "volume_concentration": (piecewise(volume_share, SCORE_ANCHORS["prelim_volume_share"]), 40)
        if volume_share is not None
        else None,
        "neighbor_oi_anomaly": (piecewise(neighbor, SCORE_ANCHORS["prelim_neighbor"]), 30)
        if neighbor is not None
        else None,
        "volume_skew_strength": (piecewise(abs(volume_skew), SCORE_ANCHORS["prelim_skew"]), 30)
        if volume_skew is not None
        else None,
    }
    score, basis, missing = normalized_score(values)
    return score, basis, missing, {k: round(v[0], 3) for k, v in values.items() if v}


def moneyness_points(delta: float | None) -> float | None:
    if delta is None:
        return None
    value = abs(delta)
    if value < 0.10:
        return 2
    if value < 0.20:
        return 5
    if value < 0.35:
        return 8
    if value <= 0.65:
        return 10
    if value < 0.80:
        return 8
    if value < 0.90:
        return 5
    return 4


@dataclass(frozen=True)
class ContractInput:
    volume: int
    previous_oi: int
    estimated_premium: float | None
    spread_pct: float | None
    delta: float | None
    robust_z: float | None = None
    history_count: int = 0
    burst_ratio: float | None = None
    dte: int = 0
    quote_supplied: bool = True


@dataclass(frozen=True)
class ContractScore:
    score: float
    basis: float
    classification: str
    candidate: bool
    hard_reject: str | None
    flags: tuple[str, ...]
    components: dict[str, float] = field(default_factory=dict)


def score_contract(item: ContractInput) -> ContractScore:
    flags: list[str] = []
    if item.dte > 90:
        return ContractScore(0, 0, "IGNORE", False, "DTE_OUT_OF_RANGE", (), {})
    if item.spread_pct is not None and item.spread_pct > 0.50:
        return ContractScore(0, 0, "IGNORE", False, "SPREAD_OVER_50_PERCENT", (), {})
    if item.quote_supplied and item.spread_pct is None:
        return ContractScore(0, 0, "IGNORE", False, "UNUSABLE_QUOTE", (), {})
    if item.previous_oi < 100:
        flags.append("LOW_OI_BASE")
    if item.delta is not None and abs(item.delta) < 0.10:
        flags.append("LOTTO_RISK")
    ratio = item.volume / max(item.previous_oi, 1)
    activity = piecewise(ratio, SCORE_ANCHORS["contract_volume_oi"]) + piecewise(
        item.volume, SCORE_ANCHORS["contract_volume"]
    )
    history = None
    if item.history_count >= 10 and item.robust_z is not None:
        history = (piecewise(abs(item.robust_z), SCORE_ANCHORS["contract_history"]), 20)
    else:
        flags.append("HISTORY_INSUFFICIENT")
    components: dict[str, tuple[float, float] | None] = {
        "relative_activity": (activity, 20),
        "premium_capital": (
            piecewise(item.estimated_premium, SCORE_ANCHORS["contract_premium"]),
            20,
        )
        if item.estimated_premium is not None
        else None,
        "historical_abnormality": history,
        "intraday_burst": (piecewise(item.burst_ratio, SCORE_ANCHORS["contract_burst"]), 15)
        if item.burst_ratio is not None
        else None,
        "liquidity_quality": (piecewise(item.spread_pct, SCORE_ANCHORS["contract_liquidity"]), 15)
        if item.spread_pct is not None
        else None,
        "moneyness_quality": (
            (moneyness_points(item.delta) or 0, 10) if item.delta is not None else None
        ),
    }
    score, basis, missing = normalized_score(components)
    flags.extend(f"MISSING_{name.upper()}" for name in missing if name != "historical_abnormality")
    classification = (
        "EXTREME"
        if score >= 85
        else "STRONG"
        if score >= 75
        else "CANDIDATE"
        if score >= 65
        else "OBSERVE"
        if score >= 50
        else "IGNORE"
    )
    candidate = score >= 65 and basis >= 60
    return ContractScore(
        score,
        basis,
        classification,
        candidate,
        None,
        tuple(sorted(flags)),
        {key: round(value[0], 3) for key, value in components.items() if value},
    )


def final_expiry_score(
    *,
    oi_share: float | None,
    neighbor: float | None,
    volume_share: float | None,
    skews: Iterable[float | None],
    premium_share: float | None,
) -> tuple[float, float, list[str], dict[str, float]]:
    strongest_skew = max((abs(value) for value in skews if value is not None), default=None)
    configured = (
        ("oi_concentration", oi_share, "final_oi_share"),
        ("neighbor_anomaly", neighbor, "final_neighbor"),
        ("volume_concentration", volume_share, "final_volume_share"),
        ("skew_strength", strongest_skew, "final_skew"),
        ("premium_concentration", premium_share, "final_premium_share"),
    )
    components = {
        name: (piecewise(value, SCORE_ANCHORS[key]), COMPONENT_MAX[key])
        if value is not None
        else None
        for name, value, key in configured
    }
    score, basis, missing = normalized_score(components)
    return score, basis, missing, {k: round(v[0], 3) for k, v in components.items() if v}


def detection_tenor(expiration: date, market_day: date) -> tuple[int, DteBucket | None, list[str]]:
    dte = calendar_dte(expiration, market_day)
    return dte, bucket_for_dte(dte), (["ZERO_DTE"] if dte == 0 else [])


def premium_weighted_strike(rows: Iterable[tuple[Decimal, float]]) -> Decimal | None:
    values = [(strike, premium) for strike, premium in rows if premium > 0]
    total = sum(premium for _, premium in values)
    if total <= 0:
        return None
    return sum((strike * Decimal(str(premium)) for strike, premium in values), Decimal()) / Decimal(
        str(total)
    )

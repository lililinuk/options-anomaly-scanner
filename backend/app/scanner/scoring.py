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


@dataclass(frozen=True)
class FixedScore:
    score: float
    basis: float
    missing: tuple[str, ...]
    components: dict[str, float]


@dataclass(frozen=True)
class ZeroDteScore:
    score: float | None
    basis: float
    status: str
    observation_count: int
    mean: float | None
    median: float | None
    mad: float | None
    percentile: float | None
    robust_deviation: float | None
    method: str
    components: dict[str, float]
    missing: tuple[str, ...]


@dataclass(frozen=True)
class ComparableExpiry:
    dte: int
    volume: int
    expiration_type: str | None = None


@dataclass(frozen=True)
class ComparablePeerSet:
    ratio: float | None
    count: int
    dtes: tuple[int, ...]
    quality: str
    median_volume: float | None


@dataclass(frozen=True)
class DiscoveryResult:
    score: float | None
    primary: float | None
    secondary: float | None
    confirmation_bonus: float
    source: str
    evidence_breadth: int


def same_day_activity_score(
    volume_share: float | None, volume_neighbor_ratio: float | None
) -> FixedScore:
    configured = {
        "expiry_volume_share": (
            piecewise(volume_share, SCORE_ANCHORS["same_day_volume_share"]),
            60.0,
        )
        if volume_share is not None
        else None,
        "comparable_expiry_volume_neighbor_ratio": (
            piecewise(volume_neighbor_ratio, SCORE_ANCHORS["same_day_volume_neighbor"]),
            40.0,
        )
        if volume_neighbor_ratio is not None
        else None,
    }
    present = {key: value for key, value in configured.items() if value is not None}
    return FixedScore(
        score=round(sum(value[0] for value in present.values()), 3),
        basis=sum(value[1] for value in present.values()),
        missing=tuple(sorted(set(configured) - set(present))),
        components={key: round(value[0], 3) for key, value in present.items()},
    )


def zero_dte_activity_score(
    current_volume_share: float | None,
    prior_volume_shares: Sequence[float],
    *,
    required_observations: int = 20,
    mad_epsilon: float = 1e-9,
) -> ZeroDteScore:
    """Score current 0DTE share against prior valid sessions, excluding current by contract."""

    history = [float(value) for value in prior_volume_shares][-required_observations:]
    count = len(history)
    mean = statistics.fmean(history) if history else None
    median = statistics.median(history) if history else None
    mad = (
        statistics.median(abs(value - median) for value in history)
        if median is not None
        else None
    )
    if current_volume_share is None:
        return ZeroDteScore(
            None,
            0,
            "CURRENT_OBSERVATION_UNAVAILABLE",
            count,
            mean,
            median,
            mad,
            None,
            None,
            "CURRENT_OBSERVATION_UNAVAILABLE",
            {},
            ("robust_historical_deviation", "historical_percentile"),
        )
    if count < required_observations:
        return ZeroDteScore(
            None,
            0,
            "INSUFFICIENT",
            count,
            mean,
            median,
            mad,
            None,
            None,
            "INSUFFICIENT_HISTORY",
            {},
            ("robust_historical_deviation", "historical_percentile"),
        )
    assert mean is not None and median is not None and mad is not None
    # Deterministic weak empirical rank: ties count at or below current.
    percentile = sum(value <= current_volume_share for value in history) / count
    percentile_points = piecewise(
        percentile, SCORE_ANCHORS["zero_dte_historical_percentile"]
    )
    if mad <= mad_epsilon:
        return ZeroDteScore(
            round(percentile_points, 3),
            30,
            "READY_PERCENTILE_FALLBACK",
            count,
            mean,
            median,
            mad,
            percentile,
            None,
            "HISTORICAL_PERCENTILE_FALLBACK",
            {"historical_percentile": round(percentile_points, 3)},
            ("robust_historical_deviation",),
        )
    deviation = (current_volume_share - median) / (1.4826 * mad)
    robust_points = piecewise(deviation, SCORE_ANCHORS["zero_dte_robust_deviation"])
    return ZeroDteScore(
        round(robust_points + percentile_points, 3),
        100,
        "READY",
        count,
        mean,
        median,
        mad,
        percentile,
        deviation,
        "MEDIAN_MAD_AND_EMPIRICAL_PERCENTILE",
        {
            "robust_historical_deviation": round(robust_points, 3),
            "historical_percentile": round(percentile_points, 3),
        },
        (),
    )


def comparable_nonzero_expiry_peers(
    target: ComparableExpiry,
    candidates: Sequence[ComparableExpiry],
    *,
    max_peers: int = 4,
    min_peers: int = 2,
) -> ComparablePeerSet:
    if target.dte <= 0 or target.dte > 90:
        return ComparablePeerSet(None, 0, (), "NOT_APPLICABLE", None)
    if target.dte <= 7:
        lower, upper, max_distance = 1, 7, 3
    elif target.dte <= 30:
        lower, upper, max_distance = 8, 30, 7
    else:
        lower, upper, max_distance = 31, 90, 14
    eligible = [
        row
        for row in candidates
        if row is not target
        and lower <= row.dte <= upper
        and row.dte != 0
        and abs(row.dte - target.dte) <= max_distance
        and row.volume >= 0
    ]
    eligible.sort(
        key=lambda row: (
            0
            if target.expiration_type
            and row.expiration_type
            and row.expiration_type == target.expiration_type
            else 1,
            abs(row.dte - target.dte),
            row.dte,
        )
    )
    selected = eligible[:max_peers]
    dtes = tuple(row.dte for row in selected)
    if len(selected) < min_peers:
        return ComparablePeerSet(None, len(selected), dtes, "INSUFFICIENT", None)
    median_volume = float(statistics.median(row.volume for row in selected))
    if median_volume <= 0:
        return ComparablePeerSet(None, len(selected), dtes, "UNUSABLE_ZERO_MEDIAN", median_volume)
    same_type = sum(
        bool(
            target.expiration_type
            and row.expiration_type
            and row.expiration_type == target.expiration_type
        )
        for row in selected
    )
    quality = "SAME_VERIFIED_TYPE" if same_type == len(selected) else "DISTANCE_COMPARABLE"
    return ComparablePeerSet(
        target.volume / median_volume, len(selected), dtes, quality, median_volume
    )


def discovery_with_confirmation(
    same_day: float | None, persistent: float | None
) -> DiscoveryResult:
    available = [("SAME_DAY", same_day), ("PERSISTENT", persistent)]
    present = [(name, float(value)) for name, value in available if value is not None]
    if not present:
        return DiscoveryResult(None, None, None, 0, "NONE", 0)
    primary_name, primary = max(present, key=lambda item: (item[1], item[0] == "SAME_DAY"))
    if len(present) == 1:
        return DiscoveryResult(primary, primary, None, 0, primary_name, 1)
    secondary = min(value for _name, value in present)
    bonus = 10 if secondary >= 80 else 6 if secondary >= 65 else 3 if secondary >= 40 else 0
    source = "BOTH" if bonus else primary_name
    return DiscoveryResult(
        min(100, primary + bonus), primary, secondary, float(bonus), source, 2 if bonus else 1
    )


def discovery_eligible(
    same_day: float | None, persistent: float | None, structural_cold_start: bool
) -> bool:
    return bool(
        (same_day is not None and same_day >= 40)
        or (persistent is not None and persistent >= 65)
        or structural_cold_start
    )


def structure_moneyness_points(delta: float | None) -> float | None:
    if delta is None:
        return None
    value = abs(delta)
    if value < 0.10:
        return 3
    if value < 0.20:
        return 7
    if value < 0.35:
        return 12
    if value <= 0.65:
        return 15
    if value < 0.80:
        return 12
    if value < 0.90:
        return 8
    return 6


@dataclass(frozen=True)
class ContractStructureScore:
    score: float
    basis: float
    classification: str
    candidate: bool
    hard_reject: str | None
    flags: tuple[str, ...]
    components: dict[str, float]


def contract_structure_score(
    *,
    oi_share: float | None,
    neighbor_ratio: float | None,
    spread_pct: float | None,
    delta: float | None,
    quote_supplied: bool,
) -> ContractStructureScore:
    flags: list[str] = []
    hard_reject = "SPREAD_OVER_50_PERCENT" if spread_pct is not None and spread_pct > 0.50 else None
    if quote_supplied and spread_pct is None:
        hard_reject = "UNUSABLE_QUOTE"
    if delta is not None and abs(delta) < 0.10:
        flags.append("LOTTO_RISK")
    values = {
        "same_side_expiry_oi_concentration": (
            piecewise(oi_share, SCORE_ANCHORS["contract_oi_share"]),
            40.0,
        )
        if oi_share is not None
        else None,
        "neighbor_strike_oi_anomaly": (
            piecewise(neighbor_ratio, SCORE_ANCHORS["neighbor_strike_oi"]),
            30.0,
        )
        if neighbor_ratio is not None
        else None,
        "liquidity_quality": (piecewise(spread_pct, SCORE_ANCHORS["structure_liquidity"]), 15.0)
        if spread_pct is not None
        else None,
        "moneyness_delta_quality": (structure_moneyness_points(delta), 15.0)
        if delta is not None
        else None,
    }
    present = {key: value for key, value in values.items() if value is not None}
    score = round(sum(value[0] for value in present.values()), 3)
    classification = (
        "EXTREME_STRUCTURE"
        if score >= 85
        else "STRONG_STRUCTURE"
        if score >= 75
        else "STRUCTURAL_CANDIDATE"
        if score >= 65
        else "OBSERVE"
        if score >= 50
        else "IGNORE"
    )
    return ContractStructureScore(
        score=score,
        basis=sum(value[1] for value in present.values()),
        classification=classification,
        candidate=score >= 65 and hard_reject is None,
        hard_reject=hard_reject,
        flags=tuple(flags),
        components={key: round(value[0], 3) for key, value in present.items()},
    )

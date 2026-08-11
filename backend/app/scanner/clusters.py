from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from decimal import Decimal

from app.scanner.config import SCORE_ANCHORS
from app.scanner.scoring import normalized_score, piecewise, premium_weighted_strike


@dataclass(frozen=True)
class ClusterContract:
    id: str
    strike: Decimal
    volume: int
    previous_oi: int
    premium: float | None
    score: float
    liquidity_points: float | None
    spot: Decimal | None


@dataclass(frozen=True)
class ClusterResult:
    contracts: tuple[ClusterContract, ...]
    score: float
    basis: float
    classification: str
    shape: str
    premium_share: float | None
    volume_share: float | None
    positioning_center: Decimal | None
    components: dict[str, float]


def _monotonic_75(values: Sequence[float]) -> bool:
    if len(values) < 3:
        return False
    deltas = [right - left for left, right in zip(values, values[1:], strict=False)]
    needed = max(1, int(len(deltas) * 0.75 + 0.999))
    return max(sum(delta >= 0 for delta in deltas), sum(delta <= 0 for delta in deltas)) >= needed


def build_clusters(
    *,
    candidates: Sequence[ClusterContract],
    full_strike_ladder: Sequence[Decimal],
    side_volume: int,
    side_premium: float | None,
) -> list[ClusterResult]:
    if len(candidates) < 2:
        return []
    ladder = {strike: index for index, strike in enumerate(sorted(set(full_strike_ladder)))}
    ordered = sorted(
        (row for row in candidates if row.strike in ladder), key=lambda row: row.strike
    )
    groups: list[list[ClusterContract]] = []
    current: list[ClusterContract] = []
    for row in ordered:
        if not current:
            current = [row]
            continue
        prior = current[-1]
        spot = row.spot or prior.spot
        proposed_span = float(row.strike - current[0].strike) / float(spot) if spot else None
        if ladder[row.strike] - ladder[prior.strike] <= 2 and (
            proposed_span is None or proposed_span <= 0.20
        ):
            current.append(row)
        else:
            if len(current) >= 2:
                groups.append(current)
            current = [row]
    if len(current) >= 2:
        groups.append(current)

    results: list[ClusterResult] = []
    for group in groups:
        total_volume = sum(row.volume for row in group)
        premiums = [row.premium for row in group]
        premium_complete = all(value is not None for value in premiums)
        total_premium = (
            sum(float(value) for value in premiums if value is not None)
            if premium_complete
            else None
        )
        if premium_complete and total_premium and total_premium > 0:
            weighted_strength = (
                sum(row.score * float(row.premium or 0) for row in group) / total_premium
            )
        else:
            weighted_strength = (
                sum(row.score * row.volume for row in group) / total_volume if total_volume else 0
            )
        premium_share = (
            total_premium / side_premium if total_premium is not None and side_premium else None
        )
        volume_share = total_volume / side_volume if side_volume else None
        indices = [ladder[row.strike] for row in group]
        has_gap = any(right - left == 2 for left, right in zip(indices, indices[1:], strict=False))
        coherence = (10 if len(group) == 2 else 15 if len(group) == 3 else 20) - (
            5 if has_gap else 0
        )
        liquid = [row.liquidity_points for row in group if row.liquidity_points is not None]
        liquidity = sum(liquid) / len(liquid) / 15 * 10 if liquid else None
        components = {
            "contract_strength": (weighted_strength / 100 * 25, 25),
            "premium_concentration": (
                piecewise(premium_share, SCORE_ANCHORS["cluster_premium_share"]),
                25,
            )
            if premium_share is not None
            else None,
            "volume_concentration": (
                piecewise(volume_share, SCORE_ANCHORS["cluster_volume_share"]),
                20,
            )
            if volume_share is not None
            else None,
            "strike_coherence": (max(0, coherence), 20),
            "liquidity": (liquidity, 10) if liquidity is not None else None,
        }
        score, basis, _ = normalized_score(components)
        spot = next((row.spot for row in group if row.spot), None)
        span = float(group[-1].strike - group[0].strike) / float(spot) if spot else None
        progression = (
            [float(row.premium) for row in group]
            if premium_complete
            else [float(row.volume) for row in group]
        )
        shape = (
            "LADDER"
            if _monotonic_75(progression)
            else "TIGHT_CLUSTER"
            if span is not None and span <= 0.075
            else "BROAD_CLUSTER"
        )
        center = (
            premium_weighted_strike((row.strike, float(row.premium or 0)) for row in group)
            if premium_complete
            else None
        )
        results.append(
            ClusterResult(
                tuple(group),
                score,
                basis,
                "STRONG_CLUSTER"
                if score >= 80
                else "VALID_CLUSTER"
                if score >= 65
                else "INVALID_CLUSTER",
                shape,
                premium_share,
                volume_share,
                center,
                {key: round(value[0], 3) for key, value in components.items() if value},
            )
        )
    return results

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Any

from app.scanner.config import SCORE_ANCHORS
from app.scanner.scoring import piecewise, safe_ratio

WINDOWS = (3, 5, 10)


@dataclass(frozen=True)
class OiHistoryPoint:
    vendor_date: date
    oi: int
    share: float | None = None
    call_share: float | None = None
    put_share: float | None = None


@dataclass(frozen=True)
class PersistenceResult:
    score: float | None
    state: str | None
    winning_window: int | None
    history_confidence: str
    observation_count: int
    features: dict[str, Any]


def history_confidence(count: int) -> str:
    if count < 3:
        return "INSUFFICIENT"
    if count < 5:
        return "LOW"
    if count < 10:
        return "MEDIUM"
    return "FULL"


def _window_features(points: list[OiHistoryPoint], window: int) -> dict[str, Any] | None:
    if len(points) < window:
        return None
    rows = points[-window:]
    first, current = rows[0], rows[-1]
    deltas = [right.oi - left.oi for left, right in zip(rows, rows[1:], strict=False)]
    net = current.oi - first.oi
    growth = safe_ratio(net, first.oi)
    positive = sum(delta > 0 for delta in deltas)
    negative = sum(delta < 0 for delta in deltas)
    direction = "PERSISTENT_BUILD" if net > 0 else "PERSISTENT_DECLINE" if net < 0 else "FLAT"
    matching = positive if net > 0 else negative if net < 0 else 0
    persistence = matching / len(deltas) if deltas else None
    return {
        "window": window,
        "window_first_observation_date": first.vendor_date.isoformat(),
        "window_last_observation_date": current.vendor_date.isoformat(),
        "valid_observation_count": len(rows),
        "net_oi_change": net,
        "oi_growth": growth,
        "oi_share_change": (
            current.share - first.share
            if current.share is not None and first.share is not None
            else None
        ),
        "call_oi_share_change": (
            current.call_share - first.call_share
            if current.call_share is not None and first.call_share is not None
            else None
        ),
        "put_oi_share_change": (
            current.put_share - first.put_share
            if current.put_share is not None and first.put_share is not None
            else None
        ),
        "positive_oi_intervals": positive,
        "negative_oi_intervals": negative,
        "build_persistence": positive / len(deltas) if deltas else None,
        "decline_persistence": negative / len(deltas) if deltas else None,
        "directional_persistence": persistence,
        "state": direction,
    }


def expiry_persistence(points: list[OiHistoryPoint]) -> PersistenceResult:
    ordered = sorted(
        {point.vendor_date: point for point in points}.values(), key=lambda p: p.vendor_date
    )
    windows: dict[str, Any] = {}
    candidates: list[tuple[float, int, str]] = []
    for window in WINDOWS:
        features = _window_features(ordered, window)
        if features is None:
            continue
        share_change = features["oi_share_change"]
        growth = features["oi_growth"]
        persistence = features["directional_persistence"]
        components = {
            "absolute_oi_share_change": piecewise(
                abs(share_change), SCORE_ANCHORS["expiry_persistent_share_change"]
            )
            if share_change is not None
            else None,
            "absolute_oi_growth": piecewise(abs(growth), SCORE_ANCHORS["expiry_persistent_growth"])
            if growth is not None
            else None,
            "directional_persistence": piecewise(
                persistence, SCORE_ANCHORS["directional_persistence"]
            )
            if persistence is not None
            else None,
        }
        score = sum(value for value in components.values() if value is not None)
        features["components"] = components
        features["score"] = score
        windows[str(window)] = features
        candidates.append((score, window, features["state"]))
    winner = max(candidates, default=None)
    return PersistenceResult(
        score=winner[0] if winner else None,
        winning_window=winner[1] if winner else None,
        state=winner[2] if winner else None,
        history_confidence=history_confidence(len(ordered)),
        observation_count=len(ordered),
        features={"windows": windows},
    )


def contract_persistence(
    points: list[OiHistoryPoint],
    *,
    current_same_side_expiry_oi: int | None,
    analysis_date: date | None = None,
) -> PersistenceResult:
    ordered = sorted(
        {
            point.vendor_date: point
            for point in points
            if analysis_date is None or point.vendor_date <= analysis_date
        }.values(),
        key=lambda p: p.vendor_date,
    )
    windows: dict[str, Any] = {}
    candidates: list[tuple[float, int, str]] = []
    for window in WINDOWS:
        features = _window_features(ordered, window)
        if features is None:
            continue
        growth = features["oi_growth"]
        build_share = safe_ratio(abs(features["net_oi_change"]), current_same_side_expiry_oi)
        persistence = features["directional_persistence"]
        components = {
            "absolute_oi_growth": piecewise(
                abs(growth), SCORE_ANCHORS["contract_persistent_growth"]
            )
            if growth is not None
            else None,
            "absolute_build_share": piecewise(
                build_share, SCORE_ANCHORS["contract_persistent_build_share"]
            )
            if build_share is not None
            else None,
            "directional_persistence": piecewise(
                persistence, SCORE_ANCHORS["directional_persistence"]
            )
            if persistence is not None
            else None,
        }
        score = sum(value for value in components.values() if value is not None)
        features["absolute_build_share"] = build_share
        features["components"] = components
        features["score"] = score
        windows[str(window)] = features
        candidates.append((score, window, features["state"]))
    winner = max(candidates, default=None)
    features: dict[str, Any] = {"windows": windows}
    if winner:
        winning_features = windows[str(winner[1])]
        features.update(
            {
                "window_first_observation_date": winning_features[
                    "window_first_observation_date"
                ],
                "window_last_observation_date": winning_features[
                    "window_last_observation_date"
                ],
                "valid_observation_count": winning_features["valid_observation_count"],
                "analysis_date": analysis_date.isoformat() if analysis_date else None,
                "no_lookahead_bound": "VENDOR_OI_DATE_LE_ANALYSIS_DATE"
                if analysis_date
                else "CALLER_NOT_SUPPLIED",
            }
        )
    if len(ordered) >= 2:
        features["delta_oi_1"] = ordered[-1].oi - ordered[-2].oi
    else:
        features["delta_oi_1"] = None
        features["first_observation"] = True
    return PersistenceResult(
        score=winner[0] if winner else None,
        winning_window=winner[1] if winner else None,
        state=winner[2] if winner else None,
        history_confidence=history_confidence(len(ordered)),
        observation_count=len(ordered),
        features=features,
    )

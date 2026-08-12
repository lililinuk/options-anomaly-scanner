from __future__ import annotations

from collections.abc import Iterable
from typing import Protocol, TypeVar

from app.models.signals import DteBucket
from app.scanner.config import LIMITS
from app.scanner.scoring import discovery_eligible


class ScoredExpiry(Protocol):
    ticker: str
    bucket_at_detection: str
    preliminary_score: object


class DualDiscoveryExpiry(Protocol):
    ticker: str
    bucket_at_detection: str
    same_day_activity_score: object | None
    persistent_positioning_score: object | None
    discovery_score: object | None
    structural_cold_start_eligible: bool


T = TypeVar("T", bound=ScoredExpiry)


def select_deep_expiries(rows: Iterable[T]) -> list[T]:
    expiries = list(rows)
    ticker_scores: dict[str, float] = {}
    for row in expiries:
        if row.bucket_at_detection == DteBucket.LONG.value:
            continue
        ticker_scores[row.ticker] = max(
            ticker_scores.get(row.ticker, 0), float(row.preliminary_score)
        )
    tickers = [
        ticker
        for ticker, score in sorted(ticker_scores.items(), key=lambda item: item[1], reverse=True)
        if score >= 40
    ][: LIMITS.max_deep_tickers]
    selected: list[T] = []
    for ticker in tickers:
        for bucket in (DteBucket.VERY_SHORT, DteBucket.SHORT, DteBucket.MEDIUM):
            choices = [
                row
                for row in expiries
                if row.ticker == ticker
                and row.bucket_at_detection == bucket.value
                and float(row.preliminary_score) >= 40
            ]
            if choices:
                selected.append(max(choices, key=lambda row: float(row.preliminary_score)))
    return selected


U = TypeVar("U", bound=DualDiscoveryExpiry)


def select_dual_discovery(rows: Iterable[U]) -> list[U]:
    eligible = [
        row
        for row in rows
        if row.bucket_at_detection != DteBucket.LONG.value
        and discovery_eligible(
            float(row.same_day_activity_score)
            if row.same_day_activity_score is not None
            else None,
            float(row.persistent_positioning_score)
            if row.persistent_positioning_score is not None
            else None,
            row.structural_cold_start_eligible,
        )
    ]
    normally_ranked = [row for row in eligible if row.discovery_score is not None]
    strengths = {
        ticker: max(
            float(row.discovery_score) for row in normally_ranked if row.ticker == ticker
        )
        for ticker in {row.ticker for row in normally_ranked}
    }
    tickers = [
        ticker
        for ticker, _score in sorted(
            strengths.items(), key=lambda item: item[1], reverse=True
        )[: LIMITS.max_deep_tickers]
    ]
    if len(tickers) < LIMITS.max_deep_tickers:
        cold_only = sorted(
            {
                row.ticker
                for row in eligible
                if row.discovery_score is None and row.ticker not in tickers
            }
        )
        tickers.extend(cold_only[: LIMITS.max_deep_tickers - len(tickers)])
    selected: list[U] = []
    for ticker in tickers:
        for bucket in (DteBucket.VERY_SHORT, DteBucket.SHORT, DteBucket.MEDIUM):
            choices = [
                row
                for row in eligible
                if row.ticker == ticker
                and row.bucket_at_detection == bucket.value
                and row.discovery_score is not None
            ]
            if choices:
                selected.append(max(choices, key=lambda row: float(row.discovery_score)))
                continue
            cold_choices = [
                row
                for row in eligible
                if row.ticker == ticker
                and row.bucket_at_detection == bucket.value
                and row.discovery_score is None
                and row.structural_cold_start_eligible
            ]
            if cold_choices:
                selected.append(cold_choices[0])
    return selected

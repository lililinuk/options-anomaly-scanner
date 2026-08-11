from __future__ import annotations

from collections.abc import Iterable
from typing import Protocol, TypeVar

from app.models.signals import DteBucket
from app.scanner.config import LIMITS


class ScoredExpiry(Protocol):
    ticker: str
    bucket_at_detection: str
    preliminary_score: object


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

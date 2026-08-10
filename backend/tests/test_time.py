from datetime import datetime, timedelta, timezone

import pytest

from app.core.time import UTC, ensure_utc, market_date, market_datetime


def test_market_date_uses_new_york_not_host_timezone() -> None:
    instant = datetime(2026, 8, 10, 2, 30, tzinfo=timezone.utc)
    assert market_date(instant).isoformat() == "2026-08-09"
    assert market_datetime(instant).tzinfo is not None


def test_ensure_utc_converts_aware_datetime() -> None:
    taipei = timezone(timedelta(hours=8))
    converted = ensure_utc(datetime(2026, 8, 10, 8, 0, tzinfo=taipei))
    assert converted == datetime(2026, 8, 10, 0, 0, tzinfo=UTC)


def test_naive_datetime_is_rejected() -> None:
    with pytest.raises(ValueError, match="timezone-aware"):
        ensure_utc(datetime(2026, 8, 10, 0, 0))


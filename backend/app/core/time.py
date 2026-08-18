from datetime import date, datetime, timezone
from zoneinfo import ZoneInfo

import exchange_calendars as xcals
import pandas as pd

MARKET_TIMEZONE = ZoneInfo("America/New_York")
UTC = timezone.utc


def utc_now() -> datetime:
    return datetime.now(UTC)


def ensure_utc(value: datetime) -> datetime:
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError("A timezone-aware datetime is required")
    return value.astimezone(UTC)


def market_datetime(value: datetime) -> datetime:
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError("A timezone-aware datetime is required")
    return value.astimezone(MARKET_TIMEZONE)


def market_date(value: datetime) -> date:
    return market_datetime(value).date()


def is_xnys_session(value: date) -> bool:
    """Return whether ``value`` is an authoritative NYSE trading session label."""

    calendar = xcals.get_calendar("XNYS")
    return bool(calendar.is_session(pd.Timestamp(value.isoformat())))


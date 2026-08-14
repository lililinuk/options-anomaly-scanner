from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, time
from zoneinfo import ZoneInfo

import exchange_calendars as xcals
import pandas as pd

from app.core.time import ensure_utc


@dataclass(frozen=True)
class CaptureSessionPlan:
    market_date: date
    intended_at: datetime
    session_close: datetime | None
    should_capture: bool
    status: str


def dealer_capture_session_plan(
    now: datetime,
    *,
    timezone_name: str,
    local_time: str,
) -> CaptureSessionPlan:
    """Resolve the configured slot against the authoritative XNYS session calendar."""

    aware_now = ensure_utc(now)
    timezone = ZoneInfo(timezone_name)
    market_day = aware_now.astimezone(timezone).date()
    hour, minute = (int(part) for part in local_time.split(":", 1))
    intended = datetime.combine(market_day, time(hour, minute), tzinfo=timezone)
    calendar = xcals.get_calendar("XNYS")
    session_label = pd.Timestamp(market_day.isoformat())
    if not calendar.is_session(session_label):
        return CaptureSessionPlan(
            market_day,
            intended,
            None,
            False,
            "SKIPPED_NON_TRADING_SESSION",
        )
    close = calendar.session_close(session_label).to_pydatetime().astimezone(timezone)
    if intended > close:
        return CaptureSessionPlan(
            market_day,
            intended,
            close,
            False,
            "SKIPPED_TARGET_AFTER_EARLY_CLOSE",
        )
    return CaptureSessionPlan(market_day, intended, close, True, "READY")

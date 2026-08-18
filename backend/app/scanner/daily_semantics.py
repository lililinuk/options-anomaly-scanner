from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from enum import Enum
from zoneinfo import ZoneInfo

import exchange_calendars as xcals
import pandas as pd

from app.core.time import ensure_utc

NEW_YORK = ZoneInfo("America/New_York")


class DailyPipelineMode(str, Enum):
    ALL = "all"
    ACTIVITY = "activity"
    RADAR_OI = "radar-oi"


class ZeroDteSnapshotKind(str, Enum):
    PROVISIONAL_INTRADAY = "PROVISIONAL_INTRADAY"
    CANONICAL_SESSION_COMPLETE = "CANONICAL_SESSION_COMPLETE"
    LEGACY_OR_AMBIGUOUS = "LEGACY_OR_AMBIGUOUS"


def zero_dte_snapshot_kind(snapshot: object) -> ZeroDteSnapshotKind:
    """Classify accepted pre-Stage-4A rows without mutating or guessing history."""

    value = getattr(snapshot, "snapshot_kind", None)
    if value is None:
        return ZeroDteSnapshotKind.LEGACY_OR_AMBIGUOUS
    return ZeroDteSnapshotKind(value)


@dataclass(frozen=True)
class ActivitySessionPlan:
    market_date: date
    session_close_at: datetime | None
    should_collect: bool
    status: str


def activity_session_plan(now: datetime) -> ActivitySessionPlan:
    """Authorize canonical Activity capture only after the actual XNYS close."""

    aware_now = ensure_utc(now)
    market_day = aware_now.astimezone(NEW_YORK).date()
    calendar = xcals.get_calendar("XNYS")
    session_label = pd.Timestamp(market_day.isoformat())
    if not calendar.is_session(session_label):
        return ActivitySessionPlan(
            market_date=market_day,
            session_close_at=None,
            should_collect=False,
            status="SKIPPED_NON_TRADING_SESSION",
        )
    session_close = ensure_utc(calendar.session_close(session_label).to_pydatetime())
    if aware_now < session_close:
        return ActivitySessionPlan(
            market_date=market_day,
            session_close_at=session_close,
            should_collect=False,
            status="SKIPPED_BEFORE_SESSION_CLOSE",
        )
    return ActivitySessionPlan(
        market_date=market_day,
        session_close_at=session_close,
        should_collect=True,
        status="READY",
    )

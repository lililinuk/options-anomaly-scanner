from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, time
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
class RadarOiSchedulePlan:
    market_date: date
    should_collect: bool
    status: str


def radar_oi_schedule_plan(now: datetime) -> RadarOiSchedulePlan:
    """Keep scheduled Radar/OI inside the evidence-backed XNYS morning window."""

    aware_now = ensure_utc(now)
    local_now = aware_now.astimezone(NEW_YORK)
    market_day = local_now.date()
    calendar = xcals.get_calendar("XNYS")
    session_label = pd.Timestamp(market_day.isoformat())
    if not calendar.is_session(session_label):
        return RadarOiSchedulePlan(market_day, False, "SKIPPED_NON_TRADING_SESSION")
    if local_now.time() < time(6, 0):
        return RadarOiSchedulePlan(market_day, False, "SKIPPED_BEFORE_SOURCE_READY")
    if local_now.time() > time(8, 0):
        return RadarOiSchedulePlan(market_day, False, "SKIPPED_AFTER_SAFE_WINDOW")
    return RadarOiSchedulePlan(market_day, True, "READY")


@dataclass(frozen=True)
class ActivitySessionPlan:
    market_date: date
    session_close_at: datetime | None
    should_collect: bool
    status: str


def activity_session_plan(
    now: datetime,
    *,
    intended_market_date: date | None = None,
) -> ActivitySessionPlan:
    """Authorize Activity for the intended XNYS session only after its actual close."""

    aware_now = ensure_utc(now)
    market_day = intended_market_date or aware_now.astimezone(NEW_YORK).date()
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

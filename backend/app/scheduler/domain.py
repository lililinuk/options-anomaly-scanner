from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass
from datetime import date, datetime, timezone
from enum import Enum
from zoneinfo import ZoneInfo

from app.core.time import ensure_utc

MARKET_TIMEZONE = "America/New_York"
TRIGGER_TRANSPORT = "GOOGLE_CLOUD_SCHEDULER"
NEW_YORK = ZoneInfo(MARKET_TIMEZONE)
_FRACTION = re.compile(r"^(?P<prefix>.+\.)(?P<fraction>\d+)(?P<suffix>Z|[+-]\d\d:\d\d)$")


class CanonicalSlotType(str, Enum):
    RADAR_OI = "RADAR_OI"
    DEALER_GEX = "DEALER_GEX"
    ACTIVITY_VNEXT = "ACTIVITY_VNEXT"


EXPECTED_LOCAL_TIMES = {
    CanonicalSlotType.RADAR_OI: (6, 30),
    CanonicalSlotType.DEALER_GEX: (15, 30),
    CanonicalSlotType.ACTIVITY_VNEXT: (16, 30),
}


@dataclass(frozen=True)
class CanonicalSlotIdentity:
    slot_type: CanonicalSlotType
    intended_at: datetime
    intended_market_date: date
    market_timezone: str
    canonical_key: str

    @property
    def intended_at_et(self) -> datetime:
        return self.intended_at.astimezone(NEW_YORK)


def parse_scheduler_timestamp(value: str) -> datetime:
    """Parse Cloud Scheduler RFC3339 metadata, including nanosecond precision."""

    normalized = value.strip()
    match = _FRACTION.match(normalized)
    if match:
        fraction = match.group("fraction")[:6].ljust(6, "0")
        normalized = f"{match.group('prefix')}{fraction}{match.group('suffix')}"
    if normalized.endswith("Z"):
        normalized = normalized[:-1] + "+00:00"
    try:
        parsed = datetime.fromisoformat(normalized)
    except ValueError as error:
        raise ValueError("INVALID_CLOUD_SCHEDULER_SCHEDULE_TIME") from error
    if parsed.tzinfo is None:
        raise ValueError("CLOUD_SCHEDULER_SCHEDULE_TIME_MUST_BE_AWARE")
    return ensure_utc(parsed)


def canonical_slot_identity(
    slot_type: CanonicalSlotType,
    schedule_time: str,
) -> CanonicalSlotIdentity:
    intended_at = parse_scheduler_timestamp(schedule_time)
    intended_et = intended_at.astimezone(NEW_YORK)
    expected_hour, expected_minute = EXPECTED_LOCAL_TIMES[slot_type]
    if (intended_et.hour, intended_et.minute) != (expected_hour, expected_minute):
        raise ValueError("SCHEDULE_TIME_DOES_NOT_MATCH_SLOT")
    intended_at = intended_at.replace(second=0, microsecond=0)
    intended_et = intended_at.astimezone(NEW_YORK)
    semantic = f"{slot_type.value}|{intended_at.isoformat()}"
    digest = hashlib.sha256(semantic.encode()).hexdigest()[:24]
    key = f"{slot_type.value}:{intended_at.strftime('%Y%m%dT%H%M%SZ')}:{digest}"
    return CanonicalSlotIdentity(
        slot_type=slot_type,
        intended_at=intended_at,
        intended_market_date=intended_et.date(),
        market_timezone=MARKET_TIMEZONE,
        canonical_key=key,
    )


def scheduler_job_id(job_name: str) -> str:
    value = job_name.strip().rstrip("/").rsplit("/", 1)[-1]
    if not value:
        raise ValueError("MISSING_CLOUD_SCHEDULER_JOB_NAME")
    return value


def validate_scheduler_headers(
    *,
    scheduler_marker: str | None,
    scheduler_job_name: str | None,
    expected_job_id: str,
) -> str:
    if scheduler_marker != "true":
        raise ValueError("MISSING_CLOUD_SCHEDULER_MARKER")
    if scheduler_job_name is None:
        raise ValueError("MISSING_CLOUD_SCHEDULER_JOB_NAME")
    if scheduler_job_id(scheduler_job_name) != expected_job_id:
        raise ValueError("UNEXPECTED_CLOUD_SCHEDULER_JOB")
    return scheduler_job_name


def execution_delay_seconds(identity: CanonicalSlotIdentity, actual_started_at: datetime) -> int:
    actual = ensure_utc(actual_started_at)
    return int((actual - identity.intended_at).total_seconds())


def actual_market_date(actual_started_at: datetime) -> date:
    return ensure_utc(actual_started_at).astimezone(NEW_YORK).date()


UTC = timezone.utc

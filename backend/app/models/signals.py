from dataclasses import dataclass
from datetime import date
from enum import Enum


class DteBucket(str, Enum):
    VERY_SHORT = "VERY_SHORT"
    SHORT = "SHORT"
    MEDIUM = "MEDIUM"
    LONG = "LONG"


@dataclass(frozen=True)
class DteBucketRule:
    bucket: DteBucket
    minimum: int
    maximum: int


DEFAULT_DTE_BUCKET_RULES = (
    DteBucketRule(DteBucket.VERY_SHORT, 0, 7),
    DteBucketRule(DteBucket.SHORT, 8, 30),
    DteBucketRule(DteBucket.MEDIUM, 31, 90),
    DteBucketRule(DteBucket.LONG, 91, 180),
)


def calendar_dte(expiration: date, market_day: date) -> int:
    """Calendar DTE; intentionally unrelated to signal age."""

    return (expiration - market_day).days


def bucket_for_dte(
    dte: int, rules: tuple[DteBucketRule, ...] = DEFAULT_DTE_BUCKET_RULES
) -> DteBucket | None:
    for rule in rules:
        if rule.minimum <= dte <= rule.maximum:
            return rule.bucket
    return None


class PositionLifecycleState(str, Enum):
    DETECTED = "DETECTED"
    OI_PENDING = "OI_PENDING"
    BUILD_CONFIRMED = "BUILD_CONFIRMED"
    ACTIVE = "ACTIVE"
    REINFORCED = "REINFORCED"
    PARTIAL_UNWIND = "PARTIAL_UNWIND"
    MAJOR_UNWIND = "MAJOR_UNWIND"
    POSSIBLE_ROLL = "POSSIBLE_ROLL"
    CLOSED = "CLOSED"
    EXPIRED = "EXPIRED"


@dataclass(frozen=True)
class DetectionTenor:
    """Immutable snapshot fields stored when a future signal is detected."""

    dte_at_detection: int
    bucket_at_detection: DteBucket | None


@dataclass(frozen=True)
class CurrentTenor:
    """Dynamic presentation fields calculated independently of detection age."""

    current_dte: int
    current_bucket: DteBucket | None

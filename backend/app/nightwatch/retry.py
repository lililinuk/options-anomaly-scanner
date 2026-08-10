from datetime import datetime, timezone
from email.utils import parsedate_to_datetime

RETRYABLE_STATUS_CODES = frozenset({408, 425, 429, 500, 502, 503, 504})


def is_retryable_status(status_code: int) -> bool:
    return status_code in RETRYABLE_STATUS_CODES


def retry_after_seconds(value: str | None, now: datetime | None = None) -> float | None:
    if not value:
        return None
    try:
        return max(0.0, float(value.strip()))
    except ValueError:
        pass

    try:
        retry_at = parsedate_to_datetime(value)
    except (TypeError, ValueError, OverflowError):
        return None
    if retry_at.tzinfo is None:
        retry_at = retry_at.replace(tzinfo=timezone.utc)
    current = now or datetime.now(timezone.utc)
    return max(0.0, (retry_at - current).total_seconds())


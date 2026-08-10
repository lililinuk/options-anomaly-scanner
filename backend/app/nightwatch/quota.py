from collections.abc import Mapping
from datetime import datetime

from app.nightwatch.models import QuotaMetadata
from app.nightwatch.retry import retry_after_seconds


def _integer(headers: Mapping[str, str], key: str) -> int | None:
    value = headers.get(key)
    if value is None:
        return None
    try:
        return int(value)
    except ValueError:
        return None


def _datetime(headers: Mapping[str, str], key: str) -> datetime | None:
    value = headers.get(key)
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


def parse_quota_headers(headers: Mapping[str, str]) -> QuotaMetadata:
    normalized = {key.lower(): value for key, value in headers.items()}
    return QuotaMetadata(
        quota_limit=_integer(normalized, "x-quota-limit"),
        quota_remaining=_integer(normalized, "x-quota-remaining"),
        quota_reset_at=_datetime(normalized, "x-quota-reset-at"),
        rate_limit=_integer(normalized, "x-ratelimit-limit"),
        rate_limit_remaining=_integer(normalized, "x-ratelimit-remaining"),
        rate_limit_reset_epoch=_integer(normalized, "x-ratelimit-reset"),
        retry_after_seconds=retry_after_seconds(normalized.get("retry-after")),
    )


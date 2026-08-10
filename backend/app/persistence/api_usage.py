from datetime import date
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import ApiUsageAudit
from app.nightwatch.models import ApiUsageEvent


def persist_api_usage(session: Session, event: ApiUsageEvent) -> ApiUsageAudit:
    existing = session.scalar(
        select(ApiUsageAudit).where(ApiUsageAudit.request_id == event.request_id)
    )
    if existing is not None:
        return existing

    row = ApiUsageAudit(
        endpoint=event.endpoint,
        command=event.command,
        requested_at=event.requested_at,
        ticker=event.ticker,
        expiration=date.fromisoformat(event.expiration) if event.expiration else None,
        http_status=event.http_status,
        consumed_quota=event.consumed_quota,
        quota_limit=event.quota_limit,
        quota_remaining=event.quota_remaining,
        rate_limit=event.rate_limit,
        rate_limit_remaining=event.rate_limit_remaining,
        request_id=event.request_id,
        vendor_request_id=event.vendor_request_id,
        latency_ms=Decimal(str(round(event.latency_ms, 3))),
        attempt_count=event.attempt_count,
        retry_count=event.retry_count,
        error_code=event.error_code,
    )
    session.add(row)
    session.flush()
    return row

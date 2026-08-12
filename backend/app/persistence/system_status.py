from dataclasses import dataclass
from datetime import datetime

from sqlalchemy import desc, select, text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.db.models import ApiUsageAudit, MetadataRefresh


@dataclass(frozen=True)
class PersistedSystemStatus:
    database_status: str
    nightwatch_status: str
    latest_capability_refresh_at: datetime | None = None
    quota_limit: int | None = None
    quota_remaining: int | None = None
    rate_limit: int | None = None
    rate_limit_remaining: int | None = None
    latest_request_status: int | None = None


def load_system_status(session: Session) -> PersistedSystemStatus:
    """Read only application-owned state; never contacts Nightwatch."""

    try:
        session.execute(text("SELECT 1"))
        latest_refresh = session.scalar(
            select(MetadataRefresh).order_by(desc(MetadataRefresh.observed_at)).limit(1)
        )
        latest_usage = session.scalar(
            select(ApiUsageAudit)
            .order_by(desc(ApiUsageAudit.requested_at))
            .limit(1)
        )
    except SQLAlchemyError:
        return PersistedSystemStatus(
            database_status="unavailable",
            nightwatch_status="unknown",
        )

    request_status = latest_usage.http_status if latest_usage else None
    if request_status is None:
        nightwatch_status = "not_checked"
    elif 200 <= request_status < 300:
        nightwatch_status = "connected"
    else:
        nightwatch_status = "error"
    return PersistedSystemStatus(
        database_status="connected",
        nightwatch_status=nightwatch_status,
        latest_capability_refresh_at=(latest_refresh.observed_at if latest_refresh else None),
        quota_limit=latest_usage.quota_limit if latest_usage else None,
        quota_remaining=latest_usage.quota_remaining if latest_usage else None,
        rate_limit=latest_usage.rate_limit if latest_usage else None,
        rate_limit_remaining=(latest_usage.rate_limit_remaining if latest_usage else None),
        latest_request_status=request_status,
    )

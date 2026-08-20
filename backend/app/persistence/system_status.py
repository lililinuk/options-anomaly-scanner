from dataclasses import dataclass
from datetime import datetime

from sqlalchemy import desc, select, text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.db.models import (
    ApiUsageAudit,
    DailyCollectionRun,
    DealerGexSnapshot,
    MetadataRefresh,
    ScanRun,
)


@dataclass(frozen=True)
class PersistedSystemStatus:
    database_status: str
    nightwatch_status: str
    latest_scan_status: str | None = None
    latest_scan_started_at: datetime | None = None
    latest_scan_completed_at: datetime | None = None
    latest_scan_consumed_quota_units: int | None = None
    latest_capability_refresh_at: datetime | None = None
    quota_limit: int | None = None
    quota_remaining: int | None = None
    rate_limit: int | None = None
    rate_limit_remaining: int | None = None
    latest_request_status: int | None = None
    daily_collection_last_success_at: datetime | None = None
    daily_collection_market_date: str | None = None
    dealer_archive_last_vendor_observed_at: datetime | None = None
    dealer_archive_last_captured_at: datetime | None = None


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
        latest_scan = session.scalar(
            select(ScanRun).order_by(desc(ScanRun.started_at)).limit(1)
        )
        latest_daily_success = session.scalar(
            select(DailyCollectionRun)
            .where(DailyCollectionRun.status == "COMPLETE")
            .order_by(desc(DailyCollectionRun.completed_at))
            .limit(1)
        )
        latest_dealer_observation = session.scalar(
            select(DealerGexSnapshot)
            .where(
                DealerGexSnapshot.is_analytical_observation.is_(True),
                DealerGexSnapshot.vendor_observed_at.is_not(None),
            )
            .order_by(desc(DealerGexSnapshot.vendor_observed_at))
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
        latest_scan_status=latest_scan.status if latest_scan else None,
        latest_scan_started_at=latest_scan.started_at if latest_scan else None,
        latest_scan_completed_at=latest_scan.completed_at if latest_scan else None,
        latest_scan_consumed_quota_units=(
            latest_scan.consumed_quota_units if latest_scan else None
        ),
        latest_capability_refresh_at=(latest_refresh.observed_at if latest_refresh else None),
        quota_limit=latest_usage.quota_limit if latest_usage else None,
        quota_remaining=latest_usage.quota_remaining if latest_usage else None,
        rate_limit=latest_usage.rate_limit if latest_usage else None,
        rate_limit_remaining=(latest_usage.rate_limit_remaining if latest_usage else None),
        latest_request_status=request_status,
        daily_collection_last_success_at=(
            latest_daily_success.completed_at if latest_daily_success else None
        ),
        daily_collection_market_date=(
            latest_daily_success.ny_market_date.isoformat()
            if latest_daily_success
            else None
        ),
        dealer_archive_last_vendor_observed_at=(
            latest_dealer_observation.vendor_observed_at
            if latest_dealer_observation
            else None
        ),
        dealer_archive_last_captured_at=(
            latest_dealer_observation.captured_at
            if latest_dealer_observation
            else None
        ),
    )

from datetime import datetime

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.db.session import get_db_session
from app.persistence.system_status import load_system_status

router = APIRouter()
database_session = Depends(get_db_session)


class SystemStatus(BaseModel):
    scanner_status: str = "not_scheduled"
    latest_scan_at: datetime | None = None
    latest_scan_status: str | None = None
    latest_scan_started_at: datetime | None = None
    latest_scan_completed_at: datetime | None = None
    latest_scan_consumed_quota_units: int | None = None
    nightwatch_status: str = "not_checked"
    latest_capability_refresh_at: datetime | None = None
    quota_limit: int | None = None
    quota_remaining: int | None = None
    rate_limit: int | None = None
    rate_limit_remaining: int | None = None
    latest_request_status: int | None = None
    database_status: str = "unknown"
    scheduling_enabled: bool = False
    daily_collection_last_success_at: datetime | None = None
    daily_collection_market_date: str | None = None
    dealer_archive_last_vendor_observed_at: datetime | None = None
    dealer_archive_last_captured_at: datetime | None = None


@router.get("/status", response_model=SystemStatus)
def status(session: Session = database_session) -> SystemStatus:
    """No live vendor call: reports only state owned by this application."""

    persisted = load_system_status(session)
    return SystemStatus(
        scanner_status=persisted.latest_scan_status or "not_run",
        latest_scan_at=(
            persisted.latest_scan_completed_at or persisted.latest_scan_started_at
        ),
        latest_scan_status=persisted.latest_scan_status,
        latest_scan_started_at=persisted.latest_scan_started_at,
        latest_scan_completed_at=persisted.latest_scan_completed_at,
        latest_scan_consumed_quota_units=(
            persisted.latest_scan_consumed_quota_units
        ),
        nightwatch_status=persisted.nightwatch_status,
        latest_capability_refresh_at=persisted.latest_capability_refresh_at,
        quota_limit=persisted.quota_limit,
        quota_remaining=persisted.quota_remaining,
        rate_limit=persisted.rate_limit,
        rate_limit_remaining=persisted.rate_limit_remaining,
        latest_request_status=persisted.latest_request_status,
        database_status=persisted.database_status,
        daily_collection_last_success_at=(
            persisted.daily_collection_last_success_at
        ),
        daily_collection_market_date=persisted.daily_collection_market_date,
        dealer_archive_last_vendor_observed_at=(
            persisted.dealer_archive_last_vendor_observed_at
        ),
        dealer_archive_last_captured_at=(
            persisted.dealer_archive_last_captured_at
        ),
    )

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
    nightwatch_status: str = "not_checked"
    latest_capability_refresh_at: datetime | None = None
    quota_limit: int | None = None
    quota_remaining: int | None = None
    rate_limit: int | None = None
    rate_limit_remaining: int | None = None
    latest_request_status: int | None = None
    database_status: str = "unknown"
    scheduling_enabled: bool = False


@router.get("/status", response_model=SystemStatus)
def status(session: Session = database_session) -> SystemStatus:
    """No live vendor call: reports only state owned by this application."""

    persisted = load_system_status(session)
    return SystemStatus(
        nightwatch_status=persisted.nightwatch_status,
        latest_capability_refresh_at=persisted.latest_capability_refresh_at,
        quota_limit=persisted.quota_limit,
        quota_remaining=persisted.quota_remaining,
        rate_limit=persisted.rate_limit,
        rate_limit_remaining=persisted.rate_limit_remaining,
        latest_request_status=persisted.latest_request_status,
        database_status=persisted.database_status,
    )

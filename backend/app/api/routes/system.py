from datetime import datetime

from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter()


class SystemStatus(BaseModel):
    scanner_status: str = "not_scheduled"
    latest_scan_at: datetime | None = None
    nightwatch_status: str = "not_checked"
    quota_remaining: int | None = None
    scheduling_enabled: bool = False


@router.get("/status", response_model=SystemStatus)
def status() -> SystemStatus:
    """No live vendor call: reports only state owned by this application."""

    return SystemStatus()


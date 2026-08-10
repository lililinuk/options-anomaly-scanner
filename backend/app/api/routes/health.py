from datetime import datetime

from fastapi import APIRouter
from pydantic import BaseModel

from app.core.time import utc_now

router = APIRouter()


class HealthPayload(BaseModel):
    status: str
    service: str
    checked_at: datetime


@router.get("/health", response_model=HealthPayload)
def health() -> HealthPayload:
    return HealthPayload(status="ok", service="options-anomaly-scanner-api", checked_at=utc_now())


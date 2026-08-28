from __future__ import annotations

from fastapi import APIRouter, Header, HTTPException
from fastapi.responses import JSONResponse
from sqlalchemy.exc import SQLAlchemyError

from app.config import get_settings
from app.core.time import utc_now
from app.db.session import get_session_factory
from app.scheduler.domain import (
    CanonicalSlotType,
    canonical_slot_identity,
    validate_scheduler_headers,
)
from app.scheduler.service import CanonicalSchedulerOrchestrator

router = APIRouter()


def _expected_job_id(slot_type: CanonicalSlotType) -> str:
    settings = get_settings()
    return {
        CanonicalSlotType.RADAR_OI: settings.gcp_scheduler_job_radar_oi,
        CanonicalSlotType.DEALER_GEX: settings.gcp_scheduler_job_dealer_gex,
        CanonicalSlotType.ACTIVITY_VNEXT: settings.gcp_scheduler_job_activity_vnext,
    }[slot_type]


@router.api_route("/health", methods=["GET", "POST"])
def health() -> dict[str, str]:
    return {"status": "ok", "service": "canonical-production-orchestrator"}


@router.post("/canonical-slots/{slot_type}")
async def invoke_canonical_slot(
    slot_type: CanonicalSlotType,
    x_cloudscheduler: str | None = Header(default=None),
    x_cloudscheduler_jobname: str | None = Header(default=None),
    x_cloudscheduler_scheduletime: str | None = Header(default=None),
) -> JSONResponse:
    if x_cloudscheduler_scheduletime is None:
        raise HTTPException(status_code=400, detail="MISSING_CLOUD_SCHEDULER_SCHEDULE_TIME")
    try:
        scheduler_job_name = validate_scheduler_headers(
            scheduler_marker=x_cloudscheduler,
            scheduler_job_name=x_cloudscheduler_jobname,
            expected_job_id=_expected_job_id(slot_type),
        )
        identity = canonical_slot_identity(slot_type, x_cloudscheduler_scheduletime)
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error

    settings = get_settings()
    try:
        with get_session_factory()() as session:
            result = await CanonicalSchedulerOrchestrator(session, settings).execute(
                identity=identity,
                actual_started_at=utc_now(),
                scheduler_job_name=scheduler_job_name,
            )
    except SQLAlchemyError as error:
        raise HTTPException(status_code=503, detail="PERSISTENCE_UNAVAILABLE") from error
    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=f"CANONICAL_SLOT_FAILED:{type(error).__name__}",
        ) from error
    return JSONResponse(result.to_dict())

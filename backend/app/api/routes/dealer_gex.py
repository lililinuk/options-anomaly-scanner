from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends
from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from app.db.models import DealerGexArchiveRun
from app.db.session import get_db_session
from app.dealer_archive.repository import dealer_gex_history_coverage
from app.scanner.config import UNIVERSE

router = APIRouter()
database_session = Depends(get_db_session)


@router.get("/history")
def dealer_gex_history(session: Session = database_session) -> dict[str, Any]:
    """Return persisted archive health only; this route never contacts Nightwatch."""

    latest = session.scalar(
        select(DealerGexArchiveRun).order_by(desc(DealerGexArchiveRun.started_at)).limit(1)
    )
    return {
        "archive": (
            {
                "archive_run_id": str(latest.id),
                "status": latest.status,
                "started_at": latest.started_at.isoformat(),
                "completed_at": latest.completed_at.isoformat()
                if latest.completed_at
                else None,
                "market_date": latest.ny_market_date.isoformat()
                if latest.ny_market_date
                else None,
                "intended_capture_slot": latest.intended_capture_slot,
                "market_timezone": latest.market_timezone,
                "tickers_attempted": latest.tickers_attempted,
                "tickers_succeeded": latest.tickers_succeeded,
                "tickers_failed": latest.tickers_failed,
                "network_attempts": latest.network_attempts,
                "consumed_quota_units": latest.consumed_quota_units,
                "specification_version": latest.specification_version,
            }
            if latest
            else None
        ),
        "history_coverage": dealer_gex_history_coverage(session, tuple(UNIVERSE)),
        "semantics": {
            "unavailable_is_zero": False,
            "distinct_observations_use_vendor_time": True,
            "analysis_labels_computed": False,
            "actionability_computed": False,
        },
    }

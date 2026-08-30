from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.dashboard.trading import trading_dashboard_read_model
from app.db.session import get_db_session

router = APIRouter()
database_session = Depends(get_db_session)


@router.get("")
def read_trading_dashboard(session: Session = database_session) -> dict[str, Any]:
    """Read persisted Trading context only; this endpoint never contacts Nightwatch."""

    return trading_dashboard_read_model(session)

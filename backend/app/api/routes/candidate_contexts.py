from __future__ import annotations

import uuid
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.config import get_settings
from app.confirmation.vnext import (
    Stage6BalancedContextService,
    context_history_public,
    context_public,
    load_context_history,
)
from app.db.session import get_db_session
from app.nightwatch.client import NightwatchClient

router = APIRouter()
database_session = Depends(get_db_session)


@router.get("/{candidate_id}/context")
def read_candidate_context(
    candidate_id: uuid.UUID,
    session: Session = database_session,
) -> dict[str, Any]:
    """Read persisted Stage 6 history without creating rows or calling a vendor."""

    candidate, contexts = load_context_history(session, candidate_id)
    if candidate is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="ProductCandidate not found",
        )
    return context_history_public(candidate, contexts)


@router.post("/{candidate_id}/context/baseline")
def create_candidate_context_baseline(
    candidate_id: uuid.UUID,
    session: Session = database_session,
) -> dict[str, Any]:
    """Freeze already-known/archive evidence; this path performs no vendor request."""

    service = Stage6BalancedContextService(session)
    try:
        context = service.create_baseline(candidate_id)
        session.commit()
    except LookupError as error:
        session.rollback()
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(error),
        ) from error
    except ValueError as error:
        session.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(error),
        ) from error
    return context_public(context)


@router.post("/{candidate_id}/context/refresh")
async def refresh_candidate_context(
    candidate_id: uuid.UUID,
    session: Session = database_session,
) -> dict[str, Any]:
    """Run the explicit four-source ticker refresh; no per-anomaly vendor calls."""

    settings = get_settings()
    try:
        async with NightwatchClient(
            base_url=str(settings.nightwatch_base_url),
            api_key=settings.nightwatch_api_key,
            timeout_seconds=settings.nightwatch_timeout_seconds,
            max_retries=0,
            max_concurrency=min(settings.nightwatch_max_concurrency, 4),
        ) as client:
            context = await Stage6BalancedContextService(
                session,
                client,
            ).refresh(candidate_id)
        session.commit()
    except LookupError as error:
        session.rollback()
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(error),
        ) from error
    except ValueError as error:
        session.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(error),
        ) from error
    return context_public(context)

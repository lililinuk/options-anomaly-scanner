from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.db.models import CanonicalSchedulerAttempt, CanonicalSchedulerSlot
from app.scheduler.domain import TRIGGER_TRANSPORT, CanonicalSlotIdentity


@dataclass(frozen=True)
class SlotClaim:
    slot: CanonicalSchedulerSlot
    attempt: CanonicalSchedulerAttempt
    created: bool


def claim_canonical_slot(
    session: Session,
    *,
    identity: CanonicalSlotIdentity,
    actual_started_at: datetime,
    scheduler_job_name: str,
) -> SlotClaim:
    slot = CanonicalSchedulerSlot(
        slot_type=identity.slot_type.value,
        intended_at=identity.intended_at,
        intended_market_date=identity.intended_market_date,
        market_timezone=identity.market_timezone,
        actual_started_at=actual_started_at,
        trigger_transport=TRIGGER_TRANSPORT,
        canonical_key=identity.canonical_key,
        scheduler_job_name=scheduler_job_name,
        status="CLAIMED",
        paid_work_attempted=False,
        network_attempts=0,
        consumed_units=0,
        product_candidate_count=0,
        baseline_count=0,
        result={},
        created_at=actual_started_at,
    )
    try:
        session.add(slot)
        session.flush()
        attempt = CanonicalSchedulerAttempt(
            slot_id=slot.id,
            scheduler_job_name=scheduler_job_name,
            received_at=actual_started_at,
            disposition="OWNER",
        )
        session.add(attempt)
        session.commit()
        return SlotClaim(slot, attempt, True)
    except IntegrityError:
        session.rollback()

    existing = session.scalar(
        select(CanonicalSchedulerSlot).where(
            CanonicalSchedulerSlot.slot_type == identity.slot_type.value,
            CanonicalSchedulerSlot.intended_at == identity.intended_at,
        )
    )
    if existing is None:
        raise RuntimeError("CANONICAL_SLOT_CONFLICT_WITHOUT_VISIBLE_OWNER")
    duplicate = CanonicalSchedulerAttempt(
        slot_id=existing.id,
        scheduler_job_name=scheduler_job_name,
        received_at=actual_started_at,
        disposition="DUPLICATE_DELIVERY_REUSED",
        completed_at=actual_started_at,
        result_status=existing.status,
    )
    session.add(duplicate)
    session.commit()
    return SlotClaim(existing, duplicate, False)


def finish_attempt(
    session: Session,
    attempt: CanonicalSchedulerAttempt,
    *,
    completed_at: datetime,
    disposition: str,
    result_status: str,
) -> None:
    attempt.disposition = disposition
    attempt.completed_at = completed_at
    attempt.result_status = result_status
    session.commit()

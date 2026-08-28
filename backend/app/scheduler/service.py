from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any

from sqlalchemy.orm import Session

from app.config.settings import Settings
from app.core.time import ensure_utc, utc_now
from app.db.models import CanonicalSchedulerSlot
from app.dealer_archive.service import DealerGexArchiver
from app.nightwatch.client import NightwatchClient
from app.scanner.daily import DailyDataPipeline
from app.scanner.daily_observation import DailyObservationNotReady, run_daily_vnext_observation
from app.scanner.daily_semantics import DailyPipelineMode, radar_oi_schedule_plan
from app.scheduler.domain import (
    CanonicalSlotIdentity,
    CanonicalSlotType,
    actual_market_date,
    execution_delay_seconds,
)
from app.scheduler.repository import SlotClaim, claim_canonical_slot, finish_attempt

CANONICAL_TRIGGER = "google_cloud_scheduler"


@dataclass(frozen=True)
class CanonicalExecutionResult:
    slot_id: str
    canonical_key: str
    slot_type: str
    intended_at: str
    intended_market_date: str
    actual_started_at: str
    execution_delay_seconds: int
    trigger_transport: str
    status: str
    paid_work_attempted: bool
    network_attempts: int
    consumed_units: int
    created_execution_state: bool
    product_candidate_count: int
    baseline_count: int
    result: dict[str, Any]

    @classmethod
    def from_claim(
        cls,
        claim: SlotClaim,
        identity: CanonicalSlotIdentity,
    ) -> CanonicalExecutionResult:
        slot = claim.slot
        return cls(
            slot_id=str(slot.id),
            canonical_key=slot.canonical_key,
            slot_type=slot.slot_type,
            intended_at=ensure_utc(slot.intended_at).isoformat(),
            intended_market_date=slot.intended_market_date.isoformat(),
            actual_started_at=ensure_utc(slot.actual_started_at).isoformat(),
            execution_delay_seconds=execution_delay_seconds(
                identity,
                slot.actual_started_at,
            ),
            trigger_transport=slot.trigger_transport,
            status=slot.status,
            paid_work_attempted=slot.paid_work_attempted,
            network_attempts=slot.network_attempts,
            consumed_units=slot.consumed_units,
            created_execution_state=claim.created,
            product_candidate_count=slot.product_candidate_count,
            baseline_count=slot.baseline_count,
            result=slot.result or {},
        )

    def to_dict(self) -> dict[str, Any]:
        return self.__dict__.copy()


class CanonicalSchedulerOrchestrator:
    def __init__(self, session: Session, settings: Settings) -> None:
        self.session = session
        self.settings = settings

    async def execute(
        self,
        *,
        identity: CanonicalSlotIdentity,
        actual_started_at: datetime,
        scheduler_job_name: str,
    ) -> CanonicalExecutionResult:
        actual = ensure_utc(actual_started_at)
        if execution_delay_seconds(identity, actual) < 0:
            raise ValueError("ACTUAL_START_PRECEDES_INTENDED_SLOT")
        claim = claim_canonical_slot(
            self.session,
            identity=identity,
            actual_started_at=actual,
            scheduler_job_name=scheduler_job_name,
        )
        if not claim.created:
            return CanonicalExecutionResult.from_claim(claim, identity)
        try:
            if identity.slot_type == CanonicalSlotType.RADAR_OI:
                await self._run_radar_oi(claim, identity, actual)
            elif identity.slot_type == CanonicalSlotType.DEALER_GEX:
                await self._run_dealer_gex(claim, identity, actual)
            else:
                await self._run_activity_vnext(claim, identity, actual)
        except Exception as error:
            self.session.rollback()
            slot = self.session.get(CanonicalSchedulerSlot, claim.slot.id)
            if slot is not None:
                self._complete(
                    claim,
                    slot,
                    status="FAILED",
                    result={"safe_error": type(error).__name__},
                )
            raise
        return CanonicalExecutionResult.from_claim(claim, identity)

    def _client(self, *, concurrency: int) -> NightwatchClient:
        return NightwatchClient(
            base_url=str(self.settings.nightwatch_base_url),
            api_key=self.settings.nightwatch_api_key,
            timeout_seconds=self.settings.nightwatch_timeout_seconds,
            max_retries=0,
            max_concurrency=concurrency,
        )

    async def _run_radar_oi(
        self,
        claim: SlotClaim,
        identity: CanonicalSlotIdentity,
        actual: datetime,
    ) -> None:
        plan = radar_oi_schedule_plan(actual)
        if actual_market_date(actual) != identity.intended_market_date:
            self._complete(
                claim,
                claim.slot,
                status="SKIPPED_OUTSIDE_INTENDED_MARKET_DATE",
                result={"source_validity_guard": "ACTUAL_DATE_MISMATCH", "network_attempts": 0},
            )
            return
        if not plan.should_collect:
            self._complete(
                claim,
                claim.slot,
                status=plan.status,
                result={"source_validity_guard": plan.status, "network_attempts": 0},
            )
            return
        async with self._client(
            concurrency=min(self.settings.nightwatch_max_concurrency, 4)
        ) as client:
            summary = await DailyDataPipeline(self.session, client).execute(
                trigger=CANONICAL_TRIGGER,
                mode=DailyPipelineMode.RADAR_OI,
                started_at=actual,
                market_date_override=identity.intended_market_date,
                canonical_slot_id=claim.slot.id,
            )
        claim.slot.network_attempts = summary.network_attempts
        claim.slot.consumed_units = summary.consumed_quota_units
        claim.slot.paid_work_attempted = summary.network_attempts > 0
        self._complete(
            claim,
            claim.slot,
            status=summary.status,
            result={
                "daily_collection_run_id": str(summary.daily_run_id),
                "subjob_statuses": {
                    name: value.get("status") for name, value in summary.subjobs.items()
                },
            },
        )

    async def _run_dealer_gex(
        self,
        claim: SlotClaim,
        identity: CanonicalSlotIdentity,
        actual: datetime,
    ) -> None:
        async with self._client(concurrency=1) as client:
            summary = await DealerGexArchiver(self.session, client).execute(
                trigger=CANONICAL_TRIGGER,
                now=actual,
                intended_market_date=identity.intended_market_date,
                canonical_slot_id=claim.slot.id,
            )
        claim.slot.network_attempts = summary.network_attempts
        claim.slot.consumed_units = summary.consumed_quota_units
        claim.slot.paid_work_attempted = summary.network_attempts > 0
        self._complete(
            claim,
            claim.slot,
            status=summary.status,
            result={
                "dealer_gex_archive_run_id": (
                    str(summary.archive_run_id) if summary.archive_run_id else None
                ),
                "ticker_statuses": {
                    str(row.get("ticker")): row.get("status") for row in summary.tickers
                },
            },
        )

    async def _run_activity_vnext(
        self,
        claim: SlotClaim,
        identity: CanonicalSlotIdentity,
        actual: datetime,
    ) -> None:
        async with self._client(
            concurrency=min(self.settings.nightwatch_max_concurrency, 4)
        ) as client:
            activity = await DailyDataPipeline(self.session, client).execute(
                trigger=CANONICAL_TRIGGER,
                mode=DailyPipelineMode.ACTIVITY,
                started_at=actual,
                market_date_override=identity.intended_market_date,
                canonical_slot_id=claim.slot.id,
            )
            claim.slot.network_attempts = activity.network_attempts
            claim.slot.consumed_units = activity.consumed_quota_units
            claim.slot.paid_work_attempted = activity.network_attempts > 0
            if activity.status != "COMPLETE":
                self._complete(
                    claim,
                    claim.slot,
                    status=activity.status,
                    result={
                        "daily_collection_run_id": str(activity.daily_run_id),
                        "activity_status": activity.status,
                        "readiness_status": "NOT_EVALUATED_ACTIVITY_INCOMPLETE",
                        "scan_run_id": None,
                    },
                )
                return
            try:
                observation = await run_daily_vnext_observation(
                    self.session,
                    client,
                    evaluated_at=actual,
                    intended_market_date=identity.intended_market_date,
                    canonical_slot_id=claim.slot.id,
                )
            except DailyObservationNotReady as error:
                self._complete(
                    claim,
                    claim.slot,
                    status="HELD_NOT_READY",
                    result={
                        "daily_collection_run_id": str(activity.daily_run_id),
                        "activity_status": activity.status,
                        "readiness_status": str(error),
                        "scan_run_id": None,
                    },
                )
                return
        claim.slot.network_attempts += observation.network_attempts
        claim.slot.consumed_units += observation.consumed_quota_units
        claim.slot.paid_work_attempted = claim.slot.network_attempts > 0
        claim.slot.product_candidate_count = observation.candidate_count
        claim.slot.baseline_count = observation.baseline_count
        self._complete(
            claim,
            claim.slot,
            status=observation.observation_status,
            result={
                "daily_collection_run_id": str(activity.daily_run_id),
                "activity_status": activity.status,
                "scan_run_id": observation.scan_run_id,
                "scan_status": observation.scan_status,
            },
        )

    def _complete(
        self,
        claim: SlotClaim,
        slot: CanonicalSchedulerSlot,
        *,
        status: str,
        result: dict[str, Any],
    ) -> None:
        completed_at = utc_now()
        slot.status = status
        slot.result = result
        slot.completed_at = completed_at
        finish_attempt(
            self.session,
            claim.attempt,
            completed_at=completed_at,
            disposition="EXECUTED",
            result_status=status,
        )

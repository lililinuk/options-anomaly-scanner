from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import date, datetime
from typing import Any

import exchange_calendars as xcals
import pandas as pd
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.confirmation.vnext import Stage6BalancedContextService
from app.core.time import utc_now
from app.db.models import (
    CanonicalSchedulerSlot,
    DailyCollectionCoverage,
    DailyCollectionRun,
    DailyOiArchiveRun,
    DailyOiArchiveTicker,
    ScanRun,
)
from app.nightwatch.client import NightwatchClient
from app.scanner.candidate_persistence import load_product_candidates_for_scan
from app.scanner.config import UNIVERSE
from app.scanner.daily_semantics import activity_session_plan
from app.scanner.v13 import Mag7Scanner


class DailyObservationNotReady(RuntimeError):
    """Fail closed before a paid scan when canonical daily evidence is incomplete."""


@dataclass(frozen=True)
class DailyObservationReadiness:
    market_date: date
    expected_vendor_oi_date: date
    activity_tickers: tuple[str, ...]
    radar_tickers: tuple[str, ...]
    oi_archive_tickers: tuple[str, ...]


@dataclass(frozen=True)
class DailyObservationSummary:
    scan_run_id: str
    scan_status: str
    observation_status: str
    candidate_count: int
    baseline_count: int
    consumed_quota_units: int
    network_attempts: int


def expected_previous_xnys_session(market_day: date) -> date:
    calendar = xcals.get_calendar("XNYS")
    label = pd.Timestamp(market_day.isoformat())
    if not calendar.is_session(label):
        raise DailyObservationNotReady("NOT_XNYS_SESSION")
    return calendar.previous_session(label).date()


def _complete_tickers(rows: list[Any]) -> tuple[str, ...]:
    return tuple(sorted({str(row.ticker) for row in rows}))


def _require_full_mag7(label: str, tickers: tuple[str, ...]) -> None:
    missing = sorted(set(UNIVERSE) - set(tickers))
    unexpected = sorted(set(tickers) - set(UNIVERSE))
    if missing or unexpected:
        raise DailyObservationNotReady(
            f"{label}_COVERAGE_INCOMPLETE missing={','.join(missing) or 'NONE'} "
            f"unexpected={','.join(unexpected) or 'NONE'}"
        )


def load_daily_observation_readiness(
    session: Session,
    *,
    evaluated_at: datetime | None = None,
    intended_market_date: date | None = None,
    canonical_slot_id: uuid.UUID | None = None,
) -> DailyObservationReadiness:
    now = evaluated_at or utc_now()
    plan = activity_session_plan(now, intended_market_date=intended_market_date)
    if not plan.should_collect:
        raise DailyObservationNotReady(plan.status)
    market_day = plan.market_date
    expected_oi_date = expected_previous_xnys_session(market_day)

    activity_query = select(DailyCollectionCoverage).where(
        DailyCollectionCoverage.subjob == "ACTIVITY",
        DailyCollectionCoverage.activity_market_date == market_day,
        DailyCollectionCoverage.status == "COMPLETE",
    )
    radar_query = select(DailyCollectionCoverage).where(
        DailyCollectionCoverage.subjob == "RADAR",
        DailyCollectionCoverage.vendor_oi_date == expected_oi_date,
        DailyCollectionCoverage.status == "COMPLETE",
    )
    oi_query = select(DailyOiArchiveTicker).where(
        DailyOiArchiveTicker.vendor_oi_date == expected_oi_date,
        DailyOiArchiveTicker.status.in_({"COMPLETE", "NO_NEW_VENDOR_OI_SNAPSHOT"}),
    )
    if canonical_slot_id is not None:
        activity_query = activity_query.join(
            DailyCollectionRun,
            DailyCollectionRun.id == DailyCollectionCoverage.daily_run_id,
        ).where(DailyCollectionRun.canonical_slot_id == canonical_slot_id)
        radar_query = (
            radar_query.join(
                DailyCollectionRun,
                DailyCollectionRun.id == DailyCollectionCoverage.daily_run_id,
            )
            .join(
                CanonicalSchedulerSlot,
                CanonicalSchedulerSlot.id == DailyCollectionRun.canonical_slot_id,
            )
            .where(
                CanonicalSchedulerSlot.slot_type == "RADAR_OI",
                CanonicalSchedulerSlot.intended_market_date == market_day,
            )
        )
        oi_query = (
            oi_query.join(
                DailyOiArchiveRun,
                DailyOiArchiveRun.id == DailyOiArchiveTicker.archive_run_id,
            )
            .join(
                CanonicalSchedulerSlot,
                CanonicalSchedulerSlot.id == DailyOiArchiveRun.canonical_slot_id,
            )
            .where(
                CanonicalSchedulerSlot.slot_type == "RADAR_OI",
                CanonicalSchedulerSlot.intended_market_date == market_day,
            )
        )
    else:
        # Interim GitHub scheduled production remains active until the atomic GCP
        # cutover. Keep its source gate isolated from workflow_dispatch/CLI evidence.
        activity_query = activity_query.join(
            DailyCollectionRun,
            DailyCollectionRun.id == DailyCollectionCoverage.daily_run_id,
        ).where(DailyCollectionRun.trigger == "scheduled")
        radar_query = radar_query.join(
            DailyCollectionRun,
            DailyCollectionRun.id == DailyCollectionCoverage.daily_run_id,
        ).where(DailyCollectionRun.trigger == "scheduled")
        oi_query = oi_query.join(
            DailyOiArchiveRun,
            DailyOiArchiveRun.id == DailyOiArchiveTicker.archive_run_id,
        ).where(DailyOiArchiveRun.trigger == "scheduled")
    activity_rows = list(session.scalars(activity_query))
    radar_rows = list(session.scalars(radar_query))
    oi_rows = list(session.scalars(oi_query))
    activity_tickers = _complete_tickers(activity_rows)
    radar_tickers = _complete_tickers(radar_rows)
    oi_tickers = _complete_tickers(oi_rows)
    _require_full_mag7("ACTIVITY", activity_tickers)
    _require_full_mag7("RADAR", radar_tickers)
    _require_full_mag7("DAILY_OI", oi_tickers)

    prior_scheduled_run = session.scalar(
        select(ScanRun.id)
        .where(
            ScanRun.market_date == market_day,
            ScanRun.trigger == "scheduled_daily",
        )
        .limit(1)
    )
    if prior_scheduled_run is not None:
        raise DailyObservationNotReady("SCHEDULED_SCAN_ALREADY_EXISTS_NO_AUTOMATIC_RETRY")

    return DailyObservationReadiness(
        market_date=market_day,
        expected_vendor_oi_date=expected_oi_date,
        activity_tickers=activity_tickers,
        radar_tickers=radar_tickers,
        oi_archive_tickers=oi_tickers,
    )


async def run_daily_vnext_observation(
    session: Session,
    client: NightwatchClient,
    *,
    evaluated_at: datetime | None = None,
    intended_market_date: date | None = None,
    canonical_slot_id: uuid.UUID | None = None,
) -> DailyObservationSummary:
    """Run one scheduled vNext scan and archived-evidence baselines after readiness passes."""

    load_daily_observation_readiness(
        session,
        evaluated_at=evaluated_at,
        intended_market_date=intended_market_date,
        canonical_slot_id=canonical_slot_id,
    )
    scan_kwargs: dict[str, Any] = {"trigger": "scheduled_daily"}
    if intended_market_date is not None:
        scan_kwargs["market_date_override"] = intended_market_date
    if canonical_slot_id is not None:
        scan_kwargs["canonical_slot_id"] = canonical_slot_id
    scan = await Mag7Scanner(session, client).execute(**scan_kwargs)
    if scan.status != "COMPLETE":
        return DailyObservationSummary(
            scan_run_id=str(scan.scan_run_id),
            scan_status=scan.status,
            observation_status=scan.status,
            candidate_count=0,
            baseline_count=0,
            consumed_quota_units=scan.consumed_quota_units,
            network_attempts=scan.network_attempts,
        )

    candidates = load_product_candidates_for_scan(session, scan.scan_run_id)
    baseline_service = Stage6BalancedContextService(session)
    baselines = [baseline_service.create_baseline(candidate.id) for candidate in candidates]
    session.commit()
    return DailyObservationSummary(
        scan_run_id=str(scan.scan_run_id),
        scan_status=scan.status,
        observation_status="COMPLETE" if candidates else "SUCCESS_NO_CANDIDATE",
        candidate_count=len(candidates),
        baseline_count=len(baselines),
        consumed_quota_units=scan.consumed_quota_units,
        network_attempts=scan.network_attempts,
    )

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from app.config import get_settings
from app.db.models import (
    BucketPositioningSummary,
    ContractScanObservation,
    DailyOiArchiveRun,
    ExpiryObservation,
    OiChangeRadarObservation,
    ScanRun,
    StrikeCluster,
)
from app.db.session import get_db_session
from app.nightwatch.client import NightwatchClient
from app.scanner.service import ConcurrentScanError, ScanSummary
from app.scanner.v11 import Mag7Scanner

router = APIRouter()
database_session = Depends(get_db_session)


class ScanSummaryResponse(BaseModel):
    scan_run_id: str
    status: str
    tickers_scanned: int
    deep_tickers: int
    expirations_deep_scanned: int
    contracts_analyzed: int
    clusters_found: int
    consumed_quota_units: int
    network_attempts: int
    cache_hits: int
    fresh_requests: int
    elapsed_seconds: float


def _response(summary: ScanSummary) -> ScanSummaryResponse:
    return ScanSummaryResponse(**{**summary.__dict__, "scan_run_id": str(summary.scan_run_id)})


@router.post("/mag7", response_model=ScanSummaryResponse)
async def run_mag7_scan(session: Session = database_session) -> ScanSummaryResponse:
    settings = get_settings()
    try:
        async with NightwatchClient(
            base_url=str(settings.nightwatch_base_url),
            api_key=settings.nightwatch_api_key,
            timeout_seconds=settings.nightwatch_timeout_seconds,
            max_retries=0,
            max_concurrency=min(settings.nightwatch_max_concurrency, 4),
        ) as client:
            return _response(await Mag7Scanner(session, client).execute(trigger="dashboard"))
    except ConcurrentScanError as error:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(error)) from error


@router.get("/mag7/latest")
def latest_mag7_scan(session: Session = database_session) -> dict[str, Any]:
    run = session.scalar(
        select(ScanRun)
        .where(ScanRun.specification_version == "signal_spec_v1.1_phase2a")
        .order_by(desc(ScanRun.started_at))
        .limit(1)
    )
    if run is None:
        return {"scan": None, "results": []}
    summaries = list(
        session.scalars(
            select(BucketPositioningSummary).where(BucketPositioningSummary.scan_run_id == run.id)
        )
    )
    expiry_by_id = {
        row.id: row
        for row in session.scalars(
            select(ExpiryObservation).where(
                ExpiryObservation.id.in_(
                    {item.strongest_expiry_id for item in summaries if item.strongest_expiry_id}
                )
            )
        )
    }
    by_ticker: dict[str, BucketPositioningSummary] = {}
    for item in summaries:
        expiry = expiry_by_id.get(item.strongest_expiry_id)
        prior = by_ticker.get(item.ticker)
        prior_expiry = expiry_by_id.get(prior.strongest_expiry_id) if prior else None
        if prior is None or float(expiry.discovery_score or 0) > float(
            prior_expiry.discovery_score or 0
        ):
            by_ticker[item.ticker] = item
    archive = session.scalar(
        select(DailyOiArchiveRun).order_by(desc(DailyOiArchiveRun.started_at)).limit(1)
    )
    selected = list(by_ticker.values())
    cluster_by_id = {
        row.id: row
        for row in session.scalars(
            select(StrikeCluster).where(
                StrikeCluster.id.in_(
                    {
                        identifier
                        for item in selected
                        for identifier in (
                            item.strongest_call_cluster_id,
                            item.strongest_put_cluster_id,
                        )
                        if identifier
                    }
                )
            )
        )
    }
    contract_by_id = {
        row.id: row
        for row in session.scalars(
            select(ContractScanObservation).where(
                ContractScanObservation.id.in_(
                    {
                        identifier
                        for item in selected
                        for identifier in (
                            item.strongest_call_contract_id,
                            item.strongest_put_contract_id,
                        )
                        if identifier
                    }
                )
            )
        )
    }
    radar_tested_tickers = set(
        session.scalars(
            select(OiChangeRadarObservation.ticker)
            .where(OiChangeRadarObservation.scan_run_id == run.id)
            .distinct()
        )
    )
    radar_match_tickers = set(
        session.scalars(
            select(ContractScanObservation.ticker)
            .where(
                ContractScanObservation.scan_run_id == run.id,
                ContractScanObservation.oi_change_radar_status == "OBSERVED",
            )
            .distinct()
        )
    )
    results = []
    for ticker, item in sorted(by_ticker.items()):
        expiry = expiry_by_id.get(item.strongest_expiry_id)
        call_cluster = cluster_by_id.get(item.strongest_call_cluster_id)
        put_cluster = cluster_by_id.get(item.strongest_put_cluster_id)
        call_contract = contract_by_id.get(item.strongest_call_contract_id)
        put_contract = contract_by_id.get(item.strongest_put_contract_id)
        contract_rows = [row for row in (call_contract, put_contract) if row]
        results.append(
            {
                "ticker": ticker,
                "strongest_bucket": item.bucket,
                "strongest_expiry": expiry.expiration.isoformat() if expiry else None,
                "same_day_activity_score": _float(
                    expiry.same_day_activity_score if expiry else None
                ),
                "persistent_positioning_score": _float(
                    expiry.persistent_positioning_score if expiry else None
                ),
                "discovery_score": _float(expiry.discovery_score if expiry else None),
                "discovery_source": expiry.discovery_source if expiry else None,
                "oi_share": _float(expiry.oi_share if expiry else None),
                "oi_share_change": _winning_share_change(expiry),
                "oi_skew": _float(expiry.oi_skew if expiry else None),
                "history_coverage": expiry.history_confidence if expiry else None,
                "contract_structure_score": _max_numeric(
                    row.structure_score for row in contract_rows
                ),
                "contract_persistent_score": _max_numeric(
                    row.persistent_positioning_score for row in contract_rows
                ),
                "oi_change_radar_status": _radar_status(
                    ticker, radar_tested_tickers, radar_match_tickers
                ),
                "strongest_call_cluster": _cluster_label(call_cluster),
                "strongest_put_cluster": _cluster_label(put_cluster),
                "call_cluster_score": _float(call_cluster.cluster_score if call_cluster else None),
                "put_cluster_score": _float(put_cluster.cluster_score if put_cluster else None),
                "positioning_structure": item.positioning_label,
                "archive_vendor_oi_date": expiry.vendor_oi_date.isoformat()
                if expiry and expiry.vendor_oi_date
                else None,
                "last_scan": run.completed_at or run.started_at,
            }
        )
    return {
        "scan": {
            "scan_run_id": str(run.id),
            "status": run.status,
            "started_at": run.started_at,
            "completed_at": run.completed_at,
            "consumed_quota_units": run.consumed_quota_units,
            "network_attempts": run.network_attempts,
            "cache_hits": run.cache_hits,
            "fresh_requests": run.fresh_requests,
            **(run.summary or {}),
            "archive_status": archive.status if archive else None,
            "archive_vendor_dates": (archive.summary or {}).get("vendor_dates")
            if archive
            else None,
            "archive_completed_at": archive.completed_at if archive else None,
        },
        "results": results,
    }


def _float(value: Any) -> float | None:
    return float(value) if value is not None else None


def _max_numeric(values: Any) -> float | None:
    present = [float(value) for value in values if value is not None]
    return max(present) if present else None


def _radar_status(ticker: str, tested: set[str], matched: set[str]) -> str:
    if ticker in matched:
        return "OBSERVED"
    if ticker in tested:
        return "NOT_OBSERVED"
    return "NOT_TESTED"


def _winning_share_change(expiry: ExpiryObservation | None) -> float | None:
    if not expiry or not expiry.persistent_winning_window:
        return None
    details = (
        (expiry.persistent_components or {})
        .get("windows", {})
        .get(str(expiry.persistent_winning_window), {})
    )
    value = details.get("oi_share_change")
    return float(value) * 100 if value is not None else None


def _cluster_label(cluster: StrikeCluster | None) -> str | None:
    return f"{cluster.min_strike:g}–{cluster.max_strike:g}" if cluster else None

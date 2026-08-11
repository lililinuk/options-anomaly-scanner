from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from app.config import get_settings
from app.db.models import BucketPositioningSummary, ExpiryObservation, ScanRun, StrikeCluster
from app.db.session import get_db_session
from app.nightwatch.client import NightwatchClient
from app.scanner.service import ConcurrentScanError, Mag7Scanner, ScanSummary

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
    except ConcurrentScanError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc


@router.get("/mag7/latest")
def latest_mag7_scan(session: Session = database_session) -> dict[str, Any]:
    run = session.scalar(
        select(ScanRun)
        .where(ScanRun.specification_version.is_not(None))
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
    by_ticker: dict[str, BucketPositioningSummary] = {}
    for item in summaries:
        expiry = (
            session.get(ExpiryObservation, item.strongest_expiry_id)
            if item.strongest_expiry_id
            else None
        )
        prior = by_ticker.get(item.ticker)
        prior_expiry = (
            session.get(ExpiryObservation, prior.strongest_expiry_id)
            if prior and prior.strongest_expiry_id
            else None
        )
        if prior is None or float(expiry.expiry_score or expiry.preliminary_score) > float(
            prior_expiry.expiry_score or prior_expiry.preliminary_score
        ):
            by_ticker[item.ticker] = item
    results = []
    for ticker, item in sorted(by_ticker.items()):
        expiry = (
            session.get(ExpiryObservation, item.strongest_expiry_id)
            if item.strongest_expiry_id
            else None
        )
        call_cluster = (
            session.get(StrikeCluster, item.strongest_call_cluster_id)
            if item.strongest_call_cluster_id
            else None
        )
        put_cluster = (
            session.get(StrikeCluster, item.strongest_put_cluster_id)
            if item.strongest_put_cluster_id
            else None
        )
        results.append(
            {
                "ticker": ticker,
                "strongest_bucket": item.bucket,
                "strongest_expiry": expiry.expiration.isoformat() if expiry else None,
                "expiry_anomaly_score": float(expiry.expiry_score or expiry.preliminary_score)
                if expiry
                else None,
                "strongest_call_cluster": _cluster_label(call_cluster),
                "strongest_put_cluster": _cluster_label(put_cluster),
                "call_cluster_score": float(call_cluster.cluster_score) if call_cluster else None,
                "put_cluster_score": float(put_cluster.cluster_score) if put_cluster else None,
                "positioning_structure": item.positioning_label,
                "oi_status": item.oi_status,
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
        },
        "results": results,
    }


def _cluster_label(cluster: StrikeCluster | None) -> str | None:
    return f"{cluster.min_strike:g}–{cluster.max_strike:g}" if cluster else None

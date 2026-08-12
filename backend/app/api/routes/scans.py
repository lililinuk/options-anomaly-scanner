from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from app.config import get_settings
from app.db.models import (
    ContractScanObservation,
    DailyOiArchiveRun,
    ExpiryObservation,
    OiChangeRadarObservation,
    ScanRun,
    StrikeCluster,
)
from app.db.session import get_db_session
from app.nightwatch.client import NightwatchClient
from app.scanner.config import LIMITS, UNIVERSE
from app.scanner.service import ConcurrentScanError, ScanSummary
from app.scanner.v12 import Mag7Scanner

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
        .where(ScanRun.specification_version == "signal_spec_v1.2_phase2a")
        .order_by(desc(ScanRun.started_at))
        .limit(1)
    )
    if run is None:
        return {
            "scan": None,
            "results": [],
            "distribution": _distribution([]),
            "top_expiries": [],
            "zero_dte_status": [],
            "structural_cold_start": [],
        }
    expiries = list(
        session.scalars(
            select(ExpiryObservation).where(ExpiryObservation.scan_run_id == run.id)
        )
    )
    normal_eligible = [row for row in expiries if _normal_eligible(row)]
    winners = {
        ticker: max(
            (row for row in normal_eligible if row.ticker == ticker),
            key=lambda row: float(row.discovery_score),
            default=None,
        )
        for ticker in UNIVERSE
    }
    archive = session.scalar(
        select(DailyOiArchiveRun).order_by(desc(DailyOiArchiveRun.started_at)).limit(1)
    )
    contracts = list(
        session.scalars(
            select(ContractScanObservation).where(ContractScanObservation.scan_run_id == run.id)
        )
    )
    expiry_ids = {row.id for row in expiries}
    clusters = list(
        session.scalars(
            select(StrikeCluster).where(StrikeCluster.expiry_observation_id.in_(expiry_ids))
        )
    )
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
    for ticker in UNIVERSE:
        expiry = winners[ticker]
        expiry_contracts = [
            row for row in contracts if expiry and row.expiry_observation_id == expiry.id
        ]
        expiry_clusters = [
            row for row in clusters if expiry and row.expiry_observation_id == expiry.id
        ]
        call_cluster = max(
            (row for row in expiry_clusters if row.right == "C"),
            key=lambda row: float(row.cluster_score),
            default=None,
        )
        put_cluster = max(
            (row for row in expiry_clusters if row.right == "P"),
            key=lambda row: float(row.cluster_score),
            default=None,
        )
        results.append(
            {
                "ticker": ticker,
                "strongest_bucket": expiry.bucket_at_detection if expiry else None,
                "strongest_expiry": expiry.expiration.isoformat() if expiry else None,
                "dte": expiry.dte_at_detection if expiry else None,
                "same_day_activity_score": _float(
                    expiry.same_day_activity_score if expiry else None
                ),
                "persistent_positioning_score": _float(
                    expiry.persistent_positioning_score if expiry else None
                ),
                "discovery_score": _float(expiry.discovery_score if expiry else None),
                "discovery_source": expiry.discovery_source if expiry else None,
                "discovery_evidence_breadth": expiry.discovery_evidence_breadth
                if expiry
                else 0,
                "discovery_primary_score": _float(
                    expiry.discovery_primary_score if expiry else None
                ),
                "discovery_secondary_score": _float(
                    expiry.discovery_secondary_score if expiry else None
                ),
                "discovery_confirmation_bonus": _float(
                    expiry.discovery_confirmation_bonus if expiry else None
                ),
                "oi_share": _float(expiry.oi_share if expiry else None),
                "oi_share_change": _winning_share_change(expiry),
                "oi_skew": _float(expiry.oi_skew if expiry else None),
                "history_coverage": expiry.history_confidence if expiry else None,
                "contract_structure_score": _max_numeric(
                    row.structure_score for row in expiry_contracts
                ),
                "contract_persistent_score": _max_numeric(
                    row.persistent_positioning_score for row in expiry_contracts
                ),
                "oi_change_radar_status": _radar_status(
                    ticker, radar_tested_tickers, radar_match_tickers
                ),
                "strongest_call_cluster": _cluster_label(call_cluster),
                "strongest_put_cluster": _cluster_label(put_cluster),
                "call_cluster_score": _float(call_cluster.cluster_score if call_cluster else None),
                "put_cluster_score": _float(put_cluster.cluster_score if put_cluster else None),
                "positioning_structure": _positioning_label(call_cluster, put_cluster),
                "archive_vendor_oi_date": expiry.vendor_oi_date.isoformat()
                if expiry and expiry.vendor_oi_date
                else None,
                "current_volume_share": _float(expiry.volume_share if expiry else None),
                "same_day_baseline_status": expiry.same_day_baseline_status
                if expiry
                else None,
                "baseline_observation_count": expiry.baseline_observation_count
                if expiry
                else None,
                "last_scan": run.completed_at or run.started_at,
            }
        )
    top_expiries = sorted(
        normal_eligible, key=lambda row: float(row.discovery_score), reverse=True
    )[:15]
    zero_dte = [row for row in expiries if row.dte_at_detection == 0]
    cold_only = [
        row
        for row in expiries
        if row.structural_cold_start_eligible and row.discovery_score is None
    ]
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
        "distribution": _distribution(expiries),
        "top_expiries": [_expiry_public(row) for row in top_expiries],
        "zero_dte_status": [_zero_dte_public(row) for row in zero_dte],
        "structural_cold_start": [_expiry_public(row) for row in cold_only],
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


def _normal_eligible(row: ExpiryObservation) -> bool:
    if row.dte_at_detection > 90 or row.discovery_score is None:
        return False
    same_day = _float(row.same_day_activity_score)
    persistent = _float(row.persistent_positioning_score)
    return bool(
        (same_day is not None and same_day >= LIMITS.same_day_eligibility_score)
        or (
            persistent is not None
            and persistent >= LIMITS.persistent_eligibility_score
        )
    )


def _distribution(rows: list[ExpiryObservation]) -> dict[str, int]:
    in_scope = [row for row in rows if row.dte_at_detection <= 90]
    scores = [float(row.discovery_score) for row in in_scope if row.discovery_score is not None]
    return {
        "total_expiries": len(in_scope),
        "scored_expiries": len(scores),
        "normal_eligible_expiries": sum(_normal_eligible(row) for row in in_scope),
        "discovery_90_plus": sum(score >= 90 for score in scores),
        "discovery_80_89": sum(80 <= score < 90 for score in scores),
        "discovery_65_79": sum(65 <= score < 80 for score in scores),
        "discovery_40_64": sum(40 <= score < 65 for score in scores),
        "discovery_below_40": sum(score < 40 for score in scores),
        "unavailable": sum(row.discovery_score is None for row in in_scope),
        "cold_start": sum(
            row.discovery_score is None
            and (
                row.same_day_baseline_status == "INSUFFICIENT"
                or row.structural_cold_start_eligible
            )
            for row in in_scope
        ),
    }


def _expiry_public(row: ExpiryObservation) -> dict[str, Any]:
    return {
        "ticker": row.ticker,
        "expiry": row.expiration.isoformat(),
        "dte": row.dte_at_detection,
        "bucket": row.bucket_at_detection,
        "same_day_activity_score": _float(row.same_day_activity_score),
        "persistent_positioning_score": _float(row.persistent_positioning_score),
        "discovery_score": _float(row.discovery_score),
        "discovery_source": row.discovery_source,
        "discovery_evidence_breadth": row.discovery_evidence_breadth,
        "current_volume_share": _float(row.volume_share),
        "peer_count": row.comparable_peer_count,
        "peer_dtes": row.comparable_peer_dtes,
        "peer_quality": row.comparable_peer_quality,
    }


def _zero_dte_public(row: ExpiryObservation) -> dict[str, Any]:
    return {
        **_expiry_public(row),
        "current_expiry_volume": row.current_expiry_volume,
        "raw_neighbor_ratio_descriptive_only": _float(row.neighbor_ratio),
        "baseline_status": row.same_day_baseline_status,
        "baseline_observation_count": row.baseline_observation_count,
        "baseline_required": LIMITS.zero_dte_baseline_observations,
        "baseline_mean": _float(row.baseline_20_mean_volume_share),
        "baseline_median": _float(row.baseline_20_median_volume_share),
        "baseline_mad": _float(row.baseline_20_mad_volume_share),
        "historical_percentile": _float(row.historical_percentile_20),
        "robust_deviation": _float(row.robust_deviation),
        "baseline_method": row.zero_dte_baseline_method,
    }


def _positioning_label(
    call_cluster: StrikeCluster | None, put_cluster: StrikeCluster | None
) -> str:
    if call_cluster and put_cluster:
        return "TWO_SIDED"
    if call_cluster:
        return "CALL_STRUCTURE"
    if put_cluster:
        return "PUT_STRUCTURE"
    return "NO_STRONG_STRUCTURE"


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

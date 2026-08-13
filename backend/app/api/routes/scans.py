from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import desc, func, select
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
from app.scanner.v13 import Mag7Scanner, active_radar_threshold_profile

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
        .where(ScanRun.specification_version == "signal_spec_v1.3_phase2a")
        .order_by(desc(ScanRun.started_at))
        .limit(1)
    )
    if run is None:
        # Preserve access to accepted v1.2 history until the first v1.3 interactive run. Daily
        # Radar evidence is still returned independently below.
        run = session.scalar(
            select(ScanRun)
            .where(ScanRun.specification_version == "signal_spec_v1.2_phase2a")
            .order_by(desc(ScanRun.started_at))
            .limit(1)
        )
    if run is None:
        empty = {
            "scan": None,
            "results": [],
            "distribution": _distribution([]),
            "top_expiries": [],
            "zero_dte_status": [],
            "structural_cold_start": [],
        }
        empty.update(_v13_sections(session, None, [], []))
        return empty
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
    payload = {
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
    payload.update(_v13_sections(session, run, expiries, contracts))
    return payload


def _v13_sections(
    session: Session,
    run: ScanRun | None,
    expiries: list[ExpiryObservation],
    contracts: list[ContractScanObservation],
) -> dict[str, Any]:
    profile = active_radar_threshold_profile()
    radar_rows: list[OiChangeRadarObservation] = []
    for ticker in UNIVERSE:
        latest = session.scalar(
            select(func.max(OiChangeRadarObservation.observation_date)).where(
                OiChangeRadarObservation.ticker == ticker,
                OiChangeRadarObservation.material_event_eligible.is_(True),
            )
        )
        if latest:
            radar_rows.extend(
                session.scalars(
                    select(OiChangeRadarObservation).where(
                        OiChangeRadarObservation.ticker == ticker,
                        OiChangeRadarObservation.observation_date == latest,
                        OiChangeRadarObservation.material_event_eligible.is_(True),
                    )
                )
            )
    radar_rows.sort(
        key=lambda row: (_float(row.premium) or 0, abs(row.delta_oi or 0)), reverse=True
    )
    material_events = [_radar_public(row) for row in radar_rows]

    persistent_contracts = [
        row
        for row in contracts
        if row.persistent_positioning_score is not None
        and float(row.persistent_positioning_score) >= LIMITS.persistent_eligibility_score
    ]
    persistent_contracts.sort(
        key=lambda row: float(row.persistent_positioning_score or 0), reverse=True
    )
    activity = [row for row in expiries if row.expiry_activity_route_eligible]
    activity.sort(key=lambda row: float(row.same_day_activity_score or 0), reverse=True)
    deep_dive = _deep_dive_public(radar_rows, persistent_contracts, expiries)
    return {
        "specification_version": "signal_spec_v1.3_phase2a",
        "threshold_profile": profile.snapshot(),
        "radar_filters": {
            "min_premium_usd": _float(profile.min_premium_usd),
            "min_abs_oi_diff": profile.min_abs_oi_diff,
        },
        "latest_contract_events": material_events[:15],
        "all_material_contract_events": material_events,
        "persistent_positioning": [_persistent_public(row) for row in persistent_contracts],
        "unusual_expiry_activity": [_activity_public(row) for row in activity],
        "research_candidates": deep_dive,
        "route_counts": _route_counts(radar_rows, persistent_contracts, expiries),
        "legacy_v12_available": bool(
            run and run.specification_version == "signal_spec_v1.2_phase2a"
        ),
    }


def _radar_public(row: OiChangeRadarObservation) -> dict[str, Any]:
    return {
        "ticker": row.ticker,
        "contract_symbol": row.contract_symbol,
        "vendor_observation_date": row.observation_date.isoformat()
        if row.observation_date
        else None,
        "previous_observation_date": row.previous_date.isoformat()
        if row.previous_date
        else None,
        "previous_oi": row.previous_oi,
        "current_oi": row.current_oi,
        "oi_diff": row.delta_oi,
        "oi_change": _float(row.relative_oi_change),
        "volume": row.volume,
        "trades": row.trades,
        "premium_usd": _float(row.premium),
        "avg_price_usd": _float(row.average_price),
        "last_bid_usd": _float(row.last_bid),
        "last_ask_usd": _float(row.last_ask),
        "last_fill_usd": _float(row.last_fill),
        "vendor_rank": row.rank,
        "premium_per_trade": _float(row.premium_per_trade),
        "volume_per_trade": _float(row.volume_per_trade),
        "archive_match_status": row.archive_match_status or "UNAVAILABLE",
        "expiration": row.matched_expiration.isoformat() if row.matched_expiration else None,
        "dte": row.matched_dte,
        "right": row.matched_right,
        "strike": _float(row.matched_strike),
        "archived_oi": row.archived_oi,
        "archive_completeness": row.archive_completeness or "UNAVAILABLE",
        "contract_structure_score": _float(row.contract_structure_score),
        "contract_persistent_score": _float(row.contract_persistent_score),
        "radar_scope": row.radar_scope,
        "deep_dive_eligible": row.deep_dive_eligible,
        "trigger_sources": row.trigger_sources or [],
        "risk_flags": row.risk_flags or [],
        "threshold_profile_id": row.threshold_profile_id,
        "threshold_profile_version": row.threshold_profile_version,
    }


def _persistent_public(row: ContractScanObservation) -> dict[str, Any]:
    windows = (row.persistent_components or {}).get("windows", {})
    return {
        "ticker": row.ticker,
        "contract_symbol": row.contract_symbol,
        "expiration": row.expiration.isoformat(),
        "dte": row.dte_at_detection,
        "right": row.right,
        "strike": _float(row.strike),
        "oi_change_3": windows.get("3", {}).get("net_oi_change"),
        "oi_change_5": windows.get("5", {}).get("net_oi_change"),
        "oi_change_10": windows.get("10", {}).get("net_oi_change"),
        "oi_growth": windows.get(str(row.persistent_winning_window), {}).get("oi_growth")
        if row.persistent_winning_window
        else None,
        "persistent_state": row.persistent_state,
        "persistent_score": _float(row.persistent_positioning_score),
        "winning_window": row.persistent_winning_window,
        "history_confidence": row.history_confidence,
        "history_observation_count": row.history_observation_count,
        "history_required": 3,
    }


def _activity_public(row: ExpiryObservation) -> dict[str, Any]:
    return {
        "ticker": row.ticker,
        "expiry": row.expiration.isoformat(),
        "dte": row.dte_at_detection,
        "same_day_activity_score": _float(row.same_day_activity_score),
        "volume_share": _float(row.volume_share),
        "volume_share_points": _float(row.volume_share_points),
        "neighbor_ratio": _float(row.neighbor_ratio),
        "neighbor_points": _float(row.neighbor_points),
        "score_basis": row.same_day_score_basis,
        "standard_monthly_inferred": row.standard_monthly_inferred,
        "monthly_context_source": row.monthly_context_source,
        "baseline_status": row.same_day_baseline_status,
        "baseline_observation_count": row.baseline_observation_count,
    }


def _deep_dive_public(
    radar: list[OiChangeRadarObservation],
    persistent: list[ContractScanObservation],
    expiries: list[ExpiryObservation],
) -> list[dict[str, Any]]:
    candidates: dict[tuple[str, str], dict[str, Any]] = {}
    for row in radar:
        if not row.deep_dive_eligible:
            continue
        key = (row.ticker, row.contract_symbol)
        candidates[key] = {
            "ticker": row.ticker,
            "contract_or_expiry": row.contract_symbol,
            "expiration": row.matched_expiration.isoformat() if row.matched_expiration else None,
            "trigger_sources": row.trigger_sources or ["RADAR_EVENT"],
            "radar_premium_usd": _float(row.premium),
            "radar_oi_diff": row.delta_oi,
            "persistent_score": _float(row.contract_persistent_score),
            "expiry_activity_score": None,
            "structure_score": _float(row.contract_structure_score),
            "archive_completeness": row.archive_completeness,
            "risk_flags": row.risk_flags or [],
        }
    for row in persistent:
        key = (row.ticker, row.contract_symbol)
        item = candidates.setdefault(
            key,
            {
                "ticker": row.ticker,
                "contract_or_expiry": row.contract_symbol,
                "expiration": row.expiration.isoformat(),
                "trigger_sources": [],
                "radar_premium_usd": None,
                "radar_oi_diff": None,
                "expiry_activity_score": None,
                "archive_completeness": "COMPLETE_ARCHIVE_REUSED",
                "risk_flags": row.risk_flags or [],
            },
        )
        item["persistent_score"] = _float(row.persistent_positioning_score)
        item["structure_score"] = _float(row.structure_score)
        item["trigger_sources"] = sorted(
            set([*item["trigger_sources"], "CONTRACT_PERSISTENCE"])
        )
    for row in expiries:
        if not row.deep_dive_eligible:
            continue
        key = (row.ticker, row.expiration.isoformat())
        candidates.setdefault(
            key,
            {
                "ticker": row.ticker,
                "contract_or_expiry": row.expiration.isoformat(),
                "expiration": row.expiration.isoformat(),
                "trigger_sources": row.trigger_sources or [],
                "radar_premium_usd": None,
                "radar_oi_diff": None,
                "persistent_score": _float(row.persistent_positioning_score),
                "expiry_activity_score": _float(row.same_day_activity_score),
                "structure_score": None,
                "archive_completeness": "COMPLETE_ARCHIVE_REUSED"
                if row.selected_for_deep_scan
                else "NOT_LOADED",
                "risk_flags": [],
            },
        )
    return list(candidates.values())


def _route_counts(
    radar: list[OiChangeRadarObservation],
    persistent: list[ContractScanObservation],
    expiries: list[ExpiryObservation],
) -> dict[str, int]:
    return {
        "radar_events": len(radar),
        "persistent_contracts": len(persistent),
        "expiry_activity": sum(row.expiry_activity_route_eligible for row in expiries),
        "expiry_persistence": sum(row.persistent_route_eligible for row in expiries),
        "structural_cold_start": sum(row.structural_cold_start_eligible for row in expiries),
        "multiple_routes": sum(len(set(row.trigger_sources or [])) > 1 for row in expiries),
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

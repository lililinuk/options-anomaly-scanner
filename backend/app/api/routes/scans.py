from __future__ import annotations

from datetime import date
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from app.config import get_settings
from app.confirmation.service import latest_candidate_context
from app.db.models import (
    ContractScanObservation,
    DailyOiArchiveRun,
    ExpiryObservation,
    OiChangeRadarObservation,
    ScanRun,
    StrikeCluster,
    ZeroDteActivitySessionSnapshot,
)
from app.db.session import get_db_session
from app.nightwatch.client import NightwatchClient
from app.scanner.candidate_persistence import (
    load_product_candidates_for_scan,
    product_candidate_public,
)
from app.scanner.candidate_projection import (
    contract_deep_dive as _shared_contract_deep_dive,
)
from app.scanner.candidate_projection import (
    expiry_deep_dive as _shared_expiry_deep_dive,
)
from app.scanner.candidate_projection import (
    load_stage4_candidate_projection,
)
from app.scanner.candidate_projection import (
    persistence_evidence_for_projection as _shared_persistence_evidence,
)
from app.scanner.candidate_projection import (
    persistent_public as _shared_persistent_public,
)
from app.scanner.candidate_projection import (
    vnext_anomaly_pool as _shared_vnext_anomaly_pool,
)
from app.scanner.config import LIMITS, SIGNAL_SPEC_VERSION, UNIVERSE
from app.scanner.service import ConcurrentScanError, ScanSummary
from app.scanner.v13 import Mag7Scanner, active_radar_threshold_profile
from app.scanner.vnext import (
    ACTIVE_DISCOVERY_FAMILIES,
    REMOVED_ACTIVE_DISCOVERY_FAMILIES,
    persistence_freshness_policy,
)

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


def _run_state(run: ScanRun | None, *, candidate_count: int) -> str:
    """Map persisted scan truth to the Stage 2 run-level availability contract."""

    if run is None:
        return "NOT_RUN"
    if run.status == "RUNNING":
        return "RUNNING"
    if run.status != "COMPLETE":
        # PARTIAL, DATA_PENDING, and budget-limited runs must not claim a successful
        # no-candidate outcome. The original backend status remains available in scan.status.
        return "FAILED"
    return "SUCCESS_WITH_CANDIDATES" if candidate_count else "SUCCESS_NO_CANDIDATE"


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
        .where(ScanRun.specification_version == SIGNAL_SPEC_VERSION)
        .order_by(desc(ScanRun.started_at))
        .limit(1)
    )
    if run is None:
        # Accepted historical rows remain readable, but the API labels them explicitly and
        # never uses their legacy universal score/breadth fields for the vNext projection.
        run = session.scalar(
            select(ScanRun)
            .where(
                ScanRun.specification_version.in_(
                    ("signal_spec_v1.3_phase2a", "signal_spec_v1.2_phase2a")
                )
            )
            .order_by(desc(ScanRun.started_at))
            .limit(1)
        )
    if run is None:
        empty = {
            "run_state": "NOT_RUN",
            "scan": None,
            "product_candidates_state": "NOT_YET_AVAILABLE",
            "product_candidates": [],
            "zero_dte_status": [],
            "legacy_phase2a": None,
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
            key=lambda row: float(row.same_day_activity_score or 0),
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
            (row for row in expiry_clusters if row.right == "C" and _valid_cluster(row)),
            key=lambda row: float(row.cluster_score),
            default=None,
        )
        put_cluster = max(
            (row for row in expiry_clusters if row.right == "P" and _valid_cluster(row)),
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
                "legacy_discovery_score": _float(expiry.discovery_score if expiry else None),
                "legacy_discovery_source": expiry.discovery_source if expiry else None,
                "legacy_discovery_evidence_breadth": expiry.discovery_evidence_breadth
                if expiry
                else None,
                "legacy_discovery_primary_score": _float(
                    expiry.discovery_primary_score if expiry else None
                ),
                "legacy_discovery_secondary_score": _float(
                    expiry.discovery_secondary_score if expiry else None
                ),
                "legacy_discovery_confirmation_bonus": _float(
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
        normal_eligible, key=lambda row: float(row.same_day_activity_score or 0), reverse=True
    )[:15]
    zero_dte = [row for row in expiries if row.dte_at_detection == 0]
    zero_dte_snapshot_kind = {
        row.ticker: row.snapshot_kind
        for row in (
            session.scalars(
                select(ZeroDteActivitySessionSnapshot).where(
                    ZeroDteActivitySessionSnapshot.scan_run_id == run.id
                )
            )
            if zero_dte
            else []
        )
    }
    persisted_candidates = load_product_candidates_for_scan(session, run.id)
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
        "product_candidates_state": (
            "AVAILABLE"
            if run.candidate_materialized_at is not None
            else "NOT_YET_AVAILABLE"
        ),
        "product_candidates": [
            product_candidate_public(candidate) for candidate in persisted_candidates
        ],
        "zero_dte_status": [
            _zero_dte_public(
                row,
                current_snapshot_kind=zero_dte_snapshot_kind.get(
                    row.ticker,
                    "LEGACY_OR_AMBIGUOUS",
                ),
            )
            for row in zero_dte
        ],
        "legacy_phase2a": {
            "source_specification_version": run.specification_version,
            "not_used_for_vnext_candidate_qualification": True,
            "results": results,
            "distribution": _distribution(expiries),
            "top_expiries": [_expiry_public(row) for row in top_expiries],
            "structural_cold_start_history": [_expiry_public(row) for row in cold_only],
        },
    }
    payload.update(_v13_sections(session, run, expiries, contracts))
    payload["run_state"] = _run_state(
        run,
        candidate_count=len(payload["research_candidates"]),
    )
    return payload


@router.get("/candidates/{contract_symbol}/confirmation")
def candidate_confirmation(
    contract_symbol: str, session: Session = database_session
) -> dict[str, Any]:
    """Read persisted Phase 2B evidence; this route never contacts Nightwatch."""

    context = latest_candidate_context(session, contract_symbol)
    if context is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Context not available")
    return context


def _v13_sections(
    session: Session,
    run: ScanRun | None,
    expiries: list[ExpiryObservation],
    contracts: list[ContractScanObservation],
) -> dict[str, Any]:
    profile = active_radar_threshold_profile()
    projection = load_stage4_candidate_projection(
        session,
        run,
        expiries,
        contracts,
        policy=persistence_freshness_policy(),
        knowledge_cutoff=getattr(run, "candidate_materialized_at", None),
    )
    analysis_date = run.market_date if run is not None else None
    radar_rows = projection.radar_rows
    material_events = [_radar_public(row) for row in radar_rows]
    persistent_contracts = projection.persistence_rows
    activity = projection.activity_rows
    anomaly_pool = projection.anomaly_pool
    product_candidates = projection.product_candidates
    return {
        "specification_version": SIGNAL_SPEC_VERSION,
        "architecture": {
            "active_discovery": list(ACTIVE_DISCOVERY_FAMILIES),
            "removed_active_discovery": list(REMOVED_ACTIVE_DISCOVERY_FAMILIES),
            "candidate_entity": "TICKER_PRODUCT_PROJECTION",
            "anomaly_entity": "CONTRACT_OR_EXPIRY",
            "persisted_product_candidate_created": bool(
                getattr(run, "candidate_materialized_at", None) is not None
            ),
        },
        "threshold_profile": profile.snapshot(),
        "radar_filters": {
            "min_premium_usd": _float(profile.min_premium_usd),
            "min_abs_oi_diff": profile.min_abs_oi_diff,
        },
        "latest_contract_events": material_events[:15],
        "all_material_contract_events": material_events,
        "persistent_positioning": [
            _persistent_public(row, analysis_date=analysis_date) for row in persistent_contracts
        ],
        "unusual_expiry_activity": [_activity_public(row) for row in activity],
        "anomaly_pool": anomaly_pool,
        "research_candidates": product_candidates,
        "route_counts": _route_counts(
            anomaly_pool,
            product_candidates,
            projection.persistence_analytics,
        ),
        "persistence_current_trigger_freshness": persistence_freshness_policy().snapshot(),
    }


def _persistence_evidence_for_projection(
    session: Session,
    *,
    analysis_date: date | None,
    current_run_analytics: list[ContractScanObservation],
) -> list[ContractScanObservation]:
    return _shared_persistence_evidence(
        session,
        analysis_date=analysis_date,
        current_run_analytics=current_run_analytics,
        policy=persistence_freshness_policy(),
    )


def _vnext_anomaly_pool(
    radar: list[OiChangeRadarObservation],
    persistent: list[ContractScanObservation],
    activity: list[ExpiryObservation],
    *,
    contracts: list[ContractScanObservation],
    clusters: list[StrikeCluster],
    analysis_date: date | None,
) -> list[dict[str, Any]]:
    return _shared_vnext_anomaly_pool(
        radar,
        persistent,
        activity,
        contracts=contracts,
        clusters=clusters,
        analysis_date=analysis_date,
        policy=persistence_freshness_policy(),
    )


def _contract_deep_dive(row: ContractScanObservation | None) -> dict[str, Any]:
    return _shared_contract_deep_dive(row)


def _expiry_deep_dive(
    contracts: list[ContractScanObservation], clusters: list[StrikeCluster]
) -> dict[str, Any]:
    return _shared_expiry_deep_dive(contracts, clusters)


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


def _persistent_public(
    row: ContractScanObservation, *, analysis_date: date | None
) -> dict[str, Any]:
    return _shared_persistent_public(
        row,
        analysis_date=analysis_date,
        policy=persistence_freshness_policy(),
    )


def _activity_public(row: ExpiryObservation) -> dict[str, Any]:
    components = row.components or {}
    dte_identity = components.get("dte_identity", {})
    return {
        "ticker": row.ticker,
        "expiry": row.expiration.isoformat(),
        "dte": row.dte_at_detection,
        "same_day_activity_score": _float(row.same_day_activity_score),
        "volume_share": _float(row.volume_share),
        "volume_share_points": _float(row.volume_share_points),
        "comparable_neighbor_ratio": _float(row.neighbor_ratio),
        "comparable_peer_count": row.comparable_peer_count,
        "comparable_peer_dtes": row.comparable_peer_dtes,
        "comparable_peer_quality": row.comparable_peer_quality,
        "comparable_peer_median_volume": _float(row.comparable_peer_median_volume),
        "raw_cross_expiry_neighbor_ratio_descriptive_only": components.get(
            "raw_cross_expiry_neighbor_ratio_descriptive_only"
        ),
        "neighbor_points": _float(row.neighbor_points),
        "score_basis": row.same_day_score_basis,
        "score_components": components.get("same_day", {}),
        "dte_anchor_date": dte_identity.get("anchor_date"),
        "dte_anchor_type": dte_identity.get("anchor_type"),
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
            "entity_type": "CONTRACT",
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
                "entity_type": "CONTRACT",
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
                "entity_type": "EXPIRY_ONLY",
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
    anomaly_pool: list[dict[str, Any]],
    product_candidates: list[dict[str, Any]],
    persistent_analytics: list[ContractScanObservation],
) -> dict[str, int]:
    return {
        "radar_events": sum(
            row["evidence_family"] == "RADAR_EVENT" for row in anomaly_pool
        ),
        "expiry_activity": sum(
            row["evidence_family"] == "EXPIRY_ACTIVITY" for row in anomaly_pool
        ),
        "contract_persistence_current_triggers": sum(
            row["evidence_family"] == "CONTRACT_PERSISTENCE"
            and row["qualifies_current_candidate"] is True
            for row in anomaly_pool
        ),
        "contract_persistence_analytics": len(persistent_analytics),
        "product_candidates": len(product_candidates),
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
    """Legacy v1.2/v1.3 expiry summary eligibility; never used by vNext projection."""

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
        "score_basis": row.same_day_score_basis,
        "current_volume_share": _float(row.volume_share),
        "comparable_neighbor_ratio": _float(row.neighbor_ratio),
        "peer_count": row.comparable_peer_count,
        "peer_dtes": row.comparable_peer_dtes,
        "peer_quality": row.comparable_peer_quality,
    }


def _zero_dte_public(
    row: ExpiryObservation,
    *,
    current_snapshot_kind: str = "LEGACY_OR_AMBIGUOUS",
) -> dict[str, Any]:
    observation_count = row.baseline_observation_count or 0
    return {
        **_expiry_public(row),
        "current_expiry_volume": row.current_expiry_volume,
        "raw_neighbor_ratio_descriptive_only": (row.components or {}).get(
            "raw_cross_expiry_neighbor_ratio_descriptive_only"
        ),
        "baseline_status": row.same_day_baseline_status,
        "baseline_observation_count": row.baseline_observation_count,
        "baseline_required": LIMITS.zero_dte_baseline_observations,
        "current_snapshot_kind": current_snapshot_kind,
        "canonical_history_maturity": (
            "AVAILABLE"
            if observation_count >= LIMITS.zero_dte_baseline_observations
            else "HISTORY_IMMATURE"
        ),
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
    valid_call = _valid_cluster(call_cluster)
    valid_put = _valid_cluster(put_cluster)
    if valid_call and valid_put:
        return "TWO_SIDED"
    if valid_call:
        return "CALL_STRUCTURE"
    if valid_put:
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
    return f"{cluster.min_strike:g}–{cluster.max_strike:g}" if _valid_cluster(cluster) else None


def _valid_cluster(cluster: StrikeCluster | None) -> bool:
    return bool(
        cluster and cluster.classification in {"VALID_CLUSTER", "STRONG_CLUSTER"}
    )

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from typing import Any
from uuid import UUID

from sqlalchemy import desc, func, select
from sqlalchemy.orm import Session

from app.confirmation.provenance import source_time_entry
from app.db.models import (
    ContractScanObservation,
    ExpiryObservation,
    OiChangeRadarObservation,
    RawVendorPayload,
    ScanRun,
    StrikeCluster,
)
from app.scanner.config import LIMITS, UNIVERSE
from app.scanner.vnext import (
    PersistenceFreshnessPolicy,
    analysis_date_exclusive_utc_cutoff,
    group_product_candidates,
    persistence_observation_is_time_admissible,
    persistence_window_last_observation_date,
    select_current_persistence_observations,
)


@dataclass(frozen=True)
class Stage4CandidateProjection:
    """The accepted Stage 4 candidate projection and its exact source rows."""

    radar_rows: list[OiChangeRadarObservation]
    persistence_rows: list[ContractScanObservation]
    persistence_analytics: list[ContractScanObservation]
    activity_rows: list[ExpiryObservation]
    anomaly_pool: list[dict[str, Any]]
    product_candidates: list[dict[str, Any]]


def load_stage4_candidate_projection(
    session: Session,
    run: ScanRun | None,
    expiries: list[ExpiryObservation],
    contracts: list[ContractScanObservation],
    *,
    policy: PersistenceFreshnessPolicy,
    knowledge_cutoff: datetime | None = None,
) -> Stage4CandidateProjection:
    """Load and group the accepted Stage 4 evidence without a second eligibility model."""

    radar_rows = _latest_radar_rows(session, knowledge_cutoff=knowledge_cutoff)
    persistence_analytics = [
        row
        for row in contracts
        if row.persistent_positioning_score is not None
        and float(row.persistent_positioning_score) >= LIMITS.persistent_eligibility_score
    ]
    persistence_rows = persistence_evidence_for_projection(
        session,
        analysis_date=run.market_date if run is not None else None,
        current_run_analytics=persistence_analytics,
        policy=policy,
        knowledge_cutoff=knowledge_cutoff,
    )
    persistence_rows.sort(
        key=lambda row: float(row.persistent_positioning_score or 0), reverse=True
    )
    activity_rows = [
        row
        for row in expiries
        if row.same_day_activity_score is not None
        and float(row.same_day_activity_score) >= LIMITS.same_day_eligibility_score
    ]
    activity_rows.sort(key=lambda row: float(row.same_day_activity_score or 0), reverse=True)
    expiry_ids = [row.id for row in expiries]
    clusters = (
        list(
            session.scalars(
                select(StrikeCluster).where(StrikeCluster.expiry_observation_id.in_(expiry_ids))
            )
        )
        if expiry_ids
        else []
    )
    raw_payloads = _load_raw_payloads(
        session,
        [*radar_rows, *persistence_rows, *activity_rows],
    )
    anomaly_pool = vnext_anomaly_pool(
        radar_rows,
        persistence_rows,
        activity_rows,
        contracts=contracts,
        clusters=clusters,
        analysis_date=run.market_date if run is not None else None,
        policy=policy,
        raw_payloads=raw_payloads,
    )
    return Stage4CandidateProjection(
        radar_rows=radar_rows,
        persistence_rows=persistence_rows,
        persistence_analytics=persistence_analytics,
        activity_rows=activity_rows,
        anomaly_pool=anomaly_pool,
        product_candidates=group_product_candidates(anomaly_pool),
    )


def persistence_evidence_for_projection(
    session: Session,
    *,
    analysis_date: date | None,
    current_run_analytics: list[ContractScanObservation],
    policy: PersistenceFreshnessPolicy,
    knowledge_cutoff: datetime | None = None,
) -> list[ContractScanObservation]:
    """Return untruncated current triggers plus available current-run analytics."""

    current_triggers: list[ContractScanObservation] = []
    if analysis_date is not None:
        conditions = [
            ContractScanObservation.persistent_positioning_score
            >= LIMITS.persistent_eligibility_score,
            ContractScanObservation.ticker.in_(UNIVERSE),
            ContractScanObservation.observed_at
            < analysis_date_exclusive_utc_cutoff(analysis_date),
        ]
        if knowledge_cutoff is not None:
            conditions.append(ContractScanObservation.observed_at <= knowledge_cutoff)
        candidates = list(
            session.scalars(
                select(ContractScanObservation)
                .where(*conditions)
                .order_by(desc(ContractScanObservation.observed_at))
            )
        )
        current_triggers = list(
            select_current_persistence_observations(
                candidates,
                policy=policy,
                analysis_date=analysis_date,
            )
        )

    evidence_by_symbol = {row.contract_symbol: row for row in current_triggers}
    for row in current_run_analytics:
        if knowledge_cutoff is None or _at_or_before(row.observed_at, knowledge_cutoff):
            evidence_by_symbol.setdefault(row.contract_symbol, row)
    return list(evidence_by_symbol.values())


def vnext_anomaly_pool(
    radar: list[OiChangeRadarObservation],
    persistent: list[ContractScanObservation],
    activity: list[ExpiryObservation],
    *,
    contracts: list[ContractScanObservation],
    clusters: list[StrikeCluster],
    analysis_date: date | None,
    policy: PersistenceFreshnessPolicy,
    raw_payloads: dict[str, RawVendorPayload] | None = None,
) -> list[dict[str, Any]]:
    """Build the accepted full active-anomaly pool with immutable source provenance."""

    raw_payloads = raw_payloads or {}
    anomalies: list[dict[str, Any]] = []
    contracts_by_symbol = {row.contract_symbol: row for row in contracts}
    contracts_by_expiry: dict[Any, list[ContractScanObservation]] = {}
    clusters_by_expiry: dict[Any, list[StrikeCluster]] = {}
    for row in contracts:
        contracts_by_expiry.setdefault(row.expiry_observation_id, []).append(row)
    for row in clusters:
        clusters_by_expiry.setdefault(row.expiry_observation_id, []).append(row)
    for row in radar:
        contract = contracts_by_symbol.get(row.contract_symbol)
        source = _source_provenance(
            raw_payloads,
            _row_raw_payload_ids(row),
            source_request_ids=[getattr(row, "source_request_id", None)],
            capability="options.oi_change.radar",
        )
        row_id = getattr(row, "id", None)
        anomalies.append(
            {
                "anomaly_entity": "CONTRACT",
                "anomaly_identity": row.contract_symbol,
                "ticker": row.ticker,
                "evidence_family": "RADAR_EVENT",
                "evidence_date": row.observation_date.isoformat()
                if row.observation_date
                else None,
                "qualifies_current_candidate": True,
                "expiration": row.matched_expiration.isoformat()
                if row.matched_expiration
                else None,
                "dte": row.matched_dte,
                "dte_anchor_date": row.observation_date.isoformat()
                if row.observation_date
                else None,
                "dte_anchor_type": "VENDOR_OBSERVATION_DATE",
                "deep_dive_eligible": bool(row.deep_dive_eligible),
                "radar_premium_usd": _float(row.premium),
                "radar_oi_diff": row.delta_oi,
                "archive_completeness": row.archive_completeness or "UNAVAILABLE",
                "risk_flags": row.risk_flags or [],
                "deep_dive_context": contract_deep_dive(contract),
                "source_evidence_identity": f"oi_change_radar_observation:{row_id}",
                "source_radar_observation_id": str(row_id) if row_id is not None else None,
                "source_expiry_observation_id": None,
                "source_contract_observation_id": None,
                "source_raw_payload_id": _string_or_none(
                    getattr(row, "raw_payload_id", None)
                ),
                "trigger_first_knowledge_at": getattr(row, "captured_at", None)
                or source["local_captured_at"],
                "specification_version": getattr(row, "specification_version", None),
                "threshold_profile_version": getattr(
                    row, "threshold_profile_version", None
                ),
                **source,
            }
        )
    for row in activity:
        dte_identity = (row.components or {}).get("dte_identity", {})
        source = _source_provenance(
            raw_payloads,
            _row_raw_payload_ids(row),
            source_request_ids=getattr(row, "source_request_ids", None) or [],
            capability="options.expiry_activity",
        )
        row_id = getattr(row, "id", None)
        anomalies.append(
            {
                "anomaly_entity": "EXPIRY",
                "anomaly_identity": row.expiration.isoformat(),
                "ticker": row.ticker,
                "evidence_family": "EXPIRY_ACTIVITY",
                "evidence_date": dte_identity.get("anchor_date"),
                "qualifies_current_candidate": True,
                "expiration": row.expiration.isoformat(),
                "dte": row.dte_at_detection,
                "dte_anchor_date": dte_identity.get("anchor_date"),
                "dte_anchor_type": dte_identity.get("anchor_type"),
                "score_basis": row.same_day_score_basis,
                "same_day_activity_score": _float(row.same_day_activity_score),
                "comparable_neighbor_ratio": _float(row.neighbor_ratio),
                "deep_dive_eligible": bool(row.deep_dive_eligible),
                "deep_dive_context": expiry_deep_dive(
                    contracts_by_expiry.get(row.id, []),
                    clusters_by_expiry.get(row.id, []),
                ),
                "source_evidence_identity": f"expiry_observation:{row_id}",
                "source_radar_observation_id": None,
                "source_expiry_observation_id": str(row_id) if row_id is not None else None,
                "source_contract_observation_id": None,
                "source_raw_payload_id": None,
                "trigger_first_knowledge_at": getattr(row, "observed_at", None),
                "specification_version": getattr(row, "specification_version", None),
                **source,
            }
        )
    for row in persistent:
        public = persistent_public(row, analysis_date=analysis_date, policy=policy)
        deep_dive_row = contracts_by_symbol.get(row.contract_symbol)
        source = _source_provenance(
            raw_payloads,
            _row_raw_payload_ids(row),
            source_request_ids=getattr(row, "source_request_ids", None) or [],
            capability="options.contract_persistence",
        )
        row_id = getattr(row, "id", None)
        anomalies.append(
            {
                "anomaly_entity": "CONTRACT",
                "anomaly_identity": row.contract_symbol,
                "ticker": row.ticker,
                "evidence_family": "CONTRACT_PERSISTENCE",
                "evidence_date": public["window_last_observation_date"],
                "qualifies_current_candidate": public["current_trigger_eligible"],
                "expiration": row.expiration.isoformat(),
                "dte": row.dte_at_detection,
                "dte_anchor_date": (row.components or {})
                .get("dte_identity", {})
                .get("anchor_date"),
                "dte_anchor_type": (row.components or {})
                .get("dte_identity", {})
                .get("anchor_type"),
                "persistent_state": row.persistent_state,
                "current_trigger_freshness": public["current_trigger_freshness"],
                "deep_dive_selected_for_current_run": deep_dive_row is not None,
                "deep_dive_eligible": deep_dive_row is not None,
                "deep_dive_context": contract_deep_dive(deep_dive_row),
                "source_evidence_identity": f"contract_scan_observation:{row_id}",
                "source_radar_observation_id": None,
                "source_expiry_observation_id": None,
                "source_contract_observation_id": str(row_id) if row_id is not None else None,
                "source_raw_payload_id": _string_or_none(
                    getattr(row, "raw_payload_id", None)
                ),
                "trigger_first_knowledge_at": getattr(row, "observed_at", None),
                "specification_version": getattr(row, "specification_version", None),
                **source,
            }
        )
    return anomalies


def persistent_public(
    row: ContractScanObservation,
    *,
    analysis_date: date | None,
    policy: PersistenceFreshnessPolicy,
) -> dict[str, Any]:
    windows = (row.persistent_components or {}).get("windows", {})
    window_last = persistence_window_last_observation_date(row)
    if analysis_date is None:
        current_trigger_eligible = False
        current_trigger_state = (
            "CALIBRATION_REQUIRED"
            if policy.mode == "CALIBRATION_REQUIRED"
            else "ANALYSIS_DATE_UNAVAILABLE"
        )
        observation_age_days = None
    elif (
        policy.mode != "CALIBRATION_REQUIRED"
        and not persistence_observation_is_time_admissible(row, analysis_date=analysis_date)
    ):
        current_trigger_eligible = False
        current_trigger_state = "INADMISSIBLE_OBSERVATION_TIME"
        observation_age_days = None
    else:
        assessment = policy.assess(
            window_last_observation_date=window_last,
            analysis_date=analysis_date,
        )
        current_trigger_eligible = assessment.eligible
        current_trigger_state = assessment.state
        observation_age_days = assessment.observation_age_days
    components = row.persistent_components or {}
    quote = (row.components or {}).get("quote", {})
    dte_identity = (row.components or {}).get("dte_identity", {})
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
        "window_first_observation_date": components.get("window_first_observation_date"),
        "window_last_observation_date": components.get("window_last_observation_date"),
        "valid_observation_count": components.get("valid_observation_count"),
        "no_lookahead_bound": components.get("no_lookahead_bound"),
        "current_trigger_eligible": current_trigger_eligible,
        "current_trigger_freshness": {
            **policy.snapshot(),
            "state": current_trigger_state,
            "observation_age_days": observation_age_days,
        },
        "dte_anchor_date": dte_identity.get("anchor_date"),
        "dte_anchor_type": dte_identity.get("anchor_type"),
        "quote_availability": quote.get("availability"),
        "quote_as_of": quote.get("quote_as_of"),
    }


def contract_deep_dive(row: ContractScanObservation | None) -> dict[str, Any]:
    if row is None:
        return {
            "availability": "UNAVAILABLE",
            "structure_positive_evidence": False,
            "structure": None,
            "quote": None,
        }
    positive = bool(
        row.is_candidate
        and row.classification
        in {"STRUCTURAL_CANDIDATE", "STRONG_STRUCTURE", "EXTREME_STRUCTURE"}
        and row.hard_reject_reason is None
    )
    quote = (row.components or {}).get("quote")
    return {
        "availability": "AVAILABLE",
        "structure_positive_evidence": positive,
        "structure": {
            "score": _float(row.structure_score),
            "classification": row.classification,
            "components": row.structure_components or {},
        },
        "quote": quote,
    }


def expiry_deep_dive(
    contracts: list[ContractScanObservation], clusters: list[StrikeCluster]
) -> dict[str, Any]:
    return {
        "availability": "AVAILABLE" if contracts else "UNAVAILABLE",
        "structures": [contract_deep_dive(row) for row in contracts],
        "valid_clusters": [
            {
                "right": row.right,
                "classification": row.classification,
                "min_strike": _float(row.min_strike),
                "max_strike": _float(row.max_strike),
                "score": _float(row.cluster_score),
                "components": row.components,
            }
            for row in clusters
            if _valid_cluster(row)
        ],
    }


def _latest_radar_rows(
    session: Session, *, knowledge_cutoff: datetime | None
) -> list[OiChangeRadarObservation]:
    rows: list[OiChangeRadarObservation] = []
    for ticker in UNIVERSE:
        latest_query = (
            select(func.max(OiChangeRadarObservation.observation_date))
            .join(
                RawVendorPayload,
                RawVendorPayload.id == OiChangeRadarObservation.raw_payload_id,
            )
            .where(
                OiChangeRadarObservation.ticker == ticker,
                OiChangeRadarObservation.material_event_eligible.is_(True),
            )
        )
        if knowledge_cutoff is not None:
            latest_query = latest_query.where(
                RawVendorPayload.received_at <= knowledge_cutoff
            )
        latest = session.scalar(latest_query)
        if latest is None:
            continue
        row_query = (
            select(OiChangeRadarObservation)
            .join(
                RawVendorPayload,
                RawVendorPayload.id == OiChangeRadarObservation.raw_payload_id,
            )
            .where(
                OiChangeRadarObservation.ticker == ticker,
                OiChangeRadarObservation.observation_date == latest,
                OiChangeRadarObservation.material_event_eligible.is_(True),
            )
        )
        if knowledge_cutoff is not None:
            row_query = row_query.where(RawVendorPayload.received_at <= knowledge_cutoff)
        rows.extend(session.scalars(row_query))
    rows.sort(key=lambda row: (_float(row.premium) or 0, abs(row.delta_oi or 0)), reverse=True)
    return rows


def _load_raw_payloads(
    session: Session, source_rows: list[Any]
) -> dict[str, RawVendorPayload]:
    ids: set[UUID] = set()
    for row in source_rows:
        for value in _row_raw_payload_ids(row):
            try:
                ids.add(UUID(str(value)))
            except (TypeError, ValueError):
                continue
    if not ids:
        return {}
    return {
        str(row.id): row
        for row in session.scalars(select(RawVendorPayload).where(RawVendorPayload.id.in_(ids)))
    }


def _row_raw_payload_ids(row: Any) -> list[Any]:
    values = list(getattr(row, "raw_payload_ids", None) or [])
    single = getattr(row, "raw_payload_id", None)
    if single is not None:
        values.append(single)
    return values


def _source_provenance(
    raw_payloads: dict[str, RawVendorPayload],
    raw_ids: list[Any],
    *,
    source_request_ids: list[Any],
    capability: str,
) -> dict[str, Any]:
    raws = [raw_payloads[str(value)] for value in raw_ids if str(value) in raw_payloads]
    entries = {
        str(raw.id): source_time_entry(raw, capability=capability) for raw in raws
    }
    received = sorted(raw.received_at for raw in raws)
    vendor_times = {raw.observed_at for raw in raws if raw.observed_at is not None}
    return {
        "source_first_received_at": received[0] if received else None,
        "vendor_observed_at": next(iter(vendor_times)) if len(vendor_times) == 1 else None,
        "local_captured_at": received[-1] if received else None,
        "source_ids": {
            "raw_payload_ids": [str(value) for value in raw_ids],
            "source_request_ids": [
                str(value) for value in source_request_ids if value is not None
            ],
        },
        "source_time_provenance": entries,
    }


def _at_or_before(value: datetime, cutoff: datetime) -> bool:
    return value <= cutoff


def _string_or_none(value: Any) -> str | None:
    return str(value) if value is not None else None


def _float(value: Any) -> float | None:
    return float(value) if value is not None else None


def _valid_cluster(cluster: StrikeCluster | None) -> bool:
    return bool(
        cluster and cluster.classification in {"VALID_CLUSTER", "STRONG_CLUSTER"}
    )

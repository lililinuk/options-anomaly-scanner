from __future__ import annotations

import hashlib
import json
import uuid
from datetime import date, datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.confirmation.provenance import CandidateFirstKnowledge
from app.core.time import ensure_utc
from app.db.models import (
    ContractScanObservation,
    ExpiryObservation,
    ProductCandidate,
    ProductCandidateTrigger,
    ScanRun,
)
from app.scanner.candidate_projection import (
    Stage4CandidateProjection,
    load_stage4_candidate_projection,
)
from app.scanner.config import SIGNAL_SPEC_VERSION
from app.scanner.vnext import ACTIVE_DISCOVERY_FAMILIES, persistence_freshness_policy

MATERIALIZATION_RULE_VERSION = (
    f"{SIGNAL_SPEC_VERSION}.product-candidate-materialization.v1"
)


def materialize_successful_scan_candidates(
    session: Session,
    run: ScanRun,
    *,
    materialized_at: datetime,
) -> list[ProductCandidate]:
    """Persist the accepted Stage 4 projection exactly once for a successful scan."""

    if run.status != "COMPLETE":
        return []
    cutoff = ensure_utc(materialized_at)
    if run.completed_at is None or ensure_utc(run.completed_at) != cutoff:
        raise ValueError("Candidate materialization cutoff must be the successful scan cutoff")
    rule_hash = materialization_rule_hash(run)
    if run.candidate_materialized_at is not None:
        return _load_verified_replay(session, run, rule_hash=rule_hash)

    existing = load_product_candidates_for_scan(session, run.id)
    if existing:
        raise ValueError("Candidate rows exist without an authoritative materialization marker")

    expiries = list(
        session.scalars(
            select(ExpiryObservation).where(ExpiryObservation.scan_run_id == run.id)
        )
    )
    contracts = list(
        session.scalars(
            select(ContractScanObservation).where(
                ContractScanObservation.scan_run_id == run.id
            )
        )
    )
    projection = load_stage4_candidate_projection(
        session,
        run,
        expiries,
        contracts,
        policy=persistence_freshness_policy(),
        knowledge_cutoff=cutoff,
    )
    return persist_candidate_projection(
        session,
        run,
        projection,
        materialized_at=cutoff,
        rule_hash=rule_hash,
    )


def persist_candidate_projection(
    session: Session,
    run: ScanRun,
    projection: Stage4CandidateProjection,
    *,
    materialized_at: datetime,
    rule_hash: str | None = None,
) -> list[ProductCandidate]:
    """Persist a precomputed accepted projection; exposed for deterministic proofs."""

    cutoff = ensure_utc(materialized_at)
    rule_hash = rule_hash or materialization_rule_hash(run)
    first_knowledge = CandidateFirstKnowledge().establish(
        at=cutoff,
        materialization_rule_version=MATERIALIZATION_RULE_VERSION,
    )
    if first_knowledge.at is None:
        raise ValueError("Prospective candidate first knowledge must be authoritative")

    candidates: list[ProductCandidate] = []
    for item in projection.product_candidates:
        anomalies = list(item.get("anomalies") or [])
        if not any(
            anomaly.get("qualifies_current_candidate") is True for anomaly in anomalies
        ):
            raise ValueError("A ProductCandidate requires a qualifying active trigger")
        candidate = ProductCandidate(
            id=uuid.uuid4(),
            scan_run_id=run.id,
            ticker=str(item["ticker"]),
            candidate_first_knowledge_at=first_knowledge.at,
            materialization_rule_version=MATERIALIZATION_RULE_VERSION,
            materialization_rule_hash=rule_hash,
            lifecycle_state="MATERIALIZED",
            created_at=cutoff,
        )
        session.add(candidate)
        session.flush()
        candidate.triggers.extend(
            _materialize_triggers(
                candidate,
                anomalies,
                materialized_at=cutoff,
                rule_hash=rule_hash,
            )
        )
        candidates.append(candidate)

    run.candidate_materialized_at = cutoff
    run.candidate_materialization_rule_version = MATERIALIZATION_RULE_VERSION
    run.candidate_materialization_rule_hash = rule_hash
    session.flush()
    return candidates


def load_product_candidates_for_scan(
    session: Session, scan_run_id: uuid.UUID
) -> list[ProductCandidate]:
    return list(
        session.scalars(
            select(ProductCandidate)
            .options(selectinload(ProductCandidate.triggers))
            .where(ProductCandidate.scan_run_id == scan_run_id)
            .order_by(ProductCandidate.ticker, ProductCandidate.id)
        )
    )


def load_product_candidate(
    session: Session, candidate_id: uuid.UUID
) -> ProductCandidate | None:
    return session.scalar(
        select(ProductCandidate)
        .options(selectinload(ProductCandidate.triggers))
        .where(ProductCandidate.id == candidate_id)
    )


def product_candidate_public(candidate: ProductCandidate) -> dict[str, Any]:
    triggers = sorted(
        candidate.triggers,
        key=lambda row: (
            ACTIVE_DISCOVERY_FAMILIES.index(row.evidence_family),
            row.anomaly_identity,
            row.source_evidence_identity,
        ),
    )
    return {
        "id": str(candidate.id),
        "scan_run_id": str(candidate.scan_run_id),
        "ticker": candidate.ticker,
        "candidate_first_knowledge_at": candidate.candidate_first_knowledge_at,
        "materialization_rule_version": candidate.materialization_rule_version,
        "materialization_rule_hash": candidate.materialization_rule_hash,
        "lifecycle_state": candidate.lifecycle_state,
        "created_at": candidate.created_at,
        "triggers": [
            {
                "id": str(trigger.id),
                "evidence_family": trigger.evidence_family,
                "anomaly_entity_type": trigger.anomaly_entity_type,
                "anomaly_identity": trigger.anomaly_identity,
                "source_evidence_identity": trigger.source_evidence_identity,
                "qualifies_candidate": trigger.qualifies_candidate,
                "present_at_first_knowledge": trigger.present_at_first_knowledge,
                "event_date": trigger.event_date,
                "trigger_first_knowledge_at": trigger.trigger_first_knowledge_at,
                "source_first_received_at": trigger.source_first_received_at,
                "vendor_observed_at": trigger.vendor_observed_at,
                "local_captured_at": trigger.local_captured_at,
                "source_ids": trigger.source_ids,
                "provenance": trigger.provenance,
                "specification_version": trigger.specification_version,
            }
            for trigger in triggers
        ],
    }


def materialization_rule_hash(run: ScanRun) -> str:
    encoded = json.dumps(
        {
            "rule_version": MATERIALIZATION_RULE_VERSION,
            "source_specification_version": run.specification_version,
            "source_configuration_snapshot": run.configuration_snapshot,
            "active_discovery_families": list(ACTIVE_DISCOVERY_FAMILIES),
        },
        sort_keys=True,
        separators=(",", ":"),
        default=str,
    ).encode()
    return hashlib.sha256(encoded).hexdigest()


def _materialize_triggers(
    candidate: ProductCandidate,
    anomalies: list[dict[str, Any]],
    *,
    materialized_at: datetime,
    rule_hash: str,
) -> list[ProductCandidateTrigger]:
    deduplicated: dict[tuple[str, str], dict[str, Any]] = {}
    for anomaly in anomalies:
        family = str(anomaly.get("evidence_family"))
        source_identity = str(anomaly.get("source_evidence_identity"))
        if family not in ACTIVE_DISCOVERY_FAMILIES:
            raise ValueError(f"Forbidden candidate trigger family: {family}")
        if not source_identity or source_identity.endswith(":None"):
            raise ValueError("Candidate trigger requires authoritative source evidence identity")
        key = (family, source_identity)
        existing = deduplicated.get(key)
        if existing is not None and _trigger_identity(existing) != _trigger_identity(anomaly):
            raise ValueError("Conflicting replay for the same logical trigger")
        deduplicated.setdefault(key, anomaly)

    triggers: list[ProductCandidateTrigger] = []
    for anomaly in deduplicated.values():
        trigger_first = _required_datetime(
            anomaly.get("trigger_first_knowledge_at"),
            "trigger_first_knowledge_at",
        )
        if trigger_first > materialized_at:
            raise ValueError("Future trigger evidence cannot enter first-knowledge state")
        source_first = _optional_datetime(anomaly.get("source_first_received_at"))
        local_captured = _optional_datetime(anomaly.get("local_captured_at"))
        vendor_observed = _optional_datetime(anomaly.get("vendor_observed_at"))
        if source_first is not None and source_first > materialized_at:
            raise ValueError("Future source receipt cannot enter first-knowledge state")
        if local_captured is not None and local_captured > materialized_at:
            raise ValueError("Future local capture cannot enter first-knowledge state")
        trigger = ProductCandidateTrigger(
            id=uuid.uuid4(),
            product_candidate_id=candidate.id,
            evidence_family=str(anomaly["evidence_family"]),
            anomaly_entity_type=str(anomaly["anomaly_entity"]),
            anomaly_identity=str(anomaly["anomaly_identity"]),
            source_evidence_identity=str(anomaly["source_evidence_identity"]),
            qualifies_candidate=anomaly.get("qualifies_current_candidate") is True,
            present_at_first_knowledge=True,
            event_date=_optional_date(anomaly.get("evidence_date")),
            trigger_first_knowledge_at=trigger_first,
            source_first_received_at=source_first,
            vendor_observed_at=vendor_observed,
            local_captured_at=local_captured,
            source_raw_payload_id=_optional_uuid(anomaly.get("source_raw_payload_id")),
            source_radar_observation_id=_optional_uuid(
                anomaly.get("source_radar_observation_id")
            ),
            source_expiry_observation_id=_optional_uuid(
                anomaly.get("source_expiry_observation_id")
            ),
            source_contract_observation_id=_optional_uuid(
                anomaly.get("source_contract_observation_id")
            ),
            source_ids=dict(anomaly.get("source_ids") or {}),
            provenance={
                "materialization_rule_version": MATERIALIZATION_RULE_VERSION,
                "materialization_rule_hash": rule_hash,
                "source_time_provenance": anomaly.get("source_time_provenance") or {},
                "current_trigger_freshness": anomaly.get("current_trigger_freshness"),
                "threshold_profile_version": anomaly.get("threshold_profile_version"),
            },
            specification_version=str(
                anomaly.get("specification_version") or SIGNAL_SPEC_VERSION
            ),
            created_at=materialized_at,
        )
        triggers.append(trigger)
    return triggers


def _load_verified_replay(
    session: Session, run: ScanRun, *, rule_hash: str
) -> list[ProductCandidate]:
    marker = (
        run.candidate_materialized_at,
        run.candidate_materialization_rule_version,
        run.candidate_materialization_rule_hash,
    )
    if any(value is None for value in marker):
        raise ValueError("Incomplete candidate materialization marker")
    if run.candidate_materialization_rule_version != MATERIALIZATION_RULE_VERSION:
        raise ValueError("Candidate occurrence was materialized under a different rule version")
    if run.candidate_materialization_rule_hash != rule_hash:
        raise ValueError("Candidate occurrence rule provenance conflicts with replay")
    candidates = load_product_candidates_for_scan(session, run.id)
    for candidate in candidates:
        if (
            candidate.candidate_first_knowledge_at != run.candidate_materialized_at
            or candidate.materialization_rule_version != MATERIALIZATION_RULE_VERSION
            or candidate.materialization_rule_hash != rule_hash
        ):
            raise ValueError("Persisted candidate identity conflicts with scan occurrence")
    return candidates


def _trigger_identity(anomaly: dict[str, Any]) -> tuple[Any, ...]:
    return (
        anomaly.get("anomaly_entity"),
        anomaly.get("anomaly_identity"),
        anomaly.get("source_first_received_at"),
        anomaly.get("trigger_first_knowledge_at"),
    )


def _required_datetime(value: Any, field: str) -> datetime:
    parsed = _optional_datetime(value)
    if parsed is None:
        raise ValueError(f"Candidate trigger requires {field}")
    return parsed


def _optional_datetime(value: Any) -> datetime | None:
    if value is None:
        return None
    if isinstance(value, str):
        value = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if not isinstance(value, datetime):
        raise ValueError("Invalid trigger timestamp")
    return ensure_utc(value)


def _optional_date(value: Any) -> date | None:
    if value is None or isinstance(value, date):
        return value
    if isinstance(value, str):
        return date.fromisoformat(value)
    raise ValueError("Invalid trigger event date")


def _optional_uuid(value: Any) -> uuid.UUID | None:
    if value is None:
        return None
    return value if isinstance(value, uuid.UUID) else uuid.UUID(str(value))

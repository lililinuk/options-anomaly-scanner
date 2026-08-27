from __future__ import annotations

from collections import Counter
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from enum import Enum
from typing import Any
from uuid import UUID

import exchange_calendars as xcals
import pandas as pd

from app.core.time import ensure_utc, market_datetime
from app.db.models import (
    ProductCandidate,
    ProductCandidateContext,
    ProductCandidateTrigger,
    ScanRun,
)
from app.models.signals import DteBucket, bucket_for_dte

REFERENCE_PRICE_POLICY = "PRIOR_COMPLETED_REGULAR_CLOSE"
OUTCOME_METHODOLOGY_VERSION = "stage9a.close-path.v1"
RUN_ORIGIN_CLASSIFICATION_VERSION = "stage9a.scan-trigger-origin.v1"
PRICE_BASIS_CAPABILITY = "UNCONFIRMED"
DIRECTION = "UNRESOLVED"


class RunOrigin(str, Enum):
    CANONICAL_SCHEDULED_PRODUCTION = "CANONICAL_SCHEDULED_PRODUCTION"
    MANUAL = "MANUAL"
    CONTROLLED_OBSERVATION = "CONTROLLED_OBSERVATION"
    DIAGNOSTIC = "DIAGNOSTIC"
    REMEDIATION = "REMEDIATION"
    DEVELOPER_RERUN = "DEVELOPER_RERUN"
    OTHER_NON_CANONICAL = "OTHER_NON_CANONICAL"


class ResearchSampleValidity(str, Enum):
    VALID = "VALID"
    INVALID_SAMPLE = "INVALID_SAMPLE"


class RouteComposition(str, Enum):
    RADAR_ONLY = "RADAR_ONLY"
    EXPIRY_ONLY = "EXPIRY_ONLY"
    PERSISTENCE_ONLY = "PERSISTENCE_ONLY"
    RADAR_EXPIRY = "RADAR + EXPIRY"
    RADAR_PERSISTENCE = "RADAR + PERSISTENCE"
    EXPIRY_PERSISTENCE = "EXPIRY + PERSISTENCE"
    RADAR_EXPIRY_PERSISTENCE = "RADAR + EXPIRY + PERSISTENCE"


class MaturityState(str, Enum):
    NOT_YET_MATURE = "NOT_YET_MATURE"
    MATURE_AVAILABLE = "MATURE_AVAILABLE"
    MATURE_MISSING_DATA = "MATURE_MISSING_DATA"
    INVALID_SAMPLE = "INVALID_SAMPLE"


class CorporateActionBasisStatus(str, Enum):
    PROVEN_CONSISTENT = "PROVEN_CONSISTENT"
    UNCONFIRMED = "UNCONFIRMED"
    MISMATCHED = "MISMATCHED"


class PriceBasisNotProvable(ValueError):
    """Raised when outcome prices cannot be proven corporate-action consistent."""


@dataclass(frozen=True)
class ForwardSessionPlan:
    reference_session: date
    t1_session: date
    t3_session: date
    t5_session: date


@dataclass(frozen=True)
class CohortMetadata:
    has_radar: bool
    has_expiry_activity: bool
    has_contract_persistence: bool
    route_composition: RouteComposition | None
    qualifying_trigger_count: int
    dte_bucket_counts: Mapping[str, int]


@dataclass(frozen=True)
class ResearchSampleFoundation:
    product_candidate_id: UUID
    frozen_baseline_context_id: UUID | None
    scan_run_id: UUID
    ticker: str
    candidate_first_knowledge_at: datetime
    sample_validity_state: ResearchSampleValidity
    invalid_reason: str | None
    run_origin: RunOrigin
    run_origin_source_trigger: str
    primary_research_eligible: bool
    sessions: ForwardSessionPlan
    outcome_window_key: str
    cohort: CohortMetadata
    reference_price_policy: str = REFERENCE_PRICE_POLICY
    outcome_methodology_version: str = OUTCOME_METHODOLOGY_VERSION
    run_origin_classification_version: str = RUN_ORIGIN_CLASSIFICATION_VERSION
    price_basis_capability: str = PRICE_BASIS_CAPABILITY
    direction: str = DIRECTION


@dataclass(frozen=True)
class PriceBasis:
    basis_id: str | None
    corporate_action_status: CorporateActionBasisStatus
    provenance: Mapping[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class ClosePriceEvidence:
    session: date
    close: Decimal | int | float | str | None
    basis: PriceBasis


@dataclass(frozen=True)
class OutcomeMetrics:
    close_return: Decimal
    max_upside: Decimal
    max_downside: Decimal


_RUN_ORIGINS = {
    "scheduled_daily": RunOrigin.CANONICAL_SCHEDULED_PRODUCTION,
    "cli": RunOrigin.MANUAL,
    "dashboard": RunOrigin.CONTROLLED_OBSERVATION,
    "controlled": RunOrigin.CONTROLLED_OBSERVATION,
    "diagnostic": RunOrigin.DIAGNOSTIC,
    "test": RunOrigin.DIAGNOSTIC,
    "remediation": RunOrigin.REMEDIATION,
    "developer_rerun": RunOrigin.DEVELOPER_RERUN,
}


def classify_scan_origin(trigger: str) -> RunOrigin:
    """Classify only the explicit persisted trigger; never infer origin from clock time."""

    return _RUN_ORIGINS.get(trigger.strip().lower(), RunOrigin.OTHER_NON_CANONICAL)


def primary_research_eligible(origin: RunOrigin) -> bool:
    return origin is RunOrigin.CANONICAL_SCHEDULED_PRODUCTION


def cohort_metadata(
    triggers: Sequence[ProductCandidateTrigger],
    *,
    dte_by_trigger_id: Mapping[UUID | str, int | str | DteBucket | None] | None = None,
) -> CohortMetadata:
    """Describe qualifying first-knowledge evidence without another admission filter."""

    qualifying = [
        trigger
        for trigger in triggers
        if trigger.qualifies_candidate is True and trigger.present_at_first_knowledge is True
    ]
    families = {trigger.evidence_family for trigger in qualifying}
    composition = _route_composition(families)
    counts: Counter[str] = Counter()
    resolved_dtes = dte_by_trigger_id or {}
    for trigger in qualifying:
        value = resolved_dtes.get(trigger.id)
        if value is None:
            value = resolved_dtes.get(str(trigger.id))
        bucket = _canonical_dte_bucket(value)
        if bucket is not None:
            counts[bucket.value] += 1
    return CohortMetadata(
        has_radar="RADAR_EVENT" in families,
        has_expiry_activity="EXPIRY_ACTIVITY" in families,
        has_contract_persistence="CONTRACT_PERSISTENCE" in families,
        route_composition=composition,
        qualifying_trigger_count=len(qualifying),
        dte_bucket_counts=dict(sorted(counts.items())),
    )


def build_research_sample_foundation(
    candidate: ProductCandidate,
    scan_run: ScanRun,
    baseline: ProductCandidateContext | None,
    *,
    dte_by_trigger_id: Mapping[UUID | str, int | str | DteBucket | None] | None = None,
    same_day_close_known_as_of_first_knowledge: bool = False,
) -> ResearchSampleFoundation:
    """Build one foundation record for one occurrence without writing or filtering it."""

    invalid_reason = _sample_invalid_reason(candidate, scan_run, baseline)
    validity = (
        ResearchSampleValidity.INVALID_SAMPLE
        if invalid_reason is not None
        else ResearchSampleValidity.VALID
    )
    origin = classify_scan_origin(scan_run.trigger)
    sessions = map_forward_sessions(
        candidate.candidate_first_knowledge_at,
        same_day_close_known_as_of_first_knowledge=(same_day_close_known_as_of_first_knowledge),
    )
    cohort = cohort_metadata(
        candidate.triggers,
        dte_by_trigger_id=dte_by_trigger_id,
    )
    if cohort.qualifying_trigger_count == 0 and invalid_reason is None:
        invalid_reason = "NO_QUALIFYING_FIRST_KNOWLEDGE_TRIGGER"
        validity = ResearchSampleValidity.INVALID_SAMPLE
    return ResearchSampleFoundation(
        product_candidate_id=candidate.id,
        frozen_baseline_context_id=baseline.id if baseline is not None else None,
        scan_run_id=scan_run.id,
        ticker=candidate.ticker,
        candidate_first_knowledge_at=ensure_utc(candidate.candidate_first_knowledge_at),
        sample_validity_state=validity,
        invalid_reason=invalid_reason,
        run_origin=origin,
        run_origin_source_trigger=scan_run.trigger,
        primary_research_eligible=(
            validity is ResearchSampleValidity.VALID and primary_research_eligible(origin)
        ),
        sessions=sessions,
        outcome_window_key=outcome_window_key(candidate.ticker, sessions),
        cohort=cohort,
    )


def map_forward_sessions(
    candidate_first_knowledge_at: datetime,
    *,
    same_day_close_known_as_of_first_knowledge: bool = False,
) -> ForwardSessionPlan:
    """Map the locked reference/T+N policy with the exchange-aware XNYS calendar."""

    first_known = ensure_utc(candidate_first_knowledge_at)
    market_day = market_datetime(first_known).date()
    calendar = xcals.get_calendar("XNYS")
    label = pd.Timestamp(market_day.isoformat())
    if calendar.is_session(label):
        official_close = calendar.session_close(label).to_pydatetime()
        if first_known < ensure_utc(official_close):
            reference = calendar.previous_session(label)
            t1 = label
        else:
            reference = (
                label
                if same_day_close_known_as_of_first_knowledge
                else calendar.previous_session(label)
            )
            t1 = calendar.next_session(label)
    else:
        reference = calendar.date_to_session(label, direction="previous")
        t1 = calendar.date_to_session(label, direction="next")
    t3 = _advance_sessions(calendar, t1, 2)
    t5 = _advance_sessions(calendar, t1, 4)
    return ForwardSessionPlan(
        reference_session=reference.date(),
        t1_session=t1.date(),
        t3_session=t3.date(),
        t5_session=t5.date(),
    )


def outcome_window_key(ticker: str, sessions: ForwardSessionPlan) -> str:
    return "|".join(
        (
            ticker.upper(),
            sessions.reference_session.isoformat(),
            sessions.t1_session.isoformat(),
            sessions.t3_session.isoformat(),
            sessions.t5_session.isoformat(),
        )
    )


def maturity_state(
    target_session: date,
    *,
    evaluated_at: datetime,
    close_present: bool,
    sample_valid: bool = True,
    price_basis_provable: bool = True,
) -> MaturityState:
    if not sample_valid or not price_basis_provable:
        return MaturityState.INVALID_SAMPLE
    calendar = xcals.get_calendar("XNYS")
    label = pd.Timestamp(target_session.isoformat())
    if not calendar.is_session(label):
        return MaturityState.INVALID_SAMPLE
    official_close = ensure_utc(calendar.session_close(label).to_pydatetime())
    if ensure_utc(evaluated_at) < official_close:
        return MaturityState.NOT_YET_MATURE
    return MaturityState.MATURE_AVAILABLE if close_present else MaturityState.MATURE_MISSING_DATA


def calculate_close_path_outcome(
    reference: ClosePriceEvidence,
    future_closes: Sequence[ClosePriceEvidence],
) -> OutcomeMetrics | None:
    """Calculate direction-neutral Close-path outcomes or preserve missing as missing."""

    if reference.close is None or not future_closes:
        return None
    if any(item.close is None for item in future_closes):
        return None
    _require_consistent_price_basis([reference, *future_closes])
    reference_value = _decimal(reference.close)
    if reference_value <= 0:
        raise ValueError("Reference Close must be positive")
    closes = [_decimal(item.close) for item in future_closes]
    target = closes[-1]
    return OutcomeMetrics(
        close_return=target / reference_value - Decimal(1),
        max_upside=max(closes) / reference_value - Decimal(1),
        max_downside=min(closes) / reference_value - Decimal(1),
    )


def _sample_invalid_reason(
    candidate: ProductCandidate,
    scan_run: ScanRun,
    baseline: ProductCandidateContext | None,
) -> str | None:
    if candidate.scan_run_id != scan_run.id:
        return "SCAN_RUN_IDENTITY_MISMATCH"
    if baseline is None:
        return "FROZEN_FIRST_KNOWLEDGE_BASELINE_MISSING"
    if baseline.product_candidate_id != candidate.id:
        return "FROZEN_BASELINE_CANDIDATE_MISMATCH"
    if baseline.evaluation_kind != "FIRST_KNOWLEDGE_BASELINE":
        return "FROZEN_BASELINE_KIND_INVALID"
    if ensure_utc(baseline.candidate_first_knowledge_at) != ensure_utc(
        candidate.candidate_first_knowledge_at
    ):
        return "FROZEN_BASELINE_FIRST_KNOWLEDGE_MISMATCH"
    return None


def _route_composition(families: set[str]) -> RouteComposition | None:
    key = frozenset(families)
    return {
        frozenset(("RADAR_EVENT",)): RouteComposition.RADAR_ONLY,
        frozenset(("EXPIRY_ACTIVITY",)): RouteComposition.EXPIRY_ONLY,
        frozenset(("CONTRACT_PERSISTENCE",)): RouteComposition.PERSISTENCE_ONLY,
        frozenset(("RADAR_EVENT", "EXPIRY_ACTIVITY")): RouteComposition.RADAR_EXPIRY,
        frozenset(("RADAR_EVENT", "CONTRACT_PERSISTENCE")): (RouteComposition.RADAR_PERSISTENCE),
        frozenset(("EXPIRY_ACTIVITY", "CONTRACT_PERSISTENCE")): (
            RouteComposition.EXPIRY_PERSISTENCE
        ),
        frozenset(
            ("RADAR_EVENT", "EXPIRY_ACTIVITY", "CONTRACT_PERSISTENCE")
        ): RouteComposition.RADAR_EXPIRY_PERSISTENCE,
    }.get(key)


def _canonical_dte_bucket(value: int | str | DteBucket | None) -> DteBucket | None:
    if isinstance(value, DteBucket):
        return value
    if isinstance(value, int):
        return bucket_for_dte(value)
    if isinstance(value, str):
        try:
            return DteBucket(value)
        except ValueError:
            return None
    return None


def _advance_sessions(calendar: Any, start: pd.Timestamp, count: int) -> pd.Timestamp:
    session = start
    for _ in range(count):
        session = calendar.next_session(session)
    return session


def _require_consistent_price_basis(evidence: Sequence[ClosePriceEvidence]) -> None:
    basis_ids = {item.basis.basis_id for item in evidence}
    statuses = {item.basis.corporate_action_status for item in evidence}
    if statuses != {CorporateActionBasisStatus.PROVEN_CONSISTENT}:
        raise PriceBasisNotProvable("Corporate-action consistency is not proven for every Close")
    if None in basis_ids or "" in basis_ids or len(basis_ids) != 1:
        raise PriceBasisNotProvable(
            "Reference and future Closes do not share one proven price basis"
        )


def _decimal(value: Decimal | int | float | str) -> Decimal:
    try:
        return Decimal(str(value))
    except (InvalidOperation, ValueError) as error:
        raise ValueError("Close must be numeric") from error

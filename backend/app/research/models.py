from __future__ import annotations

import uuid
from datetime import date, datetime
from decimal import Decimal
from typing import Any

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, validates

from app.db.base import Base


class ForwardOutcomeResearchSample(Base):
    """Immutable Stage 9 Research identity for one ProductCandidate occurrence."""

    __tablename__ = "forward_outcome_research_samples"
    __table_args__ = (
        UniqueConstraint(
            "product_candidate_id",
            name="uq_forward_outcome_sample_candidate_occurrence",
        ),
        CheckConstraint(
            "sample_validity_state IN ('VALID', 'INVALID_SAMPLE')",
            name="forward_outcome_sample_validity_allowed",
        ),
        CheckConstraint(
            "(sample_validity_state = 'VALID' "
            "AND frozen_baseline_context_id IS NOT NULL AND invalid_reason IS NULL) OR "
            "(sample_validity_state = 'INVALID_SAMPLE' AND invalid_reason IS NOT NULL)",
            name="forward_outcome_sample_baseline_validity_consistent",
        ),
        CheckConstraint(
            "run_origin IN ('CANONICAL_SCHEDULED_PRODUCTION', 'MANUAL', "
            "'CONTROLLED_OBSERVATION', 'DIAGNOSTIC', 'REMEDIATION', "
            "'DEVELOPER_RERUN', 'OTHER_NON_CANONICAL')",
            name="forward_outcome_run_origin_allowed",
        ),
        CheckConstraint(
            "primary_research_eligible = false OR "
            "(run_origin = 'CANONICAL_SCHEDULED_PRODUCTION' "
            "AND sample_validity_state = 'VALID')",
            name="forward_outcome_primary_eligibility_consistent",
        ),
        CheckConstraint(
            "route_composition IS NULL OR route_composition IN "
            "('RADAR_ONLY', 'EXPIRY_ONLY', 'PERSISTENCE_ONLY', "
            "'RADAR + EXPIRY', 'RADAR + PERSISTENCE', "
            "'EXPIRY + PERSISTENCE', 'RADAR + EXPIRY + PERSISTENCE')",
            name="forward_outcome_route_composition_allowed",
        ),
        CheckConstraint(
            "sample_validity_state = 'INVALID_SAMPLE' OR "
            "(qualifying_trigger_count > 0 AND route_composition IS NOT NULL)",
            name="forward_outcome_valid_sample_has_qualifying_evidence",
        ),
        CheckConstraint(
            "reference_price_policy = 'PRIOR_COMPLETED_REGULAR_CLOSE'",
            name="forward_outcome_reference_policy_locked",
        ),
        CheckConstraint(
            "direction = 'UNRESOLVED'",
            name="forward_outcome_direction_unresolved",
        ),
        CheckConstraint(
            "reference_session < t1_session AND t1_session < t3_session "
            "AND t3_session < t5_session",
            name="forward_outcome_session_order",
        ),
        CheckConstraint(
            "price_basis_capability IN ('PROVEN_CONSISTENT', 'RAW_UNADJUSTED', "
            "'UNCONFIRMED', 'MISMATCHED')",
            name="forward_outcome_price_basis_capability_allowed",
        ),
        CheckConstraint(
            "price_basis_capability <> 'PROVEN_CONSISTENT' OR price_basis_name IS NOT NULL",
            name="forward_outcome_proven_basis_named",
        ),
        Index(
            "ix_forward_outcome_primary_window",
            "primary_research_eligible",
            "outcome_window_key",
        ),
        Index(
            "ix_forward_outcome_ticker_first_known",
            "ticker",
            "candidate_first_knowledge_at",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    product_candidate_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("product_candidates.id"), nullable=False
    )
    frozen_baseline_context_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("product_candidate_contexts.id")
    )
    scan_run_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("scan_runs.id"), nullable=False)
    ticker: Mapped[str] = mapped_column(String(16), nullable=False)
    candidate_first_knowledge_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    sample_validity_state: Mapped[str] = mapped_column(String(24), nullable=False)
    invalid_reason: Mapped[str | None] = mapped_column(String(96))
    run_origin: Mapped[str] = mapped_column(String(48), nullable=False)
    run_origin_source_trigger: Mapped[str] = mapped_column(String(32), nullable=False)
    run_origin_classification_version: Mapped[str] = mapped_column(String(64), nullable=False)
    primary_research_eligible: Mapped[bool] = mapped_column(Boolean, nullable=False)
    has_radar: Mapped[bool] = mapped_column(Boolean, nullable=False)
    has_expiry_activity: Mapped[bool] = mapped_column(Boolean, nullable=False)
    has_contract_persistence: Mapped[bool] = mapped_column(Boolean, nullable=False)
    route_composition: Mapped[str | None] = mapped_column(String(64))
    qualifying_trigger_count: Mapped[int] = mapped_column(Integer, nullable=False)
    dte_bucket_counts: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict)
    reference_price_policy: Mapped[str] = mapped_column(String(64), nullable=False)
    reference_session: Mapped[date] = mapped_column(Date, nullable=False)
    t1_session: Mapped[date] = mapped_column(Date, nullable=False)
    t3_session: Mapped[date] = mapped_column(Date, nullable=False)
    t5_session: Mapped[date] = mapped_column(Date, nullable=False)
    outcome_window_key: Mapped[str] = mapped_column(String(128), nullable=False)
    price_basis_capability: Mapped[str] = mapped_column(String(32), nullable=False)
    price_basis_name: Mapped[str | None] = mapped_column(String(64))
    price_basis_provenance: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict)
    outcome_methodology_version: Mapped[str] = mapped_column(String(64), nullable=False)
    direction: Mapped[str] = mapped_column(String(16), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    @validates(
        "product_candidate_id",
        "frozen_baseline_context_id",
        "scan_run_id",
        "ticker",
        "candidate_first_knowledge_at",
        "sample_validity_state",
        "invalid_reason",
        "run_origin",
        "run_origin_source_trigger",
        "run_origin_classification_version",
        "primary_research_eligible",
        "has_radar",
        "has_expiry_activity",
        "has_contract_persistence",
        "route_composition",
        "qualifying_trigger_count",
        "dte_bucket_counts",
        "reference_price_policy",
        "reference_session",
        "t1_session",
        "t3_session",
        "t5_session",
        "outcome_window_key",
        "price_basis_capability",
        "price_basis_name",
        "price_basis_provenance",
        "outcome_methodology_version",
        "direction",
    )
    def _validate_immutable_research_identity(self, key: str, value: Any) -> Any:
        if key in self.__dict__ and self.__dict__[key] != value:
            raise ValueError(f"ForwardOutcomeResearchSample.{key} is immutable")
        return value


class ForwardOutcomeMeasurement(Base):
    """Append-only, versioned Stage 9B-compatible outcome row; Stage 9A writes none."""

    __tablename__ = "forward_outcome_measurements"
    __table_args__ = (
        UniqueConstraint(
            "research_sample_id",
            "horizon_sessions",
            "outcome_methodology_version",
            "calculation_revision",
            name="uq_forward_outcome_measurement_revision",
        ),
        CheckConstraint(
            "horizon_sessions IN (1, 3, 5)",
            name="forward_outcome_horizon_allowed",
        ),
        CheckConstraint(
            "maturity_state IN ('NOT_YET_MATURE', 'MATURE_AVAILABLE', "
            "'MATURE_MISSING_DATA', 'INVALID_SAMPLE', "
            "'CORPORATE_ACTION_CONTAMINATED')",
            name="forward_outcome_maturity_allowed",
        ),
        CheckConstraint(
            "direction = 'UNRESOLVED'",
            name="forward_outcome_measurement_direction_unresolved",
        ),
        CheckConstraint(
            "calculation_revision > 0",
            name="forward_outcome_calculation_revision_positive",
        ),
        CheckConstraint(
            "price_basis_status IN ('PROVEN_CONSISTENT', 'RAW_UNADJUSTED', "
            "'UNCONFIRMED', 'MISMATCHED')",
            name="forward_outcome_measurement_basis_status_allowed",
        ),
        CheckConstraint(
            "(maturity_state = 'MATURE_AVAILABLE' "
            "AND reference_close IS NOT NULL AND target_close IS NOT NULL "
            "AND close_return IS NOT NULL AND max_upside IS NOT NULL "
            "AND max_downside IS NOT NULL "
            "AND price_basis_status IN ('PROVEN_CONSISTENT', 'RAW_UNADJUSTED') "
            "AND price_basis_name IS NOT NULL) OR "
            "(maturity_state <> 'MATURE_AVAILABLE' "
            "AND close_return IS NULL AND max_upside IS NULL "
            "AND max_downside IS NULL)",
            name="forward_outcome_values_match_maturity",
        ),
        CheckConstraint(
            "primary_descriptive_eligible = false OR "
            "maturity_state = 'MATURE_AVAILABLE'",
            name="forward_outcome_primary_descriptive_eligibility",
        ),
        CheckConstraint(
            "corporate_action_state IN "
            "('NO_KNOWN_PRICE_SCALE_EVENT_RECORDED', "
            "'KNOWN_PRICE_SCALE_EVENT', 'NOT_APPLICABLE')",
            name="forward_outcome_corporate_action_state_allowed",
        ),
        CheckConstraint(
            "maturity_state <> 'CORPORATE_ACTION_CONTAMINATED' OR "
            "(corporate_action_state = 'KNOWN_PRICE_SCALE_EVENT' "
            "AND primary_descriptive_eligible = false)",
            name="forward_outcome_contamination_quarantined",
        ),
        Index(
            "ix_forward_outcome_measurement_sample_horizon",
            "research_sample_id",
            "horizon_sessions",
            "calculated_at",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    research_sample_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("forward_outcome_research_samples.id"), nullable=False
    )
    horizon_sessions: Mapped[int] = mapped_column(Integer, nullable=False)
    target_session: Mapped[date] = mapped_column(Date, nullable=False)
    maturity_state: Mapped[str] = mapped_column(String(32), nullable=False)
    reference_close: Mapped[Decimal | None] = mapped_column(Numeric(24, 10))
    target_close: Mapped[Decimal | None] = mapped_column(Numeric(24, 10))
    close_return: Mapped[Decimal | None] = mapped_column(Numeric(24, 12))
    max_upside: Mapped[Decimal | None] = mapped_column(Numeric(24, 12))
    max_downside: Mapped[Decimal | None] = mapped_column(Numeric(24, 12))
    price_basis_status: Mapped[str] = mapped_column(String(32), nullable=False)
    price_basis_name: Mapped[str | None] = mapped_column(String(64))
    price_basis_provenance: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict)
    input_bar_evidence: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict)
    primary_descriptive_eligible: Mapped[bool] = mapped_column(Boolean, nullable=False)
    corporate_action_state: Mapped[str] = mapped_column(String(48), nullable=False)
    corporate_action_event_ids: Mapped[list[str]] = mapped_column(JSONB, default=list)
    outcome_methodology_version: Mapped[str] = mapped_column(String(64), nullable=False)
    calculation_revision: Mapped[int] = mapped_column(Integer, nullable=False)
    semantic_fingerprint: Mapped[str] = mapped_column(String(64), nullable=False)
    supersedes_measurement_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("forward_outcome_measurements.id")
    )
    calculated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    direction: Mapped[str] = mapped_column(String(16), nullable=False)
    provenance: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    @validates(
        "research_sample_id",
        "horizon_sessions",
        "target_session",
        "maturity_state",
        "reference_close",
        "target_close",
        "close_return",
        "max_upside",
        "max_downside",
        "price_basis_status",
        "price_basis_name",
        "price_basis_provenance",
        "input_bar_evidence",
        "primary_descriptive_eligible",
        "corporate_action_state",
        "corporate_action_event_ids",
        "outcome_methodology_version",
        "calculation_revision",
        "semantic_fingerprint",
        "supersedes_measurement_id",
        "calculated_at",
        "direction",
        "provenance",
    )
    def _validate_immutable_measurement(self, key: str, value: Any) -> Any:
        if key in self.__dict__ and self.__dict__[key] != value:
            raise ValueError(f"ForwardOutcomeMeasurement.{key} is immutable")
        return value


class ForwardOutcomeCorporateAction(Base):
    """Append-only known price-scale-changing event evidence for Research."""

    __tablename__ = "forward_outcome_corporate_actions"
    __table_args__ = (
        UniqueConstraint(
            "ticker",
            "effective_session",
            "action_type",
            "source_name",
            "source_reference",
            "record_revision",
            name="uq_forward_outcome_corporate_action_revision",
        ),
        CheckConstraint(
            "action_type IN ('SPLIT', 'REVERSE_SPLIT', 'STOCK_DIVIDEND', "
            "'SPIN_OFF', 'SPECIAL_DISTRIBUTION', 'OTHER_PRICE_SCALE_CHANGING')",
            name="forward_outcome_corporate_action_type_allowed",
        ),
        CheckConstraint(
            "record_status IN ('KNOWN', 'RETRACTED')",
            name="forward_outcome_corporate_action_status_allowed",
        ),
        CheckConstraint(
            "record_revision > 0",
            name="forward_outcome_corporate_action_revision_positive",
        ),
        Index(
            "ix_forward_outcome_corporate_action_ticker_session",
            "ticker",
            "effective_session",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    ticker: Mapped[str] = mapped_column(String(16), nullable=False)
    effective_session: Mapped[date] = mapped_column(Date, nullable=False)
    action_type: Mapped[str] = mapped_column(String(40), nullable=False)
    price_scale_changing: Mapped[bool] = mapped_column(Boolean, nullable=False)
    record_status: Mapped[str] = mapped_column(String(16), nullable=False)
    source_name: Mapped[str] = mapped_column(String(64), nullable=False)
    source_reference: Mapped[str] = mapped_column(String(255), nullable=False)
    record_revision: Mapped[int] = mapped_column(Integer, nullable=False)
    provenance: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict)
    recorded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    @validates(
        "ticker",
        "effective_session",
        "action_type",
        "price_scale_changing",
        "record_status",
        "source_name",
        "source_reference",
        "record_revision",
        "provenance",
        "recorded_at",
    )
    def _validate_immutable_corporate_action(self, key: str, value: Any) -> Any:
        if key in self.__dict__ and self.__dict__[key] != value:
            raise ValueError(f"ForwardOutcomeCorporateAction.{key} is immutable")
        return value

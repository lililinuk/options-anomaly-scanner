"""Add Stage 9A Forward Outcome Research foundation.

Revision ID: 20260827_0018
Revises: 20260818_0017
"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "20260827_0018"
down_revision: str | None = "20260818_0017"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

SAMPLE_TABLE = "forward_outcome_research_samples"
MEASUREMENT_TABLE = "forward_outcome_measurements"


def upgrade() -> None:
    op.create_table(
        SAMPLE_TABLE,
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("product_candidate_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "frozen_baseline_context_id",
            postgresql.UUID(as_uuid=True),
            nullable=True,
        ),
        sa.Column("scan_run_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("ticker", sa.String(length=16), nullable=False),
        sa.Column(
            "candidate_first_knowledge_at",
            sa.DateTime(timezone=True),
            nullable=False,
        ),
        sa.Column("sample_validity_state", sa.String(length=24), nullable=False),
        sa.Column("invalid_reason", sa.String(length=96), nullable=True),
        sa.Column("run_origin", sa.String(length=48), nullable=False),
        sa.Column("run_origin_source_trigger", sa.String(length=32), nullable=False),
        sa.Column(
            "run_origin_classification_version",
            sa.String(length=64),
            nullable=False,
        ),
        sa.Column("primary_research_eligible", sa.Boolean(), nullable=False),
        sa.Column("has_radar", sa.Boolean(), nullable=False),
        sa.Column("has_expiry_activity", sa.Boolean(), nullable=False),
        sa.Column("has_contract_persistence", sa.Boolean(), nullable=False),
        sa.Column("route_composition", sa.String(length=64), nullable=True),
        sa.Column("qualifying_trigger_count", sa.Integer(), nullable=False),
        sa.Column(
            "dte_bucket_counts",
            postgresql.JSONB(),
            server_default=sa.text("'{}'::jsonb"),
            nullable=False,
        ),
        sa.Column("reference_price_policy", sa.String(length=64), nullable=False),
        sa.Column("reference_session", sa.Date(), nullable=False),
        sa.Column("t1_session", sa.Date(), nullable=False),
        sa.Column("t3_session", sa.Date(), nullable=False),
        sa.Column("t5_session", sa.Date(), nullable=False),
        sa.Column("outcome_window_key", sa.String(length=128), nullable=False),
        sa.Column("price_basis_capability", sa.String(length=32), nullable=False),
        sa.Column("price_basis_name", sa.String(length=64), nullable=True),
        sa.Column(
            "price_basis_provenance",
            postgresql.JSONB(),
            server_default=sa.text("'{}'::jsonb"),
            nullable=False,
        ),
        sa.Column(
            "outcome_methodology_version",
            sa.String(length=64),
            nullable=False,
        ),
        sa.Column("direction", sa.String(length=16), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint(
            "sample_validity_state IN ('VALID', 'INVALID_SAMPLE')",
            name="forward_outcome_sample_validity_allowed",
        ),
        sa.CheckConstraint(
            "(sample_validity_state = 'VALID' "
            "AND frozen_baseline_context_id IS NOT NULL AND invalid_reason IS NULL) OR "
            "(sample_validity_state = 'INVALID_SAMPLE' AND invalid_reason IS NOT NULL)",
            name="forward_outcome_sample_baseline_validity_consistent",
        ),
        sa.CheckConstraint(
            "run_origin IN ('CANONICAL_SCHEDULED_PRODUCTION', 'MANUAL', "
            "'CONTROLLED_OBSERVATION', 'DIAGNOSTIC', 'REMEDIATION', "
            "'DEVELOPER_RERUN', 'OTHER_NON_CANONICAL')",
            name="forward_outcome_run_origin_allowed",
        ),
        sa.CheckConstraint(
            "primary_research_eligible = false OR "
            "(run_origin = 'CANONICAL_SCHEDULED_PRODUCTION' "
            "AND sample_validity_state = 'VALID')",
            name="forward_outcome_primary_eligibility_consistent",
        ),
        sa.CheckConstraint(
            "route_composition IS NULL OR route_composition IN "
            "('RADAR_ONLY', 'EXPIRY_ONLY', 'PERSISTENCE_ONLY', "
            "'RADAR + EXPIRY', 'RADAR + PERSISTENCE', "
            "'EXPIRY + PERSISTENCE', 'RADAR + EXPIRY + PERSISTENCE')",
            name="forward_outcome_route_composition_allowed",
        ),
        sa.CheckConstraint(
            "sample_validity_state = 'INVALID_SAMPLE' OR "
            "(qualifying_trigger_count > 0 AND route_composition IS NOT NULL)",
            name="forward_outcome_valid_sample_has_qualifying_evidence",
        ),
        sa.CheckConstraint(
            "reference_price_policy = 'PRIOR_COMPLETED_REGULAR_CLOSE'",
            name="forward_outcome_reference_policy_locked",
        ),
        sa.CheckConstraint(
            "direction = 'UNRESOLVED'",
            name="forward_outcome_direction_unresolved",
        ),
        sa.CheckConstraint(
            "reference_session < t1_session AND t1_session < t3_session "
            "AND t3_session < t5_session",
            name="forward_outcome_session_order",
        ),
        sa.CheckConstraint(
            "price_basis_capability IN ('PROVEN_CONSISTENT', 'UNCONFIRMED', 'MISMATCHED')",
            name="forward_outcome_price_basis_capability_allowed",
        ),
        sa.CheckConstraint(
            "price_basis_capability <> 'PROVEN_CONSISTENT' OR price_basis_name IS NOT NULL",
            name="forward_outcome_proven_basis_named",
        ),
        sa.ForeignKeyConstraint(["product_candidate_id"], ["product_candidates.id"]),
        sa.ForeignKeyConstraint(
            ["frozen_baseline_context_id"],
            ["product_candidate_contexts.id"],
        ),
        sa.ForeignKeyConstraint(["scan_run_id"], ["scan_runs.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "product_candidate_id",
            name="uq_forward_outcome_sample_candidate_occurrence",
        ),
    )
    op.create_index(
        "ix_forward_outcome_primary_window",
        SAMPLE_TABLE,
        ["primary_research_eligible", "outcome_window_key"],
    )
    op.create_index(
        "ix_forward_outcome_ticker_first_known",
        SAMPLE_TABLE,
        ["ticker", "candidate_first_knowledge_at"],
    )

    op.create_table(
        MEASUREMENT_TABLE,
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("research_sample_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("horizon_sessions", sa.Integer(), nullable=False),
        sa.Column("target_session", sa.Date(), nullable=False),
        sa.Column("maturity_state", sa.String(length=32), nullable=False),
        sa.Column("reference_close", sa.Numeric(precision=24, scale=10), nullable=True),
        sa.Column("target_close", sa.Numeric(precision=24, scale=10), nullable=True),
        sa.Column("close_return", sa.Numeric(precision=24, scale=12), nullable=True),
        sa.Column("max_upside", sa.Numeric(precision=24, scale=12), nullable=True),
        sa.Column("max_downside", sa.Numeric(precision=24, scale=12), nullable=True),
        sa.Column("price_basis_status", sa.String(length=32), nullable=False),
        sa.Column("price_basis_name", sa.String(length=64), nullable=True),
        sa.Column(
            "price_basis_provenance",
            postgresql.JSONB(),
            server_default=sa.text("'{}'::jsonb"),
            nullable=False,
        ),
        sa.Column(
            "input_bar_evidence",
            postgresql.JSONB(),
            server_default=sa.text("'{}'::jsonb"),
            nullable=False,
        ),
        sa.Column(
            "outcome_methodology_version",
            sa.String(length=64),
            nullable=False,
        ),
        sa.Column("calculation_revision", sa.Integer(), nullable=False),
        sa.Column("calculated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("direction", sa.String(length=16), nullable=False),
        sa.Column(
            "provenance",
            postgresql.JSONB(),
            server_default=sa.text("'{}'::jsonb"),
            nullable=False,
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint(
            "horizon_sessions IN (1, 3, 5)",
            name="forward_outcome_horizon_allowed",
        ),
        sa.CheckConstraint(
            "maturity_state IN ('NOT_YET_MATURE', 'MATURE_AVAILABLE', "
            "'MATURE_MISSING_DATA', 'INVALID_SAMPLE')",
            name="forward_outcome_maturity_allowed",
        ),
        sa.CheckConstraint(
            "direction = 'UNRESOLVED'",
            name="forward_outcome_measurement_direction_unresolved",
        ),
        sa.CheckConstraint(
            "calculation_revision > 0",
            name="forward_outcome_calculation_revision_positive",
        ),
        sa.CheckConstraint(
            "price_basis_status IN ('PROVEN_CONSISTENT', 'UNCONFIRMED', 'MISMATCHED')",
            name="forward_outcome_measurement_basis_status_allowed",
        ),
        sa.CheckConstraint(
            "(maturity_state = 'MATURE_AVAILABLE' "
            "AND reference_close IS NOT NULL AND target_close IS NOT NULL "
            "AND close_return IS NOT NULL AND max_upside IS NOT NULL "
            "AND max_downside IS NOT NULL "
            "AND price_basis_status = 'PROVEN_CONSISTENT' "
            "AND price_basis_name IS NOT NULL) OR "
            "(maturity_state <> 'MATURE_AVAILABLE' "
            "AND close_return IS NULL AND max_upside IS NULL "
            "AND max_downside IS NULL)",
            name="forward_outcome_values_match_maturity",
        ),
        sa.ForeignKeyConstraint(
            ["research_sample_id"],
            ["forward_outcome_research_samples.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "research_sample_id",
            "horizon_sessions",
            "outcome_methodology_version",
            "calculation_revision",
            name="uq_forward_outcome_measurement_revision",
        ),
    )
    op.create_index(
        "ix_forward_outcome_measurement_sample_horizon",
        MEASUREMENT_TABLE,
        ["research_sample_id", "horizon_sessions", "calculated_at"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_forward_outcome_measurement_sample_horizon",
        table_name=MEASUREMENT_TABLE,
    )
    op.drop_table(MEASUREMENT_TABLE)
    op.drop_index("ix_forward_outcome_ticker_first_known", table_name=SAMPLE_TABLE)
    op.drop_index("ix_forward_outcome_primary_window", table_name=SAMPLE_TABLE)
    op.drop_table(SAMPLE_TABLE)

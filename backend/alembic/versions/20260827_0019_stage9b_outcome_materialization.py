"""Add Stage 9B raw outcome materialization and corporate-action quarantine.

Revision ID: 20260827_0019
Revises: 20260827_0018
"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "20260827_0019"
down_revision: str | None = "20260827_0018"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

SAMPLE_TABLE = "forward_outcome_research_samples"
MEASUREMENT_TABLE = "forward_outcome_measurements"
ACTION_TABLE = "forward_outcome_corporate_actions"


def upgrade() -> None:
    op.drop_constraint(
        op.f(
            "ck_forward_outcome_research_samples_"
            "forward_outcome_price_basis_capability_allowed"
        ),
        SAMPLE_TABLE,
        type_="check",
    )
    op.create_check_constraint(
        "forward_outcome_price_basis_capability_allowed",
        SAMPLE_TABLE,
        "price_basis_capability IN ('PROVEN_CONSISTENT', 'RAW_UNADJUSTED', "
        "'UNCONFIRMED', 'MISMATCHED')",
    )

    op.drop_constraint(
        op.f(
            "ck_forward_outcome_measurements_"
            "forward_outcome_maturity_allowed"
        ),
        MEASUREMENT_TABLE,
        type_="check",
    )
    op.drop_constraint(
        op.f(
            "ck_forward_outcome_measurements_"
            "forward_outcome_measurement_basis_status_allowed"
        ),
        MEASUREMENT_TABLE,
        type_="check",
    )
    op.drop_constraint(
        op.f(
            "ck_forward_outcome_measurements_"
            "forward_outcome_values_match_maturity"
        ),
        MEASUREMENT_TABLE,
        type_="check",
    )

    op.add_column(
        MEASUREMENT_TABLE,
        sa.Column(
            "primary_descriptive_eligible",
            sa.Boolean(),
            server_default=sa.false(),
            nullable=False,
        ),
    )
    op.add_column(
        MEASUREMENT_TABLE,
        sa.Column(
            "corporate_action_state",
            sa.String(length=48),
            server_default="NOT_APPLICABLE",
            nullable=False,
        ),
    )
    op.add_column(
        MEASUREMENT_TABLE,
        sa.Column(
            "corporate_action_event_ids",
            postgresql.JSONB(),
            server_default=sa.text("'[]'::jsonb"),
            nullable=False,
        ),
    )
    op.add_column(
        MEASUREMENT_TABLE,
        sa.Column(
            "semantic_fingerprint",
            sa.String(length=64),
            server_default="0000000000000000000000000000000000000000000000000000000000000000",
            nullable=False,
        ),
    )
    op.add_column(
        MEASUREMENT_TABLE,
        sa.Column(
            "supersedes_measurement_id",
            postgresql.UUID(as_uuid=True),
            nullable=True,
        ),
    )
    op.create_foreign_key(
        "fk_forward_outcome_measurements_supersedes",
        MEASUREMENT_TABLE,
        MEASUREMENT_TABLE,
        ["supersedes_measurement_id"],
        ["id"],
    )

    op.create_check_constraint(
        "forward_outcome_maturity_allowed",
        MEASUREMENT_TABLE,
        "maturity_state IN ('NOT_YET_MATURE', 'MATURE_AVAILABLE', "
        "'MATURE_MISSING_DATA', 'INVALID_SAMPLE', "
        "'CORPORATE_ACTION_CONTAMINATED')",
    )
    op.create_check_constraint(
        "forward_outcome_measurement_basis_status_allowed",
        MEASUREMENT_TABLE,
        "price_basis_status IN ('PROVEN_CONSISTENT', 'RAW_UNADJUSTED', "
        "'UNCONFIRMED', 'MISMATCHED')",
    )
    op.create_check_constraint(
        "forward_outcome_values_match_maturity",
        MEASUREMENT_TABLE,
        "(maturity_state = 'MATURE_AVAILABLE' "
        "AND reference_close IS NOT NULL AND target_close IS NOT NULL "
        "AND close_return IS NOT NULL AND max_upside IS NOT NULL "
        "AND max_downside IS NOT NULL "
        "AND price_basis_status IN ('PROVEN_CONSISTENT', 'RAW_UNADJUSTED') "
        "AND price_basis_name IS NOT NULL) OR "
        "(maturity_state <> 'MATURE_AVAILABLE' "
        "AND close_return IS NULL AND max_upside IS NULL "
        "AND max_downside IS NULL)",
    )
    op.create_check_constraint(
        "forward_outcome_primary_descriptive_eligibility",
        MEASUREMENT_TABLE,
        "primary_descriptive_eligible = false OR "
        "maturity_state = 'MATURE_AVAILABLE'",
    )
    op.create_check_constraint(
        "forward_outcome_corporate_action_state_allowed",
        MEASUREMENT_TABLE,
        "corporate_action_state IN "
        "('NO_KNOWN_PRICE_SCALE_EVENT_RECORDED', "
        "'KNOWN_PRICE_SCALE_EVENT', 'NOT_APPLICABLE')",
    )
    op.create_check_constraint(
        "forward_outcome_contamination_quarantined",
        MEASUREMENT_TABLE,
        "maturity_state <> 'CORPORATE_ACTION_CONTAMINATED' OR "
        "(corporate_action_state = 'KNOWN_PRICE_SCALE_EVENT' "
        "AND primary_descriptive_eligible = false)",
    )
    op.alter_column(
        MEASUREMENT_TABLE,
        "primary_descriptive_eligible",
        server_default=None,
    )
    op.alter_column(MEASUREMENT_TABLE, "corporate_action_state", server_default=None)
    op.alter_column(MEASUREMENT_TABLE, "corporate_action_event_ids", server_default=None)
    op.alter_column(MEASUREMENT_TABLE, "semantic_fingerprint", server_default=None)

    op.create_table(
        ACTION_TABLE,
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("ticker", sa.String(length=16), nullable=False),
        sa.Column("effective_session", sa.Date(), nullable=False),
        sa.Column("action_type", sa.String(length=40), nullable=False),
        sa.Column("price_scale_changing", sa.Boolean(), nullable=False),
        sa.Column("record_status", sa.String(length=16), nullable=False),
        sa.Column("source_name", sa.String(length=64), nullable=False),
        sa.Column("source_reference", sa.String(length=255), nullable=False),
        sa.Column("record_revision", sa.Integer(), nullable=False),
        sa.Column(
            "provenance",
            postgresql.JSONB(),
            server_default=sa.text("'{}'::jsonb"),
            nullable=False,
        ),
        sa.Column("recorded_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint(
            "action_type IN ('SPLIT', 'REVERSE_SPLIT', 'STOCK_DIVIDEND', "
            "'SPIN_OFF', 'SPECIAL_DISTRIBUTION', 'OTHER_PRICE_SCALE_CHANGING')",
            name="forward_outcome_corporate_action_type_allowed",
        ),
        sa.CheckConstraint(
            "record_status IN ('KNOWN', 'RETRACTED')",
            name="forward_outcome_corporate_action_status_allowed",
        ),
        sa.CheckConstraint(
            "record_revision > 0",
            name="forward_outcome_corporate_action_revision_positive",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "ticker",
            "effective_session",
            "action_type",
            "source_name",
            "source_reference",
            "record_revision",
            name="uq_forward_outcome_corporate_action_revision",
        ),
    )
    op.create_index(
        "ix_forward_outcome_corporate_action_ticker_session",
        ACTION_TABLE,
        ["ticker", "effective_session"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_forward_outcome_corporate_action_ticker_session",
        table_name=ACTION_TABLE,
    )
    op.drop_table(ACTION_TABLE)

    op.drop_constraint(
        op.f(
            "ck_forward_outcome_measurements_"
            "forward_outcome_contamination_quarantined"
        ),
        MEASUREMENT_TABLE,
        type_="check",
    )
    op.drop_constraint(
        op.f(
            "ck_forward_outcome_measurements_"
            "forward_outcome_corporate_action_state_allowed"
        ),
        MEASUREMENT_TABLE,
        type_="check",
    )
    op.drop_constraint(
        op.f(
            "ck_forward_outcome_measurements_"
            "forward_outcome_primary_descriptive_eligibility"
        ),
        MEASUREMENT_TABLE,
        type_="check",
    )
    op.drop_constraint(
        op.f(
            "ck_forward_outcome_measurements_"
            "forward_outcome_values_match_maturity"
        ),
        MEASUREMENT_TABLE,
        type_="check",
    )
    op.drop_constraint(
        op.f(
            "ck_forward_outcome_measurements_"
            "forward_outcome_measurement_basis_status_allowed"
        ),
        MEASUREMENT_TABLE,
        type_="check",
    )
    op.drop_constraint(
        op.f(
            "ck_forward_outcome_measurements_"
            "forward_outcome_maturity_allowed"
        ),
        MEASUREMENT_TABLE,
        type_="check",
    )
    op.drop_constraint(
        "fk_forward_outcome_measurements_supersedes",
        MEASUREMENT_TABLE,
        type_="foreignkey",
    )
    op.drop_column(MEASUREMENT_TABLE, "supersedes_measurement_id")
    op.drop_column(MEASUREMENT_TABLE, "semantic_fingerprint")
    op.drop_column(MEASUREMENT_TABLE, "corporate_action_event_ids")
    op.drop_column(MEASUREMENT_TABLE, "corporate_action_state")
    op.drop_column(MEASUREMENT_TABLE, "primary_descriptive_eligible")

    op.create_check_constraint(
        "forward_outcome_maturity_allowed",
        MEASUREMENT_TABLE,
        "maturity_state IN ('NOT_YET_MATURE', 'MATURE_AVAILABLE', "
        "'MATURE_MISSING_DATA', 'INVALID_SAMPLE')",
    )
    op.create_check_constraint(
        "forward_outcome_measurement_basis_status_allowed",
        MEASUREMENT_TABLE,
        "price_basis_status IN ('PROVEN_CONSISTENT', 'UNCONFIRMED', 'MISMATCHED')",
    )
    op.create_check_constraint(
        "forward_outcome_values_match_maturity",
        MEASUREMENT_TABLE,
        "(maturity_state = 'MATURE_AVAILABLE' "
        "AND reference_close IS NOT NULL AND target_close IS NOT NULL "
        "AND close_return IS NOT NULL AND max_upside IS NOT NULL "
        "AND max_downside IS NOT NULL "
        "AND price_basis_status = 'PROVEN_CONSISTENT' "
        "AND price_basis_name IS NOT NULL) OR "
        "(maturity_state <> 'MATURE_AVAILABLE' "
        "AND close_return IS NULL AND max_upside IS NULL "
        "AND max_downside IS NULL)",
    )

    op.drop_constraint(
        op.f(
            "ck_forward_outcome_research_samples_"
            "forward_outcome_price_basis_capability_allowed"
        ),
        SAMPLE_TABLE,
        type_="check",
    )
    op.create_check_constraint(
        "forward_outcome_price_basis_capability_allowed",
        SAMPLE_TABLE,
        "price_basis_capability IN ('PROVEN_CONSISTENT', 'UNCONFIRMED', 'MISMATCHED')",
    )

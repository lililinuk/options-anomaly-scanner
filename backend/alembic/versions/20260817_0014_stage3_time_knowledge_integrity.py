"""Add Stage 3 time and knowledge integrity foundations.

Revision ID: 20260817_0014
Revises: 20260815_0013
"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "20260817_0014"
down_revision: str | None = "20260815_0013"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

CONTEXT_TABLE = "phase2b_ticker_context_snapshots"
EVALUATION_TABLE = "phase2b_candidate_evaluations"


def upgrade() -> None:
    op.add_column(
        CONTEXT_TABLE,
        sa.Column("source_first_received_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        CONTEXT_TABLE,
        sa.Column("freshness_anchor_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        CONTEXT_TABLE,
        sa.Column("source_time_provenance", postgresql.JSONB(), nullable=True),
    )
    op.create_index(
        "ix_phase2b_ticker_context_ticker_freshness",
        CONTEXT_TABLE,
        ["ticker", "freshness_anchor_at"],
    )

    op.add_column(
        EVALUATION_TABLE,
        sa.Column("source_first_received_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        EVALUATION_TABLE,
        sa.Column("source_radar_observation_id", postgresql.UUID(as_uuid=True), nullable=True),
    )
    op.add_column(
        EVALUATION_TABLE,
        sa.Column("evaluation_identity", sa.String(32), nullable=True),
    )
    op.create_foreign_key(
        "fk_phase2b_eval_source_radar",
        EVALUATION_TABLE,
        "oi_change_radar_observations",
        ["source_radar_observation_id"],
        ["id"],
    )
    op.create_check_constraint(
        "eval_identity_allowed",
        EVALUATION_TABLE,
        "evaluation_identity IS NULL OR evaluation_identity IN "
        "('FIRST_KNOWLEDGE_BASELINE', 'REFRESH')",
    )
    op.create_index(
        "ix_phase2b_candidate_symbol_identity",
        EVALUATION_TABLE,
        ["contract_symbol", "evaluation_identity"],
    )


def downgrade() -> None:
    op.drop_index("ix_phase2b_candidate_symbol_identity", table_name=EVALUATION_TABLE)
    op.drop_constraint(
        "eval_identity_allowed",
        EVALUATION_TABLE,
        type_="check",
    )
    op.drop_constraint(
        "fk_phase2b_eval_source_radar",
        EVALUATION_TABLE,
        type_="foreignkey",
    )
    op.drop_column(EVALUATION_TABLE, "evaluation_identity")
    op.drop_column(EVALUATION_TABLE, "source_radar_observation_id")
    op.drop_column(EVALUATION_TABLE, "source_first_received_at")

    op.drop_index("ix_phase2b_ticker_context_ticker_freshness", table_name=CONTEXT_TABLE)
    op.drop_column(CONTEXT_TABLE, "source_time_provenance")
    op.drop_column(CONTEXT_TABLE, "freshness_anchor_at")
    op.drop_column(CONTEXT_TABLE, "source_first_received_at")

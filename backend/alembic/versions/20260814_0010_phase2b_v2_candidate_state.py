"""Phase 2B v2 append-only trade setup research state.

Revision ID: 20260814_0010
Revises: 20260813_0009
"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "20260814_0010"
down_revision: str | None = "20260813_0009"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "phase2b_candidate_states",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "candidate_evaluation_id", postgresql.UUID(as_uuid=True),
            sa.ForeignKey("phase2b_candidate_evaluations.id"), nullable=False,
        ),
        sa.Column(
            "ticker_context_id", postgresql.UUID(as_uuid=True),
            sa.ForeignKey("phase2b_ticker_context_snapshots.id"), nullable=False,
        ),
        sa.Column("contract_symbol", sa.String(64), nullable=False),
        sa.Column("ticker", sa.String(16), nullable=False),
        sa.Column("evaluated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("positioning_state", postgresql.JSONB(), nullable=False),
        sa.Column("price_state", postgresql.JSONB(), nullable=False),
        sa.Column("volatility_state", postgresql.JSONB(), nullable=False),
        sa.Column("dealer_gex_state", postgresql.JSONB(), nullable=False),
        sa.Column("execution_state", postgresql.JSONB(), nullable=False),
        sa.Column("research_readiness", postgresql.JSONB(), nullable=False),
        sa.Column("phase2a_provenance", postgresql.JSONB(), nullable=False),
        sa.Column("direction", sa.String(16), nullable=False),
        sa.Column("specification_version", sa.String(64), nullable=False),
        sa.Column("source_context_specification_version", sa.String(64), nullable=False),
        sa.Column("config_version", sa.String(64), nullable=False),
        sa.Column("config_hash", sa.String(64), nullable=False),
        sa.Column("context_config_version", sa.String(64), nullable=False),
        sa.Column("context_config_hash", sa.String(64), nullable=False),
        sa.Column("topology_rule_version", sa.String(64), nullable=False),
        sa.Column("readiness_rule_version", sa.String(64), nullable=False),
        sa.UniqueConstraint(
            "candidate_evaluation_id", "specification_version",
            name="uq_phase2b_candidate_state_evaluation_spec",
        ),
    )
    op.create_index(
        "ix_phase2b_candidate_state_symbol_evaluated",
        "phase2b_candidate_states", ["contract_symbol", "evaluated_at"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_phase2b_candidate_state_symbol_evaluated",
        table_name="phase2b_candidate_states",
    )
    op.drop_table("phase2b_candidate_states")

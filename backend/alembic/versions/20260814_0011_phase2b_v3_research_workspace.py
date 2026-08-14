"""Phase 2B v3 append-only research workspace and GEX structure.

Revision ID: 20260814_0011
Revises: 20260814_0010
"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "20260814_0011"
down_revision: str | None = "20260814_0010"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "phase2b_v3_research_workspaces",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "source_v2_state_id", postgresql.UUID(as_uuid=True),
            sa.ForeignKey("phase2b_candidate_states.id"), nullable=False,
        ),
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
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("contract_identity", postgresql.JSONB(), nullable=False),
        sa.Column("opportunity_positioning", postgresql.JSONB(), nullable=False),
        sa.Column("underlying_price", postgresql.JSONB(), nullable=False),
        sa.Column("volatility_context", postgresql.JSONB(), nullable=False),
        sa.Column("dealer_gex_structure", postgresql.JSONB(), nullable=False),
        sa.Column("execution_context", postgresql.JSONB(), nullable=False),
        sa.Column("provenance", postgresql.JSONB(), nullable=False),
        sa.Column("specification_version", sa.String(64), nullable=False),
        sa.Column("config_version", sa.String(64), nullable=False),
        sa.Column("config_hash", sa.String(64), nullable=False),
        sa.Column("primary_floor_rule_version", sa.String(64), nullable=False),
        sa.Column("primary_upper_node_rule_version", sa.String(64), nullable=False),
        sa.Column("below_floor_path_rule_version", sa.String(64), nullable=False),
        sa.Column("adjacent_expiry_rule_version", sa.String(64), nullable=False),
        sa.UniqueConstraint(
            "source_v2_state_id", "specification_version",
            name="uq_phase2b_v3_workspace_source_state_spec",
        ),
    )
    op.create_index(
        "ix_phase2b_v3_workspace_symbol_created",
        "phase2b_v3_research_workspaces",
        ["contract_symbol", "created_at"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_phase2b_v3_workspace_symbol_created",
        table_name="phase2b_v3_research_workspaces",
    )
    op.drop_table("phase2b_v3_research_workspaces")

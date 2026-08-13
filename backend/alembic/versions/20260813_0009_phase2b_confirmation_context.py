"""Phase 2B v1 immutable confirmation context.

Revision ID: 20260813_0009
Revises: 20260813_0008
"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "20260813_0009"
down_revision: str | None = "20260813_0008"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "phase2b_ticker_context_snapshots",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("ticker", sa.String(16), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("specification_version", sa.String(64), nullable=False),
        sa.Column("config_version", sa.String(64), nullable=False),
        sa.Column("config_hash", sa.String(64), nullable=False),
        sa.Column("effective_config", postgresql.JSONB(), nullable=False),
        sa.Column("stock_state", postgresql.JSONB(), nullable=False),
        sa.Column("price_context", postgresql.JSONB(), nullable=False),
        sa.Column("iv_rank", postgresql.JSONB(), nullable=False),
        sa.Column("term_structure", postgresql.JSONB(), nullable=False),
        sa.Column("dealer_heatmap", postgresql.JSONB(), nullable=False),
        sa.Column("source_timestamps", postgresql.JSONB(), nullable=False),
        sa.Column("raw_payload_ids", postgresql.JSONB(), nullable=False),
        sa.Column("source_request_ids", postgresql.JSONB(), nullable=False),
        sa.Column("endpoint_statuses", postgresql.JSONB(), nullable=False),
    )
    op.create_index(
        "ix_phase2b_ticker_context_ticker_created",
        "phase2b_ticker_context_snapshots", ["ticker", "created_at"],
    )
    op.create_table(
        "phase2b_candidate_evaluations",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "ticker_context_id", postgresql.UUID(as_uuid=True),
            sa.ForeignKey("phase2b_ticker_context_snapshots.id"), nullable=False,
        ),
        sa.Column("contract_symbol", sa.String(64), nullable=False),
        sa.Column("ticker", sa.String(16), nullable=False),
        sa.Column("expiration", sa.Date(), nullable=False),
        sa.Column("right", sa.String(1), nullable=False),
        sa.Column("strike", sa.Numeric(18, 6), nullable=False),
        sa.Column("dte_at_detection", sa.Integer()),
        sa.Column("evaluated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("trigger_sources", postgresql.JSONB(), nullable=False),
        sa.Column("phase2a_evidence", postgresql.JSONB(), nullable=False),
        sa.Column("strike_location", postgresql.JSONB(), nullable=False),
        sa.Column("volatility_context", postgresql.JSONB(), nullable=False),
        sa.Column("dealer_context", postgresql.JSONB(), nullable=False),
        sa.Column("execution_context", postgresql.JSONB(), nullable=False),
        sa.Column("evidence_states", postgresql.JSONB(), nullable=False),
        sa.Column("source_timestamps", postgresql.JSONB(), nullable=False),
        sa.Column("direction", sa.String(16), nullable=False),
        sa.Column("specification_version", sa.String(64), nullable=False),
        sa.Column("config_version", sa.String(64), nullable=False),
        sa.Column("config_hash", sa.String(64), nullable=False),
        sa.UniqueConstraint(
            "ticker_context_id", "contract_symbol", name="uq_phase2b_context_contract"
        ),
    )
    op.create_index(
        "ix_phase2b_candidate_symbol_evaluated",
        "phase2b_candidate_evaluations", ["contract_symbol", "evaluated_at"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_phase2b_candidate_symbol_evaluated", table_name="phase2b_candidate_evaluations"
    )
    op.drop_table("phase2b_candidate_evaluations")
    op.drop_index(
        "ix_phase2b_ticker_context_ticker_created",
        table_name="phase2b_ticker_context_snapshots",
    )
    op.drop_table("phase2b_ticker_context_snapshots")

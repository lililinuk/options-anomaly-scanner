"""Add Stage 6 Balanced Product Candidate context persistence.

Revision ID: 20260818_0017
Revises: 20260818_0016
"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "20260818_0017"
down_revision: str | None = "20260818_0016"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

CONTEXT_TABLE = "product_candidate_contexts"
DETAIL_TABLE = "anomaly_context_details"


def upgrade() -> None:
    op.create_table(
        CONTEXT_TABLE,
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("product_candidate_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("evaluation_kind", sa.String(length=32), nullable=False),
        sa.Column(
            "candidate_first_knowledge_at",
            sa.DateTime(timezone=True),
            nullable=False,
        ),
        sa.Column("context_evaluated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("price_as_of", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "context_specification_version",
            sa.String(length=64),
            nullable=False,
        ),
        sa.Column("context_config_version", sa.String(length=96), nullable=False),
        sa.Column("context_config_hash", sa.String(length=64), nullable=False),
        sa.Column(
            "price_context",
            postgresql.JSONB(),
            server_default=sa.text("'{}'::jsonb"),
            nullable=False,
        ),
        sa.Column(
            "volatility_context",
            postgresql.JSONB(),
            server_default=sa.text("'{}'::jsonb"),
            nullable=False,
        ),
        sa.Column(
            "dealer_gex_context",
            postgresql.JSONB(),
            server_default=sa.text("'{}'::jsonb"),
            nullable=False,
        ),
        sa.Column(
            "availability",
            postgresql.JSONB(),
            server_default=sa.text("'{}'::jsonb"),
            nullable=False,
        ),
        sa.Column(
            "provenance",
            postgresql.JSONB(),
            server_default=sa.text("'{}'::jsonb"),
            nullable=False,
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint(
            "evaluation_kind IN ('FIRST_KNOWLEDGE_BASELINE', 'REFRESH')",
            name="product_candidate_context_evaluation_kind_allowed",
        ),
        sa.CheckConstraint(
            "context_evaluated_at >= candidate_first_knowledge_at",
            name="product_candidate_context_time_order",
        ),
        sa.ForeignKeyConstraint(["product_candidate_id"], ["product_candidates.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "uq_product_candidate_stage6_baseline",
        CONTEXT_TABLE,
        ["product_candidate_id", "context_specification_version", "context_config_hash"],
        unique=True,
        postgresql_where=sa.text("evaluation_kind = 'FIRST_KNOWLEDGE_BASELINE'"),
    )
    op.create_index(
        "ix_product_candidate_context_history",
        CONTEXT_TABLE,
        ["product_candidate_id", "context_evaluated_at"],
    )

    op.create_table(
        DETAIL_TABLE,
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "product_candidate_context_id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
        ),
        sa.Column(
            "product_candidate_trigger_id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
        ),
        sa.Column("anomaly_entity_type", sa.String(length=16), nullable=False),
        sa.Column("anomaly_identity", sa.String(length=128), nullable=False),
        sa.Column("event_date", sa.Date(), nullable=True),
        sa.Column("expiry_anchor", sa.Date(), nullable=True),
        sa.Column("source_first_received_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("vendor_observed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("local_captured_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("quote_as_of", sa.DateTime(timezone=True), nullable=True),
        sa.Column("contract_snapshot", postgresql.JSONB(), nullable=True),
        sa.Column("expiry_activity_recap", postgresql.JSONB(), nullable=True),
        sa.Column(
            "volatility_context",
            postgresql.JSONB(),
            server_default=sa.text("'{}'::jsonb"),
            nullable=False,
        ),
        sa.Column(
            "dealer_gex_context",
            postgresql.JSONB(),
            server_default=sa.text("'{}'::jsonb"),
            nullable=False,
        ),
        sa.Column(
            "deep_dive_references",
            postgresql.JSONB(),
            server_default=sa.text("'{}'::jsonb"),
            nullable=False,
        ),
        sa.Column(
            "availability",
            postgresql.JSONB(),
            server_default=sa.text("'{}'::jsonb"),
            nullable=False,
        ),
        sa.Column(
            "provenance",
            postgresql.JSONB(),
            server_default=sa.text("'{}'::jsonb"),
            nullable=False,
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint(
            "anomaly_entity_type IN ('CONTRACT', 'EXPIRY')",
            name="anomaly_context_entity_allowed",
        ),
        sa.CheckConstraint(
            "(anomaly_entity_type = 'CONTRACT' "
            "AND contract_snapshot IS NOT NULL "
            "AND expiry_activity_recap IS NULL) OR "
            "(anomaly_entity_type = 'EXPIRY' "
            "AND contract_snapshot IS NULL "
            "AND expiry_activity_recap IS NOT NULL)",
            name="anomaly_context_payload_matches_entity",
        ),
        sa.ForeignKeyConstraint(
            ["product_candidate_context_id"],
            ["product_candidate_contexts.id"],
        ),
        sa.ForeignKeyConstraint(
            ["product_candidate_trigger_id"],
            ["product_candidate_triggers.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "product_candidate_context_id",
            "product_candidate_trigger_id",
            name="uq_anomaly_context_evaluation_trigger",
        ),
    )
    op.create_index(
        "ix_anomaly_context_trigger_history",
        DETAIL_TABLE,
        ["product_candidate_trigger_id", "created_at"],
    )


def downgrade() -> None:
    op.drop_index("ix_anomaly_context_trigger_history", table_name=DETAIL_TABLE)
    op.drop_table(DETAIL_TABLE)
    op.drop_index("ix_product_candidate_context_history", table_name=CONTEXT_TABLE)
    op.drop_index("uq_product_candidate_stage6_baseline", table_name=CONTEXT_TABLE)
    op.drop_table(CONTEXT_TABLE)

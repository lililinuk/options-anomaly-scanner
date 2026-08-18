"""Add Stage 5 Product Candidate persistence.

Revision ID: 20260818_0016
Revises: 20260818_0015
"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "20260818_0016"
down_revision: str | None = "20260818_0015"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

SCAN_RUN_TABLE = "scan_runs"
CANDIDATE_TABLE = "product_candidates"
TRIGGER_TABLE = "product_candidate_triggers"


def upgrade() -> None:
    op.add_column(
        SCAN_RUN_TABLE,
        sa.Column("candidate_materialized_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        SCAN_RUN_TABLE,
        sa.Column(
            "candidate_materialization_rule_version",
            sa.String(length=96),
            nullable=True,
        ),
    )
    op.add_column(
        SCAN_RUN_TABLE,
        sa.Column(
            "candidate_materialization_rule_hash",
            sa.String(length=64),
            nullable=True,
        ),
    )
    op.create_check_constraint(
        "scan_candidate_materialization_all_or_none",
        SCAN_RUN_TABLE,
        "(candidate_materialized_at IS NULL "
        "AND candidate_materialization_rule_version IS NULL "
        "AND candidate_materialization_rule_hash IS NULL) OR "
        "(candidate_materialized_at IS NOT NULL "
        "AND candidate_materialization_rule_version IS NOT NULL "
        "AND candidate_materialization_rule_hash IS NOT NULL)",
    )

    op.create_table(
        CANDIDATE_TABLE,
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("scan_run_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("ticker", sa.String(length=16), nullable=False),
        sa.Column(
            "candidate_first_knowledge_at",
            sa.DateTime(timezone=True),
            nullable=False,
        ),
        sa.Column("materialization_rule_version", sa.String(length=96), nullable=False),
        sa.Column("materialization_rule_hash", sa.String(length=64), nullable=False),
        sa.Column(
            "lifecycle_state",
            sa.String(length=24),
            server_default="MATERIALIZED",
            nullable=False,
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint(
            "lifecycle_state = 'MATERIALIZED'",
            name="product_candidate_lifecycle_allowed",
        ),
        sa.ForeignKeyConstraint(["scan_run_id"], ["scan_runs.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "scan_run_id",
            "ticker",
            "materialization_rule_version",
            name="uq_product_candidate_occurrence",
        ),
    )
    op.create_index(
        "ix_product_candidate_ticker_first_known",
        CANDIDATE_TABLE,
        ["ticker", "candidate_first_knowledge_at"],
    )

    op.create_table(
        TRIGGER_TABLE,
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("product_candidate_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("evidence_family", sa.String(length=32), nullable=False),
        sa.Column("anomaly_entity_type", sa.String(length=16), nullable=False),
        sa.Column("anomaly_identity", sa.String(length=128), nullable=False),
        sa.Column("source_evidence_identity", sa.String(length=192), nullable=False),
        sa.Column("qualifies_candidate", sa.Boolean(), nullable=False),
        sa.Column("present_at_first_knowledge", sa.Boolean(), nullable=False),
        sa.Column("event_date", sa.Date(), nullable=True),
        sa.Column(
            "trigger_first_knowledge_at",
            sa.DateTime(timezone=True),
            nullable=False,
        ),
        sa.Column(
            "source_first_received_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
        sa.Column("vendor_observed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("local_captured_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("source_raw_payload_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column(
            "source_radar_observation_id",
            postgresql.UUID(as_uuid=True),
            nullable=True,
        ),
        sa.Column(
            "source_expiry_observation_id",
            postgresql.UUID(as_uuid=True),
            nullable=True,
        ),
        sa.Column(
            "source_contract_observation_id",
            postgresql.UUID(as_uuid=True),
            nullable=True,
        ),
        sa.Column(
            "source_ids",
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
        sa.Column("specification_version", sa.String(length=64), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint(
            "evidence_family IN "
            "('RADAR_EVENT', 'EXPIRY_ACTIVITY', 'CONTRACT_PERSISTENCE')",
            name="candidate_trigger_family_allowed",
        ),
        sa.CheckConstraint(
            "anomaly_entity_type IN ('CONTRACT', 'EXPIRY')",
            name="candidate_trigger_entity_allowed",
        ),
        sa.CheckConstraint(
            "(evidence_family = 'EXPIRY_ACTIVITY' AND anomaly_entity_type = 'EXPIRY' "
            "AND source_expiry_observation_id IS NOT NULL "
            "AND source_radar_observation_id IS NULL "
            "AND source_contract_observation_id IS NULL) OR "
            "(evidence_family = 'RADAR_EVENT' AND anomaly_entity_type = 'CONTRACT' "
            "AND source_radar_observation_id IS NOT NULL "
            "AND source_expiry_observation_id IS NULL "
            "AND source_contract_observation_id IS NULL) OR "
            "(evidence_family = 'CONTRACT_PERSISTENCE' "
            "AND anomaly_entity_type = 'CONTRACT' "
            "AND source_contract_observation_id IS NOT NULL "
            "AND source_radar_observation_id IS NULL "
            "AND source_expiry_observation_id IS NULL)",
            name="candidate_trigger_source_matches_family",
        ),
        sa.ForeignKeyConstraint(
            ["product_candidate_id"],
            ["product_candidates.id"],
        ),
        sa.ForeignKeyConstraint(
            ["source_raw_payload_id"],
            ["raw_vendor_payloads.id"],
        ),
        sa.ForeignKeyConstraint(
            ["source_radar_observation_id"],
            ["oi_change_radar_observations.id"],
        ),
        sa.ForeignKeyConstraint(
            ["source_expiry_observation_id"],
            ["expiry_observations.id"],
        ),
        sa.ForeignKeyConstraint(
            ["source_contract_observation_id"],
            ["contract_scan_observations.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "product_candidate_id",
            "evidence_family",
            "source_evidence_identity",
            name="uq_candidate_trigger_source_evidence",
        ),
    )
    op.create_index(
        "ix_candidate_trigger_candidate_family",
        TRIGGER_TABLE,
        ["product_candidate_id", "evidence_family"],
    )


def downgrade() -> None:
    op.drop_index("ix_candidate_trigger_candidate_family", table_name=TRIGGER_TABLE)
    op.drop_table(TRIGGER_TABLE)
    op.drop_index("ix_product_candidate_ticker_first_known", table_name=CANDIDATE_TABLE)
    op.drop_table(CANDIDATE_TABLE)

    op.drop_constraint(
        "scan_candidate_materialization_all_or_none",
        SCAN_RUN_TABLE,
        type_="check",
    )
    op.drop_column(SCAN_RUN_TABLE, "candidate_materialization_rule_hash")
    op.drop_column(SCAN_RUN_TABLE, "candidate_materialization_rule_version")
    op.drop_column(SCAN_RUN_TABLE, "candidate_materialized_at")

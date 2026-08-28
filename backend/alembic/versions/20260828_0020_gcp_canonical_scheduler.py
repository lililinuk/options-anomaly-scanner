"""Add Google Cloud canonical production scheduler slot identity.

Revision ID: 20260828_0020
Revises: 20260827_0019
"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "20260828_0020"
down_revision: str | None = "20260827_0019"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

SLOT_TABLE = "canonical_scheduler_slots"
ATTEMPT_TABLE = "canonical_scheduler_attempts"
OWNED_RUN_TABLES = (
    "scan_runs",
    "daily_oi_archive_runs",
    "daily_collection_runs",
    "dealer_gex_archive_runs",
)


def upgrade() -> None:
    op.create_table(
        SLOT_TABLE,
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("slot_type", sa.String(length=32), nullable=False),
        sa.Column("intended_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("intended_market_date", sa.Date(), nullable=False),
        sa.Column("market_timezone", sa.String(length=64), nullable=False),
        sa.Column("actual_started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("trigger_transport", sa.String(length=48), nullable=False),
        sa.Column("canonical_key", sa.String(length=96), nullable=False),
        sa.Column("scheduler_job_name", sa.String(length=255), nullable=False),
        sa.Column("status", sa.String(length=48), nullable=False),
        sa.Column("paid_work_attempted", sa.Boolean(), nullable=False),
        sa.Column("network_attempts", sa.Integer(), nullable=False),
        sa.Column("consumed_units", sa.Integer(), nullable=False),
        sa.Column("product_candidate_count", sa.Integer(), nullable=False),
        sa.Column("baseline_count", sa.Integer(), nullable=False),
        sa.Column(
            "result",
            postgresql.JSONB(),
            server_default=sa.text("'{}'::jsonb"),
            nullable=False,
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint(
            "slot_type IN ('RADAR_OI', 'DEALER_GEX', 'ACTIVITY_VNEXT')",
            name="canonical_slot_type_allowed",
        ),
        sa.CheckConstraint(
            "trigger_transport = 'GOOGLE_CLOUD_SCHEDULER'",
            name="canonical_slot_transport_google_only",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "slot_type",
            "intended_at",
            name="uq_canonical_slot_type_intended",
        ),
        sa.UniqueConstraint("canonical_key", name="uq_canonical_slot_key"),
    )
    op.create_index(
        "ix_canonical_slot_market_date",
        SLOT_TABLE,
        ["intended_market_date", "slot_type"],
    )
    op.create_table(
        ATTEMPT_TABLE,
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("slot_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("scheduler_job_name", sa.String(length=255), nullable=False),
        sa.Column("received_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("disposition", sa.String(length=48), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("result_status", sa.String(length=48), nullable=True),
        sa.ForeignKeyConstraint(["slot_id"], [f"{SLOT_TABLE}.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_canonical_attempt_slot_received",
        ATTEMPT_TABLE,
        ["slot_id", "received_at"],
    )

    for table in OWNED_RUN_TABLES:
        op.add_column(
            table,
            sa.Column("canonical_slot_id", postgresql.UUID(as_uuid=True), nullable=True),
        )
        op.create_foreign_key(
            f"fk_{table}_canonical_slot",
            table,
            SLOT_TABLE,
            ["canonical_slot_id"],
            ["id"],
        )
        op.create_unique_constraint(
            f"uq_{table}_canonical_slot",
            table,
            ["canonical_slot_id"],
        )


def downgrade() -> None:
    for table in reversed(OWNED_RUN_TABLES):
        op.drop_constraint(f"uq_{table}_canonical_slot", table, type_="unique")
        op.drop_constraint(f"fk_{table}_canonical_slot", table, type_="foreignkey")
        op.drop_column(table, "canonical_slot_id")

    op.drop_index("ix_canonical_attempt_slot_received", table_name=ATTEMPT_TABLE)
    op.drop_table(ATTEMPT_TABLE)
    op.drop_index("ix_canonical_slot_market_date", table_name=SLOT_TABLE)
    op.drop_table(SLOT_TABLE)

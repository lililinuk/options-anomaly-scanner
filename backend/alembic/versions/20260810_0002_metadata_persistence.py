"""Add metadata snapshots and complete API usage fields."""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "20260810_0002"
down_revision: str | None = "20260810_0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("api_usage_audit", sa.Column("quota_limit", sa.Integer()))
    op.add_column("api_usage_audit", sa.Column("rate_limit", sa.Integer()))
    op.add_column(
        "api_usage_audit",
        sa.Column("retry_count", sa.Integer(), nullable=False, server_default="0"),
    )
    op.alter_column("api_usage_audit", "retry_count", server_default=None)

    op.create_table(
        "metadata_refreshes",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("raw_payload_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("observed_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("source_request_id", sa.String(128), nullable=False),
        sa.Column("http_status", sa.Integer(), nullable=False),
        sa.Column("capability_count", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(
            ["raw_payload_id"],
            ["raw_vendor_payloads.id"],
            name="fk_metadata_refreshes_raw_payload_id_raw_vendor_payloads",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_metadata_refreshes"),
        sa.UniqueConstraint(
            "source_request_id", name="uq_metadata_refreshes_source_request_id"
        ),
    )
    op.create_index(
        "ix_metadata_refreshes_observed_at", "metadata_refreshes", ["observed_at"]
    )
    op.create_table(
        "capability_snapshots",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("refresh_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("observed_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("capability_identifier", sa.String(160), nullable=False),
        sa.Column("available", sa.Boolean(), nullable=False),
        sa.Column("coverage", sa.String(160)),
        sa.Column("weight", sa.Integer()),
        sa.Column("source_request_id", sa.String(128), nullable=False),
        sa.Column("source_metadata", postgresql.JSONB(), nullable=False),
        sa.ForeignKeyConstraint(
            ["refresh_id"],
            ["metadata_refreshes.id"],
            name="fk_capability_snapshots_refresh_id_metadata_refreshes",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_capability_snapshots"),
        sa.UniqueConstraint(
            "source_request_id",
            "capability_identifier",
            name="uq_capability_snapshot_request_identifier",
        ),
    )
    op.create_index(
        "ix_capability_snapshots_identifier_observed",
        "capability_snapshots",
        ["capability_identifier", "observed_at"],
    )


def downgrade() -> None:
    op.drop_table("capability_snapshots")
    op.drop_table("metadata_refreshes")
    op.drop_column("api_usage_audit", "retry_count")
    op.drop_column("api_usage_audit", "rate_limit")
    op.drop_column("api_usage_audit", "quota_limit")

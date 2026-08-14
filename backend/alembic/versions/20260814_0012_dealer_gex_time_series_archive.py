"""Phase 2B v3.1 append-only Dealer/GEX time-series archive.

Revision ID: 20260814_0012
Revises: 20260814_0011
"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "20260814_0012"
down_revision: str | None = "20260814_0011"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "dealer_gex_archive_runs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("trigger", sa.String(32), nullable=False),
        sa.Column("status", sa.String(48), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True)),
        sa.Column("ny_market_date", sa.Date()),
        sa.Column("intended_capture_slot", sa.String(16), nullable=False),
        sa.Column("scope_key", sa.String(128), nullable=False),
        sa.Column("market_timezone", sa.String(64), nullable=False),
        sa.Column("universe", postgresql.JSONB(), nullable=False),
        sa.Column("specification_version", sa.String(64), nullable=False),
        sa.Column("config_version", sa.String(64), nullable=False),
        sa.Column("config_hash", sa.String(64), nullable=False),
        sa.Column("configuration_snapshot", postgresql.JSONB(), nullable=False),
        sa.Column("tickers_attempted", sa.Integer(), nullable=False),
        sa.Column("tickers_succeeded", sa.Integer(), nullable=False),
        sa.Column("tickers_failed", sa.Integer(), nullable=False),
        sa.Column("observations_reused", sa.Integer(), nullable=False),
        sa.Column("usable_snapshots", sa.Integer(), nullable=False),
        sa.Column("degraded_snapshots", sa.Integer(), nullable=False),
        sa.Column("unavailable_snapshots", sa.Integer(), nullable=False),
        sa.Column("incomplete_snapshots", sa.Integer(), nullable=False),
        sa.Column("network_attempts", sa.Integer(), nullable=False),
        sa.Column("http_successes", sa.Integer(), nullable=False),
        sa.Column("http_failures", sa.Integer(), nullable=False),
        sa.Column("consumed_quota_units", sa.Integer(), nullable=False),
        sa.Column("quota_remaining_before", sa.Integer()),
        sa.Column("quota_remaining_after", sa.Integer()),
        sa.Column("summary", postgresql.JSONB(), nullable=False),
        sa.UniqueConstraint(
            "ny_market_date",
            "intended_capture_slot",
            "scope_key",
            name="uq_dealer_gex_run_market_date_slot_scope",
        ),
    )
    op.create_index(
        "ix_dealer_gex_run_started", "dealer_gex_archive_runs", ["started_at"]
    )

    op.create_table(
        "dealer_gex_snapshots",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "archive_run_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("dealer_gex_archive_runs.id"),
            nullable=False,
        ),
        sa.Column("ticker", sa.String(16), nullable=False),
        sa.Column("vendor_observed_at", sa.DateTime(timezone=True)),
        sa.Column("captured_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("spot_usd", sa.Numeric(18, 6)),
        sa.Column("source_quality", sa.String(40), nullable=False),
        sa.Column("availability", sa.String(24), nullable=False),
        sa.Column("endpoint", sa.String(256), nullable=False),
        sa.Column("capability", sa.String(96), nullable=False),
        sa.Column("endpoint_parameters", postgresql.JSONB(), nullable=False),
        sa.Column("source_request_id", sa.String(128)),
        sa.Column(
            "raw_payload_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("raw_vendor_payloads.id"),
        ),
        sa.Column("source_http_status", sa.Integer()),
        sa.Column("safe_error_code", sa.String(96)),
        sa.Column("truncated", sa.Boolean(), nullable=False),
        sa.Column("cell_count", sa.Integer(), nullable=False),
        sa.Column("expiration_count", sa.Integer(), nullable=False),
        sa.Column("surface_schema_version", sa.String(64), nullable=False),
        sa.Column("observation_identity", sa.String(64)),
        sa.Column("is_analytical_observation", sa.Boolean(), nullable=False),
        sa.Column("quality_details", postgresql.JSONB(), nullable=False),
        sa.Column("specification_version", sa.String(64), nullable=False),
        sa.Column("config_version", sa.String(64), nullable=False),
        sa.Column("config_hash", sa.String(64), nullable=False),
        sa.UniqueConstraint(
            "archive_run_id", "ticker", name="uq_dealer_gex_snapshot_run_ticker"
        ),
        sa.UniqueConstraint(
            "observation_identity", name="uq_dealer_gex_snapshot_observation_identity"
        ),
    )
    op.create_index(
        "ix_dealer_gex_snapshot_ticker_vendor_time",
        "dealer_gex_snapshots",
        ["ticker", "vendor_observed_at"],
    )
    op.create_index(
        "ix_dealer_gex_snapshot_ticker_captured",
        "dealer_gex_snapshots",
        ["ticker", "captured_at"],
    )

    op.create_table(
        "dealer_gex_snapshot_cells",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "snapshot_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("dealer_gex_snapshots.id"),
            nullable=False,
        ),
        sa.Column("expiration", sa.Date(), nullable=False),
        sa.Column("strike", sa.Numeric(18, 6), nullable=False),
        sa.Column("net_dealer_gex_usd", sa.Numeric(32, 6)),
        sa.Column("call_gex_usd", sa.Numeric(32, 6)),
        sa.Column("put_gex_usd", sa.Numeric(32, 6)),
        sa.UniqueConstraint(
            "snapshot_id",
            "expiration",
            "strike",
            name="uq_dealer_gex_cell_snapshot_expiry_strike",
        ),
    )
    op.create_index(
        "ix_dealer_gex_cell_expiry_strike",
        "dealer_gex_snapshot_cells",
        ["expiration", "strike"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_dealer_gex_cell_expiry_strike", table_name="dealer_gex_snapshot_cells"
    )
    op.drop_table("dealer_gex_snapshot_cells")
    op.drop_index(
        "ix_dealer_gex_snapshot_ticker_captured", table_name="dealer_gex_snapshots"
    )
    op.drop_index(
        "ix_dealer_gex_snapshot_ticker_vendor_time",
        table_name="dealer_gex_snapshots",
    )
    op.drop_table("dealer_gex_snapshots")
    op.drop_index("ix_dealer_gex_run_started", table_name="dealer_gex_archive_runs")
    op.drop_table("dealer_gex_archive_runs")

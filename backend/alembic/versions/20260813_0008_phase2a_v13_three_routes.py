"""Phase 2A v1.3 three-route discovery and durable daily collection.

Revision ID: 20260813_0008
Revises: 20260812_0007
"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "20260813_0008"
down_revision: str | None = "20260812_0007"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("scan_runs", sa.Column("radar_threshold_profile_id", sa.String(64)))
    op.add_column("scan_runs", sa.Column("radar_threshold_profile_version", sa.String(64)))
    op.add_column("scan_runs", sa.Column("radar_threshold_config_hash", sa.String(64)))

    for name in (
        "radar_route_eligible",
        "persistent_route_eligible",
        "expiry_activity_route_eligible",
        "deep_dive_eligible",
        "standard_monthly_inferred",
    ):
        op.add_column(
            "expiry_observations",
            sa.Column(name, sa.Boolean(), nullable=False, server_default=sa.false()),
        )
    op.add_column(
        "expiry_observations",
        sa.Column("trigger_sources", postgresql.JSONB(), nullable=False, server_default="[]"),
    )
    op.add_column("expiry_observations", sa.Column("monthly_context_source", sa.String(16)))
    op.add_column("expiry_observations", sa.Column("volume_share_points", sa.Numeric(8, 3)))
    op.add_column("expiry_observations", sa.Column("neighbor_points", sa.Numeric(8, 3)))
    op.add_column("expiry_observations", sa.Column("same_day_score_basis", sa.String(32)))

    for name in ("radar_route_eligible", "persistent_route_eligible", "deep_dive_eligible"):
        op.add_column(
            "contract_scan_observations",
            sa.Column(name, sa.Boolean(), nullable=False, server_default=sa.false()),
        )
    op.add_column(
        "contract_scan_observations",
        sa.Column("trigger_sources", postgresql.JSONB(), nullable=False, server_default="[]"),
    )

    op.create_table(
        "daily_collection_runs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("trigger", sa.String(32), nullable=False),
        sa.Column("status", sa.String(32), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True)),
        sa.Column("ny_market_date", sa.Date(), nullable=False),
        sa.Column("specification_version", sa.String(64), nullable=False),
        sa.Column("radar_threshold_profile_id", sa.String(64), nullable=False),
        sa.Column("radar_threshold_profile_version", sa.String(64), nullable=False),
        sa.Column("radar_threshold_config_hash", sa.String(64), nullable=False),
        sa.Column("configuration_snapshot", postgresql.JSONB(), nullable=False),
        sa.Column("subjobs", postgresql.JSONB(), nullable=False),
        sa.Column("consumed_quota_units", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("network_attempts", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("summary", postgresql.JSONB(), nullable=False),
    )
    op.create_table(
        "daily_collection_coverage",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "daily_run_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("daily_collection_runs.id"),
            nullable=False,
        ),
        sa.Column("subjob", sa.String(24), nullable=False),
        sa.Column("ticker", sa.String(16), nullable=False),
        sa.Column("observation_date", sa.Date(), nullable=False),
        sa.Column("vendor_as_of", sa.DateTime(timezone=True)),
        sa.Column("captured_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("status", sa.String(32), nullable=False),
        sa.Column("row_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("source_request_ids", postgresql.JSONB(), nullable=False),
        sa.Column("details", postgresql.JSONB(), nullable=False),
        sa.UniqueConstraint(
            "subjob", "ticker", "observation_date", name="uq_daily_coverage_job_ticker_date"
        ),
    )
    op.create_index(
        "ix_daily_coverage_job_date",
        "daily_collection_coverage",
        ["subjob", "observation_date"],
    )
    op.create_table(
        "daily_expiry_activity_snapshots",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "daily_run_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("daily_collection_runs.id"),
            nullable=False,
        ),
        sa.Column("ticker", sa.String(16), nullable=False),
        sa.Column("expiration", sa.Date(), nullable=False),
        sa.Column("observation_date", sa.Date(), nullable=False),
        sa.Column("captured_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("vendor_date", sa.Date()),
        sa.Column("vendor_as_of", sa.DateTime(timezone=True)),
        sa.Column("dte", sa.Integer(), nullable=False),
        sa.Column("total_volume", sa.BigInteger(), nullable=False),
        sa.Column("ticker_scope_volume", sa.BigInteger(), nullable=False),
        sa.Column("volume_share", sa.Numeric(12, 8)),
        sa.Column("call_volume_context", sa.BigInteger()),
        sa.Column("put_volume_context", sa.BigInteger()),
        sa.Column("raw_payload_ids", postgresql.JSONB(), nullable=False),
        sa.Column("source_request_ids", postgresql.JSONB(), nullable=False),
        sa.Column("specification_version", sa.String(64), nullable=False),
        sa.UniqueConstraint(
            "ticker", "expiration", "observation_date", name="uq_daily_activity_identity"
        ),
    )
    op.create_index(
        "ix_daily_activity_history",
        "daily_expiry_activity_snapshots",
        ["ticker", "expiration", "observation_date"],
    )

    op.alter_column("zero_dte_activity_daily_snapshots", "scan_run_id", nullable=True)
    op.add_column(
        "zero_dte_activity_daily_snapshots",
        sa.Column(
            "daily_run_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("daily_collection_runs.id"),
        ),
    )

    op.drop_constraint(
        "uq_oi_radar_request_contract", "oi_change_radar_observations", type_="unique"
    )
    op.alter_column("oi_change_radar_observations", "scan_run_id", nullable=True)
    op.add_column(
        "oi_change_radar_observations",
        sa.Column(
            "daily_run_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("daily_collection_runs.id"),
        ),
    )
    radar_columns = (
        sa.Column("captured_at", sa.DateTime(timezone=True)),
        sa.Column("ny_market_date", sa.Date()),
        sa.Column("material_event_eligible", sa.Boolean()),
        sa.Column("radar_route_eligible", sa.Boolean()),
        sa.Column("eligibility_reason", sa.String(64)),
        sa.Column("threshold_profile_id", sa.String(64)),
        sa.Column("threshold_profile_version", sa.String(64)),
        sa.Column("threshold_config_hash", sa.String(64)),
        sa.Column("effective_thresholds", postgresql.JSONB()),
        sa.Column("premium_per_trade", sa.Numeric(22, 6)),
        sa.Column("volume_per_trade", sa.Numeric(18, 6)),
        sa.Column("archive_match_status", sa.String(32)),
        sa.Column("matched_expiration", sa.Date()),
        sa.Column("matched_dte", sa.Integer()),
        sa.Column("matched_right", sa.String(1)),
        sa.Column("matched_strike", sa.Numeric(18, 6)),
        sa.Column("archived_oi", sa.BigInteger()),
        sa.Column("archive_vendor_oi_date", sa.Date()),
        sa.Column("archive_completeness", sa.String(32)),
        sa.Column("contract_structure_score", sa.Numeric(8, 3)),
        sa.Column("contract_persistent_score", sa.Numeric(8, 3)),
        sa.Column("radar_scope", sa.String(32)),
        sa.Column("deep_dive_eligible", sa.Boolean()),
        sa.Column("trigger_sources", postgresql.JSONB()),
        sa.Column("risk_flags", postgresql.JSONB()),
    )
    for column in radar_columns:
        op.add_column("oi_change_radar_observations", column)
    op.create_unique_constraint(
        "uq_oi_radar_identity",
        "oi_change_radar_observations",
        ["ticker", "contract_symbol", "observation_date"],
    )


def downgrade() -> None:
    op.drop_constraint("uq_oi_radar_identity", "oi_change_radar_observations", type_="unique")
    for name in (
        "risk_flags",
        "trigger_sources",
        "deep_dive_eligible",
        "radar_scope",
        "contract_persistent_score",
        "contract_structure_score",
        "archive_completeness",
        "archive_vendor_oi_date",
        "archived_oi",
        "matched_strike",
        "matched_right",
        "matched_dte",
        "matched_expiration",
        "archive_match_status",
        "volume_per_trade",
        "premium_per_trade",
        "effective_thresholds",
        "threshold_config_hash",
        "threshold_profile_version",
        "threshold_profile_id",
        "eligibility_reason",
        "radar_route_eligible",
        "material_event_eligible",
        "ny_market_date",
        "captured_at",
        "daily_run_id",
    ):
        op.drop_column("oi_change_radar_observations", name)
    op.alter_column("oi_change_radar_observations", "scan_run_id", nullable=False)
    op.create_unique_constraint(
        "uq_oi_radar_request_contract",
        "oi_change_radar_observations",
        ["source_request_id", "contract_symbol"],
    )
    op.drop_column("zero_dte_activity_daily_snapshots", "daily_run_id")
    op.alter_column("zero_dte_activity_daily_snapshots", "scan_run_id", nullable=False)
    op.drop_table("daily_expiry_activity_snapshots")
    op.drop_table("daily_collection_coverage")
    op.drop_table("daily_collection_runs")
    for name in (
        "trigger_sources",
        "deep_dive_eligible",
        "persistent_route_eligible",
        "radar_route_eligible",
    ):
        op.drop_column("contract_scan_observations", name)
    for name in (
        "same_day_score_basis",
        "neighbor_points",
        "volume_share_points",
        "monthly_context_source",
        "standard_monthly_inferred",
        "deep_dive_eligible",
        "trigger_sources",
        "expiry_activity_route_eligible",
        "persistent_route_eligible",
        "radar_route_eligible",
    ):
        op.drop_column("expiry_observations", name)
    op.drop_column("scan_runs", "radar_threshold_config_hash")
    op.drop_column("scan_runs", "radar_threshold_profile_version")
    op.drop_column("scan_runs", "radar_threshold_profile_id")

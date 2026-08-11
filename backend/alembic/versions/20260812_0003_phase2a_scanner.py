"""Add append-only Phase 2A positioning scanner entities."""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "20260812_0003"
down_revision: str | None = "20260810_0002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

UUID = postgresql.UUID(as_uuid=True)
JSONB = postgresql.JSONB()


def upgrade() -> None:
    op.add_column("scan_runs", sa.Column("specification_version", sa.String(64)))
    op.add_column("scan_runs", sa.Column("market_date", sa.Date()))
    op.add_column(
        "scan_runs",
        sa.Column("consumed_quota_units", sa.Integer(), nullable=False, server_default="0"),
    )
    op.add_column(
        "scan_runs", sa.Column("network_attempts", sa.Integer(), nullable=False, server_default="0")
    )
    op.add_column(
        "scan_runs", sa.Column("cache_hits", sa.Integer(), nullable=False, server_default="0")
    )
    op.add_column(
        "scan_runs", sa.Column("fresh_requests", sa.Integer(), nullable=False, server_default="0")
    )
    op.add_column(
        "scan_runs",
        sa.Column("summary", JSONB, nullable=False, server_default=sa.text("'{}'::jsonb")),
    )
    op.add_column("api_usage_audit", sa.Column("scan_run_id", UUID))
    op.create_foreign_key(
        "fk_api_usage_audit_scan_run_id", "api_usage_audit", "scan_runs", ["scan_run_id"], ["id"]
    )

    op.create_table(
        "scan_stages",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("scan_run_id", UUID, nullable=False),
        sa.Column("stage", sa.String(32), nullable=False),
        sa.Column("status", sa.String(32), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True)),
        sa.Column("details", JSONB, nullable=False),
        sa.ForeignKeyConstraint(["scan_run_id"], ["scan_runs.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("scan_run_id", "stage", name="uq_scan_stage_run_stage"),
    )
    op.create_table(
        "ticker_scan_results",
        sa.Column("id", UUID, nullable=False),
        sa.Column("scan_run_id", UUID, nullable=False),
        sa.Column("ticker", sa.String(16), nullable=False),
        sa.Column("observed_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("preliminary_score", sa.Numeric(8, 3)),
        sa.Column("selected_for_deep_scan", sa.Boolean(), nullable=False),
        sa.Column("data_completeness", sa.String(32), nullable=False),
        sa.Column("raw_payload_ids", JSONB, nullable=False),
        sa.Column("source_request_ids", JSONB, nullable=False),
        sa.Column("specification_version", sa.String(64), nullable=False),
        sa.ForeignKeyConstraint(["scan_run_id"], ["scan_runs.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("scan_run_id", "ticker", name="uq_ticker_result_run_ticker"),
    )
    op.create_index("ix_ticker_scan_results_ticker", "ticker_scan_results", ["ticker"])
    op.create_table(
        "expiry_observations",
        sa.Column("id", UUID, nullable=False),
        sa.Column("scan_run_id", UUID, nullable=False),
        sa.Column("ticker", sa.String(16), nullable=False),
        sa.Column("expiration", sa.Date(), nullable=False),
        sa.Column("observed_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("dte_at_detection", sa.Integer(), nullable=False),
        sa.Column("bucket_at_detection", sa.String(32), nullable=False),
        sa.Column("current_dte", sa.Integer(), nullable=False),
        sa.Column("current_bucket", sa.String(32)),
        sa.Column("call_volume", sa.BigInteger(), nullable=False),
        sa.Column("put_volume", sa.BigInteger(), nullable=False),
        sa.Column("call_oi", sa.BigInteger(), nullable=False),
        sa.Column("put_oi", sa.BigInteger(), nullable=False),
        sa.Column("volume_share", sa.Numeric(12, 8)),
        sa.Column("oi_share", sa.Numeric(12, 8)),
        sa.Column("neighbor_ratio", sa.Numeric(12, 5)),
        sa.Column("volume_skew", sa.Numeric(12, 8)),
        sa.Column("oi_skew", sa.Numeric(12, 8)),
        sa.Column("expiration_type", sa.String(40), nullable=False),
        sa.Column("expiration_type_source", sa.String(16), nullable=False),
        sa.Column("baseline_quality", sa.String(32), nullable=False),
        sa.Column("preliminary_score", sa.Numeric(8, 3), nullable=False),
        sa.Column("preliminary_basis", sa.Numeric(8, 3), nullable=False),
        sa.Column("expiry_score", sa.Numeric(8, 3)),
        sa.Column("expiry_score_basis", sa.Numeric(8, 3)),
        sa.Column("classification", sa.String(40)),
        sa.Column("selected_for_deep_scan", sa.Boolean(), nullable=False),
        sa.Column("components", JSONB, nullable=False),
        sa.Column("raw_payload_ids", JSONB, nullable=False),
        sa.Column("source_request_ids", JSONB, nullable=False),
        sa.Column("specification_version", sa.String(64), nullable=False),
        sa.ForeignKeyConstraint(["scan_run_id"], ["scan_runs.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "scan_run_id", "ticker", "expiration", name="uq_expiry_observation_run_ticker_expiry"
        ),
    )
    op.create_index("ix_expiry_observations_ticker", "expiry_observations", ["ticker"])
    op.create_table(
        "contract_scan_observations",
        sa.Column("id", UUID, nullable=False),
        sa.Column("scan_run_id", UUID, nullable=False),
        sa.Column("expiry_observation_id", UUID, nullable=False),
        sa.Column("raw_payload_id", UUID, nullable=False),
        sa.Column("contract_symbol", sa.String(64), nullable=False),
        sa.Column("ticker", sa.String(16), nullable=False),
        sa.Column("expiration", sa.Date(), nullable=False),
        sa.Column("right", sa.String(1), nullable=False),
        sa.Column("strike", sa.Numeric(18, 6), nullable=False),
        sa.Column("observed_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("dte_at_detection", sa.Integer(), nullable=False),
        sa.Column("bucket_at_detection", sa.String(32), nullable=False),
        sa.Column("current_dte", sa.Integer(), nullable=False),
        sa.Column("current_bucket", sa.String(32)),
        sa.Column("volume", sa.BigInteger(), nullable=False),
        sa.Column("previous_oi", sa.BigInteger(), nullable=False),
        sa.Column("volume_oi_ratio", sa.Numeric(18, 6), nullable=False),
        sa.Column("bid", sa.Numeric(18, 6)),
        sa.Column("ask", sa.Numeric(18, 6)),
        sa.Column("mid", sa.Numeric(18, 6)),
        sa.Column("spread_pct", sa.Numeric(12, 8)),
        sa.Column("last", sa.Numeric(18, 6)),
        sa.Column("delta", sa.Numeric(12, 8)),
        sa.Column("spot", sa.Numeric(18, 6)),
        sa.Column("estimated_premium", sa.Numeric(22, 4)),
        sa.Column("premium_quality", sa.String(40)),
        sa.Column("historical_robust_z", sa.Numeric(12, 5)),
        sa.Column("intraday_burst_ratio", sa.Numeric(12, 5)),
        sa.Column("anomaly_score", sa.Numeric(8, 3), nullable=False),
        sa.Column("score_basis_weight", sa.Numeric(8, 3), nullable=False),
        sa.Column("classification", sa.String(24), nullable=False),
        sa.Column("is_candidate", sa.Boolean(), nullable=False),
        sa.Column("hard_reject_reason", sa.String(64)),
        sa.Column("risk_flags", JSONB, nullable=False),
        sa.Column("components", JSONB, nullable=False),
        sa.Column("source_request_ids", JSONB, nullable=False),
        sa.Column("specification_version", sa.String(64), nullable=False),
        sa.ForeignKeyConstraint(["scan_run_id"], ["scan_runs.id"]),
        sa.ForeignKeyConstraint(["expiry_observation_id"], ["expiry_observations.id"]),
        sa.ForeignKeyConstraint(["raw_payload_id"], ["raw_vendor_payloads.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("scan_run_id", "contract_symbol", name="uq_contract_scan_run_symbol"),
    )
    op.create_index(
        "ix_contract_scan_observations_ticker", "contract_scan_observations", ["ticker"]
    )
    op.create_table(
        "strike_clusters",
        sa.Column("id", UUID, nullable=False),
        sa.Column("scan_run_id", UUID, nullable=False),
        sa.Column("expiry_observation_id", UUID, nullable=False),
        sa.Column("ticker", sa.String(16), nullable=False),
        sa.Column("expiration", sa.Date(), nullable=False),
        sa.Column("right", sa.String(1), nullable=False),
        sa.Column("min_strike", sa.Numeric(18, 6), nullable=False),
        sa.Column("max_strike", sa.Numeric(18, 6), nullable=False),
        sa.Column("contract_count", sa.Integer(), nullable=False),
        sa.Column("total_volume", sa.BigInteger(), nullable=False),
        sa.Column("total_estimated_premium", sa.Numeric(22, 4)),
        sa.Column("total_oi", sa.BigInteger(), nullable=False),
        sa.Column("premium_share", sa.Numeric(12, 8)),
        sa.Column("volume_share", sa.Numeric(12, 8)),
        sa.Column("premium_weighted_strike", sa.Numeric(18, 6)),
        sa.Column("cluster_score", sa.Numeric(8, 3), nullable=False),
        sa.Column("score_basis_weight", sa.Numeric(8, 3), nullable=False),
        sa.Column("classification", sa.String(32), nullable=False),
        sa.Column("shape", sa.String(24), nullable=False),
        sa.Column("source_contract_ids", JSONB, nullable=False),
        sa.Column("components", JSONB, nullable=False),
        sa.Column("specification_version", sa.String(64), nullable=False),
        sa.ForeignKeyConstraint(["scan_run_id"], ["scan_runs.id"]),
        sa.ForeignKeyConstraint(["expiry_observation_id"], ["expiry_observations.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_strike_clusters_ticker", "strike_clusters", ["ticker"])
    op.create_table(
        "bucket_positioning_summaries",
        sa.Column("id", UUID, nullable=False),
        sa.Column("scan_run_id", UUID, nullable=False),
        sa.Column("ticker", sa.String(16), nullable=False),
        sa.Column("bucket", sa.String(32), nullable=False),
        sa.Column("observed_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("strongest_expiry_id", UUID),
        sa.Column("strongest_call_contract_id", UUID),
        sa.Column("strongest_put_contract_id", UUID),
        sa.Column("strongest_call_cluster_id", UUID),
        sa.Column("strongest_put_cluster_id", UUID),
        sa.Column("positioning_label", sa.String(32), nullable=False),
        sa.Column("day_zero_status", sa.String(48)),
        sa.Column("oi_status", sa.String(24), nullable=False),
        sa.Column("data_completeness", sa.String(32), nullable=False),
        sa.Column("metrics", JSONB, nullable=False),
        sa.Column("specification_version", sa.String(64), nullable=False),
        sa.ForeignKeyConstraint(["scan_run_id"], ["scan_runs.id"]),
        sa.ForeignKeyConstraint(["strongest_expiry_id"], ["expiry_observations.id"]),
        sa.ForeignKeyConstraint(["strongest_call_contract_id"], ["contract_scan_observations.id"]),
        sa.ForeignKeyConstraint(["strongest_put_contract_id"], ["contract_scan_observations.id"]),
        sa.ForeignKeyConstraint(["strongest_call_cluster_id"], ["strike_clusters.id"]),
        sa.ForeignKeyConstraint(["strongest_put_cluster_id"], ["strike_clusters.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "scan_run_id", "ticker", "bucket", name="uq_bucket_summary_run_ticker_bucket"
        ),
    )
    op.create_index(
        "ix_bucket_positioning_summaries_ticker", "bucket_positioning_summaries", ["ticker"]
    )
    op.create_table(
        "oi_confirmation_events",
        sa.Column("id", UUID, nullable=False),
        sa.Column("scan_run_id", UUID, nullable=False),
        sa.Column("contract_observation_id", UUID, nullable=False),
        sa.Column("status", sa.String(24), nullable=False),
        sa.Column("observed_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("evidence", JSONB, nullable=False),
        sa.Column("source_request_ids", JSONB, nullable=False),
        sa.Column("specification_version", sa.String(64), nullable=False),
        sa.ForeignKeyConstraint(["scan_run_id"], ["scan_runs.id"]),
        sa.ForeignKeyConstraint(["contract_observation_id"], ["contract_scan_observations.id"]),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    for table in (
        "oi_confirmation_events",
        "bucket_positioning_summaries",
        "strike_clusters",
        "contract_scan_observations",
        "expiry_observations",
        "ticker_scan_results",
        "scan_stages",
    ):
        op.drop_table(table)
    for column in (
        "summary",
        "fresh_requests",
        "cache_hits",
        "network_attempts",
        "consumed_quota_units",
        "market_date",
        "specification_version",
    ):
        op.drop_column("scan_runs", column)
    op.drop_constraint("fk_api_usage_audit_scan_run_id", "api_usage_audit", type_="foreignkey")
    op.drop_column("api_usage_audit", "scan_run_id")

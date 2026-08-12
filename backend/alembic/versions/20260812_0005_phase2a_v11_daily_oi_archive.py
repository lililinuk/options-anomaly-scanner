"""Add Phase 2A v1.1 daily OI archive and runtime-aligned discovery fields."""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "20260812_0005"
down_revision: str | None = "20260812_0004"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

UUID = postgresql.UUID(as_uuid=True)
JSONB = postgresql.JSONB()


def upgrade() -> None:
    op.add_column("ticker_scan_results", sa.Column("activity_context", JSONB))
    for _name, column in (
        ("vendor_oi_date", sa.Column("vendor_oi_date", sa.Date())),
        ("call_oi_share", sa.Column("call_oi_share", sa.Numeric(12, 8))),
        ("put_oi_share", sa.Column("put_oi_share", sa.Numeric(12, 8))),
        ("same_day_activity_score", sa.Column("same_day_activity_score", sa.Numeric(8, 3))),
        ("same_day_score_basis_weight", sa.Column("same_day_score_basis_weight", sa.Numeric(8, 3))),
        ("same_day_data_coverage", sa.Column("same_day_data_coverage", sa.Numeric(8, 3))),
        ("missing_same_day_components", sa.Column("missing_same_day_components", JSONB)),
        (
            "persistent_positioning_score",
            sa.Column("persistent_positioning_score", sa.Numeric(8, 3)),
        ),
        ("persistent_state", sa.Column("persistent_state", sa.String(32))),
        ("persistent_winning_window", sa.Column("persistent_winning_window", sa.Integer())),
        ("history_confidence", sa.Column("history_confidence", sa.String(16))),
        ("persistent_components", sa.Column("persistent_components", JSONB)),
        ("discovery_score", sa.Column("discovery_score", sa.Numeric(8, 3))),
        ("discovery_source", sa.Column("discovery_source", sa.String(16))),
        (
            "structural_cold_start_eligible",
            sa.Column(
                "structural_cold_start_eligible",
                sa.Boolean(),
                nullable=False,
                server_default=sa.false(),
            ),
        ),
    ):
        op.add_column("expiry_observations", column)

    for column in (
        "volume",
        "previous_oi",
        "volume_oi_ratio",
        "anomaly_score",
        "score_basis_weight",
    ):
        existing = sa.BigInteger() if column in {"volume", "previous_oi"} else sa.Numeric(18, 6)
        if column in {"anomaly_score", "score_basis_weight"}:
            existing = sa.Numeric(8, 3)
        op.alter_column("contract_scan_observations", column, existing_type=existing, nullable=True)
    for column in (
        sa.Column("current_oi", sa.BigInteger()),
        sa.Column("contract_oi_share", sa.Numeric(12, 8)),
        sa.Column("neighbor_strike_ratio", sa.Numeric(12, 5)),
        sa.Column("structure_score", sa.Numeric(8, 3)),
        sa.Column("structure_components", JSONB),
        sa.Column("persistent_positioning_score", sa.Numeric(8, 3)),
        sa.Column("persistent_state", sa.String(32)),
        sa.Column("persistent_winning_window", sa.Integer()),
        sa.Column("history_observation_count", sa.Integer()),
        sa.Column("history_confidence", sa.String(16)),
        sa.Column("persistent_components", JSONB),
        sa.Column("oi_change_radar_status", sa.String(24)),
        sa.Column("oi_change_radar_evidence", JSONB),
    ):
        op.add_column("contract_scan_observations", column)

    op.alter_column("strike_clusters", "total_volume", existing_type=sa.BigInteger(), nullable=True)
    for column in (
        sa.Column("cluster_oi_share", sa.Numeric(12, 8)),
        sa.Column("positioning_center", sa.Numeric(18, 6)),
        sa.Column("persistent_build_count", sa.Integer()),
        sa.Column("persistent_decline_count", sa.Integer()),
        sa.Column("oi_weighted_persistent_score", sa.Numeric(8, 3)),
        sa.Column("cluster_net_oi_changes", JSONB),
    ):
        op.add_column("strike_clusters", column)

    op.create_table(
        "daily_oi_archive_runs",
        sa.Column("id", UUID, primary_key=True),
        sa.Column("trigger", sa.String(32), nullable=False),
        sa.Column("status", sa.String(48), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True)),
        sa.Column("configuration_snapshot", JSONB, nullable=False),
        sa.Column("specification_version", sa.String(64), nullable=False),
        sa.Column("consumed_quota_units", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("network_attempts", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("summary", JSONB, nullable=False),
    )
    op.create_table(
        "daily_oi_archive_tickers",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column(
            "archive_run_id", UUID, sa.ForeignKey("daily_oi_archive_runs.id"), nullable=False
        ),
        sa.Column("ticker", sa.String(16), nullable=False),
        sa.Column("vendor_oi_date", sa.Date()),
        sa.Column("vendor_oi_as_of", sa.DateTime(timezone=True)),
        sa.Column("status", sa.String(48), nullable=False),
        sa.Column("expiries_expected", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("complete_chains", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("incomplete_chains", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("contracts_persisted", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("details", JSONB, nullable=False),
        sa.UniqueConstraint("archive_run_id", "ticker", name="uq_archive_ticker_run_ticker"),
    )
    op.create_index("ix_daily_oi_archive_tickers_ticker", "daily_oi_archive_tickers", ["ticker"])
    op.create_table(
        "expiry_oi_daily_snapshots",
        sa.Column("id", UUID, primary_key=True),
        sa.Column(
            "archive_run_id", UUID, sa.ForeignKey("daily_oi_archive_runs.id"), nullable=False
        ),
        sa.Column("ticker", sa.String(16), nullable=False),
        sa.Column("expiration", sa.Date(), nullable=False),
        sa.Column("vendor_oi_date", sa.Date(), nullable=False),
        sa.Column("vendor_oi_as_of", sa.DateTime(timezone=True), nullable=False),
        sa.Column("call_oi", sa.BigInteger(), nullable=False),
        sa.Column("put_oi", sa.BigInteger(), nullable=False),
        sa.Column("total_oi", sa.BigInteger(), nullable=False),
        sa.Column("call_oi_share", sa.Numeric(12, 8)),
        sa.Column("put_oi_share", sa.Numeric(12, 8)),
        sa.Column("total_oi_share", sa.Numeric(12, 8)),
        sa.Column("dte", sa.Integer(), nullable=False),
        sa.Column("bucket", sa.String(32), nullable=False),
        sa.Column("chain_status", sa.String(32), nullable=False),
        sa.Column("raw_payload_id", UUID, sa.ForeignKey("raw_vendor_payloads.id"), nullable=False),
        sa.Column("source_request_id", sa.String(128), nullable=False),
        sa.Column("specification_version", sa.String(64), nullable=False),
        sa.UniqueConstraint(
            "ticker", "expiration", "vendor_oi_date", name="uq_expiry_oi_ticker_expiry_date"
        ),
    )
    op.create_index(
        "ix_expiry_oi_history",
        "expiry_oi_daily_snapshots",
        ["ticker", "expiration", "vendor_oi_date"],
    )
    op.create_table(
        "contract_oi_daily_snapshots",
        sa.Column("id", UUID, primary_key=True),
        sa.Column(
            "archive_run_id", UUID, sa.ForeignKey("daily_oi_archive_runs.id"), nullable=False
        ),
        sa.Column("ticker", sa.String(16), nullable=False),
        sa.Column("contract_symbol", sa.String(64), nullable=False),
        sa.Column("vendor_oi_date", sa.Date(), nullable=False),
        sa.Column("vendor_oi_as_of", sa.DateTime(timezone=True), nullable=False),
        sa.Column("expiration", sa.Date(), nullable=False),
        sa.Column("right", sa.String(1), nullable=False),
        sa.Column("strike", sa.Numeric(18, 6), nullable=False),
        sa.Column("dte", sa.Integer(), nullable=False),
        sa.Column("bucket", sa.String(32), nullable=False),
        sa.Column("open_interest", sa.BigInteger(), nullable=False),
        sa.Column("bid", sa.Numeric(18, 6)),
        sa.Column("ask", sa.Numeric(18, 6)),
        sa.Column("implied_volatility", sa.Numeric(18, 8)),
        sa.Column("delta", sa.Numeric(12, 8)),
        sa.Column("gamma", sa.Numeric(18, 10)),
        sa.Column("theta", sa.Numeric(18, 8)),
        sa.Column("vega", sa.Numeric(18, 8)),
        sa.Column("charm", sa.Numeric(18, 8)),
        sa.Column("underlying_price", sa.Numeric(18, 6)),
        sa.Column("quote_as_of", sa.DateTime(timezone=True)),
        sa.Column("greeks_as_of", sa.DateTime(timezone=True)),
        sa.Column("underlying_as_of", sa.DateTime(timezone=True)),
        sa.Column("raw_payload_id", UUID, sa.ForeignKey("raw_vendor_payloads.id"), nullable=False),
        sa.Column("source_request_id", sa.String(128), nullable=False),
        sa.Column("specification_version", sa.String(64), nullable=False),
        sa.UniqueConstraint(
            "ticker", "contract_symbol", "vendor_oi_date", name="uq_contract_oi_ticker_symbol_date"
        ),
    )
    op.create_index(
        "ix_contract_oi_history",
        "contract_oi_daily_snapshots",
        ["ticker", "contract_symbol", "vendor_oi_date"],
    )
    op.create_table(
        "oi_change_radar_observations",
        sa.Column("id", UUID, primary_key=True),
        sa.Column("scan_run_id", UUID, sa.ForeignKey("scan_runs.id"), nullable=False),
        sa.Column("ticker", sa.String(16), nullable=False),
        sa.Column("contract_symbol", sa.String(64), nullable=False),
        sa.Column("observation_date", sa.Date()),
        sa.Column("previous_date", sa.Date()),
        sa.Column("previous_oi", sa.BigInteger()),
        sa.Column("current_oi", sa.BigInteger()),
        sa.Column("delta_oi", sa.BigInteger()),
        sa.Column("relative_oi_change", sa.Numeric(18, 8)),
        sa.Column("volume", sa.BigInteger()),
        sa.Column("trades", sa.BigInteger()),
        sa.Column("average_price", sa.Numeric(18, 6)),
        sa.Column("premium", sa.Numeric(22, 4)),
        sa.Column("rank", sa.Integer()),
        sa.Column("last_bid", sa.Numeric(18, 6)),
        sa.Column("last_ask", sa.Numeric(18, 6)),
        sa.Column("last_fill", sa.Numeric(18, 6)),
        sa.Column("raw_payload_id", UUID, sa.ForeignKey("raw_vendor_payloads.id"), nullable=False),
        sa.Column("source_request_id", sa.String(128), nullable=False),
        sa.Column("specification_version", sa.String(64), nullable=False),
        sa.UniqueConstraint(
            "source_request_id", "contract_symbol", name="uq_oi_radar_request_contract"
        ),
    )
    op.create_index(
        "ix_oi_radar_ticker_date", "oi_change_radar_observations", ["ticker", "observation_date"]
    )


def downgrade() -> None:
    op.drop_table("oi_change_radar_observations")
    op.drop_table("contract_oi_daily_snapshots")
    op.drop_table("expiry_oi_daily_snapshots")
    op.drop_table("daily_oi_archive_tickers")
    op.drop_table("daily_oi_archive_runs")
    for name in (
        "cluster_net_oi_changes",
        "oi_weighted_persistent_score",
        "persistent_decline_count",
        "persistent_build_count",
        "positioning_center",
        "cluster_oi_share",
    ):
        op.drop_column("strike_clusters", name)
    op.alter_column(
        "strike_clusters", "total_volume", existing_type=sa.BigInteger(), nullable=False
    )
    for name in (
        "oi_change_radar_evidence",
        "oi_change_radar_status",
        "persistent_components",
        "history_confidence",
        "history_observation_count",
        "persistent_winning_window",
        "persistent_state",
        "persistent_positioning_score",
        "structure_components",
        "structure_score",
        "neighbor_strike_ratio",
        "contract_oi_share",
        "current_oi",
    ):
        op.drop_column("contract_scan_observations", name)
    for name in (
        "structural_cold_start_eligible",
        "discovery_source",
        "discovery_score",
        "persistent_components",
        "history_confidence",
        "persistent_winning_window",
        "persistent_state",
        "persistent_positioning_score",
        "missing_same_day_components",
        "same_day_data_coverage",
        "same_day_score_basis_weight",
        "same_day_activity_score",
        "put_oi_share",
        "call_oi_share",
        "vendor_oi_date",
    ):
        op.drop_column("expiry_observations", name)
    op.drop_column("ticker_scan_results", "activity_context")

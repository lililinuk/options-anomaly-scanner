"""Add Phase 2A v1.2 0DTE calibration and discovery evidence fields."""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "20260812_0006"
down_revision: str | None = "20260812_0005"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

UUID = postgresql.UUID(as_uuid=True)
JSONB = postgresql.JSONB()


def upgrade() -> None:
    for column in (
        sa.Column("current_expiry_volume", sa.BigInteger()),
        sa.Column("same_day_baseline_status", sa.String(32)),
        sa.Column("baseline_observation_count", sa.Integer()),
        sa.Column("baseline_20_mean_volume_share", sa.Numeric(12, 8)),
        sa.Column("baseline_20_median_volume_share", sa.Numeric(12, 8)),
        sa.Column("baseline_20_mad_volume_share", sa.Numeric(12, 8)),
        sa.Column("historical_percentile_20", sa.Numeric(12, 8)),
        sa.Column("robust_deviation", sa.Numeric(18, 8)),
        sa.Column("zero_dte_baseline_method", sa.String(48)),
        sa.Column("comparable_peer_count", sa.Integer()),
        sa.Column("comparable_peer_dtes", JSONB),
        sa.Column("comparable_peer_quality", sa.String(32)),
        sa.Column("comparable_peer_median_volume", sa.Numeric(18, 3)),
        sa.Column("discovery_primary_score", sa.Numeric(8, 3)),
        sa.Column("discovery_secondary_score", sa.Numeric(8, 3)),
        sa.Column("discovery_confirmation_bonus", sa.Numeric(8, 3)),
        sa.Column("discovery_evidence_breadth", sa.Integer()),
    ):
        op.add_column("expiry_observations", column)

    op.create_table(
        "zero_dte_activity_daily_snapshots",
        sa.Column("id", UUID, primary_key=True),
        sa.Column("scan_run_id", UUID, sa.ForeignKey("scan_runs.id"), nullable=False),
        sa.Column("ticker", sa.String(16), nullable=False),
        sa.Column("observation_date", sa.Date(), nullable=False),
        sa.Column("expiration", sa.Date(), nullable=False),
        sa.Column("expiry_volume", sa.BigInteger(), nullable=False),
        sa.Column("ticker_scope_volume", sa.BigInteger(), nullable=False),
        sa.Column("volume_share", sa.Numeric(12, 8), nullable=False),
        sa.Column("raw_cross_expiry_neighbor_ratio", sa.Numeric(18, 8)),
        sa.Column(
            "raw_payload_id", UUID, sa.ForeignKey("raw_vendor_payloads.id"), nullable=False
        ),
        sa.Column("source_request_id", sa.String(128), nullable=False),
        sa.Column("specification_version", sa.String(64), nullable=False),
        sa.UniqueConstraint(
            "ticker", "observation_date", name="uq_zero_dte_activity_ticker_date"
        ),
    )
    op.create_index(
        "ix_zero_dte_activity_history",
        "zero_dte_activity_daily_snapshots",
        ["ticker", "observation_date"],
    )


def downgrade() -> None:
    op.drop_table("zero_dte_activity_daily_snapshots")
    for name in (
        "discovery_evidence_breadth",
        "discovery_confirmation_bonus",
        "discovery_secondary_score",
        "discovery_primary_score",
        "comparable_peer_median_volume",
        "comparable_peer_quality",
        "comparable_peer_dtes",
        "comparable_peer_count",
        "zero_dte_baseline_method",
        "robust_deviation",
        "historical_percentile_20",
        "baseline_20_mad_volume_share",
        "baseline_20_median_volume_share",
        "baseline_20_mean_volume_share",
        "baseline_observation_count",
        "same_day_baseline_status",
        "current_expiry_volume",
    ):
        op.drop_column("expiry_observations", name)

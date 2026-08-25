"""Add Stage 4A daily-pipeline evidence identities.

Revision ID: 20260818_0015
Revises: 20260817_0014
"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "20260818_0015"
down_revision: str | None = "20260817_0014"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

COVERAGE_TABLE = "daily_collection_coverage"
CONTRACT_TABLE = "contract_oi_daily_snapshots"
ZERO_DTE_SESSION_TABLE = "zero_dte_activity_session_snapshots"


def upgrade() -> None:
    op.add_column(COVERAGE_TABLE, sa.Column("activity_market_date", sa.Date(), nullable=True))
    op.add_column(COVERAGE_TABLE, sa.Column("vendor_oi_date", sa.Date(), nullable=True))
    op.create_unique_constraint(
        "uq_daily_coverage_activity_market_date",
        COVERAGE_TABLE,
        ["subjob", "ticker", "activity_market_date"],
    )
    op.create_unique_constraint(
        "uq_daily_coverage_vendor_oi_date",
        COVERAGE_TABLE,
        ["subjob", "ticker", "vendor_oi_date"],
    )
    op.create_check_constraint(
        "daily_coverage_activity_date_semantics",
        COVERAGE_TABLE,
        "activity_market_date IS NULL OR subjob = 'ACTIVITY'",
    )
    op.create_check_constraint(
        "daily_coverage_vendor_oi_date_semantics",
        COVERAGE_TABLE,
        "vendor_oi_date IS NULL OR subjob = 'RADAR'",
    )

    op.add_column(
        CONTRACT_TABLE,
        sa.Column("open_interest_as_of", sa.DateTime(timezone=True), nullable=True),
    )

    op.create_table(
        ZERO_DTE_SESSION_TABLE,
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("scan_run_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("daily_run_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("ticker", sa.String(length=16), nullable=False),
        sa.Column("observation_date", sa.Date(), nullable=False),
        sa.Column("expiration", sa.Date(), nullable=False),
        sa.Column("snapshot_kind", sa.String(length=40), nullable=False),
        sa.Column("captured_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("session_close_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("expiry_volume", sa.BigInteger(), nullable=False),
        sa.Column("ticker_scope_volume", sa.BigInteger(), nullable=False),
        sa.Column("volume_share", sa.Numeric(precision=12, scale=8), nullable=False),
        sa.Column(
            "raw_cross_expiry_neighbor_ratio",
            sa.Numeric(precision=18, scale=8),
            nullable=True,
        ),
        sa.Column("raw_payload_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("source_request_id", sa.String(length=128), nullable=False),
        sa.Column("specification_version", sa.String(length=64), nullable=False),
        sa.CheckConstraint(
            "snapshot_kind IN "
            "('PROVISIONAL_INTRADAY', 'CANONICAL_SESSION_COMPLETE', "
            "'LEGACY_OR_AMBIGUOUS')",
            name="zero_dte_session_kind_allowed",
        ),
        sa.CheckConstraint(
            "(snapshot_kind = 'PROVISIONAL_INTRADAY' "
            "AND scan_run_id IS NOT NULL AND daily_run_id IS NULL "
            "AND session_close_at IS NULL) OR "
            "(snapshot_kind = 'CANONICAL_SESSION_COMPLETE' "
            "AND scan_run_id IS NULL AND daily_run_id IS NOT NULL "
            "AND session_close_at IS NOT NULL) OR "
            "snapshot_kind = 'LEGACY_OR_AMBIGUOUS'",
            name="zero_dte_session_origin_consistent",
        ),
        sa.ForeignKeyConstraint(["daily_run_id"], ["daily_collection_runs.id"]),
        sa.ForeignKeyConstraint(["raw_payload_id"], ["raw_vendor_payloads.id"]),
        sa.ForeignKeyConstraint(["scan_run_id"], ["scan_runs.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "ticker",
            "observation_date",
            "snapshot_kind",
            name="uq_zero_dte_session_ticker_date_kind",
        ),
    )
    op.create_index(
        "ix_zero_dte_canonical_history",
        ZERO_DTE_SESSION_TABLE,
        ["ticker", "snapshot_kind", "observation_date"],
    )


def downgrade() -> None:
    op.drop_index("ix_zero_dte_canonical_history", table_name=ZERO_DTE_SESSION_TABLE)
    op.drop_table(ZERO_DTE_SESSION_TABLE)

    op.drop_column(CONTRACT_TABLE, "open_interest_as_of")

    op.drop_constraint(
        "daily_coverage_vendor_oi_date_semantics", COVERAGE_TABLE, type_="check"
    )
    op.drop_constraint(
        "daily_coverage_activity_date_semantics", COVERAGE_TABLE, type_="check"
    )
    op.drop_constraint(
        "uq_daily_coverage_vendor_oi_date", COVERAGE_TABLE, type_="unique"
    )
    op.drop_constraint(
        "uq_daily_coverage_activity_market_date", COVERAGE_TABLE, type_="unique"
    )
    op.drop_column(COVERAGE_TABLE, "vendor_oi_date")
    op.drop_column(COVERAGE_TABLE, "activity_market_date")

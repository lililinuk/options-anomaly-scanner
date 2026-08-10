"""Create Phase 1 persistence foundation."""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "20260810_0001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "scan_runs",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("trigger", sa.String(32), nullable=False),
        sa.Column("status", sa.String(32), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True)),
        sa.Column("configuration_snapshot", postgresql.JSONB(), nullable=False),
        sa.PrimaryKeyConstraint("id", name="pk_scan_runs"),
    )
    op.create_table(
        "api_usage_audit",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("endpoint", sa.String(255), nullable=False),
        sa.Column("command", sa.String(128)),
        sa.Column("requested_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("ticker", sa.String(16)),
        sa.Column("expiration", sa.Date()),
        sa.Column("http_status", sa.Integer()),
        sa.Column("consumed_quota", sa.Boolean()),
        sa.Column("quota_remaining", sa.Integer()),
        sa.Column("rate_limit_remaining", sa.Integer()),
        sa.Column("request_id", sa.String(128), nullable=False),
        sa.Column("vendor_request_id", sa.String(128)),
        sa.Column("latency_ms", sa.Numeric(12, 3), nullable=False),
        sa.Column("attempt_count", sa.Integer(), nullable=False),
        sa.Column("error_code", sa.String(100)),
        sa.PrimaryKeyConstraint("id", name="pk_api_usage_audit"),
        sa.UniqueConstraint("request_id", name="uq_api_usage_audit_request_id"),
    )
    op.create_index(
        "ix_api_usage_requested_endpoint", "api_usage_audit", ["requested_at", "endpoint"]
    )
    op.create_table(
        "raw_vendor_payloads",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("scan_run_id", postgresql.UUID(as_uuid=True)),
        sa.Column("source", sa.String(40), nullable=False),
        sa.Column("endpoint", sa.String(255), nullable=False),
        sa.Column("request_id", sa.String(128), nullable=False),
        sa.Column("vendor_request_id", sa.String(128)),
        sa.Column("ticker", sa.String(16)),
        sa.Column("expiration", sa.Date()),
        sa.Column("observed_at", sa.DateTime(timezone=True)),
        sa.Column("received_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("payload_sha256", sa.String(64), nullable=False),
        sa.Column("payload", postgresql.JSONB(), nullable=False),
        sa.ForeignKeyConstraint(["scan_run_id"], ["scan_runs.id"], name="fk_raw_payload_scan"),
        sa.PrimaryKeyConstraint("id", name="pk_raw_vendor_payloads"),
        sa.UniqueConstraint("source", "request_id", name="uq_raw_payload_source_request"),
    )
    op.create_index("ix_raw_vendor_payloads_ticker", "raw_vendor_payloads", ["ticker"])
    op.create_index(
        "ix_raw_vendor_payloads_received_endpoint",
        "raw_vendor_payloads",
        ["received_at", "endpoint"],
    )
    op.create_table(
        "option_contract_observations",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("raw_payload_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("contract_symbol", sa.String(32), nullable=False),
        sa.Column("ticker", sa.String(16), nullable=False),
        sa.Column("expiration", sa.Date(), nullable=False),
        sa.Column("strike", sa.Numeric(18, 6), nullable=False),
        sa.Column("option_right", sa.String(1), nullable=False),
        sa.Column("observed_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("open_interest", sa.BigInteger()),
        sa.Column("volume", sa.BigInteger()),
        sa.Column("bid", sa.Numeric(18, 6)),
        sa.Column("ask", sa.Numeric(18, 6)),
        sa.Column("normalized_fields", postgresql.JSONB(), nullable=False),
        sa.ForeignKeyConstraint(
            ["raw_payload_id"], ["raw_vendor_payloads.id"], name="fk_observation_raw_payload"
        ),
        sa.PrimaryKeyConstraint("id", name="pk_option_contract_observations"),
        sa.UniqueConstraint(
            "raw_payload_id", "contract_symbol", name="uq_observation_raw_contract"
        ),
    )
    op.create_index(
        "ix_contract_observation_ticker_expiry_time",
        "option_contract_observations",
        ["ticker", "expiration", "observed_at"],
    )
    op.create_table(
        "signal_detections",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("scan_run_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("ticker", sa.String(16), nullable=False),
        sa.Column("detected_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("expiration", sa.Date(), nullable=False),
        sa.Column("dte_at_detection", sa.Integer(), nullable=False),
        sa.Column("bucket_at_detection", sa.String(32)),
        sa.Column("evidence", postgresql.JSONB(), nullable=False),
        sa.ForeignKeyConstraint(["scan_run_id"], ["scan_runs.id"], name="fk_detection_scan"),
        sa.PrimaryKeyConstraint("id", name="pk_signal_detections"),
    )
    op.create_index("ix_signal_detections_ticker", "signal_detections", ["ticker"])
    op.create_table(
        "position_lifecycle_events",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("detection_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("state", sa.String(32), nullable=False),
        sa.Column("recorded_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("evidence", postgresql.JSONB(), nullable=False),
        sa.Column("notes", sa.Text()),
        sa.ForeignKeyConstraint(
            ["detection_id"], ["signal_detections.id"], name="fk_lifecycle_detection"
        ),
        sa.PrimaryKeyConstraint("id", name="pk_position_lifecycle_events"),
    )
    op.create_index(
        "ix_lifecycle_detection_recorded",
        "position_lifecycle_events",
        ["detection_id", "recorded_at"],
    )


def downgrade() -> None:
    op.drop_table("position_lifecycle_events")
    op.drop_table("signal_detections")
    op.drop_table("option_contract_observations")
    op.drop_table("raw_vendor_payloads")
    op.drop_table("api_usage_audit")
    op.drop_table("scan_runs")

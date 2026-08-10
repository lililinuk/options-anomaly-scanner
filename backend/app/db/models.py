import uuid
from datetime import date, datetime
from decimal import Decimal
from typing import Any

from sqlalchemy import (
    BigInteger,
    Boolean,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class ScanRun(Base):
    __tablename__ = "scan_runs"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    trigger: Mapped[str] = mapped_column(String(32))
    status: Mapped[str] = mapped_column(String(32), default="created")
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    configuration_snapshot: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict)


class RawVendorPayload(Base):
    __tablename__ = "raw_vendor_payloads"
    __table_args__ = (
        UniqueConstraint("source", "request_id", name="uq_raw_payload_source_request"),
        Index("ix_raw_vendor_payloads_received_endpoint", "received_at", "endpoint"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    scan_run_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("scan_runs.id"))
    source: Mapped[str] = mapped_column(String(40), default="nightwatch")
    endpoint: Mapped[str] = mapped_column(String(255))
    request_id: Mapped[str] = mapped_column(String(128))
    vendor_request_id: Mapped[str | None] = mapped_column(String(128))
    ticker: Mapped[str | None] = mapped_column(String(16), index=True)
    expiration: Mapped[date | None] = mapped_column(Date)
    observed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    received_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    payload_sha256: Mapped[str] = mapped_column(String(64))
    payload: Mapped[dict[str, Any] | list[Any]] = mapped_column(JSONB)


class ApiUsageAudit(Base):
    __tablename__ = "api_usage_audit"
    __table_args__ = (Index("ix_api_usage_requested_endpoint", "requested_at", "endpoint"),)

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    endpoint: Mapped[str] = mapped_column(String(255))
    command: Mapped[str | None] = mapped_column(String(128))
    requested_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    ticker: Mapped[str | None] = mapped_column(String(16))
    expiration: Mapped[date | None] = mapped_column(Date)
    http_status: Mapped[int | None] = mapped_column(Integer)
    consumed_quota: Mapped[bool | None] = mapped_column(Boolean)
    quota_remaining: Mapped[int | None] = mapped_column(Integer)
    rate_limit_remaining: Mapped[int | None] = mapped_column(Integer)
    request_id: Mapped[str] = mapped_column(String(128), unique=True)
    vendor_request_id: Mapped[str | None] = mapped_column(String(128))
    latency_ms: Mapped[Decimal] = mapped_column(Numeric(12, 3))
    attempt_count: Mapped[int] = mapped_column(Integer)
    error_code: Mapped[str | None] = mapped_column(String(100))


class OptionContractObservation(Base):
    __tablename__ = "option_contract_observations"
    __table_args__ = (
        UniqueConstraint("raw_payload_id", "contract_symbol", name="uq_observation_raw_contract"),
        Index("ix_contract_observation_ticker_expiry_time", "ticker", "expiration", "observed_at"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    raw_payload_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("raw_vendor_payloads.id"))
    contract_symbol: Mapped[str] = mapped_column(String(32))
    ticker: Mapped[str] = mapped_column(String(16))
    expiration: Mapped[date] = mapped_column(Date)
    strike: Mapped[Decimal] = mapped_column(Numeric(18, 6))
    option_right: Mapped[str] = mapped_column(String(1))
    observed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    open_interest: Mapped[int | None] = mapped_column(BigInteger)
    volume: Mapped[int | None] = mapped_column(BigInteger)
    bid: Mapped[Decimal | None] = mapped_column(Numeric(18, 6))
    ask: Mapped[Decimal | None] = mapped_column(Numeric(18, 6))
    normalized_fields: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict)


class SignalDetection(Base):
    """Future detection record: detection fields are append-only historical facts."""

    __tablename__ = "signal_detections"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    scan_run_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("scan_runs.id"))
    ticker: Mapped[str] = mapped_column(String(16), index=True)
    detected_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    expiration: Mapped[date] = mapped_column(Date)
    dte_at_detection: Mapped[int] = mapped_column(Integer)
    bucket_at_detection: Mapped[str | None] = mapped_column(String(32))
    evidence: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict)

    lifecycle_events: Mapped[list["PositionLifecycleEvent"]] = relationship(
        back_populates="detection", order_by="PositionLifecycleEvent.recorded_at"
    )


class PositionLifecycleEvent(Base):
    """Append-only lifecycle history; never overwrite a prior state transition."""

    __tablename__ = "position_lifecycle_events"
    __table_args__ = (Index("ix_lifecycle_detection_recorded", "detection_id", "recorded_at"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    detection_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("signal_detections.id"))
    state: Mapped[str] = mapped_column(String(32))
    recorded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    evidence: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict)
    notes: Mapped[str | None] = mapped_column(Text)

    detection: Mapped[SignalDetection] = relationship(back_populates="lifecycle_events")


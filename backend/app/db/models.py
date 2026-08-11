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
    specification_version: Mapped[str | None] = mapped_column(String(64))
    market_date: Mapped[date | None] = mapped_column(Date)
    consumed_quota_units: Mapped[int] = mapped_column(Integer, default=0)
    network_attempts: Mapped[int] = mapped_column(Integer, default=0)
    cache_hits: Mapped[int] = mapped_column(Integer, default=0)
    fresh_requests: Mapped[int] = mapped_column(Integer, default=0)
    summary: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict)


class ScanStage(Base):
    __tablename__ = "scan_stages"
    __table_args__ = (UniqueConstraint("scan_run_id", "stage", name="uq_scan_stage_run_stage"),)

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    scan_run_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("scan_runs.id"))
    stage: Mapped[str] = mapped_column(String(32))
    status: Mapped[str] = mapped_column(String(32))
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    details: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict)


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
    scan_run_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("scan_runs.id"))
    endpoint: Mapped[str] = mapped_column(String(255))
    command: Mapped[str | None] = mapped_column(String(128))
    requested_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    ticker: Mapped[str | None] = mapped_column(String(16))
    expiration: Mapped[date | None] = mapped_column(Date)
    http_status: Mapped[int | None] = mapped_column(Integer)
    consumed_quota: Mapped[bool | None] = mapped_column(Boolean)
    quota_limit: Mapped[int | None] = mapped_column(Integer)
    quota_remaining: Mapped[int | None] = mapped_column(Integer)
    rate_limit: Mapped[int | None] = mapped_column(Integer)
    rate_limit_remaining: Mapped[int | None] = mapped_column(Integer)
    request_id: Mapped[str] = mapped_column(String(128), unique=True)
    vendor_request_id: Mapped[str | None] = mapped_column(String(128))
    latency_ms: Mapped[Decimal] = mapped_column(Numeric(12, 3))
    attempt_count: Mapped[int] = mapped_column(Integer)
    retry_count: Mapped[int] = mapped_column(Integer)
    error_code: Mapped[str | None] = mapped_column(String(100))


class MetadataRefresh(Base):
    """One immutable discovery response persisted as a metadata snapshot."""

    __tablename__ = "metadata_refreshes"
    __table_args__ = (Index("ix_metadata_refreshes_observed_at", "observed_at"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    raw_payload_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("raw_vendor_payloads.id"))
    observed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    source_request_id: Mapped[str] = mapped_column(String(128), unique=True)
    http_status: Mapped[int] = mapped_column(Integer)
    capability_count: Mapped[int] = mapped_column(Integer)

    capabilities: Mapped[list["CapabilitySnapshot"]] = relationship(
        back_populates="refresh",
        cascade="all, delete-orphan",
        order_by="CapabilitySnapshot.capability_identifier",
        lazy="selectin",
    )


class CapabilitySnapshot(Base):
    """Normalized account capability evidence from a single discover response."""

    __tablename__ = "capability_snapshots"
    __table_args__ = (
        UniqueConstraint(
            "source_request_id",
            "capability_identifier",
            name="uq_capability_snapshot_request_identifier",
        ),
        Index(
            "ix_capability_snapshots_identifier_observed",
            "capability_identifier",
            "observed_at",
        ),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    refresh_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("metadata_refreshes.id"))
    observed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    capability_identifier: Mapped[str] = mapped_column(String(160))
    available: Mapped[bool] = mapped_column(Boolean)
    coverage: Mapped[str | None] = mapped_column(String(160))
    weight: Mapped[int | None] = mapped_column(Integer)
    source_request_id: Mapped[str] = mapped_column(String(128))
    source_metadata: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict)

    refresh: Mapped[MetadataRefresh] = relationship(back_populates="capabilities")


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


class TickerScanResult(Base):
    __tablename__ = "ticker_scan_results"
    __table_args__ = (
        UniqueConstraint("scan_run_id", "ticker", name="uq_ticker_result_run_ticker"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    scan_run_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("scan_runs.id"))
    ticker: Mapped[str] = mapped_column(String(16), index=True)
    observed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    preliminary_score: Mapped[Decimal | None] = mapped_column(Numeric(8, 3))
    selected_for_deep_scan: Mapped[bool] = mapped_column(Boolean, default=False)
    data_completeness: Mapped[str] = mapped_column(String(32))
    raw_payload_ids: Mapped[list[str]] = mapped_column(JSONB, default=list)
    source_request_ids: Mapped[list[str]] = mapped_column(JSONB, default=list)
    specification_version: Mapped[str] = mapped_column(String(64))


class ExpiryObservation(Base):
    __tablename__ = "expiry_observations"
    __table_args__ = (
        UniqueConstraint(
            "scan_run_id", "ticker", "expiration", name="uq_expiry_observation_run_ticker_expiry"
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    scan_run_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("scan_runs.id"))
    ticker: Mapped[str] = mapped_column(String(16), index=True)
    expiration: Mapped[date] = mapped_column(Date)
    observed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    dte_at_detection: Mapped[int] = mapped_column(Integer)
    bucket_at_detection: Mapped[str] = mapped_column(String(32))
    current_dte: Mapped[int] = mapped_column(Integer)
    current_bucket: Mapped[str | None] = mapped_column(String(32))
    call_volume: Mapped[int | None] = mapped_column(BigInteger)
    put_volume: Mapped[int | None] = mapped_column(BigInteger)
    call_oi: Mapped[int | None] = mapped_column(BigInteger)
    put_oi: Mapped[int | None] = mapped_column(BigInteger)
    volume_share: Mapped[Decimal | None] = mapped_column(Numeric(12, 8))
    oi_share: Mapped[Decimal | None] = mapped_column(Numeric(12, 8))
    neighbor_ratio: Mapped[Decimal | None] = mapped_column(Numeric(12, 5))
    volume_skew: Mapped[Decimal | None] = mapped_column(Numeric(12, 8))
    oi_skew: Mapped[Decimal | None] = mapped_column(Numeric(12, 8))
    expiration_type: Mapped[str] = mapped_column(String(40))
    expiration_type_source: Mapped[str] = mapped_column(String(16))
    baseline_quality: Mapped[str] = mapped_column(String(32))
    preliminary_score: Mapped[Decimal] = mapped_column(Numeric(8, 3))
    preliminary_basis: Mapped[Decimal] = mapped_column(Numeric(8, 3))
    expiry_score: Mapped[Decimal | None] = mapped_column(Numeric(8, 3))
    expiry_score_basis: Mapped[Decimal | None] = mapped_column(Numeric(8, 3))
    classification: Mapped[str | None] = mapped_column(String(40))
    selected_for_deep_scan: Mapped[bool] = mapped_column(Boolean, default=False)
    components: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict)
    raw_payload_ids: Mapped[list[str]] = mapped_column(JSONB, default=list)
    source_request_ids: Mapped[list[str]] = mapped_column(JSONB, default=list)
    specification_version: Mapped[str] = mapped_column(String(64))


class ContractScanObservation(Base):
    __tablename__ = "contract_scan_observations"
    __table_args__ = (
        UniqueConstraint("scan_run_id", "contract_symbol", name="uq_contract_scan_run_symbol"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    scan_run_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("scan_runs.id"))
    expiry_observation_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("expiry_observations.id"))
    raw_payload_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("raw_vendor_payloads.id"))
    contract_symbol: Mapped[str] = mapped_column(String(64))
    ticker: Mapped[str] = mapped_column(String(16), index=True)
    expiration: Mapped[date] = mapped_column(Date)
    right: Mapped[str] = mapped_column(String(1))
    strike: Mapped[Decimal] = mapped_column(Numeric(18, 6))
    observed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    dte_at_detection: Mapped[int] = mapped_column(Integer)
    bucket_at_detection: Mapped[str] = mapped_column(String(32))
    current_dte: Mapped[int] = mapped_column(Integer)
    current_bucket: Mapped[str | None] = mapped_column(String(32))
    volume: Mapped[int] = mapped_column(BigInteger)
    previous_oi: Mapped[int] = mapped_column(BigInteger)
    volume_oi_ratio: Mapped[Decimal] = mapped_column(Numeric(18, 6))
    bid: Mapped[Decimal | None] = mapped_column(Numeric(18, 6))
    ask: Mapped[Decimal | None] = mapped_column(Numeric(18, 6))
    mid: Mapped[Decimal | None] = mapped_column(Numeric(18, 6))
    spread_pct: Mapped[Decimal | None] = mapped_column(Numeric(12, 8))
    last: Mapped[Decimal | None] = mapped_column(Numeric(18, 6))
    delta: Mapped[Decimal | None] = mapped_column(Numeric(12, 8))
    spot: Mapped[Decimal | None] = mapped_column(Numeric(18, 6))
    estimated_premium: Mapped[Decimal | None] = mapped_column(Numeric(22, 4))
    premium_quality: Mapped[str | None] = mapped_column(String(40))
    historical_robust_z: Mapped[Decimal | None] = mapped_column(Numeric(12, 5))
    intraday_burst_ratio: Mapped[Decimal | None] = mapped_column(Numeric(12, 5))
    anomaly_score: Mapped[Decimal] = mapped_column(Numeric(8, 3))
    score_basis_weight: Mapped[Decimal] = mapped_column(Numeric(8, 3))
    classification: Mapped[str] = mapped_column(String(24))
    is_candidate: Mapped[bool] = mapped_column(Boolean)
    hard_reject_reason: Mapped[str | None] = mapped_column(String(64))
    risk_flags: Mapped[list[str]] = mapped_column(JSONB, default=list)
    components: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict)
    source_request_ids: Mapped[list[str]] = mapped_column(JSONB, default=list)
    specification_version: Mapped[str] = mapped_column(String(64))


class StrikeCluster(Base):
    __tablename__ = "strike_clusters"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    scan_run_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("scan_runs.id"))
    expiry_observation_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("expiry_observations.id"))
    ticker: Mapped[str] = mapped_column(String(16), index=True)
    expiration: Mapped[date] = mapped_column(Date)
    right: Mapped[str] = mapped_column(String(1))
    min_strike: Mapped[Decimal] = mapped_column(Numeric(18, 6))
    max_strike: Mapped[Decimal] = mapped_column(Numeric(18, 6))
    contract_count: Mapped[int] = mapped_column(Integer)
    total_volume: Mapped[int] = mapped_column(BigInteger)
    total_estimated_premium: Mapped[Decimal | None] = mapped_column(Numeric(22, 4))
    total_oi: Mapped[int] = mapped_column(BigInteger)
    premium_share: Mapped[Decimal | None] = mapped_column(Numeric(12, 8))
    volume_share: Mapped[Decimal | None] = mapped_column(Numeric(12, 8))
    premium_weighted_strike: Mapped[Decimal | None] = mapped_column(Numeric(18, 6))
    cluster_score: Mapped[Decimal] = mapped_column(Numeric(8, 3))
    score_basis_weight: Mapped[Decimal] = mapped_column(Numeric(8, 3))
    classification: Mapped[str] = mapped_column(String(32))
    shape: Mapped[str] = mapped_column(String(24))
    source_contract_ids: Mapped[list[str]] = mapped_column(JSONB, default=list)
    components: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict)
    specification_version: Mapped[str] = mapped_column(String(64))


class BucketPositioningSummary(Base):
    __tablename__ = "bucket_positioning_summaries"
    __table_args__ = (
        UniqueConstraint(
            "scan_run_id", "ticker", "bucket", name="uq_bucket_summary_run_ticker_bucket"
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    scan_run_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("scan_runs.id"))
    ticker: Mapped[str] = mapped_column(String(16), index=True)
    bucket: Mapped[str] = mapped_column(String(32))
    observed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    strongest_expiry_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("expiry_observations.id")
    )
    strongest_call_contract_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("contract_scan_observations.id")
    )
    strongest_put_contract_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("contract_scan_observations.id")
    )
    strongest_call_cluster_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("strike_clusters.id")
    )
    strongest_put_cluster_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("strike_clusters.id")
    )
    positioning_label: Mapped[str] = mapped_column(String(32))
    day_zero_status: Mapped[str | None] = mapped_column(String(48))
    oi_status: Mapped[str] = mapped_column(String(24))
    data_completeness: Mapped[str] = mapped_column(String(32))
    metrics: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict)
    specification_version: Mapped[str] = mapped_column(String(64))


class OiConfirmationEvent(Base):
    __tablename__ = "oi_confirmation_events"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    scan_run_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("scan_runs.id"))
    contract_observation_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("contract_scan_observations.id")
    )
    status: Mapped[str] = mapped_column(String(24))
    observed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    evidence: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict)
    source_request_ids: Mapped[list[str]] = mapped_column(JSONB, default=list)
    specification_version: Mapped[str] = mapped_column(String(64))


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

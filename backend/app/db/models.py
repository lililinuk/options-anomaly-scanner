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
    radar_threshold_profile_id: Mapped[str | None] = mapped_column(String(64))
    radar_threshold_profile_version: Mapped[str | None] = mapped_column(String(64))
    radar_threshold_config_hash: Mapped[str | None] = mapped_column(String(64))


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
    activity_context: Mapped[dict[str, Any] | None] = mapped_column(JSONB)


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
    preliminary_score: Mapped[Decimal | None] = mapped_column(Numeric(8, 3))
    preliminary_basis: Mapped[Decimal] = mapped_column(Numeric(8, 3))
    expiry_score: Mapped[Decimal | None] = mapped_column(Numeric(8, 3))
    expiry_score_basis: Mapped[Decimal | None] = mapped_column(Numeric(8, 3))
    classification: Mapped[str | None] = mapped_column(String(40))
    selected_for_deep_scan: Mapped[bool] = mapped_column(Boolean, default=False)
    components: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict)
    raw_payload_ids: Mapped[list[str]] = mapped_column(JSONB, default=list)
    source_request_ids: Mapped[list[str]] = mapped_column(JSONB, default=list)
    specification_version: Mapped[str] = mapped_column(String(64))
    vendor_oi_date: Mapped[date | None] = mapped_column(Date)
    call_oi_share: Mapped[Decimal | None] = mapped_column(Numeric(12, 8))
    put_oi_share: Mapped[Decimal | None] = mapped_column(Numeric(12, 8))
    same_day_activity_score: Mapped[Decimal | None] = mapped_column(Numeric(8, 3))
    same_day_score_basis_weight: Mapped[Decimal | None] = mapped_column(Numeric(8, 3))
    same_day_data_coverage: Mapped[Decimal | None] = mapped_column(Numeric(8, 3))
    missing_same_day_components: Mapped[list[str] | None] = mapped_column(JSONB)
    persistent_positioning_score: Mapped[Decimal | None] = mapped_column(Numeric(8, 3))
    persistent_state: Mapped[str | None] = mapped_column(String(32))
    persistent_winning_window: Mapped[int | None] = mapped_column(Integer)
    history_confidence: Mapped[str | None] = mapped_column(String(16))
    persistent_components: Mapped[dict[str, Any] | None] = mapped_column(JSONB)
    discovery_score: Mapped[Decimal | None] = mapped_column(Numeric(8, 3))
    discovery_source: Mapped[str | None] = mapped_column(String(16))
    structural_cold_start_eligible: Mapped[bool] = mapped_column(Boolean, default=False)
    current_expiry_volume: Mapped[int | None] = mapped_column(BigInteger)
    same_day_baseline_status: Mapped[str | None] = mapped_column(String(32))
    baseline_observation_count: Mapped[int | None] = mapped_column(Integer)
    baseline_20_mean_volume_share: Mapped[Decimal | None] = mapped_column(Numeric(12, 8))
    baseline_20_median_volume_share: Mapped[Decimal | None] = mapped_column(Numeric(12, 8))
    baseline_20_mad_volume_share: Mapped[Decimal | None] = mapped_column(Numeric(12, 8))
    historical_percentile_20: Mapped[Decimal | None] = mapped_column(Numeric(12, 8))
    robust_deviation: Mapped[Decimal | None] = mapped_column(Numeric(18, 8))
    zero_dte_baseline_method: Mapped[str | None] = mapped_column(String(48))
    comparable_peer_count: Mapped[int | None] = mapped_column(Integer)
    comparable_peer_dtes: Mapped[list[int] | None] = mapped_column(JSONB)
    comparable_peer_quality: Mapped[str | None] = mapped_column(String(32))
    comparable_peer_median_volume: Mapped[Decimal | None] = mapped_column(Numeric(18, 3))
    discovery_primary_score: Mapped[Decimal | None] = mapped_column(Numeric(8, 3))
    discovery_secondary_score: Mapped[Decimal | None] = mapped_column(Numeric(8, 3))
    discovery_confirmation_bonus: Mapped[Decimal | None] = mapped_column(Numeric(8, 3))
    discovery_evidence_breadth: Mapped[int | None] = mapped_column(Integer)
    radar_route_eligible: Mapped[bool] = mapped_column(Boolean, default=False)
    persistent_route_eligible: Mapped[bool] = mapped_column(Boolean, default=False)
    expiry_activity_route_eligible: Mapped[bool] = mapped_column(Boolean, default=False)
    trigger_sources: Mapped[list[str]] = mapped_column(JSONB, default=list)
    deep_dive_eligible: Mapped[bool] = mapped_column(Boolean, default=False)
    standard_monthly_inferred: Mapped[bool] = mapped_column(Boolean, default=False)
    monthly_context_source: Mapped[str | None] = mapped_column(String(16))
    volume_share_points: Mapped[Decimal | None] = mapped_column(Numeric(8, 3))
    neighbor_points: Mapped[Decimal | None] = mapped_column(Numeric(8, 3))
    same_day_score_basis: Mapped[str | None] = mapped_column(String(32))


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
    volume: Mapped[int | None] = mapped_column(BigInteger)
    previous_oi: Mapped[int | None] = mapped_column(BigInteger)
    volume_oi_ratio: Mapped[Decimal | None] = mapped_column(Numeric(18, 6))
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
    anomaly_score: Mapped[Decimal | None] = mapped_column(Numeric(8, 3))
    score_basis_weight: Mapped[Decimal | None] = mapped_column(Numeric(8, 3))
    classification: Mapped[str] = mapped_column(String(24))
    is_candidate: Mapped[bool] = mapped_column(Boolean)
    hard_reject_reason: Mapped[str | None] = mapped_column(String(64))
    risk_flags: Mapped[list[str]] = mapped_column(JSONB, default=list)
    components: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict)
    source_request_ids: Mapped[list[str]] = mapped_column(JSONB, default=list)
    specification_version: Mapped[str] = mapped_column(String(64))
    current_oi: Mapped[int | None] = mapped_column(BigInteger)
    contract_oi_share: Mapped[Decimal | None] = mapped_column(Numeric(12, 8))
    neighbor_strike_ratio: Mapped[Decimal | None] = mapped_column(Numeric(12, 5))
    structure_score: Mapped[Decimal | None] = mapped_column(Numeric(8, 3))
    structure_components: Mapped[dict[str, Any] | None] = mapped_column(JSONB)
    persistent_positioning_score: Mapped[Decimal | None] = mapped_column(Numeric(8, 3))
    persistent_state: Mapped[str | None] = mapped_column(String(32))
    persistent_winning_window: Mapped[int | None] = mapped_column(Integer)
    history_observation_count: Mapped[int | None] = mapped_column(Integer)
    history_confidence: Mapped[str | None] = mapped_column(String(16))
    persistent_components: Mapped[dict[str, Any] | None] = mapped_column(JSONB)
    oi_change_radar_status: Mapped[str | None] = mapped_column(String(24))
    oi_change_radar_evidence: Mapped[dict[str, Any] | None] = mapped_column(JSONB)
    radar_route_eligible: Mapped[bool] = mapped_column(Boolean, default=False)
    persistent_route_eligible: Mapped[bool] = mapped_column(Boolean, default=False)
    trigger_sources: Mapped[list[str]] = mapped_column(JSONB, default=list)
    deep_dive_eligible: Mapped[bool] = mapped_column(Boolean, default=False)


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
    total_volume: Mapped[int | None] = mapped_column(BigInteger)
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
    cluster_oi_share: Mapped[Decimal | None] = mapped_column(Numeric(12, 8))
    positioning_center: Mapped[Decimal | None] = mapped_column(Numeric(18, 6))
    persistent_build_count: Mapped[int | None] = mapped_column(Integer)
    persistent_decline_count: Mapped[int | None] = mapped_column(Integer)
    oi_weighted_persistent_score: Mapped[Decimal | None] = mapped_column(Numeric(8, 3))
    cluster_net_oi_changes: Mapped[dict[str, Any] | None] = mapped_column(JSONB)


class DailyOiArchiveRun(Base):
    __tablename__ = "daily_oi_archive_runs"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    trigger: Mapped[str] = mapped_column(String(32))
    status: Mapped[str] = mapped_column(String(48))
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    configuration_snapshot: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict)
    specification_version: Mapped[str] = mapped_column(String(64))
    consumed_quota_units: Mapped[int] = mapped_column(Integer, default=0)
    network_attempts: Mapped[int] = mapped_column(Integer, default=0)
    summary: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict)


class DailyCollectionRun(Base):
    __tablename__ = "daily_collection_runs"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    trigger: Mapped[str] = mapped_column(String(32))
    status: Mapped[str] = mapped_column(String(32))
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    ny_market_date: Mapped[date] = mapped_column(Date)
    specification_version: Mapped[str] = mapped_column(String(64))
    radar_threshold_profile_id: Mapped[str] = mapped_column(String(64))
    radar_threshold_profile_version: Mapped[str] = mapped_column(String(64))
    radar_threshold_config_hash: Mapped[str] = mapped_column(String(64))
    configuration_snapshot: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict)
    subjobs: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict)
    consumed_quota_units: Mapped[int] = mapped_column(Integer, default=0)
    network_attempts: Mapped[int] = mapped_column(Integer, default=0)
    summary: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict)


class DailyCollectionCoverage(Base):
    __tablename__ = "daily_collection_coverage"
    __table_args__ = (
        UniqueConstraint(
            "subjob", "ticker", "observation_date", name="uq_daily_coverage_job_ticker_date"
        ),
        Index("ix_daily_coverage_job_date", "subjob", "observation_date"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    daily_run_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("daily_collection_runs.id"))
    subjob: Mapped[str] = mapped_column(String(24))
    ticker: Mapped[str] = mapped_column(String(16))
    observation_date: Mapped[date] = mapped_column(Date)
    vendor_as_of: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    captured_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    status: Mapped[str] = mapped_column(String(32))
    row_count: Mapped[int] = mapped_column(Integer, default=0)
    source_request_ids: Mapped[list[str]] = mapped_column(JSONB, default=list)
    details: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict)


class DailyExpiryActivitySnapshot(Base):
    __tablename__ = "daily_expiry_activity_snapshots"
    __table_args__ = (
        UniqueConstraint(
            "ticker", "expiration", "observation_date", name="uq_daily_activity_identity"
        ),
        Index("ix_daily_activity_history", "ticker", "expiration", "observation_date"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    daily_run_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("daily_collection_runs.id"))
    ticker: Mapped[str] = mapped_column(String(16))
    expiration: Mapped[date] = mapped_column(Date)
    observation_date: Mapped[date] = mapped_column(Date)
    captured_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    vendor_date: Mapped[date | None] = mapped_column(Date)
    vendor_as_of: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    dte: Mapped[int] = mapped_column(Integer)
    total_volume: Mapped[int] = mapped_column(BigInteger)
    ticker_scope_volume: Mapped[int] = mapped_column(BigInteger)
    volume_share: Mapped[Decimal | None] = mapped_column(Numeric(12, 8))
    call_volume_context: Mapped[int | None] = mapped_column(BigInteger)
    put_volume_context: Mapped[int | None] = mapped_column(BigInteger)
    raw_payload_ids: Mapped[list[str]] = mapped_column(JSONB, default=list)
    source_request_ids: Mapped[list[str]] = mapped_column(JSONB, default=list)
    specification_version: Mapped[str] = mapped_column(String(64))


class ZeroDteActivityDailySnapshot(Base):
    __tablename__ = "zero_dte_activity_daily_snapshots"
    __table_args__ = (
        UniqueConstraint(
            "ticker", "observation_date", name="uq_zero_dte_activity_ticker_date"
        ),
        Index("ix_zero_dte_activity_history", "ticker", "observation_date"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    scan_run_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("scan_runs.id"))
    daily_run_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("daily_collection_runs.id"))
    ticker: Mapped[str] = mapped_column(String(16))
    observation_date: Mapped[date] = mapped_column(Date)
    expiration: Mapped[date] = mapped_column(Date)
    expiry_volume: Mapped[int] = mapped_column(BigInteger)
    ticker_scope_volume: Mapped[int] = mapped_column(BigInteger)
    volume_share: Mapped[Decimal] = mapped_column(Numeric(12, 8))
    raw_cross_expiry_neighbor_ratio: Mapped[Decimal | None] = mapped_column(Numeric(18, 8))
    raw_payload_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("raw_vendor_payloads.id"))
    source_request_id: Mapped[str] = mapped_column(String(128))
    specification_version: Mapped[str] = mapped_column(String(64))


class DailyOiArchiveTicker(Base):
    __tablename__ = "daily_oi_archive_tickers"
    __table_args__ = (
        UniqueConstraint("archive_run_id", "ticker", name="uq_archive_ticker_run_ticker"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    archive_run_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("daily_oi_archive_runs.id"))
    ticker: Mapped[str] = mapped_column(String(16), index=True)
    vendor_oi_date: Mapped[date | None] = mapped_column(Date)
    vendor_oi_as_of: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    status: Mapped[str] = mapped_column(String(48))
    expiries_expected: Mapped[int] = mapped_column(Integer, default=0)
    complete_chains: Mapped[int] = mapped_column(Integer, default=0)
    incomplete_chains: Mapped[int] = mapped_column(Integer, default=0)
    contracts_persisted: Mapped[int] = mapped_column(Integer, default=0)
    details: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict)


class ExpiryOiDailySnapshot(Base):
    __tablename__ = "expiry_oi_daily_snapshots"
    __table_args__ = (
        UniqueConstraint(
            "ticker", "expiration", "vendor_oi_date", name="uq_expiry_oi_ticker_expiry_date"
        ),
        Index("ix_expiry_oi_history", "ticker", "expiration", "vendor_oi_date"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    archive_run_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("daily_oi_archive_runs.id"))
    ticker: Mapped[str] = mapped_column(String(16))
    expiration: Mapped[date] = mapped_column(Date)
    vendor_oi_date: Mapped[date] = mapped_column(Date)
    vendor_oi_as_of: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    call_oi: Mapped[int] = mapped_column(BigInteger)
    put_oi: Mapped[int] = mapped_column(BigInteger)
    total_oi: Mapped[int] = mapped_column(BigInteger)
    call_oi_share: Mapped[Decimal | None] = mapped_column(Numeric(12, 8))
    put_oi_share: Mapped[Decimal | None] = mapped_column(Numeric(12, 8))
    total_oi_share: Mapped[Decimal | None] = mapped_column(Numeric(12, 8))
    dte: Mapped[int] = mapped_column(Integer)
    bucket: Mapped[str] = mapped_column(String(32))
    chain_status: Mapped[str] = mapped_column(String(32), default="PENDING")
    raw_payload_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("raw_vendor_payloads.id"))
    source_request_id: Mapped[str] = mapped_column(String(128))
    specification_version: Mapped[str] = mapped_column(String(64))


class ContractOiDailySnapshot(Base):
    __tablename__ = "contract_oi_daily_snapshots"
    __table_args__ = (
        UniqueConstraint(
            "ticker", "contract_symbol", "vendor_oi_date", name="uq_contract_oi_ticker_symbol_date"
        ),
        Index("ix_contract_oi_history", "ticker", "contract_symbol", "vendor_oi_date"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    archive_run_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("daily_oi_archive_runs.id"))
    ticker: Mapped[str] = mapped_column(String(16))
    contract_symbol: Mapped[str] = mapped_column(String(64))
    vendor_oi_date: Mapped[date] = mapped_column(Date)
    vendor_oi_as_of: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    expiration: Mapped[date] = mapped_column(Date)
    right: Mapped[str] = mapped_column(String(1))
    strike: Mapped[Decimal] = mapped_column(Numeric(18, 6))
    dte: Mapped[int] = mapped_column(Integer)
    bucket: Mapped[str] = mapped_column(String(32))
    open_interest: Mapped[int] = mapped_column(BigInteger)
    bid: Mapped[Decimal | None] = mapped_column(Numeric(18, 6))
    ask: Mapped[Decimal | None] = mapped_column(Numeric(18, 6))
    implied_volatility: Mapped[Decimal | None] = mapped_column(Numeric(18, 8))
    delta: Mapped[Decimal | None] = mapped_column(Numeric(12, 8))
    gamma: Mapped[Decimal | None] = mapped_column(Numeric(18, 10))
    theta: Mapped[Decimal | None] = mapped_column(Numeric(18, 8))
    vega: Mapped[Decimal | None] = mapped_column(Numeric(18, 8))
    charm: Mapped[Decimal | None] = mapped_column(Numeric(18, 8))
    underlying_price: Mapped[Decimal | None] = mapped_column(Numeric(18, 6))
    quote_as_of: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    greeks_as_of: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    underlying_as_of: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    raw_payload_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("raw_vendor_payloads.id"))
    source_request_id: Mapped[str] = mapped_column(String(128))
    specification_version: Mapped[str] = mapped_column(String(64))


class OiChangeRadarObservation(Base):
    __tablename__ = "oi_change_radar_observations"
    __table_args__ = (
        UniqueConstraint(
            "ticker", "contract_symbol", "observation_date", name="uq_oi_radar_identity"
        ),
        Index("ix_oi_radar_ticker_date", "ticker", "observation_date"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    scan_run_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("scan_runs.id"))
    daily_run_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("daily_collection_runs.id"))
    ticker: Mapped[str] = mapped_column(String(16))
    contract_symbol: Mapped[str] = mapped_column(String(64))
    observation_date: Mapped[date | None] = mapped_column(Date)
    previous_date: Mapped[date | None] = mapped_column(Date)
    previous_oi: Mapped[int | None] = mapped_column(BigInteger)
    current_oi: Mapped[int | None] = mapped_column(BigInteger)
    delta_oi: Mapped[int | None] = mapped_column(BigInteger)
    relative_oi_change: Mapped[Decimal | None] = mapped_column(Numeric(18, 8))
    volume: Mapped[int | None] = mapped_column(BigInteger)
    trades: Mapped[int | None] = mapped_column(BigInteger)
    average_price: Mapped[Decimal | None] = mapped_column(Numeric(18, 6))
    premium: Mapped[Decimal | None] = mapped_column(Numeric(22, 4))
    rank: Mapped[int | None] = mapped_column(Integer)
    last_bid: Mapped[Decimal | None] = mapped_column(Numeric(18, 6))
    last_ask: Mapped[Decimal | None] = mapped_column(Numeric(18, 6))
    last_fill: Mapped[Decimal | None] = mapped_column(Numeric(18, 6))
    raw_payload_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("raw_vendor_payloads.id"))
    source_request_id: Mapped[str] = mapped_column(String(128))
    specification_version: Mapped[str] = mapped_column(String(64))
    captured_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    ny_market_date: Mapped[date | None] = mapped_column(Date)
    material_event_eligible: Mapped[bool | None] = mapped_column(Boolean)
    radar_route_eligible: Mapped[bool | None] = mapped_column(Boolean)
    eligibility_reason: Mapped[str | None] = mapped_column(String(64))
    threshold_profile_id: Mapped[str | None] = mapped_column(String(64))
    threshold_profile_version: Mapped[str | None] = mapped_column(String(64))
    threshold_config_hash: Mapped[str | None] = mapped_column(String(64))
    effective_thresholds: Mapped[dict[str, Any] | None] = mapped_column(JSONB)
    premium_per_trade: Mapped[Decimal | None] = mapped_column(Numeric(22, 6))
    volume_per_trade: Mapped[Decimal | None] = mapped_column(Numeric(18, 6))
    archive_match_status: Mapped[str | None] = mapped_column(String(32))
    matched_expiration: Mapped[date | None] = mapped_column(Date)
    matched_dte: Mapped[int | None] = mapped_column(Integer)
    matched_right: Mapped[str | None] = mapped_column(String(1))
    matched_strike: Mapped[Decimal | None] = mapped_column(Numeric(18, 6))
    archived_oi: Mapped[int | None] = mapped_column(BigInteger)
    archive_vendor_oi_date: Mapped[date | None] = mapped_column(Date)
    archive_completeness: Mapped[str | None] = mapped_column(String(32))
    contract_structure_score: Mapped[Decimal | None] = mapped_column(Numeric(8, 3))
    contract_persistent_score: Mapped[Decimal | None] = mapped_column(Numeric(8, 3))
    radar_scope: Mapped[str | None] = mapped_column(String(32))
    deep_dive_eligible: Mapped[bool | None] = mapped_column(Boolean)
    trigger_sources: Mapped[list[str] | None] = mapped_column(JSONB)
    risk_flags: Mapped[list[str] | None] = mapped_column(JSONB)


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


class Phase2bTickerContextSnapshot(Base):
    """Immutable shared ticker evidence used by one or more candidate evaluations."""

    __tablename__ = "phase2b_ticker_context_snapshots"
    __table_args__ = (
        Index("ix_phase2b_ticker_context_ticker_created", "ticker", "created_at"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    ticker: Mapped[str] = mapped_column(String(16), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    specification_version: Mapped[str] = mapped_column(String(64), nullable=False)
    config_version: Mapped[str] = mapped_column(String(64), nullable=False)
    config_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    effective_config: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)
    stock_state: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict)
    price_context: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict)
    iv_rank: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict)
    term_structure: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict)
    dealer_heatmap: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict)
    source_timestamps: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict)
    raw_payload_ids: Mapped[list[str]] = mapped_column(JSONB, default=list)
    source_request_ids: Mapped[list[str]] = mapped_column(JSONB, default=list)
    endpoint_statuses: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict)


class Phase2bCandidateEvaluation(Base):
    """Append-only context bound to one selected Phase 2A candidate."""

    __tablename__ = "phase2b_candidate_evaluations"
    __table_args__ = (
        UniqueConstraint(
            "ticker_context_id", "contract_symbol", name="uq_phase2b_context_contract"
        ),
        Index("ix_phase2b_candidate_symbol_evaluated", "contract_symbol", "evaluated_at"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    ticker_context_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("phase2b_ticker_context_snapshots.id"), nullable=False
    )
    contract_symbol: Mapped[str] = mapped_column(String(64), nullable=False)
    ticker: Mapped[str] = mapped_column(String(16), nullable=False)
    expiration: Mapped[date] = mapped_column(Date, nullable=False)
    right: Mapped[str] = mapped_column(String(1), nullable=False)
    strike: Mapped[Decimal] = mapped_column(Numeric(18, 6), nullable=False)
    dte_at_detection: Mapped[int | None] = mapped_column(Integer)
    evaluated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    trigger_sources: Mapped[list[str]] = mapped_column(JSONB, default=list)
    phase2a_evidence: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict)
    strike_location: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict)
    volatility_context: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict)
    dealer_context: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict)
    execution_context: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict)
    evidence_states: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict)
    source_timestamps: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict)
    direction: Mapped[str] = mapped_column(String(16), nullable=False)
    specification_version: Mapped[str] = mapped_column(String(64), nullable=False)
    config_version: Mapped[str] = mapped_column(String(64), nullable=False)
    config_hash: Mapped[str] = mapped_column(String(64), nullable=False)


class Phase2bCandidateState(Base):
    """Immutable v2 research state derived from one preserved candidate evaluation."""

    __tablename__ = "phase2b_candidate_states"
    __table_args__ = (
        UniqueConstraint(
            "candidate_evaluation_id",
            "specification_version",
            name="uq_phase2b_candidate_state_evaluation_spec",
        ),
        Index("ix_phase2b_candidate_state_symbol_evaluated", "contract_symbol", "evaluated_at"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    candidate_evaluation_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("phase2b_candidate_evaluations.id"), nullable=False
    )
    ticker_context_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("phase2b_ticker_context_snapshots.id"), nullable=False
    )
    contract_symbol: Mapped[str] = mapped_column(String(64), nullable=False)
    ticker: Mapped[str] = mapped_column(String(16), nullable=False)
    evaluated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    positioning_state: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)
    price_state: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)
    volatility_state: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)
    dealer_gex_state: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)
    execution_state: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)
    research_readiness: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)
    phase2a_provenance: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)
    direction: Mapped[str] = mapped_column(String(16), nullable=False)
    specification_version: Mapped[str] = mapped_column(String(64), nullable=False)
    source_context_specification_version: Mapped[str] = mapped_column(String(64), nullable=False)
    config_version: Mapped[str] = mapped_column(String(64), nullable=False)
    config_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    context_config_version: Mapped[str] = mapped_column(String(64), nullable=False)
    context_config_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    topology_rule_version: Mapped[str] = mapped_column(String(64), nullable=False)
    readiness_rule_version: Mapped[str] = mapped_column(String(64), nullable=False)


class Phase2bV3ResearchWorkspace(Base):
    """Immutable v3 research workspace derived only from preserved evidence."""

    __tablename__ = "phase2b_v3_research_workspaces"
    __table_args__ = (
        UniqueConstraint(
            "source_v2_state_id",
            "specification_version",
            name="uq_phase2b_v3_workspace_source_state_spec",
        ),
        Index(
            "ix_phase2b_v3_workspace_symbol_created",
            "contract_symbol",
            "created_at",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    source_v2_state_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("phase2b_candidate_states.id"), nullable=False
    )
    candidate_evaluation_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("phase2b_candidate_evaluations.id"), nullable=False
    )
    ticker_context_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("phase2b_ticker_context_snapshots.id"), nullable=False
    )
    contract_symbol: Mapped[str] = mapped_column(String(64), nullable=False)
    ticker: Mapped[str] = mapped_column(String(16), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    contract_identity: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)
    opportunity_positioning: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)
    underlying_price: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)
    volatility_context: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)
    dealer_gex_structure: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)
    execution_context: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)
    provenance: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)
    specification_version: Mapped[str] = mapped_column(String(64), nullable=False)
    config_version: Mapped[str] = mapped_column(String(64), nullable=False)
    config_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    primary_floor_rule_version: Mapped[str] = mapped_column(String(64), nullable=False)
    primary_upper_node_rule_version: Mapped[str] = mapped_column(String(64), nullable=False)
    below_floor_path_rule_version: Mapped[str] = mapped_column(String(64), nullable=False)
    adjacent_expiry_rule_version: Mapped[str] = mapped_column(String(64), nullable=False)


class DealerGexArchiveRun(Base):
    """One externally triggered, append-only MAG7 Dealer/GEX capture run."""

    __tablename__ = "dealer_gex_archive_runs"
    __table_args__ = (
        UniqueConstraint(
            "ny_market_date",
            "intended_capture_slot",
            "scope_key",
            name="uq_dealer_gex_run_market_date_slot_scope",
        ),
        Index("ix_dealer_gex_run_started", "started_at"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    trigger: Mapped[str] = mapped_column(String(32), nullable=False)
    status: Mapped[str] = mapped_column(String(48), nullable=False)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    ny_market_date: Mapped[date | None] = mapped_column(Date)
    intended_capture_slot: Mapped[str] = mapped_column(String(16), nullable=False)
    scope_key: Mapped[str] = mapped_column(String(128), nullable=False)
    market_timezone: Mapped[str] = mapped_column(String(64), nullable=False)
    universe: Mapped[list[str]] = mapped_column(JSONB, default=list)
    specification_version: Mapped[str] = mapped_column(String(64), nullable=False)
    config_version: Mapped[str] = mapped_column(String(64), nullable=False)
    config_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    configuration_snapshot: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict)
    tickers_attempted: Mapped[int] = mapped_column(Integer, default=0)
    tickers_succeeded: Mapped[int] = mapped_column(Integer, default=0)
    tickers_failed: Mapped[int] = mapped_column(Integer, default=0)
    observations_reused: Mapped[int] = mapped_column(Integer, default=0)
    usable_snapshots: Mapped[int] = mapped_column(Integer, default=0)
    degraded_snapshots: Mapped[int] = mapped_column(Integer, default=0)
    unavailable_snapshots: Mapped[int] = mapped_column(Integer, default=0)
    incomplete_snapshots: Mapped[int] = mapped_column(Integer, default=0)
    network_attempts: Mapped[int] = mapped_column(Integer, default=0)
    http_successes: Mapped[int] = mapped_column(Integer, default=0)
    http_failures: Mapped[int] = mapped_column(Integer, default=0)
    consumed_quota_units: Mapped[int] = mapped_column(Integer, default=0)
    quota_remaining_before: Mapped[int | None] = mapped_column(Integer)
    quota_remaining_after: Mapped[int | None] = mapped_column(Integer)
    summary: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict)


class DealerGexSnapshot(Base):
    """A vendor Dealer/GEX surface or an explicitly unavailable capture attempt."""

    __tablename__ = "dealer_gex_snapshots"
    __table_args__ = (
        UniqueConstraint(
            "archive_run_id", "ticker", name="uq_dealer_gex_snapshot_run_ticker"
        ),
        UniqueConstraint(
            "observation_identity", name="uq_dealer_gex_snapshot_observation_identity"
        ),
        Index(
            "ix_dealer_gex_snapshot_ticker_vendor_time",
            "ticker",
            "vendor_observed_at",
        ),
        Index(
            "ix_dealer_gex_snapshot_ticker_captured",
            "ticker",
            "captured_at",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    archive_run_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("dealer_gex_archive_runs.id"), nullable=False
    )
    ticker: Mapped[str] = mapped_column(String(16), nullable=False)
    vendor_observed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    captured_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    spot_usd: Mapped[Decimal | None] = mapped_column(Numeric(18, 6))
    source_quality: Mapped[str] = mapped_column(String(40), nullable=False)
    availability: Mapped[str] = mapped_column(String(24), nullable=False)
    endpoint: Mapped[str] = mapped_column(String(256), nullable=False)
    capability: Mapped[str] = mapped_column(String(96), nullable=False)
    endpoint_parameters: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict)
    source_request_id: Mapped[str | None] = mapped_column(String(128))
    raw_payload_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("raw_vendor_payloads.id")
    )
    source_http_status: Mapped[int | None] = mapped_column(Integer)
    safe_error_code: Mapped[str | None] = mapped_column(String(96))
    truncated: Mapped[bool] = mapped_column(Boolean, default=False)
    cell_count: Mapped[int] = mapped_column(Integer, default=0)
    expiration_count: Mapped[int] = mapped_column(Integer, default=0)
    surface_schema_version: Mapped[str] = mapped_column(String(64), nullable=False)
    observation_identity: Mapped[str | None] = mapped_column(String(64))
    is_analytical_observation: Mapped[bool] = mapped_column(Boolean, default=False)
    quality_details: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict)
    specification_version: Mapped[str] = mapped_column(String(64), nullable=False)
    config_version: Mapped[str] = mapped_column(String(64), nullable=False)
    config_hash: Mapped[str] = mapped_column(String(64), nullable=False)


class DealerGexSnapshotCell(Base):
    """One immutable expiration/strike cell from a usable archived surface."""

    __tablename__ = "dealer_gex_snapshot_cells"
    __table_args__ = (
        UniqueConstraint(
            "snapshot_id",
            "expiration",
            "strike",
            name="uq_dealer_gex_cell_snapshot_expiry_strike",
        ),
        Index(
            "ix_dealer_gex_cell_expiry_strike",
            "expiration",
            "strike",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    snapshot_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("dealer_gex_snapshots.id"), nullable=False
    )
    expiration: Mapped[date] = mapped_column(Date, nullable=False)
    strike: Mapped[Decimal] = mapped_column(Numeric(18, 6), nullable=False)
    net_dealer_gex_usd: Mapped[Decimal | None] = mapped_column(Numeric(32, 6))
    call_gex_usd: Mapped[Decimal | None] = mapped_column(Numeric(32, 6))
    put_gex_usd: Mapped[Decimal | None] = mapped_column(Numeric(32, 6))


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

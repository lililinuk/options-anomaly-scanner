from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, model_validator


class NightwatchPayload(BaseModel):
    """Forward-compatible envelope for vendor payloads that can evolve."""

    model_config = ConfigDict(extra="allow")


class HealthResponse(NightwatchPayload):
    status: str | None = None


class CapabilityDetail(NightwatchPayload):
    command: str | None = None
    capability: str | None = None
    name: str | None = None
    available: bool | None = None
    enabled: bool | None = None


class DiscoverResponse(NightwatchPayload):
    capabilities: Any = Field(default_factory=list)
    capabilities_detail: list[CapabilityDetail | dict[str, Any]] = Field(default_factory=list)
    monthly_remaining: int | None = None
    quota: dict[str, Any] | None = None
    rate_limit: dict[str, Any] | None = None

    @model_validator(mode="before")
    @classmethod
    def unwrap_vendor_envelope(cls, value: Any) -> Any:
        """The live REST response wraps discover fields in `data`."""

        if not isinstance(value, dict) or not isinstance(value.get("data"), dict):
            return value
        merged = dict(value)
        for key, child in value["data"].items():
            merged.setdefault(key, child)
        return merged


class QuotaMetadata(BaseModel):
    quota_limit: int | None = None
    quota_remaining: int | None = None
    quota_reset_at: datetime | None = None
    rate_limit: int | None = None
    rate_limit_remaining: int | None = None
    rate_limit_reset_epoch: int | None = None
    retry_after_seconds: float | None = None


class ApiUsageEvent(BaseModel):
    endpoint: str
    command: str | None = None
    requested_at: datetime
    ticker: str | None = None
    expiration: str | None = None
    http_status: int | None = None
    consumed_quota: bool | None = None
    quota_remaining: int | None = None
    rate_limit_remaining: int | None = None
    request_id: str
    vendor_request_id: str | None = None
    latency_ms: float
    attempt_count: int
    error_code: str | None = None


class NightwatchResult(BaseModel):
    payload: Any
    status_code: int
    request_id: str
    vendor_request_id: str | None = None
    quota: QuotaMetadata

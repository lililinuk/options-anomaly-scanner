from dataclasses import dataclass, field
from datetime import datetime
from typing import Protocol

from app.nightwatch.client import NightwatchClient
from app.nightwatch.errors import NightwatchError
from app.nightwatch.models import ApiUsageEvent, DiscoverResponse, NightwatchResult
from app.normalization.capabilities import NormalizedCapability, normalize_capabilities
from app.persistence.metadata import PersistedMetadataSummary


@dataclass
class ApiUsageCollector:
    events: list[ApiUsageEvent] = field(default_factory=list)

    def __call__(self, event: ApiUsageEvent) -> None:
        self.events.append(event)

    @property
    def latest(self) -> ApiUsageEvent:
        if not self.events:
            raise RuntimeError("Nightwatch request did not emit an API usage observation")
        return self.events[-1]


class MetadataStore(Protocol):
    def persist_refresh(
        self,
        *,
        result: NightwatchResult,
        usage_event: ApiUsageEvent,
        capabilities: list[NormalizedCapability],
    ) -> PersistedMetadataSummary: ...

    def persist_usage_only(self, event: ApiUsageEvent) -> None: ...


@dataclass(frozen=True)
class MetadataRefreshSummary:
    observed_at: datetime
    source_request_id: str
    capability_count: int
    available_count: int
    http_status: int
    quota_limit: int | None
    quota_remaining: int | None
    rate_limit: int | None
    rate_limit_remaining: int | None
    retry_count: int
    created: bool


async def refresh_metadata(
    *,
    client: NightwatchClient,
    store: MetadataStore,
    usage_collector: ApiUsageCollector,
) -> MetadataRefreshSummary:
    """Fetch, parse, normalize, persist, and verify one discover snapshot."""

    try:
        result = await client.request("GET", "/v1/discover", command="discover")
    except NightwatchError:
        if usage_collector.events:
            store.persist_usage_only(usage_collector.latest)
        raise

    usage = usage_collector.latest
    parsed = DiscoverResponse.model_validate(result.payload)
    source_request_id = result.vendor_request_id or result.request_id
    capabilities = normalize_capabilities(
        parsed,
        observed_at=usage.requested_at,
        source_request_id=source_request_id,
    )
    persisted = store.persist_refresh(
        result=result,
        usage_event=usage,
        capabilities=capabilities,
    )
    return MetadataRefreshSummary(
        observed_at=persisted.observed_at,
        source_request_id=persisted.source_request_id,
        capability_count=persisted.capability_count,
        available_count=persisted.available_count,
        http_status=result.status_code,
        quota_limit=usage.quota_limit,
        quota_remaining=usage.quota_remaining,
        rate_limit=usage.rate_limit,
        rate_limit_remaining=usage.rate_limit_remaining,
        retry_count=usage.retry_count,
        created=persisted.created,
    )

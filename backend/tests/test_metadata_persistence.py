import json
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import httpx
import pytest
from pydantic import SecretStr

from app.db.models import (
    ApiUsageAudit,
    CapabilitySnapshot,
    MetadataRefresh,
    RawVendorPayload,
)
from app.metadata.service import ApiUsageCollector, refresh_metadata
from app.nightwatch.client import NightwatchClient
from app.nightwatch.models import ApiUsageEvent, DiscoverResponse, NightwatchResult, QuotaMetadata
from app.normalization.capabilities import normalize_capabilities
from app.persistence.api_usage import persist_api_usage
from app.persistence.metadata import MetadataRepository, PersistedMetadataSummary


def usage_event(request_id: str = "client-request") -> ApiUsageEvent:
    return ApiUsageEvent(
        endpoint="/v1/discover",
        command="discover",
        requested_at=datetime(2026, 8, 10, 12, 0, tzinfo=timezone.utc),
        http_status=200,
        consumed_quota=False,
        quota_limit=100000,
        quota_remaining=99999,
        rate_limit=60,
        rate_limit_remaining=59,
        request_id=request_id,
        vendor_request_id="vendor-request",
        latency_ms=12.3456,
        attempt_count=1,
        retry_count=0,
    )


class FakeSession:
    def __init__(self) -> None:
        self.rows: list[Any] = []
        self.commits = 0
        self.rollbacks = 0

    def scalar(self, statement: Any) -> Any:
        sql = str(statement)
        if "count(capability_snapshots.id)" in sql:
            rows = [row for row in self.rows if isinstance(row, CapabilitySnapshot)]
            if "capability_snapshots.available IS true" in sql:
                return sum(row.available for row in rows)
            return len(rows)
        if "FROM metadata_refreshes" in sql:
            return next((row for row in self.rows if isinstance(row, MetadataRefresh)), None)
        if "FROM api_usage_audit" in sql:
            return next((row for row in self.rows if isinstance(row, ApiUsageAudit)), None)
        return None

    def add(self, row: Any) -> None:
        if isinstance(row, (RawVendorPayload, MetadataRefresh)) and row.id is None:
            row.id = uuid.uuid4()
        self.rows.append(row)

    def add_all(self, rows: list[Any]) -> None:
        self.rows.extend(rows)

    def flush(self) -> None:
        return None

    def commit(self) -> None:
        self.commits += 1

    def rollback(self) -> None:
        self.rollbacks += 1


def discover_payload() -> dict[str, Any]:
    fixture = Path(__file__).parent / "fixtures" / "discover.json"
    return json.loads(fixture.read_text(encoding="utf-8"))


def test_capability_and_usage_persistence_are_read_back_and_idempotent() -> None:
    session = FakeSession()
    event = usage_event()
    result = NightwatchResult(
        payload=discover_payload(),
        status_code=200,
        request_id=event.request_id,
        vendor_request_id=event.vendor_request_id,
        quota=QuotaMetadata(),
    )
    parsed = DiscoverResponse.model_validate(result.payload)
    capabilities = normalize_capabilities(
        parsed,
        observed_at=event.requested_at,
        source_request_id="vendor-request",
    )
    assert len(capabilities) == 3
    repository = MetadataRepository(session)  # type: ignore[arg-type]

    first = repository.persist_refresh(
        result=result,
        usage_event=event,
        capabilities=capabilities,
    )
    second = repository.persist_refresh(
        result=result,
        usage_event=event,
        capabilities=capabilities,
    )

    assert first.created is True
    assert second.created is False
    assert first.capability_count == len(capabilities)
    assert len([row for row in session.rows if isinstance(row, MetadataRefresh)]) == 1
    assert len([row for row in session.rows if isinstance(row, ApiUsageAudit)]) == 1
    assert len([row for row in session.rows if isinstance(row, RawVendorPayload)]) == 1
    assert len([row for row in session.rows if isinstance(row, CapabilitySnapshot)]) == len(
        capabilities
    )
    assert all(
        "Authorization" not in row.source_metadata
        for row in session.rows
        if isinstance(row, CapabilitySnapshot)
    )


def test_api_usage_persistence_includes_required_quota_and_retry_fields() -> None:
    session = FakeSession()
    row = persist_api_usage(session, usage_event())  # type: ignore[arg-type]

    assert row.quota_limit == 100000
    assert row.quota_remaining == 99999
    assert row.rate_limit == 60
    assert row.rate_limit_remaining == 59
    assert row.retry_count == 0
    assert row.consumed_quota is False
    assert row.latency_ms.as_tuple().exponent == -3


class RecordingStore:
    def __init__(self) -> None:
        self.capabilities = []
        self.usage = None

    def persist_refresh(self, *, result, usage_event, capabilities):  # type: ignore[no-untyped-def]
        self.capabilities = capabilities
        self.usage = usage_event
        return PersistedMetadataSummary(
            source_request_id=result.vendor_request_id,
            capability_count=len(capabilities),
            available_count=sum(item.available for item in capabilities),
            observed_at=usage_event.requested_at,
            created=True,
        )

    def persist_usage_only(self, event):  # type: ignore[no-untyped-def]
        self.usage = event


@pytest.mark.asyncio
async def test_metadata_refresh_uses_mocked_discover_and_preserves_coverage() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/v1/discover"
        return httpx.Response(
            200,
            json=discover_payload(),
            headers={
                "X-Request-ID": "vendor-request",
                "X-Quota-Limit": "100000",
                "X-Quota-Remaining": "100000",
                "X-RateLimit-Limit": "60",
                "X-RateLimit-Remaining": "59",
            },
        )

    collector = ApiUsageCollector()
    store = RecordingStore()
    async with NightwatchClient(
        api_key=SecretStr("fixture-key"),
        transport=httpx.MockTransport(handler),
        usage_observer=collector,
    ) as client:
        summary = await refresh_metadata(
            client=client,
            store=store,
            usage_collector=collector,
        )

    assert summary.created is True
    assert summary.quota_remaining == 100000
    assert summary.retry_count == 0
    oi_expiry = next(
        item
        for item in store.capabilities
        if item.capability_identifier == "options.oi_per_expiry"
    )
    assert oi_expiry.coverage == "on-demand"
    assert store.usage.consumed_quota is False

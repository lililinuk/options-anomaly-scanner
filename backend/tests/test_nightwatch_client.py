import httpx
import pytest
from pydantic import SecretStr

from app.nightwatch.client import NightwatchClient
from app.nightwatch.errors import NightwatchError
from app.nightwatch.models import ApiUsageEvent


@pytest.mark.asyncio
async def test_health_response_and_quota_metadata_are_parsed() -> None:
    events: list[ApiUsageEvent] = []

    def handler(request: httpx.Request) -> httpx.Response:
        assert "authorization" not in request.headers
        return httpx.Response(
            200,
            json={"status": "ok", "service": "data-api"},
            headers={"X-Request-ID": "vendor-123", "X-Quota-Remaining": "99999"},
        )

    async def observe(event: ApiUsageEvent) -> None:
        events.append(event)

    async with NightwatchClient(
        transport=httpx.MockTransport(handler), usage_observer=observe
    ) as client:
        response = await client.health()

    assert response.status == "ok"
    assert events[0].vendor_request_id == "vendor-123"
    assert events[0].quota_remaining == 99999
    assert events[0].consumed_quota is False


@pytest.mark.asyncio
async def test_retries_429_then_succeeds_and_honors_zero_retry_after() -> None:
    calls = 0

    def handler(_: httpx.Request) -> httpx.Response:
        nonlocal calls
        calls += 1
        if calls == 1:
            return httpx.Response(429, json={"code": "RATE_LIMITED"}, headers={"Retry-After": "0"})
        return httpx.Response(200, json={"status": "ok"})

    async with NightwatchClient(transport=httpx.MockTransport(handler), max_retries=1) as client:
        assert (await client.health()).status == "ok"
    assert calls == 2


@pytest.mark.asyncio
async def test_non_retryable_4xx_is_structured_and_not_retried() -> None:
    calls = 0

    def handler(_: httpx.Request) -> httpx.Response:
        nonlocal calls
        calls += 1
        return httpx.Response(
            422,
            json={"error": {"code": "PARAM_INVALID", "message": "Bad expiration"}},
            headers={"X-Request-ID": "vendor-error"},
        )

    async with NightwatchClient(
        api_key=SecretStr("test-only"), transport=httpx.MockTransport(handler), max_retries=3
    ) as client:
        with pytest.raises(NightwatchError) as captured:
            await client.request("GET", "/v1/options/chain-snapshot/SPY")

    assert calls == 1
    assert captured.value.code == "PARAM_INVALID"
    assert captured.value.request_id == "vendor-error"
    assert not captured.value.retryable

import asyncio
import time
import uuid
from collections.abc import Awaitable, Callable, Mapping
from datetime import datetime, timezone
from typing import Any

import httpx
from pydantic import SecretStr

from app.nightwatch.errors import (
    NightwatchAuthenticationError,
    NightwatchError,
    NightwatchTransportError,
)
from app.nightwatch.models import (
    ApiUsageEvent,
    DiscoverResponse,
    HealthResponse,
    NightwatchResult,
)
from app.nightwatch.quota import parse_quota_headers
from app.nightwatch.retry import is_retryable_status

UsageObserver = Callable[[ApiUsageEvent], Awaitable[None] | None]
ZERO_QUOTA_PATHS = frozenset({"/v1/health", "/v1/discover", "/v1/openapi.json"})


class NightwatchClient:
    def __init__(
        self,
        *,
        base_url: str = "https://api.yehangshe.com",
        api_key: SecretStr | None = None,
        timeout_seconds: float = 20.0,
        max_retries: int = 3,
        max_concurrency: int = 4,
        transport: httpx.AsyncBaseTransport | None = None,
        usage_observer: UsageObserver | None = None,
    ) -> None:
        self._api_key = api_key
        self._max_retries = max_retries
        self._semaphore = asyncio.Semaphore(max_concurrency)
        self._usage_observer = usage_observer
        self._client = httpx.AsyncClient(
            base_url=base_url.rstrip("/"),
            timeout=httpx.Timeout(timeout_seconds),
            transport=transport,
            headers={"Accept": "application/json", "User-Agent": "options-anomaly-scanner/0.1"},
        )

    async def __aenter__(self) -> "NightwatchClient":
        return self

    async def __aexit__(self, *_: object) -> None:
        await self.aclose()

    async def aclose(self) -> None:
        await self._client.aclose()

    async def health(self) -> HealthResponse:
        result = await self.request("GET", "/v1/health", authenticated=False, command="health")
        return HealthResponse.model_validate(result.payload)

    async def discover(self) -> DiscoverResponse:
        result = await self.request("GET", "/v1/discover", command="discover")
        return DiscoverResponse.model_validate(result.payload)

    async def openapi(self) -> dict[str, Any]:
        result = await self.request(
            "GET", "/v1/openapi.json", authenticated=False, command="openapi"
        )
        if not isinstance(result.payload, dict):
            raise NightwatchError("OpenAPI response was not a JSON object")
        return result.payload

    async def request(
        self,
        method: str,
        path: str,
        *,
        params: Mapping[str, Any] | None = None,
        authenticated: bool = True,
        command: str | None = None,
        ticker: str | None = None,
        expiration: str | None = None,
    ) -> NightwatchResult:
        if authenticated and self._api_key is None:
            raise NightwatchAuthenticationError(
                "Nightwatch API key is not configured", code="KEY_MISSING"
            )

        request_id = str(uuid.uuid4())
        headers = {"X-Client-Request-ID": request_id}
        if authenticated:
            headers["Authorization"] = f"Bearer {self._api_key.get_secret_value()}"

        started_at = datetime.now(timezone.utc)
        started = time.perf_counter()
        response: httpx.Response | None = None
        last_transport_error: Exception | None = None
        attempts = 0

        async with self._semaphore:
            for attempt in range(self._max_retries + 1):
                attempts = attempt + 1
                try:
                    response = await self._client.request(
                        method.upper(), path, params=params, headers=headers
                    )
                except (httpx.TimeoutException, httpx.NetworkError) as exc:
                    last_transport_error = exc
                    if attempt >= self._max_retries or method.upper() not in {"GET", "HEAD"}:
                        break
                    await asyncio.sleep(min(0.25 * (2**attempt), 4.0))
                    continue

                if not is_retryable_status(response.status_code) or attempt >= self._max_retries:
                    break
                delay = parse_quota_headers(response.headers).retry_after_seconds
                await asyncio.sleep(delay if delay is not None else min(0.25 * (2**attempt), 4.0))

        latency_ms = (time.perf_counter() - started) * 1000
        if response is None:
            event = ApiUsageEvent(
                endpoint=path,
                command=command,
                requested_at=started_at,
                ticker=ticker,
                expiration=expiration,
                request_id=request_id,
                latency_ms=latency_ms,
                attempt_count=attempts,
                retry_count=max(0, attempts - 1),
                error_code="TRANSPORT_ERROR",
            )
            await self._observe(event)
            raise NightwatchTransportError(
                "Nightwatch request failed before receiving a response",
                request_id=request_id,
                retryable=True,
            ) from last_transport_error

        quota = parse_quota_headers(response.headers)
        vendor_request_id = response.headers.get("x-request-id")
        payload = _safe_json(response)
        error_code = _error_code(payload) if response.is_error else None
        event = ApiUsageEvent(
            endpoint=path,
            command=command,
            requested_at=started_at,
            ticker=ticker,
            expiration=expiration,
            http_status=response.status_code,
            consumed_quota=(
                False
                if path in ZERO_QUOTA_PATHS
                else (True if response.status_code == 200 else None)
            ),
            quota_limit=quota.quota_limit,
            quota_remaining=quota.quota_remaining,
            rate_limit=quota.rate_limit,
            rate_limit_remaining=quota.rate_limit_remaining,
            request_id=request_id,
            vendor_request_id=vendor_request_id,
            latency_ms=latency_ms,
            attempt_count=attempts,
            retry_count=max(0, attempts - 1),
            error_code=error_code,
        )
        await self._observe(event)

        if response.is_error:
            raise NightwatchError(
                _error_message(payload, response.status_code),
                status_code=response.status_code,
                code=error_code,
                request_id=vendor_request_id or request_id,
                retryable=is_retryable_status(response.status_code),
                details=payload,
            )
        return NightwatchResult(
            payload=payload,
            status_code=response.status_code,
            request_id=request_id,
            vendor_request_id=vendor_request_id,
            quota=quota,
        )

    async def _observe(self, event: ApiUsageEvent) -> None:
        if self._usage_observer is None:
            return
        result = self._usage_observer(event)
        if result is not None:
            await result


def _safe_json(response: httpx.Response) -> Any:
    try:
        return response.json()
    except ValueError:
        return {"raw_text": response.text[:1000]}


def _error_code(payload: Any) -> str | None:
    if not isinstance(payload, dict):
        return None
    error = payload.get("error")
    if isinstance(error, dict) and isinstance(error.get("code"), str):
        return error["code"]
    return payload.get("code") if isinstance(payload.get("code"), str) else None


def _error_message(payload: Any, status: int) -> str:
    if isinstance(payload, dict):
        error = payload.get("error")
        if isinstance(error, dict) and isinstance(error.get("message"), str):
            return error["message"]
        if isinstance(payload.get("message"), str):
            return payload["message"]
    return f"Nightwatch returned HTTP {status}"

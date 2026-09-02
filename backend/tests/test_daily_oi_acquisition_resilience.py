from __future__ import annotations

import copy
import uuid
from dataclasses import replace
from datetime import date, datetime, timezone
from types import SimpleNamespace
from typing import Any

import httpx
import pytest
from pydantic import SecretStr

from app.db.models import (
    CanonicalSchedulerSlot,
    ContractOiDailySnapshot,
    DailyOiArchiveTicker,
    ExpiryOiDailySnapshot,
)
from app.nightwatch.client import NightwatchClient
from app.nightwatch.errors import NightwatchError
from app.nightwatch.models import NightwatchResult, QuotaMetadata
from app.scanner import archive as archive_module
from app.scanner.archive import DailyOiArchiver, recovery_vendor_date_matches
from app.scanner.parsers import parse_complete_chain

VENDOR_DATE = date(2026, 8, 11)
EXPIRY_ONE = date(2026, 9, 18)
EXPIRY_TWO = date(2026, 10, 16)
EXPIRY_THREE = date(2026, 11, 20)


def _surface_payload(*expirations: date) -> dict[str, Any]:
    return {
        "data": {
            "as_of": "2026-08-11T04:00:00Z",
            "expiries": [
                {
                    "expiry": expiration.isoformat(),
                    "date": VENDOR_DATE.isoformat(),
                    "call_oi": 10,
                    "put_oi": 20,
                }
                for expiration in expirations
            ],
        }
    }


def _chain_payload(
    expiration: date,
    *,
    vendor_date: date = VENDOR_DATE,
    open_interest: object = 10,
) -> dict[str, Any]:
    return {
        "data": {
            "total_contracts": 2,
            "open_interest_as_of": f"{vendor_date.isoformat()}T10:30:00Z",
            "contracts": [
                {
                    "contract_symbol": f"NVDA{expiration:%y%m%d}C00200000",
                    "expiration": expiration.isoformat(),
                    "right": "C",
                    "strike_usd": 200,
                    "open_interest": open_interest,
                },
                {
                    "contract_symbol": f"NVDA{expiration:%y%m%d}P00200000",
                    "expiration": expiration.isoformat(),
                    "right": "P",
                    "strike_usd": 200,
                    "open_interest": 0,
                },
            ],
        },
        "_meta": {"truncated": False},
    }


def _result(payload: dict[str, Any], sequence: int) -> NightwatchResult:
    return NightwatchResult(
        payload=payload,
        status_code=200,
        request_id=f"client-{sequence}",
        vendor_request_id=f"vendor-{sequence}",
        quota=QuotaMetadata(),
    )


class _Session:
    def __init__(self) -> None:
        self.added: list[object] = []
        self.commits = 0

    def scalar(self, _statement: Any) -> Any:
        return None

    def add(self, row: object) -> None:
        if isinstance(row, DailyOiArchiveTicker):
            row.complete_chains = row.complete_chains or 0
            row.incomplete_chains = row.incomplete_chains or 0
            row.contracts_persisted = row.contracts_persisted or 0
        self.added.append(row)

    def commit(self) -> None:
        self.commits += 1


class _WaitClient:
    def __init__(self) -> None:
        self.waits: list[float] = []

    async def wait_for_materialization(self, delay_seconds: float) -> None:
        self.waits.append(delay_seconds)


def _ticker(session: _Session) -> DailyOiArchiveTicker:
    return next(row for row in session.added if isinstance(row, DailyOiArchiveTicker))


def _expiries(session: _Session) -> dict[date, ExpiryOiDailySnapshot]:
    return {
        row.expiration: row
        for row in session.added
        if isinstance(row, ExpiryOiDailySnapshot)
    }


def _contracts(session: _Session) -> list[ContractOiDailySnapshot]:
    return [row for row in session.added if isinstance(row, ContractOiDailySnapshot)]


@pytest.mark.asyncio
async def test_normal_full_complete_and_explicit_zero_remain_unchanged() -> None:
    session = _Session()
    client = _WaitClient()
    archiver = DailyOiArchiver(session, client)  # type: ignore[arg-type]
    archiver.run = SimpleNamespace(id=uuid.uuid4())
    calls: list[date] = []

    async def fetch(path: str, **kwargs: Any):  # type: ignore[no-untyped-def]
        if "oi-per-expiry" in path:
            return _result(_surface_payload(EXPIRY_ONE), 1), SimpleNamespace(id=uuid.uuid4())
        calls.append(kwargs["expiration"])
        return _result(_chain_payload(EXPIRY_ONE), 2), SimpleNamespace(id=uuid.uuid4())

    archiver._fetch = fetch  # type: ignore[method-assign]
    await archiver._archive_ticker("NVDA")

    assert calls == [EXPIRY_ONE]
    assert _ticker(session).status == "COMPLETE"
    assert _expiries(session)[EXPIRY_ONE].chain_status == "COMPLETE"
    assert [row.open_interest for row in _contracts(session)] == [10, 0]
    assert _ticker(session).details["recovery_attempts"] == 0
    assert client.waits == []


@pytest.mark.parametrize("invalid_value", [None, "unknown", object()])
def test_null_and_non_numeric_oi_remain_invalid_and_never_become_zero(
    invalid_value: object,
) -> None:
    parsed = parse_complete_chain(
        _chain_payload(EXPIRY_ONE, open_interest=invalid_value),
        EXPIRY_ONE,
    )

    assert parsed.complete is False
    assert parsed.reason == "INVALID_RESPONSE"
    assert parsed.invalid_row_reasons == {"INVALID_OPEN_INTEREST": 1}
    assert parsed.contracts == ()


def test_missing_oi_remains_invalid_and_is_not_materialized_as_zero() -> None:
    payload = _chain_payload(EXPIRY_ONE)
    del payload["data"]["contracts"][0]["open_interest"]

    parsed = parse_complete_chain(payload, EXPIRY_ONE)

    assert parsed.reason == "INVALID_RESPONSE"
    assert parsed.invalid_row_reasons == {"INVALID_OPEN_INTEREST": 1}
    assert parsed.contracts == ()


@pytest.mark.asyncio
async def test_invalid_response_is_deferred_once_and_full_retry_recovers() -> None:
    session = _Session()
    client = _WaitClient()
    archiver = DailyOiArchiver(session, client)  # type: ignore[arg-type]
    archiver.run = SimpleNamespace(id=uuid.uuid4())
    call_order: list[date] = []
    attempts = {EXPIRY_ONE: 0, EXPIRY_TWO: 0}

    async def fetch(path: str, **kwargs: Any):  # type: ignore[no-untyped-def]
        if "oi-per-expiry" in path:
            return (
                _result(_surface_payload(EXPIRY_ONE, EXPIRY_TWO), 1),
                SimpleNamespace(id=uuid.uuid4()),
            )
        expiration = kwargs["expiration"]
        call_order.append(expiration)
        attempts[expiration] += 1
        payload = _chain_payload(expiration)
        if expiration == EXPIRY_ONE and attempts[expiration] == 1:
            payload["data"]["contracts"][0]["open_interest"] = None
        return _result(payload, len(call_order) + 1), SimpleNamespace(id=uuid.uuid4())

    archiver._fetch = fetch  # type: ignore[method-assign]
    await archiver._archive_ticker("NVDA")

    assert call_order == [EXPIRY_ONE, EXPIRY_TWO, EXPIRY_ONE]
    assert attempts == {EXPIRY_ONE: 2, EXPIRY_TWO: 1}
    assert len(client.waits) == 1
    assert client.waits[0] > 0
    assert _ticker(session).status == "COMPLETE"
    assert _ticker(session).incomplete_chains == 0
    assert _ticker(session).details["recovered_chains"] == 1
    assert _ticker(session).details["deferred_recovery_history"][0]["final_outcome"] == (
        "FULL_COMPLETE"
    )
    assert len([row for row in _contracts(session) if row.expiration == EXPIRY_ONE]) == 2
    assert len([row for row in session.added if isinstance(row, ExpiryOiDailySnapshot)]) == 2
    assert not any(isinstance(row, CanonicalSchedulerSlot) for row in session.added)


@pytest.mark.asyncio
async def test_invalid_response_retry_still_invalid_stops_after_one_retry() -> None:
    session = _Session()
    archiver = DailyOiArchiver(session, _WaitClient())  # type: ignore[arg-type]
    archiver.run = SimpleNamespace(id=uuid.uuid4())
    chain_calls = 0

    async def fetch(path: str, **kwargs: Any):  # type: ignore[no-untyped-def]
        nonlocal chain_calls
        if "oi-per-expiry" in path:
            return _result(_surface_payload(EXPIRY_ONE), 1), SimpleNamespace(id=uuid.uuid4())
        chain_calls += 1
        payload = _chain_payload(kwargs["expiration"])
        payload["data"]["contracts"][0]["open_interest"] = None
        return _result(payload, chain_calls + 1), SimpleNamespace(id=uuid.uuid4())

    archiver._fetch = fetch  # type: ignore[method-assign]
    await archiver._archive_ticker("NVDA")

    assert chain_calls == 2
    assert _ticker(session).status == "PARTIAL_INCOMPLETE_CHAIN"
    assert _expiries(session)[EXPIRY_ONE].chain_status == "INVALID_RESPONSE"
    assert _ticker(session).details["recovery_attempts"] == 1
    assert _ticker(session).details["deferred_recovery_history"][0]["final_outcome"] == (
        "INVALID_RESPONSE"
    )
    assert _contracts(session) == []


@pytest.mark.asyncio
async def test_429_honors_retry_after_continues_later_expiry_then_recovers() -> None:
    session = _Session()
    client = _WaitClient()
    archiver = DailyOiArchiver(session, client)  # type: ignore[arg-type]
    archiver.run = SimpleNamespace(id=uuid.uuid4())
    call_order: list[date] = []
    attempts = {EXPIRY_ONE: 0, EXPIRY_TWO: 0}

    async def fetch(path: str, **kwargs: Any):  # type: ignore[no-untyped-def]
        if "oi-per-expiry" in path:
            return (
                _result(_surface_payload(EXPIRY_ONE, EXPIRY_TWO), 1),
                SimpleNamespace(id=uuid.uuid4()),
            )
        expiration = kwargs["expiration"]
        call_order.append(expiration)
        attempts[expiration] += 1
        if expiration == EXPIRY_ONE and attempts[expiration] == 1:
            raise NightwatchError(
                "rate limited",
                status_code=429,
                code="RATE_LIMITED",
                request_id="original-429",
                retryable=True,
                retry_after_seconds=4.0,
            )
        return (
            _result(_chain_payload(expiration), len(call_order) + 1),
            SimpleNamespace(id=uuid.uuid4()),
        )

    archiver._fetch = fetch  # type: ignore[method-assign]
    await archiver._archive_ticker("NVDA")

    assert call_order == [EXPIRY_ONE, EXPIRY_TWO, EXPIRY_ONE]
    assert client.waits == [4.0]
    assert _expiries(session)[EXPIRY_TWO].chain_status == "COMPLETE"
    assert _expiries(session)[EXPIRY_ONE].chain_status == "COMPLETE"
    assert _ticker(session).status == "COMPLETE"
    history = _ticker(session).details["deferred_recovery_history"]
    assert history[0]["original_outcome"] == "HTTP_429"
    assert history[0]["original_request_id"] == "original-429"
    assert history[0]["retry_attempt_number"] == 1
    assert history[0]["retry_executed_at"].endswith("+00:00")


@pytest.mark.asyncio
async def test_second_429_stays_incomplete_without_third_attempt() -> None:
    session = _Session()
    client = _WaitClient()
    archiver = DailyOiArchiver(session, client)  # type: ignore[arg-type]
    archiver.run = SimpleNamespace(id=uuid.uuid4())
    call_order: list[date] = []
    attempts = {EXPIRY_ONE: 0, EXPIRY_TWO: 0}

    async def fetch(path: str, **kwargs: Any):  # type: ignore[no-untyped-def]
        if "oi-per-expiry" in path:
            return (
                _result(_surface_payload(EXPIRY_ONE, EXPIRY_TWO), 1),
                SimpleNamespace(id=uuid.uuid4()),
            )
        expiration = kwargs["expiration"]
        call_order.append(expiration)
        attempts[expiration] += 1
        if expiration == EXPIRY_ONE:
            raise NightwatchError(
                "rate limited",
                status_code=429,
                code="RATE_LIMITED",
                request_id=f"rate-{attempts[expiration]}",
                retryable=True,
                retry_after_seconds=3.0,
            )
        return _result(_chain_payload(expiration), 3), SimpleNamespace(id=uuid.uuid4())

    archiver._fetch = fetch  # type: ignore[method-assign]
    await archiver._archive_ticker("NVDA")

    assert call_order == [EXPIRY_ONE, EXPIRY_TWO, EXPIRY_ONE]
    assert attempts[EXPIRY_ONE] == 2
    assert client.waits == [3.0]
    assert _expiries(session)[EXPIRY_ONE].chain_status == "TRANSIENT_RATE_LIMIT"
    assert _expiries(session)[EXPIRY_TWO].chain_status == "COMPLETE"
    assert _ticker(session).status == "PARTIAL_INCOMPLETE_CHAIN"
    assert _ticker(session).details["true_incomplete_chains"] == 1
    assert _ticker(session).details["deferred_recovery_history"][0]["final_outcome"] == (
        "TRANSIENT_RATE_LIMIT"
    )


@pytest.mark.asyncio
async def test_client_exposes_safe_retry_after_metadata_on_429() -> None:
    def handler(_request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            429,
            headers={"Retry-After": "6", "X-RateLimit-Reset": "1788323425"},
            json={"error": {"code": "RATE_LIMITED", "message": "slow down"}},
        )

    async with NightwatchClient(
        api_key=SecretStr("fixture-only"),
        transport=httpx.MockTransport(handler),
        max_retries=0,
    ) as client:
        with pytest.raises(NightwatchError) as raised:
            await client.request("GET", "/v1/options/chain-snapshot/NVDA")

    assert raised.value.status_code == 429
    assert raised.value.retry_after_seconds == 6
    assert raised.value.rate_limit_reset_epoch == 1788323425


def test_expected_recovery_vendor_date_is_required() -> None:
    expected = parse_complete_chain(_chain_payload(EXPIRY_ONE), EXPIRY_ONE)
    rolled = parse_complete_chain(
        _chain_payload(EXPIRY_ONE, vendor_date=date(2026, 8, 12)),
        EXPIRY_ONE,
    )

    assert recovery_vendor_date_matches(expected, VENDOR_DATE) is True
    assert recovery_vendor_date_matches(rolled, VENDOR_DATE) is False
    missing_as_of = copy.deepcopy(_chain_payload(EXPIRY_ONE))
    del missing_as_of["data"]["open_interest_as_of"]
    assert (
        recovery_vendor_date_matches(
            parse_complete_chain(missing_as_of, EXPIRY_ONE),
            VENDOR_DATE,
        )
        is False
    )


@pytest.mark.asyncio
async def test_rolled_forward_retry_never_persists_old_date_contracts() -> None:
    session = _Session()
    archiver = DailyOiArchiver(session, _WaitClient())  # type: ignore[arg-type]
    archiver.run = SimpleNamespace(id=uuid.uuid4())
    chain_calls = 0

    async def fetch(path: str, **kwargs: Any):  # type: ignore[no-untyped-def]
        nonlocal chain_calls
        if "oi-per-expiry" in path:
            return _result(_surface_payload(EXPIRY_ONE), 1), SimpleNamespace(id=uuid.uuid4())
        chain_calls += 1
        payload = _chain_payload(kwargs["expiration"])
        if chain_calls == 1:
            payload["data"]["contracts"][0]["open_interest"] = None
        else:
            payload["data"]["open_interest_as_of"] = "2026-08-12T10:30:00Z"
        return _result(payload, chain_calls + 1), SimpleNamespace(id=uuid.uuid4())

    archiver._fetch = fetch  # type: ignore[method-assign]
    await archiver._archive_ticker("NVDA")

    assert chain_calls == 2
    assert _contracts(session) == []
    assert _expiries(session)[EXPIRY_ONE].chain_status == "VENDOR_DATE_MISMATCH"
    assert _ticker(session).status == "PARTIAL_INCOMPLETE_CHAIN"
    assert _ticker(session).details["deferred_recovery_history"][0]["final_outcome"] == (
        "VENDOR_DATE_MISMATCH"
    )


@pytest.mark.asyncio
async def test_pathological_failures_obey_per_expiry_and_run_level_caps(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    limits = replace(
        archive_module.ARCHIVE_LIMITS,
        recovery_max_attempts_per_run=2,
        recovery_default_defer_seconds=0,
    )
    monkeypatch.setattr(archive_module, "ARCHIVE_LIMITS", limits)
    session = _Session()
    archiver = DailyOiArchiver(session, _WaitClient())  # type: ignore[arg-type]
    archiver.run = SimpleNamespace(id=uuid.uuid4())
    attempts = {EXPIRY_ONE: 0, EXPIRY_TWO: 0, EXPIRY_THREE: 0}

    async def fetch(path: str, **kwargs: Any):  # type: ignore[no-untyped-def]
        if "oi-per-expiry" in path:
            return (
                _result(_surface_payload(EXPIRY_ONE, EXPIRY_TWO, EXPIRY_THREE), 1),
                SimpleNamespace(id=uuid.uuid4()),
            )
        expiration = kwargs["expiration"]
        attempts[expiration] += 1
        payload = _chain_payload(expiration)
        payload["data"]["contracts"][0]["open_interest"] = None
        return _result(payload, sum(attempts.values()) + 1), SimpleNamespace(id=uuid.uuid4())

    archiver._fetch = fetch  # type: ignore[method-assign]
    await archiver._archive_ticker("NVDA")

    assert attempts == {EXPIRY_ONE: 2, EXPIRY_TWO: 2, EXPIRY_THREE: 1}
    assert archiver.recovery_attempts == 2
    assert all(count <= 2 for count in attempts.values())
    third = next(
        item
        for item in _ticker(session).details["incomplete_expiries"]
        if item["expiration"] == EXPIRY_THREE.isoformat()
    )
    assert third["recovery_disposition"] == "RUN_LEVEL_RECOVERY_CAP_REACHED"
    assert _contracts(session) == []


@pytest.mark.asyncio
async def test_successful_persistence_helper_is_idempotent() -> None:
    session = _Session()
    archiver = DailyOiArchiver(session, _WaitClient())  # type: ignore[arg-type]
    archiver.run = SimpleNamespace(id=uuid.uuid4())
    payload = _chain_payload(EXPIRY_ONE)
    chain = parse_complete_chain(payload, EXPIRY_ONE)
    snapshot = ExpiryOiDailySnapshot(
        archive_run_id=archiver.run.id,
        ticker="NVDA",
        expiration=EXPIRY_ONE,
        vendor_oi_date=VENDOR_DATE,
        vendor_oi_as_of=datetime(2026, 8, 11, 4, tzinfo=timezone.utc),
        call_oi=10,
        put_oi=20,
        total_oi=30,
        dte=38,
        bucket="MEDIUM",
        chain_status="INVALID_RESPONSE",
        raw_payload_id=uuid.uuid4(),
        source_request_id="surface",
        specification_version="fixture",
    )
    result = _result(payload, 1)
    raw = SimpleNamespace(id=uuid.uuid4())

    first = archiver._persist_complete_chain(
        ticker="NVDA",
        vendor_date=VENDOR_DATE,
        vendor_as_of=snapshot.vendor_oi_as_of,
        expiration=EXPIRY_ONE,
        expiry_snapshot=snapshot,
        chain_result=result,
        chain_raw=raw,
        chain=chain,
    )
    count_after_first = len(_contracts(session))
    second = archiver._persist_complete_chain(
        ticker="NVDA",
        vendor_date=VENDOR_DATE,
        vendor_as_of=snapshot.vendor_oi_as_of,
        expiration=EXPIRY_ONE,
        expiry_snapshot=snapshot,
        chain_result=result,
        chain_raw=raw,
        chain=chain,
    )

    assert first[:2] == (True, 2)
    assert second == (False, 0, None)
    assert len(_contracts(session)) == count_after_first == 2
    assert snapshot.chain_status == "COMPLETE"

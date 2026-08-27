from __future__ import annotations

import copy
import uuid
from datetime import date, datetime, timezone
from inspect import getsource
from types import SimpleNamespace
from typing import Any

import httpx
import pytest
from pydantic import SecretStr

from app import cli
from app.db.models import (
    ContractOiDailySnapshot,
    DailyOiArchiveTicker,
    ExpiryOiDailySnapshot,
)
from app.nightwatch.client import NightwatchClient
from app.nightwatch.errors import NightwatchError
from app.nightwatch.models import ApiUsageEvent, NightwatchResult, QuotaMetadata
from app.scanner.archive import DailyOiArchiver, materialization_retry_after_seconds
from app.scanner.config import ARCHIVE_LIMITS
from app.scanner.daily import DailyRadarCollector, daily_pipeline_status
from app.scanner.parsers import parse_complete_chain

EXPIRATION = date(2026, 9, 18)


def _chain_payload() -> dict[str, Any]:
    return {
        "data": {
            "total_contracts": 2,
            "contracts": [
                {
                    "contract_symbol": "NVDA260918C00200000",
                    "expiration": EXPIRATION.isoformat(),
                    "right": "C",
                    "strike_usd": 200,
                    "open_interest": 10,
                },
                {
                    "contract_symbol": "NVDA260918P00200000",
                    "expiration": EXPIRATION.isoformat(),
                    "right": "P",
                    "strike_usd": 200,
                    "open_interest": 20,
                },
            ],
        },
        "_meta": {"truncated": False},
    }


def _sized_chain_payload(
    *,
    expiration: date = EXPIRATION,
    total: int,
    returned: int,
    truncated: bool = False,
    invalid_open_interest_at: int | None = None,
) -> dict[str, Any]:
    rows = [
        {
            "contract_symbol": (
                f"NVDA{expiration:%y%m%d}"
                f"{'C' if index % 2 == 0 else 'P'}{index:08d}"
            ),
            "expiration": expiration.isoformat(),
            "right": "C" if index % 2 == 0 else "P",
            "strike_usd": index + 1,
            "open_interest": index + 10,
        }
        for index in range(returned)
    ]
    if invalid_open_interest_at is not None:
        rows[invalid_open_interest_at]["open_interest"] = None
    return {
        "data": {
            "total_contracts": total,
            "contracts": rows,
            "underlying_price_usd": 200,
        },
        "_meta": {"truncated": truncated},
    }


def _result(
    status_code: int,
    payload: dict[str, Any],
    *,
    header_retry_after: float | None = None,
) -> NightwatchResult:
    return NightwatchResult(
        payload=payload,
        status_code=status_code,
        request_id=f"client-{status_code}",
        vendor_request_id=f"vendor-{status_code}",
        quota=QuotaMetadata(retry_after_seconds=header_retry_after),
    )


class _WaitClient:
    def __init__(self) -> None:
        self.waits: list[float] = []

    async def wait_for_materialization(self, delay_seconds: float) -> None:
        self.waits.append(delay_seconds)


@pytest.mark.asyncio
async def test_202_then_200_retries_only_chain_and_becomes_complete() -> None:
    client = _WaitClient()
    archiver = DailyOiArchiver(object(), client)  # type: ignore[arg-type]
    responses = iter(
        [
            (
                _result(
                    202,
                    {"data": {}, "_meta": {"status": "materializing", "retry_after_seconds": 7.5}},
                ),
                SimpleNamespace(id=uuid.uuid4()),
            ),
            (_result(200, _chain_payload()), SimpleNamespace(id=uuid.uuid4())),
        ]
    )
    calls: list[tuple[str, dict[str, str], date]] = []

    async def fake_fetch(path: str, **kwargs: Any):  # type: ignore[no-untyped-def]
        calls.append((path, kwargs["params"], kwargs["expiration"]))
        return next(responses)

    archiver._fetch = fake_fetch  # type: ignore[method-assign]
    result, _raw, reason, attempts = await archiver._fetch_materialized_chain(
        ticker="NVDA",
        expiration=EXPIRATION,
    )

    assert reason is None
    assert attempts == 2
    assert client.waits == [7.5]
    assert calls == [calls[0], calls[0]]
    assert parse_complete_chain(result.payload, EXPIRATION).reason == "FULL_COMPLETE"


@pytest.mark.asyncio
async def test_repeated_202_stops_at_bounded_attempt_limit() -> None:
    client = _WaitClient()
    archiver = DailyOiArchiver(object(), client)  # type: ignore[arg-type]
    calls = 0

    async def fake_fetch(*_args: Any, **_kwargs: Any):  # type: ignore[no-untyped-def]
        nonlocal calls
        calls += 1
        return (
            _result(
                202,
                {"data": {}, "_meta": {"status": "materializing", "retry_after_seconds": 0}},
            ),
            SimpleNamespace(id=uuid.uuid4()),
        )

    archiver._fetch = fake_fetch  # type: ignore[method-assign]
    result, _raw, reason, attempts = await archiver._fetch_materialized_chain(
        ticker="NVDA",
        expiration=EXPIRATION,
    )

    assert result.status_code == 202
    assert reason == "MATERIALIZATION_TIMEOUT"
    assert attempts == ARCHIVE_LIMITS.materialization_max_attempts
    assert calls == ARCHIVE_LIMITS.materialization_max_attempts
    assert len(client.waits) == ARCHIVE_LIMITS.materialization_max_attempts - 1


def test_retry_after_prefers_vendor_payload_then_header_then_config_default() -> None:
    assert (
        materialization_retry_after_seconds(
            _result(
                202,
                {"_meta": {"retry_after_seconds": 6}},
                header_retry_after=2,
            )
        )
        == 6
    )
    assert (
        materialization_retry_after_seconds(
            _result(202, {"_meta": {"status": "materializing"}}, header_retry_after=2)
        )
        == 2
    )
    assert (
        materialization_retry_after_seconds(
            _result(202, {"_meta": {"status": "materializing"}})
        )
        == ARCHIVE_LIMITS.materialization_default_retry_after_seconds
    )


@pytest.mark.asyncio
async def test_each_poll_is_an_attempt_and_only_http_200_is_paid() -> None:
    events: list[ApiUsageEvent] = []
    calls = 0

    def handler(_request: httpx.Request) -> httpx.Response:
        nonlocal calls
        calls += 1
        if calls == 1:
            return httpx.Response(
                202,
                json={"data": {}, "_meta": {"status": "materializing", "retry_after_seconds": 0}},
            )
        return httpx.Response(200, json=_chain_payload())

    async def observe(event: ApiUsageEvent) -> None:
        events.append(event)

    async with NightwatchClient(
        api_key=SecretStr("fixture-only"),
        transport=httpx.MockTransport(handler),
        max_retries=0,
        usage_observer=observe,
    ) as client:
        first = await client.request("GET", "/v1/options/chain-snapshot/NVDA")
        second = await client.request("GET", "/v1/options/chain-snapshot/NVDA")

    assert [first.status_code, second.status_code] == [202, 200]
    assert sum(event.attempt_count for event in events) == 2
    assert [event.consumed_quota for event in events] == [False, True]
    assert sum(event.consumed_quota is True for event in events) == 1


def test_complete_chain_reason_codes_are_explicit_and_fail_closed() -> None:
    complete = parse_complete_chain(_chain_payload(), EXPIRATION)
    assert complete.complete is True
    assert complete.reason == "FULL_COMPLETE"

    mismatched = _chain_payload()
    mismatched["data"]["total_contracts"] = 3
    parsed_mismatched = parse_complete_chain(mismatched, EXPIRATION)
    assert parsed_mismatched.complete is False
    assert parsed_mismatched.reason == "ROW_COUNT_MISMATCH"
    assert parsed_mismatched.contracts == ()

    invalid = _chain_payload()
    invalid["data"]["contracts"][0]["open_interest"] = None
    parsed_invalid = parse_complete_chain(invalid, EXPIRATION)
    assert parsed_invalid.complete is False
    assert parsed_invalid.reason == "INVALID_RESPONSE"
    assert parsed_invalid.invalid_row_reasons == {"INVALID_OPEN_INTEREST": 1}

    legitimate_other_failure = _chain_payload()
    legitimate_other_failure["_meta"]["truncated"] = True
    assert parse_complete_chain(legitimate_other_failure, EXPIRATION).reason == "TRUNCATED"


@pytest.mark.parametrize("total", [494, 434])
def test_vendor_limit_is_complete_bounded_snapshot_even_when_truncated_false(
    total: int,
) -> None:
    parsed = parse_complete_chain(
        _sized_chain_payload(total=total, returned=400, truncated=False),
        EXPIRATION,
    )

    assert parsed.complete is True
    assert parsed.reason == "COMPLETE_BOUNDED_SNAPSHOT"
    assert parsed.returned_count == ARCHIVE_LIMITS.vendor_chain_contract_limit
    assert parsed.total_contracts == total
    assert parsed.truncated is False
    assert len(parsed.contracts) == 400


def test_under_limit_shortfall_is_true_row_count_mismatch() -> None:
    parsed = parse_complete_chain(
        _sized_chain_payload(total=494, returned=399, truncated=False),
        EXPIRATION,
    )

    assert parsed.complete is False
    assert parsed.reason == "ROW_COUNT_MISMATCH"
    assert parsed.contracts == ()


def test_invalid_oi_in_bounded_response_remains_invalid_response() -> None:
    parsed = parse_complete_chain(
        _sized_chain_payload(
            total=494,
            returned=400,
            truncated=False,
            invalid_open_interest_at=17,
        ),
        EXPIRATION,
    )

    assert parsed.complete is False
    assert parsed.reason == "INVALID_RESPONSE"
    assert parsed.invalid_row_reasons == {"INVALID_OPEN_INTEREST": 1}
    assert parsed.contracts == ()

    negative = _sized_chain_payload(total=494, returned=400, truncated=False)
    negative["data"]["contracts"][17]["open_interest"] = -1
    parsed_negative = parse_complete_chain(negative, EXPIRATION)
    assert parsed_negative.complete is False
    assert parsed_negative.reason == "INVALID_RESPONSE"
    assert parsed_negative.invalid_row_reasons == {"INVALID_OPEN_INTEREST": 1}
    assert parsed_negative.contracts == ()


def test_duplicate_contract_rows_cannot_duplicate_persistence() -> None:
    overlapping = _chain_payload()
    overlapping["data"]["contracts"][1] = copy.deepcopy(overlapping["data"]["contracts"][0])
    parsed = parse_complete_chain(overlapping, EXPIRATION)
    assert parsed.reason == "ROW_COUNT_MISMATCH"
    assert parsed.invalid_row_reasons == {"DUPLICATE_CONTRACT_SYMBOL": 1}
    assert parsed.contracts == ()


class _ArchiveSession:
    def __init__(self) -> None:
        self.added: list[object] = []

    def scalar(self, _statement: Any) -> Any:
        return None

    def add(self, row: object) -> None:
        if isinstance(row, DailyOiArchiveTicker):
            row.complete_chains = row.complete_chains or 0
            row.incomplete_chains = row.incomplete_chains or 0
            row.contracts_persisted = row.contracts_persisted or 0
        self.added.append(row)

    def commit(self) -> None:
        return None


@pytest.mark.asyncio
async def test_exhausted_202_reason_is_persisted_and_logged(
    capsys: pytest.CaptureFixture[str],
) -> None:
    session = _ArchiveSession()
    archiver = DailyOiArchiver(session, _WaitClient())  # type: ignore[arg-type]
    archiver.run = SimpleNamespace(id=uuid.uuid4())

    async def fake_fetch(*_args: Any, **_kwargs: Any):  # type: ignore[no-untyped-def]
        return (
            SimpleNamespace(
                payload={
                    "data": {
                        "as_of": "2026-08-26T04:00:00Z",
                        "expiries": [
                            {
                                "expiry": EXPIRATION.isoformat(),
                                "date": "2026-08-26",
                                "call_oi": 10,
                                "put_oi": 20,
                            }
                        ],
                    }
                },
                vendor_request_id="surface",
                request_id="surface-client",
            ),
            SimpleNamespace(id=uuid.uuid4()),
        )

    async def materialization_timeout(**_kwargs: Any):  # type: ignore[no-untyped-def]
        return (
            _result(
                202,
                {"data": {}, "_meta": {"status": "materializing", "retry_after_seconds": 1}},
            ),
            SimpleNamespace(id=uuid.uuid4()),
            "MATERIALIZATION_TIMEOUT",
            ARCHIVE_LIMITS.materialization_max_attempts,
        )

    archiver._fetch = fake_fetch  # type: ignore[method-assign]
    archiver._fetch_materialized_chain = materialization_timeout  # type: ignore[method-assign]
    await archiver._archive_ticker("NVDA")

    ticker = next(row for row in session.added if isinstance(row, DailyOiArchiveTicker))
    expiry = next(row for row in session.added if isinstance(row, ExpiryOiDailySnapshot))
    assert ticker.status == "PARTIAL_INCOMPLETE_CHAIN"
    assert ticker.details["incomplete_reason_counts"] == {"MATERIALIZATION_TIMEOUT": 1}
    assert expiry.chain_status == "MATERIALIZATION_TIMEOUT"
    assert not any(isinstance(row, ContractOiDailySnapshot) for row in session.added)

    class LogSession:
        def scalar(self, _statement: Any) -> DailyOiArchiveTicker:
            return ticker

    archiver.session = LogSession()  # type: ignore[assignment]
    archiver._emit_ticker_summary("NVDA")
    output = capsys.readouterr().out
    assert "ticker=NVDA" in output
    assert "status=PARTIAL_INCOMPLETE_CHAIN" in output
    assert "MATERIALIZATION_TIMEOUT=1" in output


@pytest.mark.asyncio
async def test_full_bounded_and_expired_404_are_operationally_complete_with_truthful_coverage(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    expired = date(2026, 8, 24)
    full = EXPIRATION
    bounded = date(2026, 10, 16)
    monkeypatch.setattr(
        "app.scanner.archive.utc_now",
        lambda: datetime(2026, 8, 26, 12, tzinfo=timezone.utc),
    )
    session = _ArchiveSession()
    archiver = DailyOiArchiver(session, _WaitClient())  # type: ignore[arg-type]
    archiver.run = SimpleNamespace(id=uuid.uuid4())

    async def fake_fetch(path: str, **kwargs: Any):  # type: ignore[no-untyped-def]
        if "oi-per-expiry" in path:
            return (
                SimpleNamespace(
                    payload={
                        "data": {
                            "as_of": "2026-08-11T04:00:00Z",
                            "expiries": [
                                {
                                    "expiry": expiration.isoformat(),
                                    "date": "2026-08-11",
                                    "call_oi": 10,
                                    "put_oi": 20,
                                }
                                for expiration in (expired, full, bounded)
                            ],
                        }
                    },
                    vendor_request_id="surface",
                    request_id="surface-client",
                ),
                SimpleNamespace(id=uuid.uuid4()),
            )
        expiration = kwargs["expiration"]
        if expiration == expired:
            raise NightwatchError(
                "expired chain unavailable",
                status_code=404,
                code="NOT_FOUND",
            )
        payload = (
            _sized_chain_payload(expiration=full, total=2, returned=2)
            if expiration == full
            else _sized_chain_payload(expiration=bounded, total=494, returned=400)
        )
        return _result(200, payload), SimpleNamespace(id=uuid.uuid4())

    archiver._fetch = fake_fetch  # type: ignore[method-assign]
    await archiver._archive_ticker("NVDA")

    ticker = next(row for row in session.added if isinstance(row, DailyOiArchiveTicker))
    expiries = {
        row.expiration: row
        for row in session.added
        if isinstance(row, ExpiryOiDailySnapshot)
    }
    contracts = [
        row for row in session.added if isinstance(row, ContractOiDailySnapshot)
    ]
    assert ticker.status == "COMPLETE"
    assert ticker.complete_chains == 2
    assert ticker.incomplete_chains == 1
    assert ticker.contracts_persisted == 402
    assert expiries[expired].chain_status == "EXPIRED_CHAIN_UNAVAILABLE"
    assert expiries[full].chain_status == "COMPLETE"
    assert expiries[bounded].chain_status == "COMPLETE_BOUNDED_SNAPSHOT"
    assert len(contracts) == 402
    assert ticker.details["full_complete_chains"] == 1
    assert ticker.details["bounded_complete_chains"] == 1
    assert ticker.details["true_incomplete_chains"] == 0
    assert ticker.details["accepted_lifecycle_unavailable_chains"] == 1
    assert ticker.details["coverage_reason_counts"] == {
        "COMPLETE_BOUNDED_SNAPSHOT": 1,
        "EXPIRED_EXPIRY_CHAIN_404": 1,
        "FULL_COMPLETE": 1,
    }
    assert ticker.details["incomplete_reason_counts"] == {
        "EXPIRED_EXPIRY_CHAIN_404": 1
    }
    assert ticker.details["bounded_complete_expiries"] == [
        {
            "expiration": bounded.isoformat(),
            "coverage_type": "COMPLETE_BOUNDED_SNAPSHOT",
            "coverage_scope": "NEAR_ATM_BOUNDED",
            "full_chain_available": False,
            "vendor_contract_limit": 400,
            "vendor_total_contracts": 494,
            "contracts_returned": 400,
            "contracts_omitted": 94,
            "pagination_supported": False,
        }
    ]

    class LogSession:
        def scalar(self, _statement: Any) -> DailyOiArchiveTicker:
            return ticker

    archiver.session = LogSession()  # type: ignore[assignment]
    archiver._emit_ticker_summary("NVDA")
    output = capsys.readouterr().out
    assert "status=COMPLETE" in output
    assert "full_complete_chains=1" in output
    assert "bounded_chains=1" in output
    assert "true_incomplete_chains=0" in output
    assert "coverage_reasons=COMPLETE_BOUNDED_SNAPSHOT=1" in output

    class FinishSession:
        def scalars(self, _statement: Any) -> list[DailyOiArchiveTicker]:
            return [ticker]

        def commit(self) -> None:
            return None

    finish_archiver = DailyOiArchiver(FinishSession(), _WaitClient())  # type: ignore[arg-type]
    finish_archiver.run = SimpleNamespace(id=uuid.uuid4())
    summary = finish_archiver._finish(0)
    assert summary.status == "COMPLETE"
    assert summary.complete_chains == 2
    assert summary.full_complete_chains == 1
    assert summary.bounded_complete_chains == 1
    assert summary.true_incomplete_chains == 0
    assert daily_pipeline_status([summary.status, "COMPLETE"]) == "COMPLETE"


def test_cli_complete_is_zero_and_genuine_partial_remains_nonzero() -> None:
    assert cli.daily_oi_archive_exit_code("COMPLETE") == 0
    assert cli.daily_oi_archive_exit_code("PARTIAL") == 6
    assert cli.daily_oi_archive_exit_code("FAILED") == 6


def test_bounded_coverage_does_not_change_radar_full_chain_gate() -> None:
    source = getsource(DailyRadarCollector)
    assert 'expiry.chain_status == "COMPLETE"' in source
    assert 'expiry_archive.chain_status == "COMPLETE"' in source
    assert "COMPLETE_BOUNDED_SNAPSHOT" not in source

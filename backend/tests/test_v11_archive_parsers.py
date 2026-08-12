import uuid
from datetime import date
from types import SimpleNamespace

import pytest

from app.db.models import ContractOiDailySnapshot
from app.models.signals import DteBucket, bucket_for_dte
from app.scanner.archive import (
    DailyOiArchiver,
    expiry_oi_shares,
    mark_expiry_budget_omissions,
)
from app.scanner.parsers import (
    parse_complete_chain,
    parse_daily_expiry_oi,
    parse_oi_change_radar,
    parse_ticker_activity,
)


def test_vendor_date_is_authoritative_and_sides_are_symmetric() -> None:
    rows = parse_daily_expiry_oi({
        "data": {
            "as_of": "2026-08-11T04:00:00Z",
            "expiries": [{
                "expiry": "2026-09-18", "date": "2026-08-11",
                "call_oi": 600, "put_oi": 400,
            }],
        }
    })
    assert rows[0].vendor_date == date(2026, 8, 11)
    assert rows[0].call_oi + rows[0].put_oi == 1000


def test_total_call_and_put_oi_shares_use_separate_scope_denominators() -> None:
    rows = parse_daily_expiry_oi({"data": {
        "as_of": "2026-08-11T04:00:00Z", "expiries": [
            {"expiry": "2026-09-18", "date": "2026-08-11", "call_oi": 600, "put_oi": 100},
            {"expiry": "2026-10-16", "date": "2026-08-11", "call_oi": 400, "put_oi": 300},
        ]
    }})
    assert expiry_oi_shares(rows)[date(2026, 9, 18)] == {
        "call": 0.6, "put": 0.25, "total": 0.5,
    }


@pytest.mark.parametrize(
    ("dte", "bucket"),
    [(0, "VERY_SHORT"), (7, "VERY_SHORT"), (8, "SHORT"), (30, "SHORT"),
     (31, "MEDIUM"), (90, "MEDIUM"), (91, "LONG"), (180, "LONG")],
)
def test_archive_dte_boundaries(dte: int, bucket: str) -> None:
    assert bucket_for_dte(dte) is DteBucket(bucket)


def _chain(*, truncated: bool = False, total: int = 2):
    return {
        "data": {
            "total_contracts": total, "underlying_price_usd": 200,
            "quote_as_of": "2026-08-11T20:00:00Z",
            "greeks_as_of": "2026-08-11T20:00:00Z",
            "underlying_as_of": "2026-08-12T00:00:00Z",
            "open_interest_as_of": "2026-08-11T10:30:00Z",
            "contracts": [
                {"contract_symbol": "NVDA260918C00200000", "expiration": "2026-09-18",
                 "right": "C", "strike_usd": 200, "open_interest": 10,
                 "bid_usd": 1, "ask_usd": 1.1, "delta": 0.5},
                {"contract_symbol": "NVDA260918P00200000", "expiration": "2026-09-18",
                 "right": "P", "strike_usd": 200, "open_interest": 20,
                 "bid_usd": 1, "ask_usd": 1.1, "delta": -0.5},
            ],
        },
        "_meta": {"truncated": truncated},
    }


def test_only_matching_nontruncated_chain_is_complete() -> None:
    complete = parse_complete_chain(_chain(), date(2026, 9, 18))
    assert complete.complete and len(complete.contracts) == 2
    assert {row.right for row in complete.contracts} == {"C", "P"}
    assert not parse_complete_chain(_chain(truncated=True), date(2026, 9, 18)).complete
    assert not parse_complete_chain(_chain(total=3), date(2026, 9, 18)).complete


def test_contract_snapshot_uniqueness_is_append_only_by_vendor_date() -> None:
    constraint_columns = {
        tuple(column.name for column in constraint.columns)
        for constraint in ContractOiDailySnapshot.__table__.constraints
    }
    assert ("ticker", "contract_symbol", "vendor_oi_date") in constraint_columns


def test_budget_limit_marks_every_unattempted_expiry_explicitly() -> None:
    pending = SimpleNamespace(chain_status="PENDING")
    complete = SimpleNamespace(chain_status="COMPLETE")
    later = SimpleNamespace(chain_status="PENDING")
    omitted = mark_expiry_budget_omissions(
        [
            (date(2026, 8, 21), pending),
            (date(2026, 8, 28), complete),
            (date(2026, 9, 4), later),
        ]
    )
    assert omitted == ["2026-08-21", "2026-09-04"]
    assert pending.chain_status == later.chain_status == "BUDGET_NOT_ATTEMPTED"
    assert complete.chain_status == "COMPLETE"


def test_ticker_activity_stays_ticker_scoped_and_radar_is_ranked_evidence() -> None:
    context = parse_ticker_activity({"data": {"as_of": "2026-08-11T04:00:00Z", "day": {
        "date": "2026-08-11", "call_volume": 100, "put_volume": 50,
        "call_open_interest": 200, "put_open_interest": 300, "call_premium_usd": 1000,
    }}})
    assert context.call_volume == 100 and context.vendor_date == date(2026, 8, 11)
    radar = parse_oi_change_radar({"data": {"contracts": [{
        "option_symbol": "NVDA260918C00200000", "prev_oi": 10, "oi": 25,
        "oi_diff": 15, "date": "2026-08-11", "rank": 1,
    }]}})
    assert radar[0].delta_oi == 15 and radar[0].rank == 1


@pytest.mark.asyncio
async def test_duplicate_vendor_date_skips_chain_download(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    class FakeSession:
        def __init__(self) -> None:
            self.added = []

        def scalar(self, _statement):  # type: ignore[no-untyped-def]
            return uuid.uuid4()

        def add(self, row):  # type: ignore[no-untyped-def]
            self.added.append(row)

        def commit(self) -> None:
            return None

    session = FakeSession()
    archiver = DailyOiArchiver(session, object())  # type: ignore[arg-type]
    archiver.run = SimpleNamespace(id=uuid.uuid4())
    calls: list[str] = []

    async def fake_fetch(path, **_kwargs):  # type: ignore[no-untyped-def]
        calls.append(path)
        result = SimpleNamespace(
            payload={"data": {
                "as_of": "2026-08-11T04:00:00Z",
                "expiries": [{
                    "expiry": "2026-09-18", "date": "2026-08-11",
                    "call_oi": 1, "put_oi": 1,
                }],
            }},
            vendor_request_id="safe-request", request_id="client-request",
        )
        return result, SimpleNamespace(id=uuid.uuid4())

    monkeypatch.setattr(archiver, "_fetch", fake_fetch)
    await archiver._archive_ticker("NVDA")
    assert calls == ["/v1/options/oi-per-expiry/NVDA"]
    assert session.added[-1].status == "NO_NEW_VENDOR_OI_SNAPSHOT"

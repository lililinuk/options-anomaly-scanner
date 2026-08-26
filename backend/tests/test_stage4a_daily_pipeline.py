import uuid
from datetime import date, datetime, timezone
from decimal import Decimal
from inspect import getsource
from types import SimpleNamespace

import pytest

from app.db.models import (
    ContractOiDailySnapshot,
    DailyCollectionCoverage,
    DailyOiArchiveTicker,
    ExpiryOiDailySnapshot,
    ZeroDteActivityDailySnapshot,
    ZeroDteActivitySessionSnapshot,
)
from app.nightwatch.errors import NightwatchError
from app.scanner.archive import DailyOiArchiver
from app.scanner.daily import (
    DailyActivityCollector,
    DailyDataPipeline,
    DailyRadarCollector,
    SubjobSummary,
)
from app.scanner.daily_semantics import (
    ZeroDteSnapshotKind,
    activity_session_plan,
    zero_dte_snapshot_kind,
)
from app.scanner.parsers import ExpiryAggregate, parse_complete_chain
from app.scanner.v12 import Mag7Scanner

UTC = timezone.utc


def _chain_payload(*, include_oi_time: bool = True) -> dict[str, object]:
    first = {
        "contract_symbol": "NVDA260918C00200000",
        "expiration": "2026-09-18",
        "right": "C",
        "strike_usd": 200,
        "open_interest": 10,
        "open_interest_as_of": "2026-08-11T11:00:00Z",
    }
    second = {
        "contract_symbol": "NVDA260918P00200000",
        "expiration": "2026-09-18",
        "right": "P",
        "strike_usd": 200,
        "open_interest": 20,
    }
    data: dict[str, object] = {
        "total_contracts": 2,
        "underlying_price_usd": 200,
        "contracts": [first, second],
    }
    if include_oi_time:
        data["open_interest_as_of"] = "2026-08-11T10:30:00Z"
    else:
        first.pop("open_interest_as_of")
    return {"data": data, "_meta": {"truncated": False}}


def test_activity_calendar_requires_actual_xnys_close_and_handles_early_close() -> None:
    weekend = activity_session_plan(datetime(2026, 8, 15, 20, tzinfo=UTC))
    before_regular_close = activity_session_plan(datetime(2026, 8, 14, 19, 59, tzinfo=UTC))
    after_regular_close = activity_session_plan(datetime(2026, 8, 14, 20, 1, tzinfo=UTC))
    before_early_close = activity_session_plan(datetime(2026, 11, 27, 17, 59, tzinfo=UTC))
    after_early_close = activity_session_plan(datetime(2026, 11, 27, 18, 1, tzinfo=UTC))

    assert weekend.status == "SKIPPED_NON_TRADING_SESSION"
    assert before_regular_close.status == "SKIPPED_BEFORE_SESSION_CLOSE"
    assert after_regular_close.should_collect is True
    assert before_early_close.status == "SKIPPED_BEFORE_SESSION_CLOSE"
    assert after_early_close.should_collect is True
    assert after_early_close.session_close_at == datetime(2026, 11, 27, 18, tzinfo=UTC)


@pytest.mark.asyncio
async def test_activity_guard_skips_without_vendor_request() -> None:
    async def forbidden_fetch(*_args, **_kwargs):  # type: ignore[no-untyped-def]
        raise AssertionError("session guard must run before transport")

    pipeline = SimpleNamespace(
        run=SimpleNamespace(
            id=uuid.uuid4(),
            started_at=datetime(2026, 8, 15, 20, tzinfo=UTC),
        ),
        session=object(),
        fetch=forbidden_fetch,
    )
    result = await DailyActivityCollector(pipeline).execute()
    assert result.status == "SKIPPED_NON_TRADING_SESSION"
    assert result.tickers_attempted == 0
    assert result.details["network_request_performed"] is False


def test_stage4a_schema_keeps_legacy_zero_dte_and_adds_versioned_identity() -> None:
    assert ZeroDteActivityDailySnapshot.__tablename__ == "zero_dte_activity_daily_snapshots"
    assert (
        zero_dte_snapshot_kind(ZeroDteActivityDailySnapshot())
        is ZeroDteSnapshotKind.LEGACY_OR_AMBIGUOUS
    )
    constraint_columns = {
        tuple(column.name for column in constraint.columns)
        for constraint in ZeroDteActivitySessionSnapshot.__table__.constraints
    }
    assert ("ticker", "observation_date", "snapshot_kind") in constraint_columns
    assert ContractOiDailySnapshot.__table__.c.open_interest_as_of.nullable is True

    coverage_columns = DailyCollectionCoverage.__table__.c
    assert coverage_columns.activity_market_date.nullable is True
    assert coverage_columns.vendor_oi_date.nullable is True
    coverage_checks = " ".join(
        str(constraint.sqltext)
        for constraint in DailyCollectionCoverage.__table__.constraints
        if hasattr(constraint, "sqltext")
    )
    assert "activity_market_date IS NULL OR subjob = 'ACTIVITY'" in coverage_checks
    assert "vendor_oi_date IS NULL OR subjob = 'RADAR'" in coverage_checks


def test_interactive_provisional_and_daily_canonical_can_coexist() -> None:
    class Session:
        def __init__(self) -> None:
            self.added: list[object] = []

        def scalar(self, _statement):  # type: ignore[no-untyped-def]
            return None

        def add(self, row: object) -> None:
            self.added.append(row)

    session = Session()
    market_day = date(2026, 8, 14)
    aggregate = ExpiryAggregate(market_day, 60, 40, None, None)
    scanner = SimpleNamespace(session=session, run=SimpleNamespace(id=uuid.uuid4()))
    Mag7Scanner._persist_zero_dte_snapshot(
        scanner,
        "NVDA",
        market_day,
        (aggregate, 0.4, None, 250),
        uuid.uuid4(),
        "interactive-request",
    )
    collector = DailyActivityCollector(
        SimpleNamespace(session=session, run=SimpleNamespace(id=uuid.uuid4()))
    )
    collector._persist_zero_dte(
        "NVDA",
        market_day,
        100,
        250,
        0.4,
        SimpleNamespace(id=uuid.uuid4()),
        "daily-request",
        datetime(2026, 8, 14, 20, tzinfo=UTC),
    )

    assert [row.snapshot_kind for row in session.added] == [
        ZeroDteSnapshotKind.PROVISIONAL_INTRADAY.value,
        ZeroDteSnapshotKind.CANONICAL_SESSION_COMPLETE.value,
    ]
    assert session.added[0].session_close_at is None
    assert session.added[1].session_close_at == datetime(2026, 8, 14, 20, tzinfo=UTC)


def test_repeated_canonical_capture_is_idempotent() -> None:
    existing_id = uuid.uuid4()

    class Session:
        def __init__(self) -> None:
            self.scalar_results = iter([None, existing_id])
            self.added: list[object] = []

        def scalar(self, _statement):  # type: ignore[no-untyped-def]
            return next(self.scalar_results)

        def add(self, row: object) -> None:
            self.added.append(row)

    session = Session()
    collector = DailyActivityCollector(
        SimpleNamespace(session=session, run=SimpleNamespace(id=uuid.uuid4()))
    )
    arguments = (
        "NVDA",
        date(2026, 8, 14),
        100,
        250,
        0.4,
        SimpleNamespace(id=uuid.uuid4()),
        "daily-request",
        datetime(2026, 8, 14, 20, tzinfo=UTC),
    )
    collector._persist_zero_dte(*arguments)
    collector._persist_zero_dte(*arguments)
    assert len(session.added) == 1


def test_clean_twenty_observation_query_reads_canonical_v2_only() -> None:
    class Session:
        def __init__(self) -> None:
            self.statement = None

        def scalars(self, statement):  # type: ignore[no-untyped-def]
            self.statement = statement
            return [SimpleNamespace(volume_share=Decimal("0.25"))]

    session = Session()
    scanner = SimpleNamespace(session=session)
    assert Mag7Scanner._zero_dte_history(scanner, "NVDA", date(2026, 8, 18)) == [0.25]
    statement = str(session.statement)
    assert "zero_dte_activity_session_snapshots" in statement
    assert "snapshot_kind" in statement
    assert "zero_dte_activity_daily_snapshots" not in statement


def test_contract_open_interest_as_of_parser_preserves_only_explicit_values() -> None:
    parsed = parse_complete_chain(_chain_payload(), date(2026, 9, 18))
    assert parsed.contracts[0].open_interest_as_of == datetime(2026, 8, 11, 11, tzinfo=UTC)
    assert parsed.contracts[1].open_interest_as_of is None
    assert parsed.open_interest_as_of == datetime(2026, 8, 11, 10, 30, tzinfo=UTC)

    different = _chain_payload()
    different_data = different["data"]
    assert isinstance(different_data, dict)
    different_contracts = different_data["contracts"]
    assert isinstance(different_contracts, list)
    assert isinstance(different_contracts[1], dict)
    different_contracts[1]["open_interest_as_of"] = "2026-08-11T12:00:00Z"
    independently_timed = parse_complete_chain(different, date(2026, 9, 18))
    assert [contract.open_interest_as_of for contract in independently_timed.contracts] == [
        datetime(2026, 8, 11, 11, tzinfo=UTC),
        datetime(2026, 8, 11, 12, tzinfo=UTC),
    ]

    absent = parse_complete_chain(_chain_payload(include_oi_time=False), date(2026, 9, 18))
    assert all(contract.open_interest_as_of is None for contract in absent.contracts)


def test_contract_open_interest_as_of_archive_persists_only_explicit_values() -> None:
    class Session:
        def __init__(self) -> None:
            self.added: list[object] = []

        def scalar(self, _statement):  # type: ignore[no-untyped-def]
            return None

        def add(self, row: object) -> None:
            if isinstance(row, DailyOiArchiveTicker):
                row.complete_chains = row.complete_chains or 0
                row.incomplete_chains = row.incomplete_chains or 0
                row.contracts_persisted = row.contracts_persisted or 0
            self.added.append(row)

        def commit(self) -> None:
            return None

    session = Session()
    archiver = DailyOiArchiver(session, object())  # type: ignore[arg-type]
    archiver.run = SimpleNamespace(id=uuid.uuid4())
    responses = iter(
        [
            SimpleNamespace(
                payload={
                    "data": {
                        "as_of": "2026-08-11T04:00:00Z",
                        "expiries": [
                            {
                                "expiry": "2026-09-18",
                                "date": "2026-08-11",
                                "call_oi": 10,
                                "put_oi": 20,
                            }
                        ],
                    }
                },
                vendor_request_id="oi-surface-request",
                request_id="oi-surface-client",
            ),
            SimpleNamespace(
                payload=_chain_payload(),
                vendor_request_id="chain-request",
                request_id="chain-client",
                status_code=200,
            ),
        ]
    )

    local_capture = datetime(2026, 8, 11, 13, tzinfo=UTC)

    async def fake_fetch(*_args, **_kwargs):  # type: ignore[no-untyped-def]
        return next(responses), SimpleNamespace(id=uuid.uuid4(), received_at=local_capture)

    archiver._fetch = fake_fetch  # type: ignore[method-assign]
    import asyncio

    asyncio.run(archiver._archive_ticker("NVDA"))
    contracts = [row for row in session.added if isinstance(row, ContractOiDailySnapshot)]
    assert [row.open_interest_as_of for row in contracts] == [
        datetime(2026, 8, 11, 11, tzinfo=UTC),
        None,
    ]
    assert all(row.vendor_oi_as_of == datetime(2026, 8, 11, 4, tzinfo=UTC) for row in contracts)
    assert all(row.vendor_oi_date == date(2026, 8, 11) for row in contracts)
    assert all(row.expiration == date(2026, 9, 18) for row in contracts)
    assert contracts[1].open_interest_as_of not in {
        contracts[1].vendor_oi_as_of,
        datetime.combine(contracts[1].vendor_oi_date, datetime.min.time(), tzinfo=UTC),
        datetime.combine(contracts[1].expiration, datetime.min.time(), tzinfo=UTC),
        local_capture,
    }


def test_new_coverage_writes_use_one_explicit_date_identity() -> None:
    activity_source = getsource(DailyActivityCollector.execute)
    radar_source = getsource(DailyRadarCollector.execute)
    assert "activity_market_date=observation_date" in activity_source
    assert "vendor_oi_date=None" in activity_source
    assert "activity_market_date=None" in radar_source
    assert "vendor_oi_date=observation_date" in radar_source


def _oi_surface_payload(expiries: list[str]) -> dict[str, object]:
    return {
        "data": {
            "as_of": "2026-08-11T04:00:00Z",
            "expiries": [
                {
                    "expiry": expiration,
                    "date": "2026-08-11",
                    "call_oi": 10,
                    "put_oi": 20,
                }
                for expiration in expiries
            ],
        }
    }


class _ArchiveSession:
    def __init__(self) -> None:
        self.added: list[object] = []
        self.rollback_count = 0
        self.poisoned = False

    def scalar(self, _statement):  # type: ignore[no-untyped-def]
        return None

    def add(self, row: object) -> None:
        if isinstance(row, DailyOiArchiveTicker):
            row.complete_chains = row.complete_chains or 0
            row.incomplete_chains = row.incomplete_chains or 0
            row.contracts_persisted = row.contracts_persisted or 0
        self.added.append(row)

    def commit(self) -> None:
        if self.poisoned:
            raise AssertionError("commit attempted before rollback")

    def rollback(self) -> None:
        self.rollback_count += 1
        self.poisoned = False


@pytest.mark.asyncio
async def test_expired_chain_404_preserves_oi_and_continues_remaining_expiries(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        "app.scanner.archive.utc_now",
        lambda: datetime(2026, 8, 26, 12, tzinfo=UTC),
    )
    session = _ArchiveSession()
    archiver = DailyOiArchiver(session, object())  # type: ignore[arg-type]
    archiver.run = SimpleNamespace(id=uuid.uuid4())

    async def fake_fetch(path: str, *_args, **kwargs):  # type: ignore[no-untyped-def]
        if "oi-per-expiry" in path:
            return (
                SimpleNamespace(
                    payload=_oi_surface_payload(["2026-08-24", "2026-09-18"]),
                    vendor_request_id="surface",
                    request_id="surface-client",
                ),
                SimpleNamespace(id=uuid.uuid4()),
            )
        if kwargs["expiration"] == date(2026, 8, 24):
            raise NightwatchError(
                "expired chain unavailable",
                status_code=404,
                code="NOT_FOUND",
            )
        return (
            SimpleNamespace(
                payload=_chain_payload(),
                vendor_request_id="chain",
                request_id="chain-client",
                status_code=200,
            ),
            SimpleNamespace(id=uuid.uuid4()),
        )

    archiver._fetch = fake_fetch  # type: ignore[method-assign]
    await archiver._archive_ticker("NVDA")

    ticker_rows = [row for row in session.added if isinstance(row, DailyOiArchiveTicker)]
    expiry_rows = [row for row in session.added if isinstance(row, ExpiryOiDailySnapshot)]
    contract_rows = [row for row in session.added if isinstance(row, ContractOiDailySnapshot)]
    assert len(ticker_rows) == 1
    assert ticker_rows[0].status == "COMPLETE"
    assert ticker_rows[0].details["chain_unavailable"] == [
        {
            "expiration": "2026-08-24",
            "classification": "EXPIRED_EXPIRY_CHAIN_404",
            "safe_error": "NightwatchError",
            "error_code": "NOT_FOUND",
            "http_status": 404,
            "blocks_active_coverage": False,
        }
    ]
    assert [(row.expiration, row.chain_status) for row in expiry_rows] == [
        (date(2026, 8, 24), "EXPIRED_CHAIN_UNAVAILABLE"),
        (date(2026, 9, 18), "COMPLETE"),
    ]
    assert expiry_rows[0].call_oi == 10
    assert expiry_rows[0].put_oi == 20
    assert len(contract_rows) == 2


@pytest.mark.asyncio
async def test_active_chain_404_is_truthful_fail_closed_without_duplicate_or_zero(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        "app.scanner.archive.utc_now",
        lambda: datetime(2026, 8, 26, 12, tzinfo=UTC),
    )
    session = _ArchiveSession()
    archiver = DailyOiArchiver(session, object())  # type: ignore[arg-type]
    archiver.run = SimpleNamespace(id=uuid.uuid4())

    async def fake_fetch(path: str, *_args, **_kwargs):  # type: ignore[no-untyped-def]
        if "oi-per-expiry" in path:
            return (
                SimpleNamespace(
                    payload=_oi_surface_payload(["2026-09-18"]),
                    vendor_request_id="surface",
                    request_id="surface-client",
                ),
                SimpleNamespace(id=uuid.uuid4()),
            )
        raise NightwatchError("active chain unavailable", status_code=404, code="NOT_FOUND")

    archiver._fetch = fake_fetch  # type: ignore[method-assign]
    await archiver._archive_ticker("NVDA")

    ticker_rows = [row for row in session.added if isinstance(row, DailyOiArchiveTicker)]
    expiry_rows = [row for row in session.added if isinstance(row, ExpiryOiDailySnapshot)]
    assert len(ticker_rows) == 1
    assert ticker_rows[0].status == "PARTIAL_INCOMPLETE_CHAIN"
    assert ticker_rows[0].details["chain_unavailable"][0]["classification"] == (
        "ACTIVE_EXPIRY_CHAIN_404"
    )
    assert ticker_rows[0].details["chain_unavailable"][0]["blocks_active_coverage"] is True
    assert len(expiry_rows) == 1
    assert expiry_rows[0].chain_status == "ACTIVE_CHAIN_UNAVAILABLE"
    assert expiry_rows[0].total_oi == 30
    assert not any(isinstance(row, ContractOiDailySnapshot) for row in session.added)


@pytest.mark.asyncio
async def test_archiver_failure_rolls_back_and_reraises_original_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    original = RuntimeError("original archive failure")

    class Session(_ArchiveSession):
        def __init__(self) -> None:
            super().__init__()
            self.run = None

        def scalar(self, _statement):  # type: ignore[no-untyped-def]
            return True

        def add(self, row: object) -> None:
            if getattr(row, "id", None) is None:
                row.id = uuid.uuid4()  # type: ignore[attr-defined]
            if row.__class__.__name__ == "DailyOiArchiveRun":
                self.run = row
            super().add(row)

        def get(self, _model, _identifier):  # type: ignore[no-untyped-def]
            return self.run

        def execute(self, _statement):  # type: ignore[no-untyped-def]
            return None

    session = Session()
    archiver = DailyOiArchiver(session, SimpleNamespace())

    async def fail_ticker(_ticker: str) -> None:
        session.poisoned = True
        raise original

    monkeypatch.setattr(archiver, "_archive_ticker", fail_ticker)
    monkeypatch.setattr("app.scanner.archive.UNIVERSE", ("AAPL",))

    with pytest.raises(RuntimeError) as raised:
        await archiver.execute(trigger="test")

    assert raised.value is original
    assert session.rollback_count >= 1
    assert session.poisoned is False
    assert session.run.status == "FAILED"
    assert session.run.summary == {"safe_error": "RuntimeError"}


@pytest.mark.asyncio
async def test_daily_parent_recovers_session_and_preserves_archiver_usage(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class Session(_ArchiveSession):
        def scalar(self, _statement):  # type: ignore[no-untyped-def]
            return True

        def add(self, row: object) -> None:
            if getattr(row, "id", None) is None:
                row.id = uuid.uuid4()  # type: ignore[attr-defined]
            super().add(row)

        def execute(self, _statement):  # type: ignore[no-untyped-def]
            return None

    session = Session()

    class FailingArchiver:
        def __init__(self, archive_session, _client) -> None:  # type: ignore[no-untyped-def]
            assert archive_session is session
            self.budget = SimpleNamespace(consumed=1, attempts=2)

        async def execute(self, *, trigger: str):  # type: ignore[no-untyped-def]
            assert trigger == "daily_pipeline"
            session.poisoned = True
            raise RuntimeError("archive failed")

    async def healthy_radar(_collector):  # type: ignore[no-untyped-def]
        assert session.poisoned is False
        return SubjobSummary("COMPLETE", 7, 0, 7, {})

    monkeypatch.setattr("app.scanner.daily.DailyOiArchiver", FailingArchiver)
    monkeypatch.setattr(DailyRadarCollector, "execute", healthy_radar)
    result = await DailyDataPipeline(session, SimpleNamespace()).execute(mode="radar-oi")

    assert result.status == "PARTIAL"
    assert result.subjobs["daily_oi"]["status"] == "FAILED"
    assert result.subjobs["radar"]["status"] == "COMPLETE"
    assert result.consumed_quota_units == 1
    assert result.network_attempts == 2
    assert result.subjobs["daily_oi"]["details"]["consumed_quota_units"] == 1
    assert result.subjobs["daily_oi"]["details"]["network_attempts"] == 2
    assert session.rollback_count >= 1

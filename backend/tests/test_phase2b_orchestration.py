import uuid
from datetime import date
from decimal import Decimal
from types import SimpleNamespace

from app.confirmation.config import Phase2bContextConfig
from app.confirmation.service import CandidateSource, Phase2bContextService
from app.nightwatch.errors import NightwatchError


class FakeSession:
    def __init__(self) -> None:
        self.commits = 0

    def commit(self) -> None:
        self.commits += 1

    def add(self, row) -> None:  # type: ignore[no-untyped-def]
        if getattr(row, "id", None) is None:
            row.id = uuid.uuid4()

    def flush(self) -> None:
        return None


class NoNetworkClient:
    calls = 0


def config() -> Phase2bContextConfig:
    return Phase2bContextConfig(
        version="test.v1", stock_state_freshness_minutes=10,
        ohlc_freshness_minutes=20, iv_rank_freshness_minutes=20,
        term_structure_freshness_minutes=20, heatmap_freshness_minutes=10,
        at_spot_tolerance_pct=Decimal("0.0025"),
    )


def candidate(symbol: str) -> CandidateSource:
    return CandidateSource(
        contract_symbol=symbol, ticker="NVDA", expiration=date(2026, 8, 21),
        right="C", strike=Decimal("220"), dte_at_detection=9,
    )


async def test_no_deep_dive_candidate_makes_no_phase2b_call(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    session = FakeSession()
    service = Phase2bContextService(session, NoNetworkClient(), config())  # type: ignore[arg-type]
    monkeypatch.setattr(service, "_candidate_source", lambda _symbol: None)
    summary = await service.refresh_contracts(["MISSING"])
    assert summary.evaluations == ()
    assert summary.ticker_snapshots_created == 0
    assert session.commits == 0


async def test_same_ticker_candidates_share_one_context_fetch(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    session = FakeSession()
    service = Phase2bContextService(session, NoNetworkClient(), config())  # type: ignore[arg-type]
    sources = {"A": candidate("A"), "B": candidate("B")}
    context = SimpleNamespace(id="ticker-context")
    fetches: list[str] = []
    monkeypatch.setattr(service, "_candidate_source", sources.get)
    monkeypatch.setattr(service, "_fresh_context", lambda _ticker: None)

    async def fetch(ticker: str):  # type: ignore[no-untyped-def]
        fetches.append(ticker)
        return context

    monkeypatch.setattr(service, "_fetch_ticker_context", fetch)
    monkeypatch.setattr(
        service, "_evaluation",
        lambda _context, source: SimpleNamespace(id=f"evaluation-{source.contract_symbol}"),
    )
    summary = await service.refresh_contracts(["A", "B"])
    assert fetches == ["NVDA"]
    assert summary.ticker_snapshots_created == 1
    assert len(summary.evaluations) == 2


async def test_fresh_context_avoids_network_and_is_shared(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    session = FakeSession()
    service = Phase2bContextService(session, NoNetworkClient(), config())  # type: ignore[arg-type]
    context = SimpleNamespace(id="cached")
    monkeypatch.setattr(service, "_candidate_source", lambda symbol: candidate(symbol))
    monkeypatch.setattr(service, "_fresh_context", lambda _ticker: context)

    async def forbidden(_ticker: str):  # type: ignore[no-untyped-def]
        raise AssertionError("fresh context must not make a vendor call")

    monkeypatch.setattr(service, "_fetch_ticker_context", forbidden)
    monkeypatch.setattr(
        service, "_evaluation", lambda _context, source: SimpleNamespace(id=source.contract_symbol)
    )
    summary = await service.refresh_contracts(["A", "B"])
    assert summary.ticker_snapshots_reused == 1
    assert summary.ticker_snapshots_created == 0


async def test_reprocesses_preserved_raw_without_vendor_call(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    session = FakeSession()
    service = Phase2bContextService(session, NoNetworkClient(), config())  # type: ignore[arg-type]
    previous = SimpleNamespace(id="v1-context")
    amended = SimpleNamespace(id="v1.1-context")
    monkeypatch.setattr(service, "_candidate_source", lambda symbol: candidate(symbol))
    monkeypatch.setattr(service, "_fresh_context", lambda _ticker: None)
    monkeypatch.setattr(service, "_latest_context", lambda _ticker: previous)
    monkeypatch.setattr(service, "_reprocess_ticker_context", lambda source: amended)

    async def forbidden(_ticker: str):  # type: ignore[no-untyped-def]
        raise AssertionError("preserved raw reprocessing must not call Nightwatch")

    monkeypatch.setattr(service, "_fetch_ticker_context", forbidden)
    monkeypatch.setattr(
        service, "_evaluation", lambda context, _source: SimpleNamespace(id=context.id)
    )
    summary = await service.refresh_contracts(["A"], reuse_latest_raw=True)
    assert summary.ticker_snapshots_reprocessed == 1
    assert summary.ticker_snapshots_reused == 0
    assert summary.ticker_snapshots_created == 0
    assert summary.evaluations == ("v1.1-context",)


def test_request_set_has_no_chain_rv_skew_standard_or_zero_dte_endpoint() -> None:
    paths = {path for _name, path, _params in Phase2bContextService.ENDPOINTS}
    assert len(paths) == 5
    forbidden = ("chain", "realized", "stats", "skew", "standard-gex", "dealer-gex")
    assert all(not any(term in path for term in forbidden) for path in paths)


async def test_heatmap_failure_keeps_ticker_context_available() -> None:
    class PartialClient:
        async def request(self, _method, path, **_kwargs):  # type: ignore[no-untyped-def]
            if "heatmap" in path:
                raise NightwatchError("fixture failure", status_code=503, code="UPSTREAM")
            payloads = {
                "ohlc": {"data": {"bars": []}},
                "stock-state": {"data": {"close_usd": 200, "prev_close_usd": 199}},
                "iv-rank": {"data": {"iv_rank": 30}},
                "term-structure": {"data": {"nodes": []}},
            }
            payload = next(value for key, value in payloads.items() if key in path)
            return SimpleNamespace(
                payload=payload, status_code=200, request_id=str(uuid.uuid4()),
                vendor_request_id=None,
            )

    service = Phase2bContextService(FakeSession(), PartialClient(), config())  # type: ignore[arg-type]
    context = await service._fetch_ticker_context("NVDA")
    assert context.stock_state["availability"] == "AVAILABLE"
    assert context.endpoint_statuses["dealer_heatmap"]["availability"] == "UNAVAILABLE"
    assert context.dealer_heatmap.get("cells") is None

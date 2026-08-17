import uuid
from datetime import date, datetime, timezone
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

    def scalar(self, _statement):  # type: ignore[no-untyped-def]
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
                raise NightwatchError(
                    "fixture failure", status_code=400, code="VALIDATION_ERROR",
                    request_id="safe-request-id",
                )
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
    assert context.endpoint_statuses["dealer_heatmap"]["status"] == 400
    assert context.endpoint_statuses["dealer_heatmap"]["error_code"] == "VALIDATION_ERROR"
    assert context.endpoint_statuses["dealer_heatmap"]["request_id"] == "safe-request-id"
    assert context.dealer_heatmap["availability"] == "UNAVAILABLE"
    assert context.dealer_heatmap["availability_reason"] == "VALIDATION_ERROR"
    assert context.dealer_heatmap["cells"] == []
    assert context.dealer_heatmap["row_stacks"] == []
    assert context.source_first_received_at is not None
    assert context.freshness_anchor_at is not None
    assert context.source_time_provenance["dealer_heatmap"]["vendor_observed_at"] is None
    assert (
        context.source_time_provenance["dealer_heatmap"]["freshness_basis"]
        == "LOCAL_REQUEST_ATTEMPT_ONLY"
    )


async def test_unavailable_heatmap_is_requested_once_and_shared_by_ticker(
    monkeypatch,
) -> None:  # type: ignore[no-untyped-def]
    class CountingClient:
        def __init__(self) -> None:
            self.paths: list[str] = []

        async def request(self, _method, path, **_kwargs):  # type: ignore[no-untyped-def]
            self.paths.append(path)
            if "heatmap" in path:
                raise NightwatchError(
                    "fixture failure", status_code=400, code="VALIDATION_ERROR"
                )
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

    session = FakeSession()
    client = CountingClient()
    service = Phase2bContextService(session, client, config())  # type: ignore[arg-type]
    sources = {"A": candidate("A"), "B": candidate("B")}
    monkeypatch.setattr(service, "_candidate_source", sources.get)
    monkeypatch.setattr(service, "_fresh_context", lambda _ticker: None)
    observed: list[tuple[str, str]] = []

    def evaluate(context, source):  # type: ignore[no-untyped-def]
        observed.append((source.contract_symbol, context.dealer_heatmap["availability"]))
        return SimpleNamespace(id=f"evaluation-{source.contract_symbol}")

    monkeypatch.setattr(service, "_evaluation", evaluate)
    summary = await service.refresh_contracts(["A", "B"])
    assert sum("heatmap" in path for path in client.paths) == 1
    assert len(client.paths) == 5
    assert observed == [("A", "UNAVAILABLE"), ("B", "UNAVAILABLE")]
    assert len(summary.evaluations) == 2
    assert session.commits == 1


def test_candidate_evaluation_survives_unavailable_dealer_context() -> None:
    radar = SimpleNamespace(
        material_event_eligible=True,
        observation_date=date(2026, 8, 12),
        premium=Decimal("10434044"),
        delta_oi=4531,
        relative_oi_change=Decimal("0.07211294"),
        volume=3000,
        trades=120,
        contract_structure_score=Decimal("70.722"),
        archive_completeness="COMPLETE",
        threshold_profile_version="test-threshold-v1",
        threshold_config_hash="test-hash",
        trigger_sources=["RADAR_EVENT"],
    )
    chain = SimpleNamespace(
        implied_volatility=Decimal("0.2973"),
        bid=Decimal("3.85"), ask=Decimal("3.95"), open_interest=12000,
        delta=Decimal("0.4787"), gamma=Decimal("0.0369"),
        theta=Decimal("-0.2247"), vega=Decimal("14.4368"),
        charm=Decimal("-1.0396"), underlying_price=Decimal("223.73"),
        quote_as_of=None, greeks_as_of=None, vendor_oi_date=date(2026, 8, 12),
    )
    contract = SimpleNamespace(
        structure_score=Decimal("70.722"), persistent_positioning_score=None
    )
    expiry = SimpleNamespace(
        persistent_positioning_score=None, same_day_activity_score=Decimal("75")
    )

    class EvaluationSession(FakeSession):
        def __init__(self) -> None:
            super().__init__()
            self.scalar_values = iter([None, radar, chain, contract, expiry])

        def scalar(self, _statement):  # type: ignore[no-untyped-def]
            return next(self.scalar_values)

        def scalars(self, _statement):  # type: ignore[no-untyped-def]
            return []

    context = SimpleNamespace(
        id=uuid.uuid4(),
        stock_state={"availability": "AVAILABLE", "current_price_usd": 223.73},
        price_context={"availability": "AVAILABLE", "atr_14": 8.0},
        iv_rank={"availability": "AVAILABLE", "value": 32.4},
        term_structure={
            "availability": "AVAILABLE",
            "nodes": [{
                "expiry": "2026-08-21", "dte": 9, "implied_vol_pct": 0.331,
            }],
        },
        dealer_heatmap={
            "availability": "UNAVAILABLE",
            "availability_reason": "VALIDATION_ERROR",
            "source_http_status": 400,
            "source_error_code": "VALIDATION_ERROR",
            "cells": [],
            "row_stacks": [],
            "truncated": False,
        },
        source_timestamps={"heatmap": "2026-08-14T01:02:03Z"},
    )
    service = Phase2bContextService(
        EvaluationSession(), NoNetworkClient(), config()  # type: ignore[arg-type]
    )
    evaluation = service._evaluation(context, candidate("NVDA260821C00220000"))
    assert evaluation.phase2a_evidence["radar_material_event"] is True
    assert evaluation.strike_location["availability"] == "AVAILABLE"
    assert evaluation.volatility_context["availability"] == "AVAILABLE"
    assert evaluation.execution_context["availability"] == "AVAILABLE"
    assert evaluation.execution_context["delta"] == 0.4787
    assert evaluation.dealer_context["availability"] == "UNAVAILABLE"
    assert evaluation.dealer_context["candidate_heatmap_cell_status"] == "UNAVAILABLE"
    assert evaluation.dealer_context["candidate_net_gex_usd"] is None
    assert evaluation.dealer_context["row_stack_status"] == "ROW_UNAVAILABLE"
    assert evaluation.evidence_states == {
        "price": "AVAILABLE",
        "stock_state": "AVAILABLE",
        "volatility": "AVAILABLE",
        "dealer": "UNAVAILABLE",
        "execution": "AVAILABLE",
        "positioning": "AVAILABLE",
    }
    assert evaluation.direction == "UNRESOLVED"
    assert evaluation.evaluation_identity == "REFRESH"
    assert evaluation.source_radar_observation_id is None
    assert evaluation.specification_version == "signal_spec_v1.2_phase2b"
    assert isinstance(evaluation.evaluated_at, datetime)
    assert evaluation.evaluated_at.tzinfo == timezone.utc

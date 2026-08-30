from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
from uuid import uuid4

import app.dashboard.trading as trading
from app.confirmation.provenance import EvaluationIdentity
from app.dashboard.trading import _candidate_read_model, trading_dashboard_read_model

UTC = timezone.utc
NOW = datetime(2026, 8, 30, 16, 0, tzinfo=UTC)


class NoWriteSession:
    def __init__(self, *, scalar_value=None, contexts=None) -> None:  # type: ignore[no-untyped-def]
        self.scalar_value = scalar_value
        self.contexts = contexts or []
        self.writes = 0

    def scalar(self, _statement):  # type: ignore[no-untyped-def]
        return self.scalar_value

    def scalars(self, _statement):  # type: ignore[no-untyped-def]
        return self.contexts

    def add(self, _value):  # type: ignore[no-untyped-def]
        self.writes += 1
        raise AssertionError("Trading read model attempted a write")

    def flush(self):
        self.writes += 1
        raise AssertionError("Trading read model attempted a flush")

    def commit(self):
        self.writes += 1
        raise AssertionError("Trading read model attempted a commit")


def test_unavailable_population_is_truthful_and_read_only() -> None:
    session = NoWriteSession()
    result = trading_dashboard_read_model(session, as_of=NOW)  # type: ignore[arg-type]
    assert result["candidate_population"]["state"] == "UNAVAILABLE"
    assert result["candidate_population"]["freshness"] == "UNAVAILABLE"
    assert result["candidates"] == []
    assert result["contracts"] == {
        "vendor_requests_on_read": 0,
        "frozen_first_knowledge_mutated": False,
        "automatic_context_capture": False,
    }
    assert session.writes == 0


def test_current_context_does_not_fall_back_to_frozen_baseline(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    baseline = SimpleNamespace(
        id=uuid4(),
        evaluation_kind=EvaluationIdentity.FIRST_KNOWLEDGE_BASELINE.value,
        context_evaluated_at=NOW - timedelta(days=2),
        price_context={"stock_state": {"current_price_usd": 999}},
        volatility_context={},
        provenance={},
        details=[],
    )
    before = deepcopy(baseline.price_context)
    candidate = SimpleNamespace(
        id=uuid4(),
        scan_run_id=uuid4(),
        ticker="NVDA",
        candidate_first_knowledge_at=NOW - timedelta(days=2),
        triggers=[],
    )
    monkeypatch.setattr(trading, "best_archived_surface_at_or_before", lambda *_a, **_k: None)
    session = NoWriteSession(contexts=[baseline])
    result = _candidate_read_model(
        session,  # type: ignore[arg-type]
        candidate,
        generated_at=NOW,
        config=trading.active_phase2b_config(),
    )
    assert result["current_trading_context"]["identity"]["state"] == "UNAVAILABLE"
    assert result["current_trading_context"]["price"]["freshness"] == "UNAVAILABLE"
    assert result["frozen_first_knowledge"] == {
        "state": "PRESERVED_OUTSIDE_TRADING_VIEW",
        "available": True,
        "rendered_as_current": False,
    }
    assert baseline.price_context == before
    assert session.writes == 0


def test_refresh_origin_remains_null_when_schema_does_not_preserve_it(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    refresh = SimpleNamespace(
        id=uuid4(),
        evaluation_kind=EvaluationIdentity.REFRESH.value,
        context_evaluated_at=NOW - timedelta(hours=1),
        price_as_of=None,
        price_context={},
        volatility_context={},
        provenance={},
        details=[],
    )
    baseline = SimpleNamespace(
        id=uuid4(),
        evaluation_kind=EvaluationIdentity.FIRST_KNOWLEDGE_BASELINE.value,
        context_evaluated_at=NOW - timedelta(days=2),
        details=[],
    )
    candidate = SimpleNamespace(
        id=uuid4(),
        scan_run_id=uuid4(),
        ticker="MSFT",
        candidate_first_knowledge_at=NOW - timedelta(days=2),
        triggers=[],
    )
    monkeypatch.setattr(trading, "best_archived_surface_at_or_before", lambda *_a, **_k: None)
    result = _candidate_read_model(
        NoWriteSession(contexts=[refresh, baseline]),  # type: ignore[arg-type]
        candidate,
        generated_at=NOW,
        config=trading.active_phase2b_config(),
    )
    identity = result["current_trading_context"]["identity"]
    assert identity["state"] == "AVAILABLE"
    assert identity["context_id"] == str(refresh.id)
    assert identity["origin"] is None
    assert identity["origin_state"] == "NOT_PERSISTED"

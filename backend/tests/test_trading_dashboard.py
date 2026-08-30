from __future__ import annotations

import inspect
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
from types import SimpleNamespace
from uuid import uuid4

from fastapi.testclient import TestClient

import app.dashboard.trading as trading
from app.api.routes import trading_dashboard as route
from app.confirmation.config import Phase2bContextConfig
from app.dashboard.trading import (
    _active_anomaly,
    _dealer_gex_context,
    _price_context,
    _volatility_context,
    expiration_is_active,
    freshness_state,
    latest_successful_candidate_run,
    select_featured_anomalies,
)
from app.db.models import OiChangeRadarObservation
from app.db.session import get_db_session
from app.main import app

UTC = timezone.utc
NOW = datetime(2026, 8, 21, 18, 0, tzinfo=UTC)


def _config() -> Phase2bContextConfig:
    return Phase2bContextConfig(
        version="test",
        stock_state_freshness_minutes=15,
        ohlc_freshness_minutes=720,
        iv_rank_freshness_minutes=720,
        term_structure_freshness_minutes=720,
        heatmap_freshness_minutes=15,
        at_spot_tolerance_pct=Decimal("0.0025"),
    )


def _anomaly(
    identity: str,
    family: str,
    *,
    premium: float | None = None,
    delta_oi: int | None = None,
    activity_score: float | None = None,
) -> dict[str, object]:
    return {
        "id": identity,
        "identity": identity,
        "family": family,
        "premium_usd": premium,
        "delta_oi": delta_oi,
        "same_day_activity_score": activity_score,
    }


def test_latest_candidate_population_query_requires_successful_materialization() -> None:
    expected = SimpleNamespace(id=uuid4())

    class RecordingSession:
        statement = None

        def scalar(self, statement):  # type: ignore[no-untyped-def]
            self.statement = statement
            return expected

    session = RecordingSession()
    assert latest_successful_candidate_run(session) is expected  # type: ignore[arg-type]
    query = str(session.statement)
    assert "scan_runs.status" in query
    assert "scan_runs.specification_version" in query
    assert "scan_runs.candidate_materialized_at IS NOT NULL" in query
    assert "scan_runs.market_date DESC" in query


def test_expiry_activity_uses_authoritative_xnys_close() -> None:
    before_close = datetime(2026, 8, 21, 19, 59, tzinfo=UTC)
    after_close = datetime(2026, 8, 21, 20, 1, tzinfo=UTC)
    assert expiration_is_active(date(2026, 8, 21), as_of=before_close)
    assert not expiration_is_active(date(2026, 8, 21), as_of=after_close)
    # Legacy Saturday expiry identity still stops trading at the prior XNYS close.
    assert not expiration_is_active(date(2026, 8, 22), as_of=after_close)


def test_current_stale_and_unavailable_are_distinct() -> None:
    assert freshness_state(NOW - timedelta(minutes=10), as_of=NOW, max_age_minutes=15) == (
        "CURRENT"
    )
    assert freshness_state(NOW - timedelta(minutes=16), as_of=NOW, max_age_minutes=15) == ("STALE")
    assert freshness_state(None, as_of=NOW, max_age_minutes=15) == "UNAVAILABLE"


def test_featured_uses_native_family_ordering_without_cross_family_score() -> None:
    anomalies = [
        _anomaly("radar-oi", "RADAR_EVENT", premium=2_000_000, delta_oi=8_000),
        _anomaly("radar-premium", "RADAR_EVENT", premium=3_000_000, delta_oi=1_000),
        _anomaly("activity-low", "EXPIRY_ACTIVITY", activity_score=71),
        _anomaly("activity-high", "EXPIRY_ACTIVITY", activity_score=88),
        _anomaly("persistence", "CONTRACT_PERSISTENCE"),
    ]
    featured = select_featured_anomalies(anomalies)
    assert [item["id"] for item in featured] == ["radar-premium", "activity-high"]
    assert len(featured) <= 3
    assert len({item["family"] for item in featured}) == len(featured)
    assert all("score" not in item and "universal_score" not in item for item in featured)
    assert not any(item["family"] == "CONTRACT_PERSISTENCE" for item in featured)


def test_active_anomaly_excludes_expired_and_preserves_detection_dte() -> None:
    source_id = uuid4()
    trigger = SimpleNamespace(
        id=uuid4(),
        evidence_family="RADAR_EVENT",
        anomaly_entity_type="CONTRACT",
        anomaly_identity="NVDA260821C00212500",
        qualifies_candidate=True,
        source_radar_observation_id=source_id,
        source_expiry_observation_id=None,
        source_contract_observation_id=None,
    )
    source = SimpleNamespace(
        matched_expiration=date(2026, 8, 21),
        matched_right="C",
        matched_strike=Decimal("212.5"),
        matched_dte=2,
        premium=Decimal("3000000"),
        delta_oi=5000,
    )

    class SourceSession:
        def get(self, model, identity):  # type: ignore[no-untyped-def]
            assert model is OiChangeRadarObservation
            assert identity == source_id
            return source

    active = _active_anomaly(
        SourceSession(),  # type: ignore[arg-type]
        trigger,
        detail=None,
        as_of=datetime(2026, 8, 21, 19, 0, tzinfo=UTC),
    )
    assert active is not None
    assert active["current_dte"] == 0
    assert active["detection_dte"] == 2
    assert active["strike"] == 212.5
    assert source.matched_dte == 2
    assert (
        _active_anomaly(
            SourceSession(),  # type: ignore[arg-type]
            trigger,
            detail=None,
            as_of=datetime(2026, 8, 21, 21, 0, tzinfo=UTC),
        )
        is None
    )


def test_price_context_does_not_label_stale_stock_current_and_labels_fallback() -> None:
    stale = NOW - timedelta(hours=2)
    context = SimpleNamespace(
        price_context={
            "stock_state": {
                "current_price_usd": 181.25,
                "as_of": stale.isoformat(),
                "session": "REGULAR",
            },
            "history": {
                "latest_regular_close_usd": 179.5,
                "latest_trading_date": "2026-08-20",
            },
        },
        price_as_of=NOW - timedelta(hours=3),
        provenance={
            "sources": {
                "stock_state": {"freshness_anchor_at": stale.isoformat()},
                "daily_ohlc": {"freshness_anchor_at": (NOW - timedelta(hours=3)).isoformat()},
            }
        },
    )
    result = _price_context(context, as_of=NOW, config=_config())
    assert result["label"] == "Previous Close"
    assert result["value_usd"] == 179.5
    assert result["fallback_used"] is True
    assert result["stock_state_freshness"] == "STALE"
    assert result["freshness"] == "CURRENT"


def test_volatility_filters_expired_terms_and_withholds_iv_rank_classification() -> None:
    source_time = (NOW - timedelta(hours=1)).isoformat()
    context = SimpleNamespace(
        volatility_context={
            "term_structure": {"as_of": source_time},
            "iv_rank": {
                "value": 42,
                "as_of": source_time,
                "vendor_semantics": "UNVERIFIED",
                "classification": "SHOULD_NOT_ESCAPE",
            },
            "expiry_contexts": {
                "2026-08-20": {"candidate_term_iv": 0.331},
                "2026-08-28": {"candidate_term_iv": 0.355},
            },
        },
        provenance={
            "sources": {
                "iv_rank": {"freshness_anchor_at": source_time},
                "term_structure": {"freshness_anchor_at": source_time},
            }
        },
    )
    result = _volatility_context(
        context,
        active_expirations={date(2026, 8, 28)},
        as_of=NOW,
        config=_config(),
    )
    assert set(result["active_expiry_terms"]) == {"2026-08-28"}
    assert result["iv_rank"]["classification"] is None
    assert result["iv_rank"]["vendor_semantics"] == "UNVERIFIED"


def test_latest_gex_excludes_expired_expiries_and_uses_global_price(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    snapshot = SimpleNamespace(
        id=uuid4(),
        vendor_observed_at=NOW - timedelta(minutes=20),
        captured_at=NOW - timedelta(minutes=19),
        availability="AVAILABLE",
        spot_usd=Decimal("170"),
    )
    payload = {
        "spot_usd": 170,
        "cells": [
            {"expiration": "2026-08-20", "strike_usd": 175, "net_dealer_gex_usd": 1},
            {"expiration": "2026-08-28", "strike_usd": 180, "net_dealer_gex_usd": 2},
        ],
    }
    seen_spots = []
    monkeypatch.setattr(
        trading,
        "best_archived_surface_at_or_before",
        lambda *_args, **_kwargs: (snapshot, payload),
    )

    def context_for_expiry(value, *, expiration):  # type: ignore[no-untyped-def]
        seen_spots.append(value["spot_usd"])
        return {"anchor_expiry": expiration.isoformat()}

    monkeypatch.setattr(trading, "dealer_gex_context_for_expiry", context_for_expiry)
    result = _dealer_gex_context(
        object(),  # type: ignore[arg-type]
        ticker="NVDA",
        price={"label": "Previous Close", "value_usd": 181.5},
        as_of=NOW,
        config=_config(),
    )
    assert result["freshness"] == "STALE"
    assert set(result["active_expiry_contexts"]) == {"2026-08-28"}
    assert seen_spots == [181.5]
    assert result["vendor_snapshot_spot_usd"] == 170
    assert "bullish/bearish" in result["sign_disclosure"]


def test_trading_route_is_read_only_and_does_not_import_nightwatch(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    expected = {"candidate_population": {"freshness": "STALE"}, "candidates": []}
    monkeypatch.setattr(route, "trading_dashboard_read_model", lambda _session: expected)
    app.dependency_overrides[get_db_session] = lambda: object()
    try:
        with TestClient(app) as client:
            response = client.get("/api/v1/dashboard/trading")
    finally:
        app.dependency_overrides.clear()
    assert response.status_code == 200
    assert response.json() == expected
    source = inspect.getsource(trading)
    assert "NightwatchClient" not in source
    assert "phase2b.vnext.refresh" not in source

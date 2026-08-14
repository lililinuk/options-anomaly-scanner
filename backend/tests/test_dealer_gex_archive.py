from __future__ import annotations

import uuid
from datetime import date, datetime, timezone
from types import SimpleNamespace

import pytest

from app.cli import dealer_gex_archive_exit_code
from app.confirmation.workspace_v3 import build_workspace_payload
from app.db.models import (
    DealerGexArchiveRun,
    DealerGexSnapshot,
    DealerGexSnapshotCell,
)
from app.dealer_archive.calendar import dealer_capture_session_plan
from app.dealer_archive.config import (
    DEALER_GEX_SURFACE_SCHEMA_VERSION,
    DealerGexArchiveConfig,
)
from app.dealer_archive.domain import normalize_dealer_gex_surface
from app.dealer_archive.repository import (
    best_archived_surface_at_or_before,
    persist_surface,
)
from app.dealer_archive.service import DealerGexArchiver
from app.nightwatch.errors import NightwatchError
from app.nightwatch.models import ApiUsageEvent

UTC = timezone.utc


@pytest.mark.parametrize(
    ("status", "expected_exit_code"),
    [
        ("COMPLETE", 0),
        ("DRY_RUN_READY", 0),
        ("SKIPPED_NON_TRADING_SESSION", 0),
        ("SKIPPED_TARGET_AFTER_EARLY_CLOSE", 0),
        ("PARTIAL", 4),
        ("EMPTY", 4),
        ("SKIPPED_DISABLED", 4),
    ],
)
def test_dealer_archive_exit_code_preserves_scheduler_observability(
    status: str, expected_exit_code: int
) -> None:
    assert dealer_gex_archive_exit_code(status) == expected_exit_code


def _payload(*, truncated: bool = False, generated_at: str = "2026-08-14T19:30:00Z") -> dict:
    return {
        "_meta": {
            "truncated": truncated,
            "request_id": "safe-vendor-request",
            "cache_hit": False,
            "data_freshness_seconds": 42,
            "rate_limit_remaining": 57,
            "quota_remaining_pct": 91.25,
        },
        "data": {
            "ticker": "NVDA",
            "generated_at": generated_at,
            "session_date_et": "2026-08-14",
            "market_status": "open",
            "spot_usd": 181.25,
            "expirations": ["2026-08-14", "2026-08-21"],
            "strikes_usd": [180, 185],
            "cells": [
                {
                    "expiration": "2026-08-14",
                    "strike_usd": 180,
                    "net_dealer_gex_usd": 0,
                },
                {
                    "expiration": "2026-08-21",
                    "strike_usd": 185,
                    "net_dealer_gex_usd": -250,
                },
            ],
        },
    }


def _config(universe: tuple[str, ...] = ("NVDA", "MSFT")) -> DealerGexArchiveConfig:
    return DealerGexArchiveConfig(
        version="test.v3.1",
        enabled=True,
        universe=universe,
        market_timezone="America/New_York",
        intended_capture_slot="15:30",
        max_network_attempts=len(universe),
        max_consumed_units=len(universe),
    )


def test_normalization_preserves_real_zero_and_missing_values() -> None:
    result = normalize_dealer_gex_surface(
        "NVDA",
        _payload(),
        source_http_status=200,
        captured_at=datetime(2026, 8, 14, 19, 31, tzinfo=UTC),
    )
    assert result.source_quality == "AVAILABLE"
    assert result.availability == "AVAILABLE"
    assert result.vendor_observed_at == datetime(2026, 8, 14, 19, 30, tzinfo=UTC)
    assert result.cells[0].net_dealer_gex_usd == 0
    assert result.cells[0].call_gex_usd is None
    assert result.cells[0].put_gex_usd is None
    assert result.cells[1].call_gex_usd is None
    assert result.observation_identity is not None
    assert result.quality_details["truncated_present"] is True
    assert result.quality_details["truncated_value"] is False
    assert result.quality_details["vendor_meta"]["request_id"] == "safe-vendor-request"


def test_default_request_profile_is_versioned_and_omits_format() -> None:
    config = _config(("NVDA",))
    assert config.endpoint_format is None
    assert DEALER_GEX_SURFACE_SCHEMA_VERSION == "nightwatch_dealer_heatmap_default_v1"


def test_missing_truncation_flag_is_distinct_and_degraded_not_truncated() -> None:
    payload = _payload()
    payload["_meta"].pop("truncated")
    result = normalize_dealer_gex_surface(
        "NVDA",
        payload,
        source_http_status=200,
        captured_at=datetime(2026, 8, 14, 19, 31, tzinfo=UTC),
    )
    assert result.source_quality == "AVAILABLE_DEGRADED"
    assert result.safe_error_code == "TRUNCATION_STATUS_MISSING_OR_INVALID"
    assert result.truncated is False
    assert result.quality_details["truncated_present"] is False
    assert len(result.cells) == 2


def test_same_vendor_observation_has_stable_analytical_identity() -> None:
    first = normalize_dealer_gex_surface(
        "NVDA", _payload(), source_http_status=200,
        captured_at=datetime(2026, 8, 14, 19, 31, tzinfo=UTC),
    )
    replay = normalize_dealer_gex_surface(
        "NVDA", _payload(), source_http_status=200,
        captured_at=datetime(2026, 8, 14, 19, 35, tzinfo=UTC),
    )
    assert first.observation_identity == replay.observation_identity


@pytest.mark.parametrize(
    ("mutator", "quality"),
    [
        (lambda payload: payload["data"].update({"generated_at": None}), "UNAVAILABLE"),
        (lambda payload: payload["data"]["cells"].append({"bad": "row"}),
         "INCOMPLETE_OR_TRUNCATED"),
    ],
)
def test_unusable_surface_never_persists_partial_cells(mutator, quality: str) -> None:  # type: ignore[no-untyped-def]
    payload = _payload()
    mutator(payload)
    result = normalize_dealer_gex_surface(
        "NVDA", payload, source_http_status=200,
        captured_at=datetime(2026, 8, 14, 19, 31, tzinfo=UTC),
    )
    assert result.source_quality == quality
    assert result.availability == "UNAVAILABLE"
    assert result.cells == ()
    assert result.observation_identity is None


def test_truncated_surface_is_retained_as_attempt_without_cells() -> None:
    result = normalize_dealer_gex_surface(
        "NVDA", _payload(truncated=True), source_http_status=200,
        captured_at=datetime(2026, 8, 14, 19, 31, tzinfo=UTC),
    )
    assert result.source_quality == "INCOMPLETE_OR_TRUNCATED"
    assert result.truncated is True
    assert not result.usable
    assert result.cells == ()


def test_archive_model_uniqueness_is_observation_and_run_scoped_not_ticker_date() -> None:
    run_unique = {
        tuple(column.name for column in constraint.columns)
        for constraint in DealerGexArchiveRun.__table__.constraints
        if constraint.__class__.__name__ == "UniqueConstraint"
    }
    snapshot_unique = {
        tuple(column.name for column in constraint.columns)
        for constraint in DealerGexSnapshot.__table__.constraints
        if constraint.__class__.__name__ == "UniqueConstraint"
    }
    cell_unique = {
        tuple(column.name for column in constraint.columns)
        for constraint in DealerGexSnapshotCell.__table__.constraints
        if constraint.__class__.__name__ == "UniqueConstraint"
    }
    assert ("ny_market_date", "intended_capture_slot", "scope_key") in run_unique
    assert ("observation_identity",) in snapshot_unique
    assert ("archive_run_id", "ticker") in snapshot_unique
    assert ("snapshot_id", "expiration", "strike") in cell_unique


def test_persist_surface_reuses_replayed_observation_without_new_cells() -> None:
    surface = normalize_dealer_gex_surface(
        "NVDA", _payload(), source_http_status=200,
        captured_at=datetime(2026, 8, 14, 19, 31, tzinfo=UTC),
    )
    existing = SimpleNamespace(id=uuid.uuid4())

    class Session:
        def scalar(self, _statement):  # type: ignore[no-untyped-def]
            return existing

        def add(self, _row):  # type: ignore[no-untyped-def]
            raise AssertionError("replay must not add a second analytical snapshot")

    run = SimpleNamespace(id=uuid.uuid4(), specification_version="signal_spec_v3.1_phase2b")
    row, reused = persist_surface(
        Session(),  # type: ignore[arg-type]
        run=run,
        surface=surface,
        captured_at=datetime(2026, 8, 14, 19, 31, tzinfo=UTC),
        endpoint="/v1/derived/heatmap/NVDA/snapshot",
        source_request_id="safe-request",
        source_http_status=200,
        raw=SimpleNamespace(id=uuid.uuid4()),
        config=_config(("NVDA",)),
    )
    assert reused is True
    assert row is existing


def test_market_calendar_skips_weekend_and_target_after_early_close() -> None:
    weekend = dealer_capture_session_plan(
        datetime(2026, 8, 15, 15, tzinfo=UTC),
        timezone_name="America/New_York",
        local_time="15:30",
    )
    early_close = dealer_capture_session_plan(
        datetime(2026, 11, 27, 15, tzinfo=UTC),
        timezone_name="America/New_York",
        local_time="15:30",
    )
    assert weekend.status == "SKIPPED_NON_TRADING_SESSION"
    assert early_close.status == "SKIPPED_TARGET_AFTER_EARLY_CLOSE"
    assert early_close.session_close is not None


def test_temporal_archive_selection_requires_vendor_and_capture_time_no_later_than_cutoff() -> None:
    class Session:
        statement = None

        def scalar(self, statement):  # type: ignore[no-untyped-def]
            self.statement = statement
            return None

    session = Session()
    result = best_archived_surface_at_or_before(
        session,  # type: ignore[arg-type]
        ticker="NVDA",
        as_of=datetime(2026, 8, 14, 19, 30, tzinfo=UTC),
    )
    sql = str(session.statement)
    assert result is None
    assert "vendor_observed_at <=" in sql
    assert "captured_at <=" in sql
    assert "is_analytical_observation" in sql


def test_new_workspace_preserves_archive_snapshot_provenance_and_adjacent_scope() -> None:
    evaluated_at = datetime(2026, 8, 14, 19, 35, tzinfo=UTC)
    evaluation = SimpleNamespace(
        id=uuid.uuid4(), ticker="NVDA", contract_symbol="NVDA260821C00180000",
        expiration=date(2026, 8, 21), right="C", strike=180,
        dte_at_detection=7, direction="UNRESOLVED", phase2a_evidence={},
        source_timestamps={}, specification_version="signal_spec_v1.2_phase2b",
        evaluated_at=evaluated_at,
    )
    context = SimpleNamespace(
        id=uuid.uuid4(), dealer_heatmap={}, stock_state={"current_price_usd": 181.25},
        raw_payload_ids=[], source_request_ids=[], source_timestamps={},
    )
    state = SimpleNamespace(
        id=uuid.uuid4(), specification_version="signal_spec_v2.0_phase2b",
        positioning_state={}, price_state={}, volatility_state={}, execution_state={},
    )
    snapshot = SimpleNamespace(
        id=uuid.uuid4(), raw_payload_id=uuid.uuid4(), source_request_id="safe-request",
        vendor_observed_at=datetime(2026, 8, 14, 19, 30, tzinfo=UTC),
        captured_at=datetime(2026, 8, 14, 19, 31, tzinfo=UTC),
    )
    result = build_workspace_payload(
        evaluation,
        context,
        state,
        dealer_heatmap={
            "availability": "AVAILABLE", "spot_usd": 181.25,
            "generated_at": "2026-08-14T19:30:00Z",
            "cells": [
                {"expiration": "2026-08-14", "strike_usd": 180,
                 "net_dealer_gex_usd": 10},
                {"expiration": "2026-08-21", "strike_usd": 180,
                 "net_dealer_gex_usd": 20},
                {"expiration": "2026-08-28", "strike_usd": 180,
                 "net_dealer_gex_usd": 30},
                {"expiration": "2026-09-18", "strike_usd": 180,
                 "net_dealer_gex_usd": 40},
            ],
        },
        dealer_archive_snapshot=snapshot,
    )
    provenance = result["provenance"]
    adjacent = result["trade_structure"]["dealer_gex"]["adjacent_expiry_context"]
    assert provenance["dealer_snapshot_source"] == "DEALER_GEX_ARCHIVE"
    assert provenance["dealer_snapshot_reference"] == str(snapshot.id)
    assert provenance["dealer_snapshot_source_time_eligible"] is True
    assert adjacent["previous"]["expiration"] == "2026-08-14"
    assert adjacent["next"]["expiration"] == "2026-08-28"
    assert adjacent["scope"] == "NEAREST_PREVIOUS_ANCHOR_NEAREST_NEXT_ONLY"


@pytest.mark.asyncio
async def test_partial_vendor_failure_keeps_prior_ticker_success_and_never_retries(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class Session:
        def scalar(self, _statement):  # type: ignore[no-untyped-def]
            return True if "pg_try_advisory_lock" in str(_statement) else None

        def add(self, row):  # type: ignore[no-untyped-def]
            if getattr(row, "id", None) is None:
                row.id = uuid.uuid4()

        def commit(self) -> None:
            return None

        def execute(self, _statement):  # type: ignore[no-untyped-def]
            return None

    class Client:
        _usage_observer = None

        def __init__(self) -> None:
            self.calls: list[tuple[str, str, object]] = []

        async def request(self, _method, path, **kwargs):  # type: ignore[no-untyped-def]
            ticker = kwargs["ticker"]
            self.calls.append((ticker, path, kwargs.get("params")))
            event = ApiUsageEvent(
                endpoint=path,
                command="phase2b.dealer_gex_archive",
                requested_at=datetime(2026, 8, 14, 19, 30, tzinfo=UTC),
                ticker=ticker,
                http_status=200 if ticker == "NVDA" else 400,
                consumed_quota=True if ticker == "NVDA" else None,
                quota_remaining=99 if ticker == "NVDA" else 99,
                request_id=f"safe-{ticker}",
                latency_ms=1,
                attempt_count=1,
                retry_count=0,
                error_code=None if ticker == "NVDA" else "VALIDATION_ERROR",
            )
            self._usage_observer(event)
            if ticker == "MSFT":
                raise NightwatchError(
                    "fixture", status_code=400, code="VALIDATION_ERROR",
                    request_id="safe-MSFT",
                )
            return SimpleNamespace(
                payload=_payload(), status_code=200,
                vendor_request_id="safe-vendor-NVDA", request_id="safe-NVDA",
            )

    monkeypatch.setattr(
        "app.dealer_archive.service.existing_archive_run", lambda *_args, **_kwargs: None
    )
    monkeypatch.setattr(
        "app.dealer_archive.service.persist_api_usage", lambda *_args, **_kwargs: None
    )
    raw_endpoints: list[str] = []

    def persist_raw(*_args, **kwargs):  # type: ignore[no-untyped-def]
        raw_endpoints.append(kwargs["endpoint"])
        return SimpleNamespace(id=uuid.uuid4())

    monkeypatch.setattr("app.dealer_archive.service.RawIngestor.persist", persist_raw)
    monkeypatch.setattr(
        "app.dealer_archive.service.persist_surface",
        lambda *_args, **_kwargs: (SimpleNamespace(id=uuid.uuid4()), False),
    )
    client = Client()
    summary = await DealerGexArchiver(
        Session(), client, _config()  # type: ignore[arg-type]
    ).execute(now=datetime(2026, 8, 14, 18, tzinfo=UTC))
    assert client.calls == [
        ("NVDA", "/v1/derived/heatmap/NVDA/snapshot", None),
        ("MSFT", "/v1/derived/heatmap/MSFT/snapshot", None),
    ]
    assert raw_endpoints == ["/v1/derived/heatmap/NVDA/snapshot"]
    assert all("format=full" not in path for _ticker, path, _params in client.calls)
    assert summary.status == "PARTIAL"
    assert summary.tickers_attempted == 2
    assert summary.tickers_succeeded == 1
    assert summary.tickers_failed == 1
    assert summary.network_attempts == 2
    assert summary.consumed_quota_units == 1
    assert all(row.get("request_id", "").startswith("safe-") for row in summary.tickers)


@pytest.mark.asyncio
async def test_dry_run_has_no_database_or_network_side_effects() -> None:
    class Forbidden:
        def __getattr__(self, _name):  # type: ignore[no-untyped-def]
            raise AssertionError("dry-run must not touch this dependency")

    summary = await DealerGexArchiver(
        Forbidden(), Forbidden(), _config(("NVDA",))  # type: ignore[arg-type]
    ).execute(dry_run=True, now=datetime(2026, 8, 14, 18, tzinfo=UTC))
    assert summary.status == "DRY_RUN_READY"
    assert summary.network_attempts == 0
    assert summary.archive_run_id is None

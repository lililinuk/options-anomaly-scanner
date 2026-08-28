from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import date, datetime
from time import perf_counter
from typing import Any

from sqlalchemy import select, text
from sqlalchemy.orm import Session

from app.core.time import utc_now
from app.db.models import DealerGexArchiveRun, RawVendorPayload
from app.dealer_archive.calendar import dealer_capture_session_plan
from app.dealer_archive.config import (
    DEALER_GEX_ARCHIVE_SPEC_VERSION,
    DEALER_GEX_ENDPOINT_TEMPLATE,
    DealerGexArchiveConfig,
    active_dealer_gex_archive_config,
)
from app.dealer_archive.domain import normalize_dealer_gex_surface, unavailable_surface
from app.dealer_archive.repository import persist_surface, reusable_completed_archive_run
from app.ingestion.raw import RawIngestor, parse_vendor_observed_at
from app.nightwatch.client import NightwatchClient
from app.nightwatch.errors import NightwatchError
from app.nightwatch.models import ApiUsageEvent
from app.persistence.api_usage import persist_api_usage


class DealerGexArchiveConcurrentError(RuntimeError):
    pass


@dataclass(frozen=True)
class DealerGexArchiveSummary:
    archive_run_id: uuid.UUID | None
    status: str
    market_date: str
    intended_capture_slot: str
    tickers: tuple[dict[str, Any], ...]
    tickers_attempted: int
    tickers_succeeded: int
    tickers_failed: int
    observations_reused: int
    network_attempts: int
    consumed_quota_units: int
    quota_remaining_before: int | None
    quota_remaining_after: int | None
    dry_run: bool = False


def _summary_from_run(run: DealerGexArchiveRun) -> DealerGexArchiveSummary:
    ticker_rows = run.summary.get("tickers", []) if isinstance(run.summary, dict) else []
    return DealerGexArchiveSummary(
        archive_run_id=run.id,
        status=run.status,
        market_date=run.ny_market_date.isoformat() if run.ny_market_date else "UNAVAILABLE",
        intended_capture_slot=run.intended_capture_slot,
        tickers=tuple(ticker_rows if isinstance(ticker_rows, list) else []),
        tickers_attempted=run.tickers_attempted,
        tickers_succeeded=run.tickers_succeeded,
        tickers_failed=run.tickers_failed,
        observations_reused=run.observations_reused,
        network_attempts=run.network_attempts,
        consumed_quota_units=run.consumed_quota_units,
        quota_remaining_before=run.quota_remaining_before,
        quota_remaining_after=run.quota_remaining_after,
    )


class DealerGexArchiver:
    """Sequentially capture one full Dealer/GEX surface per requested MAG7 ticker."""

    def __init__(
        self,
        session: Session,
        client: NightwatchClient,
        config: DealerGexArchiveConfig | None = None,
    ) -> None:
        self.session = session
        self.client = client
        self.config = config or active_dealer_gex_archive_config()
        self._events: list[ApiUsageEvent] = []
        self._run: DealerGexArchiveRun | None = None

    def _observe_usage(self, event: ApiUsageEvent) -> None:
        self._events.append(event)
        persist_api_usage(self.session, event)
        self.session.commit()

    async def execute(
        self,
        *,
        tickers: tuple[str, ...] | None = None,
        trigger: str = "cli",
        dry_run: bool = False,
        now: datetime | None = None,
        intended_market_date: date | None = None,
        canonical_slot_id: uuid.UUID | None = None,
    ) -> DealerGexArchiveSummary:
        started_clock = perf_counter()
        capture_time = now or utc_now()
        plan = dealer_capture_session_plan(
            capture_time,
            timezone_name=self.config.market_timezone,
            local_time=self.config.intended_capture_slot,
            enforce_target_time=trigger in {"external_scheduler", "google_cloud_scheduler"},
            intended_market_date=intended_market_date,
        )
        selected = tuple(dict.fromkeys(tickers or self.config.universe))
        invalid = sorted(set(selected).difference(self.config.universe))
        if invalid:
            raise ValueError("Dealer/GEX archive ticker must be in the configured MAG7 universe")
        scope_key = ",".join(sorted(selected))
        if dry_run:
            return DealerGexArchiveSummary(
                None,
                plan.status if not plan.should_capture else "DRY_RUN_READY",
                plan.market_date.isoformat(),
                self.config.intended_capture_slot,
                tuple({"ticker": ticker, "status": "PLANNED"} for ticker in selected),
                0,
                0,
                0,
                0,
                0,
                0,
                None,
                None,
                True,
            )

        config_hash = self.config.hash()
        if self.config.enabled and plan.should_capture:
            existing = reusable_completed_archive_run(
                self.session,
                market_date=plan.market_date,
                intended_capture_slot=self.config.intended_capture_slot,
                scope_key=scope_key,
                specification_version=DEALER_GEX_ARCHIVE_SPEC_VERSION,
                config_version=self.config.version,
                config_hash=config_hash,
                intended_at=plan.intended_at,
            )
            if existing is not None:
                return _summary_from_run(existing)

        if not bool(
            self.session.scalar(
                text("SELECT pg_try_advisory_lock(hashtext('dealer_gex_time_series_archive'))")
            )
        ):
            raise DealerGexArchiveConcurrentError("A Dealer/GEX archive is already running")
        original_observer: Any = None
        observer_installed = False
        try:
            if self.config.enabled and plan.should_capture:
                existing = reusable_completed_archive_run(
                    self.session,
                    market_date=plan.market_date,
                    intended_capture_slot=self.config.intended_capture_slot,
                    scope_key=scope_key,
                    specification_version=DEALER_GEX_ARCHIVE_SPEC_VERSION,
                    config_version=self.config.version,
                    config_hash=config_hash,
                    intended_at=plan.intended_at,
                )
                if existing is not None:
                    return _summary_from_run(existing)

            self._run = DealerGexArchiveRun(
                canonical_slot_id=canonical_slot_id,
                trigger=trigger,
                status="RUNNING",
                started_at=capture_time,
                ny_market_date=plan.market_date,
                intended_capture_slot=self.config.intended_capture_slot,
                scope_key=scope_key,
                market_timezone=self.config.market_timezone,
                universe=list(selected),
                specification_version=DEALER_GEX_ARCHIVE_SPEC_VERSION,
                config_version=self.config.version,
                config_hash=config_hash,
                configuration_snapshot={
                    **self.config.snapshot(),
                    "scheduler": "EXTERNAL_DURABLE_SCHEDULER_REQUIRED",
                    "session_close": (
                        plan.session_close.isoformat() if plan.session_close else None
                    ),
                },
                summary={},
            )
            self.session.add(self._run)
            self.session.commit()
            if not self.config.enabled:
                return self._finish("SKIPPED_DISABLED", [], started_clock)
            if not plan.should_capture:
                return self._finish(plan.status, [], started_clock)

            original_observer = getattr(self.client, "_usage_observer", None)
            self.client._usage_observer = self._observe_usage
            observer_installed = True

            ticker_results: list[dict[str, Any]] = []
            for ticker in selected:
                if (
                    sum(event.attempt_count for event in self._events)
                    >= self.config.max_network_attempts
                    or sum(event.consumed_quota is True for event in self._events)
                    >= self.config.max_consumed_units
                ):
                    ticker_results.append(
                        {"ticker": ticker, "status": "BUDGET_NOT_ATTEMPTED"}
                    )
                    continue
                ticker_results.append(await self._capture_ticker(ticker))
            status = (
                "COMPLETE"
                if ticker_results
                and all(row["status"] in {"PERSISTED", "REUSED"} for row in ticker_results)
                else "PARTIAL"
                if ticker_results
                else "EMPTY"
            )
            return self._finish(status, ticker_results, started_clock)
        except Exception as error:
            if self._run is not None:
                self._run.status = "FAILED"
                self._run.completed_at = utc_now()
                self._run.summary = {"safe_error": type(error).__name__}
                self._set_usage_totals()
                self.session.commit()
            raise
        finally:
            if observer_installed:
                self.client._usage_observer = original_observer
            self.session.execute(
                text("SELECT pg_advisory_unlock(hashtext('dealer_gex_time_series_archive'))")
            )
            self.session.commit()

    async def _capture_ticker(self, ticker: str) -> dict[str, Any]:
        assert self._run is not None
        endpoint = DEALER_GEX_ENDPOINT_TEMPLATE.format(ticker=ticker)
        captured_at = utc_now()
        request_parameters = (
            {"format": self.config.endpoint_format}
            if self.config.endpoint_format is not None
            else None
        )
        try:
            result = await self.client.request(
                "GET",
                endpoint,
                params=request_parameters,
                command="phase2b.dealer_gex_archive",
                ticker=ticker,
            )
            request_id = result.vendor_request_id or result.request_id
            raw = self.session.scalar(
                select(RawVendorPayload).where(
                    RawVendorPayload.source == "nightwatch",
                    RawVendorPayload.request_id == request_id,
                )
            )
            if raw is None:
                raw_endpoint = (
                    f"{endpoint}?format={self.config.endpoint_format}"
                    if self.config.endpoint_format is not None
                    else endpoint
                )
                raw = RawIngestor(self.session).persist(
                    endpoint=raw_endpoint,
                    request_id=request_id,
                    vendor_request_id=result.vendor_request_id,
                    payload=result.payload,
                    ticker=ticker,
                    vendor_observed_at=parse_vendor_observed_at(result.payload),
                    scan_run_id=None,
                )
            surface = normalize_dealer_gex_surface(
                ticker,
                result.payload if isinstance(result.payload, dict) else None,
                source_http_status=result.status_code,
                captured_at=captured_at,
            )
            snapshot, reused = persist_surface(
                self.session,
                run=self._run,
                surface=surface,
                captured_at=captured_at,
                endpoint=endpoint,
                source_request_id=request_id,
                source_http_status=result.status_code,
                raw=raw,
                config=self.config,
            )
            self.session.commit()
            ticker_status = (
                "REUSED"
                if reused
                else "PERSISTED"
                if surface.usable
                else surface.source_quality
            )
            return {
                "ticker": ticker,
                "status": ticker_status,
                "http_status": result.status_code,
                "source_quality": surface.source_quality,
                "vendor_observed_at": (
                    surface.vendor_observed_at.isoformat()
                    if surface.vendor_observed_at
                    else None
                ),
                "snapshot_id": str(snapshot.id),
                "request_id": request_id,
                "cells": len(surface.cells),
                "expirations": len({cell.expiration for cell in surface.cells}),
                "safe_error_code": surface.safe_error_code,
                "payload_structure": surface.quality_details,
            }
        except NightwatchError as error:
            surface = unavailable_surface(
                ticker,
                safe_error_code=error.code or type(error).__name__,
                source_http_status=error.status_code,
            )
            snapshot, _ = persist_surface(
                self.session,
                run=self._run,
                surface=surface,
                captured_at=captured_at,
                endpoint=endpoint,
                source_request_id=error.request_id,
                source_http_status=error.status_code,
                raw=None,
                config=self.config,
            )
            self.session.commit()
            return {
                "ticker": ticker,
                "status": "UNAVAILABLE",
                "http_status": error.status_code,
                "source_quality": "UNAVAILABLE",
                "vendor_observed_at": None,
                "snapshot_id": str(snapshot.id),
                "request_id": error.request_id,
                "cells": 0,
                "expirations": 0,
                "safe_error_code": error.code or type(error).__name__,
                "payload_structure": {},
            }

    def _set_usage_totals(self) -> None:
        assert self._run is not None
        self._run.network_attempts = sum(event.attempt_count for event in self._events)
        self._run.http_successes = sum(
            event.http_status is not None and event.http_status < 400 for event in self._events
        )
        self._run.http_failures = sum(
            event.http_status is None or event.http_status >= 400 for event in self._events
        )
        self._run.consumed_quota_units = sum(
            event.consumed_quota is True for event in self._events
        )
        remaining = [
            event.quota_remaining
            for event in self._events
            if event.quota_remaining is not None
        ]
        self._run.quota_remaining_after = remaining[-1] if remaining else None
        if self._events and self._events[0].quota_remaining is not None:
            self._run.quota_remaining_before = self._events[0].quota_remaining + (
                1 if self._events[0].consumed_quota is True else 0
            )

    def _finish(
        self,
        status: str,
        ticker_results: list[dict[str, Any]],
        started_clock: float,
    ) -> DealerGexArchiveSummary:
        assert self._run is not None
        attempted = [row for row in ticker_results if row["status"] != "BUDGET_NOT_ATTEMPTED"]
        succeeded = [row for row in attempted if row["status"] in {"PERSISTED", "REUSED"}]
        self._run.status = status
        self._run.completed_at = utc_now()
        self._run.tickers_attempted = len(attempted)
        self._run.tickers_succeeded = len(succeeded)
        self._run.tickers_failed = len(attempted) - len(succeeded)
        self._run.observations_reused = sum(row["status"] == "REUSED" for row in attempted)
        self._run.usable_snapshots = sum(
            row.get("source_quality") == "AVAILABLE" for row in attempted
        )
        self._run.degraded_snapshots = sum(
            row.get("source_quality") == "AVAILABLE_DEGRADED" for row in attempted
        )
        self._run.incomplete_snapshots = sum(
            row.get("source_quality") == "INCOMPLETE_OR_TRUNCATED" for row in attempted
        )
        self._run.unavailable_snapshots = sum(
            row.get("source_quality") == "UNAVAILABLE" for row in attempted
        )
        self._set_usage_totals()
        self._run.summary = {
            "tickers": ticker_results,
            "elapsed_seconds": round(perf_counter() - started_clock, 3),
            "retry_count": sum(event.retry_count for event in self._events),
            "analysis_labels_computed": False,
            "actionability_computed": False,
        }
        self.session.commit()
        return _summary_from_run(self._run)

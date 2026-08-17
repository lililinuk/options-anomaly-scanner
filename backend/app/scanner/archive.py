from __future__ import annotations

import uuid
from dataclasses import asdict, dataclass
from datetime import date
from decimal import Decimal
from time import perf_counter
from typing import Any

from sqlalchemy import select, text
from sqlalchemy.orm import Session

from app.core.time import utc_now
from app.db.models import (
    ContractOiDailySnapshot,
    DailyOiArchiveRun,
    DailyOiArchiveTicker,
    ExpiryOiDailySnapshot,
    RawVendorPayload,
)
from app.ingestion.raw import RawIngestor, parse_vendor_observed_at
from app.models.signals import bucket_for_dte, calendar_dte
from app.nightwatch.client import NightwatchClient
from app.nightwatch.errors import NightwatchError
from app.nightwatch.models import ApiUsageEvent, NightwatchResult
from app.persistence.api_usage import persist_api_usage
from app.scanner.config import ARCHIVE_LIMITS, SIGNAL_SPEC_VERSION, UNIVERSE
from app.scanner.parsers import parse_complete_chain, parse_daily_expiry_oi


class ArchiveConcurrentError(RuntimeError):
    pass


class ArchiveBudgetExceeded(RuntimeError):
    pass


@dataclass(frozen=True)
class ArchiveSummary:
    archive_run_id: uuid.UUID
    status: str
    vendor_dates: dict[str, str | None]
    tickers_attempted: int
    tickers_skipped: int
    expiries_attempted: int
    complete_chains: int
    incomplete_chains: int
    contracts_persisted: int
    consumed_quota_units: int
    network_attempts: int
    elapsed_seconds: float


class ArchiveBudget:
    def __init__(self, session: Session) -> None:
        self.session = session
        self.consumed = 0
        self.attempts = 0

    def ensure_room(self) -> None:
        if self.consumed >= ARCHIVE_LIMITS.max_consumed_units:
            raise ArchiveBudgetExceeded("archive quota budget reached")
        if self.attempts >= ARCHIVE_LIMITS.max_network_attempts:
            raise ArchiveBudgetExceeded("archive network-attempt budget reached")

    def observe(self, event: ApiUsageEvent) -> None:
        self.attempts += event.attempt_count
        if event.consumed_quota:
            self.consumed += 1
        persist_api_usage(self.session, event)
        self.session.commit()


class DailyOiArchiver:
    def __init__(self, session: Session, client: NightwatchClient) -> None:
        self.session = session
        self.client = client
        self.run: DailyOiArchiveRun | None = None
        self.budget = ArchiveBudget(session)
        self.budget_limited = False

    async def execute(self, *, trigger: str = "cli") -> ArchiveSummary:
        started_clock = perf_counter()
        if not bool(
            self.session.scalar(
                text("SELECT pg_try_advisory_lock(hashtext('mag7_daily_oi_archive'))")
            )
        ):
            raise ArchiveConcurrentError("A daily OI archive is already running")
        try:
            self.run = DailyOiArchiveRun(
                trigger=trigger,
                status="RUNNING",
                started_at=utc_now(),
                configuration_snapshot={
                    "daily_oi_archive": asdict(ARCHIVE_LIMITS),
                    "universe": list(UNIVERSE),
                },
                specification_version=SIGNAL_SPEC_VERSION,
                summary={},
            )
            self.session.add(self.run)
            self.session.commit()
            self.client._usage_observer = self.budget.observe
            for ticker_index, ticker in enumerate(UNIVERSE):
                try:
                    await self._archive_ticker(ticker)
                except ArchiveBudgetExceeded:
                    self.budget_limited = True
                    self._mark_unattempted_tickers(UNIVERSE[ticker_index:])
                    break
                except NightwatchError as error:
                    self.session.add(
                        DailyOiArchiveTicker(
                            archive_run_id=self.run.id,
                            ticker=ticker,
                            status="VENDOR_ERROR",
                            details={"safe_error": type(error).__name__},
                        )
                    )
                    self.session.commit()
            return self._finish(started_clock)
        except Exception as error:
            if self.run:
                self.run.status = "FAILED"
                self.run.completed_at = utc_now()
                self.run.consumed_quota_units = self.budget.consumed
                self.run.network_attempts = self.budget.attempts
                self.run.summary = {"safe_error": type(error).__name__}
                self.session.commit()
            raise
        finally:
            self.session.execute(
                text("SELECT pg_advisory_unlock(hashtext('mag7_daily_oi_archive'))")
            )
            self.session.commit()

    async def _archive_ticker(self, ticker: str) -> None:
        assert self.run
        oi_result, oi_raw = await self._fetch(
            f"/v1/options/oi-per-expiry/{ticker}",
            ticker=ticker,
            command="daily_archive.options.oi_per_expiry",
        )
        parsed = parse_daily_expiry_oi(oi_result.payload)
        vendor_dates = {row.vendor_date for row in parsed}
        if not parsed or len(vendor_dates) != 1:
            self.session.add(
                DailyOiArchiveTicker(
                    archive_run_id=self.run.id,
                    ticker=ticker,
                    status="INVALID_OI_SURFACE",
                    details={
                        "parsed_expiries": len(parsed),
                        "vendor_date_count": len(vendor_dates),
                    },
                )
            )
            self.session.commit()
            return
        vendor_date = next(iter(vendor_dates))
        vendor_as_of = parsed[0].vendor_as_of
        existing = self.session.scalar(
            select(ExpiryOiDailySnapshot.id)
            .where(
                ExpiryOiDailySnapshot.ticker == ticker,
                ExpiryOiDailySnapshot.vendor_oi_date == vendor_date,
            )
            .limit(1)
        )
        if existing is not None:
            self.session.add(
                DailyOiArchiveTicker(
                    archive_run_id=self.run.id,
                    ticker=ticker,
                    vendor_oi_date=vendor_date,
                    vendor_oi_as_of=vendor_as_of,
                    status="NO_NEW_VENDOR_OI_SNAPSHOT",
                    details={"reused_existing_snapshot": True},
                )
            )
            self.session.commit()
            return
        scoped = [
            row
            for row in parsed
            if 0 <= calendar_dte(row.expiration, vendor_date) <= ARCHIVE_LIMITS.max_dte
        ]
        shares = expiry_oi_shares(scoped)
        ticker_status = DailyOiArchiveTicker(
            archive_run_id=self.run.id,
            ticker=ticker,
            vendor_oi_date=vendor_date,
            vendor_oi_as_of=vendor_as_of,
            status="RUNNING",
            expiries_expected=len(scoped),
            details={},
        )
        self.session.add(ticker_status)
        snapshots: dict[date, ExpiryOiDailySnapshot] = {}
        for item in scoped:
            dte = calendar_dte(item.expiration, vendor_date)
            bucket = bucket_for_dte(dte)
            if bucket is None:
                continue
            snapshot = ExpiryOiDailySnapshot(
                archive_run_id=self.run.id,
                ticker=ticker,
                expiration=item.expiration,
                vendor_oi_date=vendor_date,
                vendor_oi_as_of=vendor_as_of,
                call_oi=item.call_oi,
                put_oi=item.put_oi,
                total_oi=item.call_oi + item.put_oi,
                call_oi_share=_dec(shares[item.expiration]["call"]),
                put_oi_share=_dec(shares[item.expiration]["put"]),
                total_oi_share=_dec(shares[item.expiration]["total"]),
                dte=dte,
                bucket=bucket.value,
                chain_status="PENDING",
                raw_payload_id=oi_raw.id,
                source_request_id=oi_result.vendor_request_id or oi_result.request_id,
                specification_version=SIGNAL_SPEC_VERSION,
            )
            self.session.add(snapshot)
            snapshots[item.expiration] = snapshot
        self.session.commit()

        incomplete_details: list[dict[str, Any]] = []
        expiry_items = list(snapshots.items())
        for expiry_index, (expiration, expiry_snapshot) in enumerate(expiry_items):
            try:
                chain_result, chain_raw = await self._fetch(
                    f"/v1/options/chain-snapshot/{ticker}",
                    params={"expiration": expiration.isoformat()},
                    ticker=ticker,
                    expiration=expiration,
                    command="daily_archive.options.chain_snapshot",
                )
            except ArchiveBudgetExceeded:
                omitted = mark_expiry_budget_omissions(expiry_items[expiry_index:])
                ticker_status.status = "PARTIAL_ARCHIVE_BUDGET_LIMIT"
                ticker_status.details = {"budget_not_attempted_expiries": omitted}
                self.session.commit()
                raise
            chain = parse_complete_chain(chain_result.payload, expiration)
            if not chain.complete:
                expiry_snapshot.chain_status = "INCOMPLETE_CHAIN"
                ticker_status.incomplete_chains += 1
                incomplete_details.append(
                    {
                        "expiration": expiration.isoformat(),
                        "returned": chain.returned_count,
                        "total": chain.total_contracts,
                        "truncated": chain.truncated,
                        "http_status": chain_result.status_code,
                    }
                )
                self.session.commit()
                continue
            for contract in chain.contracts:
                self.session.add(
                    ContractOiDailySnapshot(
                        archive_run_id=self.run.id,
                        ticker=ticker,
                        contract_symbol=contract.symbol,
                        vendor_oi_date=vendor_date,
                        vendor_oi_as_of=vendor_as_of,
                        expiration=expiration,
                        right=contract.right,
                        strike=contract.strike,
                        dte=expiry_snapshot.dte,
                        bucket=expiry_snapshot.bucket,
                        open_interest=contract.open_interest,
                        bid=contract.bid,
                        ask=contract.ask,
                        implied_volatility=contract.implied_volatility,
                        delta=contract.delta,
                        gamma=contract.gamma,
                        theta=contract.theta,
                        vega=contract.vega,
                        charm=contract.charm,
                        underlying_price=chain.underlying_price,
                        quote_as_of=chain.quote_as_of,
                        greeks_as_of=chain.greeks_as_of,
                        underlying_as_of=chain.underlying_as_of,
                        raw_payload_id=chain_raw.id,
                        source_request_id=chain_result.vendor_request_id or chain_result.request_id,
                        specification_version=SIGNAL_SPEC_VERSION,
                    )
                )
            expiry_snapshot.chain_status = "COMPLETE"
            ticker_status.complete_chains += 1
            ticker_status.contracts_persisted += len(chain.contracts)
            self.session.commit()
        ticker_status.status = (
            "COMPLETE" if not ticker_status.incomplete_chains else "PARTIAL_INCOMPLETE_CHAIN"
        )
        ticker_status.details = {"incomplete_expiries": incomplete_details}
        self.session.commit()

    def _mark_unattempted_tickers(self, tickers: tuple[str, ...]) -> None:
        assert self.run
        for ticker in tickers:
            existing = self.session.scalar(
                select(DailyOiArchiveTicker.id).where(
                    DailyOiArchiveTicker.archive_run_id == self.run.id,
                    DailyOiArchiveTicker.ticker == ticker,
                )
            )
            if existing is None:
                self.session.add(
                    DailyOiArchiveTicker(
                        archive_run_id=self.run.id,
                        ticker=ticker,
                        status="BUDGET_NOT_ATTEMPTED",
                        details={"reason": "archive_budget_limit"},
                    )
                )
        self.session.commit()

    async def _fetch(
        self,
        path: str,
        *,
        ticker: str,
        command: str,
        params: dict[str, str] | None = None,
        expiration: date | None = None,
    ) -> tuple[NightwatchResult, RawVendorPayload]:
        self.budget.ensure_room()
        result = await self.client.request(
            "GET",
            path,
            params=params,
            command=command,
            ticker=ticker,
            expiration=expiration.isoformat() if expiration else None,
        )
        source_request_id = result.vendor_request_id or result.request_id
        raw = RawIngestor(self.session).persist(
            endpoint=path + ("?expiration=" + expiration.isoformat() if expiration else ""),
            request_id=source_request_id,
            vendor_request_id=result.vendor_request_id,
            payload=result.payload,
            ticker=ticker,
            expiration=expiration,
            vendor_observed_at=parse_vendor_observed_at(result.payload),
            scan_run_id=None,
        )
        self.session.commit()
        return result, raw

    def _finish(self, started_clock: float) -> ArchiveSummary:
        assert self.run
        rows = list(
            self.session.scalars(
                select(DailyOiArchiveTicker).where(
                    DailyOiArchiveTicker.archive_run_id == self.run.id
                )
            )
        )
        status = (
            "PARTIAL_ARCHIVE_BUDGET_LIMIT"
            if self.budget_limited
            else "PARTIAL"
            if any(
                row.status in {"VENDOR_ERROR", "INVALID_OI_SURFACE", "PARTIAL_INCOMPLETE_CHAIN"}
                for row in rows
            )
            else "NO_NEW_VENDOR_OI_SNAPSHOT"
            if rows and all(row.status == "NO_NEW_VENDOR_OI_SNAPSHOT" for row in rows)
            else "COMPLETE"
        )
        elapsed = round(perf_counter() - started_clock, 3)
        values = {
            "vendor_dates": {
                row.ticker: row.vendor_oi_date.isoformat() if row.vendor_oi_date else None
                for row in rows
            },
            "tickers_attempted": len(rows),
            "tickers_skipped": sum(row.status == "NO_NEW_VENDOR_OI_SNAPSHOT" for row in rows),
            "expiries_attempted": sum(row.complete_chains + row.incomplete_chains for row in rows),
            "complete_chains": sum(row.complete_chains for row in rows),
            "incomplete_chains": sum(row.incomplete_chains for row in rows),
            "contracts_persisted": sum(row.contracts_persisted for row in rows),
        }
        self.run.status = status
        self.run.completed_at = utc_now()
        self.run.consumed_quota_units = self.budget.consumed
        self.run.network_attempts = self.budget.attempts
        self.run.summary = {**values, "elapsed_seconds": elapsed}
        self.session.commit()
        return ArchiveSummary(
            self.run.id,
            status,
            values["vendor_dates"],
            values["tickers_attempted"],
            values["tickers_skipped"],
            values["expiries_attempted"],
            values["complete_chains"],
            values["incomplete_chains"],
            values["contracts_persisted"],
            self.budget.consumed,
            self.budget.attempts,
            elapsed,
        )


def _dec(value: float | int | Decimal | None) -> Decimal | None:
    return Decimal(str(round(float(value), 8))) if value is not None else None


def expiry_oi_shares(rows: list[Any]) -> dict[date, dict[str, float | None]]:
    total_call = sum(row.call_oi for row in rows)
    total_put = sum(row.put_oi for row in rows)
    total_oi = total_call + total_put
    return {
        row.expiration: {
            "call": row.call_oi / total_call if total_call else None,
            "put": row.put_oi / total_put if total_put else None,
            "total": (row.call_oi + row.put_oi) / total_oi if total_oi else None,
        }
        for row in rows
    }


def mark_expiry_budget_omissions(
    rows: list[tuple[date, ExpiryOiDailySnapshot]],
) -> list[str]:
    omitted: list[str] = []
    for expiration, snapshot in rows:
        if snapshot.chain_status == "PENDING":
            snapshot.chain_status = "BUDGET_NOT_ATTEMPTED"
            omitted.append(expiration.isoformat())
    return omitted

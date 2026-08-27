from __future__ import annotations

import uuid
from collections import Counter
from dataclasses import asdict, dataclass
from datetime import date
from decimal import Decimal
from time import perf_counter
from typing import Any

from sqlalchemy import select, text
from sqlalchemy.orm import Session

from app.core.time import market_date, utc_now
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
    full_complete_chains: int = 0
    bounded_complete_chains: int = 0
    true_incomplete_chains: int = 0


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
        failed = False
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
                    self._emit_ticker_summary(ticker)
                except ArchiveBudgetExceeded:
                    self.budget_limited = True
                    self._mark_unattempted_tickers(UNIVERSE[ticker_index:])
                    self._emit_ticker_summary(ticker)
                    break
                except NightwatchError as error:
                    self.session.rollback()
                    ticker_row = self.session.scalar(
                        select(DailyOiArchiveTicker).where(
                            DailyOiArchiveTicker.archive_run_id == self.run.id,
                            DailyOiArchiveTicker.ticker == ticker,
                        )
                    )
                    if ticker_row is None:
                        ticker_row = DailyOiArchiveTicker(
                            archive_run_id=self.run.id,
                            ticker=ticker,
                        )
                        self.session.add(ticker_row)
                    ticker_row.status = "VENDOR_ERROR"
                    ticker_row.details = {
                        "safe_error": type(error).__name__,
                        "error_code": error.code,
                        "http_status": error.status_code,
                    }
                    self.session.commit()
                    self._emit_ticker_summary(ticker)
                except Exception as error:
                    print(
                        "Daily OI ticker: "
                        f"ticker={ticker} status=FAILED safe_error={type(error).__name__}"
                    )
                    raise
            return self._finish(started_clock)
        except Exception as error:
            failed = True
            self._finalize_failed_run(error)
            raise
        finally:
            try:
                self.session.execute(
                    text("SELECT pg_advisory_unlock(hashtext('mag7_daily_oi_archive'))")
                )
                self.session.commit()
            except Exception:
                self.session.rollback()
                if not failed:
                    raise

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
        unavailable_details: list[dict[str, Any]] = []
        bounded_complete_details: list[dict[str, Any]] = []
        full_complete_chains = 0
        bounded_complete_chains = 0
        active_chain_unavailable = False
        expiry_items = list(snapshots.items())
        for expiry_index, (expiration, expiry_snapshot) in enumerate(expiry_items):
            try:
                (
                    chain_result,
                    chain_raw,
                    materialization_reason,
                    materialization_attempts,
                ) = await self._fetch_materialized_chain(
                    ticker=ticker,
                    expiration=expiration,
                )
            except ArchiveBudgetExceeded:
                omitted = mark_expiry_budget_omissions(expiry_items[expiry_index:])
                ticker_status.status = "PARTIAL_ARCHIVE_BUDGET_LIMIT"
                ticker_status.details = {"budget_not_attempted_expiries": omitted}
                self.session.commit()
                raise
            except NightwatchError as error:
                if error.status_code != 404:
                    raise
                expired = expiration < market_date(utc_now())
                classification = (
                    "EXPIRED_EXPIRY_CHAIN_404" if expired else "ACTIVE_EXPIRY_CHAIN_404"
                )
                expiry_snapshot.chain_status = (
                    "EXPIRED_CHAIN_UNAVAILABLE" if expired else "ACTIVE_CHAIN_UNAVAILABLE"
                )
                ticker_status.incomplete_chains += 1
                active_chain_unavailable = active_chain_unavailable or not expired
                unavailable_details.append(
                    {
                        "expiration": expiration.isoformat(),
                        "classification": classification,
                        "safe_error": type(error).__name__,
                        "error_code": error.code,
                        "http_status": error.status_code,
                        "blocks_active_coverage": not expired,
                    }
                )
                self.session.commit()
                continue
            if materialization_reason is not None:
                expiry_snapshot.chain_status = materialization_reason
                ticker_status.incomplete_chains += 1
                incomplete_details.append(
                    {
                        "expiration": expiration.isoformat(),
                        "reason": materialization_reason,
                        "returned": 0,
                        "total": None,
                        "truncated": None,
                        "http_status": chain_result.status_code,
                        "materialization_attempts": materialization_attempts,
                    }
                )
                self.session.commit()
                continue
            chain = parse_complete_chain(chain_result.payload, expiration)
            if not chain.complete:
                expiry_snapshot.chain_status = chain.reason
                ticker_status.incomplete_chains += 1
                incomplete_details.append(
                    {
                        "expiration": expiration.isoformat(),
                        "reason": chain.reason,
                        "returned": chain.returned_count,
                        "total": chain.total_contracts,
                        "truncated": chain.truncated,
                        "http_status": chain_result.status_code,
                        "invalid_row_reasons": chain.invalid_row_reasons,
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
                        open_interest_as_of=contract.open_interest_as_of,
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
            # Preserve the accepted persisted full-chain literal consumed by Radar.
            # Bounded coverage remains explicitly distinct and is never promoted to
            # the legacy full-chain eligibility marker.
            expiry_snapshot.chain_status = (
                "COMPLETE_BOUNDED_SNAPSHOT"
                if chain.reason == "COMPLETE_BOUNDED_SNAPSHOT"
                else "COMPLETE"
            )
            ticker_status.complete_chains += 1
            ticker_status.contracts_persisted += len(chain.contracts)
            if chain.reason == "COMPLETE_BOUNDED_SNAPSHOT":
                bounded_complete_chains += 1
                assert chain.total_contracts is not None
                bounded_complete_details.append(
                    {
                        "expiration": expiration.isoformat(),
                        "coverage_type": "COMPLETE_BOUNDED_SNAPSHOT",
                        "coverage_scope": ARCHIVE_LIMITS.vendor_chain_coverage_scope,
                        "full_chain_available": False,
                        "vendor_contract_limit": ARCHIVE_LIMITS.vendor_chain_contract_limit,
                        "vendor_total_contracts": chain.total_contracts,
                        "contracts_returned": chain.returned_count,
                        "contracts_omitted": chain.total_contracts - chain.returned_count,
                        "pagination_supported": (
                            ARCHIVE_LIMITS.vendor_chain_pagination_supported
                        ),
                    }
                )
            else:
                full_complete_chains += 1
            self.session.commit()
        ticker_status.status = (
            "PARTIAL_INCOMPLETE_CHAIN"
            if incomplete_details or active_chain_unavailable
            else "COMPLETE"
        )
        ticker_status.details = {
            "incomplete_expiries": incomplete_details,
            "chain_unavailable": unavailable_details,
            "bounded_complete_expiries": bounded_complete_details,
            "full_complete_chains": full_complete_chains,
            "bounded_complete_chains": bounded_complete_chains,
            "true_incomplete_chains": len(incomplete_details)
            + sum(
                bool(item.get("blocks_active_coverage")) for item in unavailable_details
            ),
            "accepted_lifecycle_unavailable_chains": sum(
                not bool(item.get("blocks_active_coverage")) for item in unavailable_details
            ),
            "coverage_reason_counts": dict(
                sorted(
                    Counter(
                        ["FULL_COMPLETE"] * full_complete_chains
                        + ["COMPLETE_BOUNDED_SNAPSHOT"] * bounded_complete_chains
                        + [
                            str(item["classification"])
                            for item in unavailable_details
                            if item.get("classification")
                            and not item.get("blocks_active_coverage")
                        ]
                    ).items()
                )
            ),
            "incomplete_reason_counts": dict(
                sorted(
                    Counter(
                        [
                            str(item["reason"])
                            for item in incomplete_details
                            if item.get("reason")
                        ]
                        + [
                            str(item["classification"])
                            for item in unavailable_details
                            if item.get("classification")
                        ]
                    ).items()
                )
            ),
        }
        self.session.commit()

    async def _fetch_materialized_chain(
        self,
        *,
        ticker: str,
        expiration: date,
    ) -> tuple[NightwatchResult, RawVendorPayload, str | None, int]:
        started = perf_counter()
        attempts = 0
        while True:
            attempts += 1
            result, raw = await self._fetch(
                f"/v1/options/chain-snapshot/{ticker}",
                params={"expiration": expiration.isoformat()},
                ticker=ticker,
                expiration=expiration,
                command="daily_archive.options.chain_snapshot",
            )
            if result.status_code != 202:
                return result, raw, None, attempts

            delay = materialization_retry_after_seconds(result)
            elapsed = perf_counter() - started
            if (
                attempts >= ARCHIVE_LIMITS.materialization_max_attempts
                or elapsed + delay > ARCHIVE_LIMITS.materialization_max_wait_seconds
            ):
                return result, raw, "MATERIALIZATION_TIMEOUT", attempts
            await self.client.wait_for_materialization(delay)

    def _emit_ticker_summary(self, ticker: str) -> None:
        assert self.run
        row = self.session.scalar(
            select(DailyOiArchiveTicker).where(
                DailyOiArchiveTicker.archive_run_id == self.run.id,
                DailyOiArchiveTicker.ticker == ticker,
            )
        )
        if not isinstance(row, DailyOiArchiveTicker):
            return
        details = row.details if isinstance(row.details, dict) else {}
        reason_counts = details.get("incomplete_reason_counts")
        if not isinstance(reason_counts, dict):
            reason_counts = {}
        reasons = ",".join(
            f"{reason}={count}" for reason, count in sorted(reason_counts.items())
        ) or "none"
        coverage_reason_counts = details.get("coverage_reason_counts")
        if not isinstance(coverage_reason_counts, dict):
            coverage_reason_counts = {}
        coverage_reasons = ",".join(
            f"{reason}={count}"
            for reason, count in sorted(coverage_reason_counts.items())
        ) or "none"
        print(
            "Daily OI ticker: "
            f"ticker={row.ticker} status={row.status} "
            f"vendor_oi_date={row.vendor_oi_date.isoformat() if row.vendor_oi_date else None} "
            f"expiries_expected={row.expiries_expected} "
            f"complete_chains={row.complete_chains} "
            f"full_complete_chains={details.get('full_complete_chains', 0)} "
            f"bounded_chains={details.get('bounded_complete_chains', 0)} "
            f"incomplete_chains={row.incomplete_chains} "
            f"true_incomplete_chains={details.get('true_incomplete_chains', 0)} "
            f"contracts_persisted={row.contracts_persisted} "
            f"coverage_reasons={coverage_reasons} incomplete_reasons={reasons}"
        )

    def _finalize_failed_run(self, error: Exception) -> None:
        if self.run is None:
            self.session.rollback()
            return
        run_id = self.run.id
        values = {
            "status": "FAILED",
            "completed_at": utc_now(),
            "consumed_quota_units": self.budget.consumed,
            "network_attempts": self.budget.attempts,
            "summary": {"safe_error": type(error).__name__},
        }

        def assign(run: DailyOiArchiveRun) -> None:
            for name, value in values.items():
                setattr(run, name, value)

        self.session.rollback()
        try:
            run = self.session.get(DailyOiArchiveRun, run_id)
            if run is not None:
                assign(run)
                self.session.commit()
                return
        except Exception:
            self.session.rollback()

        # A failed SQLAlchemy transaction must not poison terminal-state persistence. Recover
        # through a fresh session bound to the same database if the original session cannot commit.
        try:
            bind = self.session.get_bind()
            with Session(bind=bind, expire_on_commit=False) as recovery:
                run = recovery.get(DailyOiArchiveRun, run_id)
                if run is not None:
                    assign(run)
                    recovery.commit()
        except Exception:
            self.session.rollback()

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
            "full_complete_chains": sum(
                int((row.details or {}).get("full_complete_chains", 0)) for row in rows
            ),
            "bounded_complete_chains": sum(
                int((row.details or {}).get("bounded_complete_chains", 0)) for row in rows
            ),
            "true_incomplete_chains": sum(
                int((row.details or {}).get("true_incomplete_chains", 0)) for row in rows
            ),
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
            values["full_complete_chains"],
            values["bounded_complete_chains"],
            values["true_incomplete_chains"],
        )


def materialization_retry_after_seconds(result: NightwatchResult) -> float:
    payload = result.payload if isinstance(result.payload, dict) else {}
    meta = payload.get("_meta") if isinstance(payload.get("_meta"), dict) else {}
    value = meta.get("retry_after_seconds")
    if isinstance(value, (int, float)) and not isinstance(value, bool) and value >= 0:
        return float(value)
    header_delay = result.quota.retry_after_seconds
    if header_delay is not None:
        return header_delay
    return ARCHIVE_LIMITS.materialization_default_retry_after_seconds


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

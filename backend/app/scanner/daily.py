from __future__ import annotations

import uuid
from collections.abc import Awaitable, Callable, Iterable
from dataclasses import asdict, dataclass
from datetime import date
from decimal import Decimal
from time import perf_counter
from typing import Any

from sqlalchemy import desc, func, select, text
from sqlalchemy.orm import Session

from app.core.time import market_date, utc_now
from app.db.models import (
    ContractOiDailySnapshot,
    ContractScanObservation,
    DailyCollectionCoverage,
    DailyCollectionRun,
    DailyExpiryActivitySnapshot,
    ExpiryOiDailySnapshot,
    OiChangeRadarObservation,
    RawVendorPayload,
    ZeroDteActivityDailySnapshot,
)
from app.ingestion.raw import RawIngestor
from app.models.signals import calendar_dte
from app.nightwatch.client import NightwatchClient
from app.nightwatch.errors import NightwatchError
from app.nightwatch.models import ApiUsageEvent, NightwatchResult
from app.persistence.api_usage import persist_api_usage
from app.scanner.archive import ArchiveSummary, DailyOiArchiver
from app.scanner.config import ARCHIVE_LIMITS, SIGNAL_SPEC_VERSION, UNIVERSE
from app.scanner.history import OiHistoryPoint, contract_persistence
from app.scanner.parsers import (
    parse_expiry_aggregates,
    parse_oi_change_radar,
    parse_ticker_activity,
)
from app.scanner.v13 import (
    active_radar_threshold_profile,
    evaluate_radar_material_event,
    radar_scope,
)


class DailyCollectionConcurrentError(RuntimeError):
    pass


class DailyCollectionBudgetExceeded(RuntimeError):
    pass


@dataclass(frozen=True)
class SubjobSummary:
    status: str
    tickers_attempted: int
    tickers_skipped: int
    rows_persisted: int
    details: dict[str, Any]


@dataclass(frozen=True)
class DailyCollectionSummary:
    daily_run_id: uuid.UUID
    status: str
    subjobs: dict[str, dict[str, Any]]
    consumed_quota_units: int
    network_attempts: int
    elapsed_seconds: float


class CollectionBudget:
    def __init__(self, session: Session) -> None:
        self.session = session
        self.consumed = 0
        self.attempts = 0

    def ensure_room(self) -> None:
        if self.consumed >= ARCHIVE_LIMITS.max_consumed_units:
            raise DailyCollectionBudgetExceeded("daily collection quota budget reached")
        if self.attempts >= ARCHIVE_LIMITS.max_network_attempts:
            raise DailyCollectionBudgetExceeded("daily collection network-attempt budget reached")

    def observe(self, event: ApiUsageEvent) -> None:
        self.attempts += event.attempt_count
        if event.consumed_quota:
            self.consumed += 1
        persist_api_usage(self.session, event)
        self.session.commit()


class DailyDataPipeline:
    """Durable, externally scheduled OI/Activity/Radar orchestration.

    Subjobs are deliberately isolated: one failure produces PARTIAL and preserves successful work.
    """

    def __init__(self, session: Session, client: NightwatchClient) -> None:
        self.session = session
        self.client = client
        self.profile = active_radar_threshold_profile()
        self.run: DailyCollectionRun | None = None
        self.budget = CollectionBudget(session)

    async def execute(self, *, trigger: str = "cli") -> DailyCollectionSummary:
        started_clock = perf_counter()
        now = utc_now()
        if not bool(
            self.session.scalar(text("SELECT pg_try_advisory_lock(hashtext('mag7_daily_v13'))"))
        ):
            raise DailyCollectionConcurrentError("A MAG7 daily collection is already running")
        try:
            self.run = DailyCollectionRun(
                trigger=trigger,
                status="RUNNING",
                started_at=now,
                ny_market_date=market_date(now),
                specification_version=SIGNAL_SPEC_VERSION,
                radar_threshold_profile_id=self.profile.profile_id,
                radar_threshold_profile_version=self.profile.version,
                radar_threshold_config_hash=self.profile.configuration_hash,
                configuration_snapshot={
                    "universe": list(UNIVERSE),
                    "daily_oi_archive": asdict(ARCHIVE_LIMITS),
                    "radar_discovery": self.profile.snapshot(),
                },
                subjobs={},
                summary={},
            )
            self.session.add(self.run)
            self.session.commit()

            subjobs: dict[str, dict[str, Any]] = {}
            oi_consumed = oi_attempts = 0
            try:
                oi = await DailyOiArchiver(self.session, self.client).execute(
                    trigger="daily_pipeline"
                )
                oi_consumed, oi_attempts = oi.consumed_quota_units, oi.network_attempts
                subjobs["daily_oi"] = _archive_summary(oi)
            except Exception as error:
                subjobs["daily_oi"] = _failed_subjob(error)

            self.client._usage_observer = self.budget.observe
            activity = await self._isolated(
                "activity", lambda: DailyActivityCollector(self).execute()
            )
            subjobs["activity"] = asdict(activity)
            radar = await self._isolated("radar", lambda: DailyRadarCollector(self).execute())
            subjobs["radar"] = asdict(radar)

            statuses = [str(item["status"]) for item in subjobs.values()]
            status = daily_pipeline_status(statuses)
            elapsed = round(perf_counter() - started_clock, 3)
            self.run.status = status
            self.run.completed_at = utc_now()
            self.run.subjobs = subjobs
            self.run.consumed_quota_units = oi_consumed + self.budget.consumed
            self.run.network_attempts = oi_attempts + self.budget.attempts
            self.run.summary = {"elapsed_seconds": elapsed}
            self.session.commit()
            return DailyCollectionSummary(
                self.run.id,
                status,
                subjobs,
                self.run.consumed_quota_units,
                self.run.network_attempts,
                elapsed,
            )
        finally:
            self.session.execute(text("SELECT pg_advisory_unlock(hashtext('mag7_daily_v13'))"))
            self.session.commit()

    async def _isolated(
        self, name: str, operation: Callable[[], Awaitable[SubjobSummary]]
    ) -> SubjobSummary:
        try:
            return await operation()
        except Exception as error:
            self.session.rollback()
            return SubjobSummary(
                "FAILED", 0, 0, 0, {"subjob": name, "safe_error": type(error).__name__}
            )

    async def fetch(
        self, path: str, *, ticker: str, command: str
    ) -> tuple[NightwatchResult, RawVendorPayload]:
        self.budget.ensure_room()
        result = await self.client.request("GET", path, ticker=ticker, command=command)
        source_request_id = result.vendor_request_id or result.request_id
        raw = RawIngestor(self.session).persist(
            endpoint=path,
            request_id=source_request_id,
            vendor_request_id=result.vendor_request_id,
            payload=result.payload,
            ticker=ticker,
            observed_at=utc_now(),
        )
        self.session.commit()
        return result, raw


class DailyRadarBackfill:
    """Controlled Radar-only collection for missing latest-date MAG7 coverage."""

    def __init__(self, session: Session, client: NightwatchClient) -> None:
        self.pipeline = DailyDataPipeline(session, client)

    async def execute(self, *, trigger: str = "cli") -> DailyCollectionSummary:
        started_clock = perf_counter()
        now = utc_now()
        session = self.pipeline.session
        if not bool(
            session.scalar(text("SELECT pg_try_advisory_lock(hashtext('mag7_daily_v13'))"))
        ):
            raise DailyCollectionConcurrentError("A MAG7 daily collection is already running")
        try:
            for stale in session.scalars(
                select(DailyCollectionRun).where(DailyCollectionRun.status == "RUNNING")
            ):
                stale.status = "FAILED"
                stale.completed_at = utc_now()
                stale.summary = {
                    "safe_error": "INTERRUPTED_PROCESS",
                    "recovered_after_advisory_lock_release": True,
                }
            session.commit()
            profile = self.pipeline.profile
            run = DailyCollectionRun(
                trigger=trigger,
                status="RUNNING",
                started_at=now,
                ny_market_date=market_date(now),
                specification_version=SIGNAL_SPEC_VERSION,
                radar_threshold_profile_id=profile.profile_id,
                radar_threshold_profile_version=profile.version,
                radar_threshold_config_hash=profile.configuration_hash,
                configuration_snapshot={
                    "universe": list(UNIVERSE),
                    "radar_discovery": profile.snapshot(),
                    "mode": "RADAR_MISSING_COVERAGE_ONLY",
                },
                subjobs={},
                summary={},
            )
            session.add(run)
            session.commit()
            self.pipeline.run = run
            self.pipeline.client._usage_observer = self.pipeline.budget.observe
            radar = await DailyRadarCollector(self.pipeline).execute()
            elapsed = round(perf_counter() - started_clock, 3)
            subjobs = {"radar": asdict(radar)}
            run.status = radar.status
            run.completed_at = utc_now()
            run.subjobs = subjobs
            run.consumed_quota_units = self.pipeline.budget.consumed
            run.network_attempts = self.pipeline.budget.attempts
            run.summary = {"elapsed_seconds": elapsed, "mode": "RADAR_MISSING_COVERAGE_ONLY"}
            session.commit()
            return DailyCollectionSummary(
                run.id,
                run.status,
                subjobs,
                run.consumed_quota_units,
                run.network_attempts,
                elapsed,
            )
        finally:
            session.execute(text("SELECT pg_advisory_unlock(hashtext('mag7_daily_v13'))"))
            session.commit()


class DailyActivityCollector:
    def __init__(self, pipeline: DailyDataPipeline) -> None:
        self.pipeline = pipeline
        self.session = pipeline.session

    async def execute(self) -> SubjobSummary:
        assert self.pipeline.run
        observation_date = self.pipeline.run.ny_market_date
        attempted = skipped = persisted = 0
        errors: dict[str, str] = {}
        for ticker in UNIVERSE:
            existing = self.session.scalar(
                select(DailyCollectionCoverage.id).where(
                    DailyCollectionCoverage.subjob == "ACTIVITY",
                    DailyCollectionCoverage.ticker == ticker,
                    DailyCollectionCoverage.observation_date == observation_date,
                    DailyCollectionCoverage.status == "COMPLETE",
                )
            )
            if existing:
                skipped += 1
                continue
            attempted += 1
            try:
                activity_result, activity_raw = await self.pipeline.fetch(
                    f"/v1/options/expiry-breakdown/{ticker}",
                    ticker=ticker,
                    command="daily_activity.options.expiry_breakdown",
                )
                context_result, context_raw = await self.pipeline.fetch(
                    f"/v1/options/options-volume/{ticker}",
                    ticker=ticker,
                    command="daily_activity.options.options_volume",
                )
                aggregates = [
                    row
                    for row in parse_expiry_aggregates(activity_result.payload)
                    if 0 <= calendar_dte(row.expiration, observation_date) <= 180
                ]
                if not aggregates:
                    raise ValueError("No scoped expiry activity rows")
                context = parse_ticker_activity(context_result.payload)
                total_volume = sum(row.total_volume for row in aggregates)
                source_ids = [
                    activity_result.vendor_request_id or activity_result.request_id,
                    context_result.vendor_request_id or context_result.request_id,
                ]
                for aggregate in aggregates:
                    exists = self.session.scalar(
                        select(DailyExpiryActivitySnapshot.id).where(
                            DailyExpiryActivitySnapshot.ticker == ticker,
                            DailyExpiryActivitySnapshot.expiration == aggregate.expiration,
                            DailyExpiryActivitySnapshot.observation_date == observation_date,
                        )
                    )
                    if exists:
                        continue
                    share = aggregate.total_volume / total_volume if total_volume else None
                    self.session.add(
                        DailyExpiryActivitySnapshot(
                            daily_run_id=self.pipeline.run.id,
                            ticker=ticker,
                            expiration=aggregate.expiration,
                            observation_date=observation_date,
                            captured_at=utc_now(),
                            vendor_date=context.vendor_date,
                            vendor_as_of=context.vendor_as_of,
                            dte=calendar_dte(aggregate.expiration, observation_date),
                            total_volume=aggregate.total_volume,
                            ticker_scope_volume=total_volume,
                            volume_share=_decimal(share),
                            call_volume_context=context.call_volume,
                            put_volume_context=context.put_volume,
                            raw_payload_ids=[str(activity_raw.id), str(context_raw.id)],
                            source_request_ids=source_ids,
                            specification_version=SIGNAL_SPEC_VERSION,
                        )
                    )
                    persisted += 1
                    if aggregate.expiration == observation_date and share is not None:
                        self._persist_zero_dte(
                            ticker,
                            observation_date,
                            aggregate.total_volume,
                            total_volume,
                            share,
                            activity_raw,
                            source_ids[0],
                        )
                self.session.add(
                    DailyCollectionCoverage(
                        daily_run_id=self.pipeline.run.id,
                        subjob="ACTIVITY",
                        ticker=ticker,
                        observation_date=observation_date,
                        vendor_as_of=context.vendor_as_of,
                        captured_at=utc_now(),
                        status="COMPLETE",
                        row_count=len(aggregates),
                        source_request_ids=source_ids,
                        details={
                            "vendor_date": context.vendor_date.isoformat()
                            if context.vendor_date
                            else None,
                            "ny_market_date": observation_date.isoformat(),
                        },
                    )
                )
                self.session.commit()
            except (NightwatchError, ValueError, DailyCollectionBudgetExceeded) as error:
                self.session.rollback()
                errors[ticker] = type(error).__name__
        status = "COMPLETE" if not errors else "PARTIAL" if persisted else "FAILED"
        return SubjobSummary(status, attempted, skipped, persisted, {"errors": errors})

    def _persist_zero_dte(
        self,
        ticker: str,
        observation_date: date,
        expiry_volume: int,
        scope_volume: int,
        share: float,
        raw: RawVendorPayload,
        source_request_id: str,
    ) -> None:
        assert self.pipeline.run
        existing = self.session.scalar(
            select(ZeroDteActivityDailySnapshot.id).where(
                ZeroDteActivityDailySnapshot.ticker == ticker,
                ZeroDteActivityDailySnapshot.observation_date == observation_date,
            )
        )
        if existing:
            return
        self.session.add(
            ZeroDteActivityDailySnapshot(
                scan_run_id=None,
                daily_run_id=self.pipeline.run.id,
                ticker=ticker,
                observation_date=observation_date,
                expiration=observation_date,
                expiry_volume=expiry_volume,
                ticker_scope_volume=scope_volume,
                volume_share=_decimal(share),
                raw_cross_expiry_neighbor_ratio=None,
                raw_payload_id=raw.id,
                source_request_id=source_request_id,
                specification_version=SIGNAL_SPEC_VERSION,
            )
        )


class DailyRadarCollector:
    def __init__(self, pipeline: DailyDataPipeline) -> None:
        self.pipeline = pipeline
        self.session = pipeline.session

    async def execute(self) -> SubjobSummary:
        assert self.pipeline.run
        self._backfill_existing_observations()
        targets = self._target_tickers()
        skipped = len(UNIVERSE) - len(targets)
        persisted = 0
        errors: dict[str, str] = {}
        vendor_dates: dict[str, str] = {}
        for ticker in targets:
            try:
                result, raw = await self.pipeline.fetch(
                    f"/v1/options/oi-change/{ticker}",
                    ticker=ticker,
                    command="daily_radar.options.oi_change",
                )
                parsed = parse_oi_change_radar(result.payload)
                dates = {row.observation_date for row in parsed if row.observation_date}
                if not parsed or len(dates) != 1:
                    raise ValueError("Radar payload lacks one authoritative observation date")
                observation_date = next(iter(dates))
                assert observation_date is not None
                vendor_dates[ticker] = observation_date.isoformat()
                coverage = self.session.scalar(
                    select(DailyCollectionCoverage.id).where(
                        DailyCollectionCoverage.subjob == "RADAR",
                        DailyCollectionCoverage.ticker == ticker,
                        DailyCollectionCoverage.observation_date == observation_date,
                        DailyCollectionCoverage.status == "COMPLETE",
                    )
                )
                if coverage:
                    skipped += 1
                    continue
                source_id = result.vendor_request_id or result.request_id
                for item in parsed:
                    existing = self.session.scalar(
                        select(OiChangeRadarObservation.id).where(
                            OiChangeRadarObservation.ticker == ticker,
                            OiChangeRadarObservation.contract_symbol == item.symbol,
                            OiChangeRadarObservation.observation_date == observation_date,
                        )
                    )
                    if existing:
                        continue
                    self.session.add(
                        self._observation(ticker, item, raw, source_id, observation_date)
                    )
                    persisted += 1
                self.session.add(
                    DailyCollectionCoverage(
                        daily_run_id=self.pipeline.run.id,
                        subjob="RADAR",
                        ticker=ticker,
                        observation_date=observation_date,
                        vendor_as_of=None,
                        captured_at=utc_now(),
                        status="COMPLETE",
                        row_count=len(parsed),
                        source_request_ids=[source_id],
                        details={"authoritative_date_source": "payload.contracts[].date"},
                    )
                )
                self.session.commit()
            except (NightwatchError, ValueError, DailyCollectionBudgetExceeded) as error:
                self.session.rollback()
                errors[ticker] = type(error).__name__
        status = (
            "NO_NEW_DATA"
            if not targets
            else "COMPLETE"
            if not errors
            else "PARTIAL"
            if persisted
            else "FAILED"
        )
        return SubjobSummary(
            status,
            len(targets),
            skipped,
            persisted,
            {"errors": errors, "vendor_dates": vendor_dates},
        )

    def _backfill_existing_observations(self) -> None:
        """Evaluate accepted legacy evidence locally; this performs no vendor request."""

        assert self.pipeline.run
        rows = list(
            self.session.scalars(
                select(OiChangeRadarObservation).where(
                    OiChangeRadarObservation.observation_date.is_not(None),
                    OiChangeRadarObservation.material_event_eligible.is_(None),
                )
            )
        )
        symbols = {row.contract_symbol for row in rows}
        archived_rows = list(
            self.session.scalars(
                select(ContractOiDailySnapshot)
                .where(ContractOiDailySnapshot.contract_symbol.in_(symbols))
                .order_by(
                    ContractOiDailySnapshot.contract_symbol,
                    ContractOiDailySnapshot.vendor_oi_date,
                )
            )
        )
        archived_by_symbol: dict[str, list[ContractOiDailySnapshot]] = {}
        for archived in archived_rows:
            archived_by_symbol.setdefault(archived.contract_symbol, []).append(archived)
        expiry_keys = {
            (row.ticker, row.expiration, row.vendor_oi_date) for row in archived_rows
        }
        expiry_rows = list(
            self.session.scalars(
                select(ExpiryOiDailySnapshot).where(
                    ExpiryOiDailySnapshot.ticker.in_({key[0] for key in expiry_keys})
                )
            )
        )
        expiry_by_key = {
            (row.ticker, row.expiration, row.vendor_oi_date): row for row in expiry_rows
        }
        structure_rows = list(
            self.session.scalars(
                select(ContractScanObservation)
                .where(ContractScanObservation.contract_symbol.in_(symbols))
                .order_by(ContractScanObservation.observed_at)
            )
        )
        structure_by_symbol = {row.contract_symbol: row for row in structure_rows}
        grouped: dict[tuple[str, date], list[OiChangeRadarObservation]] = {}
        for row in rows:
            assert row.observation_date
            eligibility = evaluate_radar_material_event(
                premium_usd=row.premium,
                oi_diff=row.delta_oi,
                previous_oi=row.previous_oi,
                profile=self.pipeline.profile,
            )
            history = [
                item
                for item in archived_by_symbol.get(row.contract_symbol, [])
                if item.vendor_oi_date <= row.observation_date
            ]
            archived = history[-1] if history else None
            expiry = (
                expiry_by_key.get(
                    (archived.ticker, archived.expiration, archived.vendor_oi_date)
                )
                if archived
                else None
            )
            complete = bool(expiry and expiry.chain_status == "COMPLETE")
            dte = calendar_dte(archived.expiration, row.observation_date) if archived else None
            scope = radar_scope(
                dte=dte,
                exact_match=archived is not None,
                chain_complete=complete,
            )
            persistence = contract_persistence(
                [OiHistoryPoint(item.vendor_oi_date, item.open_interest) for item in history],
                current_same_side_expiry_oi=None,
            )
            structure = structure_by_symbol.get(row.contract_symbol)
            row.captured_at = utc_now()
            row.ny_market_date = self.pipeline.run.ny_market_date
            row.material_event_eligible = eligibility.eligible
            row.radar_route_eligible = eligibility.eligible
            row.eligibility_reason = eligibility.reason
            row.threshold_profile_id = self.pipeline.profile.profile_id
            row.threshold_profile_version = self.pipeline.profile.version
            row.threshold_config_hash = self.pipeline.profile.configuration_hash
            row.effective_thresholds = self.pipeline.profile.snapshot()
            row.premium_per_trade = _per(_float(row.premium), row.trades)
            row.volume_per_trade = _per(row.volume, row.trades)
            row.archive_match_status = "EXACT" if archived else "UNAVAILABLE"
            row.matched_expiration = archived.expiration if archived else None
            row.matched_dte = dte
            row.matched_right = archived.right if archived else None
            row.matched_strike = archived.strike if archived else None
            row.archived_oi = archived.open_interest if archived else None
            row.archive_vendor_oi_date = archived.vendor_oi_date if archived else None
            row.archive_completeness = expiry.chain_status if expiry else "UNAVAILABLE"
            row.contract_structure_score = structure.structure_score if structure else None
            row.contract_persistent_score = _decimal(persistence.score)
            row.radar_scope = scope
            row.deep_dive_eligible = bool(
                eligibility.eligible and scope == "FULL_DEEP_DIVE_ELIGIBLE"
            )
            row.trigger_sources = ["RADAR_EVENT"] if eligibility.eligible else []
            row.risk_flags = list(eligibility.risk_flags)
            grouped.setdefault((row.ticker, row.observation_date), []).append(row)
        for (ticker, observation_date), group in grouped.items():
            existing = self.session.scalar(
                select(DailyCollectionCoverage.id).where(
                    DailyCollectionCoverage.subjob == "RADAR",
                    DailyCollectionCoverage.ticker == ticker,
                    DailyCollectionCoverage.observation_date == observation_date,
                )
            )
            if existing:
                continue
            self.session.add(
                DailyCollectionCoverage(
                    daily_run_id=self.pipeline.run.id,
                    subjob="RADAR",
                    ticker=ticker,
                    observation_date=observation_date,
                    vendor_as_of=None,
                    captured_at=utc_now(),
                    status="COMPLETE",
                    row_count=len(group),
                    source_request_ids=sorted({row.source_request_id for row in group}),
                    details={
                        "locally_evaluated_from_persisted_raw_evidence": True,
                        "network_request_performed": False,
                    },
                )
            )
        self.session.commit()

    def _target_tickers(self) -> tuple[str, ...]:
        latest = self.session.scalar(
            select(func.max(DailyCollectionCoverage.observation_date)).where(
                DailyCollectionCoverage.subjob == "RADAR",
                DailyCollectionCoverage.status == "COMPLETE",
            )
        )
        if latest is None:
            return UNIVERSE
        covered = set(
            self.session.scalars(
                select(DailyCollectionCoverage.ticker).where(
                    DailyCollectionCoverage.subjob == "RADAR",
                    DailyCollectionCoverage.observation_date == latest,
                    DailyCollectionCoverage.status == "COMPLETE",
                )
            )
        )
        return missing_coverage_tickers(covered) or UNIVERSE

    def _observation(
        self,
        ticker: str,
        item: Any,
        raw: RawVendorPayload,
        source_id: str,
        observation_date: date,
    ) -> OiChangeRadarObservation:
        assert self.pipeline.run
        eligibility = evaluate_radar_material_event(
            premium_usd=item.premium,
            oi_diff=item.delta_oi,
            previous_oi=item.previous_oi,
            profile=self.pipeline.profile,
        )
        archived = self.session.scalar(
            select(ContractOiDailySnapshot)
            .where(
                ContractOiDailySnapshot.ticker == ticker,
                ContractOiDailySnapshot.contract_symbol == item.symbol,
                ContractOiDailySnapshot.vendor_oi_date <= observation_date,
            )
            .order_by(desc(ContractOiDailySnapshot.vendor_oi_date))
            .limit(1)
        )
        expiry_archive = (
            self.session.scalar(
                select(ExpiryOiDailySnapshot).where(
                    ExpiryOiDailySnapshot.ticker == ticker,
                    ExpiryOiDailySnapshot.expiration == archived.expiration,
                    ExpiryOiDailySnapshot.vendor_oi_date == archived.vendor_oi_date,
                )
            )
            if archived
            else None
        )
        chain_complete = bool(expiry_archive and expiry_archive.chain_status == "COMPLETE")
        dte = calendar_dte(archived.expiration, observation_date) if archived else None
        scope = radar_scope(
            dte=dte,
            exact_match=archived is not None,
            chain_complete=chain_complete,
        )
        latest_structure = self.session.scalar(
            select(ContractScanObservation)
            .where(ContractScanObservation.contract_symbol == item.symbol)
            .order_by(desc(ContractScanObservation.observed_at))
            .limit(1)
        )
        history = (
            list(
                self.session.scalars(
                    select(ContractOiDailySnapshot)
                    .where(
                        ContractOiDailySnapshot.ticker == ticker,
                        ContractOiDailySnapshot.contract_symbol == item.symbol,
                    )
                    .order_by(ContractOiDailySnapshot.vendor_oi_date)
                )
            )
            if archived
            else []
        )
        persistence = contract_persistence(
            [OiHistoryPoint(row.vendor_oi_date, row.open_interest) for row in history],
            current_same_side_expiry_oi=None,
        )
        deep = eligibility.eligible and scope == "FULL_DEEP_DIVE_ELIGIBLE"
        return OiChangeRadarObservation(
            scan_run_id=None,
            daily_run_id=self.pipeline.run.id,
            ticker=ticker,
            contract_symbol=item.symbol,
            observation_date=observation_date,
            previous_date=item.previous_date,
            previous_oi=item.previous_oi,
            current_oi=item.current_oi,
            delta_oi=item.delta_oi,
            relative_oi_change=_decimal(item.relative_change),
            volume=item.volume,
            trades=item.trades,
            average_price=_decimal(item.average_price),
            premium=_decimal(item.premium),
            rank=item.rank,
            last_bid=_decimal(item.last_bid),
            last_ask=_decimal(item.last_ask),
            last_fill=_decimal(item.last_fill),
            raw_payload_id=raw.id,
            source_request_id=source_id,
            specification_version=SIGNAL_SPEC_VERSION,
            captured_at=utc_now(),
            ny_market_date=self.pipeline.run.ny_market_date,
            material_event_eligible=eligibility.eligible,
            radar_route_eligible=eligibility.eligible,
            eligibility_reason=eligibility.reason,
            threshold_profile_id=self.pipeline.profile.profile_id,
            threshold_profile_version=self.pipeline.profile.version,
            threshold_config_hash=self.pipeline.profile.configuration_hash,
            effective_thresholds=self.pipeline.profile.snapshot(),
            premium_per_trade=_per(item.premium, item.trades),
            volume_per_trade=_per(item.volume, item.trades),
            archive_match_status="EXACT" if archived else "UNAVAILABLE",
            matched_expiration=archived.expiration if archived else None,
            matched_dte=dte,
            matched_right=archived.right if archived else None,
            matched_strike=archived.strike if archived else None,
            archived_oi=archived.open_interest if archived else None,
            archive_vendor_oi_date=archived.vendor_oi_date if archived else None,
            archive_completeness=expiry_archive.chain_status if expiry_archive else "UNAVAILABLE",
            contract_structure_score=latest_structure.structure_score
            if latest_structure
            else None,
            contract_persistent_score=_decimal(persistence.score if persistence else None),
            radar_scope=scope,
            deep_dive_eligible=deep,
            trigger_sources=["RADAR_EVENT"] if eligibility.eligible else [],
            risk_flags=list(eligibility.risk_flags),
        )


def _archive_summary(summary: ArchiveSummary) -> dict[str, Any]:
    return {
        "status": summary.status,
        "tickers_attempted": summary.tickers_attempted,
        "tickers_skipped": summary.tickers_skipped,
        "rows_persisted": summary.contracts_persisted,
        "details": {
            "vendor_dates": summary.vendor_dates,
            "complete_chains": summary.complete_chains,
            "incomplete_chains": summary.incomplete_chains,
        },
    }


def _failed_subjob(error: Exception) -> dict[str, Any]:
    return {
        "status": "FAILED",
        "tickers_attempted": 0,
        "tickers_skipped": 0,
        "rows_persisted": 0,
        "details": {"safe_error": type(error).__name__},
    }


def _decimal(value: float | int | Decimal | None) -> Decimal | None:
    return Decimal(str(value)) if value is not None else None


def _per(numerator: float | int | None, denominator: int | None) -> Decimal | None:
    if numerator is None or denominator is None or denominator <= 0:
        return None
    return Decimal(str(numerator)) / Decimal(denominator)


def _float(value: Any) -> float | None:
    return float(value) if value is not None else None


def missing_coverage_tickers(covered: Iterable[str]) -> tuple[str, ...]:
    covered_set = set(covered)
    return tuple(ticker for ticker in UNIVERSE if ticker not in covered_set)


def daily_pipeline_status(statuses: Iterable[str]) -> str:
    values = list(statuses)
    if values and all(value in {"COMPLETE", "NO_NEW_DATA"} for value in values):
        return "COMPLETE"
    if values and all(value == "FAILED" for value in values):
        return "FAILED"
    return "PARTIAL"

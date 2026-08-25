from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import date, timedelta
from decimal import Decimal
from time import perf_counter
from typing import Any

from sqlalchemy import desc, select, text
from sqlalchemy.orm import Session

from app.core.time import market_date, utc_now
from app.db.models import (
    ApiUsageAudit,
    BucketPositioningSummary,
    CapabilitySnapshot,
    ContractScanObservation,
    ExpiryObservation,
    OiConfirmationEvent,
    RawVendorPayload,
    ScanRun,
    ScanStage,
    StrikeCluster,
    TickerScanResult,
)
from app.ingestion.raw import RawIngestor, parse_vendor_observed_at
from app.models.signals import DteBucket, bucket_for_dte, calendar_dte
from app.nightwatch.client import NightwatchClient
from app.nightwatch.errors import NightwatchError
from app.nightwatch.models import ApiUsageEvent, NightwatchResult
from app.persistence.api_usage import persist_api_usage
from app.scanner.clusters import ClusterContract, build_clusters
from app.scanner.config import LIMITS, SIGNAL_SPEC_VERSION, UNIVERSE, configuration_snapshot
from app.scanner.parsers import (
    ChainContract,
    intraday_metrics,
    object_rows,
    parse_chain,
    parse_expiry_aggregates,
)
from app.scanner.scoring import (
    ContractInput,
    expiry_type,
    final_expiry_score,
    neighbor_ratio,
    preliminary_expiry_score,
    robust_z_score,
    safe_ratio,
    score_contract,
    skew,
)
from app.scanner.selection import select_deep_expiries


class ConcurrentScanError(RuntimeError):
    pass


class BudgetExceeded(RuntimeError):
    pass


@dataclass(frozen=True)
class FetchResult:
    payload: Any
    raw: RawVendorPayload
    source_request_id: str
    cached: bool
    status_code: int = 200


@dataclass(frozen=True)
class ScanSummary:
    scan_run_id: uuid.UUID
    status: str
    tickers_scanned: int
    deep_tickers: int
    expirations_deep_scanned: int
    contracts_analyzed: int
    clusters_found: int
    consumed_quota_units: int
    network_attempts: int
    cache_hits: int
    fresh_requests: int
    elapsed_seconds: float


class BudgetTracker:
    def __init__(self, session: Session, scan_run_id: uuid.UUID) -> None:
        self.session = session
        self.scan_run_id = scan_run_id
        self.consumed = 0
        self.attempts = 0

    def ensure_room(self) -> None:
        if self.consumed >= LIMITS.max_consumed_units_per_scan:
            raise BudgetExceeded("consumed quota budget reached")
        if self.attempts >= LIMITS.max_network_attempts_per_scan:
            raise BudgetExceeded("network attempt budget reached")

    def would_exceed(self, *, attempts: int = 1, consumed: int = 1) -> bool:
        return (
            self.attempts + attempts > LIMITS.max_network_attempts_per_scan
            or self.consumed + consumed > LIMITS.max_consumed_units_per_scan
        )

    def observe(self, event: ApiUsageEvent) -> None:
        self.attempts += event.attempt_count
        if event.consumed_quota:
            self.consumed += 1
        row = persist_api_usage(self.session, event)
        row.scan_run_id = self.scan_run_id
        self.session.commit()


class Mag7Scanner:
    def __init__(self, session: Session, client: NightwatchClient) -> None:
        self.session = session
        self.client = client
        self.run: ScanRun | None = None
        self.budget: BudgetTracker | None = None
        self.cache_hits = 0
        self.fresh_requests = 0
        self.partial = False
        self.budget_limited = False
        self.data_pending = False

    async def execute(self, *, trigger: str = "cli") -> ScanSummary:
        started_clock = perf_counter()
        now = utc_now()
        market_day = market_date(now)
        if not bool(
            self.session.scalar(text("SELECT pg_try_advisory_lock(hashtext('mag7_phase2a_scan'))"))
        ):
            raise ConcurrentScanError("A MAG7 scan is already running")
        try:
            conflict = self.session.scalar(
                select(ScanRun).where(ScanRun.status == "RUNNING").limit(1)
            )
            if conflict:
                raise ConcurrentScanError("A scan run is already marked RUNNING")
            self.run = ScanRun(
                trigger=trigger,
                status="RUNNING",
                started_at=now,
                market_date=market_day,
                specification_version=SIGNAL_SPEC_VERSION,
                configuration_snapshot=configuration_snapshot(),
                summary={},
            )
            self.session.add(self.run)
            self.session.commit()
            self.budget = BudgetTracker(self.session, self.run.id)
            self.client._usage_observer = self.budget.observe  # scoped backend-only observer

            self._preflight(market_day)
            await self._confirm_pending_oi()
            ticker_rows, expiry_rows = await self._aggregate_scan(market_day)
            selected = self._select_deep(ticker_rows, expiry_rows)
            contracts, clusters = await self._deep_scan(selected, market_day)
            self._summarize(expiry_rows, contracts, clusters)

            status = completion_status(
                partial=self.partial,
                budget_limited=self.budget_limited,
                data_pending=self.data_pending and not expiry_rows,
            )
            summary = self._finish(
                status, ticker_rows, selected, contracts, clusters, started_clock
            )
            return summary
        except ConcurrentScanError:
            raise
        except Exception as exc:
            if self.run is not None:
                self.run.status = "FAILED"
                self.run.completed_at = utc_now()
                self.run.summary = {"safe_error": type(exc).__name__}
                self._sync_counters()
                self.session.commit()
            raise
        finally:
            self.session.execute(text("SELECT pg_advisory_unlock(hashtext('mag7_phase2a_scan'))"))
            self.session.commit()

    def _stage(self, name: str, status: str = "COMPLETE", **details: Any) -> None:
        assert self.run
        now = utc_now()
        self.session.add(
            ScanStage(
                scan_run_id=self.run.id,
                stage=name,
                status=status,
                started_at=now,
                completed_at=now,
                details=details,
            )
        )
        self.session.commit()

    def _preflight(self, market_day: date) -> None:
        self.session.execute(text("SELECT 1"))
        identifiers = set(
            self.session.scalars(
                select(CapabilitySnapshot.capability_identifier).where(
                    CapabilitySnapshot.available.is_(True)
                )
            )
        )
        required = {"options.volume_oi_per_expiry", "options.chain_snapshot"}
        missing = sorted(required - identifiers)
        if missing:
            raise RuntimeError(
                f"Required Nightwatch capabilities unavailable: {', '.join(missing)}"
            )
        # Dynamic presentation fields may advance; immutable detection tenor never changes.
        expiry_rows = list(self.session.scalars(select(ExpiryObservation)))
        for row in expiry_rows:
            row.current_dte = calendar_dte(row.expiration, market_day)
            current = bucket_for_dte(row.current_dte)
            row.current_bucket = current.value if current else None
        contract_rows = list(self.session.scalars(select(ContractScanObservation)))
        for row in contract_rows:
            row.current_dte = calendar_dte(row.expiration, market_day)
            current = bucket_for_dte(row.current_dte)
            row.current_bucket = current.value if current else None
        latest_usage = self.session.scalar(
            select(ApiUsageAudit).order_by(desc(ApiUsageAudit.requested_at)).limit(1)
        )
        if latest_usage and latest_usage.quota_remaining == 0:
            raise BudgetExceeded("Nightwatch monthly quota has no known remaining units")
        self.session.commit()
        self._stage(
            "S0_PREFLIGHT",
            market_date=market_day.isoformat(),
            capabilities_verified=sorted(required),
        )

    async def _confirm_pending_oi(self) -> None:
        pending = list(
            self.session.scalars(
                select(OiConfirmationEvent).where(OiConfirmationEvent.status == "PENDING")
            )
        )
        by_ticker: dict[str, list[OiConfirmationEvent]] = {}
        for event in pending:
            contract = self.session.get(ContractScanObservation, event.contract_observation_id)
            if contract:
                by_ticker.setdefault(contract.ticker, []).append(event)
        confirmed = 0
        for ticker, events in by_ticker.items():
            try:
                fetched = await self._fetch(
                    f"/v1/options/oi-change/{ticker}", ticker=ticker, command="options.oi_change"
                )
            except (NightwatchError, BudgetExceeded):
                self.partial = True
                continue
            changes = {}
            for item in object_rows(fetched.payload):
                symbol = (
                    item.get("contract_symbol") or item.get("option_symbol") or item.get("contract")
                )
                change = item.get("oi_change") or item.get("open_interest_change")
                if symbol and change is not None:
                    changes[str(symbol)] = float(change)
            for prior in events:
                contract = self.session.get(ContractScanObservation, prior.contract_observation_id)
                value = changes.get(contract.contract_symbol) if contract else None
                status = (
                    "INCONCLUSIVE"
                    if value is None
                    else "CONFIRMED"
                    if value > 0
                    else "NOT_CONFIRMED"
                )
                self.session.add(
                    OiConfirmationEvent(
                        scan_run_id=self.run.id,
                        contract_observation_id=prior.contract_observation_id,
                        status=status,
                        observed_at=utc_now(),
                        evidence={"oi_change": value},
                        source_request_ids=[fetched.source_request_id],
                        specification_version=SIGNAL_SPEC_VERSION,
                    )
                )
                confirmed += 1
        self.session.commit()
        self._stage("S1_OI_CONFIRMATION", pending_inspected=len(pending), events_recorded=confirmed)

    async def _aggregate_scan(
        self, market_day: date
    ) -> tuple[list[TickerScanResult], list[ExpiryObservation]]:
        ticker_results: list[TickerScanResult] = []
        all_expiries: list[ExpiryObservation] = []
        for ticker in UNIVERSE:
            try:
                fetched = await self._fetch(
                    f"/v1/options/volume-oi-per-expiry/{ticker}",
                    ticker=ticker,
                    command="options.volume_oi_per_expiry",
                )
            except BudgetExceeded:
                self.budget_limited = True
                break
            except NightwatchError:
                self.partial = True
                ticker_results.append(self._ticker_result(ticker, None, "UNAVAILABLE", [], []))
                continue
            aggregates = [
                row
                for row in parse_expiry_aggregates(fetched.payload)
                if 0 <= calendar_dte(row.expiration, market_day) <= 180
            ]
            if not aggregates:
                self.data_pending = self.data_pending or fetched.status_code == 202
                self.partial = self.partial or fetched.status_code != 202
                ticker_results.append(
                    self._ticker_result(
                        ticker, None, "UNPARSEABLE", [fetched.raw.id], [fetched.source_request_id]
                    )
                )
                continue
            total_volume = sum(row.total_volume for row in aggregates)
            total_oi = sum(row.total_oi for row in aggregates)
            typed = {
                row.expiration: expiry_type(row.expiration, row.expiration_type)
                for row in aggregates
            }
            ticker_expiries: list[ExpiryObservation] = []
            for aggregate in aggregates:
                dte = calendar_dte(aggregate.expiration, market_day)
                bucket = bucket_for_dte(dte)
                if bucket is None:
                    continue
                exp_type, type_source = typed[aggregate.expiration]
                peers = [
                    other.total_oi
                    for other in aggregates
                    if other.expiration != aggregate.expiration
                    and typed[other.expiration][0] == exp_type
                ]
                neighbor, baseline = neighbor_ratio(aggregate.total_oi, peers)
                volume_share = safe_ratio(aggregate.total_volume, total_volume)
                oi_share = safe_ratio(aggregate.total_oi, total_oi)
                volume_skew = skew(aggregate.call_volume, aggregate.put_volume)
                oi_skew = skew(aggregate.call_oi, aggregate.put_oi)
                prelim, basis, missing, components = preliminary_expiry_score(
                    volume_share, neighbor, volume_skew
                )
                row = ExpiryObservation(
                    scan_run_id=self.run.id,
                    ticker=ticker,
                    expiration=aggregate.expiration,
                    observed_at=utc_now(),
                    dte_at_detection=dte,
                    bucket_at_detection=bucket.value,
                    current_dte=dte,
                    current_bucket=bucket.value,
                    call_volume=aggregate.call_volume,
                    put_volume=aggregate.put_volume,
                    call_oi=aggregate.call_oi,
                    put_oi=aggregate.put_oi,
                    volume_share=_dec(volume_share),
                    oi_share=_dec(oi_share),
                    neighbor_ratio=_dec(neighbor),
                    volume_skew=_dec(volume_skew),
                    oi_skew=_dec(oi_skew),
                    expiration_type=exp_type,
                    expiration_type_source=type_source,
                    baseline_quality=baseline,
                    preliminary_score=_dec(prelim),
                    preliminary_basis=_dec(basis),
                    components={"preliminary": components, "missing": missing},
                    selected_for_deep_scan=False,
                    raw_payload_ids=[str(fetched.raw.id)],
                    source_request_ids=[fetched.source_request_id],
                    specification_version=SIGNAL_SPEC_VERSION,
                )
                self.session.add(row)
                ticker_expiries.append(row)
            self.session.flush()
            strongest = max(
                (
                    float(row.preliminary_score)
                    for row in ticker_expiries
                    if row.dte_at_detection <= 90
                ),
                default=0,
            )
            result = self._ticker_result(
                ticker, strongest, "COMPLETE", [fetched.raw.id], [fetched.source_request_id]
            )
            ticker_results.append(result)
            all_expiries.extend(ticker_expiries)
        self.session.commit()
        self._stage(
            "S2_S3_AGGREGATE_AND_PRELIMINARY",
            tickers=len(ticker_results),
            expiries=len(all_expiries),
        )
        return ticker_results, all_expiries

    def _ticker_result(
        self,
        ticker: str,
        score: float | None,
        completeness: str,
        raw_ids: list[Any],
        request_ids: list[str],
    ) -> TickerScanResult:
        row = TickerScanResult(
            scan_run_id=self.run.id,
            ticker=ticker,
            observed_at=utc_now(),
            preliminary_score=_dec(score),
            selected_for_deep_scan=False,
            data_completeness=completeness,
            raw_payload_ids=[str(value) for value in raw_ids],
            source_request_ids=request_ids,
            specification_version=SIGNAL_SPEC_VERSION,
        )
        self.session.add(row)
        return row

    def _select_deep(
        self, tickers: list[TickerScanResult], expiries: list[ExpiryObservation]
    ) -> list[ExpiryObservation]:
        selected = select_deep_expiries(expiries)
        selected_tickers = {row.ticker for row in selected}
        for ticker_row in tickers:
            ticker_row.selected_for_deep_scan = ticker_row.ticker in selected_tickers
        for winner in selected:
            winner.selected_for_deep_scan = True
        self.session.commit()
        self._stage(
            "S4_SELECTION", deep_tickers=len(selected_tickers), selected_expiries=len(selected)
        )
        return selected

    async def _deep_scan(
        self, selected: list[ExpiryObservation], market_day: date
    ) -> tuple[list[ContractScanObservation], list[StrikeCluster]]:
        contracts: list[ContractScanObservation] = []
        chain_contracts: dict[uuid.UUID, list[ChainContract]] = {}
        for expiry in selected:
            try:
                fetched = await self._fetch(
                    f"/v1/options/chain-snapshot/{expiry.ticker}",
                    params={"expiration": expiry.expiration.isoformat()},
                    ticker=expiry.ticker,
                    expiration=expiry.expiration,
                    command="options.chain_snapshot",
                )
            except BudgetExceeded:
                self.budget_limited = True
                break
            except NightwatchError:
                self.partial = True
                continue
            normalized = parse_chain(fetched.payload, expiry.expiration)
            chain_contracts[expiry.id] = normalized
            expiry.raw_payload_ids = [*expiry.raw_payload_ids, str(fetched.raw.id)]
            expiry.source_request_ids = [*expiry.source_request_ids, fetched.source_request_id]
            for item in normalized:
                row = self._contract_row(expiry, fetched, item, market_day)
                self.session.add(row)
                contracts.append(row)
            self.session.flush()
        self.session.commit()
        self._stage("S5_CHAIN_AND_CONTRACT_SCORE", contracts=len(contracts))

        priority = sorted(
            (
                row
                for row in contracts
                if row.hard_reject_reason is None and float(row.anomaly_score) >= 50
            ),
            key=lambda row: (float(row.anomaly_score), float(row.estimated_premium or 0)),
            reverse=True,
        )[: LIMITS.max_intraday_contracts]
        for row in priority:
            if self.budget_limited:
                break
            try:
                fetched = await self._fetch(
                    f"/v1/options/contract-intraday/{row.contract_symbol}",
                    ticker=row.ticker,
                    expiration=row.expiration,
                    command="options.contract_intraday",
                )
            except BudgetExceeded:
                self.budget_limited = True
                break
            except NightwatchError:
                self.partial = True
                continue
            burst, vwap = intraday_metrics(fetched.payload)
            row.intraday_burst_ratio = _dec(burst)
            if vwap is not None:
                row.estimated_premium = _dec(row.volume * 100 * vwap)
                row.premium_quality = "INTRADAY_VWAP_ESTIMATE"
            rescored = score_contract(
                ContractInput(
                    volume=row.volume,
                    previous_oi=row.previous_oi,
                    estimated_premium=float(row.estimated_premium)
                    if row.estimated_premium is not None
                    else None,
                    spread_pct=float(row.spread_pct) if row.spread_pct is not None else None,
                    delta=float(row.delta) if row.delta is not None else None,
                    burst_ratio=burst,
                    dte=row.dte_at_detection,
                    quote_supplied=row.bid is not None or row.ask is not None,
                )
            )
            self._apply_score(row, rescored)
            row.source_request_ids = [*row.source_request_ids, fetched.source_request_id]
        self.session.commit()
        self._stage(
            "S6_INTRADAY_DRILLDOWN",
            contracts_requested=min(len(priority), LIMITS.max_intraday_contracts),
        )

        clusters: list[StrikeCluster] = []
        ticker_premium_totals = {
            ticker: sum(
                float(row.estimated_premium or 0)
                for row in contracts
                if row.ticker == ticker
            )
            for ticker in UNIVERSE
        }
        for expiry in selected:
            expiry_contracts = [row for row in contracts if row.expiry_observation_id == expiry.id]
            call_premium = (
                sum(
                    float(row.estimated_premium or 0)
                    for row in expiry_contracts
                    if row.right == "C"
                )
                or None
            )
            put_premium = (
                sum(
                    float(row.estimated_premium or 0)
                    for row in expiry_contracts
                    if row.right == "P"
                )
                or None
            )
            premium_total = (call_premium or 0) + (put_premium or 0)
            premium_skew = (
                ((call_premium or 0) - (put_premium or 0)) / premium_total
                if premium_total
                else None
            )
            expiry_premium = (call_premium or 0) + (put_premium or 0)
            premium_share = safe_ratio(expiry_premium, ticker_premium_totals[expiry.ticker])
            final, basis, missing, components = final_expiry_score(
                oi_share=float(expiry.oi_share) if expiry.oi_share is not None else None,
                neighbor=float(expiry.neighbor_ratio)
                if expiry.neighbor_ratio is not None
                else None,
                volume_share=float(expiry.volume_share)
                if expiry.volume_share is not None
                else None,
                skews=(
                    float(expiry.oi_skew) if expiry.oi_skew is not None else None,
                    float(expiry.volume_skew) if expiry.volume_skew is not None else None,
                    premium_skew,
                ),
                premium_share=premium_share,
            )
            expiry.expiry_score = _dec(final)
            expiry.expiry_score_basis = _dec(basis)
            expiry.classification = (
                "STRONG_EXPIRY_CANDIDATE"
                if final >= 80
                else "EXPIRY_CANDIDATE"
                if final >= 65
                else "NOT_CANDIDATE"
            )
            expiry.components = {
                **expiry.components,
                "final": components,
                "final_missing": missing,
                "premium_skew": premium_skew,
            }
            for right, side_premium in (("C", call_premium), ("P", put_premium)):
                side = [row for row in expiry_contracts if row.right == right]
                candidates = [row for row in side if row.is_candidate]
                cluster_inputs = [
                    ClusterContract(
                        id=str(row.id),
                        strike=row.strike,
                        volume=row.volume,
                        previous_oi=row.previous_oi,
                        premium=float(row.estimated_premium)
                        if row.estimated_premium is not None
                        else None,
                        score=float(row.anomaly_score),
                        liquidity_points=float(row.components.get("liquidity_quality"))
                        if "liquidity_quality" in row.components
                        else None,
                        spot=row.spot,
                    )
                    for row in candidates
                ]
                results = build_clusters(
                    candidates=cluster_inputs,
                    full_strike_ladder=[row.strike for row in side],
                    side_volume=sum(row.volume for row in side),
                    side_premium=side_premium,
                )
                for result in results:
                    source_rows = [
                        row
                        for row in candidates
                        if str(row.id) in {item.id for item in result.contracts}
                    ]
                    cluster = StrikeCluster(
                        scan_run_id=self.run.id,
                        expiry_observation_id=expiry.id,
                        ticker=expiry.ticker,
                        expiration=expiry.expiration,
                        right=right,
                        min_strike=min(item.strike for item in result.contracts),
                        max_strike=max(item.strike for item in result.contracts),
                        contract_count=len(result.contracts),
                        total_volume=sum(item.volume for item in result.contracts),
                        total_estimated_premium=_dec(
                            sum(item.premium or 0 for item in result.contracts)
                        )
                        if all(item.premium is not None for item in result.contracts)
                        else None,
                        total_oi=sum(item.previous_oi for item in result.contracts),
                        premium_share=_dec(result.premium_share),
                        volume_share=_dec(result.volume_share),
                        premium_weighted_strike=result.positioning_center,
                        cluster_score=_dec(result.score),
                        score_basis_weight=_dec(result.basis),
                        classification=result.classification,
                        shape=result.shape,
                        source_contract_ids=[str(row.id) for row in source_rows],
                        components=result.components,
                        specification_version=SIGNAL_SPEC_VERSION,
                    )
                    self.session.add(cluster)
                    clusters.append(cluster)
        self.session.commit()
        self._stage("S7_FINAL_EXPIRY_AND_CLUSTERS", clusters=len(clusters))
        return contracts, clusters

    def _contract_row(
        self, expiry: ExpiryObservation, fetched: FetchResult, item: ChainContract, market_day: date
    ) -> ContractScanObservation:
        mid = (
            (item.bid + item.ask) / 2
            if item.bid is not None
            and item.ask is not None
            and item.bid >= 0
            and item.ask >= item.bid
            else None
        )
        spread = (
            (item.ask - item.bid) / mid
            if mid and item.ask is not None and item.bid is not None
            else None
        )
        if item.vendor_premium is not None:
            premium, quality = item.vendor_premium, "VENDOR_AGGREGATE_ESTIMATE"
        elif item.last is not None and item.last > 0:
            premium, quality = item.volume * 100 * float(item.last), "LAST_PRICE_ESTIMATE"
        elif mid is not None and mid > 0:
            premium, quality = item.volume * 100 * float(mid), "MIDPOINT_ESTIMATE"
        else:
            premium, quality = None, None
        history = self._historical_volumes(item.symbol)
        historical_z = robust_z_score(item.volume, history)
        scored = score_contract(
            ContractInput(
                volume=item.volume,
                previous_oi=item.previous_oi,
                estimated_premium=premium,
                spread_pct=float(spread) if spread is not None else None,
                delta=item.delta,
                robust_z=historical_z,
                history_count=len(history),
                dte=expiry.dte_at_detection,
                quote_supplied=item.bid is not None or item.ask is not None,
            )
        )
        row = ContractScanObservation(
            scan_run_id=self.run.id,
            expiry_observation_id=expiry.id,
            raw_payload_id=fetched.raw.id,
            contract_symbol=item.symbol,
            ticker=expiry.ticker,
            expiration=item.expiration,
            right=item.right,
            strike=item.strike,
            observed_at=item.observed_at or utc_now(),
            dte_at_detection=expiry.dte_at_detection,
            bucket_at_detection=expiry.bucket_at_detection,
            current_dte=calendar_dte(item.expiration, market_day),
            current_bucket=expiry.current_bucket,
            volume=item.volume,
            previous_oi=item.previous_oi,
            volume_oi_ratio=_dec(item.volume / max(item.previous_oi, 1)),
            bid=item.bid,
            ask=item.ask,
            mid=mid,
            spread_pct=spread,
            last=item.last,
            delta=_dec(item.delta),
            spot=item.spot,
            estimated_premium=_dec(premium),
            premium_quality=quality,
            historical_robust_z=_dec(historical_z),
            anomaly_score=_dec(scored.score),
            score_basis_weight=_dec(scored.basis),
            classification=scored.classification,
            is_candidate=scored.candidate,
            hard_reject_reason=scored.hard_reject,
            risk_flags=list(scored.flags),
            components=scored.components,
            source_request_ids=[fetched.source_request_id],
            specification_version=SIGNAL_SPEC_VERSION,
        )
        return row

    def _historical_volumes(self, symbol: str) -> list[int]:
        return list(
            self.session.scalars(
                select(ContractScanObservation.volume)
                .where(ContractScanObservation.contract_symbol == symbol)
                .order_by(desc(ContractScanObservation.observed_at))
                .limit(50)
            )
        )

    @staticmethod
    def _apply_score(row: ContractScanObservation, scored: Any) -> None:
        row.anomaly_score = _dec(scored.score)
        row.score_basis_weight = _dec(scored.basis)
        row.classification = scored.classification
        row.is_candidate = scored.candidate
        row.hard_reject_reason = scored.hard_reject
        row.risk_flags = list(scored.flags)
        row.components = scored.components

    def _summarize(
        self,
        expiries: list[ExpiryObservation],
        contracts: list[ContractScanObservation],
        clusters: list[StrikeCluster],
    ) -> None:
        for ticker in UNIVERSE:
            for bucket in (DteBucket.VERY_SHORT, DteBucket.SHORT, DteBucket.MEDIUM, DteBucket.LONG):
                bucket_expiries = [
                    row
                    for row in expiries
                    if row.ticker == ticker and row.bucket_at_detection == bucket.value
                ]
                if not bucket_expiries:
                    continue
                strongest_expiry = max(
                    bucket_expiries,
                    key=lambda row: float(row.expiry_score or row.preliminary_score),
                )
                bucket_contracts = [
                    row
                    for row in contracts
                    if row.ticker == ticker and row.bucket_at_detection == bucket.value
                ]
                bucket_clusters = [
                    row
                    for row in clusters
                    if row.ticker == ticker
                    and any(exp.id == row.expiry_observation_id for exp in bucket_expiries)
                ]
                call_contract = max(
                    (row for row in bucket_contracts if row.right == "C"),
                    key=lambda row: float(row.anomaly_score),
                    default=None,
                )
                put_contract = max(
                    (row for row in bucket_contracts if row.right == "P"),
                    key=lambda row: float(row.anomaly_score),
                    default=None,
                )
                call_cluster = max(
                    (row for row in bucket_clusters if row.right == "C"),
                    key=lambda row: float(row.cluster_score),
                    default=None,
                )
                put_cluster = max(
                    (row for row in bucket_clusters if row.right == "P"),
                    key=lambda row: float(row.cluster_score),
                    default=None,
                )
                valid_call = call_cluster is not None and call_cluster.classification in {
                    "VALID_CLUSTER",
                    "STRONG_CLUSTER",
                }
                valid_put = put_cluster is not None and put_cluster.classification in {
                    "VALID_CLUSTER",
                    "STRONG_CLUSTER",
                }
                label = (
                    "TWO_SIDED"
                    if valid_call and valid_put
                    else "CALL_DOMINANT"
                    if valid_call
                    else "PUT_DOMINANT"
                    if valid_put
                    else "NO_STRONG_STRUCTURE"
                )
                expiry_candidate = strongest_expiry.classification in {
                    "EXPIRY_CANDIDATE",
                    "STRONG_EXPIRY_CANDIDATE",
                }
                provisional = (
                    "PROVISIONAL_POSITIONING_CANDIDATE"
                    if (valid_call or valid_put) and expiry_candidate
                    else None
                )
                self.session.add(
                    BucketPositioningSummary(
                        scan_run_id=self.run.id,
                        ticker=ticker,
                        bucket=bucket.value,
                        observed_at=utc_now(),
                        strongest_expiry_id=strongest_expiry.id,
                        strongest_call_contract_id=call_contract.id if call_contract else None,
                        strongest_put_contract_id=put_contract.id if put_contract else None,
                        strongest_call_cluster_id=call_cluster.id if call_cluster else None,
                        strongest_put_cluster_id=put_cluster.id if put_cluster else None,
                        positioning_label=label,
                        day_zero_status=provisional,
                        oi_status="PENDING" if provisional else "INCONCLUSIVE",
                        data_completeness="COMPLETE"
                        if bucket_contracts or bucket == DteBucket.LONG
                        else "AGGREGATE_ONLY",
                        metrics={
                            "volume_skew": float(strongest_expiry.volume_skew)
                            if strongest_expiry.volume_skew is not None
                            else None,
                            "oi_skew": float(strongest_expiry.oi_skew)
                            if strongest_expiry.oi_skew is not None
                            else None,
                        },
                        specification_version=SIGNAL_SPEC_VERSION,
                    )
                )
                for candidate in (
                    row for row in bucket_contracts if row.is_candidate and provisional
                ):
                    self.session.add(
                        OiConfirmationEvent(
                            scan_run_id=self.run.id,
                            contract_observation_id=candidate.id,
                            status="PENDING",
                            observed_at=utc_now(),
                            evidence={"day_zero": True},
                            source_request_ids=candidate.source_request_ids,
                            specification_version=SIGNAL_SPEC_VERSION,
                        )
                    )
        self.session.commit()
        self._stage("S8_POSITIONING_SUMMARY")

    async def _fetch(
        self,
        path: str,
        *,
        params: dict[str, str] | None = None,
        ticker: str | None = None,
        expiration: date | None = None,
        command: str,
    ) -> FetchResult:
        assert self.run and self.budget
        signature = cache_signature(path, params)
        cutoff = utc_now() - timedelta(minutes=LIMITS.cache_cooldown_minutes)
        cached = self.session.scalar(
            select(RawVendorPayload)
            .where(
                RawVendorPayload.source == "nightwatch",
                RawVendorPayload.endpoint == signature,
                RawVendorPayload.received_at >= cutoff,
            )
            .order_by(desc(RawVendorPayload.received_at))
            .limit(1)
        )
        if cached:
            self.cache_hits += 1
            return FetchResult(
                cached.payload, cached, cached.vendor_request_id or cached.request_id, True
            )
        self.budget.ensure_room()
        result: NightwatchResult = await self.client.request(
            "GET",
            path,
            params=params,
            command=command,
            ticker=ticker,
            expiration=expiration.isoformat() if expiration else None,
        )
        source_request_id = result.vendor_request_id or result.request_id
        raw = RawIngestor(self.session).persist(
            endpoint=signature,
            request_id=source_request_id,
            vendor_request_id=result.vendor_request_id,
            payload=result.payload,
            ticker=ticker,
            expiration=expiration,
            vendor_observed_at=parse_vendor_observed_at(result.payload),
            scan_run_id=self.run.id,
        )
        self.session.commit()
        self.fresh_requests += 1
        return FetchResult(result.payload, raw, source_request_id, False, result.status_code)

    def _sync_counters(self) -> None:
        if self.run and self.budget:
            self.run.consumed_quota_units = self.budget.consumed
            self.run.network_attempts = self.budget.attempts
            self.run.cache_hits = self.cache_hits
            self.run.fresh_requests = self.fresh_requests

    def _finish(
        self,
        status: str,
        tickers: list[TickerScanResult],
        selected: list[ExpiryObservation],
        contracts: list[ContractScanObservation],
        clusters: list[StrikeCluster],
        started_clock: float,
    ) -> ScanSummary:
        assert self.run and self.budget
        self.run.status = status
        self.run.completed_at = utc_now()
        self._sync_counters()
        deep_tickers = len({row.ticker for row in selected})
        elapsed = round(perf_counter() - started_clock, 3)
        self.run.summary = {
            "tickers_scanned": len(tickers),
            "deep_tickers": deep_tickers,
            "expirations_deep_scanned": len(selected),
            "contracts_analyzed": len(contracts),
            "clusters_found": len(clusters),
            "elapsed_seconds": elapsed,
        }
        self.session.commit()
        return ScanSummary(
            self.run.id,
            status,
            len(tickers),
            deep_tickers,
            len(selected),
            len(contracts),
            len(clusters),
            self.budget.consumed,
            self.budget.attempts,
            self.cache_hits,
            self.fresh_requests,
            elapsed,
        )


def _dec(value: float | int | Decimal | None) -> Decimal | None:
    return Decimal(str(round(float(value), 8))) if value is not None else None




def completion_status(*, partial: bool, budget_limited: bool, data_pending: bool) -> str:
    if budget_limited:
        return "PARTIAL_BUDGET_LIMIT"
    if data_pending:
        return "DATA_PENDING"
    return "PARTIAL" if partial else "COMPLETE"


def cache_signature(path: str, params: dict[str, str] | None = None) -> str:
    return path + (
        "?" + "&".join(f"{key}={params[key]}" for key in sorted(params))
        if params
        else ""
    )

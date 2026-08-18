from __future__ import annotations

import statistics
from datetime import date
from decimal import Decimal
from time import perf_counter
from typing import Any

from sqlalchemy import func, select, text

from app.core.time import market_date, utc_now
from app.db.models import (
    BucketPositioningSummary,
    CapabilitySnapshot,
    ContractOiDailySnapshot,
    ContractScanObservation,
    ExpiryObservation,
    ExpiryOiDailySnapshot,
    OiChangeRadarObservation,
    ScanRun,
    StrikeCluster,
    TickerScanResult,
)
from app.models.signals import DteBucket, bucket_for_dte, calendar_dte
from app.nightwatch.errors import NightwatchError
from app.scanner.candidate_persistence import materialize_successful_scan_candidates
from app.scanner.clusters import PositioningClusterContract, build_positioning_clusters
from app.scanner.config import LIMITS, SIGNAL_SPEC_VERSION, UNIVERSE, configuration_snapshot
from app.scanner.history import OiHistoryPoint, contract_persistence, expiry_persistence
from app.scanner.parsers import (
    parse_expiry_aggregates,
    parse_oi_change_radar,
    parse_ticker_activity,
)
from app.scanner.scoring import (
    contract_structure_score,
    expiry_type,
    neighbor_ratio,
    safe_ratio,
    same_day_activity_score,
    skew,
)
from app.scanner.selection import select_dual_discovery
from app.scanner.service import (
    BudgetExceeded,
    BudgetTracker,
    ConcurrentScanError,
    ScanSummary,
    completion_status,
)
from app.scanner.service import Mag7Scanner as LegacyMag7Scanner


class Mag7Scanner(LegacyMag7Scanner):
    """Runtime-aligned Phase 2A v1.1 interactive scan.

    Same-day endpoints are refreshed independently. Contract structure is computed only from the
    latest complete daily archive; the interactive scan never rebuilds the 0–180 DTE archive.
    """

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
            self.client._usage_observer = self.budget.observe
            self._preflight_v11(market_day)
            ticker_rows, expiry_rows = await self._activity_surface(market_day)
            selected = self._select_dual(ticker_rows, expiry_rows)
            contracts, clusters, radar_matches = await self._structure_scan(selected, market_day)
            self._summarize_v11(expiry_rows, contracts, clusters)
            status = completion_status(
                partial=self.partial,
                budget_limited=self.budget_limited,
                data_pending=self.data_pending and not expiry_rows,
            )
            return self._finish_v11(
                status, ticker_rows, selected, contracts, clusters, radar_matches, started_clock
            )
        except ConcurrentScanError:
            raise
        except Exception as error:
            if self.run:
                self.session.rollback()
                self.run.status = "FAILED"
                self.run.completed_at = utc_now()
                self.run.summary = {"safe_error": type(error).__name__}
                self._sync_counters()
                self.session.commit()
            raise
        finally:
            self.session.execute(text("SELECT pg_advisory_unlock(hashtext('mag7_phase2a_scan'))"))
            self.session.commit()

    def _preflight_v11(self, market_day: date) -> None:
        self.session.execute(text("SELECT 1"))
        identifiers = set(
            self.session.scalars(
                select(CapabilitySnapshot.capability_identifier).where(
                    CapabilitySnapshot.available.is_(True)
                )
            )
        )
        required = {
            "options.expiry_breakdown",
            "options.options_volume",
            "options.oi_per_expiry",
            "options.chain_snapshot",
        }
        missing = sorted(required - identifiers)
        if missing:
            raise RuntimeError(
                f"Required Nightwatch capabilities unavailable: {', '.join(missing)}"
            )
        self._stage(
            "S0_PREFLIGHT_V11",
            market_date=market_day.isoformat(),
            capabilities_verified=sorted(required),
        )

    async def _activity_surface(
        self, market_day: date
    ) -> tuple[list[TickerScanResult], list[ExpiryObservation]]:
        ticker_results: list[TickerScanResult] = []
        all_expiries: list[ExpiryObservation] = []
        for ticker in UNIVERSE:
            try:
                activity_fetch = await self._fetch(
                    f"/v1/options/expiry-breakdown/{ticker}",
                    ticker=ticker,
                    command="options.expiry_breakdown",
                )
                context_fetch = await self._fetch(
                    f"/v1/options/options-volume/{ticker}",
                    ticker=ticker,
                    command="options.options_volume",
                )
            except BudgetExceeded:
                self.budget_limited = True
                break
            except NightwatchError:
                self.partial = True
                ticker_results.append(self._ticker_result_v11(ticker, None, "UNAVAILABLE", {}))
                continue
            aggregates = [
                row
                for row in parse_expiry_aggregates(activity_fetch.payload)
                if 0 <= calendar_dte(row.expiration, market_day) <= 180
            ]
            if not aggregates:
                self.partial = True
                ticker_results.append(self._ticker_result_v11(ticker, None, "UNPARSEABLE", {}))
                continue
            context = parse_ticker_activity(context_fetch.payload)
            activity_context = {
                "vendor_date": context.vendor_date.isoformat() if context.vendor_date else None,
                "vendor_as_of": context.vendor_as_of.isoformat() if context.vendor_as_of else None,
                "call_volume": context.call_volume,
                "put_volume": context.put_volume,
                "call_oi": context.call_oi,
                "put_oi": context.put_oi,
                "ticker_volume_skew": skew(context.call_volume, context.put_volume),
                "premium_context": context.premiums,
                "scope": "TICKER_DAY_ONLY",
            }
            latest_vendor_date = self.session.scalar(
                select(func.max(ExpiryOiDailySnapshot.vendor_oi_date)).where(
                    ExpiryOiDailySnapshot.ticker == ticker
                )
            )
            latest_snapshots = (
                {
                    row.expiration: row
                    for row in self.session.scalars(
                        select(ExpiryOiDailySnapshot).where(
                            ExpiryOiDailySnapshot.ticker == ticker,
                            ExpiryOiDailySnapshot.vendor_oi_date == latest_vendor_date,
                        )
                    )
                }
                if latest_vendor_date
                else {}
            )
            total_volume = sum(row.total_volume for row in aggregates)
            typed = {row.expiration: expiry_type(row.expiration) for row in aggregates}
            ticker_expiries: list[ExpiryObservation] = []
            for aggregate in aggregates:
                dte = calendar_dte(aggregate.expiration, market_day)
                bucket = bucket_for_dte(dte)
                if bucket is None:
                    continue
                peers = [
                    row.total_volume
                    for row in aggregates
                    if row.expiration != aggregate.expiration
                    and typed[row.expiration][0] == typed[aggregate.expiration][0]
                ]
                volume_neighbor, baseline = neighbor_ratio(aggregate.total_volume, peers)
                volume_share = safe_ratio(aggregate.total_volume, total_volume)
                same_day = same_day_activity_score(volume_share, volume_neighbor)
                archived = latest_snapshots.get(aggregate.expiration)
                persistence = self._expiry_history(ticker, aggregate.expiration)
                persistent_score = persistence.score if persistence else None
                same_qualifies = same_day.score >= LIMITS.same_day_eligibility_score
                persistent_qualifies = (
                    persistent_score is not None
                    and persistent_score >= LIMITS.persistent_eligibility_score
                )
                source = (
                    "BOTH"
                    if same_qualifies and persistent_qualifies
                    else "SAME_DAY"
                    if same_qualifies
                    else "PERSISTENT"
                    if persistent_qualifies
                    else None
                )
                oi_share = (
                    float(archived.total_oi_share)
                    if archived and archived.total_oi_share is not None
                    else None
                )
                cold = persistence.observation_count < 3 if persistence else True
                cold_eligible = (
                    cold
                    and oi_share is not None
                    and oi_share >= LIMITS.structural_cold_start_oi_share
                )
                discovery_values = [same_day.score]
                if persistent_score is not None:
                    discovery_values.append(persistent_score)
                discovery_score = max(discovery_values)
                exp_type, type_source = typed[aggregate.expiration]
                row = ExpiryObservation(
                    scan_run_id=self.run.id,
                    ticker=ticker,
                    expiration=aggregate.expiration,
                    observed_at=utc_now(),
                    dte_at_detection=dte,
                    bucket_at_detection=bucket.value,
                    current_dte=dte,
                    current_bucket=bucket.value,
                    call_volume=None,
                    put_volume=None,
                    call_oi=archived.call_oi if archived else None,
                    put_oi=archived.put_oi if archived else None,
                    volume_share=_dec(volume_share),
                    oi_share=_dec(oi_share),
                    neighbor_ratio=_dec(volume_neighbor),
                    volume_skew=None,
                    oi_skew=_dec(skew(archived.call_oi, archived.put_oi)) if archived else None,
                    expiration_type=exp_type,
                    expiration_type_source=type_source,
                    baseline_quality=baseline,
                    preliminary_score=_dec(same_day.score),
                    preliminary_basis=_dec(same_day.basis),
                    expiry_score=_dec(discovery_score),
                    expiry_score_basis=_dec(100),
                    classification="DISCOVERY_ELIGIBLE" if source or cold_eligible else "OBSERVE",
                    selected_for_deep_scan=False,
                    components={"same_day": same_day.components},
                    raw_payload_ids=[str(activity_fetch.raw.id), str(context_fetch.raw.id)],
                    source_request_ids=[
                        activity_fetch.source_request_id,
                        context_fetch.source_request_id,
                    ],
                    specification_version=SIGNAL_SPEC_VERSION,
                    vendor_oi_date=latest_vendor_date,
                    call_oi_share=archived.call_oi_share if archived else None,
                    put_oi_share=archived.put_oi_share if archived else None,
                    same_day_activity_score=_dec(same_day.score),
                    same_day_score_basis_weight=_dec(same_day.basis),
                    same_day_data_coverage=_dec(same_day.basis),
                    missing_same_day_components=list(same_day.missing),
                    persistent_positioning_score=_dec(persistent_score),
                    persistent_state=persistence.state if persistence else None,
                    persistent_winning_window=persistence.winning_window if persistence else None,
                    history_confidence=persistence.history_confidence
                    if persistence
                    else "INSUFFICIENT",
                    persistent_components=persistence.features if persistence else {"windows": {}},
                    discovery_score=_dec(discovery_score),
                    discovery_source=source,
                    structural_cold_start_eligible=cold_eligible,
                )
                self.session.add(row)
                ticker_expiries.append(row)
            self.session.flush()
            strongest = max(
                (
                    float(row.discovery_score or 0)
                    for row in ticker_expiries
                    if row.dte_at_detection <= 90
                ),
                default=0,
            )
            ticker_result = self._ticker_result_v11(ticker, strongest, "COMPLETE", activity_context)
            ticker_result.raw_payload_ids = [str(activity_fetch.raw.id), str(context_fetch.raw.id)]
            ticker_result.source_request_ids = [
                activity_fetch.source_request_id,
                context_fetch.source_request_id,
            ]
            ticker_results.append(ticker_result)
            all_expiries.extend(ticker_expiries)
            self.session.commit()
        self._stage("S2_ACTIVITY_SURFACE", tickers=len(ticker_results), expiries=len(all_expiries))
        self._stage("S3_DUAL_DISCOVERY", persistent_source="DAILY_OI_ARCHIVE")
        return ticker_results, all_expiries

    def _ticker_result_v11(
        self, ticker: str, score: float | None, completeness: str, context: dict[str, Any]
    ) -> TickerScanResult:
        row = TickerScanResult(
            scan_run_id=self.run.id,
            ticker=ticker,
            observed_at=utc_now(),
            preliminary_score=_dec(score),
            selected_for_deep_scan=False,
            data_completeness=completeness,
            raw_payload_ids=[],
            source_request_ids=[],
            specification_version=SIGNAL_SPEC_VERSION,
            activity_context=context,
        )
        self.session.add(row)
        return row

    def _expiry_history(self, ticker: str, expiration: date):
        rows = list(
            self.session.scalars(
                select(ExpiryOiDailySnapshot)
                .where(
                    ExpiryOiDailySnapshot.ticker == ticker,
                    ExpiryOiDailySnapshot.expiration == expiration,
                )
                .order_by(ExpiryOiDailySnapshot.vendor_oi_date)
            )
        )
        return expiry_persistence(
            [
                OiHistoryPoint(
                    row.vendor_oi_date,
                    row.total_oi,
                    float(row.total_oi_share) if row.total_oi_share is not None else None,
                    float(row.call_oi_share) if row.call_oi_share is not None else None,
                    float(row.put_oi_share) if row.put_oi_share is not None else None,
                )
                for row in rows
            ]
        )

    def _select_dual(
        self, tickers: list[TickerScanResult], expiries: list[ExpiryObservation]
    ) -> list[ExpiryObservation]:
        selected = select_dual_discovery(expiries)
        chosen_tickers = sorted({row.ticker for row in selected})
        for row in selected:
            row.selected_for_deep_scan = True
        for row in tickers:
            row.selected_for_deep_scan = row.ticker in chosen_tickers
        self.session.commit()
        self._stage(
            "S4_DUAL_SELECTION", deep_tickers=len(chosen_tickers), selected_expiries=len(selected)
        )
        return selected

    async def _structure_scan(
        self,
        selected: list[ExpiryObservation],
        market_day: date,
    ) -> tuple[list[ContractScanObservation], list[StrikeCluster], int]:
        contracts: list[ContractScanObservation] = []
        clusters: list[StrikeCluster] = []
        for expiry in selected:
            archived_expiry = self.session.scalar(
                select(ExpiryOiDailySnapshot).where(
                    ExpiryOiDailySnapshot.ticker == expiry.ticker,
                    ExpiryOiDailySnapshot.expiration == expiry.expiration,
                    ExpiryOiDailySnapshot.vendor_oi_date == expiry.vendor_oi_date,
                    ExpiryOiDailySnapshot.chain_status == "COMPLETE",
                )
            )
            if archived_expiry is None:
                self.partial = True
                continue
            if expiry.vendor_oi_date is None:
                # Contract Persistence and archive-derived DTE require an authoritative
                # vendor evidence date.  Missing is not replaced with the scan date.
                self.partial = True
                continue
            archived = list(
                self.session.scalars(
                    select(ContractOiDailySnapshot).where(
                        ContractOiDailySnapshot.ticker == expiry.ticker,
                        ContractOiDailySnapshot.expiration == expiry.expiration,
                        ContractOiDailySnapshot.vendor_oi_date == expiry.vendor_oi_date,
                    )
                )
            )
            history_pool = list(
                self.session.scalars(
                    select(ContractOiDailySnapshot)
                    .where(
                        ContractOiDailySnapshot.ticker == expiry.ticker,
                        ContractOiDailySnapshot.contract_symbol.in_(
                            [row.contract_symbol for row in archived]
                        ),
                        ContractOiDailySnapshot.vendor_oi_date <= expiry.vendor_oi_date,
                    )
                    .order_by(
                        ContractOiDailySnapshot.contract_symbol,
                        ContractOiDailySnapshot.vendor_oi_date,
                    )
                )
            )
            history_by_symbol = group_contract_histories(history_pool)
            by_right = {
                right: [row for row in archived if row.right == right] for right in ("C", "P")
            }
            current_rows: list[ContractScanObservation] = []
            for right, side in by_right.items():
                side_total = sum(row.open_interest for row in side)
                ordered = sorted(side, key=lambda row: row.strike)
                for index, item in enumerate(ordered):
                    neighbors = [
                        row.open_interest
                        for position, row in enumerate(ordered)
                        if position != index and abs(position - index) <= 2
                    ]
                    neighbor_value = statistics.median(neighbors) if neighbors else None
                    neighbor_ratio_value = (
                        item.open_interest / neighbor_value
                        if neighbor_value and neighbor_value > 0
                        else None
                    )
                    mid = (
                        (item.bid + item.ask) / 2
                        if item.bid is not None and item.ask is not None and item.ask >= item.bid
                        else None
                    )
                    spread = (
                        (item.ask - item.bid) / mid
                        if mid and item.bid is not None and item.ask is not None
                        else None
                    )
                    oi_share = safe_ratio(item.open_interest, side_total)
                    scored = contract_structure_score(
                        oi_share=oi_share,
                        neighbor_ratio=neighbor_ratio_value,
                        spread_pct=float(spread) if spread is not None else None,
                        delta=float(item.delta) if item.delta is not None else None,
                        quote_supplied=item.bid is not None or item.ask is not None,
                    )
                    history_rows = history_by_symbol.get(item.contract_symbol, [])
                    persistent = contract_persistence(
                        [
                            OiHistoryPoint(row.vendor_oi_date, row.open_interest)
                            for row in history_rows
                        ],
                        current_same_side_expiry_oi=side_total,
                        analysis_date=expiry.vendor_oi_date,
                    )
                    prior_oi = history_rows[-2].open_interest if len(history_rows) >= 2 else None
                    detection_dte = calendar_dte(item.expiration, item.vendor_oi_date)
                    detection_bucket = bucket_for_dte(detection_dte)
                    current_dte = calendar_dte(item.expiration, market_day)
                    current_bucket = bucket_for_dte(current_dte)
                    quote_availability = (
                        "AVAILABLE"
                        if item.bid is not None and item.ask is not None and item.ask >= item.bid
                        else "PARTIAL"
                        if item.bid is not None or item.ask is not None
                        else "UNAVAILABLE"
                    )
                    row = ContractScanObservation(
                        scan_run_id=self.run.id,
                        expiry_observation_id=expiry.id,
                        raw_payload_id=item.raw_payload_id,
                        contract_symbol=item.contract_symbol,
                        ticker=item.ticker,
                        expiration=item.expiration,
                        right=right,
                        strike=item.strike,
                        observed_at=utc_now(),
                        dte_at_detection=detection_dte,
                        bucket_at_detection=(
                            detection_bucket.value
                            if detection_bucket is not None
                            else expiry.bucket_at_detection
                        ),
                        current_dte=current_dte,
                        current_bucket=current_bucket.value if current_bucket is not None else None,
                        volume=None,
                        previous_oi=prior_oi,
                        volume_oi_ratio=None,
                        bid=item.bid,
                        ask=item.ask,
                        mid=mid,
                        spread_pct=_dec(spread),
                        last=None,
                        delta=item.delta,
                        spot=item.underlying_price,
                        estimated_premium=None,
                        premium_quality=None,
                        historical_robust_z=None,
                        intraday_burst_ratio=None,
                        anomaly_score=None,
                        score_basis_weight=_dec(scored.basis),
                        classification=scored.classification,
                        is_candidate=scored.candidate,
                        hard_reject_reason=scored.hard_reject,
                        risk_flags=list(scored.flags),
                        components={
                            "dte_identity": {
                                "anchor_date": item.vendor_oi_date.isoformat(),
                                "anchor_type": "VENDOR_OI_DATE",
                            },
                            "quote": {
                                "availability": quote_availability,
                                "quote_as_of": item.quote_as_of.isoformat()
                                if item.quote_as_of
                                else None,
                                "source": "COMPLETE_DAILY_CHAIN_ARCHIVE",
                            },
                        },
                        source_request_ids=[item.source_request_id],
                        specification_version=SIGNAL_SPEC_VERSION,
                        current_oi=item.open_interest,
                        contract_oi_share=_dec(oi_share),
                        neighbor_strike_ratio=_dec(neighbor_ratio_value),
                        structure_score=_dec(scored.score),
                        structure_components=scored.components,
                        persistent_positioning_score=_dec(persistent.score),
                        persistent_state=persistent.state,
                        persistent_winning_window=persistent.winning_window,
                        history_observation_count=persistent.observation_count,
                        history_confidence=persistent.history_confidence,
                        persistent_components=persistent.features,
                        oi_change_radar_status="NOT_OBSERVED",
                        oi_change_radar_evidence=None,
                    )
                    self.session.add(row)
                    contracts.append(row)
                    current_rows.append(row)
            self.session.flush()
            for right in ("C", "P"):
                side_rows = [row for row in current_rows if row.right == right]
                side_total = sum(row.current_oi or 0 for row in side_rows)
                inputs = [
                    PositioningClusterContract(
                        id=str(row.id),
                        strike=row.strike,
                        open_interest=row.current_oi or 0,
                        structure_score=float(row.structure_score or 0),
                        liquidity_points=(row.structure_components or {}).get("liquidity_quality"),
                        spot=row.spot,
                        persistent_score=float(row.persistent_positioning_score)
                        if row.persistent_positioning_score is not None
                        else None,
                        persistent_state=row.persistent_state,
                        net_oi_changes={
                            window: details.get("net_oi_change")
                            for window, details in (row.persistent_components or {})
                            .get("windows", {})
                            .items()
                        },
                    )
                    for row in side_rows
                    if row.is_candidate
                ]
                for result in build_positioning_clusters(
                    candidates=inputs,
                    full_strike_ladder=[row.strike for row in side_rows],
                    same_side_expiry_oi=side_total,
                ):
                    cluster = StrikeCluster(
                        scan_run_id=self.run.id,
                        expiry_observation_id=expiry.id,
                        ticker=expiry.ticker,
                        expiration=expiry.expiration,
                        right=right,
                        min_strike=min(row.strike for row in result.contracts),
                        max_strike=max(row.strike for row in result.contracts),
                        contract_count=len(result.contracts),
                        total_volume=None,
                        total_estimated_premium=None,
                        total_oi=sum(row.open_interest for row in result.contracts),
                        premium_share=None,
                        volume_share=None,
                        premium_weighted_strike=None,
                        cluster_score=_dec(result.score),
                        score_basis_weight=_dec(100),
                        classification=result.classification,
                        shape=result.shape,
                        source_contract_ids=[row.id for row in result.contracts],
                        components=result.components,
                        specification_version=SIGNAL_SPEC_VERSION,
                        cluster_oi_share=_dec(result.oi_share),
                        positioning_center=result.positioning_center,
                        persistent_build_count=result.persistent_build_count,
                        persistent_decline_count=result.persistent_decline_count,
                        oi_weighted_persistent_score=_dec(result.oi_weighted_persistent_score),
                        cluster_net_oi_changes=result.net_oi_changes,
                    )
                    self.session.add(cluster)
                    clusters.append(cluster)
            self.session.commit()
        radar_matches = await self._radar(selected, contracts)
        self._stage(
            "S5_STRUCTURE_AND_RADAR",
            contracts=len(contracts),
            clusters=len(clusters),
            radar_matches=radar_matches,
        )
        return contracts, clusters, radar_matches

    async def _radar(
        self, selected: list[ExpiryObservation], contracts: list[ContractScanObservation]
    ) -> int:
        matches = 0
        for ticker in sorted({row.ticker for row in selected}):
            try:
                fetched = await self._fetch(
                    f"/v1/options/oi-change/{ticker}",
                    ticker=ticker,
                    command="options.oi_change.radar",
                )
            except (BudgetExceeded, NightwatchError):
                self.partial = True
                continue
            parsed = parse_oi_change_radar(fetched.payload)
            by_symbol = {row.symbol: row for row in parsed}
            for item in parsed:
                self.session.add(
                    OiChangeRadarObservation(
                        scan_run_id=self.run.id,
                        ticker=ticker,
                        contract_symbol=item.symbol,
                        observation_date=item.observation_date,
                        previous_date=item.previous_date,
                        previous_oi=item.previous_oi,
                        current_oi=item.current_oi,
                        delta_oi=item.delta_oi,
                        relative_oi_change=_dec(item.relative_change),
                        volume=item.volume,
                        trades=item.trades,
                        average_price=_dec(item.average_price),
                        premium=_dec(item.premium),
                        rank=item.rank,
                        last_bid=_dec(item.last_bid),
                        last_ask=_dec(item.last_ask),
                        last_fill=_dec(item.last_fill),
                        raw_payload_id=fetched.raw.id,
                        source_request_id=fetched.source_request_id,
                        specification_version=SIGNAL_SPEC_VERSION,
                    )
                )
            for contract in (row for row in contracts if row.ticker == ticker):
                radar = by_symbol.get(contract.contract_symbol)
                if radar:
                    contract.oi_change_radar_status = "OBSERVED"
                    contract.oi_change_radar_evidence = {
                        "delta_oi": radar.delta_oi,
                        "premium": radar.premium,
                        "rank": radar.rank,
                        "observation_date": radar.observation_date.isoformat()
                        if radar.observation_date
                        else None,
                    }
                    matches += 1
            self.session.commit()
        return matches

    def _summarize_v11(
        self,
        expiries: list[ExpiryObservation],
        contracts: list[ContractScanObservation],
        clusters: list[StrikeCluster],
    ) -> None:
        for ticker in UNIVERSE:
            for bucket in DteBucket:
                bucket_expiries = [
                    row
                    for row in expiries
                    if row.ticker == ticker and row.bucket_at_detection == bucket.value
                ]
                if not bucket_expiries:
                    continue
                strongest = max(bucket_expiries, key=lambda row: float(row.discovery_score or 0))
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
                    key=lambda row: float(row.structure_score or 0),
                    default=None,
                )
                put_contract = max(
                    (row for row in bucket_contracts if row.right == "P"),
                    key=lambda row: float(row.structure_score or 0),
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
                    else "CALL_STRUCTURE"
                    if valid_call
                    else "PUT_STRUCTURE"
                    if valid_put
                    else "NO_STRONG_STRUCTURE"
                )
                self.session.add(
                    BucketPositioningSummary(
                        scan_run_id=self.run.id,
                        ticker=ticker,
                        bucket=bucket.value,
                        observed_at=utc_now(),
                        strongest_expiry_id=strongest.id,
                        strongest_call_contract_id=call_contract.id if call_contract else None,
                        strongest_put_contract_id=put_contract.id if put_contract else None,
                        strongest_call_cluster_id=call_cluster.id if call_cluster else None,
                        strongest_put_cluster_id=put_cluster.id if put_cluster else None,
                        positioning_label=label,
                        day_zero_status=None,
                        oi_status=strongest.history_confidence or "INSUFFICIENT",
                        data_completeness="COMPLETE_ARCHIVE_REUSED"
                        if bucket_contracts
                        else "ACTIVITY_ONLY",
                        metrics={
                            "oi_skew": float(strongest.oi_skew)
                            if strongest.oi_skew is not None
                            else None,
                            "discovery_source": strongest.discovery_source,
                            "structural_cold_start_eligible": (
                                strongest.structural_cold_start_eligible
                            ),
                        },
                        specification_version=SIGNAL_SPEC_VERSION,
                    )
                )
        self.session.commit()
        self._stage("S6_POSITIONING_SUMMARY")

    def _finish_v11(
        self,
        status: str,
        tickers: list[TickerScanResult],
        selected: list[ExpiryObservation],
        contracts: list[ContractScanObservation],
        clusters: list[StrikeCluster],
        radar_matches: int,
        started_clock: float,
    ) -> ScanSummary:
        assert self.run and self.budget
        self.run.status = status
        self.run.completed_at = utc_now()
        self._sync_counters()
        elapsed = round(perf_counter() - started_clock, 3)
        deep_tickers = len({row.ticker for row in selected})
        self.run.summary = {
            "tickers_scanned": len(tickers),
            "deep_tickers": deep_tickers,
            "expirations_deep_scanned": len(selected),
            "contracts_analyzed": len(contracts),
            "structural_contract_candidates": sum(row.is_candidate for row in contracts),
            "clusters_found": len(clusters),
            "oi_change_radar_matches": radar_matches,
            "daily_archive_requests": 0,
            "intraday_requests": 0,
            "elapsed_seconds": elapsed,
        }
        if status == "COMPLETE":
            materialize_successful_scan_candidates(
                self.session,
                self.run,
                materialized_at=self.run.completed_at,
            )
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


def group_contract_histories(
    rows: list[ContractOiDailySnapshot],
) -> dict[str, list[ContractOiDailySnapshot]]:
    grouped: dict[str, list[ContractOiDailySnapshot]] = {}
    for row in rows:
        grouped.setdefault(row.contract_symbol, []).append(row)
    return grouped

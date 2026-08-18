from __future__ import annotations

from datetime import date
from typing import Any

from sqlalchemy import desc, func, select

from app.core.time import utc_now
from app.db.models import (
    BucketPositioningSummary,
    ContractScanObservation,
    ExpiryObservation,
    ExpiryOiDailySnapshot,
    StrikeCluster,
    TickerScanResult,
    ZeroDteActivitySessionSnapshot,
)
from app.models.signals import DteBucket, bucket_for_dte, calendar_dte
from app.nightwatch.errors import NightwatchError
from app.scanner.config import LIMITS, SIGNAL_SPEC_VERSION, UNIVERSE
from app.scanner.daily_semantics import ZeroDteSnapshotKind
from app.scanner.history import PersistenceResult
from app.scanner.parsers import ExpiryAggregate, parse_expiry_aggregates, parse_ticker_activity
from app.scanner.scoring import (
    ComparableExpiry,
    comparable_nonzero_expiry_peers,
    discovery_with_confirmation,
    expiry_type,
    neighbor_ratio,
    safe_ratio,
    same_day_activity_score,
    skew,
    zero_dte_activity_score,
)
from app.scanner.service import BudgetExceeded
from app.scanner.v11 import Mag7Scanner as V11Mag7Scanner
from app.scanner.v11 import _dec


class Mag7Scanner(V11Mag7Scanner):
    """Phase 2A v1.2 activity calibration; v1.1 persistence economics stay unchanged."""

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

            context = parse_ticker_activity(context_fetch.payload)
            # expiry-breakdown has no verified usable activity date; New York market date is the
            # authoritative current-session date. options-volume's date remains ticker context.
            activity_date = market_day
            aggregates = [
                row
                for row in parse_expiry_aggregates(activity_fetch.payload)
                if 0 <= calendar_dte(row.expiration, activity_date) <= 180
            ]
            if not aggregates:
                self.partial = True
                ticker_results.append(self._ticker_result_v11(ticker, None, "UNPARSEABLE", {}))
                continue
            activity_context = {
                "vendor_date": context.vendor_date.isoformat()
                if context.vendor_date
                else None,
                "activity_observation_date": activity_date.isoformat(),
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
            comparable = [
                ComparableExpiry(
                    calendar_dte(row.expiration, activity_date),
                    row.total_volume,
                    row.expiration_type.upper() if row.expiration_type else None,
                )
                for row in aggregates
            ]
            typed = {
                row.expiration: expiry_type(row.expiration, row.expiration_type)
                for row in aggregates
            }
            ticker_expiries: list[ExpiryObservation] = []
            zero_dte_snapshot: tuple[ExpiryAggregate, float, float | None, int] | None = None
            for index, aggregate in enumerate(aggregates):
                dte = calendar_dte(aggregate.expiration, activity_date)
                bucket = bucket_for_dte(dte)
                if bucket is None:
                    continue
                volume_share = safe_ratio(aggregate.total_volume, total_volume)
                raw_neighbor, _raw_quality = self._raw_neighbor(
                    aggregate, aggregates, typed
                )
                persistence = self._expiry_history(ticker, aggregate.expiration)
                archived = latest_snapshots.get(aggregate.expiration)
                if dte == 0:
                    history = self._zero_dte_history(ticker, activity_date)
                    calibrated = zero_dte_activity_score(
                        volume_share,
                        history,
                        required_observations=LIMITS.zero_dte_baseline_observations,
                        mad_epsilon=LIMITS.zero_dte_mad_epsilon,
                    )
                    same_day_score = calibrated.score
                    same_day_basis = calibrated.basis
                    same_day_components = calibrated.components
                    missing = calibrated.missing
                    peer_count = 0
                    peer_dtes: list[int] = []
                    peer_quality = "ZERO_DTE_DESCRIPTIVE_ONLY"
                    peer_median = None
                    baseline_status = calibrated.status
                    baseline_count = calibrated.observation_count
                    baseline_mean = calibrated.mean
                    baseline_median = calibrated.median
                    baseline_mad = calibrated.mad
                    percentile = calibrated.percentile
                    robust_deviation = calibrated.robust_deviation
                    baseline_method = calibrated.method
                    scoring_neighbor_ratio = None
                    if volume_share is not None:
                        zero_dte_snapshot = (
                            aggregate,
                            volume_share,
                            raw_neighbor,
                            total_volume,
                        )
                else:
                    peers = comparable_nonzero_expiry_peers(
                        comparable[index],
                        comparable,
                        max_peers=LIMITS.comparable_peer_max_count,
                        min_peers=LIMITS.comparable_peer_min_count,
                    )
                    current = same_day_activity_score(volume_share, peers.ratio)
                    same_day_score = current.score
                    same_day_basis = current.basis
                    same_day_components = current.components
                    missing = current.missing
                    peer_count = peers.count
                    peer_dtes = list(peers.dtes)
                    peer_quality = peers.quality
                    peer_median = peers.median_volume
                    baseline_status = "CURRENT_SESSION_NONZERO_DTE"
                    baseline_count = None
                    baseline_mean = baseline_median = baseline_mad = None
                    percentile = robust_deviation = None
                    baseline_method = "COMPARABLE_NONZERO_DTE_PEERS"
                    scoring_neighbor_ratio = peers.ratio

                persistent_score = persistence.score if persistence else None
                oi_share = (
                    float(archived.total_oi_share)
                    if archived and archived.total_oi_share is not None
                    else None
                )
                cold = persistence.observation_count < 3 if persistence else True
                cold_eligible = bool(
                    cold
                    and oi_share is not None
                    and oi_share >= LIMITS.structural_cold_start_oi_share
                )
                discovery = discovery_with_confirmation(same_day_score, persistent_score)
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
                    oi_share=archived.total_oi_share if archived else None,
                    neighbor_ratio=_dec(scoring_neighbor_ratio),
                    volume_skew=None,
                    oi_skew=_dec(skew(archived.call_oi, archived.put_oi)) if archived else None,
                    expiration_type=exp_type,
                    expiration_type_source=type_source,
                    baseline_quality=peer_quality,
                    preliminary_score=_dec(same_day_score),
                    preliminary_basis=_dec(same_day_basis),
                    expiry_score=_dec(discovery.score),
                    expiry_score_basis=_dec(100) if discovery.score is not None else None,
                    classification="DISCOVERY_ELIGIBLE"
                    if self._eligible(same_day_score, persistent_score, cold_eligible)
                    else "OBSERVE",
                    selected_for_deep_scan=False,
                    components={
                        "same_day": same_day_components,
                        "dte_identity": {
                            "anchor_date": activity_date.isoformat(),
                            "anchor_type": "NY_MARKET_SESSION_DATE",
                        },
                        "comparable_neighbor_ratio_used_by_score": scoring_neighbor_ratio,
                        "raw_cross_expiry_neighbor_ratio_descriptive_only": raw_neighbor,
                    },
                    raw_payload_ids=[str(activity_fetch.raw.id), str(context_fetch.raw.id)],
                    source_request_ids=[
                        activity_fetch.source_request_id,
                        context_fetch.source_request_id,
                    ],
                    specification_version=SIGNAL_SPEC_VERSION,
                    vendor_oi_date=latest_vendor_date,
                    call_oi_share=archived.call_oi_share if archived else None,
                    put_oi_share=archived.put_oi_share if archived else None,
                    same_day_activity_score=_dec(same_day_score),
                    same_day_score_basis_weight=_dec(same_day_basis),
                    same_day_data_coverage=_dec(same_day_basis),
                    missing_same_day_components=list(missing),
                    persistent_positioning_score=_dec(persistent_score),
                    persistent_state=persistence.state if persistence else None,
                    persistent_winning_window=persistence.winning_window if persistence else None,
                    history_confidence=self._history_confidence(persistence),
                    persistent_components=persistence.features if persistence else {"windows": {}},
                    discovery_score=_dec(discovery.score),
                    discovery_source=discovery.source,
                    structural_cold_start_eligible=cold_eligible,
                    current_expiry_volume=aggregate.total_volume,
                    same_day_baseline_status=baseline_status,
                    baseline_observation_count=baseline_count,
                    baseline_20_mean_volume_share=_dec(baseline_mean),
                    baseline_20_median_volume_share=_dec(baseline_median),
                    baseline_20_mad_volume_share=_dec(baseline_mad),
                    historical_percentile_20=_dec(percentile),
                    robust_deviation=_dec(robust_deviation),
                    zero_dte_baseline_method=baseline_method,
                    comparable_peer_count=peer_count,
                    comparable_peer_dtes=peer_dtes,
                    comparable_peer_quality=peer_quality,
                    comparable_peer_median_volume=_dec(peer_median),
                    discovery_primary_score=_dec(discovery.primary),
                    discovery_secondary_score=_dec(discovery.secondary),
                    discovery_confirmation_bonus=_dec(discovery.confirmation_bonus),
                    discovery_evidence_breadth=discovery.evidence_breadth,
                )
                self.session.add(row)
                ticker_expiries.append(row)
            self.session.flush()
            if zero_dte_snapshot:
                self._persist_zero_dte_snapshot(
                    ticker,
                    activity_date,
                    zero_dte_snapshot,
                    activity_fetch.raw.id,
                    activity_fetch.source_request_id,
                )
            strongest = max(
                (
                    float(row.discovery_score)
                    for row in ticker_expiries
                    if row.dte_at_detection <= 90 and row.discovery_score is not None
                ),
                default=None,
            )
            ticker_result = self._ticker_result_v11(
                ticker, strongest, "COMPLETE", activity_context
            )
            ticker_result.raw_payload_ids = [str(activity_fetch.raw.id), str(context_fetch.raw.id)]
            ticker_result.source_request_ids = [
                activity_fetch.source_request_id,
                context_fetch.source_request_id,
            ]
            ticker_results.append(ticker_result)
            all_expiries.extend(ticker_expiries)
            self.session.commit()
        self._stage(
            "S2_ACTIVITY_SURFACE_V12",
            tickers=len(ticker_results),
            expiries=len(all_expiries),
        )
        self._stage("S3_DISCOVERY_CONFIRMATION", zero_dte_baseline_sessions=20)
        return ticker_results, all_expiries

    @staticmethod
    def _eligible(
        same_day: float | None, persistent: float | None, cold_eligible: bool
    ) -> bool:
        return bool(
            (same_day is not None and same_day >= LIMITS.same_day_eligibility_score)
            or (
                persistent is not None
                and persistent >= LIMITS.persistent_eligibility_score
            )
            or cold_eligible
        )

    @staticmethod
    def _history_confidence(persistence: PersistenceResult | None) -> str:
        return persistence.history_confidence if persistence else "INSUFFICIENT"

    def _zero_dte_history(self, ticker: str, observation_date: date) -> list[float]:
        rows = list(
            self.session.scalars(
                select(ZeroDteActivitySessionSnapshot)
                .where(
                    ZeroDteActivitySessionSnapshot.ticker == ticker,
                    ZeroDteActivitySessionSnapshot.snapshot_kind
                    == ZeroDteSnapshotKind.CANONICAL_SESSION_COMPLETE.value,
                    ZeroDteActivitySessionSnapshot.observation_date < observation_date,
                )
                .order_by(desc(ZeroDteActivitySessionSnapshot.observation_date))
                .limit(LIMITS.zero_dte_baseline_observations)
            )
        )
        return [float(row.volume_share) for row in reversed(rows)]

    def _persist_zero_dte_snapshot(
        self,
        ticker: str,
        observation_date: date,
        values: tuple[ExpiryAggregate, float, float | None, int],
        raw_payload_id: Any,
        source_request_id: str,
    ) -> None:
        existing = self.session.scalar(
            select(ZeroDteActivitySessionSnapshot.id).where(
                ZeroDteActivitySessionSnapshot.ticker == ticker,
                ZeroDteActivitySessionSnapshot.observation_date == observation_date,
                ZeroDteActivitySessionSnapshot.snapshot_kind
                == ZeroDteSnapshotKind.PROVISIONAL_INTRADAY.value,
            )
        )
        if existing is not None:
            return
        aggregate, share, raw_neighbor, ticker_scope_volume = values
        self.session.add(
            ZeroDteActivitySessionSnapshot(
                scan_run_id=self.run.id,
                daily_run_id=None,
                ticker=ticker,
                observation_date=observation_date,
                expiration=aggregate.expiration,
                snapshot_kind=ZeroDteSnapshotKind.PROVISIONAL_INTRADAY.value,
                captured_at=utc_now(),
                session_close_at=None,
                expiry_volume=aggregate.total_volume,
                ticker_scope_volume=ticker_scope_volume,
                volume_share=_dec(share),
                raw_cross_expiry_neighbor_ratio=_dec(raw_neighbor),
                raw_payload_id=raw_payload_id,
                source_request_id=source_request_id,
                specification_version=SIGNAL_SPEC_VERSION,
            )
        )

    def _summarize_v11(
        self,
        expiries: list[ExpiryObservation],
        contracts: list[ContractScanObservation],
        clusters: list[StrikeCluster],
    ) -> None:
        """Persist summaries only for a ranked normal winner; cold-only stays separate."""

        for ticker in UNIVERSE:
            for bucket in DteBucket:
                eligible = [
                    row
                    for row in expiries
                    if row.ticker == ticker
                    and row.bucket_at_detection == bucket.value
                    and row.discovery_score is not None
                    and self._eligible(
                        float(row.same_day_activity_score)
                        if row.same_day_activity_score is not None
                        else None,
                        float(row.persistent_positioning_score)
                        if row.persistent_positioning_score is not None
                        else None,
                        False,
                    )
                ]
                if not eligible:
                    continue
                strongest = max(eligible, key=lambda row: float(row.discovery_score))
                bucket_contracts = [
                    row
                    for row in contracts
                    if row.ticker == ticker and row.bucket_at_detection == bucket.value
                ]
                bucket_clusters = [
                    row
                    for row in clusters
                    if row.ticker == ticker
                    and any(exp.id == row.expiry_observation_id for exp in eligible)
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
                        positioning_label=self._cluster_label(call_cluster, put_cluster),
                        day_zero_status=None,
                        oi_status=strongest.history_confidence or "INSUFFICIENT",
                        data_completeness="COMPLETE_ARCHIVE_REUSED"
                        if bucket_contracts
                        else "ACTIVITY_ONLY",
                        metrics={
                            "discovery_source": strongest.discovery_source,
                            "discovery_evidence_breadth": (
                                strongest.discovery_evidence_breadth
                            ),
                        },
                        specification_version=SIGNAL_SPEC_VERSION,
                    )
                )
        self.session.commit()
        self._stage("S6_POSITIONING_SUMMARY_V12")

    @staticmethod
    def _cluster_label(
        call_cluster: StrikeCluster | None, put_cluster: StrikeCluster | None
    ) -> str:
        valid_call = bool(
            call_cluster
            and call_cluster.classification in {"VALID_CLUSTER", "STRONG_CLUSTER"}
        )
        valid_put = bool(
            put_cluster
            and put_cluster.classification in {"VALID_CLUSTER", "STRONG_CLUSTER"}
        )
        if valid_call and valid_put:
            return "TWO_SIDED"
        if valid_call:
            return "CALL_STRUCTURE"
        if valid_put:
            return "PUT_STRUCTURE"
        return "NO_STRONG_STRUCTURE"

    @staticmethod
    def _raw_neighbor(
        aggregate: ExpiryAggregate,
        aggregates: list[ExpiryAggregate],
        typed: dict[date, tuple[str, str]],
    ) -> tuple[float | None, str]:
        peers = [
            row.total_volume
            for row in aggregates
            if row.expiration != aggregate.expiration
            and typed[row.expiration][0] == typed[aggregate.expiration][0]
        ]
        return neighbor_ratio(aggregate.total_volume, peers)

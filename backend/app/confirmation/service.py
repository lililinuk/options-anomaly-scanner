from __future__ import annotations

import uuid
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from decimal import Decimal
from typing import Any

from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from app.confirmation.config import (
    PHASE2B_SPEC_VERSION,
    Phase2bContextConfig,
    active_phase2b_config,
)
from app.confirmation.domain import (
    calculate_price_context,
    evaluate_heatmap,
    map_term_structure,
    normalize_heatmap_payload,
    normalize_stock_state,
    strike_location,
)
from app.confirmation.provenance import (
    EvaluationIdentity,
    aggregate_freshness_anchor_at,
    aggregate_source_first_received_at,
    earliest_known,
    source_time_entry,
    unavailable_source_time_entry,
)
from app.confirmation.state_v2 import latest_v2_state
from app.confirmation.workspace_v3 import latest_v3_workspace
from app.core.time import utc_now
from app.db.models import (
    ContractOiDailySnapshot,
    ContractScanObservation,
    ExpiryObservation,
    OiChangeRadarObservation,
    Phase2bCandidateEvaluation,
    Phase2bTickerContextSnapshot,
    RawVendorPayload,
    StrikeCluster,
)
from app.ingestion.raw import RawIngestor, parse_vendor_observed_at
from app.nightwatch.client import NightwatchClient
from app.nightwatch.errors import NightwatchError


@dataclass(frozen=True)
class CandidateSource:
    contract_symbol: str
    ticker: str
    expiration: date
    right: str
    strike: Decimal
    dte_at_detection: int | None
    radar_observation_id: uuid.UUID | None = None
    source_first_received_at: datetime | None = None


@dataclass(frozen=True)
class Phase2bRunSummary:
    evaluations: tuple[str, ...]
    ticker_snapshots_created: int
    ticker_snapshots_reused: int
    ticker_snapshots_reprocessed: int = 0


class Phase2bContextService:
    """Fetch shared ticker context only after explicit Phase 2A candidate selection."""

    ENDPOINTS = (
        ("daily_ohlc", "/v1/stocks/ohlc/{ticker}", {"candle_size": "1d"}),
        ("stock_state", "/v1/stocks/stock-state/{ticker}", {}),
        ("iv_rank", "/v1/volatility/iv-rank/{ticker}", {}),
        ("term_structure", "/v1/volatility/term-structure/{ticker}", {}),
        ("dealer_heatmap", "/v1/derived/heatmap/{ticker}/snapshot", {"format": "full"}),
    )

    def __init__(
        self, session: Session, client: NightwatchClient,
        config: Phase2bContextConfig | None = None,
    ) -> None:
        self.session = session
        self.client = client
        self.config = config or active_phase2b_config()

    async def refresh_contracts(
        self, contract_symbols: Sequence[str], *, force: bool = False,
        reuse_latest_raw: bool = False,
    ) -> Phase2bRunSummary:
        candidates = [
            candidate
            for symbol in dict.fromkeys(contract_symbols)
            if (candidate := self._candidate_source(symbol)) is not None
        ]
        if not candidates:
            return Phase2bRunSummary((), 0, 0, 0)
        grouped: dict[str, list[CandidateSource]] = {}
        for candidate in candidates:
            grouped.setdefault(candidate.ticker, []).append(candidate)
        evaluations: list[str] = []
        created = reused = reprocessed = 0
        for ticker, ticker_candidates in grouped.items():
            context = None if force else self._fresh_context(ticker)
            was_reprocessed = False
            if context is None and reuse_latest_raw:
                previous = self._latest_context(ticker)
                context = self._reprocess_ticker_context(previous) if previous else None
                was_reprocessed = context is not None
                reprocessed += int(was_reprocessed)
            if context is None:
                context = await self._fetch_ticker_context(ticker)
                created += 1
            elif not was_reprocessed:
                reused += 1
            for candidate in ticker_candidates:
                evaluation = self._evaluation(context, candidate)
                evaluations.append(str(evaluation.id))
        self.session.commit()
        return Phase2bRunSummary(tuple(evaluations), created, reused, reprocessed)

    def _candidate_source(self, symbol: str) -> CandidateSource | None:
        radar = self.session.scalar(
            select(OiChangeRadarObservation)
            .where(
                OiChangeRadarObservation.contract_symbol == symbol,
                OiChangeRadarObservation.deep_dive_eligible.is_(True),
            )
            .order_by(desc(OiChangeRadarObservation.observation_date))
            .limit(1)
        )
        chain = self.session.scalar(
            select(ContractOiDailySnapshot)
            .where(ContractOiDailySnapshot.contract_symbol == symbol)
            .order_by(desc(ContractOiDailySnapshot.vendor_oi_date))
            .limit(1)
        )
        if radar is None or chain is None:
            return None
        source_first_received_at = earliest_known(
            *[
                raw.received_at
                for raw_id in (radar.raw_payload_id, chain.raw_payload_id)
                if (raw := self.session.get(RawVendorPayload, raw_id)) is not None
            ]
        )
        return CandidateSource(
            contract_symbol=symbol, ticker=chain.ticker, expiration=chain.expiration,
            right=chain.right, strike=chain.strike, dte_at_detection=radar.matched_dte,
            radar_observation_id=radar.id,
            source_first_received_at=source_first_received_at,
        )

    def _fresh_context(self, ticker: str) -> Phase2bTickerContextSnapshot | None:
        cutoff = utc_now() - timedelta(minutes=self.config.cache_freshness_minutes)
        return self.session.scalar(
            select(Phase2bTickerContextSnapshot)
            .where(
                Phase2bTickerContextSnapshot.ticker == ticker,
                Phase2bTickerContextSnapshot.specification_version == PHASE2B_SPEC_VERSION,
                Phase2bTickerContextSnapshot.config_version == self.config.version,
                Phase2bTickerContextSnapshot.config_hash == self.config.configuration_hash,
                Phase2bTickerContextSnapshot.freshness_anchor_at >= cutoff,
            )
            .order_by(desc(Phase2bTickerContextSnapshot.freshness_anchor_at))
            .limit(1)
        )

    def _latest_context(self, ticker: str) -> Phase2bTickerContextSnapshot | None:
        return self.session.scalar(
            select(Phase2bTickerContextSnapshot)
            .where(Phase2bTickerContextSnapshot.ticker == ticker)
            .order_by(desc(Phase2bTickerContextSnapshot.created_at))
            .limit(1)
        )

    def _reprocess_ticker_context(
        self, source: Phase2bTickerContextSnapshot
    ) -> Phase2bTickerContextSnapshot | None:
        """Append current normalization from preserved raw OHLC without a vendor request."""

        ohlc_payload: dict[str, Any] | None = None
        raw_rows: list[RawVendorPayload] = []
        for raw_id in source.raw_payload_ids:
            try:
                raw_uuid = uuid.UUID(str(raw_id))
            except (TypeError, ValueError):
                continue
            raw = self.session.get(RawVendorPayload, raw_uuid)
            if raw is not None:
                raw_rows.append(raw)
            if raw and raw.endpoint.endswith(f"/stocks/ohlc/{source.ticker}"):
                if isinstance(raw.payload, dict):
                    ohlc_payload = raw.payload
                    break
        if ohlc_payload is None:
            return None
        price = self._price_context(ohlc_payload)
        heat = normalize_heatmap_payload(
            {"data": source.dealer_heatmap},
            source_status=source.endpoint_statuses.get("dealer_heatmap"),
        )
        endpoint_statuses = {**source.endpoint_statuses}
        if "dealer_heatmap" in endpoint_statuses:
            endpoint_statuses["dealer_heatmap"] = {
                **endpoint_statuses["dealer_heatmap"],
                "analytical_availability": heat["availability"],
                "availability_reason": heat["availability_reason"],
            }
        source_provenance = getattr(source, "source_time_provenance", None)
        if not source_provenance:
            source_provenance = {}
            for raw in raw_rows:
                capability = next(
                    (
                        name
                        for name, template, _params in self.ENDPOINTS
                        if template.format(ticker=source.ticker) in raw.endpoint
                    ),
                    "unknown",
                )
                source_provenance[capability] = source_time_entry(
                    raw,
                    capability=capability,
                    # Historical Phase 2B wrote local utc_now() into observed_at.
                    trust_stored_vendor_time=False,
                )
        source_first_received_at = getattr(source, "source_first_received_at", None)
        if source_first_received_at is None:
            source_first_received_at = earliest_known(*(raw.received_at for raw in raw_rows))
        freshness_anchor_at = getattr(source, "freshness_anchor_at", None)
        if freshness_anchor_at is None:
            # Authoritative raw receipt is safe for legacy reprocess freshness; created_at is not.
            freshness_anchor_at = earliest_known(*(raw.received_at for raw in raw_rows))
        row = Phase2bTickerContextSnapshot(
            ticker=source.ticker,
            created_at=utc_now(),
            specification_version=PHASE2B_SPEC_VERSION,
            config_version=self.config.version,
            config_hash=self.config.configuration_hash,
            effective_config=self.config.snapshot(),
            stock_state=source.stock_state,
            price_context=price,
            iv_rank=source.iv_rank,
            term_structure=source.term_structure,
            dealer_heatmap=heat,
            source_timestamps={
                **source.source_timestamps,
                "heatmap": heat.get("generated_at"),
            },
            raw_payload_ids=source.raw_payload_ids,
            source_request_ids=source.source_request_ids,
            endpoint_statuses={
                **endpoint_statuses,
                "daily_ohlc_reprocessing": {
                    "availability": "AVAILABLE",
                    "source": "PRESERVED_RAW_PAYLOAD",
                },
            },
            source_first_received_at=source_first_received_at,
            freshness_anchor_at=freshness_anchor_at,
            source_time_provenance=source_provenance,
        )
        self.session.add(row)
        self.session.flush()
        return row

    def _price_context(self, payload: dict[str, Any]) -> dict[str, Any]:
        return calculate_price_context(
            payload,
            return_windows=self.config.return_windows,
            sma_windows=self.config.sma_windows,
            atr_window=self.config.atr_window,
            rolling_range_window=self.config.rolling_range_window,
        )

    async def _fetch_ticker_context(self, ticker: str) -> Phase2bTickerContextSnapshot:
        payloads: dict[str, dict[str, Any]] = {}
        raw_ids: list[str] = []
        request_ids: list[str] = []
        statuses: dict[str, Any] = {}
        source_provenance: dict[str, Any] = {}
        ingestor = RawIngestor(self.session)
        for name, template, params in self.ENDPOINTS:
            path = template.format(ticker=ticker)
            captured_at = utc_now()
            try:
                result = await self.client.request(
                    "GET", path, params=params, command="phase2b.context",
                    ticker=ticker,
                )
                payload = (
                    result.payload
                    if isinstance(result.payload, dict)
                    else {"data": result.payload}
                )
                request_id = result.vendor_request_id or result.request_id
                raw = ingestor.persist(
                    endpoint=path,
                    request_id=request_id,
                    vendor_request_id=result.vendor_request_id,
                    ticker=ticker,
                    payload=payload,
                    vendor_observed_at=parse_vendor_observed_at(payload),
                )
                payloads[name] = payload
                raw_ids.append(str(raw.id))
                request_ids.append(request_id)
                statuses[name] = {
                    "endpoint": path,
                    "capability": name,
                    "ticker": ticker,
                    "status": result.status_code,
                    "availability": "AVAILABLE",
                    "captured_at": raw.received_at.isoformat(),
                    "vendor_observed_at": (
                        raw.observed_at.isoformat() if raw.observed_at is not None else None
                    ),
                    "local_captured_at": raw.received_at.isoformat(),
                    "source_first_received_at": raw.received_at.isoformat(),
                    "request_id": request_id,
                }
                source_provenance[name] = source_time_entry(raw, capability=name)
            except NightwatchError as error:
                statuses[name] = {
                    "endpoint": path,
                    "capability": name,
                    "ticker": ticker,
                    "status": error.status_code, "availability": "UNAVAILABLE",
                    "error_code": error.code,
                    "captured_at": captured_at.isoformat(),
                    "vendor_observed_at": None,
                    "local_captured_at": captured_at.isoformat(),
                    "source_first_received_at": None,
                    "request_id": error.request_id,
                }
                source_provenance[name] = unavailable_source_time_entry(
                    capability=name,
                    local_captured_at=captured_at,
                )
                if error.request_id:
                    request_ids.append(error.request_id)
        stock = normalize_stock_state(payloads.get("stock_state", {}))
        price = self._price_context(payloads.get("daily_ohlc", {}))
        iv_data = payloads.get("iv_rank", {}).get("data", {})
        iv_rank = {
            "availability": "AVAILABLE" if iv_data else "UNAVAILABLE",
            "value": iv_data.get("iv_rank"), "vendor_date": iv_data.get("date"),
            "as_of": iv_data.get("as_of"), "classification": None,
        }
        term_data = payloads.get("term_structure", {}).get("data", {})
        term = {
            "availability": "AVAILABLE" if term_data else "UNAVAILABLE",
            "ticker": term_data.get("ticker"), "vendor_date": term_data.get("date"),
            "as_of": term_data.get("as_of"), "nodes": term_data.get("nodes", []),
            "curve_classification": None,
        }
        heat = normalize_heatmap_payload(
            payloads.get("dealer_heatmap"),
            source_status=statuses.get("dealer_heatmap"),
        )
        statuses["dealer_heatmap"]["analytical_availability"] = heat["availability"]
        statuses["dealer_heatmap"]["availability_reason"] = heat["availability_reason"]
        row = Phase2bTickerContextSnapshot(
            ticker=ticker, created_at=utc_now(), specification_version=PHASE2B_SPEC_VERSION,
            config_version=self.config.version, config_hash=self.config.configuration_hash,
            effective_config=self.config.snapshot(), stock_state=stock, price_context=price,
            iv_rank=iv_rank, term_structure=term, dealer_heatmap=heat,
            source_timestamps={
                "stock_state": stock.get("as_of"), "ohlc": price.get("vendor_as_of"),
                "iv_rank": iv_rank.get("as_of"), "term_structure": term.get("as_of"),
                "heatmap": heat.get("generated_at"),
            },
            raw_payload_ids=raw_ids, source_request_ids=request_ids, endpoint_statuses=statuses,
            source_first_received_at=aggregate_source_first_received_at(source_provenance),
            freshness_anchor_at=aggregate_freshness_anchor_at(source_provenance),
            source_time_provenance=source_provenance,
        )
        self.session.add(row)
        self.session.flush()
        return row

    def _evaluation(
        self,
        context: Phase2bTickerContextSnapshot,
        candidate: CandidateSource,
        *,
        evaluation_identity: EvaluationIdentity = EvaluationIdentity.REFRESH,
    ) -> Phase2bCandidateEvaluation:
        existing = self.session.scalar(
            select(Phase2bCandidateEvaluation).where(
                Phase2bCandidateEvaluation.ticker_context_id == context.id,
                Phase2bCandidateEvaluation.contract_symbol == candidate.contract_symbol,
            )
        )
        if existing is not None:
            if existing.evaluation_identity not in {None, evaluation_identity.value}:
                raise ValueError("Existing evaluation identity cannot be overwritten")
            return existing
        radar = (
            self.session.get(OiChangeRadarObservation, candidate.radar_observation_id)
            if candidate.radar_observation_id is not None
            else self.session.scalar(
                select(OiChangeRadarObservation)
                .where(OiChangeRadarObservation.contract_symbol == candidate.contract_symbol)
                .order_by(desc(OiChangeRadarObservation.observation_date)).limit(1)
            )
        )
        chain = self.session.scalar(
            select(ContractOiDailySnapshot)
            .where(ContractOiDailySnapshot.contract_symbol == candidate.contract_symbol)
            .order_by(desc(ContractOiDailySnapshot.vendor_oi_date)).limit(1)
        )
        contract = self.session.scalar(
            select(ContractScanObservation)
            .where(ContractScanObservation.contract_symbol == candidate.contract_symbol)
            .order_by(desc(ContractScanObservation.observed_at)).limit(1)
        )
        expiry = self.session.scalar(
            select(ExpiryObservation)
            .where(
                ExpiryObservation.ticker == candidate.ticker,
                ExpiryObservation.expiration == candidate.expiration,
            ).order_by(desc(ExpiryObservation.observed_at)).limit(1)
        )
        clusters = list(self.session.scalars(
            select(StrikeCluster).where(
                StrikeCluster.ticker == candidate.ticker,
                StrikeCluster.expiration == candidate.expiration,
            ).order_by(desc(StrikeCluster.cluster_score))
        ))
        current_price = context.stock_state.get("current_price_usd")
        atr14 = context.price_context.get("atr_14")
        contract_iv = (
            float(chain.implied_volatility)
            if chain and chain.implied_volatility is not None
            else None
        )
        term_payload = {"data": context.term_structure}
        volatility = map_term_structure(
            term_payload, candidate_expiration=candidate.expiration, contract_iv=contract_iv
        )
        dealer = evaluate_heatmap(
            {"data": context.dealer_heatmap},
            expiration=candidate.expiration, strike=candidate.strike, current_price=current_price,
        )
        bid = float(chain.bid) if chain and chain.bid is not None else None
        ask = float(chain.ask) if chain and chain.ask is not None else None
        mid = (bid + ask) / 2 if bid is not None and ask is not None and ask >= bid else None
        spread = ask - bid if bid is not None and ask is not None and ask >= bid else None
        execution = {
            "availability": "AVAILABLE" if chain else "UNAVAILABLE", "bid": bid, "ask": ask,
            "mid": mid,
            "spread_usd": spread,
            "spread_pct": spread / mid if spread is not None and mid else None,
            "open_interest": chain.open_interest if chain else None,
            "delta": _float(chain.delta) if chain else None,
            "gamma": _float(chain.gamma) if chain else None,
            "theta": _float(chain.theta) if chain else None,
            "vega": _float(chain.vega) if chain else None,
            "charm": _float(chain.charm) if chain else None,
            "chain_spot": _float(chain.underlying_price) if chain else None,
            "quote_as_of": _iso(chain.quote_as_of) if chain else None,
            "greeks_as_of": _iso(chain.greeks_as_of) if chain else None,
        }
        phase2a = {
            "radar_material_event": radar.material_event_eligible if radar else None,
            "radar_observation_date": (
                radar.observation_date.isoformat()
                if radar and radar.observation_date
                else None
            ),
            "premium_usd": _float(radar.premium) if radar else None,
            "oi_diff": radar.delta_oi if radar else None,
            "relative_oi_change": _float(radar.relative_oi_change) if radar else None,
            "volume": radar.volume if radar else None, "trades": radar.trades if radar else None,
            "structure_score": (
                _float(radar.contract_structure_score)
                if radar
                else _float(contract.structure_score) if contract else None
            ),
            "contract_persistence": (
                _float(contract.persistent_positioning_score) if contract else None
            ),
            "expiry_persistence": _float(expiry.persistent_positioning_score) if expiry else None,
            "expiry_activity": _float(expiry.same_day_activity_score) if expiry else None,
            "clusters": [
                {"right": row.right, "min_strike": _float(row.min_strike),
                 "max_strike": _float(row.max_strike), "score": _float(row.cluster_score),
                 "shape": row.shape} for row in clusters[:5]
            ],
            "archive_completeness": radar.archive_completeness if radar else None,
            "threshold_profile_version": radar.threshold_profile_version if radar else None,
            "threshold_config_hash": radar.threshold_config_hash if radar else None,
        }
        location = strike_location(
            strike=candidate.strike, current_price=current_price, atr14=atr14,
            tolerance_pct=self.config.at_spot_tolerance_pct,
        )
        source_times = {
            "radar": phase2a["radar_observation_date"],
            "chain": chain.vendor_oi_date.isoformat() if chain else None,
            "chain_quote": execution["quote_as_of"], "chain_greeks": execution["greeks_as_of"],
            **context.source_timestamps,
        }
        evaluated_at = utc_now()
        row = Phase2bCandidateEvaluation(
            ticker_context_id=context.id, contract_symbol=candidate.contract_symbol,
            ticker=candidate.ticker, expiration=candidate.expiration, right=candidate.right,
            strike=candidate.strike, dte_at_detection=candidate.dte_at_detection,
            evaluated_at=evaluated_at,
            trigger_sources=(radar.trigger_sources or ["RADAR_EVENT"]) if radar else [],
            phase2a_evidence=phase2a, strike_location=location,
            volatility_context=volatility, dealer_context=dealer, execution_context=execution,
            evidence_states={
                "price": context.price_context.get("availability", "UNAVAILABLE"),
                "stock_state": context.stock_state.get("availability", "UNAVAILABLE"),
                "volatility": volatility.get("availability", "UNAVAILABLE"),
                "dealer": dealer.get("availability", "UNAVAILABLE"),
                "execution": execution["availability"],
                "positioning": "AVAILABLE" if radar else "UNAVAILABLE",
            },
            source_timestamps=source_times, direction="UNRESOLVED",
            specification_version=PHASE2B_SPEC_VERSION, config_version=self.config.version,
            config_hash=self.config.configuration_hash,
            source_first_received_at=earliest_known(
                getattr(context, "source_first_received_at", None),
                candidate.source_first_received_at,
            ),
            source_radar_observation_id=candidate.radar_observation_id,
            evaluation_identity=evaluation_identity.value,
        )
        self.session.add(row)
        self.session.flush()
        return row


def latest_candidate_context(session: Session, contract_symbol: str) -> dict[str, Any] | None:
    evaluation = session.scalar(
        select(Phase2bCandidateEvaluation)
        .where(Phase2bCandidateEvaluation.contract_symbol == contract_symbol)
        .order_by(desc(Phase2bCandidateEvaluation.evaluated_at)).limit(1)
    )
    if evaluation is None:
        return None
    ticker = session.get(Phase2bTickerContextSnapshot, evaluation.ticker_context_id)
    return {
        "candidate": {
            "ticker": evaluation.ticker, "contract_symbol": evaluation.contract_symbol,
            "expiration": evaluation.expiration.isoformat(), "dte": evaluation.dte_at_detection,
            "right": evaluation.right, "strike": float(evaluation.strike),
            "trigger_sources": evaluation.trigger_sources,
            "direction": evaluation.direction,
            "source_radar_observation_id": (
                str(evaluation.source_radar_observation_id)
                if evaluation.source_radar_observation_id
                else None
            ),
        },
        "phase2a": evaluation.phase2a_evidence,
        "price": {"stock_state": ticker.stock_state, "history": ticker.price_context,
                  "strike_location": evaluation.strike_location},
        "volatility": {"iv_rank": ticker.iv_rank, "term": evaluation.volatility_context},
        "dealer": evaluation.dealer_context,
        "execution": evaluation.execution_context,
        "data_quality": evaluation.evidence_states,
        "timestamps": evaluation.source_timestamps,
        "time_provenance": {
            "source_first_received_at": (
                evaluation.source_first_received_at.isoformat()
                if evaluation.source_first_received_at
                else None
            ),
            "candidate_first_knowledge_at": None,
            "context_evaluated_at": evaluation.evaluated_at.isoformat(),
            "evaluation_identity": evaluation.evaluation_identity,
            "sources": ticker.source_time_provenance or {},
        },
        "specification_version": evaluation.specification_version,
        "config_version": evaluation.config_version,
        "evaluated_at": evaluation.evaluated_at.isoformat(),
        "v2_state": latest_v2_state(
            session, contract_symbol, candidate_evaluation_id=evaluation.id
        ),
        "v3_research_workspace": latest_v3_workspace(
            session, contract_symbol, candidate_evaluation_id=evaluation.id
        ),
        "deferred": {"iv_vs_rv": "NOT_IMPLEMENTED", "skew": "NOT_IMPLEMENTED",
                     "event_risk": "NOT_AVAILABLE", "standard_gex": "NOT_IMPLEMENTED",
                     "zero_dte_dealer_gex": "NOT_IMPLEMENTED"},
    }


def _float(value: Any) -> float | None:
    return float(value) if value is not None else None


def _iso(value: Any) -> str | None:
    return value.isoformat() if value is not None else None

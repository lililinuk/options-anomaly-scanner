from __future__ import annotations

import hashlib
import json
import uuid
from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from typing import Any, Final

from sqlalchemy import desc, or_, select
from sqlalchemy.orm import Session, selectinload

from app.confirmation.config import active_phase2b_config
from app.confirmation.domain import calculate_price_context, normalize_stock_state, strike_location
from app.confirmation.provenance import EvaluationIdentity, source_time_entry
from app.confirmation.workspace_v3 import (
    ADJACENT_EXPIRY_RULE_VERSION,
    BELOW_FLOOR_PATH_RULE_VERSION,
    PRIMARY_FLOOR_RULE_VERSION,
    PRIMARY_UPPER_NODE_RULE_VERSION,
)
from app.core.time import ensure_utc, market_date, utc_now
from app.db.models import (
    AnomalyContextDetail,
    ContractOiDailySnapshot,
    ContractScanObservation,
    ExpiryObservation,
    OiChangeRadarObservation,
    ProductCandidate,
    ProductCandidateContext,
    ProductCandidateTrigger,
    RawVendorPayload,
    StrikeCluster,
)
from app.dealer_archive.repository import best_archived_surface_at_or_before
from app.ingestion.raw import RawIngestor, parse_vendor_observed_at
from app.nightwatch.errors import NightwatchError
from app.scanner.candidate_projection import contract_deep_dive, expiry_deep_dive

PHASE2B_VNEXT_SPEC_VERSION: Final = "phase2b_vnext_stage6"
PHASE2B_VNEXT_CONFIG_VERSION: Final = "phase2b_vnext_stage6_balanced_v1"
IV_RANK_CORE_ELIGIBILITY: Final = "WITHHOLD_PENDING_PROVENANCE"
SOURCE_ENDPOINTS: Final = (
    ("daily_ohlc", "/v1/stocks/ohlc/{ticker}", {"candle_size": "1d"}),
    ("stock_state", "/v1/stocks/stock-state/{ticker}", {}),
    ("iv_rank", "/v1/volatility/iv-rank/{ticker}", {}),
    ("term_structure", "/v1/volatility/term-structure/{ticker}", {}),
)
AVAILABILITY_STATES: Final = frozenset(
    {"AVAILABLE", "PARTIAL", "UNAVAILABLE", "NOT_YET_AVAILABLE"}
)


def stage6_config_snapshot() -> dict[str, Any]:
    legacy = active_phase2b_config()
    return {
        "version": PHASE2B_VNEXT_CONFIG_VERSION,
        "source_contract": [name for name, _path, _params in SOURCE_ENDPOINTS],
        "dealer_gex_source": "ARCHIVE_ONLY",
        "ticker_source_call_limit": 4,
        "per_anomaly_vendor_call_limit": 0,
        "iv_rank_core_eligibility": IV_RANK_CORE_ELIGIBILITY,
        "price_return_windows": list(legacy.return_windows),
        "price_sma_windows": list(legacy.sma_windows),
        "price_atr_window": legacy.atr_window,
        "price_rolling_range_window": legacy.rolling_range_window,
        "at_spot_tolerance_pct": str(legacy.at_spot_tolerance_pct),
        "dealer_gex_rule_versions": {
            "primary_floor": PRIMARY_FLOOR_RULE_VERSION,
            "primary_upper_node": PRIMARY_UPPER_NODE_RULE_VERSION,
            "below_floor_path": BELOW_FLOOR_PATH_RULE_VERSION,
            "adjacent_expiry": ADJACENT_EXPIRY_RULE_VERSION,
        },
    }


def stage6_config_hash() -> str:
    encoded = json.dumps(
        stage6_config_snapshot(), sort_keys=True, separators=(",", ":")
    ).encode()
    return hashlib.sha256(encoded).hexdigest()


@dataclass(frozen=True)
class SourceBundle:
    payloads: dict[str, dict[str, Any]]
    provenance: dict[str, dict[str, Any]]
    statuses: dict[str, dict[str, Any]]


@dataclass(frozen=True)
class TriggerDescriptor:
    trigger: ProductCandidateTrigger
    expiration: date | None
    right: str | None
    strike: Decimal | None
    dte_at_detection: int | None
    source: Any


def _price_payload_at_or_before(
    payload: dict[str, Any],
    *,
    evidence_cutoff_at: datetime,
) -> dict[str, Any]:
    """Keep only daily bars with a provable market date at the evidence cutoff."""

    if not isinstance(payload, dict):
        return {}
    cutoff_market_date = market_date(ensure_utc(evidence_cutoff_at))
    envelope = dict(payload)
    nested = envelope.get("data")
    data = dict(nested) if isinstance(nested, dict) else envelope
    bars = data.get("bars")
    if not isinstance(bars, list):
        return envelope
    eligible: list[dict[str, Any]] = []
    for bar in bars:
        if not isinstance(bar, dict):
            continue
        trading_date = bar.get("trading_date")
        if not isinstance(trading_date, str):
            continue
        try:
            observation_date = date.fromisoformat(trading_date)
        except ValueError:
            continue
        if observation_date <= cutoff_market_date:
            eligible.append(bar)
    data["bars"] = eligible
    if isinstance(nested, dict):
        envelope["data"] = data
        return envelope
    return data


class Stage6BalancedContextService:
    """Persist the candidate-first Balanced Model without legacy Radar gating."""

    def __init__(self, session: Session, client: Any | None = None) -> None:
        self.session = session
        self.client = client
        self.config = active_phase2b_config()

    def create_baseline(
        self,
        candidate_id: uuid.UUID,
        *,
        context_evaluated_at: datetime | None = None,
    ) -> ProductCandidateContext:
        candidate = self._candidate(candidate_id)
        existing = self._baseline(candidate.id)
        if existing is not None:
            stored_trigger_ids = {
                detail.product_candidate_trigger_id for detail in existing.details
            }
            current_trigger_ids = {trigger.id for trigger in candidate.triggers}
            if stored_trigger_ids != current_trigger_ids:
                raise ValueError("Persisted baseline detail set conflicts with candidate triggers")
            return existing
        evaluated_at = ensure_utc(context_evaluated_at or utc_now())
        evidence_cutoff_at = ensure_utc(candidate.candidate_first_knowledge_at)
        if evaluated_at < evidence_cutoff_at:
            raise ValueError("Baseline cannot predate candidate first knowledge")
        sources = self._archived_source_bundle(
            candidate.ticker,
            evidence_cutoff_at=evidence_cutoff_at,
        )
        return self._persist_evaluation(
            candidate,
            evaluation_kind=EvaluationIdentity.FIRST_KNOWLEDGE_BASELINE,
            evaluated_at=evaluated_at,
            evidence_cutoff_at=evidence_cutoff_at,
            sources=sources,
        )

    async def refresh(self, candidate_id: uuid.UUID) -> ProductCandidateContext:
        if self.client is None:
            raise ValueError("An explicit Stage 6 source client is required for REFRESH")
        candidate = self._candidate(candidate_id)
        sources = await self._fetch_source_bundle(candidate.ticker)
        evaluated_at = utc_now()
        evidence_cutoff_at = evaluated_at
        return self._persist_evaluation(
            candidate,
            evaluation_kind=EvaluationIdentity.REFRESH,
            evaluated_at=evaluated_at,
            evidence_cutoff_at=evidence_cutoff_at,
            sources=sources,
        )

    def _candidate(self, candidate_id: uuid.UUID) -> ProductCandidate:
        candidate = self.session.scalar(
            select(ProductCandidate)
            .options(selectinload(ProductCandidate.triggers))
            .where(ProductCandidate.id == candidate_id)
        )
        if candidate is None:
            raise LookupError("ProductCandidate not found")
        return candidate

    def _baseline(self, candidate_id: uuid.UUID) -> ProductCandidateContext | None:
        return self.session.scalar(
            select(ProductCandidateContext)
            .options(selectinload(ProductCandidateContext.details))
            .where(
                ProductCandidateContext.product_candidate_id == candidate_id,
                ProductCandidateContext.evaluation_kind
                == EvaluationIdentity.FIRST_KNOWLEDGE_BASELINE.value,
                ProductCandidateContext.context_specification_version
                == PHASE2B_VNEXT_SPEC_VERSION,
                ProductCandidateContext.context_config_hash == stage6_config_hash(),
            )
        )

    def _archived_source_bundle(
        self,
        ticker: str,
        *,
        evidence_cutoff_at: datetime,
    ) -> SourceBundle:
        evidence_cutoff_at = ensure_utc(evidence_cutoff_at)
        payloads: dict[str, dict[str, Any]] = {}
        provenance: dict[str, dict[str, Any]] = {}
        statuses: dict[str, dict[str, Any]] = {}
        for name, template, _params in SOURCE_ENDPOINTS:
            endpoint = template.format(ticker=ticker)
            raw = self.session.scalar(
                select(RawVendorPayload)
                .where(
                    RawVendorPayload.ticker == ticker,
                    RawVendorPayload.endpoint == endpoint,
                    RawVendorPayload.received_at <= evidence_cutoff_at,
                    or_(
                        RawVendorPayload.observed_at.is_(None),
                        RawVendorPayload.observed_at <= evidence_cutoff_at,
                    ),
                )
                .order_by(desc(RawVendorPayload.received_at))
                .limit(1)
            )
            if raw is None or not isinstance(raw.payload, dict):
                statuses[name] = {
                    "availability": "NOT_YET_AVAILABLE",
                    "endpoint": endpoint,
                }
                provenance[name] = _missing_source_provenance(
                    name, availability="NOT_YET_AVAILABLE"
                )
                continue
            payloads[name] = raw.payload
            provenance[name] = source_time_entry(raw, capability=name)
            statuses[name] = {
                "availability": "AVAILABLE",
                "endpoint": endpoint,
                "raw_payload_id": str(raw.id),
                "request_id": raw.request_id,
            }
        return SourceBundle(payloads, provenance, statuses)

    async def _fetch_source_bundle(self, ticker: str) -> SourceBundle:
        payloads: dict[str, dict[str, Any]] = {}
        provenance: dict[str, dict[str, Any]] = {}
        statuses: dict[str, dict[str, Any]] = {}
        ingestor = RawIngestor(self.session)
        for name, template, params in SOURCE_ENDPOINTS:
            endpoint = template.format(ticker=ticker)
            captured_at = utc_now()
            try:
                result = await self.client.request(
                    "GET",
                    endpoint,
                    params=params,
                    command="phase2b.vnext.refresh",
                    ticker=ticker,
                )
                payload = (
                    result.payload
                    if isinstance(result.payload, dict)
                    else {"data": result.payload}
                )
                request_id = result.vendor_request_id or result.request_id
                raw = ingestor.persist(
                    endpoint=endpoint,
                    request_id=request_id,
                    vendor_request_id=result.vendor_request_id,
                    ticker=ticker,
                    payload=payload,
                    vendor_observed_at=parse_vendor_observed_at(payload),
                )
                payloads[name] = payload
                provenance[name] = source_time_entry(raw, capability=name)
                statuses[name] = {
                    "availability": "AVAILABLE",
                    "endpoint": endpoint,
                    "http_status": result.status_code,
                    "raw_payload_id": str(raw.id),
                    "request_id": request_id,
                }
            except NightwatchError as error:
                statuses[name] = {
                    "availability": "UNAVAILABLE",
                    "endpoint": endpoint,
                    "http_status": error.status_code,
                    "error_code": error.code,
                    "request_id": error.request_id,
                }
                provenance[name] = {
                    **_missing_source_provenance(name, availability="UNAVAILABLE"),
                    "local_captured_at": captured_at.isoformat(),
                    "freshness_basis": "LOCAL_REQUEST_ATTEMPT_ONLY",
                }
        return SourceBundle(payloads, provenance, statuses)

    def _persist_evaluation(
        self,
        candidate: ProductCandidate,
        *,
        evaluation_kind: EvaluationIdentity,
        evaluated_at: datetime,
        evidence_cutoff_at: datetime,
        sources: SourceBundle,
    ) -> ProductCandidateContext:
        evaluated_at = ensure_utc(evaluated_at)
        evidence_cutoff_at = ensure_utc(evidence_cutoff_at)
        if evidence_cutoff_at > evaluated_at:
            raise ValueError("Evidence cutoff cannot follow context evaluation")
        descriptors = [self._trigger_descriptor(row) for row in candidate.triggers]
        expirations = sorted(
            {item.expiration for item in descriptors if item.expiration is not None}
        )
        chain_by_expiry = {
            expiration: self._chain_context(
                candidate.ticker,
                expiration=expiration,
                evidence_cutoff_at=evidence_cutoff_at,
            )
            for expiration in expirations
        }
        archived = best_archived_surface_at_or_before(
            self.session,
            ticker=candidate.ticker,
            as_of=evidence_cutoff_at,
        )
        dealer_snapshot, dealer_payload = archived if archived else (None, None)

        price_payload = _price_payload_at_or_before(
            sources.payloads.get("daily_ohlc", {}),
            evidence_cutoff_at=evidence_cutoff_at,
        )
        price = calculate_price_context(
            price_payload,
            return_windows=self.config.return_windows,
            sma_windows=self.config.sma_windows,
            atr_window=self.config.atr_window,
            rolling_range_window=self.config.rolling_range_window,
        )
        price.setdefault("latest_trading_date", None)
        price.setdefault("latest_regular_close_usd", None)
        stock_state = normalize_stock_state(sources.payloads.get("stock_state", {}))
        term_source_state = sources.statuses.get("term_structure", {}).get(
            "availability", "NOT_YET_AVAILABLE"
        )
        iv_rank_source_state = sources.statuses.get("iv_rank", {}).get(
            "availability", "NOT_YET_AVAILABLE"
        )
        term = _normalize_term_structure(
            sources.payloads.get("term_structure", {}),
            source_state=term_source_state,
        )
        iv_rank = _normalize_iv_rank(
            sources.payloads.get("iv_rank", {}),
            source_state=iv_rank_source_state,
        )
        term_by_expiry = {
            expiration.isoformat(): term_context_for_expiry(term, expiration=expiration)
            for expiration in expirations
        }
        dealer_by_expiry = {
            expiration.isoformat(): dealer_gex_context_for_expiry(
                dealer_payload, expiration=expiration
            )
            for expiration in expirations
        }
        implied_move = _vendor_implied_move(sources.payloads.get("stock_state", {}))
        volatility = {
            "term_structure": term,
            "expiry_contexts": term_by_expiry,
            "iv_rank": iv_rank,
            "implied_move": implied_move,
        }
        dealer = {
            "source": "ARCHIVE_ONLY",
            "availability": "AVAILABLE" if dealer_snapshot else "NOT_YET_AVAILABLE",
            "archive_snapshot_id": str(dealer_snapshot.id) if dealer_snapshot else None,
            "vendor_observed_at": _iso(
                dealer_snapshot.vendor_observed_at if dealer_snapshot else None
            ),
            "local_captured_at": _iso(
                dealer_snapshot.captured_at if dealer_snapshot else None
            ),
            "expiry_contexts": dealer_by_expiry,
        }
        price_source_state = sources.statuses.get("daily_ohlc", {}).get(
            "availability", "NOT_YET_AVAILABLE"
        )
        availability = {
            "price": _price_availability(price, source_state=price_source_state),
            "stock_state": _simple_availability(
                stock_state.get("availability"),
                source_state=sources.statuses.get("stock_state", {}).get("availability"),
            ),
            "volatility": _simple_availability(
                term.get("availability"),
                source_state=term_source_state,
            ),
            "dealer_gex": dealer["availability"],
            "iv_rank": _simple_availability(
                iv_rank.get("availability"),
                source_state=iv_rank_source_state,
            ),
        }
        price_as_of = _source_vendor_time(sources.provenance.get("daily_ohlc"))
        context = ProductCandidateContext(
            id=uuid.uuid4(),
            product_candidate_id=candidate.id,
            evaluation_kind=evaluation_kind.value,
            candidate_first_knowledge_at=ensure_utc(
                candidate.candidate_first_knowledge_at
            ),
            context_evaluated_at=evaluated_at,
            price_as_of=price_as_of,
            context_specification_version=PHASE2B_VNEXT_SPEC_VERSION,
            context_config_version=PHASE2B_VNEXT_CONFIG_VERSION,
            context_config_hash=stage6_config_hash(),
            price_context={"history": price, "stock_state": stock_state},
            volatility_context=volatility,
            dealer_gex_context=dealer,
            availability=availability,
            provenance={
                "product_candidate_id": str(candidate.id),
                "candidate_first_knowledge_at": _iso(
                    candidate.candidate_first_knowledge_at
                ),
                "context_evaluated_at": _iso(evaluated_at),
                "evidence_cutoff_at": _iso(evidence_cutoff_at),
                "source_contract": [name for name, _path, _params in SOURCE_ENDPOINTS],
                "sources": sources.provenance,
                "source_statuses": sources.statuses,
                "config": stage6_config_snapshot(),
                "dealer_archive_snapshot_id": (
                    str(dealer_snapshot.id) if dealer_snapshot else None
                ),
            },
            created_at=evaluated_at,
        )
        self.session.add(context)
        self.session.flush()
        for descriptor in descriptors:
            detail = self._detail(
                candidate,
                context,
                descriptor,
                price=price,
                stock_state=stock_state,
                term_by_expiry=term_by_expiry,
                dealer_by_expiry=dealer_by_expiry,
                chain_by_expiry=chain_by_expiry,
            )
            self.session.add(detail)
            context.details.append(detail)
        self.session.flush()
        return context

    def _trigger_descriptor(self, trigger: ProductCandidateTrigger) -> TriggerDescriptor:
        source: Any = None
        expiration: date | None = None
        right: str | None = None
        strike: Decimal | None = None
        dte: int | None = None
        if trigger.anomaly_entity_type == "EXPIRY":
            source = self.session.get(
                ExpiryObservation, trigger.source_expiry_observation_id
            )
            if source is not None:
                expiration, dte = source.expiration, source.dte_at_detection
        elif trigger.evidence_family == "RADAR_EVENT":
            source = self.session.get(
                OiChangeRadarObservation, trigger.source_radar_observation_id
            )
            if source is not None:
                expiration = source.matched_expiration
                right = source.matched_right
                strike = source.matched_strike
                dte = source.matched_dte
        else:
            source = self.session.get(
                ContractScanObservation, trigger.source_contract_observation_id
            )
            if source is not None:
                expiration, right, strike, dte = (
                    source.expiration,
                    source.right,
                    source.strike,
                    source.dte_at_detection,
                )
        return TriggerDescriptor(trigger, expiration, right, strike, dte, source)

    def _chain_context(
        self,
        ticker: str,
        *,
        expiration: date,
        evidence_cutoff_at: datetime,
    ) -> dict[str, ContractOiDailySnapshot]:
        evidence_cutoff_at = ensure_utc(evidence_cutoff_at)
        rows = self.session.scalars(
            select(ContractOiDailySnapshot)
            .join(
                RawVendorPayload,
                RawVendorPayload.id == ContractOiDailySnapshot.raw_payload_id,
            )
            .where(
                ContractOiDailySnapshot.ticker == ticker,
                ContractOiDailySnapshot.expiration == expiration,
                ContractOiDailySnapshot.vendor_oi_as_of <= evidence_cutoff_at,
                RawVendorPayload.received_at <= evidence_cutoff_at,
                or_(
                    RawVendorPayload.observed_at.is_(None),
                    RawVendorPayload.observed_at <= evidence_cutoff_at,
                ),
                or_(
                    ContractOiDailySnapshot.quote_as_of.is_(None),
                    ContractOiDailySnapshot.quote_as_of <= evidence_cutoff_at,
                ),
                or_(
                    ContractOiDailySnapshot.greeks_as_of.is_(None),
                    ContractOiDailySnapshot.greeks_as_of <= evidence_cutoff_at,
                ),
            )
            .order_by(
                ContractOiDailySnapshot.contract_symbol,
                desc(ContractOiDailySnapshot.vendor_oi_as_of),
            )
        )
        result: dict[str, ContractOiDailySnapshot] = {}
        for row in rows:
            result.setdefault(row.contract_symbol, row)
        return result

    def _detail(
        self,
        candidate: ProductCandidate,
        context: ProductCandidateContext,
        descriptor: TriggerDescriptor,
        *,
        price: dict[str, Any],
        stock_state: dict[str, Any],
        term_by_expiry: dict[str, dict[str, Any]],
        dealer_by_expiry: dict[str, dict[str, Any]],
        chain_by_expiry: dict[date, dict[str, ContractOiDailySnapshot]],
    ) -> AnomalyContextDetail:
        trigger = descriptor.trigger
        expiry_key = descriptor.expiration.isoformat() if descriptor.expiration else None
        term_context = term_by_expiry.get(expiry_key, _empty_term_context(expiry_key))
        dealer_context = dealer_by_expiry.get(
            expiry_key, _empty_dealer_context(expiry_key)
        )
        chain = (
            chain_by_expiry.get(descriptor.expiration, {}).get(trigger.anomaly_identity)
            if descriptor.expiration is not None
            and trigger.anomaly_entity_type == "CONTRACT"
            else None
        )
        contract_snapshot = None
        expiry_recap = None
        quote_as_of = None
        deep_dive = self._deep_dive(candidate, descriptor)
        if trigger.anomaly_entity_type == "CONTRACT":
            bid = _number(chain.bid) if chain else None
            ask = _number(chain.ask) if chain else None
            spread = ask - bid if bid is not None and ask is not None and ask >= bid else None
            mid = (ask + bid) / 2 if spread is not None else None
            spot = _number(stock_state.get("current_price_usd"))
            if spot is None:
                spot = _number(price.get("latest_regular_close_usd"))
            location = (
                strike_location(
                    strike=descriptor.strike,
                    current_price=spot,
                    atr14=_number(price.get("atr_14")),
                    tolerance_pct=self.config.at_spot_tolerance_pct,
                )
                if descriptor.strike is not None
                else _empty_strike_location()
            )
            quote_as_of = chain.quote_as_of if chain else None
            contract_iv = _number(chain.implied_volatility) if chain else None
            contract_snapshot = {
                "contract_symbol": trigger.anomaly_identity,
                "expiration": expiry_key,
                "right": descriptor.right,
                "strike": _number(descriptor.strike),
                "dte_at_detection": descriptor.dte_at_detection,
                "dte_anchor_date": trigger.event_date.isoformat()
                if trigger.event_date
                else None,
                "dte_anchor_type": "TRIGGER_EVENT_DATE",
                "strike_location": location,
                "contract_iv": contract_iv,
                "delta": _number(chain.delta) if chain else None,
                "bid": bid,
                "ask": ask,
                "spread_usd": spread,
                "spread_pct": spread / mid if spread is not None and mid else None,
                "quote_as_of": _iso(quote_as_of),
                "chain_raw_payload_id": str(chain.raw_payload_id) if chain else None,
                "chain_source_request_id": chain.source_request_id if chain else None,
            }
        else:
            source = descriptor.source
            expiry_recap = {
                "expiration": expiry_key,
                "dte_at_detection": descriptor.dte_at_detection,
                "dte_anchor_date": trigger.event_date.isoformat()
                if trigger.event_date
                else None,
                "call_volume": getattr(source, "call_volume", None),
                "put_volume": getattr(source, "put_volume", None),
                "call_oi": getattr(source, "call_oi", None),
                "put_oi": getattr(source, "put_oi", None),
                "same_day_activity_score": _number(
                    getattr(source, "same_day_activity_score", None)
                ),
                "score_basis": getattr(source, "same_day_score_basis", None),
                "source_expiry_observation_id": (
                    str(trigger.source_expiry_observation_id)
                    if trigger.source_expiry_observation_id
                    else None
                ),
            }
        execution_availability = (
            "NOT_YET_AVAILABLE"
            if trigger.anomaly_entity_type == "EXPIRY"
            else "AVAILABLE"
            if chain and (chain.bid is not None or chain.ask is not None)
            else "PARTIAL"
            if chain
            else "NOT_YET_AVAILABLE"
        )
        detail_availability = {
            "volatility": _simple_availability(term_context.get("availability")),
            "dealer_gex": _simple_availability(dealer_context.get("availability")),
            "execution": execution_availability,
            "positioning_provenance": "AVAILABLE",
            "deep_dive": _simple_availability(deep_dive.get("availability")),
        }
        contract_iv = contract_snapshot.get("contract_iv") if contract_snapshot else None
        return AnomalyContextDetail(
            id=uuid.uuid4(),
            product_candidate_context_id=context.id,
            product_candidate_trigger_id=trigger.id,
            anomaly_entity_type=trigger.anomaly_entity_type,
            anomaly_identity=trigger.anomaly_identity,
            event_date=trigger.event_date,
            expiry_anchor=descriptor.expiration,
            source_first_received_at=trigger.source_first_received_at,
            vendor_observed_at=trigger.vendor_observed_at,
            local_captured_at=trigger.local_captured_at,
            quote_as_of=quote_as_of,
            contract_snapshot=contract_snapshot,
            expiry_activity_recap=expiry_recap,
            volatility_context={
                "shared_expiry_key": expiry_key,
                "contract_iv": contract_iv,
                "contract_iv_minus_expiry_node": (
                    contract_iv - term_context["candidate_term_iv"]
                    if contract_iv is not None
                    and term_context.get("candidate_term_iv") is not None
                    else None
                ),
            },
            dealer_gex_context={
                "shared_expiry_key": expiry_key,
                "availability": dealer_context.get("availability"),
            },
            deep_dive_references=deep_dive,
            availability=detail_availability,
            provenance={
                "product_candidate_id": str(candidate.id),
                "product_candidate_trigger_id": str(trigger.id),
                "source_evidence_identity": trigger.source_evidence_identity,
                "source_ids": trigger.source_ids,
                "trigger_provenance": trigger.provenance,
                "event_date": trigger.event_date.isoformat()
                if trigger.event_date
                else None,
                "source_first_received_at": _iso(trigger.source_first_received_at),
                "vendor_observed_at": _iso(trigger.vendor_observed_at),
                "local_captured_at": _iso(trigger.local_captured_at),
                "quote_as_of": _iso(quote_as_of),
            },
            created_at=context.context_evaluated_at,
        )

    def _deep_dive(
        self, candidate: ProductCandidate, descriptor: TriggerDescriptor
    ) -> dict[str, Any]:
        trigger = descriptor.trigger
        if trigger.anomaly_entity_type == "CONTRACT":
            source = (
                descriptor.source
                if isinstance(descriptor.source, ContractScanObservation)
                else self.session.scalar(
                    select(ContractScanObservation).where(
                        ContractScanObservation.scan_run_id == candidate.scan_run_id,
                        ContractScanObservation.contract_symbol
                        == trigger.anomaly_identity,
                    )
                )
            )
            value = contract_deep_dive(source)
            if not value.get("structure_positive_evidence"):
                return {"availability": value.get("availability"), "structure": None}
            return {"availability": "AVAILABLE", "structure": value.get("structure")}
        source = descriptor.source
        if not isinstance(source, ExpiryObservation):
            return {"availability": "UNAVAILABLE", "structures": [], "valid_clusters": []}
        contracts = list(
            self.session.scalars(
                select(ContractScanObservation).where(
                    ContractScanObservation.expiry_observation_id == source.id
                )
            )
        )
        clusters = list(
            self.session.scalars(
                select(StrikeCluster).where(StrikeCluster.expiry_observation_id == source.id)
            )
        )
        value = expiry_deep_dive(contracts, clusters)
        return {
            "availability": value.get("availability"),
            "structures": [
                item.get("structure")
                for item in value.get("structures", [])
                if item.get("structure_positive_evidence") and item.get("structure")
            ],
            "valid_clusters": value.get("valid_clusters", []),
        }


def load_context_history(
    session: Session, candidate_id: uuid.UUID
) -> tuple[ProductCandidate | None, list[ProductCandidateContext]]:
    candidate = session.scalar(
        select(ProductCandidate)
        .options(selectinload(ProductCandidate.triggers))
        .where(ProductCandidate.id == candidate_id)
    )
    if candidate is None:
        return None, []
    contexts = list(
        session.scalars(
            select(ProductCandidateContext)
            .options(selectinload(ProductCandidateContext.details))
            .where(ProductCandidateContext.product_candidate_id == candidate_id)
            .order_by(ProductCandidateContext.context_evaluated_at)
        )
    )
    return candidate, contexts


def context_history_public(
    candidate: ProductCandidate, contexts: list[ProductCandidateContext]
) -> dict[str, Any]:
    return {
        "product_candidate": {
            "id": str(candidate.id),
            "ticker": candidate.ticker,
            "candidate_first_knowledge_at": _iso(
                candidate.candidate_first_knowledge_at
            ),
            "materialization_rule_version": candidate.materialization_rule_version,
            "materialization_rule_hash": candidate.materialization_rule_hash,
        },
        "baseline_state": (
            "AVAILABLE"
            if any(
                row.evaluation_kind
                == EvaluationIdentity.FIRST_KNOWLEDGE_BASELINE.value
                for row in contexts
            )
            else "NOT_YET_AVAILABLE"
        ),
        "contexts": [context_public(row) for row in contexts],
    }


def context_public(context: ProductCandidateContext) -> dict[str, Any]:
    return {
        "id": str(context.id),
        "product_candidate_id": str(context.product_candidate_id),
        "evaluation_kind": context.evaluation_kind,
        "candidate_first_knowledge_at": _iso(context.candidate_first_knowledge_at),
        "context_evaluated_at": _iso(context.context_evaluated_at),
        "price_as_of": _iso(context.price_as_of),
        "context_specification_version": context.context_specification_version,
        "context_config_version": context.context_config_version,
        "context_config_hash": context.context_config_hash,
        "price_context": context.price_context,
        "volatility_context": context.volatility_context,
        "dealer_gex_context": context.dealer_gex_context,
        "availability": context.availability,
        "provenance": context.provenance,
        "details": [detail_public(row) for row in context.details],
    }


def detail_public(detail: AnomalyContextDetail) -> dict[str, Any]:
    return {
        "id": str(detail.id),
        "product_candidate_trigger_id": str(detail.product_candidate_trigger_id),
        "anomaly_entity_type": detail.anomaly_entity_type,
        "anomaly_identity": detail.anomaly_identity,
        "event_date": detail.event_date.isoformat() if detail.event_date else None,
        "expiry_anchor": detail.expiry_anchor.isoformat()
        if detail.expiry_anchor
        else None,
        "source_first_received_at": _iso(detail.source_first_received_at),
        "vendor_observed_at": _iso(detail.vendor_observed_at),
        "local_captured_at": _iso(detail.local_captured_at),
        "quote_as_of": _iso(detail.quote_as_of),
        "contract_snapshot": detail.contract_snapshot,
        "expiry_activity_recap": detail.expiry_activity_recap,
        "volatility_context": detail.volatility_context,
        "dealer_gex_context": detail.dealer_gex_context,
        "deep_dive_references": detail.deep_dive_references,
        "availability": detail.availability,
        "provenance": detail.provenance,
    }


def _normalize_iv_rank(
    payload: dict[str, Any], *, source_state: str = "UNAVAILABLE"
) -> dict[str, Any]:
    data = _payload_data(payload)
    availability = (
        source_state
        if source_state in {"NOT_YET_AVAILABLE", "UNAVAILABLE"}
        else "AVAILABLE"
        if data.get("iv_rank") is not None
        else "PARTIAL"
    )
    return {
        "availability": availability,
        "entity": "TICKER",
        "value": data.get("iv_rank"),
        "vendor_date": data.get("date"),
        "as_of": data.get("as_of"),
        "vendor_semantics": "UNVERIFIED",
        "core_eligibility": IV_RANK_CORE_ELIGIBILITY,
        "classification": None,
    }


def _normalize_term_structure(
    payload: dict[str, Any], *, source_state: str = "UNAVAILABLE"
) -> dict[str, Any]:
    data = _payload_data(payload)
    nodes = [row for row in data.get("nodes", []) if isinstance(row, dict)]
    availability = (
        source_state
        if source_state in {"NOT_YET_AVAILABLE", "UNAVAILABLE"}
        else "AVAILABLE"
        if nodes
        else "PARTIAL"
    )
    return {
        "availability": availability,
        "ticker": data.get("ticker"),
        "vendor_date": data.get("date"),
        "as_of": data.get("as_of"),
        "nodes": nodes,
    }


def term_context_for_expiry(
    term: dict[str, Any], *, expiration: date
) -> dict[str, Any]:
    nodes = [row for row in term.get("nodes", []) if isinstance(row, dict)]
    parsed = [
        (node, _date(node.get("expiry")), _number(node.get("implied_vol_pct")))
        for node in nodes
    ]
    parsed = [item for item in parsed if item[1] is not None]
    exact = next((item for item in parsed if item[1] == expiration), None)
    shorter = max(
        (item for item in parsed if item[1] < expiration),
        key=lambda item: item[1],
        default=None,
    )
    longer = min(
        (item for item in parsed if item[1] > expiration),
        key=lambda item: item[1],
        default=None,
    )
    candidate_iv = exact[2] if exact else None
    shorter_iv = shorter[2] if shorter else None
    longer_iv = longer[2] if longer else None
    return {
        "availability": (
            term.get("availability")
            if term.get("availability") in {"NOT_YET_AVAILABLE", "UNAVAILABLE"}
            else "AVAILABLE"
            if exact and candidate_iv is not None
            else "PARTIAL"
        ),
        "expiry": expiration.isoformat(),
        "exact_match_status": "EXACT_MATCH" if exact else "NOT_PRESENT",
        "candidate_node": exact[0] if exact else None,
        "candidate_term_iv": candidate_iv,
        "nearest_shorter_node": shorter[0] if shorter else None,
        "nearest_longer_node": longer[0] if longer else None,
        "topology": _term_topology(shorter_iv, candidate_iv, longer_iv),
    }


def _term_topology(
    shorter: float | None, candidate: float | None, longer: float | None
) -> str:
    if shorter is None or candidate is None or longer is None:
        return "INCOMPLETE"
    if candidate > shorter and candidate > longer:
        return "LOCAL_PEAK"
    if candidate < shorter and candidate < longer:
        return "LOCAL_TROUGH"
    if shorter < candidate < longer:
        return "RISING"
    if shorter > candidate > longer:
        return "FALLING"
    return "FLAT_OR_EQUAL"


def dealer_gex_context_for_expiry(
    payload: dict[str, Any] | None, *, expiration: date
) -> dict[str, Any]:
    if not payload:
        return _empty_dealer_context(expiration.isoformat())
    spot = _decimal(payload.get("spot_usd"))
    cells = []
    for raw in payload.get("cells", []):
        if not isinstance(raw, dict):
            continue
        item_expiry = _date(raw.get("expiration"))
        strike = _decimal(raw.get("strike_usd"))
        net = _decimal(raw.get("net_dealer_gex_usd"))
        if item_expiry is None or strike is None or net is None:
            continue
        cells.append((item_expiry, strike, net, raw))
    if spot is None:
        return _empty_dealer_context(expiration.isoformat(), reason="SPOT_NOT_AVAILABLE")
    anchor = [item for item in cells if item[0] == expiration]
    if not anchor:
        return _empty_dealer_context(
            expiration.isoformat(), reason="ANCHOR_EXPIRY_LADDER_NOT_AVAILABLE"
        )
    below_positive = [item for item in anchor if item[1] < spot and item[2] > 0]
    above_positive = [item for item in anchor if item[1] > spot and item[2] > 0]
    floor = max(below_positive, key=lambda item: (item[2], item[1]), default=None)
    upper = max(above_positive, key=lambda item: (item[2], -item[1]), default=None)
    below_floor = (
        max((item for item in anchor if item[1] < floor[1]), key=lambda item: item[1], default=None)
        if floor
        else None
    )
    adjacent = _adjacent_expiry_context(cells, expiration=expiration, floor=floor)
    return {
        "availability": "AVAILABLE",
        "anchor_expiry": expiration.isoformat(),
        "spot_usd": float(spot),
        "primary_floor": _gex_node(floor, spot=spot),
        "primary_upper_positive_gex_node": _gex_node(upper, spot=spot),
        "immediate_below_floor_node": _gex_node(below_floor, spot=spot),
        "adjacent_expiry_context": adjacent,
        "audit": {
            "primary_floor": {
                "rule": "MAXIMUM_POSITIVE_NET_GEX_STRICTLY_BELOW_SPOT_ON_ANCHOR_EXPIRY",
                "rule_version": PRIMARY_FLOOR_RULE_VERSION,
            },
            "primary_upper_node": {
                "rule": "MAXIMUM_POSITIVE_NET_GEX_STRICTLY_ABOVE_SPOT_ON_ANCHOR_EXPIRY",
                "rule_version": PRIMARY_UPPER_NODE_RULE_VERSION,
            },
            "below_floor_path": {
                "rule": "IMMEDIATE_LOWER_STRIKE_RAW_NODE",
                "rule_version": BELOW_FLOOR_PATH_RULE_VERSION,
            },
            "adjacent_expiry": {
                "rule": "NEAREST_PREVIOUS_AND_NEXT_AT_CANONICAL_DECIMAL_FLOOR_STRIKE",
                "rule_version": ADJACENT_EXPIRY_RULE_VERSION,
            },
        },
    }


def _adjacent_expiry_context(
    cells: list[tuple[date, Decimal, Decimal, dict[str, Any]]],
    *,
    expiration: date,
    floor: tuple[date, Decimal, Decimal, dict[str, Any]] | None,
) -> dict[str, Any]:
    expirations = sorted({item[0] for item in cells})
    previous = max((item for item in expirations if item < expiration), default=None)
    following = min((item for item in expirations if item > expiration), default=None)
    floor_strike = floor[1] if floor else None

    def same_strike(target: date | None) -> dict[str, Any] | None:
        if target is None or floor_strike is None:
            return None
        match = next(
            (item for item in cells if item[0] == target and item[1] == floor_strike),
            None,
        )
        return _gex_node(match) if match else {
            "expiration": target.isoformat(),
            "strike_usd": float(floor_strike),
            "net_dealer_gex_usd": None,
            "sign": "NOT_PRESENT",
        }

    previous_node = same_strike(previous)
    next_node = same_strike(following)
    available = [
        item
        for item in (previous_node, next_node)
        if item is not None and item.get("net_dealer_gex_usd") is not None
    ]
    signs = [item["sign"] for item in available]
    if len(signs) == 2 and signs == ["NEGATIVE", "NEGATIVE"]:
        state = "BOTH_AVAILABLE_NEGATIVE"
    elif len(signs) == 2 and signs == ["POSITIVE", "POSITIVE"]:
        state = "BOTH_AVAILABLE_POSITIVE"
    elif len(signs) == 2:
        state = "MIXED_SIGN"
    elif signs == ["NEGATIVE"]:
        state = "SINGLE_AVAILABLE_NEGATIVE"
    elif signs == ["POSITIVE"]:
        state = "SINGLE_AVAILABLE_POSITIVE"
    else:
        state = "UNAVAILABLE"
    return {
        "state": state,
        "previous": previous_node,
        "anchor": _gex_node(floor),
        "next": next_node,
        "strike_identity": "CANONICAL_DECIMAL",
        "rule_version": ADJACENT_EXPIRY_RULE_VERSION,
    }


def _gex_node(
    item: tuple[date, Decimal, Decimal, dict[str, Any]] | None,
    *,
    spot: Decimal | None = None,
) -> dict[str, Any] | None:
    if item is None:
        return None
    expiration, strike, net, raw = item
    return {
        "expiration": expiration.isoformat(),
        "strike_usd": float(strike),
        "net_dealer_gex_usd": float(net),
        "call_gex_usd": _number(raw.get("call_gex_usd")),
        "put_gex_usd": _number(raw.get("put_gex_usd")),
        "sign": "POSITIVE" if net > 0 else "NEGATIVE" if net < 0 else "ZERO",
        "distance_from_spot_usd": float(strike - spot) if spot is not None else None,
    }


def _empty_dealer_context(
    expiry: str | None,
    *,
    reason: str = "ARCHIVE_NOT_AVAILABLE",
) -> dict[str, Any]:
    return {
        "availability": "NOT_YET_AVAILABLE",
        "availability_reason": reason,
        "anchor_expiry": expiry,
        "spot_usd": None,
        "primary_floor": None,
        "primary_upper_positive_gex_node": None,
        "immediate_below_floor_node": None,
        "adjacent_expiry_context": {"state": "UNAVAILABLE"},
        "audit": {
            "primary_floor": {"rule_version": PRIMARY_FLOOR_RULE_VERSION},
            "primary_upper_node": {"rule_version": PRIMARY_UPPER_NODE_RULE_VERSION},
            "below_floor_path": {"rule_version": BELOW_FLOOR_PATH_RULE_VERSION},
            "adjacent_expiry": {"rule_version": ADJACENT_EXPIRY_RULE_VERSION},
        },
    }


def _empty_term_context(expiry: str | None) -> dict[str, Any]:
    return {
        "availability": "UNAVAILABLE",
        "expiry": expiry,
        "exact_match_status": "NOT_PRESENT",
        "candidate_node": None,
        "candidate_term_iv": None,
        "nearest_shorter_node": None,
        "nearest_longer_node": None,
        "topology": "INCOMPLETE",
    }


def _empty_strike_location() -> dict[str, Any]:
    return {
        "availability": "UNAVAILABLE",
        "strike_distance_usd": None,
        "strike_distance_pct": None,
        "strike_distance_atr": None,
        "state": None,
    }


def _vendor_implied_move(payload: dict[str, Any]) -> dict[str, Any]:
    data = _payload_data(payload)
    value = data.get("implied_move")
    if value is None:
        value = data.get("implied_move_pct")
    return {
        "availability": "AVAILABLE" if value is not None else "UNAVAILABLE",
        "vendor_value": value,
        "derived_locally": False,
    }


def _price_availability(price: dict[str, Any], *, source_state: str) -> str:
    if source_state in {"NOT_YET_AVAILABLE", "UNAVAILABLE"}:
        return source_state
    value = str(price.get("availability") or "UNAVAILABLE")
    if value in {"AVAILABLE", "AVAILABLE_WITH_GAPS"}:
        return "AVAILABLE" if value == "AVAILABLE" else "PARTIAL"
    if value in {"PARTIAL", "INSUFFICIENT_HISTORY"}:
        return "PARTIAL"
    return "UNAVAILABLE"


def _simple_availability(value: Any, *, source_state: Any = None) -> str:
    if source_state in {"NOT_YET_AVAILABLE", "UNAVAILABLE"}:
        return str(source_state)
    text = str(value or "UNAVAILABLE")
    if text in AVAILABILITY_STATES:
        return text
    if text.startswith("AVAILABLE"):
        return "AVAILABLE"
    if text in {"INSUFFICIENT_HISTORY", "HISTORY_IMMATURE"}:
        return "PARTIAL"
    return "UNAVAILABLE"


def _missing_source_provenance(
    capability: str, *, availability: str
) -> dict[str, Any]:
    return {
        "capability": capability,
        "availability": availability,
        "source_identity": None,
        "vendor_observed_at": None,
        "local_captured_at": None,
        "source_first_received_at": None,
        "freshness_anchor_at": None,
        "freshness_basis": "UNAVAILABLE",
    }


def _source_vendor_time(entry: dict[str, Any] | None) -> datetime | None:
    if not isinstance(entry, dict):
        return None
    value = entry.get("vendor_observed_at")
    if not isinstance(value, str):
        return None
    try:
        return ensure_utc(datetime.fromisoformat(value.replace("Z", "+00:00")))
    except ValueError:
        return None


def _payload_data(payload: dict[str, Any]) -> dict[str, Any]:
    data = payload.get("data")
    return data if isinstance(data, dict) else payload


def _date(value: Any) -> date | None:
    if isinstance(value, date):
        return value
    if not isinstance(value, str):
        return None
    try:
        return date.fromisoformat(value[:10])
    except ValueError:
        return None


def _decimal(value: Any) -> Decimal | None:
    if value is None or isinstance(value, bool):
        return None
    try:
        return Decimal(str(value))
    except (InvalidOperation, ValueError):
        return None


def _number(value: Any) -> float | None:
    if value is None or isinstance(value, bool):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _iso(value: datetime | None) -> str | None:
    return ensure_utc(value).isoformat() if value is not None else None

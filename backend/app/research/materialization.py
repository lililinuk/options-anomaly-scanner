from __future__ import annotations

import hashlib
import json
import math
import uuid
from collections import Counter, defaultdict
from dataclasses import asdict, dataclass
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from typing import Any

import exchange_calendars as xcals
import pandas as pd
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.confirmation.domain import canonical_regular_daily
from app.core.time import ensure_utc, market_date, utc_now
from app.db.models import (
    ContractScanObservation,
    ExpiryObservation,
    OiChangeRadarObservation,
    ProductCandidate,
    ProductCandidateContext,
    ProductCandidateTrigger,
    RawVendorPayload,
    ScanRun,
)
from app.research.forward_outcome import (
    DIRECTION,
    REFERENCE_PRICE_POLICY,
    ClosePriceEvidence,
    CorporateActionBasisStatus,
    PriceBasis,
    ResearchSampleFoundation,
    ResearchSampleValidity,
    build_research_sample_foundation,
    calculate_close_path_outcome,
    maturity_state,
)
from app.research.models import (
    ForwardOutcomeCorporateAction,
    ForwardOutcomeMeasurement,
    ForwardOutcomeResearchSample,
)

STAGE9B_PRICE_BASIS_POLICY = "RAW_REGULAR_CLOSE_RESEARCH_V1"
STAGE9B_OUTCOME_METHODOLOGY_VERSION = "stage9b.raw-regular-close-research-v1"
STAGE9B_MATERIALIZER_VERSION = "stage9b.materializer.v1"
RAW_OHLC_SELECTION_POLICY = "LATEST_PRESERVED_PAYLOAD_AS_OF_EVALUATION"
PAID_NIGHTWATCH_CALLS = 0
HORIZONS = (1, 3, 5)


@dataclass(frozen=True)
class PreservedClose:
    ticker: str
    session: date
    close: Decimal | None
    state: str
    missing_reason: str | None
    received_at: datetime
    evidence: dict[str, Any]

    def price_evidence(self) -> ClosePriceEvidence:
        return ClosePriceEvidence(
            session=self.session,
            close=self.close,
            basis=PriceBasis(
                basis_id=STAGE9B_PRICE_BASIS_POLICY,
                corporate_action_status=CorporateActionBasisStatus.RAW_UNADJUSTED,
                provenance={
                    "price_basis_policy": STAGE9B_PRICE_BASIS_POLICY,
                    "adjustment": "RAW_UNADJUSTED",
                    "selection_policy": RAW_OHLC_SELECTION_POLICY,
                },
            ),
        )


@dataclass(frozen=True)
class ProposedMeasurement:
    horizon_sessions: int
    target_session: date
    maturity_state: str
    reference_close: Decimal | None
    target_close: Decimal | None
    close_return: Decimal | None
    max_upside: Decimal | None
    max_downside: Decimal | None
    primary_descriptive_eligible: bool
    corporate_action_state: str
    corporate_action_event_ids: tuple[str, ...]
    input_bar_evidence: dict[str, Any]
    missing_sessions: tuple[tuple[date, str], ...]


@dataclass(frozen=True)
class MaterializationSummary:
    evaluated_at: str
    price_basis_policy: str
    outcome_methodology_version: str
    total_research_samples: int
    samples_inserted: int
    samples_reused: int
    primary_eligible_samples: int
    non_primary_samples_by_origin: dict[str, int]
    valid_frozen_baselines: int
    invalid_samples_by_reason: dict[str, int]
    maturity_by_horizon: dict[str, dict[str, int]]
    measurements_inserted: int
    measurements_reused: int
    outcomes_materialized_from_preserved_ohlc: int
    known_price_scale_actions: int
    contaminated_horizons: int
    residual_missing_ohlc: list[dict[str, Any]]
    trigger_count_distribution: dict[str, Any]
    per_ticker_composition: dict[str, Any]
    route_composition_counts: dict[str, int]
    paid_nightwatch_calls: int = PAID_NIGHTWATCH_CALLS
    second_forward_outcome_scheduler: str = "NO"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class PreservedOhlcCatalog:
    """Deterministic as-of view over immutable raw regular-session payload evidence."""

    def __init__(self, payloads: list[RawVendorPayload]) -> None:
        self.payload_count = len(payloads)
        self._history: dict[tuple[str, date], list[PreservedClose]] = defaultdict(list)
        for raw in sorted(payloads, key=lambda row: (ensure_utc(row.received_at), str(row.id))):
            self._ingest(raw)
        for observations in self._history.values():
            observations.sort(key=lambda row: (row.received_at, row.evidence["raw_payload_id"]))

    def lookup(
        self,
        ticker: str,
        trading_session: date,
        *,
        as_of: datetime,
    ) -> PreservedClose | None:
        cutoff = ensure_utc(as_of)
        eligible = [
            row
            for row in self._history.get((ticker.upper(), trading_session), ())
            if row.received_at <= cutoff
        ]
        return eligible[-1] if eligible else None

    def _ingest(self, raw: RawVendorPayload) -> None:
        ticker = (raw.ticker or "").upper()
        expected_endpoint = f"/v1/stocks/ohlc/{ticker}"
        if not ticker or raw.endpoint != expected_endpoint or not isinstance(raw.payload, dict):
            return
        nested = raw.payload.get("data")
        data = nested if isinstance(nested, dict) else raw.payload
        bars = data.get("bars") if isinstance(data, dict) else None
        if not isinstance(bars, list):
            return
        rows = [row for row in bars if isinstance(row, dict)]
        canonical = canonical_regular_daily(rows)
        selected = {str(row["trading_date"]): row for row in canonical.observations}
        all_dates = {
            str(row["trading_date"])
            for row in rows
            if isinstance(row.get("trading_date"), str)
        }
        for value in sorted(all_dates):
            try:
                session = date.fromisoformat(value)
            except ValueError:
                continue
            bar = selected.get(value)
            state = "AVAILABLE"
            reason: str | None = None
            close: Decimal | None = None
            if value in canonical.ambiguous_regular_dates:
                state, reason = "UNAVAILABLE", "AMBIGUOUS_REGULAR_SESSION_ROWS"
            elif value in canonical.missing_regular_dates:
                state, reason = "UNAVAILABLE", "NO_REGULAR_SESSION_ROW"
            elif bar is None:
                state, reason = "UNAVAILABLE", "NO_CANONICAL_REGULAR_SESSION_ROW"
            else:
                close = _positive_decimal(bar.get("close_usd"))
                if close is None:
                    state, reason = "UNAVAILABLE", "INVALID_OR_MISSING_RAW_CLOSE"
            evidence = {
                "raw_payload_id": str(raw.id),
                "payload_sha256": raw.payload_sha256,
                "endpoint": raw.endpoint,
                "source": raw.source,
                "request_id": raw.request_id,
                "vendor_request_id": raw.vendor_request_id,
                "payload_observed_at": _iso(raw.observed_at),
                "payload_received_at": _iso(raw.received_at),
                "trading_date": value,
                "session": "regular",
                "raw_close_usd": str(close) if close is not None else None,
                "price_basis_policy": STAGE9B_PRICE_BASIS_POLICY,
                "price_adjustment_semantics": "RAW_UNADJUSTED",
                "parser_policy": canonical.policy,
                "selection_policy": RAW_OHLC_SELECTION_POLICY,
            }
            self._history[(ticker, session)].append(
                PreservedClose(
                    ticker=ticker,
                    session=session,
                    close=close,
                    state=state,
                    missing_reason=reason,
                    received_at=ensure_utc(raw.received_at),
                    evidence=evidence,
                )
            )


class Stage9BOutcomeMaterializer:
    """Materialize Research outcomes from preserved evidence without vendor calls."""

    def __init__(self, session: Session) -> None:
        self.session = session

    def materialize(self, *, evaluated_at: datetime | None = None) -> MaterializationSummary:
        evaluated_at = ensure_utc(evaluated_at or utc_now())
        candidates = list(
            self.session.scalars(
                select(ProductCandidate)
                .options(selectinload(ProductCandidate.triggers))
                .order_by(ProductCandidate.candidate_first_knowledge_at, ProductCandidate.ticker)
            )
        )
        run_ids = {row.scan_run_id for row in candidates}
        runs = {
            row.id: row
            for row in self.session.scalars(select(ScanRun).where(ScanRun.id.in_(run_ids)))
        }
        baselines = self._baselines({row.id for row in candidates})
        tickers = {row.ticker.upper() for row in candidates}
        payloads = list(
            self.session.scalars(
                select(RawVendorPayload)
                .where(RawVendorPayload.ticker.in_(tickers))
                .order_by(RawVendorPayload.received_at, RawVendorPayload.id)
            )
        )
        catalog = PreservedOhlcCatalog(payloads)
        actions = self._active_corporate_actions(tickers)

        samples: list[tuple[ForwardOutcomeResearchSample, ResearchSampleFoundation]] = []
        inserted_samples = 0
        reused_samples = 0
        for candidate in candidates:
            run = runs.get(candidate.scan_run_id)
            if run is None:
                raise ValueError(f"Missing ScanRun for ProductCandidate {candidate.id}")
            baseline = _select_frozen_baseline(baselines.get(candidate.id, []))
            same_day_proof = catalog.lookup(
                candidate.ticker,
                market_date(candidate.candidate_first_knowledge_at),
                as_of=candidate.candidate_first_knowledge_at,
            )
            foundation = build_research_sample_foundation(
                candidate,
                run,
                baseline,
                dte_by_trigger_id=self._trigger_dtes(candidate.triggers),
                same_day_close_known_as_of_first_knowledge=(
                    same_day_proof is not None and same_day_proof.close is not None
                ),
            )
            row, inserted = self._get_or_create_sample(foundation, evaluated_at=evaluated_at)
            inserted_samples += int(inserted)
            reused_samples += int(not inserted)
            samples.append((row, foundation))

        representative_ids = _primary_representative_ids(samples)
        maturity_counts: dict[int, Counter[str]] = {horizon: Counter() for horizon in HORIZONS}
        missing: dict[tuple[str, date, str], dict[str, Any]] = {}
        inserted_measurements = 0
        reused_measurements = 0
        available_outcomes = 0
        contaminated_horizons = 0
        for sample, foundation in samples:
            for horizon in HORIZONS:
                proposal = self._propose_measurement(
                    sample,
                    foundation,
                    horizon=horizon,
                    evaluated_at=evaluated_at,
                    catalog=catalog,
                    actions=actions.get(sample.ticker, []),
                    is_primary_representative=sample.id in representative_ids,
                )
                maturity_counts[horizon][proposal.maturity_state] += 1
                available_outcomes += int(proposal.maturity_state == "MATURE_AVAILABLE")
                contaminated_horizons += int(
                    proposal.maturity_state == "CORPORATE_ACTION_CONTAMINATED"
                )
                for missing_session, reason in proposal.missing_sessions:
                    key = (sample.ticker, missing_session, reason)
                    entry = missing.setdefault(
                        key,
                        {
                            "ticker": sample.ticker,
                            "session": missing_session.isoformat(),
                            "reason": reason,
                            "horizons": set(),
                            "research_sample_ids": set(),
                        },
                    )
                    entry["horizons"].add(horizon)
                    entry["research_sample_ids"].add(str(sample.id))
                inserted = self._append_measurement_if_changed(
                    sample, proposal, evaluated_at=evaluated_at
                )
                inserted_measurements += int(inserted)
                reused_measurements += int(not inserted)

        self.session.flush()
        foundations = [item[1] for item in samples]
        invalid = Counter(
            row.invalid_reason or "UNSPECIFIED_INVALID_SAMPLE"
            for row in foundations
            if row.sample_validity_state is ResearchSampleValidity.INVALID_SAMPLE
        )
        non_primary = Counter(
            row.run_origin.value for row in foundations if not row.primary_research_eligible
        )
        residual = []
        for entry in sorted(missing.values(), key=lambda row: (row["ticker"], row["session"])):
            residual.append(
                {
                    **entry,
                    "horizons": sorted(entry["horizons"]),
                    "research_sample_ids": sorted(entry["research_sample_ids"]),
                }
            )
        return MaterializationSummary(
            evaluated_at=evaluated_at.isoformat(),
            price_basis_policy=STAGE9B_PRICE_BASIS_POLICY,
            outcome_methodology_version=STAGE9B_OUTCOME_METHODOLOGY_VERSION,
            total_research_samples=len(samples),
            samples_inserted=inserted_samples,
            samples_reused=reused_samples,
            primary_eligible_samples=sum(row.primary_research_eligible for row in foundations),
            non_primary_samples_by_origin=dict(sorted(non_primary.items())),
            valid_frozen_baselines=sum(
                row.sample_validity_state is ResearchSampleValidity.VALID
                for row in foundations
            ),
            invalid_samples_by_reason=dict(sorted(invalid.items())),
            maturity_by_horizon={
                str(horizon): dict(sorted(maturity_counts[horizon].items()))
                for horizon in HORIZONS
            },
            measurements_inserted=inserted_measurements,
            measurements_reused=reused_measurements,
            outcomes_materialized_from_preserved_ohlc=available_outcomes,
            known_price_scale_actions=sum(len(rows) for rows in actions.values()),
            contaminated_horizons=contaminated_horizons,
            residual_missing_ohlc=residual,
            trigger_count_distribution=_trigger_count_distribution(
                samples, representative_ids=representative_ids
            ),
            per_ticker_composition=_per_ticker_composition(foundations),
            route_composition_counts=dict(
                sorted(
                    Counter(
                        row.cohort.route_composition.value
                        if row.cohort.route_composition is not None
                        else "NONE"
                        for row in foundations
                    ).items()
                )
            ),
        )

    def _baselines(
        self, candidate_ids: set[uuid.UUID]
    ) -> dict[uuid.UUID, list[ProductCandidateContext]]:
        result: dict[uuid.UUID, list[ProductCandidateContext]] = defaultdict(list)
        rows = self.session.scalars(
            select(ProductCandidateContext)
            .where(
                ProductCandidateContext.product_candidate_id.in_(candidate_ids),
                ProductCandidateContext.evaluation_kind == "FIRST_KNOWLEDGE_BASELINE",
            )
            .order_by(
                ProductCandidateContext.context_evaluated_at,
                ProductCandidateContext.id,
            )
        )
        for row in rows:
            result[row.product_candidate_id].append(row)
        return result

    def _trigger_dtes(
        self, triggers: list[ProductCandidateTrigger]
    ) -> dict[uuid.UUID, int | None]:
        result: dict[uuid.UUID, int | None] = {}
        for trigger in triggers:
            value: int | None = None
            if trigger.evidence_family == "RADAR_EVENT":
                source = self.session.get(
                    OiChangeRadarObservation, trigger.source_radar_observation_id
                )
                value = source.matched_dte if source is not None else None
            elif trigger.evidence_family == "EXPIRY_ACTIVITY":
                source = self.session.get(
                    ExpiryObservation, trigger.source_expiry_observation_id
                )
                value = source.dte_at_detection if source is not None else None
            elif trigger.evidence_family == "CONTRACT_PERSISTENCE":
                source = self.session.get(
                    ContractScanObservation, trigger.source_contract_observation_id
                )
                value = source.dte_at_detection if source is not None else None
            result[trigger.id] = value
        return result

    def _get_or_create_sample(
        self,
        foundation: ResearchSampleFoundation,
        *,
        evaluated_at: datetime,
    ) -> tuple[ForwardOutcomeResearchSample, bool]:
        existing = self.session.scalar(
            select(ForwardOutcomeResearchSample).where(
                ForwardOutcomeResearchSample.product_candidate_id
                == foundation.product_candidate_id
            )
        )
        values = _sample_values(foundation)
        if existing is not None:
            for field, expected in values.items():
                if getattr(existing, field) != expected:
                    raise ValueError(
                        f"Immutable Stage 9 sample conflict for "
                        f"{foundation.product_candidate_id}: {field}"
                    )
            return existing, False
        row = ForwardOutcomeResearchSample(
            id=uuid.uuid4(),
            **values,
            created_at=evaluated_at,
        )
        self.session.add(row)
        self.session.flush()
        return row, True

    def _active_corporate_actions(
        self, tickers: set[str]
    ) -> dict[str, list[ForwardOutcomeCorporateAction]]:
        latest: dict[tuple[Any, ...], ForwardOutcomeCorporateAction] = {}
        rows = self.session.scalars(
            select(ForwardOutcomeCorporateAction)
            .where(ForwardOutcomeCorporateAction.ticker.in_(tickers))
            .order_by(
                ForwardOutcomeCorporateAction.ticker,
                ForwardOutcomeCorporateAction.effective_session,
                ForwardOutcomeCorporateAction.record_revision,
                ForwardOutcomeCorporateAction.id,
            )
        )
        for row in rows:
            key = (
                row.ticker,
                row.effective_session,
                row.action_type,
                row.source_name,
                row.source_reference,
            )
            latest[key] = row
        result: dict[str, list[ForwardOutcomeCorporateAction]] = defaultdict(list)
        for row in latest.values():
            if row.record_status == "KNOWN" and row.price_scale_changing:
                result[row.ticker].append(row)
        for rows in result.values():
            rows.sort(key=lambda row: (row.effective_session, str(row.id)))
        return result

    def _propose_measurement(
        self,
        sample: ForwardOutcomeResearchSample,
        foundation: ResearchSampleFoundation,
        *,
        horizon: int,
        evaluated_at: datetime,
        catalog: PreservedOhlcCatalog,
        actions: list[ForwardOutcomeCorporateAction],
        is_primary_representative: bool,
    ) -> ProposedMeasurement:
        target_session = _target_session(foundation, horizon)
        path_sessions = _future_sessions(foundation.sessions.t1_session, target_session)
        relevant_actions = [
            row
            for row in actions
            if foundation.sessions.reference_session < row.effective_session <= target_session
        ]
        action_ids = tuple(str(row.id) for row in relevant_actions)
        if foundation.sample_validity_state is ResearchSampleValidity.INVALID_SAMPLE:
            return ProposedMeasurement(
                horizon,
                target_session,
                "INVALID_SAMPLE",
                None,
                None,
                None,
                None,
                None,
                False,
                "NOT_APPLICABLE",
                action_ids,
                {},
                (),
            )
        temporal_state = maturity_state(
            target_session,
            evaluated_at=evaluated_at,
            close_present=True,
        ).value
        if temporal_state == "NOT_YET_MATURE":
            return ProposedMeasurement(
                horizon,
                target_session,
                temporal_state,
                None,
                None,
                None,
                None,
                None,
                False,
                (
                    "KNOWN_PRICE_SCALE_EVENT"
                    if relevant_actions
                    else "NO_KNOWN_PRICE_SCALE_EVENT_RECORDED"
                ),
                action_ids,
                {},
                (),
            )

        required_sessions = [foundation.sessions.reference_session, *path_sessions]
        selected: list[PreservedClose | None] = [
            catalog.lookup(sample.ticker, item, as_of=evaluated_at)
            for item in required_sessions
        ]
        evidence: dict[str, Any] = {}
        missing: list[tuple[date, str]] = []
        for session_date, row in zip(required_sessions, selected, strict=True):
            if row is None:
                reason = "NO_PRESERVED_REGULAR_CLOSE"
                evidence[session_date.isoformat()] = {
                    "availability": "MISSING",
                    "reason": reason,
                    "price_basis_policy": STAGE9B_PRICE_BASIS_POLICY,
                }
                missing.append((session_date, reason))
            elif row.close is None:
                reason = row.missing_reason or "RAW_CLOSE_UNAVAILABLE"
                evidence[session_date.isoformat()] = {
                    **row.evidence,
                    "availability": "MISSING",
                    "reason": reason,
                }
                missing.append((session_date, reason))
            else:
                evidence[session_date.isoformat()] = {
                    **row.evidence,
                    "availability": "AVAILABLE",
                }
        reference = selected[0]
        target = selected[-1]
        reference_close = reference.close if reference is not None else None
        target_close = target.close if target is not None else None
        if relevant_actions:
            return ProposedMeasurement(
                horizon,
                target_session,
                "CORPORATE_ACTION_CONTAMINATED",
                reference_close,
                target_close,
                None,
                None,
                None,
                False,
                "KNOWN_PRICE_SCALE_EVENT",
                action_ids,
                evidence,
                tuple(missing),
            )
        if missing:
            return ProposedMeasurement(
                horizon,
                target_session,
                "MATURE_MISSING_DATA",
                reference_close,
                target_close,
                None,
                None,
                None,
                False,
                "NO_KNOWN_PRICE_SCALE_EVENT_RECORDED",
                (),
                evidence,
                tuple(missing),
            )
        assert reference is not None
        future = [row for row in selected[1:] if row is not None]
        metrics = calculate_close_path_outcome(
            reference.price_evidence(),
            [row.price_evidence() for row in future],
        )
        if metrics is None:
            raise ValueError("Complete preserved Close path unexpectedly produced no outcome")
        return ProposedMeasurement(
            horizon,
            target_session,
            "MATURE_AVAILABLE",
            reference.close,
            future[-1].close,
            metrics.close_return,
            metrics.max_upside,
            metrics.max_downside,
            foundation.primary_research_eligible and is_primary_representative,
            "NO_KNOWN_PRICE_SCALE_EVENT_RECORDED",
            (),
            evidence,
            (),
        )

    def _append_measurement_if_changed(
        self,
        sample: ForwardOutcomeResearchSample,
        proposal: ProposedMeasurement,
        *,
        evaluated_at: datetime,
    ) -> bool:
        fingerprint = _measurement_fingerprint(proposal)
        latest = self.session.scalar(
            select(ForwardOutcomeMeasurement)
            .where(
                ForwardOutcomeMeasurement.research_sample_id == sample.id,
                ForwardOutcomeMeasurement.horizon_sessions == proposal.horizon_sessions,
                ForwardOutcomeMeasurement.outcome_methodology_version
                == STAGE9B_OUTCOME_METHODOLOGY_VERSION,
            )
            .order_by(
                ForwardOutcomeMeasurement.calculation_revision.desc(),
                ForwardOutcomeMeasurement.id.desc(),
            )
            .limit(1)
        )
        if latest is not None and latest.semantic_fingerprint == fingerprint:
            return False
        revision = 1 if latest is None else latest.calculation_revision + 1
        self.session.add(
            ForwardOutcomeMeasurement(
                id=uuid.uuid4(),
                research_sample_id=sample.id,
                horizon_sessions=proposal.horizon_sessions,
                target_session=proposal.target_session,
                maturity_state=proposal.maturity_state,
                reference_close=proposal.reference_close,
                target_close=proposal.target_close,
                close_return=proposal.close_return,
                max_upside=proposal.max_upside,
                max_downside=proposal.max_downside,
                price_basis_status="RAW_UNADJUSTED",
                price_basis_name=STAGE9B_PRICE_BASIS_POLICY,
                price_basis_provenance={
                    "price_basis_policy": STAGE9B_PRICE_BASIS_POLICY,
                    "adjustment": "RAW_UNADJUSTED",
                    "claim_exclusions": [
                        "ADJUSTED_RETURN",
                        "TOTAL_RETURN",
                        "CORPORATE_ACTION_CONSISTENT_RETURN",
                    ],
                    "selection_policy": RAW_OHLC_SELECTION_POLICY,
                },
                input_bar_evidence=proposal.input_bar_evidence,
                primary_descriptive_eligible=proposal.primary_descriptive_eligible,
                corporate_action_state=proposal.corporate_action_state,
                corporate_action_event_ids=list(proposal.corporate_action_event_ids),
                outcome_methodology_version=STAGE9B_OUTCOME_METHODOLOGY_VERSION,
                calculation_revision=revision,
                semantic_fingerprint=fingerprint,
                supersedes_measurement_id=latest.id if latest is not None else None,
                calculated_at=evaluated_at,
                direction=DIRECTION,
                provenance={
                    "materializer_version": STAGE9B_MATERIALIZER_VERSION,
                    "reference_price_policy": REFERENCE_PRICE_POLICY,
                    "horizon_sessions": proposal.horizon_sessions,
                    "close_path_only": True,
                    "direction": DIRECTION,
                    "paid_nightwatch_calls": 0,
                },
                created_at=evaluated_at,
            )
        )
        self.session.flush()
        return True


def _sample_values(foundation: ResearchSampleFoundation) -> dict[str, Any]:
    return {
        "product_candidate_id": foundation.product_candidate_id,
        "frozen_baseline_context_id": foundation.frozen_baseline_context_id,
        "scan_run_id": foundation.scan_run_id,
        "ticker": foundation.ticker.upper(),
        "candidate_first_knowledge_at": foundation.candidate_first_knowledge_at,
        "sample_validity_state": foundation.sample_validity_state.value,
        "invalid_reason": foundation.invalid_reason,
        "run_origin": foundation.run_origin.value,
        "run_origin_source_trigger": foundation.run_origin_source_trigger,
        "run_origin_classification_version": foundation.run_origin_classification_version,
        "primary_research_eligible": foundation.primary_research_eligible,
        "has_radar": foundation.cohort.has_radar,
        "has_expiry_activity": foundation.cohort.has_expiry_activity,
        "has_contract_persistence": foundation.cohort.has_contract_persistence,
        "route_composition": (
            foundation.cohort.route_composition.value
            if foundation.cohort.route_composition is not None
            else None
        ),
        "qualifying_trigger_count": foundation.cohort.qualifying_trigger_count,
        "dte_bucket_counts": dict(foundation.cohort.dte_bucket_counts),
        "reference_price_policy": REFERENCE_PRICE_POLICY,
        "reference_session": foundation.sessions.reference_session,
        "t1_session": foundation.sessions.t1_session,
        "t3_session": foundation.sessions.t3_session,
        "t5_session": foundation.sessions.t5_session,
        "outcome_window_key": foundation.outcome_window_key,
        "price_basis_capability": "RAW_UNADJUSTED",
        "price_basis_name": STAGE9B_PRICE_BASIS_POLICY,
        "price_basis_provenance": {
            "price_basis_policy": STAGE9B_PRICE_BASIS_POLICY,
            "adjustment": "RAW_UNADJUSTED",
            "regular_session_only": True,
            "parser": "app.confirmation.domain.canonical_regular_daily",
            "selection_policy": RAW_OHLC_SELECTION_POLICY,
            "known_corporate_action_limitation": (
                "Only recorded known price-scale-changing events are quarantined"
            ),
        },
        "outcome_methodology_version": STAGE9B_OUTCOME_METHODOLOGY_VERSION,
        "direction": DIRECTION,
    }


def _select_frozen_baseline(
    rows: list[ProductCandidateContext],
) -> ProductCandidateContext | None:
    if not rows:
        return None
    return min(rows, key=lambda row: (ensure_utc(row.context_evaluated_at), str(row.id)))


def _primary_representative_ids(
    samples: list[tuple[ForwardOutcomeResearchSample, ResearchSampleFoundation]],
) -> set[uuid.UUID]:
    groups: dict[str, list[tuple[ForwardOutcomeResearchSample, ResearchSampleFoundation]]] = (
        defaultdict(list)
    )
    for pair in samples:
        if pair[1].primary_research_eligible:
            groups[pair[1].outcome_window_key].append(pair)
    result: set[uuid.UUID] = set()
    for rows in groups.values():
        selected = min(
            rows,
            key=lambda pair: (
                pair[1].candidate_first_knowledge_at,
                str(pair[1].product_candidate_id),
            ),
        )
        result.add(selected[0].id)
    return result


def _target_session(foundation: ResearchSampleFoundation, horizon: int) -> date:
    return {
        1: foundation.sessions.t1_session,
        3: foundation.sessions.t3_session,
        5: foundation.sessions.t5_session,
    }[horizon]


def _future_sessions(first: date, target: date) -> list[date]:
    calendar = xcals.get_calendar("XNYS")
    labels = calendar.sessions_in_range(
        pd.Timestamp(first.isoformat()),
        pd.Timestamp(target.isoformat()),
    )
    return [label.date() for label in labels]


def _measurement_fingerprint(proposal: ProposedMeasurement) -> str:
    payload = {
        "horizon_sessions": proposal.horizon_sessions,
        "target_session": proposal.target_session.isoformat(),
        "maturity_state": proposal.maturity_state,
        "reference_close": _decimal_string(proposal.reference_close),
        "target_close": _decimal_string(proposal.target_close),
        "close_return": _decimal_string(proposal.close_return),
        "max_upside": _decimal_string(proposal.max_upside),
        "max_downside": _decimal_string(proposal.max_downside),
        "primary_descriptive_eligible": proposal.primary_descriptive_eligible,
        "corporate_action_state": proposal.corporate_action_state,
        "corporate_action_event_ids": list(proposal.corporate_action_event_ids),
        "input_bar_evidence": proposal.input_bar_evidence,
        "price_basis_policy": STAGE9B_PRICE_BASIS_POLICY,
        "outcome_methodology_version": STAGE9B_OUTCOME_METHODOLOGY_VERSION,
    }
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(encoded).hexdigest()


def _trigger_count_distribution(
    samples: list[tuple[ForwardOutcomeResearchSample, ResearchSampleFoundation]],
    *,
    representative_ids: set[uuid.UUID],
) -> dict[str, Any]:
    canonical = [pair for pair in samples if pair[1].primary_research_eligible]
    representatives = [pair for pair in canonical if pair[0].id in representative_ids]
    by_ticker: dict[str, list[int]] = defaultdict(list)
    by_route: dict[str, list[int]] = defaultdict(list)
    for _row, foundation in canonical:
        by_ticker[foundation.ticker].append(foundation.cohort.qualifying_trigger_count)
        route = (
            foundation.cohort.route_composition.value
            if foundation.cohort.route_composition is not None
            else "NONE"
        )
        by_route[route].append(foundation.cohort.qualifying_trigger_count)
    non_primary_context = [
        pair[1].cohort.qualifying_trigger_count
        for pair in samples
        if not pair[1].primary_research_eligible
    ]
    return {
        "population": "CANONICAL_SCHEDULED_PRODUCTION_PRODUCT_CANDIDATES",
        "percentile_method": "LINEAR_INTERPOLATION_ON_SORTED_VALUES",
        "canonical_occurrences": _distribution(
            [pair[1].cohort.qualifying_trigger_count for pair in canonical]
        ),
        "primary_aggregate_representatives": _distribution(
            [pair[1].cohort.qualifying_trigger_count for pair in representatives]
        ),
        "defensive_duplicate_occurrences": len(canonical) - len(representatives),
        "by_ticker": {key: _distribution(value) for key, value in sorted(by_ticker.items())},
        "by_route_composition": {
            key: _distribution(value) for key, value in sorted(by_route.items())
        },
        "non_primary_context_only": _distribution(non_primary_context),
        "trigger_count_buckets_hardcoded": False,
    }


def _distribution(values: list[int]) -> dict[str, Any]:
    ordered = sorted(values)
    if not ordered:
        return {
            "n": 0,
            "min": None,
            "p25": None,
            "median": None,
            "p75": None,
            "p90": None,
            "max": None,
        }
    return {
        "n": len(ordered),
        "min": ordered[0],
        "p25": _percentile(ordered, 0.25),
        "median": _percentile(ordered, 0.5),
        "p75": _percentile(ordered, 0.75),
        "p90": _percentile(ordered, 0.9),
        "max": ordered[-1],
    }


def _percentile(ordered: list[int], fraction: float) -> int | float:
    position = (len(ordered) - 1) * fraction
    lower = math.floor(position)
    upper = math.ceil(position)
    if lower == upper:
        return ordered[lower]
    result = ordered[lower] + (ordered[upper] - ordered[lower]) * (position - lower)
    return int(result) if result.is_integer() else round(result, 6)


def _per_ticker_composition(
    foundations: list[ResearchSampleFoundation],
) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for ticker in sorted({row.ticker for row in foundations}):
        rows = [row for row in foundations if row.ticker == ticker]
        result[ticker] = {
            "research_samples": len(rows),
            "primary_eligible_samples": sum(row.primary_research_eligible for row in rows),
            "qualifying_trigger_count_total": sum(
                row.cohort.qualifying_trigger_count for row in rows
            ),
            "route_composition_counts": dict(
                sorted(
                    Counter(
                        row.cohort.route_composition.value
                        if row.cohort.route_composition is not None
                        else "NONE"
                        for row in rows
                    ).items()
                )
            ),
        }
    return result


def _positive_decimal(value: Any) -> Decimal | None:
    if value is None or isinstance(value, bool):
        return None
    try:
        parsed = Decimal(str(value))
    except (InvalidOperation, ValueError):
        return None
    return parsed if parsed > 0 else None


def _decimal_string(value: Decimal | None) -> str | None:
    return str(value) if value is not None else None


def _iso(value: datetime | None) -> str | None:
    return ensure_utc(value).isoformat() if value is not None else None

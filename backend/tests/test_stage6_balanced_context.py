from __future__ import annotations

import inspect
import json
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from types import SimpleNamespace
from typing import Any
from uuid import uuid4

import pytest
from sqlalchemy import CheckConstraint, Index, UniqueConstraint

import app.api.routes.candidate_contexts as candidate_routes
import app.confirmation.vnext as vnext
from app.confirmation.provenance import EvaluationIdentity
from app.confirmation.vnext import (
    IV_RANK_CORE_ELIGIBILITY,
    PHASE2B_VNEXT_SPEC_VERSION,
    SOURCE_ENDPOINTS,
    SourceBundle,
    Stage6BalancedContextService,
    TriggerDescriptor,
    _missing_source_provenance,
    _normalize_iv_rank,
    _normalize_term_structure,
    context_public,
    dealer_gex_context_for_expiry,
    stage6_config_hash,
    term_context_for_expiry,
)
from app.db.models import (
    AnomalyContextDetail,
    ContractOiDailySnapshot,
    ContractScanObservation,
    ExpiryObservation,
    Phase2bCandidateEvaluation,
    Phase2bCandidateState,
    Phase2bTickerContextSnapshot,
    Phase2bV3ResearchWorkspace,
    ProductCandidate,
    ProductCandidateContext,
    ProductCandidateTrigger,
    RawVendorPayload,
    StrikeCluster,
)

UTC = timezone.utc
FIRST_KNOWN = datetime(2026, 8, 18, 20, 0, tzinfo=UTC)
EVALUATED = FIRST_KNOWN + timedelta(minutes=5)
POST_FIRST_KNOWLEDGE = FIRST_KNOWN + timedelta(minutes=5)
DELAYED_EVALUATED = FIRST_KNOWN + timedelta(minutes=10)
EXPIRY = date(2026, 8, 21)
TICKER = "NVDA"
CANDIDATE_ID = uuid4()


def _bars(count: int = 60) -> list[dict[str, object]]:
    return [
        {
            "trading_date": (date(2026, 1, 2) + timedelta(days=index)).isoformat(),
            "session": "regular",
            "open_usd": 99.5 + index,
            "high_usd": 101.0 + index,
            "low_usd": 99.0 + index,
            "close_usd": 100.0 + index,
        }
        for index in range(count)
    ]


def _trigger(
    family: str,
    entity: str,
    identity: str,
    *,
    source_id: Any | None = None,
) -> ProductCandidateTrigger:
    source_id = source_id or uuid4()
    return ProductCandidateTrigger(
        id=uuid4(),
        product_candidate_id=CANDIDATE_ID,
        evidence_family=family,
        anomaly_entity_type=entity,
        anomaly_identity=identity,
        source_evidence_identity=f"{family.lower()}:{source_id}",
        qualifies_candidate=True,
        present_at_first_knowledge=True,
        event_date=date(2026, 8, 18),
        trigger_first_knowledge_at=FIRST_KNOWN - timedelta(minutes=1),
        source_first_received_at=FIRST_KNOWN - timedelta(minutes=2),
        vendor_observed_at=None,
        local_captured_at=FIRST_KNOWN - timedelta(minutes=2),
        source_ids={"source_request_ids": [f"request-{source_id}"]},
        provenance={},
        specification_version="phase2a_vnext_stage4b",
        created_at=FIRST_KNOWN,
    )


def _candidate(triggers: list[ProductCandidateTrigger]) -> ProductCandidate:
    candidate = ProductCandidate(
        id=CANDIDATE_ID,
        scan_run_id=uuid4(),
        ticker=TICKER,
        candidate_first_knowledge_at=FIRST_KNOWN,
        materialization_rule_version="phase2a_vnext_stage4b.product-candidate-materialization.v1",
        materialization_rule_hash="a" * 64,
        lifecycle_state="MATERIALIZED",
        created_at=FIRST_KNOWN,
    )
    candidate.triggers = triggers
    return candidate


def _sources(*, close_offset: int = 0) -> SourceBundle:
    source_time = "2026-08-18T19:59:00+00:00"
    available = {
        "availability": "AVAILABLE",
        "vendor_observed_at": source_time,
        "local_captured_at": source_time,
        "source_first_received_at": source_time,
    }
    return SourceBundle(
        payloads={
            "daily_ohlc": {"data": {"as_of": source_time, "bars": _bars(60)}},
            "stock_state": {
                "data": {
                    "close_usd": 159 + close_offset,
                    "prev_close_usd": 158,
                    "as_of": source_time,
                }
            },
            "iv_rank": {"data": {"iv_rank": 42, "as_of": source_time}},
            "term_structure": {
                "data": {
                    "nodes": [
                        {"expiry": "2026-08-14", "implied_vol_pct": 31.0},
                        {"expiry": "2026-08-21", "implied_vol_pct": 35.0},
                        {"expiry": "2026-08-28", "implied_vol_pct": 33.0},
                    ]
                }
            },
        },
        provenance={name: {**available, "capability": name} for name, *_ in SOURCE_ENDPOINTS},
        statuses={name: {"availability": "AVAILABLE"} for name, *_ in SOURCE_ENDPOINTS},
    )


class RecordingSession:
    def __init__(self) -> None:
        self.added: list[Any] = []
        self.flushes = 0
        self.writes = 0
        self.statements: list[Any] = []
        self.scalar_values: list[Any] = []
        self.scalars_values: list[list[Any]] = []

    def add(self, row: Any) -> None:
        self.writes += 1
        if isinstance(row, RawVendorPayload) and row.id is None:
            row.id = uuid4()
        self.added.append(row)

    def flush(self) -> None:
        self.writes += 1
        self.flushes += 1

    def commit(self) -> None:
        self.writes += 1

    def rollback(self) -> None:
        return None

    def scalar(self, statement: Any) -> Any:
        self.statements.append(statement)
        return self.scalar_values.pop(0) if self.scalar_values else None

    def scalars(self, statement: Any) -> list[Any]:
        self.statements.append(statement)
        return self.scalars_values.pop(0) if self.scalars_values else []

    def get(self, _model: Any, _identity: Any) -> Any:
        return None


def _raw_source(
    name: str,
    request_id: str,
    *,
    received_at: datetime,
    observed_at: datetime | None,
    payload: dict[str, Any],
) -> RawVendorPayload:
    template = next(template for source, template, _params in SOURCE_ENDPOINTS if source == name)
    return RawVendorPayload(
        id=uuid4(),
        source="nightwatch",
        endpoint=template.format(ticker=TICKER),
        request_id=request_id,
        ticker=TICKER,
        observed_at=observed_at,
        received_at=received_at,
        payload_sha256=request_id[0].lower() * 64,
        payload=payload,
    )


class RawTimelineSession(RecordingSession):
    def __init__(self, rows: list[RawVendorPayload]) -> None:
        super().__init__()
        self.rows = rows

    def scalar(self, statement: Any) -> Any:
        self.statements.append(statement)
        params = statement.compile().params
        endpoint = next((value for key, value in params.items() if "endpoint" in key), None)
        ticker = next((value for key, value in params.items() if "ticker" in key), None)
        cutoff = next(
            (
                value
                for key, value in params.items()
                if "received_at" in key and isinstance(value, datetime)
            ),
            None,
        )
        if endpoint is None or ticker is None or cutoff is None:
            return None
        eligible = [
            row
            for row in self.rows
            if row.endpoint == endpoint
            and row.ticker == ticker
            and row.received_at <= cutoff
            and (row.observed_at is None or row.observed_at <= cutoff)
        ]
        return max(eligible, key=lambda row: row.received_at, default=None)


class ChainTimelineSession(RecordingSession):
    def __init__(
        self,
        rows: list[ContractOiDailySnapshot],
        raw_by_id: dict[Any, RawVendorPayload],
    ) -> None:
        super().__init__()
        self.rows = rows
        self.raw_by_id = raw_by_id

    def scalars(self, statement: Any) -> list[ContractOiDailySnapshot]:
        self.statements.append(statement)
        params = statement.compile().params
        cutoff = next(value for value in params.values() if isinstance(value, datetime))
        eligible = []
        for row in self.rows:
            raw = self.raw_by_id[row.raw_payload_id]
            if (
                row.vendor_oi_as_of <= cutoff
                and raw.received_at <= cutoff
                and (raw.observed_at is None or raw.observed_at <= cutoff)
                and (row.quote_as_of is None or row.quote_as_of <= cutoff)
                and (row.greeks_as_of is None or row.greeks_as_of <= cutoff)
            ):
                eligible.append(row)
        return sorted(eligible, key=lambda row: row.vendor_oi_as_of, reverse=True)


class SourceCutoffHarness(Stage6BalancedContextService):
    def __init__(
        self,
        session: RawTimelineSession,
        candidate: ProductCandidate,
        *,
        refresh_at: datetime,
    ) -> None:
        super().__init__(session, client=object())  # type: ignore[arg-type]
        self.probe_candidate = candidate
        self.refresh_at = refresh_at

    def _candidate(self, _candidate_id: Any) -> ProductCandidate:
        return self.probe_candidate

    def _baseline(self, _candidate_id: Any) -> None:
        return None

    async def _fetch_source_bundle(self, ticker: str) -> SourceBundle:
        return self._archived_source_bundle(
            ticker,
            evidence_cutoff_at=self.refresh_at,
        )

    def _persist_evaluation(self, candidate: ProductCandidate, **kwargs: Any) -> Any:
        assert candidate is self.probe_candidate
        return SimpleNamespace(**kwargs)


def _source_cutoff_harness() -> SourceCutoffHarness:
    before_t0 = FIRST_KNOWN - timedelta(minutes=1)
    rows = [
        _raw_source(
            "daily_ohlc",
            "A-before-t0",
            received_at=before_t0,
            observed_at=FIRST_KNOWN - timedelta(minutes=2),
            payload={
                "data": {
                    "as_of": (FIRST_KNOWN - timedelta(minutes=2)).isoformat(),
                    "bars": [
                        {
                            "trading_date": "2026-08-18",
                            "session": "regular",
                            "close_usd": 100,
                        }
                    ],
                }
            },
        ),
        _raw_source(
            "daily_ohlc",
            "B-after-t0",
            received_at=POST_FIRST_KNOWLEDGE,
            observed_at=POST_FIRST_KNOWLEDGE - timedelta(minutes=1),
            payload={
                "data": {
                    "as_of": (POST_FIRST_KNOWLEDGE - timedelta(minutes=1)).isoformat(),
                    "bars": [
                        {
                            "trading_date": "2026-08-18",
                            "session": "regular",
                            "close_usd": 200,
                        }
                    ],
                }
            },
        ),
        _raw_source(
            "term_structure",
            "T-after-t0",
            received_at=POST_FIRST_KNOWLEDGE,
            observed_at=POST_FIRST_KNOWLEDGE - timedelta(minutes=1),
            payload={"data": {"nodes": [{"expiry": EXPIRY.isoformat(), "dte": 3}]}},
        ),
    ]
    candidate = _candidate([])
    return SourceCutoffHarness(
        RawTimelineSession(rows),
        candidate,
        refresh_at=DELAYED_EVALUATED,
    )


class EvaluationHarness(Stage6BalancedContextService):
    def __init__(
        self,
        session: RecordingSession,
        descriptors: dict[Any, TriggerDescriptor],
        chains: dict[str, ContractOiDailySnapshot],
    ) -> None:
        super().__init__(session)  # type: ignore[arg-type]
        self.descriptors = descriptors
        self.chains = chains
        self.chain_loads: list[date] = []

    def _trigger_descriptor(self, trigger: ProductCandidateTrigger) -> TriggerDescriptor:
        return self.descriptors[trigger.id]

    def _chain_context(
        self,
        ticker: str,
        *,
        expiration: date,
        evidence_cutoff_at: datetime,
    ) -> dict[str, ContractOiDailySnapshot]:
        assert ticker == TICKER
        assert evidence_cutoff_at >= FIRST_KNOWN
        self.chain_loads.append(expiration)
        return self.chains

    def _deep_dive(
        self,
        candidate: ProductCandidate,
        descriptor: TriggerDescriptor,
    ) -> dict[str, Any]:
        assert candidate.ticker == TICKER
        if descriptor.trigger.anomaly_entity_type == "CONTRACT":
            return {
                "availability": "AVAILABLE",
                "structure": {"classification": "STRONG_STRUCTURE"},
            }
        return {"availability": "UNAVAILABLE", "structures": [], "valid_clusters": []}


def _evaluation_fixture() -> tuple[
    RecordingSession,
    EvaluationHarness,
    ProductCandidate,
]:
    radar = _trigger("RADAR_EVENT", "CONTRACT", "NVDA260821C00160000")
    persistence = _trigger(
        "CONTRACT_PERSISTENCE",
        "CONTRACT",
        "NVDA260821P00150000",
    )
    expiry = _trigger("EXPIRY_ACTIVITY", "EXPIRY", EXPIRY.isoformat())
    candidate = _candidate([radar, expiry, persistence])
    expiry_source = SimpleNamespace(
        expiration=EXPIRY,
        dte_at_detection=3,
        call_volume=100,
        put_volume=80,
        call_oi=1000,
        put_oi=900,
        same_day_activity_score=77,
        same_day_score_basis="VOLUME_SHARE_ONLY",
    )
    descriptors = {
        radar.id: TriggerDescriptor(radar, EXPIRY, "C", vnext.Decimal("160"), 3, None),
        persistence.id: TriggerDescriptor(
            persistence,
            EXPIRY,
            "P",
            vnext.Decimal("150"),
            3,
            None,
        ),
        expiry.id: TriggerDescriptor(expiry, EXPIRY, None, None, 3, expiry_source),
    }
    chains = {
        radar.anomaly_identity: ContractOiDailySnapshot(
            contract_symbol=radar.anomaly_identity,
            bid=vnext.Decimal("4.00"),
            ask=vnext.Decimal("4.40"),
            implied_volatility=vnext.Decimal("0.44"),
            delta=vnext.Decimal("0.52"),
            quote_as_of=EVALUATED - timedelta(minutes=2),
            raw_payload_id=uuid4(),
            source_request_id="chain-radar",
        ),
        persistence.anomaly_identity: ContractOiDailySnapshot(
            contract_symbol=persistence.anomaly_identity,
            bid=vnext.Decimal("3.00"),
            ask=vnext.Decimal("3.60"),
            implied_volatility=vnext.Decimal("0.41"),
            delta=vnext.Decimal("-0.38"),
            quote_as_of=EVALUATED - timedelta(minutes=2),
            raw_payload_id=uuid4(),
            source_request_id="chain-persistence",
        ),
    }
    session = RecordingSession()
    return session, EvaluationHarness(session, descriptors, chains), candidate


def test_stage6_models_and_migration_express_additive_identity() -> None:
    assert ProductCandidateContext.__tablename__ == "product_candidate_contexts"
    assert AnomalyContextDetail.__tablename__ == "anomaly_context_details"
    constraints = ProductCandidateContext.__table__.constraints
    assert any(
        isinstance(item, CheckConstraint)
        and item.name is not None
        and item.name.endswith("product_candidate_context_time_order")
        for item in constraints
    )
    assert any(
        isinstance(item, Index)
        and item.name == "uq_product_candidate_stage6_baseline"
        and item.unique
        for item in ProductCandidateContext.__table__.indexes
    )
    assert any(
        isinstance(item, UniqueConstraint)
        and item.name is not None
        and item.name.endswith("uq_anomaly_context_evaluation_trigger")
        for item in AnomalyContextDetail.__table__.constraints
    )
    migration = Path(
        "alembic/versions/20260818_0017_stage6_balanced_context.py"
    ).read_text(encoding="utf-8")
    assert 'revision: str = "20260818_0017"' in migration
    assert 'down_revision: str | None = "20260818_0016"' in migration
    for forbidden in ("op.execute", "UPDATE ", "INSERT INTO", "DROP COLUMN"):
        assert forbidden not in migration


def test_s6_r1_baseline_raw_source_excludes_post_t0_evidence() -> None:
    service = _source_cutoff_harness()

    baseline = service.create_baseline(
        CANDIDATE_ID,
        context_evaluated_at=DELAYED_EVALUATED,
    )

    assert baseline.evidence_cutoff_at == FIRST_KNOWN
    assert baseline.evaluated_at == DELAYED_EVALUATED
    assert baseline.sources.statuses["daily_ohlc"]["request_id"] == "A-before-t0"


def test_s6_r2_delayed_baseline_invocation_keeps_t0_information_set() -> None:
    service = _source_cutoff_harness()
    much_later = FIRST_KNOWN + timedelta(days=7)

    baseline = service.create_baseline(
        CANDIDATE_ID,
        context_evaluated_at=much_later,
    )

    assert baseline.evaluated_at == much_later
    assert baseline.evidence_cutoff_at == FIRST_KNOWN
    assert baseline.sources.statuses["daily_ohlc"]["request_id"] == "A-before-t0"


@pytest.mark.asyncio
async def test_s6_r3_refresh_uses_post_t0_evidence_without_changing_baseline_cutoff(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    service = _source_cutoff_harness()
    baseline = service.create_baseline(
        CANDIDATE_ID,
        context_evaluated_at=DELAYED_EVALUATED,
    )
    monkeypatch.setattr(vnext, "utc_now", lambda: DELAYED_EVALUATED)

    refresh = await service.refresh(CANDIDATE_ID)

    assert baseline.sources.statuses["daily_ohlc"]["request_id"] == "A-before-t0"
    assert refresh.sources.statuses["daily_ohlc"]["request_id"] == "B-after-t0"
    assert refresh.evidence_cutoff_at == DELAYED_EVALUATED
    assert refresh.evaluated_at == DELAYED_EVALUATED


def test_s6_r4_chain_excludes_post_t0_snapshot_but_refresh_cutoff_admits_it() -> None:
    before_raw = _raw_source(
        "daily_ohlc",
        "chain-A",
        received_at=FIRST_KNOWN - timedelta(minutes=1),
        observed_at=FIRST_KNOWN - timedelta(minutes=2),
        payload={},
    )
    after_raw = _raw_source(
        "daily_ohlc",
        "chain-B",
        received_at=POST_FIRST_KNOWLEDGE,
        observed_at=POST_FIRST_KNOWLEDGE - timedelta(minutes=1),
        payload={},
    )
    symbol = "NVDA260821C00160000"
    before = ContractOiDailySnapshot(
        id=uuid4(),
        raw_payload_id=before_raw.id,
        ticker=TICKER,
        expiration=EXPIRY,
        contract_symbol=symbol,
        vendor_oi_as_of=FIRST_KNOWN - timedelta(minutes=2),
        quote_as_of=FIRST_KNOWN - timedelta(minutes=2),
        greeks_as_of=FIRST_KNOWN - timedelta(minutes=2),
        source_request_id="chain-A",
    )
    after = ContractOiDailySnapshot(
        id=uuid4(),
        raw_payload_id=after_raw.id,
        ticker=TICKER,
        expiration=EXPIRY,
        contract_symbol=symbol,
        vendor_oi_as_of=POST_FIRST_KNOWLEDGE,
        quote_as_of=POST_FIRST_KNOWLEDGE,
        greeks_as_of=POST_FIRST_KNOWLEDGE,
        source_request_id="chain-B",
    )
    session = ChainTimelineSession(
        [before, after],
        {before_raw.id: before_raw, after_raw.id: after_raw},
    )
    service = Stage6BalancedContextService(session)  # type: ignore[arg-type]

    baseline = service._chain_context(
        TICKER,
        expiration=EXPIRY,
        evidence_cutoff_at=FIRST_KNOWN,
    )
    refresh = service._chain_context(
        TICKER,
        expiration=EXPIRY,
        evidence_cutoff_at=DELAYED_EVALUATED,
    )

    assert baseline[symbol].source_request_id == "chain-A"
    assert refresh[symbol].source_request_id == "chain-B"


def test_s6_r5_dealer_archive_uses_t0_for_baseline_and_t1_for_refresh(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    session = RecordingSession()
    service = EvaluationHarness(session, {}, {})
    candidate = _candidate([])
    late_snapshot = SimpleNamespace(
        id=uuid4(),
        vendor_observed_at=POST_FIRST_KNOWLEDGE,
        captured_at=POST_FIRST_KNOWLEDGE,
    )
    requested_cutoffs: list[datetime] = []

    def archived_at_cutoff(
        _session: Any,
        *,
        ticker: str,
        as_of: datetime,
    ) -> Any:
        assert ticker == TICKER
        requested_cutoffs.append(as_of)
        return (late_snapshot, {}) if as_of >= POST_FIRST_KNOWLEDGE else None

    monkeypatch.setattr(vnext, "best_archived_surface_at_or_before", archived_at_cutoff)
    baseline = service._persist_evaluation(
        candidate,
        evaluation_kind=EvaluationIdentity.FIRST_KNOWLEDGE_BASELINE,
        evaluated_at=DELAYED_EVALUATED,
        evidence_cutoff_at=FIRST_KNOWN,
        sources=_sources(),
    )
    refresh = service._persist_evaluation(
        candidate,
        evaluation_kind=EvaluationIdentity.REFRESH,
        evaluated_at=DELAYED_EVALUATED,
        evidence_cutoff_at=DELAYED_EVALUATED,
        sources=_sources(),
    )

    assert requested_cutoffs == [FIRST_KNOWN, DELAYED_EVALUATED]
    assert baseline.dealer_gex_context["availability"] == "NOT_YET_AVAILABLE"
    assert refresh.dealer_gex_context["availability"] == "AVAILABLE"


@pytest.mark.asyncio
async def test_s6_r6_late_nonbackfillable_source_stays_missing_from_baseline(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    service = _source_cutoff_harness()
    baseline = service.create_baseline(
        CANDIDATE_ID,
        context_evaluated_at=DELAYED_EVALUATED,
    )
    monkeypatch.setattr(vnext, "utc_now", lambda: DELAYED_EVALUATED)

    refresh = await service.refresh(CANDIDATE_ID)

    assert baseline.sources.statuses["term_structure"]["availability"] == (
        "NOT_YET_AVAILABLE"
    )
    assert refresh.sources.statuses["term_structure"]["availability"] == "AVAILABLE"
    assert "term_structure" not in baseline.sources.payloads
    assert "term_structure" in refresh.sources.payloads


def test_s6_r7_price_context_excludes_future_and_unverifiable_bars(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    session = RecordingSession()
    service = EvaluationHarness(session, {}, {})
    candidate = _candidate([])
    sources = _sources()
    sources.payloads["daily_ohlc"] = {
        "data": {
            "as_of": (FIRST_KNOWN - timedelta(minutes=1)).isoformat(),
            "bars": [
                {
                    "trading_date": "2026-08-18",
                    "session": "regular",
                    "close_usd": 100,
                },
                {
                    "trading_date": "2026-08-19",
                    "session": "regular",
                    "close_usd": 999,
                },
                {"session": "regular", "close_usd": 888},
            ],
        }
    }
    monkeypatch.setattr(
        vnext,
        "best_archived_surface_at_or_before",
        lambda *_args, **_kwargs: None,
    )

    context = service._persist_evaluation(
        candidate,
        evaluation_kind=EvaluationIdentity.FIRST_KNOWLEDGE_BASELINE,
        evaluated_at=DELAYED_EVALUATED,
        evidence_cutoff_at=FIRST_KNOWN,
        sources=sources,
    )
    history = context.price_context["history"]
    unverifiable = vnext._price_payload_at_or_before(
        {"data": {"bars": [{"session": "regular", "close_usd": 888}]}},
        evidence_cutoff_at=FIRST_KNOWN,
    )

    assert history["latest_trading_date"] == "2026-08-18"
    assert history["latest_regular_close_usd"] == 100.0
    assert history["raw_bar_count"] == 1
    assert vnext.calculate_price_context(unverifiable)["availability"] == "UNAVAILABLE"


def test_all_active_trigger_shapes_share_one_ticker_context(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    session, service, candidate = _evaluation_fixture()
    monkeypatch.setattr(vnext, "best_archived_surface_at_or_before", lambda *_args, **_kwargs: None)

    context = service._persist_evaluation(
        candidate,
        evaluation_kind=EvaluationIdentity.FIRST_KNOWLEDGE_BASELINE,
        evaluated_at=EVALUATED,
        evidence_cutoff_at=FIRST_KNOWN,
        sources=_sources(),
    )

    assert context.product_candidate_id == candidate.id
    assert context.evaluation_kind == "FIRST_KNOWLEDGE_BASELINE"
    assert len(context.details) == 3
    assert service.chain_loads == [EXPIRY]
    assert {row.product_candidate_trigger_id for row in context.details} == {
        row.id for row in candidate.triggers
    }
    assert {row.anomaly_entity_type for row in context.details} == {"CONTRACT", "EXPIRY"}
    assert session.flushes == 2


@pytest.mark.parametrize(
    "families",
    [
        ("RADAR_EVENT",),
        ("EXPIRY_ACTIVITY",),
        ("CONTRACT_PERSISTENCE",),
        ("RADAR_EVENT", "EXPIRY_ACTIVITY", "CONTRACT_PERSISTENCE"),
    ],
)
def test_candidate_entry_has_no_radar_only_contract_gate(
    monkeypatch: pytest.MonkeyPatch,
    families: tuple[str, ...],
) -> None:
    session, service, candidate = _evaluation_fixture()
    candidate.triggers = [
        trigger for trigger in candidate.triggers if trigger.evidence_family in families
    ]
    monkeypatch.setattr(
        vnext,
        "best_archived_surface_at_or_before",
        lambda *_args, **_kwargs: None,
    )
    context = service._persist_evaluation(
        candidate,
        evaluation_kind=EvaluationIdentity.FIRST_KNOWLEDGE_BASELINE,
        evaluated_at=EVALUATED,
        evidence_cutoff_at=FIRST_KNOWN,
        sources=_sources(),
    )
    assert len(context.details) == len(families)
    assert {row.product_candidate_trigger_id for row in context.details} == {
        row.id for row in candidate.triggers
    }


def test_contract_and_expiry_details_preserve_phase2b_boundaries(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _session, service, candidate = _evaluation_fixture()
    monkeypatch.setattr(vnext, "best_archived_surface_at_or_before", lambda *_args, **_kwargs: None)
    context = service._persist_evaluation(
        candidate,
        evaluation_kind=EvaluationIdentity.FIRST_KNOWLEDGE_BASELINE,
        evaluated_at=EVALUATED,
        evidence_cutoff_at=FIRST_KNOWN,
        sources=_sources(),
    )
    contracts = [row for row in context.details if row.anomaly_entity_type == "CONTRACT"]
    expiry = next(row for row in context.details if row.anomaly_entity_type == "EXPIRY")
    assert len(contracts) == 2
    for row in contracts:
        snapshot = row.contract_snapshot
        assert snapshot is not None
        assert snapshot["contract_iv"] is not None
        assert snapshot["delta"] is not None
        assert snapshot["bid"] is not None
        assert snapshot["ask"] is not None
        assert snapshot["spread_pct"] is not None
        assert snapshot["quote_as_of"] is not None
        for excluded in ("gamma", "theta", "vega", "execution_score"):
            assert excluded not in snapshot
    assert expiry.contract_snapshot is None
    assert expiry.expiry_activity_recap is not None
    for fabricated in ("contract_symbol", "right", "strike", "contract_iv", "delta", "bid", "ask"):
        assert fabricated not in expiry.expiry_activity_recap


def test_refresh_cannot_mutate_frozen_baseline(monkeypatch: pytest.MonkeyPatch) -> None:
    _session, service, candidate = _evaluation_fixture()
    monkeypatch.setattr(vnext, "best_archived_surface_at_or_before", lambda *_args, **_kwargs: None)
    baseline = service._persist_evaluation(
        candidate,
        evaluation_kind=EvaluationIdentity.FIRST_KNOWLEDGE_BASELINE,
        evaluated_at=EVALUATED,
        evidence_cutoff_at=FIRST_KNOWN,
        sources=_sources(),
    )
    before = json.dumps(context_public(baseline), sort_keys=True)
    refresh = service._persist_evaluation(
        candidate,
        evaluation_kind=EvaluationIdentity.REFRESH,
        evaluated_at=EVALUATED + timedelta(minutes=10),
        evidence_cutoff_at=EVALUATED + timedelta(minutes=10),
        sources=_sources(close_offset=5),
    )
    after = json.dumps(context_public(baseline), sort_keys=True)
    assert before == after
    assert refresh.id != baseline.id
    assert {row.id for row in refresh.details}.isdisjoint(
        {row.id for row in baseline.details}
    )


def test_s6_r8_baseline_replay_reuses_exact_frozen_trigger_set() -> None:
    triggers = [_trigger("EXPIRY_ACTIVITY", "EXPIRY", EXPIRY.isoformat())]
    candidate = _candidate(triggers)
    context = ProductCandidateContext(
        id=uuid4(),
        product_candidate_id=candidate.id,
        evaluation_kind="FIRST_KNOWLEDGE_BASELINE",
        candidate_first_knowledge_at=FIRST_KNOWN,
        context_evaluated_at=EVALUATED,
        context_specification_version=PHASE2B_VNEXT_SPEC_VERSION,
        context_config_version="test",
        context_config_hash=stage6_config_hash(),
        price_context={},
        volatility_context={},
        dealer_gex_context={},
        availability={},
        provenance={},
        created_at=EVALUATED,
    )
    context.details = [
        AnomalyContextDetail(
            id=uuid4(),
            product_candidate_context_id=context.id,
            product_candidate_trigger_id=triggers[0].id,
            anomaly_entity_type="EXPIRY",
            anomaly_identity=EXPIRY.isoformat(),
            contract_snapshot=None,
            expiry_activity_recap={"expiration": EXPIRY.isoformat()},
            volatility_context={},
            dealer_gex_context={},
            deep_dive_references={},
            availability={},
            provenance={},
            created_at=EVALUATED,
        )
    ]

    class ReplayHarness(Stage6BalancedContextService):
        def _candidate(self, _candidate_id: Any) -> ProductCandidate:
            return candidate

        def _baseline(self, _candidate_id: Any) -> ProductCandidateContext:
            return context

        def _archived_source_bundle(
            self,
            _ticker: str,
            *,
            evidence_cutoff_at: datetime,
        ) -> SourceBundle:
            raise AssertionError(
                f"baseline replay read newer source state at {evidence_cutoff_at}"
            )

    before = json.dumps(context_public(context), sort_keys=True)
    detail_ids = [detail.id for detail in context.details]
    replayed = ReplayHarness(RecordingSession()).create_baseline(candidate.id)  # type: ignore[arg-type]
    assert replayed is context
    assert json.dumps(context_public(replayed), sort_keys=True) == before
    assert [detail.id for detail in replayed.details] == detail_ids
    candidate.triggers.append(_trigger("RADAR_EVENT", "CONTRACT", "LATE"))
    with pytest.raises(ValueError, match="conflicts"):
        ReplayHarness(RecordingSession()).create_baseline(candidate.id)  # type: ignore[arg-type]


def test_baseline_archive_queries_enforce_receipt_and_vendor_cutoffs() -> None:
    session = RecordingSession()
    bundle = Stage6BalancedContextService(session)._archived_source_bundle(  # type: ignore[arg-type]
        TICKER,
        evidence_cutoff_at=EVALUATED,
    )
    assert set(bundle.statuses) == {name for name, *_ in SOURCE_ENDPOINTS}
    assert all(row["availability"] == "NOT_YET_AVAILABLE" for row in bundle.statuses.values())
    assert len(session.statements) == 4
    for statement in session.statements:
        sql = str(statement)
        assert "raw_vendor_payloads.received_at <=" in sql
        assert "raw_vendor_payloads.observed_at IS NULL" in sql
        assert "raw_vendor_payloads.observed_at <=" in sql


def test_chain_archive_query_is_time_bounded_and_loaded_once_per_expiry() -> None:
    session = RecordingSession()
    service = Stage6BalancedContextService(session)  # type: ignore[arg-type]
    assert service._chain_context(
        TICKER,
        expiration=EXPIRY,
        evidence_cutoff_at=EVALUATED,
    ) == {}
    assert len(session.statements) == 1
    sql = str(session.statements[0])
    assert "contract_oi_daily_snapshots.vendor_oi_as_of <=" in sql
    assert "raw_vendor_payloads.received_at <=" in sql
    assert "raw_vendor_payloads.observed_at IS NULL" in sql
    assert "raw_vendor_payloads.observed_at <=" in sql
    assert "contract_oi_daily_snapshots.quote_as_of IS NULL" in sql
    assert "contract_oi_daily_snapshots.quote_as_of <=" in sql
    assert "contract_oi_daily_snapshots.greeks_as_of IS NULL" in sql
    assert "contract_oi_daily_snapshots.greeks_as_of <=" in sql


def test_missing_vendor_time_never_falls_back_to_local_capture() -> None:
    missing = _missing_source_provenance("iv_rank", availability="NOT_YET_AVAILABLE")
    assert missing["vendor_observed_at"] is None
    assert missing["local_captured_at"] is None
    assert vnext._source_vendor_time(missing) is None


def test_price_block_is_descriptive_and_missing_is_not_zero() -> None:
    session, service, candidate = _evaluation_fixture()
    sources = _sources()
    sources.payloads["daily_ohlc"] = {}
    context = service._persist_evaluation
    assert context is not None
    price = vnext.calculate_price_context(sources.payloads["daily_ohlc"])
    assert price.get("latest_regular_close_usd") is None
    assert price["return_1d"] is None
    assert price["sma_20"] is None
    assert "bullish" not in json.dumps(price).lower()
    assert session.writes == 0
    assert candidate.ticker == TICKER


def test_term_structure_and_iv_rank_remain_descriptive() -> None:
    term = _normalize_term_structure(
        _sources().payloads["term_structure"],
        source_state="AVAILABLE",
    )
    expiry = term_context_for_expiry(term, expiration=EXPIRY)
    assert expiry["candidate_term_iv"] == 35.0
    assert expiry["topology"] == "LOCAL_PEAK"
    iv_rank = _normalize_iv_rank(
        {"data": {"iv_rank": 42}},
        source_state="AVAILABLE",
    )
    assert iv_rank["entity"] == "TICKER"
    assert iv_rank["vendor_semantics"] == "UNVERIFIED"
    assert iv_rank["core_eligibility"] == IV_RANK_CORE_ELIGIBILITY
    assert iv_rank["classification"] is None


def test_dealer_context_uses_decimal_strike_identity_and_ignores_missing_strike() -> None:
    result = dealer_gex_context_for_expiry(
        {
            "spot_usd": "100.00",
            "cells": [
                {"expiration": "2026-08-21", "strike_usd": None, "net_dealer_gex_usd": 999},
                {"expiration": "2026-08-21", "strike_usd": "90.0", "net_dealer_gex_usd": 100},
                {"expiration": "2026-08-21", "strike_usd": "85", "net_dealer_gex_usd": -20},
                {"expiration": "2026-08-21", "strike_usd": "110", "net_dealer_gex_usd": 50},
                {"expiration": "2026-08-14", "strike_usd": "90.00", "net_dealer_gex_usd": -10},
                {"expiration": "2026-08-28", "strike_usd": "90.000", "net_dealer_gex_usd": -5},
            ],
        },
        expiration=EXPIRY,
    )
    assert result["primary_floor"]["strike_usd"] == 90.0
    assert result["immediate_below_floor_node"]["strike_usd"] == 85.0
    adjacent = result["adjacent_expiry_context"]
    assert adjacent["state"] == "BOTH_AVAILABLE_NEGATIVE"
    assert adjacent["strike_identity"] == "CANONICAL_DECIMAL"
    serialized = json.dumps(result)
    assert "STABILIZATION_BIAS" not in serialized
    assert "DOWNSIDE_ACCELERATION_RISK" not in serialized


def test_invalid_deep_dive_rows_do_not_leak_as_positive_context() -> None:
    trigger = _trigger("EXPIRY_ACTIVITY", "EXPIRY", EXPIRY.isoformat())
    candidate = _candidate([trigger])
    source = ExpiryObservation(id=uuid4(), expiration=EXPIRY, dte_at_detection=3)
    contract = ContractScanObservation(
        id=uuid4(),
        is_candidate=False,
        classification="NO_SIGNAL",
        hard_reject_reason=None,
        structure_components={},
        components={},
    )
    cluster = StrikeCluster(
        id=uuid4(),
        classification="INVALID_CLUSTER",
        components={},
    )
    session = RecordingSession()
    session.scalars_values = [[contract], [cluster]]
    result = Stage6BalancedContextService(session)._deep_dive(  # type: ignore[arg-type]
        candidate,
        TriggerDescriptor(trigger, EXPIRY, None, None, 3, source),
    )
    assert result["structures"] == []
    assert result["valid_clusters"] == []


@pytest.mark.asyncio
async def test_explicit_refresh_calls_each_ticker_source_once_and_never_heatmap() -> None:
    candidate = _candidate(
        [
            _trigger("RADAR_EVENT", "CONTRACT", "NVDA260821C00160000"),
            _trigger("EXPIRY_ACTIVITY", "EXPIRY", EXPIRY.isoformat()),
            _trigger(
                "CONTRACT_PERSISTENCE",
                "CONTRACT",
                "NVDA260821P00150000",
            ),
        ]
    )

    class FakeClient:
        def __init__(self) -> None:
            self.calls: list[tuple[str, str, dict[str, Any]]] = []

        async def request(self, method: str, endpoint: str, **kwargs: Any) -> Any:
            self.calls.append((method, endpoint, kwargs))
            return SimpleNamespace(
                payload={"data": {"as_of": "2026-08-18T20:01:00+00:00"}},
                vendor_request_id=None,
                request_id=f"request-{len(self.calls)}",
                status_code=200,
            )

    class RefreshHarness(Stage6BalancedContextService):
        def _candidate(self, _candidate_id: Any) -> ProductCandidate:
            return candidate

        def _persist_evaluation(self, candidate: ProductCandidate, **kwargs: Any) -> Any:
            self.persisted = (candidate, kwargs)
            return SimpleNamespace(id=uuid4())

    session = RecordingSession()
    client = FakeClient()
    service = RefreshHarness(session, client)  # type: ignore[arg-type]
    await service.refresh(candidate.id)
    assert len(client.calls) == 4
    assert [endpoint for _method, endpoint, _kwargs in client.calls] == [
        template.format(ticker=TICKER) for _name, template, _params in SOURCE_ENDPOINTS
    ]
    assert all("heatmap" not in endpoint for _method, endpoint, _kwargs in client.calls)
    assert all(TICKER in endpoint for _method, endpoint, _kwargs in client.calls)


def test_get_route_is_read_only_and_returns_truthful_missing_baseline(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    candidate = _candidate([_trigger("EXPIRY_ACTIVITY", "EXPIRY", EXPIRY.isoformat())])
    session = RecordingSession()
    monkeypatch.setattr(
        candidate_routes,
        "load_context_history",
        lambda _session, _candidate_id: (candidate, []),
    )
    payload = candidate_routes.read_candidate_context(candidate.id, session)  # type: ignore[arg-type]
    assert payload["baseline_state"] == "NOT_YET_AVAILABLE"
    assert payload["contexts"] == []
    assert session.writes == 0


def test_legacy_phase2b_models_remain_present_and_new_writes_are_isolated() -> None:
    assert Phase2bTickerContextSnapshot.__tablename__ == "phase2b_ticker_context_snapshots"
    assert Phase2bCandidateEvaluation.__tablename__ == "phase2b_candidate_evaluations"
    assert Phase2bCandidateState.__tablename__ == "phase2b_candidate_states"
    assert Phase2bV3ResearchWorkspace.__tablename__ == "phase2b_v3_research_workspaces"
    source = inspect.getsource(Stage6BalancedContextService)
    for legacy in (
        "Phase2bTickerContextSnapshot",
        "Phase2bCandidateEvaluation",
        "Phase2bCandidateState",
        "Phase2bV3ResearchWorkspace",
    ):
        assert legacy not in source


def test_stage6_outputs_contain_no_future_or_action_layer_fields() -> None:
    source = inspect.getsource(vnext).lower()
    for forbidden in (
        "forward_outcome",
        "actionability",
        "trade_expression",
        "execution_score",
        "conviction_score",
        "ticker_score",
    ):
        assert forbidden not in source
    assert "dealer_heatmap" not in {name for name, *_ in SOURCE_ENDPOINTS}

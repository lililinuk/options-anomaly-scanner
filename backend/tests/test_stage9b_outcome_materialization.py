from __future__ import annotations

import inspect
from datetime import date, datetime, timezone
from decimal import Decimal
from pathlib import Path
from types import SimpleNamespace
from uuid import uuid4

import pytest

from app.db.models import RawVendorPayload
from app.research.forward_outcome import (
    CohortMetadata,
    CorporateActionBasisStatus,
    ForwardSessionPlan,
    ResearchSampleFoundation,
    ResearchSampleValidity,
    RouteComposition,
    RunOrigin,
    calculate_close_path_outcome,
)
from app.research.materialization import (
    PAID_NIGHTWATCH_CALLS,
    STAGE9B_OUTCOME_METHODOLOGY_VERSION,
    STAGE9B_PRICE_BASIS_POLICY,
    PreservedOhlcCatalog,
    ProposedMeasurement,
    Stage9BOutcomeMaterializer,
    _distribution,
    _measurement_fingerprint,
    _trigger_count_distribution,
)
from app.research.models import (
    ForwardOutcomeCorporateAction,
    ForwardOutcomeMeasurement,
    ForwardOutcomeResearchSample,
)

ROOT = Path(__file__).resolve().parents[2]
UTC = timezone.utc
MIGRATION = (
    ROOT
    / "backend"
    / "alembic"
    / "versions"
    / "20260827_0019_stage9b_outcome_materialization.py"
)
FIRST_KNOWN = datetime(2026, 8, 20, 10, 7, tzinfo=UTC)
EVALUATED = datetime(2026, 8, 27, 22, 0, tzinfo=UTC)


def _payload(
    ticker: str,
    bars: list[dict[str, object]],
    *,
    received_at: datetime,
) -> RawVendorPayload:
    return RawVendorPayload(
        id=uuid4(),
        scan_run_id=None,
        source="nightwatch",
        endpoint=f"/v1/stocks/ohlc/{ticker}",
        request_id=f"fixture-{uuid4()}",
        vendor_request_id="vendor-fixture",
        ticker=ticker,
        expiration=None,
        observed_at=received_at,
        received_at=received_at,
        payload_sha256="a" * 64,
        payload={"data": {"bars": bars}},
    )


def _bar(trading_date: str, close: str | None, *, session: str = "regular") -> dict[str, object]:
    return {
        "trading_date": trading_date,
        "session": session,
        "close_usd": close,
    }


def _foundation(
    *,
    origin: RunOrigin = RunOrigin.CANONICAL_SCHEDULED_PRODUCTION,
    trigger_count: int = 5,
    route: RouteComposition = RouteComposition.RADAR_ONLY,
) -> ResearchSampleFoundation:
    candidate_id = uuid4()
    sessions = ForwardSessionPlan(
        reference_session=date(2026, 8, 19),
        t1_session=date(2026, 8, 20),
        t3_session=date(2026, 8, 24),
        t5_session=date(2026, 8, 26),
    )
    return ResearchSampleFoundation(
        product_candidate_id=candidate_id,
        frozen_baseline_context_id=uuid4(),
        scan_run_id=uuid4(),
        ticker="NVDA",
        candidate_first_knowledge_at=FIRST_KNOWN,
        sample_validity_state=ResearchSampleValidity.VALID,
        invalid_reason=None,
        run_origin=origin,
        run_origin_source_trigger=(
            "scheduled_daily"
            if origin is RunOrigin.CANONICAL_SCHEDULED_PRODUCTION
            else "cli"
        ),
        primary_research_eligible=(
            origin is RunOrigin.CANONICAL_SCHEDULED_PRODUCTION
        ),
        sessions=sessions,
        outcome_window_key=(
            f"NVDA|{sessions.reference_session}|{sessions.t1_session}|"
            f"{sessions.t3_session}|{sessions.t5_session}"
        ),
        cohort=CohortMetadata(
            has_radar=True,
            has_expiry_activity=route is not RouteComposition.RADAR_ONLY,
            has_contract_persistence=False,
            route_composition=route,
            qualifying_trigger_count=trigger_count,
            dte_bucket_counts={"SHORT": trigger_count},
        ),
    )


def _sample(foundation: ResearchSampleFoundation) -> ForwardOutcomeResearchSample:
    return ForwardOutcomeResearchSample(
        id=uuid4(),
        product_candidate_id=foundation.product_candidate_id,
        frozen_baseline_context_id=foundation.frozen_baseline_context_id,
        scan_run_id=foundation.scan_run_id,
        ticker=foundation.ticker,
        candidate_first_knowledge_at=foundation.candidate_first_knowledge_at,
        sample_validity_state="VALID",
        invalid_reason=None,
        run_origin=foundation.run_origin.value,
        run_origin_source_trigger=foundation.run_origin_source_trigger,
        run_origin_classification_version=foundation.run_origin_classification_version,
        primary_research_eligible=foundation.primary_research_eligible,
        has_radar=True,
        has_expiry_activity=False,
        has_contract_persistence=False,
        route_composition=foundation.cohort.route_composition.value,
        qualifying_trigger_count=foundation.cohort.qualifying_trigger_count,
        dte_bucket_counts=dict(foundation.cohort.dte_bucket_counts),
        reference_price_policy=foundation.reference_price_policy,
        reference_session=foundation.sessions.reference_session,
        t1_session=foundation.sessions.t1_session,
        t3_session=foundation.sessions.t3_session,
        t5_session=foundation.sessions.t5_session,
        outcome_window_key=foundation.outcome_window_key,
        price_basis_capability="RAW_UNADJUSTED",
        price_basis_name=STAGE9B_PRICE_BASIS_POLICY,
        price_basis_provenance={"adjustment": "RAW_UNADJUSTED"},
        outcome_methodology_version=STAGE9B_OUTCOME_METHODOLOGY_VERSION,
        direction="UNRESOLVED",
        created_at=EVALUATED,
    )


def test_raw_regular_close_basis_is_explicit_and_calculable() -> None:
    catalog = PreservedOhlcCatalog(
        [
            _payload(
                "NVDA",
                [_bar("2026-08-19", "100"), _bar("2026-08-20", "102")],
                received_at=EVALUATED,
            )
        ]
    )
    reference = catalog.lookup("NVDA", date(2026, 8, 19), as_of=EVALUATED)
    future = catalog.lookup("NVDA", date(2026, 8, 20), as_of=EVALUATED)
    assert reference is not None and future is not None
    assert reference.price_evidence().basis.corporate_action_status is (
        CorporateActionBasisStatus.RAW_UNADJUSTED
    )
    metrics = calculate_close_path_outcome(
        reference.price_evidence(), [future.price_evidence()]
    )
    assert metrics is not None
    assert metrics.close_return == Decimal("0.02")
    assert reference.evidence["price_adjustment_semantics"] == "RAW_UNADJUSTED"


def test_preserved_ohlc_reuse_is_as_of_deterministic_and_missing_is_not_zero() -> None:
    early = datetime(2026, 8, 20, 21, 0, tzinfo=UTC)
    later = datetime(2026, 8, 21, 21, 0, tzinfo=UTC)
    catalog = PreservedOhlcCatalog(
        [
            _payload("NVDA", [_bar("2026-08-20", "100")], received_at=early),
            _payload("NVDA", [_bar("2026-08-20", "101")], received_at=later),
        ]
    )
    assert catalog.lookup("NVDA", date(2026, 8, 20), as_of=early).close == Decimal("100")
    assert catalog.lookup("NVDA", date(2026, 8, 20), as_of=later).close == Decimal("101")
    assert catalog.lookup("NVDA", date(2026, 8, 24), as_of=later) is None
    invalid = PreservedOhlcCatalog(
        [_payload("NVDA", [_bar("2026-08-20", None)], received_at=early)]
    ).lookup("NVDA", date(2026, 8, 20), as_of=early)
    assert invalid is not None and invalid.close is None


def test_partial_horizon_maturity_and_preserved_path_formulas() -> None:
    foundation = _foundation()
    sample = _sample(foundation)
    catalog = PreservedOhlcCatalog(
        [
            _payload(
                "NVDA",
                [_bar("2026-08-19", "100"), _bar("2026-08-20", "102")],
                received_at=EVALUATED,
            )
        ]
    )
    service = Stage9BOutcomeMaterializer(SimpleNamespace())
    t1 = service._propose_measurement(
        sample,
        foundation,
        horizon=1,
        evaluated_at=EVALUATED,
        catalog=catalog,
        actions=[],
        is_primary_representative=True,
    )
    t3 = service._propose_measurement(
        sample,
        foundation,
        horizon=3,
        evaluated_at=EVALUATED,
        catalog=catalog,
        actions=[],
        is_primary_representative=True,
    )
    assert t1.maturity_state == "MATURE_AVAILABLE"
    assert t1.close_return == Decimal("0.02")
    assert t1.primary_descriptive_eligible is True
    assert t3.maturity_state == "MATURE_MISSING_DATA"
    assert t3.close_return is None
    assert {item[0] for item in t3.missing_sessions} == {
        date(2026, 8, 21),
        date(2026, 8, 24),
    }


def test_known_price_scale_action_quarantines_only_crossing_horizons() -> None:
    foundation = _foundation()
    sample = _sample(foundation)
    catalog = PreservedOhlcCatalog(
        [
            _payload(
                "NVDA",
                [
                    _bar("2026-08-19", "100"),
                    _bar("2026-08-20", "102"),
                    _bar("2026-08-21", "51"),
                    _bar("2026-08-24", "52"),
                ],
                received_at=EVALUATED,
            )
        ]
    )
    action = ForwardOutcomeCorporateAction(
        id=uuid4(),
        ticker="NVDA",
        effective_session=date(2026, 8, 21),
        action_type="SPLIT",
        price_scale_changing=True,
        record_status="KNOWN",
        source_name="fixture",
        source_reference="fixture://split",
        record_revision=1,
        provenance={},
        recorded_at=EVALUATED,
        created_at=EVALUATED,
    )
    service = Stage9BOutcomeMaterializer(SimpleNamespace())
    t1 = service._propose_measurement(
        sample, foundation, horizon=1, evaluated_at=EVALUATED, catalog=catalog,
        actions=[action], is_primary_representative=True,
    )
    t3 = service._propose_measurement(
        sample, foundation, horizon=3, evaluated_at=EVALUATED, catalog=catalog,
        actions=[action], is_primary_representative=True,
    )
    assert t1.maturity_state == "MATURE_AVAILABLE"
    assert t3.maturity_state == "CORPORATE_ACTION_CONTAMINATED"
    assert t3.close_return is None
    assert t3.primary_descriptive_eligible is False
    assert t3.corporate_action_event_ids == (str(action.id),)


class _AppendSession:
    def __init__(self, latest: ForwardOutcomeMeasurement | None = None) -> None:
        self.latest = latest
        self.added: list[ForwardOutcomeMeasurement] = []

    def scalar(self, _statement: object) -> ForwardOutcomeMeasurement | None:
        return self.latest

    def add(self, row: ForwardOutcomeMeasurement) -> None:
        self.added.append(row)

    def flush(self) -> None:
        return None


def _proposal(*, target_close: Decimal = Decimal("102")) -> ProposedMeasurement:
    return ProposedMeasurement(
        horizon_sessions=1,
        target_session=date(2026, 8, 20),
        maturity_state="MATURE_AVAILABLE",
        reference_close=Decimal("100"),
        target_close=target_close,
        close_return=target_close / Decimal("100") - Decimal(1),
        max_upside=target_close / Decimal("100") - Decimal(1),
        max_downside=target_close / Decimal("100") - Decimal(1),
        primary_descriptive_eligible=True,
        corporate_action_state="NO_KNOWN_PRICE_SCALE_EVENT_RECORDED",
        corporate_action_event_ids=(),
        input_bar_evidence={
            "2026-08-19": {"raw_close_usd": "100", "adjustment": "RAW_UNADJUSTED"},
            "2026-08-20": {
                "raw_close_usd": str(target_close),
                "adjustment": "RAW_UNADJUSTED",
            },
        },
        missing_sessions=(),
    )


def test_materialization_is_idempotent_and_changes_append_a_revision() -> None:
    sample = _sample(_foundation())
    first_session = _AppendSession()
    service = Stage9BOutcomeMaterializer(first_session)  # type: ignore[arg-type]
    proposal = _proposal()
    assert service._append_measurement_if_changed(
        sample, proposal, evaluated_at=EVALUATED
    )
    first = first_session.added[0]
    assert first.calculation_revision == 1
    assert first.price_basis_status == "RAW_UNADJUSTED"
    assert first.price_basis_name == STAGE9B_PRICE_BASIS_POLICY
    assert first.price_basis_provenance["claim_exclusions"] == [
        "ADJUSTED_RETURN",
        "TOTAL_RETURN",
        "CORPORATE_ACTION_CONSISTENT_RETURN",
    ]

    replay_session = _AppendSession(first)
    replay = Stage9BOutcomeMaterializer(replay_session)  # type: ignore[arg-type]
    assert not replay._append_measurement_if_changed(
        sample, proposal, evaluated_at=EVALUATED
    )
    assert replay_session.added == []

    changed_session = _AppendSession(first)
    changed = Stage9BOutcomeMaterializer(changed_session)  # type: ignore[arg-type]
    original = first.close_return
    assert changed._append_measurement_if_changed(
        sample, _proposal(target_close=Decimal("103")), evaluated_at=EVALUATED
    )
    second = changed_session.added[0]
    assert second.calculation_revision == 2
    assert second.supersedes_measurement_id == first.id
    assert first.close_return == original
    assert second.close_return == Decimal("0.03")
    with pytest.raises(ValueError, match="close_return is immutable"):
        first.close_return = Decimal("0.04")


def test_later_corrected_methodology_cannot_silently_replace_raw_v1() -> None:
    source = inspect.getsource(Stage9BOutcomeMaterializer._append_measurement_if_changed)
    assert "outcome_methodology_version" in source
    assert "== STAGE9B_OUTCOME_METHODOLOGY_VERSION" in source
    assert "supersedes_measurement_id" in source
    assert _measurement_fingerprint(_proposal()) == _measurement_fingerprint(_proposal())


def test_trigger_distribution_uses_only_canonical_population_without_buckets() -> None:
    primary_low = _foundation(trigger_count=4)
    primary_high = _foundation(trigger_count=10, route=RouteComposition.RADAR_EXPIRY)
    non_primary = _foundation(origin=RunOrigin.MANUAL, trigger_count=27)
    rows = [
        (_sample(primary_low), primary_low),
        (_sample(primary_high), primary_high),
        (_sample(non_primary), non_primary),
    ]
    report = _trigger_count_distribution(
        rows,
        representative_ids={rows[0][0].id, rows[1][0].id},
    )
    assert report["canonical_occurrences"] == {
        "n": 2,
        "min": 4,
        "p25": 5.5,
        "median": 7,
        "p75": 8.5,
        "p90": 9.4,
        "max": 10,
    }
    assert report["non_primary_context_only"]["n"] == 1
    assert report["non_primary_context_only"]["max"] == 27
    assert report["trigger_count_buckets_hardcoded"] is False
    assert _distribution([])["median"] is None


def test_stage9b_migration_is_additive_and_versioned() -> None:
    source = MIGRATION.read_text(encoding="utf-8")
    upgrade = source.split("def upgrade() -> None:", maxsplit=1)[1].split(
        "def downgrade() -> None:", maxsplit=1
    )[0]
    assert 'revision: str = "20260827_0019"' in source
    assert 'down_revision: str | None = "20260827_0018"' in source
    assert "RAW_UNADJUSTED" in upgrade
    assert "CORPORATE_ACTION_CONTAMINATED" in upgrade
    assert "forward_outcome_corporate_actions" in source
    assert "supersedes_measurement_id" in upgrade
    assert "UPDATE " not in upgrade.upper()
    assert "INSERT " not in upgrade.upper()


def test_no_paid_call_path_second_scheduler_or_live_research_dependency() -> None:
    materializer = (
        ROOT / "backend" / "app" / "research" / "materialization.py"
    ).read_text(encoding="utf-8")
    assert PAID_NIGHTWATCH_CALLS == 0
    assert "NightwatchClient" not in materializer
    assert "httpx" not in materializer
    assert "api_key" not in materializer.lower()
    assert STAGE9B_PRICE_BASIS_POLICY == "RAW_REGULAR_CLOSE_RESEARCH_V1"

    live_files = [
        ROOT / "backend" / "app" / "api" / "routes" / "scans.py",
        ROOT / "backend" / "app" / "api" / "routes" / "candidate_contexts.py",
        *sorted((ROOT / "backend" / "app" / "scanner").glob("*.py")),
    ]
    for path in live_files:
        live_source = path.read_text(encoding="utf-8").lower()
        assert "app.research" not in live_source
        assert "forward_outcome" not in live_source

    workflows = "\n".join(
        path.read_text(encoding="utf-8")
        for path in sorted((ROOT / ".github" / "workflows").glob("*.yml"))
    ).lower()
    assert "materialize-stage9b-outcomes" not in workflows
    assert "forward-outcome" not in workflows


def test_historical_trigger_population_has_no_current_activity_filter() -> None:
    source = inspect.getsource(Stage9BOutcomeMaterializer.materialize)
    assert "ProductCandidate.triggers" in source
    assert "current_dte" not in source
    assert "current_bucket" not in source
    assert "expiration >" not in source
    assert "trigger_count_bucket" not in source


def test_models_expose_raw_quarantine_and_append_only_fields() -> None:
    measurement_columns = ForwardOutcomeMeasurement.__table__.c
    assert measurement_columns.primary_descriptive_eligible.nullable is False
    assert measurement_columns.semantic_fingerprint.nullable is False
    assert measurement_columns.supersedes_measurement_id.nullable is True
    assert ForwardOutcomeCorporateAction.__tablename__ == (
        "forward_outcome_corporate_actions"
    )
    constraints = "\n".join(
        str(item.sqltext)
        for item in ForwardOutcomeMeasurement.__table__.constraints
        if hasattr(item, "sqltext")
    )
    assert "RAW_UNADJUSTED" in constraints
    assert "CORPORATE_ACTION_CONTAMINATED" in constraints

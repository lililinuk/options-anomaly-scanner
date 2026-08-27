from __future__ import annotations

import inspect
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path
from uuid import UUID, uuid4
from zoneinfo import ZoneInfo

import pytest

from app.confirmation.config import Phase2bContextConfig
from app.confirmation.domain import calculate_price_context
from app.db.models import (
    ProductCandidate,
    ProductCandidateContext,
    ProductCandidateTrigger,
    ScanRun,
)
from app.models.signals import DteBucket, bucket_for_dte
from app.research.aggregation import deterministic_primary_occurrence
from app.research.forward_outcome import (
    DIRECTION,
    OUTCOME_METHODOLOGY_VERSION,
    PRICE_BASIS_CAPABILITY,
    REFERENCE_PRICE_POLICY,
    ClosePriceEvidence,
    CorporateActionBasisStatus,
    MaturityState,
    PriceBasis,
    PriceBasisNotProvable,
    ResearchSampleFoundation,
    ResearchSampleValidity,
    RouteComposition,
    RunOrigin,
    build_research_sample_foundation,
    calculate_close_path_outcome,
    classify_scan_origin,
    cohort_metadata,
    map_forward_sessions,
    maturity_state,
)
from app.research.models import (
    ForwardOutcomeMeasurement,
    ForwardOutcomeResearchSample,
)

UTC = timezone.utc
NEW_YORK = ZoneInfo("America/New_York")
FIRST_KNOWN = datetime(2026, 8, 20, 10, 7, tzinfo=UTC)
ROOT = Path(__file__).resolve().parents[2]
MIGRATION = (
    ROOT
    / "backend"
    / "alembic"
    / "versions"
    / "20260827_0018_stage9a_forward_outcome_foundation.py"
)


def _trigger(
    candidate_id: UUID,
    index: int,
    family: str,
    *,
    qualifies: bool = True,
    event_date: date = date(2026, 8, 20),
    first_known: datetime = FIRST_KNOWN,
) -> ProductCandidateTrigger:
    trigger_id = uuid4()
    source_id = uuid4()
    is_expiry = family == "EXPIRY_ACTIVITY"
    is_radar = family == "RADAR_EVENT"
    return ProductCandidateTrigger(
        id=trigger_id,
        product_candidate_id=candidate_id,
        evidence_family=family,
        anomaly_entity_type="EXPIRY" if is_expiry else "CONTRACT",
        anomaly_identity=("2026-08-28" if is_expiry else f"NVDA260828C00{index:05d}"),
        source_evidence_identity=f"stage9a-fixture:{source_id}",
        qualifies_candidate=qualifies,
        present_at_first_knowledge=True,
        event_date=event_date,
        trigger_first_knowledge_at=first_known - timedelta(minutes=1),
        source_first_received_at=first_known - timedelta(minutes=2),
        vendor_observed_at=first_known - timedelta(minutes=3),
        local_captured_at=first_known - timedelta(minutes=2),
        source_raw_payload_id=None,
        source_radar_observation_id=source_id if is_radar else None,
        source_expiry_observation_id=source_id if is_expiry else None,
        source_contract_observation_id=(source_id if not is_expiry and not is_radar else None),
        source_ids={"source_request_ids": [f"fixture-{source_id}"]},
        provenance={"frozen_at_first_knowledge": True},
        specification_version="phase2a_vnext_stage4b",
        created_at=first_known,
    )


def _bundle(
    *,
    trigger_count: int = 1,
    run_trigger: str = "scheduled_daily",
    first_known: datetime = FIRST_KNOWN,
    families: tuple[str, ...] = (
        "RADAR_EVENT",
        "EXPIRY_ACTIVITY",
        "CONTRACT_PERSISTENCE",
    ),
) -> tuple[ScanRun, ProductCandidate, ProductCandidateContext, dict[UUID, int]]:
    run_id = uuid4()
    candidate_id = uuid4()
    run = ScanRun(
        id=run_id,
        trigger=run_trigger,
        status="COMPLETE",
        started_at=first_known - timedelta(minutes=10),
        completed_at=first_known,
        configuration_snapshot={},
        specification_version="phase2a_vnext_stage4b",
        market_date=first_known.astimezone(NEW_YORK).date(),
        summary={},
    )
    candidate = ProductCandidate(
        id=candidate_id,
        scan_run_id=run_id,
        ticker="NVDA",
        candidate_first_knowledge_at=first_known,
        materialization_rule_version="stage5.fixture",
        materialization_rule_hash="a" * 64,
        lifecycle_state="MATERIALIZED",
        created_at=first_known,
    )
    dte_by_trigger: dict[UUID, int] = {}
    for index in range(trigger_count):
        trigger = _trigger(
            candidate_id,
            index,
            families[index % len(families)],
            first_known=first_known,
        )
        candidate.triggers.append(trigger)
        dte_by_trigger[trigger.id] = (0, 8, 31)[index % 3]
    baseline = ProductCandidateContext(
        id=uuid4(),
        product_candidate_id=candidate_id,
        evaluation_kind="FIRST_KNOWLEDGE_BASELINE",
        candidate_first_knowledge_at=first_known,
        context_evaluated_at=first_known,
        price_as_of=None,
        context_specification_version="stage6.fixture",
        context_config_version="stage6.fixture",
        context_config_hash="b" * 64,
        price_context={"price_adjustment_semantics": "UNCONFIRMED"},
        volatility_context={},
        dealer_gex_context={},
        availability={},
        provenance={"frozen": True},
        created_at=first_known,
    )
    return run, candidate, baseline, dte_by_trigger


def _foundation(
    *,
    trigger_count: int = 1,
    run_trigger: str = "scheduled_daily",
    first_known: datetime = FIRST_KNOWN,
) -> ResearchSampleFoundation:
    run, candidate, baseline, dtes = _bundle(
        trigger_count=trigger_count,
        run_trigger=run_trigger,
        first_known=first_known,
    )
    return build_research_sample_foundation(
        candidate,
        run,
        baseline,
        dte_by_trigger_id=dtes,
    )


def _proven_basis(name: str = "fixture-adjusted-close-v1") -> PriceBasis:
    return PriceBasis(
        basis_id=name,
        corporate_action_status=CorporateActionBasisStatus.PROVEN_CONSISTENT,
        provenance={"fixture": True},
    )


def test_one_candidate_with_27_qualifying_triggers_is_one_research_sample() -> None:
    sample = _foundation(trigger_count=27)
    assert sample.cohort.qualifying_trigger_count == 27
    assert sample.sample_validity_state is ResearchSampleValidity.VALID
    assert isinstance(sample.product_candidate_id, UUID)


@pytest.mark.parametrize(
    ("trigger", "origin", "primary"),
    [
        ("scheduled_daily", RunOrigin.CANONICAL_SCHEDULED_PRODUCTION, True),
        ("cli", RunOrigin.MANUAL, False),
        ("dashboard", RunOrigin.CONTROLLED_OBSERVATION, False),
        ("diagnostic", RunOrigin.DIAGNOSTIC, False),
        ("remediation", RunOrigin.REMEDIATION, False),
        ("developer_rerun", RunOrigin.DEVELOPER_RERUN, False),
        ("unrecognized", RunOrigin.OTHER_NON_CANONICAL, False),
    ],
)
def test_explicit_run_origin_controls_primary_eligibility(
    trigger: str, origin: RunOrigin, primary: bool
) -> None:
    sample = _foundation(run_trigger=trigger)
    assert classify_scan_origin(trigger) is origin
    assert sample.run_origin is origin
    assert sample.primary_research_eligible is primary
    assert sample.product_candidate_id is not None


def test_missing_baseline_preserves_occurrence_as_invalid_instead_of_filtering() -> None:
    run, candidate, _baseline, dtes = _bundle(run_trigger="scheduled_daily")
    sample = build_research_sample_foundation(
        candidate,
        run,
        None,
        dte_by_trigger_id=dtes,
    )
    assert sample.sample_validity_state is ResearchSampleValidity.INVALID_SAMPLE
    assert sample.invalid_reason == "FROZEN_FIRST_KNOWLEDGE_BASELINE_MISSING"
    assert sample.primary_research_eligible is False


def test_frozen_baseline_identity_is_read_only_and_not_mutated() -> None:
    run, candidate, baseline, dtes = _bundle()
    baseline_identity = (
        baseline.id,
        baseline.product_candidate_id,
        baseline.evaluation_kind,
        baseline.candidate_first_knowledge_at,
        dict(baseline.provenance),
    )
    sample = build_research_sample_foundation(
        candidate,
        run,
        baseline,
        dte_by_trigger_id=dtes,
    )
    assert sample.frozen_baseline_context_id == baseline.id
    assert baseline_identity == (
        baseline.id,
        baseline.product_candidate_id,
        baseline.evaluation_kind,
        baseline.candidate_first_knowledge_at,
        baseline.provenance,
    )


def test_expired_historical_qualifying_trigger_remains_research_evidence() -> None:
    run, candidate, baseline, _dtes = _bundle(trigger_count=0)
    expired = _trigger(
        candidate.id,
        1,
        "RADAR_EVENT",
        event_date=date(2026, 7, 1),
    )
    candidate.triggers.append(expired)
    sample = build_research_sample_foundation(
        candidate,
        run,
        baseline,
        dte_by_trigger_id={expired.id: 7},
    )
    assert sample.cohort.qualifying_trigger_count == 1
    assert sample.cohort.route_composition is RouteComposition.RADAR_ONLY


def test_canonical_august_session_mapping() -> None:
    plan = map_forward_sessions(FIRST_KNOWN)
    assert plan.reference_session == date(2026, 8, 19)
    assert plan.t1_session == date(2026, 8, 20)
    assert plan.t3_session == date(2026, 8, 24)
    assert plan.t5_session == date(2026, 8, 26)


@pytest.mark.parametrize(
    "first_known",
    [
        datetime(2026, 8, 20, 10, 0, tzinfo=UTC),
        datetime(2026, 8, 20, 18, 0, tzinfo=UTC),
    ],
)
def test_premarket_and_intraday_use_prior_completed_close(first_known: datetime) -> None:
    plan = map_forward_sessions(first_known)
    assert plan.reference_session == date(2026, 8, 19)
    assert plan.t1_session == date(2026, 8, 20)


def test_post_close_and_exact_close_require_close_known_as_of_first_knowledge() -> None:
    post_close = map_forward_sessions(
        datetime(2026, 8, 20, 20, 30, tzinfo=UTC),
        same_day_close_known_as_of_first_knowledge=True,
    )
    exact_known = map_forward_sessions(
        datetime(2026, 8, 20, 20, 0, tzinfo=UTC),
        same_day_close_known_as_of_first_knowledge=True,
    )
    exact_unknown = map_forward_sessions(
        datetime(2026, 8, 20, 20, 0, tzinfo=UTC),
        same_day_close_known_as_of_first_knowledge=False,
    )
    assert post_close.reference_session == date(2026, 8, 20)
    assert post_close.t1_session == date(2026, 8, 21)
    assert exact_known.reference_session == date(2026, 8, 20)
    assert exact_unknown.reference_session == date(2026, 8, 19)
    assert exact_unknown.t1_session == date(2026, 8, 21)


def test_weekend_holiday_early_close_and_dst_are_exchange_aware() -> None:
    weekend = map_forward_sessions(datetime(2026, 8, 22, 16, 0, tzinfo=UTC))
    holiday = map_forward_sessions(datetime(2026, 9, 7, 16, 0, tzinfo=UTC))
    early_before = map_forward_sessions(datetime(2026, 11, 27, 17, 59, tzinfo=UTC))
    early_after = map_forward_sessions(
        datetime(2026, 11, 27, 18, 1, tzinfo=UTC),
        same_day_close_known_as_of_first_knowledge=True,
    )
    dst = map_forward_sessions(datetime(2026, 3, 9, 10, 0, tzinfo=UTC))
    assert (weekend.reference_session, weekend.t1_session) == (
        date(2026, 8, 21),
        date(2026, 8, 24),
    )
    assert (holiday.reference_session, holiday.t1_session) == (
        date(2026, 9, 4),
        date(2026, 9, 8),
    )
    assert (early_before.reference_session, early_before.t1_session) == (
        date(2026, 11, 25),
        date(2026, 11, 27),
    )
    assert (early_after.reference_session, early_after.t1_session) == (
        date(2026, 11, 27),
        date(2026, 11, 30),
    )
    assert (dst.reference_session, dst.t1_session) == (
        date(2026, 3, 6),
        date(2026, 3, 9),
    )


def test_t5_is_not_mature_before_august_26_official_close() -> None:
    assert (
        maturity_state(
            date(2026, 8, 26),
            evaluated_at=datetime(2026, 8, 26, 19, 59, tzinfo=UTC),
            close_present=False,
        )
        is MaturityState.NOT_YET_MATURE
    )
    assert (
        maturity_state(
            date(2026, 8, 26),
            evaluated_at=datetime(2026, 8, 26, 20, 0, tzinfo=UTC),
            close_present=False,
        )
        is MaturityState.MATURE_MISSING_DATA
    )
    assert (
        maturity_state(
            date(2026, 8, 26),
            evaluated_at=datetime(2026, 8, 26, 20, 0, tzinfo=UTC),
            close_present=True,
        )
        is MaturityState.MATURE_AVAILABLE
    )


def test_invalid_or_unprovable_samples_fail_closed_in_maturity() -> None:
    evaluated = datetime(2026, 8, 26, 21, 0, tzinfo=UTC)
    assert (
        maturity_state(
            date(2026, 8, 26),
            evaluated_at=evaluated,
            close_present=True,
            sample_valid=False,
        )
        is MaturityState.INVALID_SAMPLE
    )
    assert (
        maturity_state(
            date(2026, 8, 26),
            evaluated_at=evaluated,
            close_present=True,
            price_basis_provable=False,
        )
        is MaturityState.INVALID_SAMPLE
    )


def test_close_return_and_close_path_extremes_for_all_horizons() -> None:
    basis = _proven_basis()
    reference = ClosePriceEvidence(date(2026, 8, 19), Decimal("100"), basis)
    closes = [
        ClosePriceEvidence(date(2026, 8, 20), Decimal("110"), basis),
        ClosePriceEvidence(date(2026, 8, 21), Decimal("95"), basis),
        ClosePriceEvidence(date(2026, 8, 24), Decimal("105"), basis),
        ClosePriceEvidence(date(2026, 8, 25), Decimal("90"), basis),
        ClosePriceEvidence(date(2026, 8, 26), Decimal("102"), basis),
    ]
    t1 = calculate_close_path_outcome(reference, closes[:1])
    t3 = calculate_close_path_outcome(reference, closes[:3])
    t5 = calculate_close_path_outcome(reference, closes[:5])
    assert t1 is not None and t1.close_return == Decimal("0.1")
    assert t3 is not None and t3.close_return == Decimal("0.05")
    assert t3.max_upside == Decimal("0.1")
    assert t3.max_downside == Decimal("-0.05")
    assert t5 is not None and t5.close_return == Decimal("0.02")
    assert t5.max_upside == Decimal("0.1")
    assert t5.max_downside == Decimal("-0.1")


def test_missing_close_is_none_and_never_zero() -> None:
    basis = _proven_basis()
    reference = ClosePriceEvidence(date(2026, 8, 19), Decimal("100"), basis)
    future = [ClosePriceEvidence(date(2026, 8, 20), None, basis)]
    assert calculate_close_path_outcome(reference, future) is None


def test_v1_formula_contract_has_no_daily_high_or_low_dependency() -> None:
    assert set(ClosePriceEvidence.__dataclass_fields__) == {"session", "close", "basis"}
    source = inspect.getsource(calculate_close_path_outcome).lower()
    assert "high" not in source
    assert "low" not in source
    assert DIRECTION == "UNRESOLVED"


def test_price_basis_must_be_proven_and_identical() -> None:
    proven = _proven_basis("basis-a")
    other = _proven_basis("basis-b")
    unconfirmed = PriceBasis(
        basis_id="basis-a",
        corporate_action_status=CorporateActionBasisStatus.UNCONFIRMED,
    )
    reference = ClosePriceEvidence(date(2026, 8, 19), 100, proven)
    with pytest.raises(PriceBasisNotProvable):
        calculate_close_path_outcome(
            reference,
            [ClosePriceEvidence(date(2026, 8, 20), 101, other)],
        )
    with pytest.raises(PriceBasisNotProvable):
        calculate_close_path_outcome(
            ClosePriceEvidence(date(2026, 8, 19), 100, unconfirmed),
            [ClosePriceEvidence(date(2026, 8, 20), 101, unconfirmed)],
        )


def test_repository_ohlc_basis_is_truthfully_unconfirmed_and_fail_closed() -> None:
    default = Phase2bContextConfig.__dataclass_fields__["price_adjustment_semantics"].default
    normalized = calculate_price_context(
        {
            "data": {
                "bars": [
                    {
                        "trading_date": "2026-08-19",
                        "session": "regular",
                        "close_usd": 100,
                    }
                ]
            }
        }
    )
    assert default == "UNCONFIRMED"
    assert normalized["price_adjustment_semantics"] == "UNCONFIRMED"
    assert PRICE_BASIS_CAPABILITY == "UNCONFIRMED"


def test_canonical_dte_source_is_reused_and_raw_trigger_count_has_no_buckets() -> None:
    run, candidate, baseline, dtes = _bundle(trigger_count=3)
    sample = build_research_sample_foundation(
        candidate,
        run,
        baseline,
        dte_by_trigger_id=dtes,
    )
    assert bucket_for_dte(0) is DteBucket.VERY_SHORT
    assert bucket_for_dte(8) is DteBucket.SHORT
    assert bucket_for_dte(31) is DteBucket.MEDIUM
    assert sample.cohort.dte_bucket_counts == {
        "MEDIUM": 1,
        "SHORT": 1,
        "VERY_SHORT": 1,
    }
    assert sample.cohort.qualifying_trigger_count == 3
    assert "trigger_count_bucket" not in inspect.getsource(cohort_metadata)


def test_defensive_outcome_window_dedup_is_deterministic_and_non_destructive() -> None:
    earlier = _foundation(first_known=FIRST_KNOWN)
    later = _foundation(first_known=FIRST_KNOWN + timedelta(minutes=1))
    assert earlier.outcome_window_key == later.outcome_window_key
    occurrences = [later, earlier]
    assert deterministic_primary_occurrence(occurrences) is earlier
    assert len(occurrences) == 2


def test_research_models_are_immutable_and_append_only_compatible() -> None:
    sample = _foundation(trigger_count=3)
    row = ForwardOutcomeResearchSample(
        id=uuid4(),
        product_candidate_id=sample.product_candidate_id,
        frozen_baseline_context_id=sample.frozen_baseline_context_id,
        scan_run_id=sample.scan_run_id,
        ticker=sample.ticker,
        candidate_first_knowledge_at=sample.candidate_first_knowledge_at,
        sample_validity_state=sample.sample_validity_state.value,
        invalid_reason=sample.invalid_reason,
        run_origin=sample.run_origin.value,
        run_origin_source_trigger=sample.run_origin_source_trigger,
        run_origin_classification_version=sample.run_origin_classification_version,
        primary_research_eligible=sample.primary_research_eligible,
        has_radar=sample.cohort.has_radar,
        has_expiry_activity=sample.cohort.has_expiry_activity,
        has_contract_persistence=sample.cohort.has_contract_persistence,
        route_composition=sample.cohort.route_composition.value,
        qualifying_trigger_count=sample.cohort.qualifying_trigger_count,
        dte_bucket_counts=dict(sample.cohort.dte_bucket_counts),
        reference_price_policy=sample.reference_price_policy,
        reference_session=sample.sessions.reference_session,
        t1_session=sample.sessions.t1_session,
        t3_session=sample.sessions.t3_session,
        t5_session=sample.sessions.t5_session,
        outcome_window_key=sample.outcome_window_key,
        price_basis_capability=sample.price_basis_capability,
        price_basis_name=None,
        price_basis_provenance={"status": "UNCONFIRMED"},
        outcome_methodology_version=sample.outcome_methodology_version,
        direction=sample.direction,
        created_at=FIRST_KNOWN,
    )
    with pytest.raises(ValueError, match="frozen_baseline_context_id is immutable"):
        row.frozen_baseline_context_id = uuid4()

    measurement = ForwardOutcomeMeasurement(
        id=uuid4(),
        research_sample_id=row.id,
        horizon_sessions=1,
        target_session=sample.sessions.t1_session,
        maturity_state="MATURE_AVAILABLE",
        reference_close=Decimal("100"),
        target_close=Decimal("101"),
        close_return=Decimal("0.01"),
        max_upside=Decimal("0.01"),
        max_downside=Decimal("0.01"),
        price_basis_status="PROVEN_CONSISTENT",
        price_basis_name="fixture-adjusted-close-v1",
        price_basis_provenance={},
        input_bar_evidence={},
        outcome_methodology_version=OUTCOME_METHODOLOGY_VERSION,
        calculation_revision=1,
        calculated_at=datetime(2026, 8, 20, 21, 0, tzinfo=UTC),
        direction=DIRECTION,
        provenance={},
        created_at=datetime(2026, 8, 20, 21, 0, tzinfo=UTC),
    )
    with pytest.raises(ValueError, match="close_return is immutable"):
        measurement.close_return = Decimal("0.02")


def test_schema_is_additive_versioned_and_contains_no_backfill() -> None:
    source = MIGRATION.read_text(encoding="utf-8")
    upgrade = source.split("def upgrade() -> None:", maxsplit=1)[1].split(
        "def downgrade() -> None:", maxsplit=1
    )[0]
    assert 'revision: str = "20260827_0018"' in source
    assert 'down_revision: str | None = "20260818_0017"' in source
    assert upgrade.count("op.create_table(") == 2
    assert "op.execute(" not in upgrade
    assert "UPDATE " not in upgrade.upper()
    assert "INSERT " not in upgrade.upper()
    assert "op.drop_" not in upgrade
    assert ForwardOutcomeResearchSample.__table__.c.product_candidate_id.unique is None
    assert ForwardOutcomeMeasurement.__table__.c.close_return.nullable is True


def test_live_research_firewall_and_zero_paid_call_boundary() -> None:
    live_files = [
        ROOT / "backend" / "app" / "api" / "routes" / "scans.py",
        ROOT / "backend" / "app" / "api" / "routes" / "candidate_contexts.py",
        *sorted((ROOT / "backend" / "app" / "scanner").glob("*.py")),
    ]
    for path in live_files:
        source = path.read_text(encoding="utf-8").lower()
        assert "app.research" not in source
        assert "forward_outcome" not in source
        assert "close_return" not in source

    research_source = (ROOT / "backend" / "app" / "research" / "forward_outcome.py").read_text(
        encoding="utf-8"
    )
    assert "NightwatchClient" not in research_source
    assert "httpx" not in research_source
    assert "session.add" not in research_source
    assert '"/v1/' not in research_source
    workflows = "\n".join(
        path.read_text(encoding="utf-8")
        for path in sorted((ROOT / ".github" / "workflows").glob("*.yml"))
    ).lower()
    assert "forward outcome" not in workflows
    assert "forward-outcome" not in workflows


def test_locked_methodology_constants_are_exposed() -> None:
    assert REFERENCE_PRICE_POLICY == "PRIOR_COMPLETED_REGULAR_CLOSE"
    assert OUTCOME_METHODOLOGY_VERSION == "stage9a.close-path.v1"
    assert DIRECTION == "UNRESOLVED"

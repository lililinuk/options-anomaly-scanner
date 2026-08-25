import asyncio
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
from types import SimpleNamespace
from uuid import uuid4

import app.api.routes.scans as scan_routes
import app.scanner.candidate_persistence as candidate_persistence
import app.scanner.v13 as scanner_v13
from app.api.routes.scans import (
    _activity_public,
    _cluster_label,
    _contract_deep_dive,
    _persistence_evidence_for_projection,
    _persistent_public,
    _positioning_label,
    _vnext_anomaly_pool,
)
from app.config.settings import Settings
from app.core.time import is_xnys_session
from app.db.models import ProductCandidate, ScanRun, ScanStage
from app.scanner.candidate_projection import Stage4CandidateProjection
from app.scanner.clusters import PositioningClusterContract, build_positioning_clusters
from app.scanner.history import OiHistoryPoint, contract_persistence
from app.scanner.service import completion_status
from app.scanner.vnext import (
    ACTIVE_DISCOVERY_FAMILIES,
    REMOVED_ACTIVE_DISCOVERY_FAMILIES,
    PersistenceFreshnessPolicy,
    group_product_candidates,
    select_current_persistence_observations,
)


def _history(values: list[int]) -> list[OiHistoryPoint]:
    start = date(2026, 8, 1)
    return [
        OiHistoryPoint(start + timedelta(days=index), value)
        for index, value in enumerate(values)
    ]


def _persistence_row(
    ticker: str,
    *,
    observed_at: datetime,
    window_last: date,
    suffix: str = "PERSIST",
    expiry_observation_id: int = 1,
) -> SimpleNamespace:
    return SimpleNamespace(
        contract_symbol=f"{ticker}-{suffix}",
        ticker=ticker,
        expiration=date(2026, 8, 21),
        observed_at=observed_at,
        dte_at_detection=3,
        right="C",
        strike=Decimal("100"),
        persistent_components={
            "windows": {"3": {"net_oi_change": 100, "oi_growth": 1.0}},
            "window_first_observation_date": "2026-08-14",
            "window_last_observation_date": window_last.isoformat(),
            "valid_observation_count": 3,
            "no_lookahead_bound": "VENDOR_OI_DATE_LE_ANALYSIS_DATE",
        },
        persistent_winning_window=3,
        persistent_state="PERSISTENT_BUILD",
        persistent_positioning_score=Decimal("70"),
        history_confidence="LOW",
        history_observation_count=3,
        components={
            "dte_identity": {
                "anchor_date": window_last.isoformat(),
                "anchor_type": "VENDOR_OI_DATE",
            },
            "quote": {"availability": "AVAILABLE", "quote_as_of": observed_at.isoformat()},
        },
        expiry_observation_id=expiry_observation_id,
        deep_dive_eligible=True,
        is_candidate=True,
        classification="STRUCTURAL_CANDIDATE",
        hard_reject_reason=None,
        structure_score=Decimal("70"),
        structure_components={"same_side_expiry_oi_concentration": 25},
    )


class _PersistenceSession:
    def __init__(self, rows: list[SimpleNamespace]) -> None:
        self.rows = rows
        self.scalar_statements: list[object] = []
        self.scalars_statements: list[object] = []

    def scalar(self, statement: object) -> None:
        self.scalar_statements.append(statement)
        return None

    def scalars(self, statement: object) -> list[SimpleNamespace]:
        self.scalars_statements.append(statement)
        return self.rows

    def commit(self) -> None:
        return None


class _MissingStructureSession(_PersistenceSession):
    def __init__(self) -> None:
        super().__init__([])
        self.added: list[object] = []

    def add(self, row: object) -> None:
        self.added.append(row)

    def flush(self) -> None:
        return None


def _scanner_with_missing_deep_dive_archive(*, partial: bool) -> tuple[object, object]:
    session = _MissingStructureSession()
    scanner = object.__new__(scanner_v13.Mag7Scanner)
    scanner.partial = partial
    scanner.session = session
    scanner.run = SimpleNamespace(id=uuid4())
    scanner._stage = lambda *_args, **_kwargs: None

    async def no_persisted_radar(
        _selected: list[object], _contracts: list[object]
    ) -> int:
        return 0

    scanner._radar = no_persisted_radar
    expiry = SimpleNamespace(
        id=uuid4(),
        ticker="AMZN",
        expiration=date(2026, 8, 21),
        vendor_oi_date=date(2026, 8, 11),
    )
    return scanner, expiry


def _diagnostic_projection() -> Stage4CandidateProjection:
    trigger_counts = {
        "AAPL": 13,
        "AMZN": 10,
        "GOOGL": 9,
        "META": 4,
        "MSFT": 5,
        "NVDA": 27,
        "TSLA": 14,
    }
    observed_at = datetime(2026, 8, 20, 6, 47, tzinfo=timezone.utc)
    anomalies: list[dict[str, object]] = []
    for ticker, trigger_count in trigger_counts.items():
        for index in range(trigger_count):
            source_id = uuid4()
            anomalies.append(
                {
                    "ticker": ticker,
                    "evidence_family": "EXPIRY_ACTIVITY",
                    "anomaly_entity": "EXPIRY",
                    "anomaly_identity": f"{ticker}-EXPIRY-{index}",
                    "evidence_date": date(2026, 8, 20),
                    "qualifies_current_candidate": True,
                    "source_evidence_identity": f"expiry_observation:{source_id}",
                    "source_radar_observation_id": None,
                    "source_expiry_observation_id": source_id,
                    "source_contract_observation_id": None,
                    "source_raw_payload_id": None,
                    "trigger_first_knowledge_at": observed_at,
                    "source_first_received_at": observed_at,
                    "vendor_observed_at": observed_at,
                    "local_captured_at": observed_at,
                    "source_ids": {"raw_payload_ids": [], "source_request_ids": []},
                    "source_time_provenance": {},
                    "specification_version": "phase2a_vnext_stage4b",
                    "current_trigger_freshness": None,
                    "deep_dive_selected_for_current_run": ticker
                    in {"AAPL", "AMZN", "META", "NVDA"},
                }
            )
    return Stage4CandidateProjection(
        radar_rows=[],
        persistence_rows=[],
        persistence_analytics=[],
        activity_rows=[],
        anomaly_pool=anomalies,
        product_candidates=group_product_candidates(anomalies),
    )


def _run_persistence_selection(
    rows: list[SimpleNamespace], monkeypatch: object, policy: PersistenceFreshnessPolicy
) -> tuple[list[SimpleNamespace], SimpleNamespace, _PersistenceSession]:
    analysis_date = date(2026, 8, 18)
    expiry = SimpleNamespace(
        id=1,
        ticker="AAPL",
        expiration=date(2026, 8, 21),
        dte_at_detection=3,
        same_day_activity_score=None,
        deep_dive_eligible=False,
        radar_route_eligible=False,
        persistent_route_eligible=False,
        trigger_sources=[],
        selected_for_deep_scan=False,
    )
    ticker = SimpleNamespace(ticker="AAPL", selected_for_deep_scan=False)
    session = _PersistenceSession(rows)
    scanner = SimpleNamespace(
        run=SimpleNamespace(market_date=analysis_date),
        session=session,
        _stage=lambda *_args, **_kwargs: None,
    )
    monkeypatch.setattr(scanner_v13, "persistence_freshness_policy", lambda: policy)
    selected = scanner_v13.Mag7Scanner._select_dual(scanner, [ticker], [expiry])
    return selected, expiry, session


def test_missing_post_candidate_structure_archive_keeps_materialization_eligible(
    monkeypatch,
) -> None:
    scanner, expiry = _scanner_with_missing_deep_dive_archive(partial=False)

    contracts, clusters, radar_matches = asyncio.run(
        scanner._structure_scan([expiry], date(2026, 8, 20))
    )

    assert contracts == []
    assert clusters == []
    assert radar_matches == 0
    assert scanner.session.added == []
    assert scanner.partial is False
    status = completion_status(
        partial=scanner.partial,
        budget_limited=False,
        data_pending=False,
    )
    assert status == "COMPLETE"

    cutoff = datetime(2026, 8, 20, 6, 47, tzinfo=timezone.utc)
    run = ScanRun(
        id=uuid4(),
        trigger="test",
        status=status,
        started_at=cutoff - timedelta(minutes=3),
        completed_at=cutoff,
        market_date=date(2026, 8, 20),
        specification_version="phase2a_vnext_stage4b",
        configuration_snapshot={},
        summary={},
    )
    projection = _diagnostic_projection()
    materialization_session = _MissingStructureSession()
    monkeypatch.setattr(
        candidate_persistence,
        "load_product_candidates_for_scan",
        lambda *_args, **_kwargs: [],
    )
    monkeypatch.setattr(
        candidate_persistence,
        "load_stage4_candidate_projection",
        lambda *_args, **_kwargs: projection,
    )

    candidates = candidate_persistence.materialize_successful_scan_candidates(
        materialization_session,
        run,
        materialized_at=cutoff,
    )

    assert len(candidates) == 7
    assert sum(len(candidate.triggers) for candidate in candidates) == 82
    assert all(isinstance(candidate, ProductCandidate) for candidate in candidates)
    assert run.candidate_materialized_at == cutoff


def test_missing_structure_archive_preserves_legitimate_preexisting_partial() -> None:
    scanner, expiry = _scanner_with_missing_deep_dive_archive(partial=True)

    contracts, clusters, radar_matches = asyncio.run(
        scanner._structure_scan([expiry], date(2026, 8, 20))
    )

    assert contracts == []
    assert clusters == []
    assert radar_matches == 0
    assert scanner.session.added == []
    assert scanner.partial is True
    assert completion_status(
        partial=scanner.partial,
        budget_limited=False,
        data_pending=False,
    ) == "PARTIAL"


def test_active_stage4_vnext_stage_identifiers_fit_scan_stage_contract() -> None:
    analysis_date = date(2026, 8, 18)
    expiry = SimpleNamespace(
        id=1,
        ticker="AAPL",
        expiration=date(2026, 8, 21),
        dte_at_detection=3,
        same_day_activity_score=Decimal("80"),
        deep_dive_eligible=True,
        radar_route_eligible=False,
        persistent_route_eligible=False,
        trigger_sources=["EXPIRY_ACTIVITY"],
        selected_for_deep_scan=False,
    )
    ticker = SimpleNamespace(ticker="AAPL", selected_for_deep_scan=False)
    stage_identifiers: list[str] = []
    scanner = SimpleNamespace(
        run=SimpleNamespace(market_date=analysis_date),
        session=_PersistenceSession([]),
        _stage=lambda stage, **_details: stage_identifiers.append(stage),
    )

    selected = scanner_v13.Mag7Scanner._select_dual(scanner, [ticker], [expiry])
    max_stage_length = ScanStage.__table__.c.stage.type.length

    assert selected == [expiry]
    assert stage_identifiers == ["S4_VNEXT_DEEP_BUDGET_SELECTION"]
    assert len(stage_identifiers[0]) == 30
    assert all(stage.startswith("S4_VNEXT_") for stage in stage_identifiers)
    assert all(len(stage) <= max_stage_length for stage in stage_identifiers)


def test_active_family_set_is_exact_and_removed_families_are_explicit() -> None:
    assert ACTIVE_DISCOVERY_FAMILIES == (
        "RADAR_EVENT",
        "EXPIRY_ACTIVITY",
        "CONTRACT_PERSISTENCE",
    )
    assert REMOVED_ACTIVE_DISCOVERY_FAMILIES == (
        "EXPIRY_PERSISTENCE",
        "STRUCTURAL_COLD_START",
        "EVIDENCE_BREADTH",
    )


def test_default_freshness_is_calibration_required_without_numeric_window() -> None:
    settings = Settings(_env_file=None)
    assert settings.phase2a_persistence_current_trigger_max_vendor_age_days is None
    policy = PersistenceFreshnessPolicy(
        settings.phase2a_persistence_freshness_config_version,
        settings.phase2a_persistence_current_trigger_max_vendor_age_days,
    )
    result = policy.assess(
        window_last_observation_date=date(2026, 8, 18),
        analysis_date=date(2026, 8, 18),
    )
    assert policy.mode == "CALIBRATION_REQUIRED"
    assert result.eligible is False
    assert result.state == "CALIBRATION_REQUIRED"


def test_configured_freshness_is_versioned_and_rejects_stale_or_future_evidence() -> None:
    policy = PersistenceFreshnessPolicy("founder-approved-test-v1", 2)
    assert policy.assess(
        window_last_observation_date=date(2026, 8, 16),
        analysis_date=date(2026, 8, 18),
    ).eligible
    assert policy.assess(
        window_last_observation_date=date(2026, 8, 15),
        analysis_date=date(2026, 8, 18),
    ).state == "STALE"
    assert policy.assess(
        window_last_observation_date=date(2026, 8, 19),
        analysis_date=date(2026, 8, 18),
    ).state == "FUTURE_EVIDENCE_REJECTED"
    assert policy.snapshot()["config_version"] == "founder-approved-test-v1"


def test_contract_persistence_enforces_no_lookahead_and_exposes_window_span() -> None:
    first_three = _history([100, 150, 225])
    future = OiHistoryPoint(date(2026, 8, 20), 10000)
    baseline = contract_persistence(
        first_three,
        current_same_side_expiry_oi=1000,
        analysis_date=date(2026, 8, 3),
    )
    bounded = contract_persistence(
        [*first_three, future],
        current_same_side_expiry_oi=1000,
        analysis_date=date(2026, 8, 3),
    )
    assert bounded.score == baseline.score
    assert bounded.observation_count == 3
    assert bounded.features["window_first_observation_date"] == "2026-08-01"
    assert bounded.features["window_last_observation_date"] == "2026-08-03"
    assert bounded.features["valid_observation_count"] == 3
    assert bounded.features["no_lookahead_bound"] == "VENDOR_OI_DATE_LE_ANALYSIS_DATE"


def test_actual_selection_future_row_cannot_consume_valid_contract_identity(monkeypatch) -> None:
    analysis_date = date(2026, 8, 18)
    at_t = _persistence_row(
        "AAPL",
        observed_at=datetime(2026, 8, 18, 20, tzinfo=timezone.utc),
        window_last=analysis_date,
    )
    future = _persistence_row(
        "AAPL",
        observed_at=datetime(2026, 8, 19, 12, tzinfo=timezone.utc),
        window_last=date(2026, 8, 19),
    )
    future_materialization = _persistence_row(
        "AAPL",
        observed_at=datetime(2026, 8, 19, 12, tzinfo=timezone.utc),
        window_last=analysis_date,
    )
    configured = PersistenceFreshnessPolicy("founder-approved-test-v1", 0)

    admissible = select_current_persistence_observations(
        [future_materialization, future, at_t],
        policy=configured,
        analysis_date=analysis_date,
    )
    assert admissible == [at_t]

    baseline, baseline_expiry, _ = _run_persistence_selection(
        [at_t], monkeypatch, configured
    )
    with_future, future_expiry, session = _run_persistence_selection(
        [future_materialization, future, at_t], monkeypatch, configured
    )
    assert len(baseline) == len(with_future) == 1
    assert baseline_expiry.persistent_route_eligible is True
    assert future_expiry.persistent_route_eligible is True
    assert baseline_expiry.trigger_sources == future_expiry.trigger_sources == [
        "CONTRACT_PERSISTENCE"
    ]
    assert any(
        "contract_scan_observations.observed_at <" in str(statement)
        for statement in session.scalars_statements
    )
    monkeypatch.setattr(scan_routes, "persistence_freshness_policy", lambda: configured)
    future_public = _persistent_public(future_materialization, analysis_date=analysis_date)
    assert future_public["current_trigger_eligible"] is False
    assert future_public["current_trigger_freshness"]["state"] == (
        "INADMISSIBLE_OBSERVATION_TIME"
    )


def test_actual_selection_preserves_calibration_required_with_future_first(monkeypatch) -> None:
    analysis_date = date(2026, 8, 18)
    at_t = _persistence_row(
        "AAPL",
        observed_at=datetime(2026, 8, 18, 20, tzinfo=timezone.utc),
        window_last=analysis_date,
    )
    future = _persistence_row(
        "AAPL",
        observed_at=datetime(2026, 8, 19, 12, tzinfo=timezone.utc),
        window_last=date(2026, 8, 19),
    )
    calibration_required = PersistenceFreshnessPolicy("calibration-required-test-v1", None)

    baseline, baseline_expiry, _ = _run_persistence_selection(
        [at_t], monkeypatch, calibration_required
    )
    with_future, future_expiry, _ = _run_persistence_selection(
        [future, at_t], monkeypatch, calibration_required
    )
    assert baseline == with_future == []
    assert baseline_expiry.persistent_route_eligible is False
    assert future_expiry.persistent_route_eligible is False
    assert baseline_expiry.trigger_sources == future_expiry.trigger_sources == []


def test_product_projection_groups_all_anomalies_without_top_n_or_scores() -> None:
    anomalies = []
    for ticker in ("AAPL", "AMZN", "GOOGL", "META", "MSFT", "NVDA", "TSLA"):
        anomalies.append(
            {
                "ticker": ticker,
                "evidence_family": "RADAR_EVENT",
                "anomaly_identity": f"{ticker}-CONTRACT",
                "qualifies_current_candidate": True,
            }
        )
    anomalies.extend(
        [
            {
                "ticker": "NVDA",
                "evidence_family": "EXPIRY_ACTIVITY",
                "anomaly_identity": "2026-08-21",
                "qualifies_current_candidate": True,
            },
            {
                "ticker": "NVDA",
                "evidence_family": "EXPIRY_PERSISTENCE",
                "anomaly_identity": "REMOVED",
                "qualifies_current_candidate": True,
            },
            {
                "ticker": "MSFT",
                "evidence_family": "CONTRACT_PERSISTENCE",
                "anomaly_identity": "STALE",
                "qualifies_current_candidate": False,
            },
        ]
    )
    projections = group_product_candidates(anomalies)
    assert len(projections) == 7
    nvda = next(row for row in projections if row["ticker"] == "NVDA")
    assert nvda["anomaly_count"] == 2
    assert nvda["qualifying_anomaly_count"] == 2
    assert [row["anomaly_identity"] for row in nvda["anomalies"]] == [
        "NVDA-CONTRACT",
        "2026-08-21",
    ]
    assert "score" not in nvda
    msft = next(row for row in projections if row["ticker"] == "MSFT")
    assert msft["anomaly_count"] == 2
    assert msft["qualifying_anomaly_count"] == 1
    assert msft["active_trigger_sources"] == ["RADAR_EVENT"]


def test_production_projection_keeps_seven_persistence_candidates_before_budget(
    monkeypatch,
) -> None:
    analysis_date = date(2026, 8, 18)
    tickers = ("AAPL", "AMZN", "GOOGL", "META", "MSFT", "NVDA", "TSLA")
    rows = [
        _persistence_row(
            ticker,
            observed_at=datetime(2026, 8, 18, 20, tzinfo=timezone.utc),
            window_last=analysis_date,
            expiry_observation_id=index + 1,
        )
        for index, ticker in enumerate(tickers)
    ]
    policy = PersistenceFreshnessPolicy("founder-approved-test-v1", 0)
    monkeypatch.setattr(scanner_v13, "persistence_freshness_policy", lambda: policy)
    monkeypatch.setattr(scan_routes, "persistence_freshness_policy", lambda: policy)
    expiry_rows = [
        SimpleNamespace(
            id=index + 1,
            ticker=ticker,
            expiration=date(2026, 8, 21),
            dte_at_detection=3,
            same_day_activity_score=None,
            deep_dive_eligible=False,
            radar_route_eligible=False,
            persistent_route_eligible=False,
            trigger_sources=[],
            selected_for_deep_scan=False,
        )
        for index, ticker in enumerate(tickers)
    ]
    ticker_rows = [
        SimpleNamespace(ticker=ticker, selected_for_deep_scan=False) for ticker in tickers
    ]
    selection_session = _PersistenceSession(rows)
    scanner = SimpleNamespace(
        run=SimpleNamespace(market_date=analysis_date),
        session=selection_session,
        _stage=lambda *_args, **_kwargs: None,
    )
    selected_expiries = scanner_v13.Mag7Scanner._select_dual(
        scanner, ticker_rows, expiry_rows
    )
    selected_tickers = {row.ticker for row in selected_expiries}
    current_run_deep_dive = [row for row in rows if row.ticker in selected_tickers]
    session = _PersistenceSession(rows)

    payload = scan_routes._v13_sections(
        session,
        SimpleNamespace(market_date=analysis_date),
        [],
        current_run_deep_dive,
    )
    evidence = payload["persistent_positioning"]
    anomaly_pool = payload["anomaly_pool"]
    candidates = payload["research_candidates"]

    assert len(evidence) == 7
    assert len(candidates) == 7
    assert len(selected_tickers) == 4
    assert sum(row["deep_dive_selected_for_current_run"] for row in anomaly_pool) == 4
    assert payload["route_counts"]["contract_persistence_current_triggers"] == 7
    assert payload["route_counts"]["contract_persistence_analytics"] == 4
    assert {row["ticker"] for row in candidates} == set(tickers)
    for candidate in candidates:
        assert candidate["active_trigger_sources"] == ["CONTRACT_PERSISTENCE"]
        assert candidate["qualifying_anomaly_count"] == 1
        assert candidate["anomalies"][0]["qualifies_current_candidate"] is True


def test_production_projection_preserves_each_active_route_and_mixed_evidence(
    monkeypatch,
) -> None:
    analysis_date = date(2026, 8, 18)
    policy = PersistenceFreshnessPolicy("founder-approved-test-v1", 0)
    monkeypatch.setattr(scan_routes, "persistence_freshness_policy", lambda: policy)
    radar = SimpleNamespace(
        contract_symbol="AAPL-RADAR",
        ticker="AAPL",
        observation_date=analysis_date,
        matched_expiration=date(2026, 8, 21),
        matched_dte=3,
        deep_dive_eligible=True,
        premium=Decimal("200000"),
        delta_oi=3000,
        archive_completeness="COMPLETE",
        risk_flags=[],
    )
    activity = SimpleNamespace(
        id=99,
        ticker="AMZN",
        expiration=date(2026, 8, 21),
        dte_at_detection=3,
        same_day_score_basis="BALANCED",
        same_day_activity_score=Decimal("70"),
        neighbor_ratio=Decimal("2"),
        deep_dive_eligible=True,
        components={
            "dte_identity": {
                "anchor_date": analysis_date.isoformat(),
                "anchor_type": "NY_MARKET_SESSION_DATE",
            }
        },
    )
    persistence_only = _persistence_row(
        "GOOGL",
        observed_at=datetime(2026, 8, 18, 20, tzinfo=timezone.utc),
        window_last=analysis_date,
    )
    mixed = _persistence_row(
        "AAPL",
        observed_at=datetime(2026, 8, 18, 20, tzinfo=timezone.utc),
        window_last=analysis_date,
        suffix="PERSIST",
    )

    pool = _vnext_anomaly_pool(
        [radar],
        [persistence_only, mixed],
        [activity],
        contracts=[],
        clusters=[],
        analysis_date=analysis_date,
    )
    candidates = group_product_candidates(pool)

    assert {row["ticker"] for row in candidates} == {"AAPL", "AMZN", "GOOGL"}
    sources = {row["ticker"]: row["active_trigger_sources"] for row in candidates}
    assert sources == {
        "AAPL": ["RADAR_EVENT", "CONTRACT_PERSISTENCE"],
        "AMZN": ["EXPIRY_ACTIVITY"],
        "GOOGL": ["CONTRACT_PERSISTENCE"],
    }


def test_calibration_required_persistence_stays_supporting_only(monkeypatch) -> None:
    analysis_date = date(2026, 8, 18)
    row = _persistence_row(
        "AAPL",
        observed_at=datetime(2026, 8, 18, 20, tzinfo=timezone.utc),
        window_last=analysis_date,
    )
    policy = PersistenceFreshnessPolicy("calibration-required-test-v1", None)
    monkeypatch.setattr(scan_routes, "persistence_freshness_policy", lambda: policy)
    session = _PersistenceSession([row])

    evidence = _persistence_evidence_for_projection(
        session,
        analysis_date=analysis_date,
        current_run_analytics=[row],
    )
    persistence_pool = _vnext_anomaly_pool(
        [], evidence, [], contracts=[row], clusters=[], analysis_date=analysis_date
    )
    assert group_product_candidates(persistence_pool) == []

    radar_support = {
        "ticker": "AAPL",
        "evidence_family": "RADAR_EVENT",
        "anomaly_identity": "AAPL-RADAR",
        "qualifies_current_candidate": True,
    }
    candidate = group_product_candidates([radar_support, *persistence_pool])[0]
    assert candidate["active_trigger_sources"] == ["RADAR_EVENT"]
    assert candidate["anomaly_count"] == 2
    persistence = next(
        item for item in candidate["anomalies"] if item["evidence_family"] == "CONTRACT_PERSISTENCE"
    )
    assert persistence["qualifies_current_candidate"] is False
    assert persistence["current_trigger_freshness"]["state"] == "CALIBRATION_REQUIRED"


def test_cluster_missing_components_remain_null_and_invalid_is_not_positive() -> None:
    candidates = [
        PositioningClusterContract(
            id="a",
            strike=Decimal("100"),
            open_interest=100,
            structure_score=65,
            liquidity_points=None,
            spot=Decimal("100"),
            net_oi_changes={"3": None},
        ),
        PositioningClusterContract(
            id="b",
            strike=Decimal("105"),
            open_interest=200,
            structure_score=65,
            liquidity_points=None,
            spot=Decimal("100"),
            net_oi_changes={"3": 5},
        ),
    ]
    result = build_positioning_clusters(
        candidates=candidates,
        full_strike_ladder=[Decimal("100"), Decimal("105")],
        same_side_expiry_oi=0,
    )[0]
    assert result.components["same_side_expiry_oi_concentration"] is None
    assert result.components["liquidity"] is None
    assert result.net_oi_changes == {"3": 5}

    invalid = SimpleNamespace(
        classification="INVALID_CLUSTER", min_strike=100, max_strike=105
    )
    valid = SimpleNamespace(
        classification="VALID_CLUSTER", min_strike=100, max_strike=105
    )
    assert _cluster_label(invalid) is None
    assert _positioning_label(invalid, None) == "NO_STRONG_STRUCTURE"
    assert _positioning_label(valid, None) == "CALL_STRUCTURE"


def test_subthreshold_structure_is_context_but_not_positive_evidence() -> None:
    row = SimpleNamespace(
        is_candidate=False,
        classification="OBSERVE",
        hard_reject_reason=None,
        structure_score=Decimal("55"),
        structure_components={"liquidity_quality": None},
        components={
            "quote": {"availability": "UNAVAILABLE", "quote_as_of": None}
        },
    )
    context = _contract_deep_dive(row)
    assert context["structure_positive_evidence"] is False
    assert context["structure"]["score"] == 55.0
    assert context["quote"]["availability"] == "UNAVAILABLE"


def test_api_comparator_and_zero_dte_basis_fields_are_truthful() -> None:
    row = SimpleNamespace(
        ticker="NVDA",
        expiration=date(2026, 8, 21),
        dte_at_detection=3,
        same_day_activity_score=Decimal("60"),
        volume_share=Decimal("0.2"),
        volume_share_points=Decimal("25"),
        neighbor_ratio=Decimal("2"),
        comparable_peer_count=3,
        comparable_peer_dtes=[2, 4, 5],
        comparable_peer_quality="DISTANCE_COMPARABLE",
        comparable_peer_median_volume=Decimal("500"),
        neighbor_points=Decimal("15"),
        same_day_score_basis="BALANCED",
        standard_monthly_inferred=False,
        monthly_context_source=None,
        same_day_baseline_status="CURRENT_SESSION_NONZERO_DTE",
        baseline_observation_count=None,
        components={
            "same_day": {"comparable_expiry_volume_neighbor_ratio": 15},
            "dte_identity": {
                "anchor_date": "2026-08-18",
                "anchor_type": "NY_MARKET_SESSION_DATE",
            },
            "raw_cross_expiry_neighbor_ratio_descriptive_only": 9,
        },
    )
    public = _activity_public(row)
    assert public["comparable_neighbor_ratio"] == 2.0
    assert public["comparable_peer_median_volume"] == 500.0
    assert public["raw_cross_expiry_neighbor_ratio_descriptive_only"] == 9
    assert public["dte_anchor_type"] == "NY_MARKET_SESSION_DATE"


def test_persistence_api_keeps_analytics_but_disables_current_trigger_by_default() -> None:
    row = SimpleNamespace(
        ticker="NVDA",
        contract_symbol="NVDA-CONTRACT",
        expiration=date(2026, 8, 21),
        dte_at_detection=3,
        right="C",
        strike=Decimal("100"),
        persistent_components={
            "windows": {"3": {"net_oi_change": 100, "oi_growth": 1.0}},
            "window_first_observation_date": "2026-08-14",
            "window_last_observation_date": "2026-08-18",
            "valid_observation_count": 3,
            "no_lookahead_bound": "VENDOR_OI_DATE_LE_ANALYSIS_DATE",
        },
        persistent_winning_window=3,
        persistent_state="PERSISTENT_BUILD",
        persistent_positioning_score=Decimal("70"),
        history_confidence="LOW",
        history_observation_count=3,
        components={
            "dte_identity": {
                "anchor_date": "2026-08-18",
                "anchor_type": "VENDOR_OI_DATE",
            },
            "quote": {"availability": "AVAILABLE", "quote_as_of": "2026-08-18T20:00:00Z"},
        },
    )
    public = _persistent_public(row, analysis_date=date(2026, 8, 18))
    assert public["persistent_score"] == 70.0
    assert public["current_trigger_eligible"] is False
    assert public["current_trigger_freshness"]["state"] == "CALIBRATION_REQUIRED"
    assert public["window_first_observation_date"] == "2026-08-14"
    assert public["quote_as_of"] == "2026-08-18T20:00:00Z"


def test_xnys_session_validation_is_explicit() -> None:
    assert is_xnys_session(date(2026, 8, 18)) is True
    assert is_xnys_session(date(2026, 8, 16)) is False

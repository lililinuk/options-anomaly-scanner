from __future__ import annotations

import inspect
from datetime import date
from types import SimpleNamespace

from app.api.routes import scans
from app.api.routes.scans import _run_state, _zero_dte_public


def test_stage7_preserves_all_run_states_without_empty_success_conflation() -> None:
    assert _run_state(None, candidate_count=0) == "NOT_RUN"
    assert _run_state(SimpleNamespace(status="RUNNING"), candidate_count=0) == "RUNNING"
    assert _run_state(SimpleNamespace(status="FAILED"), candidate_count=0) == "FAILED"
    assert _run_state(SimpleNamespace(status="PARTIAL"), candidate_count=0) == "FAILED"
    assert (
        _run_state(SimpleNamespace(status="COMPLETE"), candidate_count=0)
        == "SUCCESS_NO_CANDIDATE"
    )
    assert (
        _run_state(SimpleNamespace(status="COMPLETE"), candidate_count=7)
        == "SUCCESS_WITH_CANDIDATES"
    )


def test_stage7_zero_dte_read_model_keeps_identity_and_maturity_separate() -> None:
    row = SimpleNamespace(
        ticker="NVDA",
        expiration=date(2026, 8, 20),
        dte_at_detection=0,
        bucket_at_detection="0-7",
        same_day_activity_score=None,
        same_day_score_basis="HISTORY_IMMATURE",
        volume_share=None,
        neighbor_ratio=None,
        comparable_peer_count=0,
        comparable_peer_dtes=[],
        comparable_peer_quality="ZERO_DTE_DESCRIPTIVE_ONLY",
        current_expiry_volume=100,
        same_day_baseline_status="INSUFFICIENT",
        baseline_observation_count=4,
        baseline_20_mean_volume_share=None,
        baseline_20_median_volume_share=None,
        baseline_20_mad_volume_share=None,
        historical_percentile_20=None,
        robust_deviation=None,
        zero_dte_baseline_method="CANONICAL_PRIOR_SESSIONS",
        components={},
    )

    payload = _zero_dte_public(
        row,
        current_snapshot_kind="PROVISIONAL_INTRADAY",
    )

    assert payload["current_snapshot_kind"] == "PROVISIONAL_INTRADAY"
    assert payload["canonical_history_maturity"] == "HISTORY_IMMATURE"
    assert payload["baseline_observation_count"] == 4
    assert payload["baseline_required"] == 20


def test_stage7_latest_scan_serializes_persisted_candidates_without_materializing() -> None:
    source = inspect.getsource(scans.latest_mag7_scan)
    assert "load_product_candidates_for_scan" in source
    assert "product_candidate_public" in source
    assert "materialize_successful_scan_candidates" not in source

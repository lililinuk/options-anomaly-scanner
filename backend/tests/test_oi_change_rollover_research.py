import inspect
import json
from dataclasses import asdict
from datetime import date, datetime, timezone
from pathlib import Path

import pytest

from app.research import oi_change_rollover as experiment


def payload(*rows: dict[str, object]) -> dict[str, object]:
    return {"data": {"contracts": list(rows)}}


def row(
    observation_date: str = "2026-08-17",
    *,
    previous_date: str = "2026-08-14",
    rank: int = 1,
) -> dict[str, object]:
    return {
        "date": observation_date,
        "prev_date": previous_date,
        "rank": rank,
        "premium_usd": 123.45,
        "oi_diff": 100,
    }


def summarize(*rows: dict[str, object]) -> experiment.ProbeRecord:
    return experiment.summarize_response(
        ticker="NVDA",
        payload=payload(*rows),
        http_status=200,
        request_time_utc=datetime(2026, 8, 18, 9, tzinfo=timezone.utc),
        expected_session=date(2026, 8, 17),
        github_run_id="123",
        github_run_attempt="1",
        network_attempts=1,
        retries=0,
        quota_remaining_after=99_000,
    )


def test_valid_vendor_response_parsing_is_safe_and_current() -> None:
    result = summarize(row(rank=9), row(rank=2))

    assert result.success
    assert result.result_state == "SUCCESS"
    assert result.row_count == 2
    assert result.distinct_observation_dates == ["2026-08-17"]
    assert result.distinct_previous_dates == ["2026-08-14"]
    assert result.latest_date_row_count == 2
    assert result.non_null_premium_usd_count == 2
    assert result.non_null_oi_diff_count == 2
    assert result.vendor_rank_min == 2
    assert result.vendor_rank_max == 9
    assert result.freshness_state == "CURRENT"
    assert result.trading_session_lag == 0


@pytest.mark.parametrize("count", [1, 7, 53])
def test_variable_row_counts_are_not_treated_as_an_invariant(count: int) -> None:
    result = summarize(*(row(rank=index + 1) for index in range(count)))
    assert result.row_count == count
    assert result.latest_date_row_count == count
    assert result.success


def test_multiple_observation_dates_are_explicitly_ambiguous() -> None:
    result = summarize(row("2026-08-14"), row("2026-08-17"))

    assert result.distinct_observation_dates == ["2026-08-14", "2026-08-17"]
    assert result.latest_observation_date == "2026-08-17"
    assert result.freshness_state == "AMBIGUOUS"
    assert result.result_state == "AMBIGUOUS_OBSERVATION_DATES"
    assert not result.success


def test_empty_response_is_unavailable_not_stale() -> None:
    result = summarize()

    assert result.row_count == 0
    assert result.result_state == "EMPTY_RESPONSE"
    assert result.freshness_state == "UNAVAILABLE"
    assert result.trading_session_lag is None


def test_malformed_or_missing_observation_date_is_not_fabricated() -> None:
    result = summarize(
        {"date": "not-a-date", "prev_date": "2026-08-14"},
        {"prev_date": "2026-08-14"},
    )

    assert result.invalid_observation_date_count == 2
    assert result.latest_observation_date is None
    assert result.result_state == "NO_OBSERVATION_DATE"
    assert result.freshness_state == "UNAVAILABLE"


def test_expected_session_uses_xnys_not_previous_calendar_day() -> None:
    assert experiment.expected_latest_completed_session(date(2026, 8, 18)) == date(2026, 8, 17)
    assert experiment.expected_latest_completed_session(date(2026, 8, 24)) == date(2026, 8, 21)


def test_weekend_is_not_an_eligible_probe_session() -> None:
    assert experiment.expected_latest_completed_session(date(2026, 8, 23)) is None


def test_experiment_date_guard_is_hard_and_timezone_aware() -> None:
    eligible = experiment.evaluate_experiment_guard(datetime(2026, 8, 18, 9, tzinfo=timezone.utc))
    before_window = experiment.evaluate_experiment_guard(
        datetime(2026, 8, 17, 9, tzinfo=timezone.utc)
    )
    after_window = experiment.evaluate_experiment_guard(
        datetime(2026, 8, 25, 9, tzinfo=timezone.utc)
    )

    assert eligible.eligible
    assert eligible.new_york_date == date(2026, 8, 18)
    assert eligible.expected_latest_completed_xnys_session == date(2026, 8, 17)
    assert not before_window.eligible
    assert not after_window.eligible


@pytest.mark.parametrize(
    ("observed", "invalid", "expected_state"),
    [
        ([date(2026, 8, 17)], 0, "CURRENT"),
        ([date(2026, 8, 14)], 0, "STALE"),
        ([date(2026, 8, 18)], 0, "AHEAD_OR_UNEXPECTED"),
        ([], 0, "UNAVAILABLE"),
        ([date(2026, 8, 17)], 1, "AMBIGUOUS"),
    ],
)
def test_freshness_classification(observed: list[date], invalid: int, expected_state: str) -> None:
    assert (
        experiment.freshness_state(observed, invalid_date_count=invalid, expected=date(2026, 8, 17))
        == expected_state
    )


def cumulative_record(
    ticker: str,
    request_time: str,
    state: str,
    *,
    run_id: str,
) -> dict[str, object]:
    record = asdict(summarize(row()))
    record.update(
        {
            "github_run_id": run_id,
            "ticker": ticker,
            "request_time_new_york": request_time,
            "expected_latest_completed_xnys_session": "2026-08-17",
            "latest_observation_date": ("2026-08-17" if state == "CURRENT" else "2026-08-14"),
            "freshness_state": state,
        }
    )
    return record


def test_first_seen_uses_earliest_current_probe() -> None:
    records = [
        cumulative_record("NVDA", "2026-08-18T06:00:00-04:00", "CURRENT", run_id="2"),
        cumulative_record("NVDA", "2026-08-18T07:00:00-04:00", "CURRENT", run_id="3"),
    ]

    result = experiment.cumulative_rows(records)[0]
    assert result["first_current_probe"] == "2026-08-18T06:00:00-04:00"
    assert result["last_stale_probe"] is None


def test_last_stale_and_publication_window_are_bounded_by_probes() -> None:
    records = [
        cumulative_record("AAPL", "2026-08-18T05:00:00-04:00", "STALE", run_id="1"),
        cumulative_record("AAPL", "2026-08-18T06:00:00-04:00", "STALE", run_id="2"),
        cumulative_record("AAPL", "2026-08-18T07:00:00-04:00", "CURRENT", run_id="3"),
    ]

    result = experiment.cumulative_rows(records)[0]
    assert result["last_stale_probe"] == "2026-08-18T06:00:00-04:00"
    assert result["first_current_probe"] == "2026-08-18T07:00:00-04:00"
    assert result["observed_publication_window"] == (
        "(2026-08-18T06:00:00-04:00, 2026-08-18T07:00:00-04:00]"
    )
    assert result["premarket_by_09_25_et"] == "YES"


def test_cross_ticker_staggered_rollover_is_descriptive() -> None:
    records = [
        cumulative_record("NVDA", "2026-08-18T06:00:00-04:00", "CURRENT", run_id="1"),
        cumulative_record("AAPL", "2026-08-18T07:00:00-04:00", "CURRENT", run_id="2"),
        cumulative_record("TSLA", "2026-08-18T07:00:00-04:00", "CURRENT", run_id="2"),
    ]
    rows = experiment.cumulative_rows(records)

    assert experiment.cross_ticker_rollover(rows) == {"2026-08-17": "STAGGERED"}


def test_cross_ticker_same_workflow_run_is_within_probe_resolution() -> None:
    records = [
        cumulative_record("NVDA", "2026-08-18T07:00:01-04:00", "CURRENT", run_id="10"),
        cumulative_record("AAPL", "2026-08-18T07:00:03-04:00", "CURRENT", run_id="10"),
        cumulative_record("TSLA", "2026-08-18T07:00:05-04:00", "CURRENT", run_id="10"),
    ]
    rows = experiment.cumulative_rows(records)

    assert experiment.cross_ticker_rollover(rows) == {
        "2026-08-17": "SIMULTANEOUS_WITHIN_PROBE_RESOLUTION"
    }


@pytest.mark.asyncio
async def test_dry_run_output_never_contains_secret(
    tmp_path, monkeypatch: pytest.MonkeyPatch
) -> None:
    secret = "test-secret-must-not-appear"
    monkeypatch.setenv("NIGHTWATCH_API_KEY", secret)

    exit_code = await experiment.probe_command("dry_run", tmp_path)

    assert exit_code == 0
    for path in tmp_path.iterdir():
        assert secret not in path.read_text(encoding="utf-8")
    document = json.loads((tmp_path / "probe_results.json").read_text(encoding="utf-8"))
    assert document["run"]["nightwatch_requests"] == 0
    assert document["records"] == []


def test_research_module_has_no_database_write_path() -> None:
    source = inspect.getsource(experiment)

    assert "app.db" not in source
    assert "get_session_factory" not in source
    assert "DATABASE_URL" not in source
    assert "INSERT " not in source
    assert "UPDATE " not in source
    assert "DELETE " not in source
    assert "DDL" not in source


def test_workflow_is_isolated_and_has_the_exact_august_schedule() -> None:
    workflow = (
        Path(__file__).resolve().parents[2]
        / ".github"
        / "workflows"
        / "oi-change-rollover-timing-experiment.yml"
    ).read_text(encoding="utf-8")

    for cron in (
        "0 9-13 * * 1-5",
        "25 13 * * 1-5",
        "45 13 * * 1-5",
        "15 14 * * 1-5",
        "45 14 * * 1-5",
        "15 15 * * 1-5",
    ):
        assert f'cron: "{cron}"' in workflow
    assert "oi-change-rollover-timing-experiment" in workflow
    assert "NIGHTWATCH_API_KEY: ${{ secrets.NIGHTWATCH_API_KEY }}" in workflow
    assert "DATABASE_URL" not in workflow
    assert "${{ runner.temp }}" not in workflow
    assert "PRIOR_DIR: ../.oi-change-rollover-prior" in workflow
    assert "dealer-gex-daily-archive" not in workflow
    assert "workflow_dispatch:" in workflow
    assert "actions/upload-artifact@v6" in workflow

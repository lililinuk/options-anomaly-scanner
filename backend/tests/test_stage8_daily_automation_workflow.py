from pathlib import Path
from types import SimpleNamespace

import pytest

import app.cli as cli

ROOT = Path(__file__).resolve().parents[2]
WORKFLOW = ROOT / ".github" / "workflows" / "phase2a-daily-archive.yml"


def test_daily_workflow_has_no_automatic_schedule_after_gcp_cutover() -> None:
    source = WORKFLOW.read_text(encoding="utf-8")
    assert "schedule:" not in source
    assert "cron:" not in source
    assert "archive-mag7-daily --mode radar-oi" in source
    assert "archive-mag7-daily --mode activity" in source
    assert "--scheduled" not in source


def test_manual_workflow_cannot_run_vnext_production_observation() -> None:
    source = WORKFLOW.read_text(encoding="utf-8")
    assert "workflow_dispatch:" in source
    assert "daily-vnext-observation:" not in source
    assert "run-daily-vnext-observation" not in source


def test_workflow_is_read_only_at_github_and_has_no_retry_or_dispatch_step() -> None:
    source = WORKFLOW.read_text(encoding="utf-8")
    assert "contents: read" in source
    assert "retry" not in source.lower()
    assert "workflow_run" not in source
    assert "actions/github-script" not in source


def test_daily_entrypoint_preserves_accepted_stage8_remediations() -> None:
    cli_source = (ROOT / "backend" / "app" / "cli.py").read_text(encoding="utf-8")
    scanner_source = (ROOT / "backend" / "app" / "scanner" / "v13.py").read_text(encoding="utf-8")
    model_source = (ROOT / "backend" / "app" / "db" / "models.py").read_text(encoding="utf-8")
    assert "max_retries=0" in cli_source
    assert "S4_VNEXT_DEEP_BUDGET_SELECTION" in scanner_source
    assert "partial_before_deep_dive" in scanner_source
    assert "none_as_null=True" in model_source


class _CliSession:
    def __enter__(self):
        return self

    def __exit__(self, *_args) -> None:  # type: ignore[no-untyped-def]
        return None

    def execute(self, _statement) -> None:  # type: ignore[no-untyped-def]
        return None


class _CliClient:
    async def __aenter__(self):
        return self

    async def __aexit__(self, *_args) -> None:  # type: ignore[no-untyped-def]
        return None


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("status", "expected"),
    [
        ("COMPLETE", 0),
        ("NO_NEW_DATA", 0),
        ("FAILED", 6),
        ("PARTIAL", 6),
    ],
)
async def test_daily_cli_exit_code_matches_persisted_terminal_status(
    monkeypatch: pytest.MonkeyPatch,
    status: str,
    expected: int,
) -> None:
    summary = SimpleNamespace(
        daily_run_id="run-id",
        status=status,
        subjobs={"daily_oi": {"status": status}},
        consumed_quota_units=0,
        network_attempts=0,
        elapsed_seconds=0.0,
    )

    class Pipeline:
        def __init__(self, _session, _client) -> None:  # type: ignore[no-untyped-def]
            pass

        async def execute(self, **_kwargs):  # type: ignore[no-untyped-def]
            return summary

    monkeypatch.setattr(
        cli,
        "get_settings",
        lambda: SimpleNamespace(
            nightwatch_base_url="https://example.invalid",
            nightwatch_api_key="redacted-test-value",
            nightwatch_timeout_seconds=1,
            nightwatch_max_concurrency=1,
        ),
    )
    monkeypatch.setattr(cli, "get_session_factory", lambda: lambda: _CliSession())
    monkeypatch.setattr(cli, "NightwatchClient", lambda **_kwargs: _CliClient())
    monkeypatch.setattr(cli, "DailyDataPipeline", Pipeline)

    assert await cli.run_archive_mag7_daily(mode="radar-oi", scheduled=False) == expected


@pytest.mark.asyncio
async def test_legitimate_scheduled_skip_remains_green(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        cli,
        "radar_oi_schedule_plan",
        lambda _now: SimpleNamespace(
            should_collect=False,
            status="SKIPPED_NON_TRADING_SESSION",
            market_date="2026-08-29",
        ),
    )

    def forbidden_settings():
        raise AssertionError("scheduler skip must happen before runtime/network setup")

    monkeypatch.setattr(cli, "get_settings", forbidden_settings)
    assert await cli.run_archive_mag7_daily(mode="radar-oi", scheduled=True) == 0

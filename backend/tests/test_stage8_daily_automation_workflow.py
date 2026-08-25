from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
WORKFLOW = ROOT / ".github" / "workflows" / "phase2a-daily-archive.yml"


def test_daily_workflow_has_evidence_backed_new_york_schedules() -> None:
    source = WORKFLOW.read_text(encoding="utf-8")
    assert 'cron: "30 6 * * 1-5"' in source
    assert 'cron: "30 16 * * 1-5"' in source
    assert source.count('timezone: "America/New_York"') == 2
    assert "archive-mag7-daily --mode radar-oi --scheduled" in source
    assert "archive-mag7-daily --mode activity --scheduled" in source


def test_scheduled_observation_is_ordered_after_activity_and_source_gated() -> None:
    source = WORKFLOW.read_text(encoding="utf-8")
    observation = source.split("  daily-vnext-observation:", maxsplit=1)[1]
    assert "needs: activity-archive" in observation
    assert "github.event_name == 'schedule'" in observation
    assert "run-daily-vnext-observation" in observation
    assert source.count("run-daily-vnext-observation") == 1
    assert "workflow_dispatch" not in observation.split("steps:", maxsplit=1)[0]


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

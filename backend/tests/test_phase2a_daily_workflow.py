from pathlib import Path

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
WORKFLOW = REPOSITORY_ROOT / ".github" / "workflows" / "phase2a-daily-archive.yml"


def test_phase2a_daily_workflow_is_manual_collection_only_after_cutover() -> None:
    workflow = WORKFLOW.read_text(encoding="utf-8")
    assert "schedule:" not in workflow
    assert "cron:" not in workflow
    assert "workflow_dispatch:" in workflow
    assert "- activity" in workflow
    assert "- radar-oi" in workflow
    assert "archive-mag7-daily --mode activity" in workflow
    assert "archive-mag7-daily --mode radar-oi" in workflow
    assert "--scheduled" not in workflow
    assert "run-daily-vnext-observation" not in workflow


def test_phase2a_daily_workflow_keeps_server_side_safety_boundaries() -> None:
    workflow = WORKFLOW.read_text(encoding="utf-8")
    assert "contents: read" in workflow
    assert "group: phase2a-daily-archive" in workflow
    assert "cancel-in-progress: false" in workflow
    assert "DATABASE_URL: ${{ secrets.DATABASE_URL }}" in workflow
    assert "NIGHTWATCH_API_KEY: ${{ secrets.NIGHTWATCH_API_KEY }}" in workflow
    assert "NEXT_PUBLIC" not in workflow
    assert "dealer-gex" not in workflow.lower()

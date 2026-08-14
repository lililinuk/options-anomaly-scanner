from __future__ import annotations

from pathlib import Path

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
WORKFLOW = REPOSITORY_ROOT / ".github" / "workflows" / "dealer-gex-archive.yml"


def test_dealer_gex_workflow_uses_accepted_scheduler_contract() -> None:
    contents = WORKFLOW.read_text(encoding="utf-8")

    required_fragments = (
        "name: Dealer GEX Daily Archive",
        'cron: "30 15 * * 1-5"',
        'timezone: "America/New_York"',
        "workflow_dispatch:",
        "contents: read",
        "group: dealer-gex-daily-archive",
        "cancel-in-progress: false",
        "timeout-minutes: 15",
        "working-directory: backend",
        "DATABASE_URL: ${{ secrets.DATABASE_URL }}",
        "NIGHTWATCH_API_KEY: ${{ secrets.NIGHTWATCH_API_KEY }}",
        "python-version: \"3.10\"",
        "python -m pip install .",
        "python -m app.cli capture-dealer-gex-archive --scheduled",
    )
    for fragment in required_fragments:
        assert fragment in contents

    assert "curl " not in contents
    assert "NEXT_PUBLIC_" not in contents

from __future__ import annotations

import uuid
from datetime import date, datetime, timezone
from pathlib import Path
from types import SimpleNamespace

import pytest

from app.db.models import CanonicalSchedulerAttempt, CanonicalSchedulerSlot
from app.scanner.daily_semantics import activity_session_plan
from app.scheduler import service as scheduler_service
from app.scheduler.domain import (
    CanonicalSlotType,
    canonical_slot_identity,
    validate_scheduler_headers,
)
from app.scheduler.repository import SlotClaim
from app.scheduler.routes import router
from app.scheduler.service import CanonicalSchedulerOrchestrator

UTC = timezone.utc
ROOT = Path(__file__).resolve().parents[2]


def _slot(
    *,
    status: str = "CLAIMED",
    actual: datetime = datetime(2026, 8, 24, 10, 30, 12, tzinfo=UTC),
) -> CanonicalSchedulerSlot:
    identity = canonical_slot_identity(CanonicalSlotType.RADAR_OI, "2026-08-24T10:30:00Z")
    return CanonicalSchedulerSlot(
        id=uuid.uuid4(),
        slot_type=identity.slot_type.value,
        intended_at=identity.intended_at,
        intended_market_date=identity.intended_market_date,
        market_timezone=identity.market_timezone,
        actual_started_at=actual,
        trigger_transport="GOOGLE_CLOUD_SCHEDULER",
        canonical_key=identity.canonical_key,
        scheduler_job_name="projects/p/locations/r/jobs/nightwatch-radar-oi",
        status=status,
        paid_work_attempted=False,
        network_attempts=0,
        consumed_units=0,
        product_candidate_count=0,
        baseline_count=0,
        result={},
        created_at=actual,
    )


def _attempt(slot: CanonicalSchedulerSlot) -> CanonicalSchedulerAttempt:
    return CanonicalSchedulerAttempt(
        id=uuid.uuid4(),
        slot_id=slot.id,
        scheduler_job_name=slot.scheduler_job_name,
        received_at=slot.actual_started_at,
        disposition="OWNER",
    )


@pytest.mark.parametrize(
    ("schedule_time", "expected_date", "expected_offset_hours"),
    [
        ("2026-01-15T11:30:00Z", date(2026, 1, 15), -5),
        ("2026-08-24T10:30:00.000000000Z", date(2026, 8, 24), -4),
    ],
)
def test_scheduler_identity_is_dst_safe(
    schedule_time: str,
    expected_date: date,
    expected_offset_hours: int,
) -> None:
    identity = canonical_slot_identity(CanonicalSlotType.RADAR_OI, schedule_time)
    assert identity.intended_market_date == expected_date
    assert identity.intended_at_et.hour == 6
    assert identity.intended_at_et.utcoffset().total_seconds() == expected_offset_hours * 3600


def test_scheduler_identity_rejects_wrong_slot_clock() -> None:
    with pytest.raises(ValueError, match="DOES_NOT_MATCH_SLOT"):
        canonical_slot_identity(CanonicalSlotType.ACTIVITY_VNEXT, "2026-08-27T19:30:00Z")


def test_scheduler_headers_require_expected_google_job() -> None:
    job = "projects/p/locations/us-east1/jobs/nightwatch-activity-vnext"
    assert (
        validate_scheduler_headers(
            scheduler_marker="true",
            scheduler_job_name=job,
            expected_job_id="nightwatch-activity-vnext",
        )
        == job
    )
    with pytest.raises(ValueError, match="UNEXPECTED"):
        validate_scheduler_headers(
            scheduler_marker="true",
            scheduler_job_name=job,
            expected_job_id="nightwatch-radar-oi",
        )


def test_health_supports_get_and_scheduler_post_without_side_effects() -> None:
    health_route = next(route for route in router.routes if route.path == "/health")
    assert health_route.methods == {"GET", "POST"}


def test_cross_midnight_activity_targets_intended_closed_session() -> None:
    actual = datetime(2026, 8, 28, 4, 24, 52, tzinfo=UTC)
    plan = activity_session_plan(actual, intended_market_date=date(2026, 8, 27))
    assert plan.market_date == date(2026, 8, 27)
    assert plan.should_collect is True
    assert plan.status == "READY"


def test_future_intended_activity_session_cannot_be_treated_as_complete() -> None:
    actual = datetime(2026, 8, 27, 19, 0, tzinfo=UTC)
    plan = activity_session_plan(actual, intended_market_date=date(2026, 8, 27))
    assert plan.should_collect is False
    assert plan.status == "SKIPPED_BEFORE_SESSION_CLOSE"


@pytest.mark.asyncio
async def test_duplicate_delivery_runs_business_execution_once(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    identity = canonical_slot_identity(CanonicalSlotType.RADAR_OI, "2026-08-24T10:30:00Z")
    slot = _slot()
    owner = SlotClaim(slot, _attempt(slot), True)
    duplicate = SlotClaim(slot, _attempt(slot), False)
    claims = iter([owner, duplicate])
    monkeypatch.setattr(
        scheduler_service,
        "claim_canonical_slot",
        lambda *_args, **_kwargs: next(claims),
    )
    executions = 0

    async def run_once(*_args, **_kwargs) -> None:  # type: ignore[no-untyped-def]
        nonlocal executions
        executions += 1
        slot.status = "COMPLETE"

    orchestrator = CanonicalSchedulerOrchestrator(
        SimpleNamespace(),  # type: ignore[arg-type]
        SimpleNamespace(),  # type: ignore[arg-type]
    )
    monkeypatch.setattr(orchestrator, "_run_radar_oi", run_once)
    first = await orchestrator.execute(
        identity=identity,
        actual_started_at=slot.actual_started_at,
        scheduler_job_name=slot.scheduler_job_name,
    )
    second = await orchestrator.execute(
        identity=identity,
        actual_started_at=slot.actual_started_at,
        scheduler_job_name=slot.scheduler_job_name,
    )
    assert executions == 1
    assert first.created_execution_state is True
    assert second.created_execution_state is False
    assert first.status == second.status == "COMPLETE"


@pytest.mark.asyncio
async def test_late_radar_delivery_makes_zero_vendor_attempts(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    actual = datetime(2026, 8, 24, 20, 41, 54, tzinfo=UTC)
    identity = canonical_slot_identity(CanonicalSlotType.RADAR_OI, "2026-08-24T10:30:00Z")
    slot = _slot(actual=actual)
    claim = SlotClaim(slot, _attempt(slot), True)
    orchestrator = CanonicalSchedulerOrchestrator(
        SimpleNamespace(),  # type: ignore[arg-type]
        SimpleNamespace(),  # type: ignore[arg-type]
    )

    def forbidden_client(**_kwargs):  # type: ignore[no-untyped-def]
        raise AssertionError("late Radar must not construct a vendor client")

    def complete(_claim, target, *, status, result):  # type: ignore[no-untyped-def]
        target.status = status
        target.result = result

    monkeypatch.setattr(orchestrator, "_client", forbidden_client)
    monkeypatch.setattr(orchestrator, "_complete", complete)
    await orchestrator._run_radar_oi(claim, identity, actual)
    assert slot.status == "SKIPPED_AFTER_SAFE_WINDOW"
    assert slot.network_attempts == 0
    assert slot.paid_work_attempted is False


def test_canonical_readiness_is_bound_to_slot_owned_source_runs() -> None:
    source = (ROOT / "backend" / "app" / "scanner" / "daily_observation.py").read_text(
        encoding="utf-8"
    )
    assert "DailyCollectionRun.canonical_slot_id == canonical_slot_id" in source
    assert 'CanonicalSchedulerSlot.slot_type == "RADAR_OI"' in source
    assert "DailyOiArchiveRun.canonical_slot_id" in source
    assert 'DailyCollectionRun.trigger == "scheduled"' in source
    assert 'DailyOiArchiveRun.trigger == "scheduled"' in source
    assert 'Mag7Scanner(session, client).execute(**scan_kwargs)' in source
    assert '"trigger": "scheduled_daily"' in source


def test_static_gcp_configuration_is_paused_private_and_no_retry() -> None:
    source = (ROOT / "infra" / "gcp" / "main.tf").read_text(encoding="utf-8")
    variables = (ROOT / "infra" / "gcp" / "variables.tf").read_text(encoding="utf-8")
    assert 'ingress             = "INGRESS_TRAFFIC_INTERNAL_ONLY"' in source
    assert 'role     = "roles/run.invoker"' in source
    assert "allUsers" not in source
    assert 'time_zone        = "America/New_York"' in source
    assert "retry_count          = 0" in source
    assert "oidc_token" in source
    assert "default     = true" in variables
    assert source.count('schedule = "30 ') == 3


def test_github_cutover_preserves_manual_and_disables_automatic_production() -> None:
    phase2a = (ROOT / ".github" / "workflows" / "phase2a-daily-archive.yml").read_text(
        encoding="utf-8"
    )
    dealer = (ROOT / ".github" / "workflows" / "dealer-gex-archive.yml").read_text(
        encoding="utf-8"
    )
    assert "schedule:" not in phase2a
    assert "schedule:" not in dealer
    assert "workflow_dispatch:" in phase2a
    assert "workflow_dispatch:" in dealer
    assert "run-daily-vnext-observation" not in phase2a
    assert "--scheduled" not in phase2a
    assert "--scheduled" not in dealer

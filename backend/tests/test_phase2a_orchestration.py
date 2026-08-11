import uuid

import pytest

from app.scanner.config import LIMITS
from app.scanner.service import (
    BudgetExceeded,
    BudgetTracker,
    cache_signature,
    completion_status,
)


def test_cache_signature_reuses_equivalent_parameter_order() -> None:
    left = cache_signature("/chain", {"ticker": "AAPL", "expiration": "2026-08-21"})
    right = cache_signature("/chain", {"expiration": "2026-08-21", "ticker": "AAPL"})
    assert left == right


def test_quota_and_attempt_hard_stops_are_independent() -> None:
    tracker = BudgetTracker(None, uuid.uuid4())  # type: ignore[arg-type]
    tracker.consumed = LIMITS.max_consumed_units_per_scan
    with pytest.raises(BudgetExceeded, match="quota"):
        tracker.ensure_room()
    tracker.consumed = 0
    tracker.attempts = LIMITS.max_network_attempts_per_scan
    with pytest.raises(BudgetExceeded, match="network"):
        tracker.ensure_room()


def test_partial_and_data_pending_statuses_are_truthful() -> None:
    assert (
        completion_status(partial=False, budget_limited=True, data_pending=False)
        == "PARTIAL_BUDGET_LIMIT"
    )
    assert (
        completion_status(partial=False, budget_limited=False, data_pending=True)
        == "DATA_PENDING"
    )
    assert completion_status(partial=True, budget_limited=False, data_pending=False) == "PARTIAL"
    assert completion_status(partial=False, budget_limited=False, data_pending=False) == "COMPLETE"

from datetime import datetime, timezone

import pytest

from app.nightwatch.retry import is_retryable_status, retry_after_seconds


@pytest.mark.parametrize("status", [408, 425, 429, 500, 502, 503, 504])
def test_retryable_statuses(status: int) -> None:
    assert is_retryable_status(status)


@pytest.mark.parametrize("status", [400, 401, 403, 404, 409, 422])
def test_logical_client_errors_are_not_retryable(status: int) -> None:
    assert not is_retryable_status(status)


def test_retry_after_http_date() -> None:
    now = datetime(2026, 8, 10, 12, 0, tzinfo=timezone.utc)
    assert retry_after_seconds("Mon, 10 Aug 2026 12:00:03 GMT", now) == 3


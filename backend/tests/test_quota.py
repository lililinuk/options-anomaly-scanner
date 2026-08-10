from datetime import timezone

from app.nightwatch.quota import parse_quota_headers


def test_parses_quota_and_rate_limit_headers_case_insensitively() -> None:
    metadata = parse_quota_headers(
        {
            "X-Quota-Limit": "100000",
            "x-quota-remaining": "99871",
            "X-Quota-Reset-At": "2026-09-01T00:00:00Z",
            "X-RateLimit-Limit": "60",
            "x-ratelimit-remaining": "57",
            "X-RateLimit-Reset": "1756742400",
            "Retry-After": "2.5",
        }
    )

    assert metadata.quota_limit == 100000
    assert metadata.quota_remaining == 99871
    assert metadata.quota_reset_at is not None
    assert metadata.quota_reset_at.tzinfo == timezone.utc
    assert metadata.rate_limit == 60
    assert metadata.rate_limit_remaining == 57
    assert metadata.rate_limit_reset_epoch == 1756742400
    assert metadata.retry_after_seconds == 2.5


def test_malformed_headers_are_ignored() -> None:
    metadata = parse_quota_headers({"X-Quota-Remaining": "unknown", "Retry-After": "later"})
    assert metadata.quota_remaining is None
    assert metadata.retry_after_seconds is None


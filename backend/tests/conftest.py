import pytest


@pytest.fixture(autouse=True)
def no_live_nightwatch(monkeypatch: pytest.MonkeyPatch) -> None:
    """A real key must never leak into, or enable network access from, unit tests."""

    monkeypatch.delenv("NIGHTWATCH_API_KEY", raising=False)
    monkeypatch.setenv("APP_ENV", "test")

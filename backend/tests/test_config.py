from pydantic import SecretStr

from app.config.settings import Settings


def test_secret_values_are_redacted_from_representation() -> None:
    secret = "not-a-real-nightwatch-secret"
    settings = Settings(
        nightwatch_api_key=secret,
        database_url="postgresql+psycopg://user:private-password@db/scanner",
        _env_file=None,
    )

    rendered = repr(settings)
    assert secret not in rendered
    assert "private-password" not in rendered
    assert isinstance(settings.nightwatch_api_key, SecretStr)


def test_empty_api_key_is_treated_as_unconfigured() -> None:
    settings = Settings(nightwatch_api_key="", _env_file=None)
    assert settings.nightwatch_api_key is None


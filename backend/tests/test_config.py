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


def test_generic_postgres_url_uses_installed_psycopg_driver() -> None:
    settings = Settings(
        database_url="postgresql://user:password@database.example/scanner",
        _env_file=None,
    )

    normalized = settings.database_url.get_secret_value()
    assert normalized.startswith("postgresql+psycopg://")
    assert "password" not in repr(settings)


def test_explicit_database_driver_is_preserved() -> None:
    configured = "postgresql+psycopg://user:password@database.example/scanner"
    settings = Settings(database_url=configured, _env_file=None)
    assert settings.database_url.get_secret_value() == configured

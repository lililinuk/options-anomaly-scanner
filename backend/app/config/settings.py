from functools import lru_cache
from pathlib import Path

from pydantic import Field, HttpUrl, SecretStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

REPOSITORY_ROOT = Path(__file__).resolve().parents[3]


class Settings(BaseSettings):
    """Validated process configuration. Secret values stay wrapped as SecretStr."""

    model_config = SettingsConfigDict(
        env_file=REPOSITORY_ROOT / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    app_name: str = "Options Anomaly Scanner API"
    app_env: str = "development"
    log_level: str = "INFO"
    backend_host: str = "127.0.0.1"
    backend_port: int = 8000

    database_url: SecretStr = SecretStr(
        "postgresql+psycopg://options_scanner:change-me@localhost:5432/options_scanner"
    )
    database_connect_timeout_seconds: int = Field(default=5, ge=1, le=30)
    nightwatch_api_key: SecretStr | None = None
    nightwatch_base_url: HttpUrl = HttpUrl("https://api.yehangshe.com")
    nightwatch_timeout_seconds: float = Field(default=20.0, gt=0, le=120)
    nightwatch_max_retries: int = Field(default=3, ge=0, le=8)
    nightwatch_max_concurrency: int = Field(default=4, ge=1, le=32)
    nightwatch_metadata_refresh_seconds: int = Field(default=900, ge=60)
    scan_schedule_enabled: bool = False

    market_timezone: str = "America/New_York"
    persisted_timezone: str = "UTC"

    @field_validator("nightwatch_api_key", mode="before")
    @classmethod
    def empty_key_is_none(cls, value: object) -> object:
        return None if value == "" else value


@lru_cache
def get_settings() -> Settings:
    return Settings()

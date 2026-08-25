from decimal import Decimal
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

    # Radar eligibility values are process configuration, not business-logic constants. The
    # explicit identity/version is persisted with every evaluation so changing an active profile
    # never changes the meaning of historical rows.
    radar_threshold_profile_id: str = "radar_material_event"
    radar_threshold_profile_version: str = "2026-08-13.v1"
    radar_threshold_enabled: bool = True
    radar_min_premium_usd: Decimal = Field(default=Decimal("150000"), ge=0)
    radar_min_abs_oi_diff: int = Field(default=2500, ge=0)
    radar_calibration_review_sessions: int = Field(default=20, ge=1)

    # Phase 2A vNext Contract Persistence may become a current trigger only under an
    # explicitly configured and versioned recency policy.  None is intentional: no
    # founder-approved numeric window exists yet, so the runtime remains in the safe
    # CALIBRATION_REQUIRED mode while still computing descriptive persistence analytics.
    phase2a_persistence_freshness_config_version: str = "2026-08-18.calibration-required.v1"
    phase2a_persistence_current_trigger_max_vendor_age_days: int | None = Field(
        default=None, ge=0
    )

    # Phase 2B evidence freshness and descriptive tolerances are versioned process
    # configuration. Evaluations persist both this version and its effective snapshot.
    phase2b_context_config_version: str = "2026-08-14.v1.2"
    phase2b_stock_state_freshness_minutes: int = Field(default=15, ge=1)
    phase2b_ohlc_freshness_minutes: int = Field(default=720, ge=1)
    phase2b_iv_rank_freshness_minutes: int = Field(default=720, ge=1)
    phase2b_term_structure_freshness_minutes: int = Field(default=720, ge=1)
    phase2b_heatmap_freshness_minutes: int = Field(default=15, ge=1)
    phase2b_at_spot_tolerance_pct: Decimal = Field(default=Decimal("0.0025"), ge=0)
    phase2b_return_windows: tuple[int, ...] = (1, 5, 20)
    phase2b_sma_windows: tuple[int, ...] = (20, 50)
    phase2b_atr_window: int = Field(default=14, ge=1)
    phase2b_rolling_range_window: int = Field(default=20, ge=1)

    # Phase 2B v3.1 Dealer/GEX capture is invoked by an external durable scheduler. The
    # process itself never starts an in-process background scheduler.
    dealer_gex_archive_enabled: bool = True
    dealer_gex_archive_config_version: str = "2026-08-14.v3.1.1"
    dealer_gex_archive_local_time: str = "15:30"
    dealer_gex_archive_max_network_attempts: int = Field(default=7, ge=1, le=50)
    dealer_gex_archive_max_consumed_units: int = Field(default=7, ge=1, le=50)

    market_timezone: str = "America/New_York"
    persisted_timezone: str = "UTC"

    @field_validator("nightwatch_api_key", mode="before")
    @classmethod
    def empty_key_is_none(cls, value: object) -> object:
        return None if value == "" else value

    @field_validator("database_url", mode="before")
    @classmethod
    def normalize_database_driver(cls, value: object) -> object:
        """Use the installed Psycopg 3 driver for generic provider URLs."""

        raw = value.get_secret_value() if isinstance(value, SecretStr) else value
        if not isinstance(raw, str):
            return value
        if raw.startswith("postgres://"):
            return "postgresql+psycopg://" + raw.removeprefix("postgres://")
        if raw.startswith("postgresql://"):
            return "postgresql+psycopg://" + raw.removeprefix("postgresql://")
        return value


@lru_cache
def get_settings() -> Settings:
    return Settings()

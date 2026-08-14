from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from typing import Final

from app.config import get_settings
from app.scanner.config import UNIVERSE

DEALER_GEX_ARCHIVE_SPEC_VERSION: Final = "signal_spec_v3.1_phase2b"
DEALER_GEX_SURFACE_SCHEMA_VERSION: Final = "nightwatch_dealer_heatmap_default_v1"
DEALER_GEX_CAPABILITY: Final = "derived.heatmap"
DEALER_GEX_ENDPOINT_TEMPLATE: Final = "/v1/derived/heatmap/{ticker}/snapshot"


@dataclass(frozen=True)
class DealerGexArchiveConfig:
    version: str
    enabled: bool
    universe: tuple[str, ...]
    market_timezone: str
    intended_capture_slot: str
    max_network_attempts: int
    max_consumed_units: int
    endpoint_format: str | None = None

    def snapshot(self) -> dict[str, object]:
        return asdict(self)

    def hash(self) -> str:
        encoded = json.dumps(self.snapshot(), sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(encoded.encode()).hexdigest()


def active_dealer_gex_archive_config() -> DealerGexArchiveConfig:
    settings = get_settings()
    return DealerGexArchiveConfig(
        version=settings.dealer_gex_archive_config_version,
        enabled=settings.dealer_gex_archive_enabled,
        universe=tuple(UNIVERSE),
        market_timezone=settings.market_timezone,
        intended_capture_slot=settings.dealer_gex_archive_local_time,
        max_network_attempts=settings.dealer_gex_archive_max_network_attempts,
        max_consumed_units=settings.dealer_gex_archive_max_consumed_units,
    )

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from decimal import Decimal
from typing import Final

from app.config import get_settings

PHASE2B_SPEC_VERSION: Final = "signal_spec_v1.1_phase2b"


@dataclass(frozen=True)
class Phase2bContextConfig:
    version: str
    stock_state_freshness_minutes: int
    ohlc_freshness_minutes: int
    iv_rank_freshness_minutes: int
    term_structure_freshness_minutes: int
    heatmap_freshness_minutes: int
    at_spot_tolerance_pct: Decimal
    return_windows: tuple[int, ...] = (1, 5, 20)
    sma_windows: tuple[int, ...] = (20, 50)
    atr_window: int = 14
    rolling_range_window: int = 20
    daily_session_policy: str = "VALID_REGULAR_SESSION_OBSERVATIONS"
    price_adjustment_semantics: str = "UNCONFIRMED"

    def snapshot(self) -> dict[str, object]:
        values = asdict(self)
        values["at_spot_tolerance_pct"] = str(self.at_spot_tolerance_pct)
        return values

    @property
    def configuration_hash(self) -> str:
        encoded = json.dumps(self.snapshot(), sort_keys=True, separators=(",", ":")).encode()
        return hashlib.sha256(encoded).hexdigest()

    @property
    def cache_freshness_minutes(self) -> int:
        return min(
            self.stock_state_freshness_minutes,
            self.ohlc_freshness_minutes,
            self.iv_rank_freshness_minutes,
            self.term_structure_freshness_minutes,
            self.heatmap_freshness_minutes,
        )


def active_phase2b_config() -> Phase2bContextConfig:
    settings = get_settings()
    return Phase2bContextConfig(
        version=settings.phase2b_context_config_version,
        stock_state_freshness_minutes=settings.phase2b_stock_state_freshness_minutes,
        ohlc_freshness_minutes=settings.phase2b_ohlc_freshness_minutes,
        iv_rank_freshness_minutes=settings.phase2b_iv_rank_freshness_minutes,
        term_structure_freshness_minutes=settings.phase2b_term_structure_freshness_minutes,
        heatmap_freshness_minutes=settings.phase2b_heatmap_freshness_minutes,
        at_spot_tolerance_pct=settings.phase2b_at_spot_tolerance_pct,
        return_windows=settings.phase2b_return_windows,
        sma_windows=settings.phase2b_sma_windows,
        atr_window=settings.phase2b_atr_window,
        rolling_range_window=settings.phase2b_rolling_range_window,
    )

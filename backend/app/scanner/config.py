from dataclasses import asdict, dataclass
from typing import Final

from app.models.signals import DEFAULT_DTE_BUCKET_RULES

# The founder intentionally deferred a numeric production spec assignment.  This working
# architecture identity keeps new Stage 4B evidence distinguishable from accepted v1.3 history.
SIGNAL_SPEC_VERSION: Final = "phase2a_vnext_stage4b"


@dataclass(frozen=True)
class ScannerLimits:
    max_deep_tickers: int = 4
    max_expiries_per_ticker: int = 3
    max_consumed_units_per_scan: int = 75
    max_network_attempts_per_scan: int = 100
    cache_cooldown_minutes: int = 30
    same_day_eligibility_score: float = 40
    persistent_eligibility_score: float = 65
    structural_cold_start_oi_share: float = 0.20
    zero_dte_baseline_observations: int = 20
    zero_dte_mad_epsilon: float = 1e-9
    comparable_peer_max_count: int = 4
    comparable_peer_min_count: int = 2


@dataclass(frozen=True)
class ArchiveLimits:
    enabled: bool = True
    timezone: str = "Asia/Singapore"
    local_time: str = "12:00"
    max_dte: int = 180
    max_consumed_units: int = 250
    max_network_attempts: int = 350
    materialization_max_attempts: int = 3
    materialization_max_wait_seconds: float = 30.0
    materialization_default_retry_after_seconds: float = 2.0


UNIVERSE: Final = ("AAPL", "MSFT", "NVDA", "AMZN", "META", "GOOGL", "TSLA")
LIMITS: Final = ScannerLimits()
ARCHIVE_LIMITS: Final = ArchiveLimits()

# Every financial threshold is versioned configuration, never embedded in scoring control flow.
SCORE_ANCHORS: Final[dict[str, tuple[tuple[float, float], ...]]] = {
    "same_day_volume_share": (
        (0.05, 0), (0.10, 10), (0.20, 25), (0.30, 40), (0.40, 50), (0.50, 60)
    ),
    "same_day_volume_neighbor": ((1.2, 0), (1.5, 8), (2.0, 15), (3.0, 25), (5.0, 40)),
    "zero_dte_robust_deviation": (
        (1.0, 0), (1.5, 15), (2.0, 30), (3.0, 50), (4.0, 70)
    ),
    "zero_dte_historical_percentile": (
        (0.70, 0), (0.80, 10), (0.90, 20), (0.95, 25), (1.0, 30)
    ),
    "expiry_persistent_share_change": (
        (0.005, 0), (0.01, 8), (0.02, 16), (0.05, 28), (0.10, 40)
    ),
    "expiry_persistent_growth": ((0.05, 0), (0.10, 5), (0.25, 12), (0.50, 20), (1.0, 30)),
    "directional_persistence": (
        (0.50, 0), (0.60, 5), (0.70, 10), (0.80, 18), (0.90, 25), (1.0, 30)
    ),
    "contract_persistent_growth": (
        (0.10, 0), (0.25, 8), (0.50, 16), (1.0, 25), (2.0, 35)
    ),
    "contract_persistent_build_share": (
        (0.0025, 0), (0.005, 5), (0.01, 12), (0.02, 22), (0.05, 35)
    ),
    "contract_oi_share": (
        (0.005, 0), (0.01, 5), (0.02, 12), (0.05, 22), (0.10, 32), (0.20, 40)
    ),
    "neighbor_strike_oi": ((1.2, 0), (1.5, 5), (2.0, 10), (3.0, 18), (5.0, 30)),
    "structure_liquidity": ((0.05, 15), (0.10, 13), (0.20, 10), (0.30, 6), (0.50, 2)),
    "cluster_oi_share": ((0.05, 0), (0.10, 5), (0.20, 12), (0.40, 22), (0.60, 35)),
    "prelim_volume_share": ((0.10, 0), (0.20, 10), (0.30, 20), (0.40, 30), (0.50, 40)),
    "prelim_neighbor": ((1.2, 0), (1.5, 5), (2.0, 10), (3.0, 20), (5.0, 30)),
    "prelim_skew": ((0.10, 0), (0.30, 10), (0.50, 20), (0.70, 30)),
    "contract_volume_oi": ((0.5, 0), (1, 4), (2, 7), (5, 10), (10, 12)),
    "contract_volume": ((100, 0), (500, 3), (2000, 5), (10000, 8)),
    "contract_premium": (
        (0, 0),
        (50000, 2),
        (150000, 6),
        (500000, 10),
        (1000000, 14),
        (5000000, 20),
    ),
    "contract_history": ((1, 0), (2, 5), (3, 10), (4, 15), (5, 20)),
    "contract_burst": ((2, 0), (3, 5), (5, 10), (10, 15)),
    "contract_liquidity": ((0.05, 15), (0.10, 13), (0.20, 10), (0.30, 6), (0.50, 2)),
    "final_oi_share": ((0.05, 0), (0.10, 5), (0.20, 10), (0.30, 15), (0.40, 20), (0.50, 25)),
    "final_neighbor": ((1.2, 0), (1.5, 5), (2, 10), (3, 15), (5, 25)),
    "final_volume_share": ((0.05, 0), (0.10, 4), (0.20, 8), (0.30, 12), (0.40, 16), (0.50, 20)),
    "final_skew": ((0.10, 0), (0.30, 5), (0.50, 10), (0.70, 15)),
    "final_premium_share": ((0.05, 0), (0.10, 3), (0.20, 6), (0.30, 9), (0.40, 12), (0.50, 15)),
    "cluster_premium_share": ((0.10, 0), (0.20, 5), (0.40, 15), (0.60, 25)),
    "cluster_volume_share": ((0.10, 0), (0.20, 5), (0.40, 12), (0.60, 20)),
}

COMPONENT_MAX: Final = {
    "prelim_volume_share": 40,
    "prelim_neighbor": 30,
    "prelim_skew": 30,
    "contract_activity": 20,
    "contract_premium": 20,
    "contract_history": 20,
    "contract_burst": 15,
    "contract_liquidity": 15,
    "contract_moneyness": 10,
    "final_oi_share": 25,
    "final_neighbor": 25,
    "final_volume_share": 20,
    "final_skew": 15,
    "final_premium_share": 15,
}


def configuration_snapshot() -> dict[str, object]:
    # Imported lazily to keep configuration dataclasses free from Settings initialization side
    # effects during module import and migration discovery.
    from app.scanner.v13 import active_radar_threshold_profile
    from app.scanner.vnext import persistence_freshness_policy

    return {
        "version": SIGNAL_SPEC_VERSION,
        "universe": {"mode": "FIXED_LIST", "tickers": list(UNIVERSE)},
        "dte": {
            "deep_scan_max": 90,
            "aggregate_max": 180,
            "buckets": {
                rule.bucket.value: [rule.minimum, rule.maximum] for rule in DEFAULT_DTE_BUCKET_RULES
            },
        },
        "selection_and_budget": asdict(LIMITS),
        "daily_oi_archive": asdict(ARCHIVE_LIMITS),
        "radar_discovery": active_radar_threshold_profile().snapshot(),
        "active_discovery_families": [
            "RADAR_EVENT",
            "EXPIRY_ACTIVITY",
            "CONTRACT_PERSISTENCE",
        ],
        "candidate_entity": "TICKER_PRODUCT_PROJECTION",
        "persistence_current_trigger": persistence_freshness_policy().snapshot(),
        "market_calendar": "XNYS",
        "scheduling": {
            "in_process": False,
            "external_schedule_required": True,
        },
        "score_anchors": {key: list(value) for key, value in SCORE_ANCHORS.items()},
    }

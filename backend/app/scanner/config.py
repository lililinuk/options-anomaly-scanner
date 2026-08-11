from dataclasses import asdict, dataclass
from typing import Final

from app.models.signals import DEFAULT_DTE_BUCKET_RULES

SIGNAL_SPEC_VERSION: Final = "signal_spec_v1.0_phase2a"


@dataclass(frozen=True)
class ScannerLimits:
    max_deep_tickers: int = 4
    max_expiries_per_ticker: int = 3
    max_intraday_contracts: int = 12
    max_consumed_units_per_scan: int = 75
    max_network_attempts_per_scan: int = 100
    cache_cooldown_minutes: int = 30


UNIVERSE: Final = ("AAPL", "MSFT", "NVDA", "AMZN", "META", "GOOGL", "TSLA")
LIMITS: Final = ScannerLimits()

# Every financial threshold is versioned configuration, never embedded in scoring control flow.
SCORE_ANCHORS: Final[dict[str, tuple[tuple[float, float], ...]]] = {
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
        "scheduling": {"enabled": False},
        "score_anchors": {key: list(value) for key, value in SCORE_ANCHORS.items()},
    }

from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from enum import Enum
from typing import Any

from app.nightwatch.models import DiscoverResponse


class CapabilityAvailability(str, Enum):
    AVAILABLE = "available"
    UNAVAILABLE = "unavailable"
    UNKNOWN = "unknown"


@dataclass(frozen=True)
class CapabilityRegistry:
    """Conservative account capability view derived only from `/v1/discover`."""

    confirmed: frozenset[str]
    explicitly_unavailable: frozenset[str] = frozenset()

    @classmethod
    def from_discover(cls, response: DiscoverResponse | Mapping[str, Any]) -> "CapabilityRegistry":
        payload = (
            response.model_dump() if isinstance(response, DiscoverResponse) else dict(response)
        )
        confirmed: set[str] = set()
        unavailable: set[str] = set()
        _collect_capabilities(payload.get("capabilities"), confirmed, unavailable)
        _collect_details(payload.get("capabilities_detail"), confirmed, unavailable)
        return cls(frozenset(confirmed), frozenset(unavailable))

    def status(self, capability: str) -> CapabilityAvailability:
        if capability in self.confirmed:
            return CapabilityAvailability.AVAILABLE
        if capability in self.explicitly_unavailable:
            return CapabilityAvailability.UNAVAILABLE
        return CapabilityAvailability.UNKNOWN

    def supports(self, capability: str) -> bool:
        return self.status(capability) is CapabilityAvailability.AVAILABLE


def _is_capability_name(value: str) -> bool:
    return "." in value and " " not in value and not value.startswith("/")


def _collect_capabilities(value: Any, confirmed: set[str], unavailable: set[str]) -> None:
    if isinstance(value, str):
        if _is_capability_name(value):
            confirmed.add(value)
        return
    if isinstance(value, Mapping):
        for key, child in value.items():
            if _is_capability_name(str(key)) and isinstance(child, bool):
                (confirmed if child else unavailable).add(str(key))
            elif isinstance(child, Iterable) and not isinstance(child, (str, bytes, Mapping)):
                for item in child:
                    if isinstance(item, str):
                        candidate = item if "." in item else f"{key}.{item}"
                        if _is_capability_name(candidate):
                            confirmed.add(candidate)
                    else:
                        _collect_capabilities(item, confirmed, unavailable)
            else:
                _collect_capabilities(child, confirmed, unavailable)
        return
    if isinstance(value, Iterable) and not isinstance(value, (str, bytes)):
        for item in value:
            if isinstance(item, Mapping):
                _collect_details([item], confirmed, unavailable)
            else:
                _collect_capabilities(item, confirmed, unavailable)


def _collect_details(value: Any, confirmed: set[str], unavailable: set[str]) -> None:
    if not isinstance(value, Iterable) or isinstance(value, (str, bytes, Mapping)):
        return
    for detail in value:
        if hasattr(detail, "model_dump"):
            detail = detail.model_dump()
        if not isinstance(detail, Mapping):
            continue
        name = detail.get("command") or detail.get("capability") or detail.get("name")
        if not isinstance(name, str) or not _is_capability_name(name):
            continue
        available = detail.get("available")
        if not isinstance(available, bool):
            available = detail.get("enabled", True)
        (confirmed if available is True else unavailable).add(name)


RESEARCH_CAPABILITIES = (
    "options.chain_snapshot",
    "options.expiry_breakdown",
    "options.oi_change",
    "options.oi_per_expiry",
    "options.oi_per_strike",
    "options.options_volume",
    "options.volume_oi_per_expiry",
    "options.contract_daily",
    "options.contract_intraday",
    "options.contract_greeks_series",
    "options.optionable_tickers",
    "volatility.iv_rank",
    "volatility.term_structure",
    "volatility.anomaly",
    "volatility.anomaly_top",
    "market.oi_change",
    "market.movers",
)

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict

from app.nightwatch.capabilities import CapabilityRegistry
from app.nightwatch.models import CapabilityDetail, DiscoverResponse


class NormalizedCapability(BaseModel):
    """Stable capability representation derived from a discover response."""

    model_config = ConfigDict(frozen=True)

    observed_at: datetime
    capability_identifier: str
    available: bool
    coverage: str | None = None
    weight: int | None = None
    source_request_id: str
    source_metadata: dict[str, Any]


def normalize_capabilities(
    response: DiscoverResponse,
    *,
    observed_at: datetime,
    source_request_id: str,
) -> list[NormalizedCapability]:
    normalized: dict[str, NormalizedCapability] = {}

    for raw_detail in response.capabilities_detail:
        detail = (
            raw_detail
            if isinstance(raw_detail, CapabilityDetail)
            else CapabilityDetail.model_validate(raw_detail)
        )
        identifier = detail.command or detail.capability or detail.name
        if not identifier:
            continue
        available = detail.available
        if available is None:
            available = detail.enabled if detail.enabled is not None else True
        normalized[identifier] = NormalizedCapability(
            observed_at=observed_at,
            capability_identifier=identifier,
            available=available,
            coverage=detail.coverage,
            weight=detail.weight,
            source_request_id=source_request_id,
            source_metadata={
                key: value
                for key, value in {
                    "scope": detail.scope,
                    "tool": detail.tool,
                }.items()
                if value is not None
            },
        )

    if not normalized:
        registry = CapabilityRegistry.from_discover(response)
        for identifier in sorted(registry.confirmed | registry.explicitly_unavailable):
            normalized[identifier] = NormalizedCapability(
                observed_at=observed_at,
                capability_identifier=identifier,
                available=identifier in registry.confirmed,
                source_request_id=source_request_id,
                source_metadata={},
            )
    return sorted(normalized.values(), key=lambda item: item.capability_identifier)

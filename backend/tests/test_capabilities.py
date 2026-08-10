import json
from pathlib import Path

from app.nightwatch.capabilities import CapabilityAvailability, CapabilityRegistry
from app.nightwatch.models import DiscoverResponse


def test_registry_is_conservative_and_handles_discover_shapes() -> None:
    fixture = Path(__file__).parent / "fixtures" / "discover.json"
    response = DiscoverResponse.model_validate(json.loads(fixture.read_text(encoding="utf-8")))
    registry = CapabilityRegistry.from_discover(response)

    assert response.monthly_remaining == 99871
    assert registry.supports("options.chain_snapshot")
    assert registry.supports("options.oi_change")
    assert registry.supports("options.oi_per_expiry")
    assert registry.supports("volatility.iv_rank")
    assert registry.supports("derived.dealer_gex")
    assert registry.status("market.movers") is CapabilityAvailability.UNAVAILABLE
    assert registry.status("derived.heatmap") is CapabilityAvailability.UNAVAILABLE
    assert registry.status("options.contract_daily") is CapabilityAvailability.UNKNOWN


def test_documentation_does_not_imply_account_availability() -> None:
    registry = CapabilityRegistry.from_discover({"capabilities": []})
    assert not registry.supports("options.chain_snapshot")

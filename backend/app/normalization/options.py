from datetime import date, datetime
from decimal import Decimal
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict


class NormalizedOptionContract(BaseModel):
    """Vendor-neutral contract observation produced after raw evidence is stored."""

    model_config = ConfigDict(frozen=True)

    contract_symbol: str
    ticker: str
    expiration: date
    strike: Decimal
    option_right: Literal["C", "P"]
    observed_at: datetime
    open_interest: int | None = None
    volume: int | None = None
    bid: Decimal | None = None
    ask: Decimal | None = None
    source_fields: dict[str, Any]


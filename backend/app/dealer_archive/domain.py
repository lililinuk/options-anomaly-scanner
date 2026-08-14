from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import date, datetime, timezone
from decimal import Decimal, InvalidOperation
from typing import Any

from app.confirmation.domain import normalize_heatmap_payload
from app.dealer_archive.config import DEALER_GEX_SURFACE_SCHEMA_VERSION

USABLE_SOURCE_QUALITIES = frozenset({"AVAILABLE", "AVAILABLE_DEGRADED"})


@dataclass(frozen=True)
class DealerGexCellValue:
    expiration: date
    strike: Decimal
    net_dealer_gex_usd: Decimal | None
    call_gex_usd: Decimal | None
    put_gex_usd: Decimal | None


@dataclass(frozen=True)
class NormalizedDealerGexSurface:
    ticker: str
    vendor_observed_at: datetime | None
    spot_usd: Decimal | None
    source_quality: str
    availability: str
    safe_error_code: str | None
    truncated: bool
    cells: tuple[DealerGexCellValue, ...]
    observation_identity: str | None
    quality_details: dict[str, Any]

    @property
    def usable(self) -> bool:
        return self.source_quality in USABLE_SOURCE_QUALITIES


def _decimal(value: Any) -> Decimal | None:
    if value is None or isinstance(value, bool):
        return None
    try:
        parsed = Decimal(str(value))
    except (InvalidOperation, TypeError, ValueError):
        return None
    return parsed if parsed.is_finite() else None


def _date(value: Any) -> date | None:
    if not isinstance(value, str):
        return None
    try:
        return date.fromisoformat(value[:10])
    except ValueError:
        return None


def _timestamp(value: Any) -> datetime | None:
    if not isinstance(value, str) or not value.strip():
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None:
        return None
    return parsed.astimezone(timezone.utc)


def analytical_observation_identity(ticker: str, vendor_observed_at: datetime) -> str:
    semantic_identity = {
        "ticker": ticker,
        "vendor_observed_at": vendor_observed_at.isoformat(),
        "surface_schema_version": DEALER_GEX_SURFACE_SCHEMA_VERSION,
        "format": "full",
    }
    encoded = json.dumps(semantic_identity, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(encoded.encode()).hexdigest()


def unavailable_surface(
    ticker: str,
    *,
    safe_error_code: str,
    source_http_status: int | None = None,
) -> NormalizedDealerGexSurface:
    return NormalizedDealerGexSurface(
        ticker=ticker,
        vendor_observed_at=None,
        spot_usd=None,
        source_quality="UNAVAILABLE",
        availability="UNAVAILABLE",
        safe_error_code=safe_error_code,
        truncated=False,
        cells=(),
        observation_identity=None,
        quality_details={"source_http_status": source_http_status},
    )


def normalize_dealer_gex_surface(
    ticker: str,
    payload: dict[str, Any] | None,
    *,
    source_http_status: int,
    captured_at: datetime,
) -> NormalizedDealerGexSurface:
    """Normalize a full heatmap without treating unavailable evidence as a zero surface."""

    source = {
        "status": source_http_status,
        "captured_at": captured_at.isoformat(),
        "availability": "AVAILABLE" if source_http_status < 400 else "UNAVAILABLE",
    }
    normalized = normalize_heatmap_payload(payload, source_status=source)
    envelope = payload if isinstance(payload, dict) else {}
    data = envelope.get("data") if isinstance(envelope.get("data"), dict) else envelope
    data = data if isinstance(data, dict) else {}
    source_cells = normalized.get("cells") if isinstance(normalized.get("cells"), list) else []
    vendor_time = _timestamp(normalized.get("generated_at"))
    parsed_cells: list[DealerGexCellValue] = []
    invalid_rows = 0
    identities: set[tuple[date, Decimal]] = set()
    duplicate_rows = 0
    missing_net_rows = 0
    representative_keys: list[str] = []
    for source_cell in source_cells:
        if not isinstance(source_cell, dict):
            invalid_rows += 1
            continue
        if not representative_keys:
            representative_keys = sorted(str(key) for key in source_cell)
        expiration = _date(source_cell.get("expiration") or source_cell.get("expiry"))
        strike = _decimal(source_cell.get("strike_usd", source_cell.get("strike")))
        if expiration is None or strike is None:
            invalid_rows += 1
            continue
        identity = (expiration, strike)
        if identity in identities:
            duplicate_rows += 1
            continue
        identities.add(identity)
        net = _decimal(source_cell.get("net_dealer_gex_usd"))
        call = _decimal(source_cell.get("call_gex_usd"))
        put = _decimal(source_cell.get("put_gex_usd"))
        if net is None:
            missing_net_rows += 1
        parsed_cells.append(DealerGexCellValue(expiration, strike, net, call, put))

    top_level_keys = sorted(str(key) for key in envelope)
    data_keys = sorted(str(key) for key in data)
    details: dict[str, Any] = {
        "top_level_keys": top_level_keys,
        "data_keys": data_keys,
        "representative_cell_keys": representative_keys,
        "source_cell_count": len(source_cells),
        "parsed_cell_count": len(parsed_cells),
        "expiration_count": len({cell.expiration for cell in parsed_cells}),
        "invalid_cell_count": invalid_rows,
        "duplicate_cell_count": duplicate_rows,
        "missing_net_cell_count": missing_net_rows,
        "source_http_status": source_http_status,
        "session_date_et": normalized.get("session_date_et"),
        "market_status": normalized.get("market_status"),
        "vendor_state": normalized.get("state"),
        "scale": normalized.get("scale"),
    }
    quality = str(normalized.get("availability") or "UNAVAILABLE")
    safe_error = normalized.get("availability_reason")
    if quality == "UNAVAILABLE":
        parsed_cells = []
    elif bool(normalized.get("truncated")) or invalid_rows or duplicate_rows:
        quality = "INCOMPLETE_OR_TRUNCATED"
        safe_error = "INCOMPLETE_OR_TRUNCATED_SURFACE"
        parsed_cells = []
    elif vendor_time is None:
        quality = "UNAVAILABLE"
        safe_error = "MISSING_VENDOR_OBSERVATION_TIMESTAMP"
        parsed_cells = []
    elif not parsed_cells or missing_net_rows == len(parsed_cells):
        quality = "UNAVAILABLE"
        safe_error = "NO_USABLE_NET_GEX_CELLS"
        parsed_cells = []
    elif missing_net_rows:
        quality = "AVAILABLE_DEGRADED"
        safe_error = "PARTIAL_NET_GEX_VALUES"

    usable = quality in USABLE_SOURCE_QUALITIES
    identity = (
        analytical_observation_identity(ticker, vendor_time)
        if usable and vendor_time
        else None
    )
    return NormalizedDealerGexSurface(
        ticker=ticker,
        vendor_observed_at=vendor_time,
        spot_usd=_decimal(normalized.get("spot_usd")),
        source_quality=quality,
        availability="AVAILABLE" if usable else "UNAVAILABLE",
        safe_error_code=str(safe_error) if safe_error else None,
        truncated=bool(normalized.get("truncated")),
        cells=tuple(parsed_cells),
        observation_identity=identity,
        quality_details=details,
    )

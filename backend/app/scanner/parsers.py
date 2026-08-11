from __future__ import annotations

import re
import statistics
from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from typing import Any


def _number(row: dict[str, Any], *names: str) -> float | None:
    for name in names:
        value = row.get(name)
        if value is not None and not isinstance(value, bool):
            try:
                return float(value)
            except (TypeError, ValueError):
                continue
    return None


def _text(row: dict[str, Any], *names: str) -> str | None:
    for name in names:
        value = row.get(name)
        if value not in (None, ""):
            return str(value)
    return None


def _date(row: dict[str, Any], *names: str) -> date | None:
    value = _text(row, *names)
    if not value:
        return None
    try:
        return date.fromisoformat(value[:10])
    except ValueError:
        return None


def object_rows(payload: Any) -> list[dict[str, Any]]:
    """Return leaf-ish records while tolerating additive vendor envelope changes."""
    rows: list[dict[str, Any]] = []

    def walk(value: Any) -> None:
        if isinstance(value, list):
            for child in value:
                walk(child)
        elif isinstance(value, dict):
            scalar_count = sum(not isinstance(child, (dict, list)) for child in value.values())
            if scalar_count:
                rows.append(value)
            for child in value.values():
                if isinstance(child, (dict, list)):
                    walk(child)

    walk(payload.get("data") if isinstance(payload, dict) and "data" in payload else payload)
    return rows


@dataclass(frozen=True)
class ExpiryAggregate:
    expiration: date
    call_volume: int | None
    put_volume: int | None
    call_oi: int | None
    put_oi: int | None
    reported_total_volume: int | None = None
    reported_total_oi: int | None = None
    expiration_type: str | None = None

    @property
    def total_volume(self) -> int:
        if self.reported_total_volume is not None:
            return self.reported_total_volume
        return (self.call_volume or 0) + (self.put_volume or 0)

    @property
    def total_oi(self) -> int:
        if self.reported_total_oi is not None:
            return self.reported_total_oi
        return (self.call_oi or 0) + (self.put_oi or 0)


def parse_expiry_aggregates(payload: Any) -> list[ExpiryAggregate]:
    combined: dict[date, dict[str, Any]] = {}
    for row in object_rows(payload):
        expiration = _date(row, "expiration", "expiry", "expiration_date", "expiry_date")
        if expiration is None:
            continue
        target = combined.setdefault(
            expiration,
            {
                "call_volume": None,
                "put_volume": None,
                "call_oi": None,
                "put_oi": None,
                "total_volume": None,
                "total_oi": None,
                "type": None,
            },
        )
        right = (_text(row, "right", "option_right", "option_type", "type") or "").upper()
        call_volume = _number(row, "call_volume", "calls_volume", "volume_call")
        put_volume = _number(row, "put_volume", "puts_volume", "volume_put")
        call_oi = _number(
            row, "call_oi", "call_open_interest", "calls_open_interest", "open_interest_call"
        )
        put_oi = _number(
            row, "put_oi", "put_open_interest", "puts_open_interest", "open_interest_put"
        )
        if any(value is not None for value in (call_volume, put_volume, call_oi, put_oi)):
            target["call_volume"] = int(call_volume) if call_volume is not None else None
            target["put_volume"] = int(put_volume) if put_volume is not None else None
            target["call_oi"] = int(call_oi) if call_oi is not None else None
            target["put_oi"] = int(put_oi) if put_oi is not None else None
        elif right in {"C", "CALL", "CALLS", "P", "PUT", "PUTS"}:
            side = "call" if right.startswith("C") else "put"
            target[f"{side}_volume"] = (target[f"{side}_volume"] or 0) + int(
                _number(row, "volume", "total_volume") or 0
            )
            target[f"{side}_oi"] = (target[f"{side}_oi"] or 0) + int(
                _number(row, "open_interest", "oi", "total_oi") or 0
            )
        else:
            target["total_volume"] = int(_number(row, "volume", "total_volume") or 0)
            target["total_oi"] = int(_number(row, "open_interest", "oi", "total_oi") or 0)
        target["type"] = target["type"] or _text(row, "expiration_type", "expiry_type")
    return [
        ExpiryAggregate(
            expiration,
            values["call_volume"],
            values["put_volume"],
            values["call_oi"],
            values["put_oi"],
            values["total_volume"],
            values["total_oi"],
            values["type"],
        )
        for expiration, values in sorted(combined.items())
    ]


OSI = re.compile(r"^(?P<ticker>[A-Z.]+)(?P<date>\d{6})(?P<right>[CP])(?P<strike>\d{8})$")


@dataclass(frozen=True)
class ChainContract:
    symbol: str
    expiration: date
    right: str
    strike: Decimal
    volume: int
    previous_oi: int
    bid: Decimal | None
    ask: Decimal | None
    last: Decimal | None
    delta: float | None
    spot: Decimal | None
    vendor_premium: float | None
    observed_at: datetime | None


def _decimal(value: float | None) -> Decimal | None:
    if value is None:
        return None
    try:
        return Decimal(str(value))
    except InvalidOperation:
        return None


def _osi_fields(symbol: str) -> tuple[date | None, str | None, Decimal | None]:
    match = OSI.match(symbol)
    if not match:
        return None, None, None
    try:
        expiry = datetime.strptime(match.group("date"), "%y%m%d").date()
    except ValueError:
        expiry = None
    return expiry, match.group("right"), Decimal(match.group("strike")) / 1000


def parse_chain(payload: Any, expected_expiration: date) -> list[ChainContract]:
    contracts: dict[str, ChainContract] = {}
    for row in object_rows(payload):
        symbol = _text(
            row, "contract_symbol", "option_symbol", "option_ticker", "contract", "symbol"
        )
        if not symbol:
            continue
        osi_expiry, osi_right, osi_strike = _osi_fields(symbol.upper().removeprefix("O:"))
        expiration = _date(row, "expiration", "expiry", "expiration_date") or osi_expiry
        right_raw = (
            _text(row, "right", "option_right", "option_type", "contract_type") or osi_right or ""
        ).upper()
        right = "C" if right_raw in {"C", "CALL"} else "P" if right_raw in {"P", "PUT"} else ""
        strike = _decimal(_number(row, "strike", "strike_price")) or osi_strike
        if (
            expiration != expected_expiration
            or right not in {"C", "P"}
            or strike is None
            or strike <= 0
        ):
            continue
        observed = _text(row, "observed_at", "updated_at", "timestamp", "as_of")
        try:
            observed_at = (
                datetime.fromisoformat(observed.replace("Z", "+00:00")) if observed else None
            )
        except ValueError:
            observed_at = None
        contracts[symbol] = ChainContract(
            symbol=symbol,
            expiration=expiration,
            right=right,
            strike=strike,
            volume=max(0, int(_number(row, "volume", "day_volume", "today_volume") or 0)),
            previous_oi=max(
                0, int(_number(row, "previous_oi", "prev_oi", "open_interest", "oi") or 0)
            ),
            bid=_decimal(_number(row, "bid", "bid_price")),
            ask=_decimal(_number(row, "ask", "ask_price")),
            last=_decimal(_number(row, "last", "last_price", "close")),
            delta=_number(row, "delta"),
            spot=_decimal(_number(row, "spot", "underlying_price", "underlying_last")),
            vendor_premium=_number(
                row, "premium", "premium_usd", "traded_value", "traded_value_usd"
            ),
            observed_at=observed_at,
        )
    return list(contracts.values())


def intraday_metrics(payload: Any) -> tuple[float | None, float | None]:
    bars: list[tuple[float, float | None]] = []
    for row in object_rows(payload):
        volume = _number(row, "volume", "v")
        if volume is None:
            continue
        price = _number(row, "vwap", "vw", "close", "price", "c")
        bars.append((max(0, volume), price))
    if not bars:
        return None, None
    rolling = [
        sum(volume for volume, _ in bars[index : index + 5])
        for index in range(max(1, len(bars) - 4))
    ]
    positive = [value for value in rolling if value > 0]
    burst = (
        max(positive) / statistics.median(positive)
        if positive and statistics.median(positive)
        else None
    )
    traded = [(volume, price) for volume, price in bars if price is not None and volume > 0]
    total = sum(volume for volume, _ in traded)
    vwap = sum(volume * float(price) for volume, price in traded) / total if total else None
    return burst, vwap


def first_meta(payload: Any, *names: str) -> Any:
    if isinstance(payload, dict):
        meta = payload.get("_meta")
        if isinstance(meta, dict):
            for name in names:
                if name in meta:
                    return meta[name]
    return None

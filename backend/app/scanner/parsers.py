from __future__ import annotations

import re
import statistics
from dataclasses import dataclass
from datetime import date, datetime, timezone
from decimal import Decimal, InvalidOperation
from math import isfinite
from typing import Any

from app.scanner.config import ARCHIVE_LIMITS


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


def _datetime(value: Any) -> datetime | None:
    if value in (None, ""):
        return None
    try:
        parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
        return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)
    except ValueError:
        return None


@dataclass(frozen=True)
class DailyExpiryOi:
    expiration: date
    vendor_date: date
    vendor_as_of: datetime
    call_oi: int
    put_oi: int


def parse_daily_expiry_oi(payload: Any) -> list[DailyExpiryOi]:
    data = payload.get("data") if isinstance(payload, dict) else None
    if not isinstance(data, dict):
        return []
    as_of = _datetime(data.get("as_of"))
    expiries = data.get("expiries")
    if as_of is None or not isinstance(expiries, list):
        return []
    parsed: list[DailyExpiryOi] = []
    for row in expiries:
        if not isinstance(row, dict):
            continue
        expiration = _date(row, "expiry", "expiration")
        vendor_date = _date(row, "date") or as_of.date()
        call_oi = _number(row, "call_oi")
        put_oi = _number(row, "put_oi")
        if expiration is None or call_oi is None or put_oi is None:
            continue
        parsed.append(DailyExpiryOi(expiration, vendor_date, as_of, int(call_oi), int(put_oi)))
    return sorted(parsed, key=lambda item: item.expiration)


@dataclass(frozen=True)
class ArchivedChainContract:
    symbol: str
    expiration: date
    right: str
    strike: Decimal
    open_interest: int
    bid: Decimal | None
    ask: Decimal | None
    implied_volatility: Decimal | None
    delta: Decimal | None
    gamma: Decimal | None
    theta: Decimal | None
    vega: Decimal | None
    charm: Decimal | None
    open_interest_as_of: datetime | None


@dataclass(frozen=True)
class CompleteChain:
    complete: bool
    reason: str
    invalid_row_reasons: dict[str, int]
    contracts: tuple[ArchivedChainContract, ...]
    returned_count: int
    total_contracts: int | None
    truncated: bool | None
    underlying_price: Decimal | None
    quote_as_of: datetime | None
    greeks_as_of: datetime | None
    underlying_as_of: datetime | None
    open_interest_as_of: datetime | None


def _archived_chain_row_issue(row: Any, expected_expiration: date) -> str | None:
    if not isinstance(row, dict):
        return "ROW_NOT_OBJECT"
    if not _text(row, "contract_symbol"):
        return "MISSING_CONTRACT_SYMBOL"
    if _date(row, "expiration") != expected_expiration:
        return "EXPIRATION_MISMATCH"
    if (_text(row, "right") or "").upper() not in {"C", "P"}:
        return "INVALID_RIGHT"
    strike = _decimal(_number(row, "strike_usd"))
    if strike is None or strike <= 0:
        return "INVALID_STRIKE"
    open_interest = _number(row, "open_interest")
    if (
        open_interest is None
        or not isfinite(open_interest)
        or open_interest < 0
        or not open_interest.is_integer()
    ):
        return "INVALID_OPEN_INTEREST"
    return None


def parse_complete_chain(payload: Any, expected_expiration: date) -> CompleteChain:
    payload_is_object = isinstance(payload, dict)
    data = payload.get("data") if payload_is_object else None
    meta = payload.get("_meta") if isinstance(payload, dict) else None
    data_is_object = isinstance(data, dict)
    data = data if isinstance(data, dict) else {}
    meta = meta if isinstance(meta, dict) else {}
    contracts_value = data.get("contracts")
    rows = contracts_value if isinstance(contracts_value, list) else []
    total_raw = data.get("total_contracts")
    total = (
        int(total_raw)
        if isinstance(total_raw, (int, float)) and not isinstance(total_raw, bool)
        else None
    )
    truncated = meta.get("truncated") if isinstance(meta.get("truncated"), bool) else None
    chain_open_interest_as_of = _datetime(data.get("open_interest_as_of"))
    invalid_row_reasons: dict[str, int] = {}
    symbols: set[str] = set()
    duplicate_symbols = 0
    for row in rows:
        issue = _archived_chain_row_issue(row, expected_expiration)
        if issue is not None:
            invalid_row_reasons[issue] = invalid_row_reasons.get(issue, 0) + 1
            continue
        assert isinstance(row, dict)
        symbol = _text(row, "contract_symbol") or ""
        if symbol in symbols:
            duplicate_symbols += 1
        symbols.add(symbol)
    if duplicate_symbols:
        invalid_row_reasons["DUPLICATE_CONTRACT_SYMBOL"] = duplicate_symbols

    if not payload_is_object or not data_is_object or not isinstance(contracts_value, list):
        reason = "INVALID_RESPONSE"
    elif truncated is True:
        reason = "TRUNCATED"
    elif truncated is not False or total is None or total < 0:
        reason = "INVALID_RESPONSE"
    elif any(
        issue != "DUPLICATE_CONTRACT_SYMBOL" for issue in invalid_row_reasons
    ):
        reason = "INVALID_RESPONSE"
    elif duplicate_symbols:
        reason = "ROW_COUNT_MISMATCH"
    elif len(rows) == total:
        reason = "FULL_COMPLETE"
    elif (
        total > len(rows)
        and len(rows) == ARCHIVE_LIMITS.vendor_chain_contract_limit
        and ARCHIVE_LIMITS.vendor_chain_pagination_supported is False
    ):
        # Nightwatch intentionally returns its full supported near-ATM product here,
        # not the mathematically full expiry chain. The meta truncated=false flag does
        # not describe this internal cap, so total/returned/limit define this case.
        reason = "COMPLETE_BOUNDED_SNAPSHOT"
    else:
        reason = "ROW_COUNT_MISMATCH"

    complete = reason in {"FULL_COMPLETE", "COMPLETE_BOUNDED_SNAPSHOT"}
    contracts: list[ArchivedChainContract] = []
    if complete:
        for row in rows:
            assert isinstance(row, dict)
            symbol = _text(row, "contract_symbol")
            expiration = _date(row, "expiration")
            right = (_text(row, "right") or "").upper()
            strike = _decimal(_number(row, "strike_usd"))
            oi = _number(row, "open_interest")
            assert symbol and expiration == expected_expiration
            assert right in {"C", "P"} and strike is not None and oi is not None
            contracts.append(
                ArchivedChainContract(
                    symbol=symbol,
                    expiration=expiration,
                    right=right,
                    strike=strike,
                    open_interest=max(0, int(oi)),
                    bid=_decimal(_number(row, "bid_usd")),
                    ask=_decimal(_number(row, "ask_usd")),
                    implied_volatility=_decimal(_number(row, "implied_vol_pct")),
                    delta=_decimal(_number(row, "delta")),
                    gamma=_decimal(_number(row, "gamma")),
                    theta=_decimal(_number(row, "theta")),
                    vega=_decimal(_number(row, "vega")),
                    charm=_decimal(_number(row, "charm")),
                    open_interest_as_of=_datetime(row.get("open_interest_as_of")),
                )
            )
    return CompleteChain(
        complete=complete,
        reason=reason,
        invalid_row_reasons=dict(sorted(invalid_row_reasons.items())),
        contracts=tuple(contracts),
        returned_count=len(rows),
        total_contracts=total,
        truncated=truncated,
        underlying_price=_decimal(_number(data, "underlying_price_usd")),
        quote_as_of=_datetime(data.get("quote_as_of")),
        greeks_as_of=_datetime(data.get("greeks_as_of")),
        underlying_as_of=_datetime(data.get("underlying_as_of")),
        open_interest_as_of=chain_open_interest_as_of,
    )


@dataclass(frozen=True)
class TickerActivity:
    vendor_as_of: datetime | None
    vendor_date: date | None
    call_volume: int | None
    put_volume: int | None
    call_oi: int | None
    put_oi: int | None
    premiums: dict[str, float]


def parse_ticker_activity(payload: Any) -> TickerActivity:
    data = payload.get("data") if isinstance(payload, dict) else None
    data = data if isinstance(data, dict) else {}
    day = data.get("day") if isinstance(data.get("day"), dict) else {}
    premiums = {
        key: float(value)
        for key, value in day.items()
        if "premium" in key and isinstance(value, (int, float))
    }

    def integer(name: str) -> int | None:
        value = _number(day, name)
        return int(value) if value is not None else None

    return TickerActivity(
        vendor_as_of=_datetime(data.get("as_of")),
        vendor_date=_date(day, "date"),
        call_volume=integer("call_volume"),
        put_volume=integer("put_volume"),
        call_oi=integer("call_open_interest"),
        put_oi=integer("put_open_interest"),
        premiums=premiums,
    )


@dataclass(frozen=True)
class RadarContract:
    symbol: str
    observation_date: date | None
    previous_date: date | None
    previous_oi: int | None
    current_oi: int | None
    delta_oi: int | None
    relative_change: float | None
    volume: int | None
    trades: int | None
    average_price: float | None
    premium: float | None
    rank: int | None
    last_bid: float | None
    last_ask: float | None
    last_fill: float | None


def parse_oi_change_radar(payload: Any) -> list[RadarContract]:
    data = payload.get("data") if isinstance(payload, dict) else None
    rows = (
        data.get("contracts")
        if isinstance(data, dict) and isinstance(data.get("contracts"), list)
        else []
    )
    result: list[RadarContract] = []
    for row in rows:
        if not isinstance(row, dict) or not _text(row, "option_symbol"):
            continue

        def integer(name: str, source: dict[str, Any] = row) -> int | None:
            value = _number(source, name)
            return int(value) if value is not None else None

        result.append(
            RadarContract(
                symbol=_text(row, "option_symbol") or "",
                observation_date=_date(row, "date"),
                previous_date=_date(row, "prev_date"),
                previous_oi=integer("prev_oi"),
                current_oi=integer("oi"),
                delta_oi=integer("oi_diff"),
                relative_change=_number(row, "oi_change"),
                volume=integer("volume"),
                trades=integer("trades"),
                average_price=_number(row, "avg_price_usd"),
                premium=_number(row, "premium_usd"),
                rank=integer("rank"),
                last_bid=_number(row, "last_bid_usd"),
                last_ask=_number(row, "last_ask_usd"),
                last_fill=_number(row, "last_fill_usd"),
            )
        )
    return result

from datetime import date

from app.scanner.parsers import parse_chain, parse_expiry_aggregates
from app.scanner.scoring import skew


def test_expiry_parser_is_call_put_symmetric_and_shares_are_computable() -> None:
    payload = {
        "data": [
            {
                "expiration": "2026-08-21",
                "option_type": "call",
                "volume": 600,
                "open_interest": 900,
            },
            {
                "expiration": "2026-08-21",
                "option_type": "put",
                "volume": 400,
                "open_interest": 1100,
            },
            {
                "expiration": "2026-09-18",
                "call_volume": 250,
                "put_volume": 250,
                "call_oi": 1000,
                "put_oi": 1000,
            },
        ]
    }
    rows = parse_expiry_aggregates(payload)
    assert rows[0].call_volume == 600 and rows[0].put_volume == 400
    assert rows[0].total_volume / sum(row.total_volume for row in rows) == 2 / 3
    assert rows[0].total_oi / sum(row.total_oi for row in rows) == 0.5
    assert skew(rows[0].call_volume, rows[0].put_volume) == 0.2


def test_chain_parser_uses_documented_osi_without_inventing_missing_quote() -> None:
    rows = parse_chain(
        {"data": [{"option_symbol": "AAPL260821C00200000", "volume": 10, "open_interest": 2}]},
        date(2026, 8, 21),
    )
    assert len(rows) == 1
    assert rows[0].right == "C" and rows[0].strike == 200
    assert rows[0].bid is None and rows[0].ask is None


def test_live_total_only_expiry_shape_preserves_unknown_sides() -> None:
    rows = parse_expiry_aggregates(
        {
            "data": {
                "as_of": None,
                "expiries": [
                    {"oi": 94696, "expiry": "2026-08-12", "volume": 184337}
                ],
            }
        }
    )
    assert rows[0].total_volume == 184337
    assert rows[0].total_oi == 94696
    assert rows[0].call_volume is None and rows[0].put_volume is None

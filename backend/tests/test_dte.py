from datetime import date

import pytest

from app.models.signals import DteBucket, bucket_for_dte, calendar_dte


@pytest.mark.parametrize(
    ("dte", "expected"),
    [
        (-1, None),
        (0, DteBucket.VERY_SHORT),
        (7, DteBucket.VERY_SHORT),
        (8, DteBucket.SHORT),
        (30, DteBucket.SHORT),
        (31, DteBucket.MEDIUM),
        (90, DteBucket.MEDIUM),
        (91, DteBucket.LONG),
        (180, DteBucket.LONG),
        (181, None),
    ],
)
def test_default_bucket_boundaries(dte: int, expected: DteBucket | None) -> None:
    assert bucket_for_dte(dte) == expected


def test_calendar_dte_is_not_business_days() -> None:
    assert calendar_dte(date(2026, 8, 10), date(2026, 8, 7)) == 3


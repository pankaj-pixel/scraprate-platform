from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal

import pytest

from app.services.market_price_service import (
    calculate_indicative_rate,
    confidence_level,
    calculate_daily_change,
)


@dataclass(frozen=True)
class Observation:
    average: Decimal
    low: Decimal = Decimal("90")
    high: Decimal = Decimal("110")
    unit: str = "kg"
    trust_score: Decimal = Decimal("50")
    is_verified: bool = False
    is_active: bool = True
    is_demo: bool = False
    price_date: date = date(2026, 8, 22)
    last_updated: datetime = datetime(2026, 8, 22, 9, 30)


def observation(average: str, **changes) -> Observation:
    values = {"average": Decimal(average)}
    for key, value in changes.items():
        values[key] = Decimal(value) if key in {"low", "high", "trust_score"} else value
    return Observation(**values)


def test_one_source():
    result = calculate_indicative_rate([observation("100")])
    assert result.source_count == 1
    assert result.indicative_price == Decimal("100.00")
    assert result.confidence == "LOW"


def test_multiple_sources_use_full_range():
    result = calculate_indicative_rate(
        [observation("100", low="80", high="105"), observation("120", low="110", high="140")]
    )
    assert result.source_count == 2
    assert result.low == Decimal("80.00")
    assert result.high == Decimal("140.00")


def test_different_trust_scores_influence_rate():
    result = calculate_indicative_rate(
        [observation("100", trust_score="90"), observation("200", trust_score="10")]
    )
    assert result.weighted_average == Decimal("110.00")
    assert result.indicative_price == Decimal("130.00")


def test_inactive_source_is_ignored():
    result = calculate_indicative_rate(
        [observation("100"), observation("900", is_active=False)]
    )
    assert result.source_count == 1
    assert result.indicative_price == Decimal("100.00")


def test_demo_only_data_is_labeled_demo():
    result = calculate_indicative_rate([observation("100", is_demo=True)])
    assert result.data_type == "demo"


def test_real_data_takes_priority_over_demo():
    result = calculate_indicative_rate(
        [observation("900", is_demo=True), observation("100", is_demo=False)]
    )
    assert result.data_type == "real"
    assert result.source_count == 1
    assert result.indicative_price == Decimal("100.00")


def test_median_calculation_for_even_source_count():
    result = calculate_indicative_rate(
        [observation("100"), observation("110"), observation("300"), observation("500")]
    )
    assert result.median == Decimal("205.00")


def test_weighted_average_calculation():
    result = calculate_indicative_rate(
        [observation("50", trust_score="20"), observation("100", trust_score="80")]
    )
    assert result.weighted_average == Decimal("90.00")


def test_no_available_observations():
    assert calculate_indicative_rate([]) is None
    assert calculate_indicative_rate([observation("100", is_active=False)]) is None


@pytest.mark.parametrize(
    ("count", "verified", "trust", "expected"),
    [
        (1, 1, Decimal("90"), "LOW"),
        (2, 1, Decimal("50"), "MEDIUM"),
        (3, 2, Decimal("60"), "HIGH"),
    ],
)
def test_confidence_low_medium_high(count, verified, trust, expected):
    assert confidence_level(count, verified, trust) == expected


def test_daily_change_uses_previous_indicative_rate():
    change, percentage = calculate_daily_change(Decimal("110"), Decimal("100"))
    assert change == Decimal("10.00")
    assert percentage == Decimal("10.00")


def test_daily_change_is_null_without_previous_rate():
    assert calculate_daily_change(Decimal("110"), None) == (None, None)

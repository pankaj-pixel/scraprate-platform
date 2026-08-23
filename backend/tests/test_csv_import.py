from decimal import Decimal

import pytest

from app.ingestion.csv_import import CsvImportError, parse_csv

HEADER = "date,city,material,grade,low_price,average_price,high_price,unit,source\n"


def test_valid_csv_row_is_parsed_and_decimal_safe():
    rows, issues = parse_csv(
        (HEADER + "2026-08-22,delhi,copper,,700.10,710.20,720.30,kg,test-source\n").encode()
    )
    assert issues == []
    assert len(rows) == 1
    assert rows[0].average_price == Decimal("710.20")


def test_malformed_price_is_rejected():
    rows, issues = parse_csv(
        (HEADER + "2026-08-22,delhi,copper,,bad,710,720,kg,test-source\n").encode()
    )
    assert rows == []
    assert "low_price must be a valid number" in issues[0].errors


@pytest.mark.parametrize(
    "prices",
    ["720,710,730", "700,730,720"],
)
def test_invalid_price_order_is_rejected(prices):
    rows, issues = parse_csv(
        (HEADER + f"2026-08-22,delhi,copper,,{prices},kg,test-source\n").encode()
    )
    assert rows == []
    assert "low_price must be <= average_price <= high_price" in issues[0].errors


def test_missing_required_header_is_rejected():
    with pytest.raises(CsvImportError, match="Missing required CSV columns"):
        parse_csv(b"date,city,material\n2026-08-22,delhi,copper\n")


def test_negative_price_is_rejected():
    rows, issues = parse_csv(
        (HEADER + "2026-08-22,delhi,copper,,-1,10,20,kg,test-source\n").encode()
    )
    assert rows == []
    assert "low_price cannot be negative" in issues[0].errors

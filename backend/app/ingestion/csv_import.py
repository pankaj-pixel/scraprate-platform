import csv
import io
from datetime import date
from decimal import Decimal, InvalidOperation

from app.ingestion.base import ParsedPriceRow, RowIssue

REQUIRED_COLUMNS = (
    "date",
    "city",
    "material",
    "grade",
    "low_price",
    "average_price",
    "high_price",
    "unit",
    "source",
)
MAX_CSV_BYTES = 2 * 1024 * 1024
MAX_CSV_ROWS = 1000
MONEY_PRECISION = Decimal("0.01")


class CsvImportError(ValueError):
    pass


def _decimal(value: str, field: str) -> Decimal:
    try:
        number = Decimal(value.strip())
    except (InvalidOperation, AttributeError) as error:
        raise ValueError(f"{field} must be a valid number") from error
    if not number.is_finite():
        raise ValueError(f"{field} must be a finite number")
    if number < 0:
        raise ValueError(f"{field} cannot be negative")
    return number.quantize(MONEY_PRECISION)


def parse_csv(content: bytes) -> tuple[list[ParsedPriceRow], list[RowIssue]]:
    if not content:
        raise CsvImportError("CSV file is empty")
    if len(content) > MAX_CSV_BYTES:
        raise CsvImportError("CSV file exceeds the 2 MB limit")
    try:
        text = content.decode("utf-8-sig")
    except UnicodeDecodeError as error:
        raise CsvImportError("CSV must use UTF-8 encoding") from error
    reader = csv.DictReader(io.StringIO(text))
    headers = tuple(reader.fieldnames or ())
    missing = [column for column in REQUIRED_COLUMNS if column not in headers]
    if missing:
        raise CsvImportError(f"Missing required CSV columns: {', '.join(missing)}")

    parsed: list[ParsedPriceRow] = []
    issues: list[RowIssue] = []
    for index, raw_row in enumerate(reader, start=2):
        if index - 1 > MAX_CSV_ROWS:
            raise CsvImportError(f"CSV cannot contain more than {MAX_CSV_ROWS} rows")
        raw = {column: (raw_row.get(column) or "").strip() for column in REQUIRED_COLUMNS}
        if not any(raw.values()):
            continue
        errors = []
        try:
            price_date = date.fromisoformat(raw["date"])
        except ValueError:
            errors.append("date must use YYYY-MM-DD format")
            price_date = None
        for field in ("city", "material", "unit", "source"):
            if not raw[field]:
                errors.append(f"{field} is required")
        prices = {}
        for field in ("low_price", "average_price", "high_price"):
            try:
                prices[field] = _decimal(raw[field], field)
            except ValueError as error:
                errors.append(str(error))
        if len(prices) == 3 and not (
            prices["low_price"] <= prices["average_price"] <= prices["high_price"]
        ):
            errors.append("low_price must be <= average_price <= high_price")
        if errors:
            issues.append(RowIssue(index, errors, raw))
            continue
        parsed.append(
            ParsedPriceRow(
                row_number=index,
                date=price_date,
                city=raw["city"],
                material=raw["material"],
                grade=raw["grade"] or None,
                low_price=prices["low_price"],
                average_price=prices["average_price"],
                high_price=prices["high_price"],
                unit=raw["unit"],
                source=raw["source"],
                raw=raw,
            )
        )
    return parsed, issues

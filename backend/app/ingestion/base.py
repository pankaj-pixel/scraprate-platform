from dataclasses import dataclass
from datetime import date
from decimal import Decimal


@dataclass(frozen=True)
class ParsedPriceRow:
    row_number: int
    date: date
    city: str | None
    material: str
    grade: str | None
    low_price: Decimal
    average_price: Decimal
    high_price: Decimal
    unit: str
    source: str
    raw: dict[str, str]
    price_context: str = "local_scrap"


@dataclass(frozen=True)
class NormalizedPriceInput:
    row_number: int
    date: date
    city: str | None
    city_id: int | None
    material: str
    material_id: int
    grade: str | None
    grade_id: int | None
    low_price: Decimal
    average_price: Decimal
    high_price: Decimal
    unit: str
    source: str
    source_id: int
    source_type: str
    source_trust_score: Decimal
    source_is_verified: bool
    confidence_score: Decimal
    is_demo: bool = False
    price_context: str = "local_scrap"

    @property
    def identity(self) -> tuple[int, int, int, date, int, str]:
        return (
            self.material_id,
            self.grade_id or 0,
            self.city_id or 0,
            self.date,
            self.source_id,
            self.price_context,
        )


@dataclass(frozen=True)
class RowIssue:
    row_number: int
    errors: list[str]
    raw: dict[str, str]

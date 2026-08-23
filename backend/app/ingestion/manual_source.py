from app.ingestion.base import ParsedPriceRow
from app.schemas import AdminPriceCreate


def from_admin_payload(payload: AdminPriceCreate, row_number: int = 1) -> ParsedPriceRow:
    """Adapt a manual payload to the common ingestion shape.

    Existing manual admin routes remain unchanged; this adapter provides the
    shared normalization boundary for future consolidation.
    """
    raw = {
        "date": payload.date.isoformat(),
        "city": payload.city,
        "material": payload.material,
        "grade": payload.grade or "",
        "low_price": str(payload.low_price),
        "average_price": str(payload.average_price),
        "high_price": str(payload.high_price),
        "unit": payload.unit,
        "source": payload.source,
    }
    return ParsedPriceRow(
        row_number=row_number,
        date=payload.date,
        city=payload.city,
        material=payload.material,
        grade=payload.grade,
        low_price=payload.low_price,
        average_price=payload.average_price,
        high_price=payload.high_price,
        unit=payload.unit,
        source=payload.source,
        raw=raw,
    )

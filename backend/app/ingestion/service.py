from decimal import Decimal, ROUND_HALF_UP

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.ingestion.base import NormalizedPriceInput, ParsedPriceRow, RowIssue
from app.ingestion.csv_import import parse_csv
from app.models import Material
from app.repositories import ingestion_repository
from app.schemas import ApprovedImportRow

CONFIDENCE_PRECISION = Decimal("0.0001")


class IngestionError(Exception):
    pass


class IngestionConflictError(IngestionError):
    pass


def _key(value: str) -> str:
    return value.strip().lower()


def _lookup(items, *attributes: str):
    result = {}
    for item in items:
        for attribute in attributes:
            value = getattr(item, attribute, None)
            if value:
                result[_key(value)] = item
    return result


def _issue(row: ParsedPriceRow, *errors: str) -> RowIssue:
    return RowIssue(row.row_number, list(errors), row.raw)


def _serialize_issue(issue: RowIssue) -> dict:
    return {
        "row_number": issue.row_number,
        "errors": issue.errors,
        "raw": issue.raw,
    }


def _serialize_valid(row: NormalizedPriceInput) -> dict:
    return {
        "row_number": row.row_number,
        "date": row.date,
        "city": row.city,
        "material": row.material,
        "grade": row.grade,
        "low_price": row.low_price,
        "average_price": row.average_price,
        "high_price": row.high_price,
        "unit": row.unit,
        "source": row.source,
        "source_type": row.source_type,
        "source_trust_score": row.source_trust_score,
        "source_is_verified": row.source_is_verified,
        "confidence_score": row.confidence_score,
        "is_demo": False,
    }


def _normalize(
    session: Session, rows: list[ParsedPriceRow]
) -> tuple[list[NormalizedPriceInput], dict[str, list[RowIssue]]]:
    cities, materials, sources = ingestion_repository.load_reference_data(session)
    city_lookup = _lookup(cities, "slug", "name")
    material_lookup = _lookup(materials, "slug", "name")
    source_lookup = _lookup(sources, "slug", "name")
    normalized = []
    issues = {
        "invalid": [],
        "unknown_materials": [],
        "unknown_cities": [],
        "unknown_grades": [],
        "unknown_sources": [],
    }
    for row in rows:
        benchmark = row.price_context == "benchmark"
        city = city_lookup.get(_key(row.city)) if row.city else None
        material: Material | None = material_lookup.get(_key(row.material))
        source = source_lookup.get(_key(row.source))
        row_errors = []
        if city is None and not benchmark:
            issue = _issue(row, "Unknown city")
            issues["unknown_cities"].append(issue)
            row_errors.append("Unknown city")
        if material is None:
            issue = _issue(row, "Unknown material")
            issues["unknown_materials"].append(issue)
            row_errors.append("Unknown material")
        grade = None
        if material is not None and row.grade:
            grade_lookup = _lookup(
                [grade for grade in material.grades if grade.is_active], "slug", "name"
            )
            grade = grade_lookup.get(_key(row.grade))
            if grade is None:
                issue = _issue(row, "Unknown grade for selected material")
                issues["unknown_grades"].append(issue)
                row_errors.append("Unknown grade for selected material")
        if source is None:
            issue = _issue(row, "Unknown price source")
            issues["unknown_sources"].append(issue)
            row_errors.append("Unknown price source")
        elif not source.is_active:
            row_errors.append("Price source is inactive")
        if source is not None and city is not None and source.city_id not in (None, city.id):
            row_errors.append("Price source is not configured for selected city")
        if benchmark and source is not None and source.source_type != "market_reference":
            row_errors.append("Benchmark observations require a market_reference source")
        if material is not None and _key(row.unit) != _key(material.unit):
            row_errors.append(f"Unit must be {material.unit} for {material.name}")
        if row_errors:
            issues["invalid"].append(_issue(row, *row_errors))
            continue
        trust = Decimal(source.trust_score)
        normalized.append(
            NormalizedPriceInput(
                row_number=row.row_number,
                date=row.date,
                city=city.slug if city else None,
                city_id=city.id if city else None,
                material=material.slug,
                material_id=material.id,
                grade=grade.slug if grade else None,
                grade_id=grade.id if grade else None,
                low_price=row.low_price,
                average_price=row.average_price,
                high_price=row.high_price,
                unit=material.unit,
                source=source.slug,
                source_id=source.id,
                source_type=source.source_type,
                source_trust_score=trust,
                source_is_verified=source.is_verified,
                confidence_score=(trust / Decimal("100")).quantize(
                    CONFIDENCE_PRECISION, rounding=ROUND_HALF_UP
                ),
                is_demo=False,
                price_context=row.price_context,
            )
        )
    return normalized, issues


def _separate_duplicates(
    session: Session, rows: list[NormalizedPriceInput]
) -> tuple[list[NormalizedPriceInput], list[RowIssue]]:
    existing = ingestion_repository.find_existing_identities(
        session, {row.identity for row in rows}
    )
    seen = set()
    valid = []
    duplicates = []
    for row in rows:
        if row.identity in existing:
            duplicates.append(
                RowIssue(row.row_number, ["Observation already exists in database"], _raw(row))
            )
        elif row.identity in seen:
            duplicates.append(
                RowIssue(row.row_number, ["Duplicate observation within import"], _raw(row))
            )
        else:
            seen.add(row.identity)
            valid.append(row)
    return valid, duplicates


def _raw(row: NormalizedPriceInput) -> dict[str, str]:
    return {
        "date": row.date.isoformat(),
        "city": row.city or "",
        "material": row.material,
        "grade": row.grade or "",
        "low_price": str(row.low_price),
        "average_price": str(row.average_price),
        "high_price": str(row.high_price),
        "unit": row.unit,
        "source": row.source,
        "price_context": row.price_context,
    }


def preview_csv(session: Session, content: bytes) -> dict:
    parsed, parse_issues = parse_csv(content)
    normalized, categories = _normalize(session, parsed)
    valid, duplicates = _separate_duplicates(session, normalized)
    invalid = parse_issues + categories["invalid"]
    return {
        "total_rows": len(parsed) + len(parse_issues),
        "valid_rows": [_serialize_valid(row) for row in valid],
        "invalid_rows": [_serialize_issue(issue) for issue in invalid],
        "duplicate_rows": [_serialize_issue(issue) for issue in duplicates],
        "unknown_materials": [
            _serialize_issue(issue) for issue in categories["unknown_materials"]
        ],
        "unknown_cities": [
            _serialize_issue(issue) for issue in categories["unknown_cities"]
        ],
        "unknown_grades": [
            _serialize_issue(issue) for issue in categories["unknown_grades"]
        ],
        "unknown_sources": [
            _serialize_issue(issue) for issue in categories["unknown_sources"]
        ],
    }


def _from_approved(row: ApprovedImportRow) -> ParsedPriceRow:
    raw = {
        "date": row.date.isoformat(),
        "city": row.city,
        "material": row.material,
        "grade": row.grade or "",
        "low_price": str(row.low_price),
        "average_price": str(row.average_price),
        "high_price": str(row.high_price),
        "unit": row.unit,
        "source": row.source,
    }
    return ParsedPriceRow(row.row_number, row.date, row.city, row.material, row.grade, row.low_price, row.average_price, row.high_price, row.unit, row.source, raw, "local_scrap")


def commit_rows(session: Session, approved: list[ApprovedImportRow]) -> dict:
    normalized, categories = _normalize(
        session, [_from_approved(row) for row in approved]
    )
    valid, duplicates = _separate_duplicates(session, normalized)
    values = [
        {
            "material_id": row.material_id,
            "material_grade_id": row.grade_id,
            "city_id": row.city_id,
            "price_date": row.date,
            "price_low": row.low_price,
            "price_average": row.average_price,
            "price_high": row.high_price,
            "unit": row.unit,
            "source_id": row.source_id,
            "source_type": row.source_type,
            "confidence_score": row.confidence_score,
            "is_demo": False,
            "price_context": row.price_context,
        }
        for row in valid
    ]
    try:
        inserted_ids = ingestion_repository.insert_real_observations(session, values) if values else []
    except IntegrityError as error:
        session.rollback()
        raise IngestionConflictError(
            "Import conflicted with a concurrently created observation; preview again"
        ) from error
    invalid = categories["invalid"]
    return {
        "approved_count": len(approved),
        "inserted_count": len(inserted_ids),
        "inserted_ids": inserted_ids,
        "invalid_rows": [_serialize_issue(issue) for issue in invalid],
        "duplicate_rows": [_serialize_issue(issue) for issue in duplicates],
    }

from datetime import date
from decimal import Decimal, ROUND_HALF_UP

from sqlalchemy.orm import Session
from pydantic import ValidationError

from app.models import ScrapPrice
from app.repositories import admin_price_repository
from app.schemas import AdminPriceCreate, AdminPriceUpdate
from app.services import material_service

MONEY_PRECISION = Decimal("0.01")
CONFIDENCE_PRECISION = Decimal("0.0001")


class AdminPriceError(Exception):
    pass


class AdminNotFoundError(AdminPriceError):
    pass


class AdminConflictError(AdminPriceError):
    pass


class AdminValidationError(AdminPriceError):
    pass


def _resolve_references(
    session: Session, *, city_slug: str, material_slug: str, grade_slug: str | None, source_slug: str
):
    city = material_service.find_city(session, city_slug)
    if city is None:
        raise AdminValidationError("Invalid city")
    material = material_service.find_material(session, material_slug)
    if material is None:
        raise AdminValidationError("Invalid material")
    grade = None
    if grade_slug:
        grade = material_service.find_grade(session, material, grade_slug)
        if grade is None:
            raise AdminValidationError("Invalid grade for selected material")
    source = material_service.find_price_source(session, source_slug)
    if source is None:
        raise AdminValidationError("Invalid price source")
    if source.city_id is not None and source.city_id != city.id:
        raise AdminValidationError("Price source is not configured for selected city")
    return city, material, grade, source


def _validate_range(low: Decimal, average: Decimal, high: Decimal) -> None:
    if min(low, average, high) < 0:
        raise AdminValidationError("Prices cannot be negative")
    if not low <= average <= high:
        raise AdminValidationError(
            "low_price must be <= average_price <= high_price"
        )


def _values(payload, city, material, grade, source) -> dict:
    source_type = payload.source_type.strip() if payload.source_type else source.source_type
    return {
        "material_id": material.id,
        "material_grade_id": grade.id if grade else None,
        "city_id": city.id,
        "price_date": payload.date,
        "price_low": payload.low_price.quantize(MONEY_PRECISION, rounding=ROUND_HALF_UP),
        "price_average": payload.average_price.quantize(MONEY_PRECISION, rounding=ROUND_HALF_UP),
        "price_high": payload.high_price.quantize(MONEY_PRECISION, rounding=ROUND_HALF_UP),
        "unit": payload.unit.strip(),
        "source_id": source.id,
        "source_type": source_type,
        "confidence_score": payload.confidence_score.quantize(
            CONFIDENCE_PRECISION, rounding=ROUND_HALF_UP
        ),
        "is_demo": payload.is_demo,
        "price_context": "local_scrap",
    }


def serialize_price(price: ScrapPrice) -> dict:
    return {
        "id": price.id,
        "date": price.price_date,
        "city": price.city.name,
        "city_slug": price.city.slug,
        "material": price.material.name,
        "material_slug": price.material.slug,
        "grade": price.material_grade.name if price.material_grade else None,
        "grade_slug": price.material_grade.slug if price.material_grade else None,
        "low_price": price.price_low,
        "average_price": price.price_average,
        "high_price": price.price_high,
        "unit": price.unit,
        "source": price.source.name if price.source else "Unknown source",
        "source_slug": price.source.slug if price.source else "unknown",
        "price_source_id": price.source_id,
        "source_type": price.source_type,
        "confidence_score": price.confidence_score,
        "is_demo": price.is_demo,
        "created_at": price.created_at,
        "updated_at": price.updated_at,
    }


def list_prices(
    session: Session,
    *,
    city_slug: str | None,
    material_slug: str | None,
    price_date: date | None,
    is_demo: bool | None,
    limit: int,
) -> list[dict]:
    city = None
    material = None
    if city_slug:
        city = material_service.find_city(session, city_slug)
        if city is None:
            raise AdminValidationError("Invalid city")
    if material_slug:
        material = material_service.find_material(session, material_slug)
        if material is None:
            raise AdminValidationError("Invalid material")
    records = admin_price_repository.list_prices(
        session,
        city_id=city.id if city else None,
        material_id=material.id if material else None,
        price_date=price_date,
        is_demo=is_demo,
        limit=limit,
    )
    return [serialize_price(record) for record in records]


def create_price(session: Session, payload: AdminPriceCreate) -> dict:
    city, material, grade, source = _resolve_references(
        session,
        city_slug=payload.city,
        material_slug=payload.material,
        grade_slug=payload.grade,
        source_slug=payload.source,
    )
    duplicate = admin_price_repository.find_duplicate(
        session,
        material_id=material.id,
        grade_id=grade.id if grade else None,
        city_id=city.id,
        price_date=payload.date,
        source_id=source.id,
    )
    if duplicate:
        raise AdminConflictError(
            f"Price observation already exists with id {duplicate.id}; use PUT or PATCH to edit it"
        )
    return serialize_price(
        admin_price_repository.add_price(
            session, _values(payload, city, material, grade, source)
        )
    )


def update_price(
    session: Session,
    price_id: int,
    payload: AdminPriceCreate | AdminPriceUpdate,
    *,
    partial: bool,
) -> dict:
    existing = admin_price_repository.get_price(session, price_id)
    if existing is None:
        raise AdminNotFoundError("Price record not found")
    if partial:
        changes = payload.model_dump(exclude_unset=True)
        if not changes:
            raise AdminValidationError("At least one field must be provided")
        try:
            merged = AdminPriceCreate(
                date=changes.get("date", existing.price_date),
                city=changes.get("city", existing.city.slug),
                material=changes.get("material", existing.material.slug),
                grade=changes.get(
                    "grade", existing.material_grade.slug if existing.material_grade else None
                ),
                low_price=changes.get("low_price", existing.price_low),
                average_price=changes.get("average_price", existing.price_average),
                high_price=changes.get("high_price", existing.price_high),
                unit=changes.get("unit", existing.unit),
                source=changes.get("source", existing.source.slug if existing.source else ""),
                source_type=changes.get("source_type", existing.source_type),
                confidence_score=changes.get("confidence_score", existing.confidence_score),
                is_demo=changes.get("is_demo", existing.is_demo),
            )
        except ValidationError as error:
            message = error.errors()[0].get("msg", "Invalid price update")
            raise AdminValidationError(message) from error
    else:
        merged = payload
    _validate_range(merged.low_price, merged.average_price, merged.high_price)
    city, material, grade, source = _resolve_references(
        session,
        city_slug=merged.city,
        material_slug=merged.material,
        grade_slug=merged.grade,
        source_slug=merged.source,
    )
    duplicate = admin_price_repository.find_duplicate(
        session,
        material_id=material.id,
        grade_id=grade.id if grade else None,
        city_id=city.id,
        price_date=merged.date,
        source_id=source.id,
        exclude_id=price_id,
    )
    if duplicate:
        raise AdminConflictError(
            f"Price observation already exists with id {duplicate.id}; edit that record instead"
        )
    return serialize_price(
        admin_price_repository.update_price(
            session, existing, _values(merged, city, material, grade, source)
        )
    )

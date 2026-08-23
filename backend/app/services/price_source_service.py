from decimal import Decimal, ROUND_HALF_UP

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models import PriceSource
from app.repositories import price_source_repository
from app.schemas import PriceSourceCreate, PriceSourceUpdate
from app.services import material_service

TRUST_PRECISION = Decimal("0.01")


class PriceSourceError(Exception):
    pass


class PriceSourceNotFoundError(PriceSourceError):
    pass


class PriceSourceConflictError(PriceSourceError):
    pass


class PriceSourceValidationError(PriceSourceError):
    pass


def _serialize(source: PriceSource) -> dict:
    return {
        "id": source.id,
        "name": source.name,
        "slug": source.slug,
        "source_type": source.source_type,
        "city": source.city.name if source.city else None,
        "city_slug": source.city.slug if source.city else None,
        "trust_score": source.trust_score,
        "is_verified": source.is_verified,
        "is_active": source.is_active,
        "notes": source.notes,
        "created_at": source.created_at,
        "updated_at": source.updated_at,
    }


def list_sources(session: Session, source_type: str | None = None) -> list[dict]:
    return [
        _serialize(source)
        for source in price_source_repository.list_sources(session, source_type)
    ]


def _city_id(session: Session, city_slug: str | None) -> int | None:
    if not city_slug:
        return None
    city = material_service.find_city(session, city_slug)
    if city is None:
        raise PriceSourceValidationError("Invalid city")
    return city.id


def create_source(session: Session, payload: PriceSourceCreate) -> dict:
    if price_source_repository.get_source_by_slug(session, payload.slug):
        raise PriceSourceConflictError("A price source with this slug already exists")
    values = {
        "name": payload.name.strip(),
        "slug": payload.slug,
        "source_type": payload.source_type,
        "city_id": _city_id(session, payload.city),
        "trust_score": payload.trust_score.quantize(
            TRUST_PRECISION, rounding=ROUND_HALF_UP
        ),
        "is_verified": payload.is_verified,
        "is_active": payload.is_active,
        "notes": payload.notes.strip() if payload.notes else None,
    }
    try:
        return _serialize(price_source_repository.create_source(session, values))
    except IntegrityError as error:
        session.rollback()
        raise PriceSourceConflictError("A price source with this slug already exists") from error


def update_source(
    session: Session, source_id: int, payload: PriceSourceUpdate
) -> dict:
    source = price_source_repository.get_source(session, source_id)
    if source is None:
        raise PriceSourceNotFoundError("Price source not found")
    changes = payload.model_dump(exclude_unset=True)
    if not changes:
        raise PriceSourceValidationError("At least one field must be provided")
    if "slug" in changes:
        duplicate = price_source_repository.get_source_by_slug(
            session, changes["slug"], exclude_id=source_id
        )
        if duplicate:
            raise PriceSourceConflictError("A price source with this slug already exists")
    values = {}
    for key in ("name", "slug", "source_type", "is_verified", "is_active"):
        if key in changes:
            values[key] = changes[key].strip() if key == "name" else changes[key]
    if "city" in changes:
        values["city_id"] = _city_id(session, changes["city"])
    if "trust_score" in changes:
        values["trust_score"] = changes["trust_score"].quantize(
            TRUST_PRECISION, rounding=ROUND_HALF_UP
        )
    if "notes" in changes:
        values["notes"] = changes["notes"].strip() if changes["notes"] else None
    try:
        return _serialize(
            price_source_repository.update_source(session, source, values)
        )
    except IntegrityError as error:
        session.rollback()
        raise PriceSourceConflictError("A price source with this slug already exists") from error

from datetime import datetime, timezone
from decimal import Decimal, ROUND_HALF_UP
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from app.models import PriceSubmission, ScrapPrice
from app.repositories import price_submission_repository
from app.schemas import PriceSubmissionCreate
from app.services import material_service

class SubmissionError(Exception): pass
class SubmissionNotFound(SubmissionError): pass
class SubmissionConflict(SubmissionError): pass
class SubmissionValidation(SubmissionError): pass

def _references(session, payload):
    source = material_service.find_price_source(session, payload.source)
    if not source: raise SubmissionValidation("Invalid price source")
    if not source.is_active: raise SubmissionValidation("Price source is inactive")
    if source.source_type not in {"dealer", "recycler"}: raise SubmissionValidation("Only dealer or recycler sources may submit prices")
    city = material_service.find_city(session, payload.city)
    if not city: raise SubmissionValidation("Invalid city")
    if source.city_id is not None and source.city_id != city.id: raise SubmissionValidation("Price source is not configured for selected city")
    material = material_service.find_material(session, payload.material)
    if not material: raise SubmissionValidation("Invalid material")
    grade = material_service.find_grade(session, material, payload.grade) if payload.grade else None
    if payload.grade and not grade: raise SubmissionValidation("Invalid grade for selected material")
    if payload.unit.strip().lower() != material.unit.lower(): raise SubmissionValidation(f"Unit must be {material.unit} for {material.name}")
    return source, city, material, grade

def serialize(item: PriceSubmission):
    return {"id": item.id, "source": item.source.name, "source_slug": item.source.slug, "source_type": item.source.source_type,
        "city": item.city.name, "city_slug": item.city.slug, "material": item.material.name, "material_slug": item.material.slug,
        "grade": item.material_grade.name if item.material_grade else None, "grade_slug": item.material_grade.slug if item.material_grade else None,
        "date": item.price_date, "low": item.low_price, "average": item.average_price, "high": item.high_price, "unit": item.unit,
        "status": item.status, "submitted_at": item.submitted_at, "reviewed_at": item.reviewed_at,
        "review_notes": item.review_notes, "approved_price_observation_id": item.approved_price_observation_id}

def create(session: Session, payload: PriceSubmissionCreate):
    source, city, material, grade = _references(session, payload)
    duplicate = price_submission_repository.find_pending_duplicate(session, source_id=source.id, city_id=city.id, material_id=material.id, grade_id=grade.id if grade else None, price_date=payload.date)
    if duplicate: raise SubmissionConflict(f"A pending submission already exists with id {duplicate.id}")
    money = lambda value: value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    return serialize(price_submission_repository.add(session, {"price_source_id": source.id, "city_id": city.id, "material_id": material.id,
        "material_grade_id": grade.id if grade else None, "price_date": payload.date, "low_price": money(payload.low),
        "average_price": money(payload.average), "high_price": money(payload.high), "unit": material.unit, "status": "pending"}))

def list_items(session, **filters):
    refs = {}
    for key, finder in (("source", material_service.find_price_source), ("city", material_service.find_city), ("material", material_service.find_material)):
        value = filters.pop(key, None)
        if value:
            ref = finder(session, value)
            if not ref: raise SubmissionValidation(f"Invalid {key}")
            refs[f"{key}_id"] = ref.id
    return [serialize(x) for x in price_submission_repository.list_submissions(session, **filters, **refs)]

def approve(session: Session, submission_id: int, notes: str | None):
    item = price_submission_repository.get(session, submission_id, lock=True)
    if not item: raise SubmissionNotFound("Price submission not found")
    if item.status == "approved": return serialize(item)
    if item.status != "pending": raise SubmissionConflict("Only pending submissions can be approved")
    if not item.source.is_active or item.source.source_type not in {"dealer", "recycler"}: raise SubmissionValidation("Source is no longer eligible")
    if price_submission_repository.find_observation(session, item): raise SubmissionConflict("An equivalent price observation already exists")
    observation = ScrapPrice(material_id=item.material_id, material_grade_id=item.material_grade_id, city_id=item.city_id,
        price_date=item.price_date, price_low=item.low_price, price_average=item.average_price, price_high=item.high_price,
        unit=item.unit, source_id=item.price_source_id, source_type=item.source.source_type,
        confidence_score=(item.source.trust_score / Decimal("100")).quantize(Decimal("0.0001")), is_demo=False, price_context="local_scrap")
    session.add(observation); session.flush()
    item.status = "approved"; item.reviewed_at = datetime.now(timezone.utc); item.review_notes = notes; item.approved_price_observation_id = observation.id
    try: session.commit()
    except IntegrityError as exc:
        session.rollback(); raise SubmissionConflict("An equivalent price observation already exists") from exc
    return serialize(price_submission_repository.get(session, item.id))

def reject(session: Session, submission_id: int, notes: str | None):
    item = price_submission_repository.get(session, submission_id, lock=True)
    if not item: raise SubmissionNotFound("Price submission not found")
    if item.status == "rejected": return serialize(item)
    if item.status != "pending": raise SubmissionConflict("Only pending submissions can be rejected")
    item.status = "rejected"; item.reviewed_at = datetime.now(timezone.utc); item.review_notes = notes
    session.commit(); return serialize(price_submission_repository.get(session, item.id))

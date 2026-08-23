from datetime import date
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload
from app.models import PriceSubmission, ScrapPrice

LOAD = (
    joinedload(PriceSubmission.source), joinedload(PriceSubmission.city),
    joinedload(PriceSubmission.material), joinedload(PriceSubmission.material_grade),
)

def get(session: Session, submission_id: int, *, lock: bool = False):
    statement = select(PriceSubmission).options(*LOAD).where(PriceSubmission.id == submission_id)
    if lock:
        statement = statement.with_for_update()
    return session.scalar(statement)

def list_submissions(session: Session, *, status=None, source_id=None, city_id=None, material_id=None, price_date=None, limit=200):
    statement = select(PriceSubmission).options(*LOAD).order_by(PriceSubmission.submitted_at.desc()).limit(limit)
    for field, value in ((PriceSubmission.status, status), (PriceSubmission.price_source_id, source_id), (PriceSubmission.city_id, city_id), (PriceSubmission.material_id, material_id), (PriceSubmission.price_date, price_date)):
        if value is not None:
            statement = statement.where(field == value)
    return list(session.scalars(statement).unique())

def find_pending_duplicate(session: Session, *, source_id: int, city_id: int, material_id: int, grade_id: int | None, price_date: date):
    statement = select(PriceSubmission).where(
        PriceSubmission.status == "pending", PriceSubmission.price_source_id == source_id,
        PriceSubmission.city_id == city_id, PriceSubmission.material_id == material_id,
        PriceSubmission.price_date == price_date,
    )
    statement = statement.where(PriceSubmission.material_grade_id.is_(None) if grade_id is None else PriceSubmission.material_grade_id == grade_id)
    return session.scalar(statement.limit(1))

def add(session: Session, values: dict):
    item = PriceSubmission(**values)
    session.add(item)
    session.commit()
    return get(session, item.id)

def find_observation(session: Session, item: PriceSubmission):
    statement = select(ScrapPrice).where(
        ScrapPrice.source_id == item.price_source_id, ScrapPrice.city_id == item.city_id,
        ScrapPrice.material_id == item.material_id, ScrapPrice.price_date == item.price_date,
    )
    statement = statement.where(ScrapPrice.material_grade_id.is_(None) if item.material_grade_id is None else ScrapPrice.material_grade_id == item.material_grade_id)
    return session.scalar(statement.limit(1))

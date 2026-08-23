from datetime import date

from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.models import ScrapPrice


PRICE_RELATIONSHIPS = (
    joinedload(ScrapPrice.city),
    joinedload(ScrapPrice.material),
    joinedload(ScrapPrice.material_grade),
    joinedload(ScrapPrice.source),
)


def list_prices(
    session: Session,
    *,
    city_id: int | None = None,
    material_id: int | None = None,
    price_date: date | None = None,
    is_demo: bool | None = None,
    limit: int = 100,
) -> list[ScrapPrice]:
    statement = (
        select(ScrapPrice)
        .options(*PRICE_RELATIONSHIPS)
        .order_by(ScrapPrice.price_date.desc(), ScrapPrice.id.desc())
        .where(ScrapPrice.price_context == "local_scrap")
        .limit(limit)
    )
    if city_id is not None:
        statement = statement.where(ScrapPrice.city_id == city_id)
    if material_id is not None:
        statement = statement.where(ScrapPrice.material_id == material_id)
    if price_date is not None:
        statement = statement.where(ScrapPrice.price_date == price_date)
    if is_demo is not None:
        statement = statement.where(ScrapPrice.is_demo.is_(is_demo))
    return list(session.scalars(statement).unique())


def get_price(session: Session, price_id: int) -> ScrapPrice | None:
    return session.scalar(
        select(ScrapPrice)
        .options(*PRICE_RELATIONSHIPS)
        .where(ScrapPrice.id == price_id)
    )


def find_duplicate(
    session: Session,
    *,
    material_id: int,
    grade_id: int | None,
    city_id: int,
    price_date: date,
    source_id: int,
    exclude_id: int | None = None,
) -> ScrapPrice | None:
    statement = select(ScrapPrice).where(
        ScrapPrice.material_id == material_id,
        ScrapPrice.city_id == city_id,
        ScrapPrice.price_date == price_date,
        ScrapPrice.source_id == source_id,
        ScrapPrice.price_context == "local_scrap",
    )
    if grade_id is None:
        statement = statement.where(ScrapPrice.material_grade_id.is_(None))
    else:
        statement = statement.where(ScrapPrice.material_grade_id == grade_id)
    if exclude_id is not None:
        statement = statement.where(ScrapPrice.id != exclude_id)
    return session.scalar(statement.limit(1))


def add_price(session: Session, values: dict) -> ScrapPrice:
    price = ScrapPrice(**values)
    session.add(price)
    session.commit()
    return get_price(session, price.id)


def update_price(session: Session, price: ScrapPrice, values: dict) -> ScrapPrice:
    for field, value in values.items():
        setattr(price, field, value)
    session.commit()
    return get_price(session, price.id)

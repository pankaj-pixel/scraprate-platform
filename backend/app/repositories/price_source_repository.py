from sqlalchemy import func, select
from sqlalchemy.orm import Session, joinedload

from app.models import PriceSource


def list_sources(session: Session, source_type: str | None = None) -> list[PriceSource]:
    statement = (
        select(PriceSource)
        .options(joinedload(PriceSource.city))
        .order_by(PriceSource.is_active.desc(), PriceSource.name)
    )
    if source_type:
        statement = statement.where(PriceSource.source_type == source_type)
    return list(session.scalars(statement).unique())


def get_source(session: Session, source_id: int) -> PriceSource | None:
    return session.scalar(
        select(PriceSource)
        .options(joinedload(PriceSource.city))
        .where(PriceSource.id == source_id)
    )


def get_source_by_slug(
    session: Session, slug: str, exclude_id: int | None = None
) -> PriceSource | None:
    statement = select(PriceSource).where(func.lower(PriceSource.slug) == slug.lower())
    if exclude_id is not None:
        statement = statement.where(PriceSource.id != exclude_id)
    return session.scalar(statement.limit(1))


def create_source(session: Session, values: dict) -> PriceSource:
    source = PriceSource(**values)
    session.add(source)
    session.commit()
    return get_source(session, source.id)


def update_source(session: Session, source: PriceSource, values: dict) -> PriceSource:
    for field, value in values.items():
        setattr(source, field, value)
    session.commit()
    return get_source(session, source.id)

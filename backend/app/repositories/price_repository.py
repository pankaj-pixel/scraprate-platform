from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import ScrapPrice


@dataclass(frozen=True)
class DailyPriceRecord:
    material_id: int
    price_date: date
    low: Decimal
    high: Decimal
    average: Decimal
    unit: str
    is_demo: bool
    last_updated: datetime


def _daily_prices(city_id: int, material_ids: list[int] | None = None):
    statement = (
        select(
            ScrapPrice.material_id.label("material_id"),
            ScrapPrice.price_date.label("price_date"),
            func.min(ScrapPrice.price_low).label("price_low"),
            func.max(ScrapPrice.price_high).label("price_high"),
            func.avg(ScrapPrice.price_average).label("price_average"),
            func.min(ScrapPrice.unit).label("unit"),
            func.min(ScrapPrice.is_demo).label("is_demo"),
            func.max(ScrapPrice.updated_at).label("last_updated"),
        )
        .where(
            ScrapPrice.city_id == city_id,
            ScrapPrice.material_grade_id.is_(None),
            ScrapPrice.price_context == "local_scrap",
        )
        .group_by(ScrapPrice.material_id, ScrapPrice.price_date)
    )
    if material_ids is not None:
        statement = statement.where(ScrapPrice.material_id.in_(material_ids))
    return statement


def _to_record(row) -> DailyPriceRecord:
    return DailyPriceRecord(
        material_id=row.material_id,
        price_date=row.price_date,
        low=Decimal(row.price_low),
        high=Decimal(row.price_high),
        average=Decimal(row.price_average),
        unit=row.unit,
        is_demo=bool(row.is_demo),
        last_updated=row.last_updated,
    )


def get_latest_and_previous_prices(
    session: Session, city_id: int, material_ids: list[int]
) -> dict[int, list[DailyPriceRecord]]:
    """Load the newest two available dates per material in one MySQL 8 query."""
    if not material_ids:
        return {}
    daily = _daily_prices(city_id, material_ids).subquery()
    ranked = select(
        daily,
        func.row_number()
        .over(partition_by=daily.c.material_id, order_by=daily.c.price_date.desc())
        .label("price_position"),
    ).subquery()
    rows = session.execute(
        select(ranked)
        .where(ranked.c.price_position <= 2)
        .order_by(ranked.c.material_id, ranked.c.price_position)
    ).all()
    result: dict[int, list[DailyPriceRecord]] = {}
    for row in rows:
        result.setdefault(row.material_id, []).append(_to_record(row))
    return result


def get_price_history(
    session: Session, material_id: int, city_id: int, days: int
) -> list[DailyPriceRecord]:
    daily = _daily_prices(city_id, [material_id]).subquery()
    recent = (
        select(daily)
        .order_by(daily.c.price_date.desc())
        .limit(days)
        .subquery()
    )
    rows = session.execute(select(recent).order_by(recent.c.price_date.asc())).all()
    return [_to_record(row) for row in rows]


def get_price_histories(
    session: Session, material_ids: list[int], city_id: int, days: int
) -> dict[int, list[DailyPriceRecord]]:
    """Load recent stored history for all homepage materials in one query."""
    if not material_ids:
        return {}
    daily = _daily_prices(city_id, material_ids).subquery()
    ranked = select(
        daily,
        func.row_number()
        .over(partition_by=daily.c.material_id, order_by=daily.c.price_date.desc())
        .label("history_position"),
    ).subquery()
    rows = session.execute(
        select(ranked)
        .where(ranked.c.history_position <= days)
        .order_by(ranked.c.material_id, ranked.c.price_date.asc())
    ).all()
    histories: dict[int, list[DailyPriceRecord]] = {}
    for row in rows:
        histories.setdefault(row.material_id, []).append(_to_record(row))
    return histories

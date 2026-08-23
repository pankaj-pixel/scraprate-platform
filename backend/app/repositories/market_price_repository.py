from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import PriceSource, ScrapPrice


@dataclass(frozen=True)
class SourceObservationRecord:
    low: Decimal
    average: Decimal
    high: Decimal
    unit: str
    trust_score: Decimal
    is_verified: bool
    is_active: bool
    is_demo: bool
    price_date: date
    last_updated: datetime
    source_name: str
    source_type: str
    trust_score_value: Decimal
    raw_reference: str | None
    metadata: dict | None


def get_latest_active_observations(
    session: Session, material_id: int, city_id: int
) -> list[SourceObservationRecord]:
    filters = (
        ScrapPrice.material_id == material_id,
        ScrapPrice.city_id == city_id,
        ScrapPrice.material_grade_id.is_(None),
        PriceSource.is_active.is_(True),
        ScrapPrice.price_context == "local_scrap",
    )
    latest_date = (
        select(func.max(ScrapPrice.price_date))
        .join(PriceSource, ScrapPrice.source_id == PriceSource.id)
        .where(*filters)
        .scalar_subquery()
    )
    rows = session.execute(
        select(
            ScrapPrice.price_low,
            ScrapPrice.price_average,
            ScrapPrice.price_high,
            ScrapPrice.unit,
            PriceSource.trust_score,
            PriceSource.is_verified,
            PriceSource.is_active,
            ScrapPrice.is_demo,
            ScrapPrice.price_date,
            ScrapPrice.updated_at,
            PriceSource.name.label("source_name"),
            PriceSource.source_type.label("source_type"),
            ScrapPrice.raw_reference,
            ScrapPrice.observation_metadata.label("metadata"),
        )
        .join(PriceSource, ScrapPrice.source_id == PriceSource.id)
        .where(*filters, ScrapPrice.price_date == latest_date)
        .order_by(ScrapPrice.id)
    ).all()
    return [
        SourceObservationRecord(
            low=Decimal(row.price_low),
            average=Decimal(row.price_average),
            high=Decimal(row.price_high),
            unit=row.unit,
            trust_score=Decimal(row.trust_score),
            is_verified=bool(row.is_verified),
            is_active=bool(row.is_active),
            is_demo=bool(row.is_demo),
            price_date=row.price_date,
            last_updated=row.updated_at,
            source_name=row.source_name,
            source_type=row.source_type,
            trust_score_value=Decimal(row.trust_score),
            raw_reference=row.raw_reference,
            metadata=row.metadata,
        )
        for row in rows
    ]


def get_latest_two_active_observations(
    session: Session, material_ids: list[int], city_id: int
) -> dict[int, dict[date, list[SourceObservationRecord]]]:
    """Load raw observations for the latest two dates of every material once."""
    if not material_ids:
        return {}
    active_filters = (
        ScrapPrice.material_id.in_(material_ids),
        ScrapPrice.city_id == city_id,
        ScrapPrice.material_grade_id.is_(None),
        PriceSource.is_active.is_(True),
        ScrapPrice.price_context == "local_scrap",
    )
    daily_dates = (
        select(ScrapPrice.material_id, ScrapPrice.price_date)
        .join(PriceSource, ScrapPrice.source_id == PriceSource.id)
        .where(*active_filters)
        .distinct()
        .subquery()
    )
    ranked_dates = select(
        daily_dates,
        func.row_number()
        .over(
            partition_by=daily_dates.c.material_id,
            order_by=daily_dates.c.price_date.desc(),
        )
        .label("date_position"),
    ).subquery()
    selected_dates = (
        select(ranked_dates.c.material_id, ranked_dates.c.price_date)
        .where(ranked_dates.c.date_position <= 2)
        .subquery()
    )
    rows = session.execute(
        select(
            ScrapPrice.material_id,
            ScrapPrice.price_low,
            ScrapPrice.price_average,
            ScrapPrice.price_high,
            ScrapPrice.unit,
            PriceSource.trust_score,
            PriceSource.is_verified,
            PriceSource.is_active,
            ScrapPrice.is_demo,
            ScrapPrice.price_date,
            ScrapPrice.updated_at,
            PriceSource.name.label("source_name"),
            PriceSource.source_type.label("source_type"),
            ScrapPrice.raw_reference,
            ScrapPrice.observation_metadata.label("metadata"),
        )
        .join(PriceSource, ScrapPrice.source_id == PriceSource.id)
        .join(
            selected_dates,
            (selected_dates.c.material_id == ScrapPrice.material_id)
            & (selected_dates.c.price_date == ScrapPrice.price_date),
        )
        .where(*active_filters)
        .order_by(
            ScrapPrice.material_id,
            ScrapPrice.price_date.desc(),
            ScrapPrice.id,
        )
    ).all()
    grouped: dict[int, dict[date, list[SourceObservationRecord]]] = {}
    for row in rows:
        record = SourceObservationRecord(
            low=Decimal(row.price_low),
            average=Decimal(row.price_average),
            high=Decimal(row.price_high),
            unit=row.unit,
            trust_score=Decimal(row.trust_score),
            is_verified=bool(row.is_verified),
            is_active=bool(row.is_active),
            is_demo=bool(row.is_demo),
            price_date=row.price_date,
            last_updated=row.updated_at,
            source_name=row.source_name,
            source_type=row.source_type,
            trust_score_value=Decimal(row.trust_score),
            raw_reference=row.raw_reference,
            metadata=row.metadata,
        )
        grouped.setdefault(row.material_id, {}).setdefault(row.price_date, []).append(record)
    return grouped

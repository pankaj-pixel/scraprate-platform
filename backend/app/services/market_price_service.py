from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal, ROUND_HALF_UP
from statistics import median
from typing import Iterable, Literal, Protocol

from sqlalchemy.orm import Session

from app.models import City, Material
from app.repositories import market_price_repository
from app.repositories import price_repository
from app.config import get_settings

MONEY_PRECISION = Decimal("0.01")
Confidence = Literal["LOW", "MEDIUM", "HIGH"]


class MarketObservation(Protocol):
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


@dataclass(frozen=True)
class IndicativeCalculation:
    indicative_price: Decimal
    low: Decimal
    high: Decimal
    median: Decimal
    weighted_average: Decimal
    source_count: int
    verified_source_count: int
    average_trust_score: Decimal
    confidence: Confidence
    data_type: Literal["demo", "real"]
    unit: str
    price_date: date
    last_updated: datetime
    source_names: tuple[str, ...]
    source_details: tuple[dict, ...]


def freshness(price_date: date, *, today: date | None = None) -> dict:
    settings = get_settings()
    age = max(0, ((today or date.today()) - price_date).days)
    if age <= settings.price_fresh_days:
        status = "FRESH"
    elif age <= settings.price_stale_days:
        status = "STALE"
    else:
        status = "VERY_STALE"
    wording = "Today's rate" if age == 0 else f"Latest available rate — updated {age} day{'s' if age != 1 else ''} ago"
    return {"freshness": status, "age_days": age, "freshness_label": wording}


def _money(value: Decimal) -> Decimal:
    return value.quantize(MONEY_PRECISION, rounding=ROUND_HALF_UP)


def confidence_level(
    source_count: int, verified_source_count: int, average_trust_score: Decimal
) -> Confidence:
    """Classify confidence using transparent source coverage thresholds.

    HIGH: at least 3 sources, 2 verified sources, and average trust >= 60.
    MEDIUM: at least 2 sources and either a verified source or trust >= 50.
    LOW: everything else, including a single source.
    """
    if (
        source_count >= 3
        and verified_source_count >= 2
        and average_trust_score >= Decimal("60")
    ):
        return "HIGH"
    if source_count >= 2 and (
        verified_source_count >= 1 or average_trust_score >= Decimal("50")
    ):
        return "MEDIUM"
    return "LOW"


def calculate_indicative_rate(
    observations: Iterable[MarketObservation],
) -> IndicativeCalculation | None:
    """Calculate an explainable market rate without mutating raw observations.

    Real observations take complete precedence over demo observations. The
    indicative rate is the midpoint of the median and trust-weighted average.
    No outliers are removed in this first implementation.
    """
    # Defense in depth: repository queries already select local_scrap only, but
    # calculations must never mix a benchmark supplied by another caller.
    records = [record for record in observations if record.is_active and getattr(record, "price_context", "local_scrap") == "local_scrap"]
    if not records:
        return None
    real_records = [record for record in records if not record.is_demo]
    selected = real_records or [record for record in records if record.is_demo]
    if not selected:
        return None

    averages = [record.average for record in selected]
    median_price = Decimal(median(averages))
    total_weight = sum((record.trust_score for record in selected), Decimal("0"))
    if total_weight > 0:
        weighted_average = sum(
            (record.average * record.trust_score for record in selected),
            Decimal("0"),
        ) / total_weight
    else:
        weighted_average = sum(averages, Decimal("0")) / Decimal(len(averages))

    source_count = len(selected)
    verified_count = sum(record.is_verified for record in selected)
    average_trust = sum(
        (record.trust_score for record in selected), Decimal("0")
    ) / Decimal(source_count)
    indicative = (median_price + weighted_average) / Decimal("2")
    return IndicativeCalculation(
        indicative_price=_money(indicative),
        low=_money(min(record.low for record in selected)),
        high=_money(max(record.high for record in selected)),
        median=_money(median_price),
        weighted_average=_money(weighted_average),
        source_count=source_count,
        verified_source_count=verified_count,
        average_trust_score=average_trust.quantize(
            MONEY_PRECISION, rounding=ROUND_HALF_UP
        ),
        confidence=confidence_level(source_count, verified_count, average_trust),
        data_type="real" if real_records else "demo",
        unit=selected[0].unit,
        price_date=selected[0].price_date,
        last_updated=max(record.last_updated for record in selected),
        source_names=tuple(sorted({getattr(record, "source_name", "Unknown source") for record in selected})),
        source_details=tuple({
            "name": getattr(record, "source_name", "Unknown source"),
            "source_type": getattr(record, "source_type", "unknown"),
            "trust_score": getattr(record, "trust_score_value", record.trust_score),
            "region": (getattr(record, "metadata", None) or {}).get("region"),
            "collected_at": (getattr(record, "metadata", None) or {}).get("collected_at"),
            "source_url": getattr(record, "raw_reference", None),
        } for record in selected),
    )


def calculate_daily_change(
    current: Decimal, previous: Decimal | None
) -> tuple[Decimal | None, Decimal | None]:
    if previous is None:
        return None, None
    change = current - previous
    percentage = change / previous * Decimal("100") if previous else Decimal("0")
    return _money(change), _money(percentage)


def get_market_price(
    session: Session, material: Material, city: City
) -> dict | None:
    observations = market_price_repository.get_latest_active_observations(
        session, material.id, city.id
    )
    result = calculate_indicative_rate(observations)
    if result is None:
        return None
    return {
        "material": material.name,
        "slug": material.slug,
        "city": city.name,
        "unit": result.unit,
        "indicative_price": result.indicative_price,
        "low": result.low,
        "high": result.high,
        "median": result.median,
        "weighted_average": result.weighted_average,
        "source_count": result.source_count,
        "verified_source_count": result.verified_source_count,
        "confidence": result.confidence,
        "data_type": result.data_type,
        "price_date": result.price_date,
        "last_updated": result.last_updated,
        "source_names": list(result.source_names),
        "source_details": list(result.source_details),
        **freshness(result.price_date),
    }


def get_market_overview(
    session: Session, materials: list[Material], city: City, history_days: int = 30
) -> dict:
    """Build the homepage market data with fixed-size batched query counts."""
    material_ids = [material.id for material in materials]
    observations = market_price_repository.get_latest_two_active_observations(
        session, material_ids, city.id
    )
    histories = price_repository.get_price_histories(
        session, material_ids, city.id, history_days
    )
    items = []
    for material in materials:
        dates = observations.get(material.id, {})
        ordered_dates = sorted(dates, reverse=True)
        current = calculate_indicative_rate(dates[ordered_dates[0]]) if ordered_dates else None
        previous = (
            calculate_indicative_rate(dates[ordered_dates[1]])
            if len(ordered_dates) > 1
            else None
        )
        if current is None:
            continue
        change, change_percent = calculate_daily_change(
            current.indicative_price,
            previous.indicative_price if previous else None,
        )
        items.append(
            {
                "material": material.name,
                "slug": material.slug,
                "category": material.category.name,
                "city": city.name,
                "unit": current.unit,
                "indicative_price": current.indicative_price,
                "low": current.low,
                "high": current.high,
                "median": current.median,
                "previous_indicative_price": (
                    previous.indicative_price if previous else None
                ),
                "change": change,
                "change_percent": change_percent,
                "source_count": current.source_count,
                "verified_source_count": current.verified_source_count,
                "confidence": current.confidence,
                "data_type": current.data_type,
                "price_date": current.price_date,
                "last_updated": current.last_updated,
                "source_names": list(current.source_names),
                "source_details": list(current.source_details),
                **freshness(current.price_date),
                "description": material.description,
                "icon": material.icon,
                "image_reference": material.image_reference,
                "aliases": material.aliases or [],
                "history": [
                    {"date": point.price_date, "price": _money(point.average)}
                    for point in histories.get(material.id, [])
                ],
            }
        )
    data_types = {item["data_type"] for item in items}
    mode = "mixed" if len(data_types) > 1 else next(iter(data_types), "demo")
    return {
        "city": city.name,
        "tracked_materials": len(items),
        "data_type": mode,
        "updated_at": max(
            (item["last_updated"] for item in items), default=None
        ),
        "materials": items,
    }

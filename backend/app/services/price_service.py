from datetime import date
from decimal import Decimal, ROUND_HALF_UP

from sqlalchemy.orm import Session

from app.models import City, Material
from app.repositories import price_repository
from app.services import market_price_service

MONEY_PRECISION = Decimal("0.01")


def _money(value: Decimal) -> Decimal:
    return value.quantize(MONEY_PRECISION, rounding=ROUND_HALF_UP)


def _percent(value: Decimal) -> Decimal:
    return value.quantize(MONEY_PRECISION, rounding=ROUND_HALF_UP)


def _snapshot(material: Material, city: City, records) -> dict | None:
    if not records:
        return None
    current = records[0]
    previous = records[1] if len(records) > 1 else current
    change = current.average - previous.average
    change_percent = (
        change / previous.average * Decimal("100")
        if previous.average
        else Decimal("0")
    )
    return {
        "material": material.name,
        "slug": material.slug,
        "category": material.category.name,
        "city": city.name,
        "unit": current.unit,
        "price": _money(current.average),
        "low": _money(current.low),
        "high": _money(current.high),
        "previous_price": _money(previous.average),
        "change": _money(change),
        "change_percent": _percent(change_percent),
        "last_updated": current.last_updated,
        "price_date": current.price_date,
        "is_demo": current.is_demo,
        "description": material.description,
        "icon": material.icon,
    }


def get_current_prices(
    session: Session, city: City, materials: list[Material]
) -> list[dict]:
    records_by_material = price_repository.get_latest_and_previous_prices(
        session, city.id, [material.id for material in materials]
    )
    snapshots = [
        _snapshot(material, city, records_by_material.get(material.id, []))
        for material in materials
    ]
    return [snapshot for snapshot in snapshots if snapshot is not None]


def get_current_price(
    session: Session, city: City, material: Material
) -> dict | None:
    prices = get_current_prices(session, city, [material])
    return prices[0] if prices else None


def get_history(
    session: Session, city: City, material: Material, days: int
) -> list[dict]:
    records = price_repository.get_price_history(session, material.id, city.id, days)
    return [
        {
            "date": record.price_date,
            "price": _money(record.average),
            "low": _money(record.low),
            "high": _money(record.high),
            "is_demo": record.is_demo,
        }
        for record in records
    ]


def _period_change(history: list[dict], days: int):
    if not history:
        return None
    current = history[-1]
    cutoff = current["date"].toordinal() - (days - 1)
    eligible = [point for point in history if point["date"].toordinal() >= cutoff]
    if len(eligible) < 2:
        return None
    previous = eligible[0]["price"]
    change = current["price"] - previous
    percent = change / previous * Decimal("100") if previous else Decimal("0")
    return {"change": _money(change), "change_percent": _percent(percent), "from_date": eligible[0]["date"]}


def get_public_detail(session: Session, city: City, material: Material) -> dict | None:
    market = market_price_service.get_market_price(session, material, city)
    if market is None:
        return None
    history = get_history(session, city, material, 365)
    prices = [point["price"] for point in history]
    return {
        **market,
        "category": material.category.name,
        "description": material.description,
        "seo_title": material.seo_title,
        "seo_description": material.seo_description,
        "image_reference": material.image_reference,
        "aliases": material.aliases or [],
        "history": history,
        "statistics": {
            "today": market["indicative_price"],
            "previous": history[-2]["price"] if len(history) > 1 else None,
            "daily": _period_change(history, 2),
            "seven_day": _period_change(history, 7),
            "thirty_day": _period_change(history, 30),
            "period_high": max(prices) if prices else None,
            "period_low": min(prices) if prices else None,
            "average": _money(sum(prices, Decimal("0")) / Decimal(len(prices))) if prices else None,
            "available_observations": len(history),
            "first_observation_date": history[0]["date"] if history else None,
        },
    }


def get_market_overview(snapshots: list[dict], city: City) -> dict:
    gainers = sorted(
        snapshots, key=lambda item: item["change_percent"], reverse=True
    )[:3]
    losers = sorted(snapshots, key=lambda item: item["change_percent"])[:3]
    latest = max(
        (item["price_date"] for item in snapshots), default=None
    )
    return {
        "city": city.name,
        "tracked_materials": len(snapshots),
        "gainers": gainers,
        "losers": losers,
        "updated_at": latest or date.today(),
    }

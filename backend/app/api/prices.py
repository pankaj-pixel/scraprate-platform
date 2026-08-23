from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.api.dependencies import require_city, require_material
from app.database import get_db
from app.schemas import (
    CityName,
    MaterialHistory,
    MaterialSummary,
    IndicativeMarketPriceResponse,
    PriceHistoryResponse,
    PriceResponse,
)
from app.services import market_price_service, material_service, price_service

router = APIRouter(prefix="/api/v1/prices", tags=["prices"])
legacy_router = APIRouter(prefix="/api/materials", tags=["prices"])


def _legacy_summary(snapshot: dict) -> dict:
    return {
        "slug": snapshot["slug"],
        "name": snapshot["material"],
        "category": snapshot["category"],
        "unit": snapshot["unit"],
        "city": snapshot["city"],
        "price": snapshot["price"],
        "low": snapshot["low"],
        "high": snapshot["high"],
        "previous_price": snapshot["previous_price"],
        "change": snapshot["change"],
        "change_pct": snapshot["change_percent"],
        "description": snapshot["description"],
        "icon": snapshot["icon"],
    }


@router.get("/today", response_model=list[PriceResponse])
def prices_today(
    city: str = Query("delhi", min_length=1, max_length=80),
    category: str | None = None,
    search: str | None = Query(None, max_length=100),
    session: Session = Depends(get_db),
):
    city_record = require_city(session, city)
    materials = material_service.get_materials(session, category, search)
    return price_service.get_current_prices(session, city_record, materials)


@router.get("/{material_slug}/history", response_model=PriceHistoryResponse)
def price_history(
    material_slug: str,
    city: str = Query("delhi", min_length=1, max_length=80),
    days: int = Query(30, ge=1, le=365),
    session: Session = Depends(get_db),
):
    material = require_material(session, material_slug)
    city_record = require_city(session, city)
    history = price_service.get_history(session, city_record, material, days)
    if not history:
        raise HTTPException(status_code=404, detail="Price data not found")
    return {
        "material": material.name,
        "slug": material.slug,
        "category": material.category.name,
        "city": city_record.name,
        "unit": material.unit,
        "days": days,
        "history": history,
    }


@router.get("/{material_slug}/market", response_model=IndicativeMarketPriceResponse)
def indicative_market_price(
    material_slug: str,
    city: str = Query("delhi", min_length=1, max_length=80),
    session: Session = Depends(get_db),
):
    material = require_material(session, material_slug)
    result = market_price_service.get_market_price(
        session, material, require_city(session, city)
    )
    if result is None:
        raise HTTPException(status_code=404, detail="No active price observations found")
    return result


@router.get("/{material_slug}/detail")
def public_material_price_detail(
    material_slug: str,
    city: str = Query("delhi", min_length=1, max_length=80),
    session: Session = Depends(get_db),
):
    material = require_material(session, material_slug)
    city_record = require_city(session, city)
    result = price_service.get_public_detail(session, city_record, material)
    if result is None:
        raise HTTPException(status_code=404, detail="Price data not found")
    return result


@router.get("/{material_slug}", response_model=PriceResponse)
def current_price(
    material_slug: str,
    city: str = Query("delhi", min_length=1, max_length=80),
    session: Session = Depends(get_db),
):
    material = require_material(session, material_slug)
    snapshot = price_service.get_current_price(
        session, require_city(session, city), material
    )
    if snapshot is None:
        raise HTTPException(status_code=404, detail="Price data not found")
    return snapshot


@legacy_router.get("", response_model=list[MaterialSummary])
def legacy_materials(
    city: CityName = Query("Delhi"),
    category: str | None = None,
    search: str | None = Query(None, max_length=100),
    session: Session = Depends(get_db),
):
    city_record = require_city(session, city)
    materials = material_service.get_materials(session, category, search)
    return [
        _legacy_summary(snapshot)
        for snapshot in price_service.get_current_prices(
            session, city_record, materials
        )
    ]


@legacy_router.get("/{slug}/history", response_model=MaterialHistory)
def legacy_material_history(
    slug: str,
    city: CityName = Query("Delhi"),
    days: int = Query(30, ge=7, le=365),
    session: Session = Depends(get_db),
):
    material = require_material(session, slug)
    city_record = require_city(session, city)
    history = price_service.get_history(session, city_record, material, days)
    return {
        "slug": material.slug,
        "city": city_record.name,
        "unit": material.unit,
        "history": [
            {"date": point["date"], "price": point["price"]}
            for point in history
        ],
    }


@legacy_router.get("/{slug}")
def legacy_material_detail(
    slug: str,
    city: CityName = Query("Delhi"),
    session: Session = Depends(get_db),
):
    material = require_material(session, slug)
    snapshot = price_service.get_current_price(
        session, require_city(session, city), material
    )
    if snapshot is None:
        raise HTTPException(status_code=404, detail="Price data not found")
    return {
        **_legacy_summary(snapshot),
        "market_note": "Indicative market rate. Actual buying price varies by grade, quantity, contamination, pickup cost and buyer.",
        "variants": [
            {"name": grade.name, "factor": float(grade.price_multiplier)}
            for grade in material_service.get_active_grades(material)
        ],
    }

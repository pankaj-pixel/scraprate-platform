from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas import (
    AdminPriceCreate,
    AdminPriceOptionsResponse,
    AdminPriceResponse,
    AdminPriceUpdate,
)
from app.services import admin_price_service, material_service

# TODO(security): These internal routes MUST require authentication and
# authorization before they are exposed in a production environment.
router = APIRouter(prefix="/api/v1/admin/prices", tags=["admin-prices"])


def _translate_admin_error(error: admin_price_service.AdminPriceError):
    if isinstance(error, admin_price_service.AdminConflictError):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(error))
    if isinstance(error, admin_price_service.AdminNotFoundError):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(error))
    raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(error))


@router.get("/options", response_model=AdminPriceOptionsResponse)
def price_options(session: Session = Depends(get_db)):
    materials = material_service.get_materials(session)
    return {
        "cities": [
            {"slug": city.slug, "name": city.name}
            for city in material_service.get_cities(session)
        ],
        "materials": [
            {
                "slug": material.slug,
                "name": material.name,
                "unit": material.unit,
                "grades": [
                    {"slug": grade.slug, "name": grade.name}
                    for grade in material_service.get_active_grades(material)
                ],
            }
            for material in materials
        ],
        "sources": [
            {
                "slug": source.slug,
                "name": source.name,
                "source_type": source.source_type,
            }
            for source in material_service.get_price_sources(session)
        ],
    }


@router.get("", response_model=list[AdminPriceResponse])
def recent_prices(
    city: str | None = Query(None, max_length=80),
    material: str | None = Query(None, max_length=100),
    price_date: date | None = Query(None, alias="date"),
    is_demo: bool | None = None,
    limit: int = Query(100, ge=1, le=500),
    session: Session = Depends(get_db),
):
    try:
        return admin_price_service.list_prices(
            session,
            city_slug=city,
            material_slug=material,
            price_date=price_date,
            is_demo=is_demo,
            limit=limit,
        )
    except admin_price_service.AdminPriceError as error:
        _translate_admin_error(error)


@router.post("", response_model=AdminPriceResponse, status_code=status.HTTP_201_CREATED)
def create_price(payload: AdminPriceCreate, session: Session = Depends(get_db)):
    try:
        return admin_price_service.create_price(session, payload)
    except admin_price_service.AdminPriceError as error:
        _translate_admin_error(error)


@router.put("/{price_id}", response_model=AdminPriceResponse)
def replace_price(
    price_id: int, payload: AdminPriceCreate, session: Session = Depends(get_db)
):
    try:
        return admin_price_service.update_price(
            session, price_id, payload, partial=False
        )
    except admin_price_service.AdminPriceError as error:
        _translate_admin_error(error)


@router.patch("/{price_id}", response_model=AdminPriceResponse)
def edit_price(
    price_id: int, payload: AdminPriceUpdate, session: Session = Depends(get_db)
):
    try:
        return admin_price_service.update_price(
            session, price_id, payload, partial=True
        )
    except admin_price_service.AdminPriceError as error:
        _translate_admin_error(error)

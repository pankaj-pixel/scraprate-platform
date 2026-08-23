from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.dependencies import require_material
from app.database import get_db
from app.schemas import MaterialDetailResponse, MaterialResponse
from app.services import material_service

router = APIRouter(prefix="/api/v1/materials", tags=["materials"])


def _material_response(material):
    return {
        "slug": material.slug,
        "name": material.name,
        "category": material.category.name,
        "unit": material.unit,
        "description": material.description,
        "icon": material.icon,
        "seo_title": material.seo_title,
        "seo_description": material.seo_description,
        "display_order": material.display_order,
        "image_reference": material.image_reference,
        "aliases": material.aliases or [],
    }


@router.get("", response_model=list[MaterialResponse])
def materials(
    category: str | None = None,
    search: str | None = Query(None, max_length=100),
    session: Session = Depends(get_db),
):
    records = material_service.get_materials(session, category, search)
    return [_material_response(material) for material in records]


@router.get("/{slug}", response_model=MaterialDetailResponse)
def material_detail(slug: str, session: Session = Depends(get_db)):
    material = require_material(session, slug)
    return {
        **_material_response(material),
        "grades": [
            {
                "slug": grade.slug,
                "name": grade.name,
                "description": grade.description,
                "price_multiplier": grade.price_multiplier,
            }
            for grade in material_service.get_active_grades(material)
        ],
    }

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models import City, Material
from app.services import material_service


def require_city(session: Session, identifier: str) -> City:
    city = material_service.find_city(session, identifier)
    if city is None:
        raise HTTPException(status_code=404, detail="City not found")
    return city


def require_material(session: Session, slug: str) -> Material:
    material = material_service.find_material(session, slug)
    if material is None:
        raise HTTPException(status_code=404, detail="Material not found")
    return material

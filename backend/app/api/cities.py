from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas import CitiesResponse
from app.services import material_service

router = APIRouter(prefix="/api/v1", tags=["cities"])
legacy_router = APIRouter(prefix="/api", tags=["cities"])


@router.get("/cities", response_model=CitiesResponse)
def cities(session: Session = Depends(get_db)):
    return {
        "cities": [
            {"slug": city.slug, "name": city.name}
            for city in material_service.get_cities(session)
        ]
    }


@legacy_router.get("/cities")
def legacy_cities(session: Session = Depends(get_db)):
    return {"cities": [city.name for city in material_service.get_cities(session)]}

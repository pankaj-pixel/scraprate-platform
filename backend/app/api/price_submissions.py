from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.schemas import AdminPriceOptionsResponse, PriceSubmissionCreate, PriceSubmissionResponse
from app.services import material_service, price_submission_service

router = APIRouter(prefix="/api/v1/price-submissions", tags=["price-submissions"])

def translate(error):
    code = status.HTTP_409_CONFLICT if isinstance(error, price_submission_service.SubmissionConflict) else status.HTTP_422_UNPROCESSABLE_ENTITY
    raise HTTPException(status_code=code, detail=str(error))

@router.get("/options", response_model=AdminPriceOptionsResponse)
def options(session: Session = Depends(get_db)):
    # TODO(production-auth): return only sources owned by the authenticated submitter.
    cities = material_service.get_cities(session)
    materials = material_service.get_materials(session)
    sources = [s for s in material_service.get_price_sources(session) if s.is_active and s.source_type in {"dealer", "recycler"}]
    return {"cities": [{"slug": x.slug, "name": x.name} for x in cities],
        "materials": [{"slug": x.slug, "name": x.name, "unit": x.unit, "grades": [{"slug": g.slug, "name": g.name} for g in material_service.get_active_grades(x)]} for x in materials],
        "sources": [{"slug": x.slug, "name": x.name, "source_type": x.source_type} for x in sources]}

@router.post("", response_model=PriceSubmissionResponse, status_code=status.HTTP_201_CREATED)
def submit(payload: PriceSubmissionCreate, session: Session = Depends(get_db)):
    # TODO(production-auth): require authenticated ownership of payload.source.
    try: return price_submission_service.create(session, payload)
    except price_submission_service.SubmissionError as error: translate(error)

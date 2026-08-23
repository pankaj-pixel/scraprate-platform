from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas import (
    PriceSourceCreate,
    PriceSourceResponse,
    PriceSourceType,
    PriceSourceUpdate,
)
from app.services import price_source_service

# TODO(security): Protect all /api/v1/admin routes with authentication and
# authorization before production deployment.
router = APIRouter(prefix="/api/v1/admin/price-sources", tags=["admin-price-sources"])


def _translate(error: price_source_service.PriceSourceError):
    if isinstance(error, price_source_service.PriceSourceConflictError):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(error))
    if isinstance(error, price_source_service.PriceSourceNotFoundError):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(error))
    raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(error))


@router.get("", response_model=list[PriceSourceResponse])
def price_sources(
    source_type: PriceSourceType | None = Query(None),
    session: Session = Depends(get_db),
):
    return price_source_service.list_sources(session, source_type)


@router.post(
    "", response_model=PriceSourceResponse, status_code=status.HTTP_201_CREATED
)
def create_price_source(
    payload: PriceSourceCreate, session: Session = Depends(get_db)
):
    try:
        return price_source_service.create_source(session, payload)
    except price_source_service.PriceSourceError as error:
        _translate(error)


@router.patch("/{source_id}", response_model=PriceSourceResponse)
def edit_price_source(
    source_id: int,
    payload: PriceSourceUpdate,
    session: Session = Depends(get_db),
):
    try:
        return price_source_service.update_source(session, source_id, payload)
    except price_source_service.PriceSourceError as error:
        _translate(error)

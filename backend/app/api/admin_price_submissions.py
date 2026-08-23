from datetime import date
from typing import Literal
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.schemas import PriceSubmissionResponse, PriceSubmissionReview
from app.services import price_submission_service

router = APIRouter(prefix="/api/v1/admin/price-submissions", tags=["admin-price-submissions"])

def translate(error):
    if isinstance(error, price_submission_service.SubmissionNotFound): code = status.HTTP_404_NOT_FOUND
    elif isinstance(error, price_submission_service.SubmissionConflict): code = status.HTTP_409_CONFLICT
    else: code = status.HTTP_422_UNPROCESSABLE_ENTITY
    raise HTTPException(status_code=code, detail=str(error))

@router.get("", response_model=list[PriceSubmissionResponse])
def list_submissions(state: Literal["pending", "approved", "rejected"] | None = Query(None, alias="status"), source: str | None = None, city: str | None = None, material: str | None = None, date: date | None = None, limit: int = Query(200, ge=1, le=500), session: Session = Depends(get_db)):
    # TODO(production-auth): protect all admin review routes and record reviewer identity.
    try: return price_submission_service.list_items(session, status=state, source=source, city=city, material=material, price_date=date, limit=limit)
    except price_submission_service.SubmissionError as error: translate(error)

@router.post("/{submission_id}/approve", response_model=PriceSubmissionResponse)
def approve(submission_id: int, payload: PriceSubmissionReview, session: Session = Depends(get_db)):
    try: return price_submission_service.approve(session, submission_id, payload.notes)
    except price_submission_service.SubmissionError as error: translate(error)

@router.post("/{submission_id}/reject", response_model=PriceSubmissionResponse)
def reject(submission_id: int, payload: PriceSubmissionReview, session: Session = Depends(get_db)):
    try: return price_submission_service.reject(session, submission_id, payload.notes)
    except price_submission_service.SubmissionError as error: translate(error)

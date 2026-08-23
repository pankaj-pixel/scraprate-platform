from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.ingestion import csv_import, service
from app.schemas import (
    PriceImportCommitRequest,
    PriceImportCommitResponse,
    PriceImportPreviewResponse,
)

# TODO(security): Price imports MUST require admin authentication and an audit
# trail before this internal route is exposed in production.
router = APIRouter(prefix="/api/v1/admin/prices/import", tags=["admin-price-imports"])


@router.post("/preview", response_model=PriceImportPreviewResponse)
async def preview_price_import(
    file: UploadFile = File(...), session: Session = Depends(get_db)
):
    if not file.filename or not file.filename.lower().endswith(".csv"):
        raise HTTPException(status_code=422, detail="Upload must be a .csv file")
    content = await file.read(csv_import.MAX_CSV_BYTES + 1)
    try:
        return service.preview_csv(session, content)
    except csv_import.CsvImportError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error


@router.post("/commit", response_model=PriceImportCommitResponse)
def commit_price_import(
    payload: PriceImportCommitRequest, session: Session = Depends(get_db)
):
    try:
        return service.commit_rows(session, payload.rows)
    except service.IngestionConflictError as error:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail=str(error)
        ) from error

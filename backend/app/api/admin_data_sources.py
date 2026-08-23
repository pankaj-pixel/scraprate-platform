from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.schemas import DataSourceHealthResponse, IngestionRunResponse
from app.services import data_source_service

# TODO(production-auth): Require administrator authorization and audit the
# operator who triggers source runs before production.
router = APIRouter(prefix="/api/v1/admin/data-sources", tags=["admin-data-sources"])

@router.get("", response_model=list[DataSourceHealthResponse])
def sources(session: Session = Depends(get_db)):
    return data_source_service.list_sources(session)

@router.post("/{source_id}/run", response_model=IngestionRunResponse)
def run(source_id: int, session: Session = Depends(get_db)):
    try: return data_source_service.run_source(session, source_id)
    except data_source_service.DataSourceNotFound as error: raise HTTPException(status_code=404, detail=str(error))
    except (data_source_service.AdapterUnsupported, data_source_service.DataSourceDisabled) as error: raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(error))
    except data_source_service.DataSourceError as error: raise HTTPException(status_code=502, detail=str(error))

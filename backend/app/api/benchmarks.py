from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.schemas import BenchmarkResponse
from app.services import benchmark_service

router=APIRouter(prefix="/api/v1/benchmarks",tags=["benchmarks"])

@router.get("/{material_slug}",response_model=BenchmarkResponse)
def benchmark(material_slug: str, session: Session=Depends(get_db)):
    try:return benchmark_service.get_benchmark(session,material_slug)
    except benchmark_service.BenchmarkNotFound as error:raise HTTPException(status_code=404,detail=str(error))

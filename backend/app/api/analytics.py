import hmac
from fastapi import APIRouter, Depends, Header, HTTPException, Request, Response, status
from sqlalchemy.orm import Session
from app.config import get_settings
from app.database import get_db
from app.schemas import AnalyticsSummaryResponse, VisitorEventCreate
from app.services import analytics_service

public_router=APIRouter(prefix="/api/v1/analytics",tags=["analytics"])
admin_router=APIRouter(prefix="/api/v1/admin/analytics",tags=["admin-analytics"])

def require_admin_key(x_admin_key: str | None=Header(None)):
    expected=get_settings().admin_api_key
    if not expected or not x_admin_key or not hmac.compare_digest(expected,x_admin_key):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,detail="Valid administrator key required")

@public_router.post("/events",status_code=204)
def event(payload: VisitorEventCreate, request: Request, session: Session=Depends(get_db)):
    analytics_service.record(session,payload,request.headers.get("user-agent", "")); return Response(status_code=204)

@admin_router.get("/summary",response_model=AnalyticsSummaryResponse,dependencies=[Depends(require_admin_key)])
def summary(days: int=30,session: Session=Depends(get_db)):
    if days not in {7,30,90}: raise HTTPException(status_code=422,detail="days must be 7, 30, or 90")
    return analytics_service.get_summary(session,days)

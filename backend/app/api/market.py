from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.dependencies import require_city
from app.api.prices import _legacy_summary
from app.database import get_db
from app.schemas import CityName, HomepageMarketOverviewResponse
from app.services import market_price_service, material_service, price_service

router = APIRouter(prefix="/api/v1/market", tags=["market"])
legacy_router = APIRouter(prefix="/api", tags=["market"])


def _legacy_overview(session: Session, city_identifier: str):
    city = require_city(session, city_identifier)
    materials = material_service.get_materials(session)
    snapshots = price_service.get_current_prices(session, city, materials)
    return price_service.get_market_overview(snapshots, city)


@router.get("/overview", response_model=HomepageMarketOverviewResponse)
def market_overview(
    city: str = Query("delhi", min_length=1, max_length=80),
    session: Session = Depends(get_db),
):
    city_record = require_city(session, city)
    materials = material_service.get_materials(session)
    return market_price_service.get_market_overview(
        session, materials, city_record
    )


@legacy_router.get("/market-overview")
def legacy_market_overview(
    city: CityName = Query("Delhi"), session: Session = Depends(get_db)
):
    overview = _legacy_overview(session, city)
    return {
        **overview,
        "gainers": [_legacy_summary(item) for item in overview["gainers"]],
        "losers": [_legacy_summary(item) for item in overview["losers"]],
    }

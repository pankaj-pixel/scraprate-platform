import logging

from fastapi import Depends, FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.api import (
    admin_price_imports,
    admin_price_sources,
    admin_prices,
    admin_price_submissions,
    admin_data_sources,
    benchmarks,
    price_submissions,
    cities,
    market,
    materials,
    prices,
    seo,
)
from app.config import get_settings
from app.database import get_db


logger = logging.getLogger(__name__)
settings = get_settings()
app = FastAPI(title="ScrapRate API", version="0.4.0", docs_url=None if settings.environment == "production" else "/docs", redoc_url=None if settings.environment == "production" else "/redoc")
app.add_middleware(TrustedHostMiddleware, allowed_hosts=settings.trusted_hosts + (["testserver"] if settings.environment != "production" else []))
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(cities.router)
app.include_router(cities.legacy_router)
app.include_router(materials.router)
app.include_router(prices.router)
app.include_router(prices.legacy_router)
app.include_router(market.router)
app.include_router(market.legacy_router)
app.include_router(admin_prices.router)
app.include_router(admin_price_sources.router)
app.include_router(admin_price_imports.router)
app.include_router(price_submissions.router)
app.include_router(admin_price_submissions.router)
app.include_router(admin_data_sources.router)
app.include_router(benchmarks.router)
app.include_router(seo.router)


@app.exception_handler(SQLAlchemyError)
async def database_error_handler(request: Request, exc: SQLAlchemyError):
    logger.exception("Database error while handling %s", request.url.path)
    return JSONResponse(
        status_code=503,
        content={"detail": "Database temporarily unavailable"},
    )


@app.get("/api/health")
def health(session: Session = Depends(get_db)):
    session.execute(text("SELECT 1"))
    return {"status": "ok", "database": "ok"}

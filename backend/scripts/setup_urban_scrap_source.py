"""Idempotently create the Urban Scrap Delhi NCR dealer source.

Run explicitly from backend/. This is never called by seed or application startup.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sqlalchemy import select

from app.database import SessionLocal
from app.models import City, PriceSource, SourceAdapterConfig

with SessionLocal() as session:
    city = session.scalar(select(City).where(City.slug == "delhi"))
    if city is None:
        raise RuntimeError("The existing default Delhi city record is required")
    source = session.scalar(select(PriceSource).where(PriceSource.slug == "urban-scrap"))
    if source is None:
        source = PriceSource(
            name="Urban Scrap",
            slug="urban-scrap",
            source_type="dealer",
            city_id=city.id,
            trust_score=50,
            is_verified=False,
            is_active=True,
            website_url="https://urbanscrap.co/scrap-rates/",
            notes=(
                "Urban Scrap's own published Delhi NCR buying rates. Not an official "
                "Delhi market price. Stored once against the default Delhi market."
            ),
        )
        session.add(source)
        session.flush()
    elif source.source_type != "dealer" or source.city_id != city.id:
        raise RuntimeError("Existing urban-scrap source has incompatible type or geography")
    config = session.scalar(
        select(SourceAdapterConfig).where(SourceAdapterConfig.source_id == source.id)
    )
    if config is None:
        config = SourceAdapterConfig(
            source_id=source.id,
            adapter_name="urban_scrap",
            enabled=False,
            polling_frequency="daily manual run for MVP",
            endpoint_config_reference="https://urbanscrap.co/scrap-rates/",
        )
        session.add(config)
    elif config.adapter_name != "urban_scrap":
        raise RuntimeError("Existing Urban Scrap source uses a different adapter")
    session.commit()
    print(
        f"Urban Scrap source ready: id={source.id}, adapter config id={config.id}, "
        "enabled=false. Review a live preview before explicitly enabling it."
    )

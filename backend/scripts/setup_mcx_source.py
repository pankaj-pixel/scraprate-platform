"""Explicitly create the MCX benchmark source/config. Run from backend/.

This is intentionally not part of seed or application startup.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sqlalchemy import select
from app.database import SessionLocal
from app.models import PriceSource, SourceAdapterConfig

with SessionLocal() as session:
    source=session.scalar(select(PriceSource).where(PriceSource.slug=="mcx-bhavcopy"))
    if source is None:
        source=PriceSource(name="MCX Official Bhavcopy",slug="mcx-bhavcopy",source_type="market_reference",city_id=None,
            trust_score=85,is_verified=True,is_active=True,website_url="https://www.mcxindia.com/market-data/bhavcopy",
            notes="Official MCX contract-level EOD benchmark; not a local scrap quote.")
        session.add(source); session.flush()
    if source.source_type != "market_reference" or source.city_id is not None:
        raise RuntimeError("Existing mcx-bhavcopy source is not a national market_reference source")
    config=session.scalar(select(SourceAdapterConfig).where(SourceAdapterConfig.source_id==source.id))
    if config is None:
        session.add(SourceAdapterConfig(source_id=source.id,adapter_name="mcx_bhavcopy",enabled=False,polling_frequency="daily after official EOD publication",endpoint_config_reference="MCX_BHAVCOPY_URL"))
    session.commit()
    print(f"MCX source ready: id={source.id}. Configure MCX_BHAVCOPY_URL, verify the official file, then explicitly enable adapter config id={config.id if config else 'new'}.")

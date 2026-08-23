from app.ingestion.adapters.base import PriceSourceAdapter, AdapterObservation
from app.ingestion.adapters.registry import adapter_registry
from app.ingestion.adapters.mcx import McxBhavcopyAdapter
from app.ingestion.adapters.urban_scrap import UrbanScrapAdapter

adapter_registry.register("mcx_bhavcopy", McxBhavcopyAdapter)
adapter_registry.register("urban_scrap", UrbanScrapAdapter)

__all__ = ["PriceSourceAdapter", "AdapterObservation", "adapter_registry", "McxBhavcopyAdapter", "UrbanScrapAdapter"]

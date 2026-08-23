from collections.abc import Callable
from app.ingestion.adapters.base import PriceSourceAdapter

class AdapterRegistry:
    def __init__(self): self._factories: dict[str, Callable[[], PriceSourceAdapter]] = {}
    def register(self, name: str, factory: Callable[[], PriceSourceAdapter]) -> None:
        key = name.strip().lower()
        if not key: raise ValueError("Adapter name is required")
        self._factories[key] = factory
    def unregister(self, name: str) -> None: self._factories.pop(name.strip().lower(), None)
    def create(self, name: str) -> PriceSourceAdapter | None:
        factory = self._factories.get(name.strip().lower())
        return factory() if factory else None
    def names(self) -> tuple[str, ...]: return tuple(sorted(self._factories))

# Production registry intentionally starts empty. Real adapters must be explicitly
# registered by deployment code; test adapters live only under tests/.
adapter_registry = AdapterRegistry()

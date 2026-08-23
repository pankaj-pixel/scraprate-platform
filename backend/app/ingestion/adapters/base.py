from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal
from typing import Any

@dataclass(frozen=True)
class AdapterObservation:
    source: str
    material: str
    city: str | None
    date: date
    low_price: Decimal
    average_price: Decimal
    high_price: Decimal
    unit: str
    grade: str | None = None
    raw_reference: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
    price_context: str = "local_scrap"

class PriceSourceAdapter(ABC):
    """Transport-neutral adapter. It returns data; it never receives a DB session."""
    @property
    @abstractmethod
    def source_identifier(self) -> str: ...

    @abstractmethod
    def fetch(self) -> Any: ...

    @abstractmethod
    def parse(self, raw: Any) -> list[Any]: ...

    @abstractmethod
    def normalize(self, rows: list[Any]) -> list[AdapterObservation]: ...

    def validate(self, observation: AdapterObservation) -> list[str]:
        errors = []
        if min(observation.low_price, observation.average_price, observation.high_price) <= 0: errors.append("Prices must be positive")
        if not observation.low_price <= observation.average_price <= observation.high_price: errors.append("low_price must be <= average_price <= high_price")
        if not observation.unit.strip(): errors.append("Unit is required")
        return errors

    def collect(self) -> list[AdapterObservation]:
        return self.normalize(self.parse(self.fetch()))

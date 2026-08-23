import re
from dataclasses import dataclass
from datetime import date, datetime, timezone
from decimal import Decimal, InvalidOperation
from html.parser import HTMLParser
from urllib.parse import urlparse
from urllib.request import Request, urlopen

from app.config import get_settings
from app.ingestion.adapters.base import AdapterObservation, PriceSourceAdapter

URBAN_SCRAP_URL = "https://urbanscrap.co/scrap-rates/"
URBAN_SCRAP_SOURCE_SLUG = "urban-scrap"
MATERIAL_MAP = {
    "iron": "iron",
    "light iron": "light-iron",
    "steel": "steel",
    "aluminium": "aluminium",
    "brass": "brass",
    "copper": "copper",
    "tin light iron": "tin-light-iron",
    "newspaper": "newspaper",
    "old books": "old-books",
    "cardboard": "cardboard",
    "magazine": "magazine",
    "office paper": "office-paper",
    "plastic": "plastic",
    "iron cooler": "iron-cooler",
    "plastic cooler": "plastic-cooler",
    "white battery": "white-battery",
    "black battery": "black-battery",
    "invertor": "inverter-scrap",
    "motor copper wiring": "motor-copper-wiring",
    "stabilizer copper": "stabilizer-copper",
    "r.o": "ro-scrap",
    "chimney": "chimney-scrap",
    "lcd tv": "lcd-tv",
    "lcd monitor": "lcd-monitor",
    "printer": "printer",
    "fan copper wiring": "fan-copper-wiring",
    "metal e-waste": "metal-e-waste",
    "plastic e-waste": "plastic-e-waste",
    "glass": "glass",
}
PRICE_PATTERN = re.compile(
    r"₹\s*([0-9][0-9,]*(?:\.\d+)?)\s*Per\s*(Kg|Kilogram|Piece)", re.IGNORECASE
)


class UrbanScrapError(ValueError):
    pass


@dataclass(frozen=True)
class PublishedRate:
    source_material_name: str
    price: Decimal
    unit: str


class _HeadingParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self._heading_depth = 0
        self._parts: list[str] = []
        self.headings: list[str] = []

    def handle_starttag(self, tag, attrs):
        if tag.lower() in {"h2", "h3", "h4"}:
            self._heading_depth += 1
            if self._heading_depth == 1:
                self._parts = []

    def handle_data(self, data):
        if self._heading_depth:
            self._parts.append(data)

    def handle_endtag(self, tag):
        if tag.lower() in {"h2", "h3", "h4"} and self._heading_depth:
            self._heading_depth -= 1
            if self._heading_depth == 0:
                text = " ".join(" ".join(self._parts).split())
                if text:
                    self.headings.append(text)


class UrbanScrapAdapter(PriceSourceAdapter):
    """Collect Urban Scrap's public Delhi NCR buying-rate page once per run."""

    def __init__(self, *, collected_on: date | None = None):
        self.collected_on = collected_on
        self.last_extracted: list[PublishedRate] = []
        self.last_skipped: list[dict[str, str]] = []

    @property
    def source_identifier(self) -> str:
        return URBAN_SCRAP_SOURCE_SLUG

    def fetch(self) -> bytes:
        settings = get_settings()
        source_url = settings.urban_scrap_url
        parsed = urlparse(source_url)
        if parsed.scheme != "https" or parsed.hostname != "urbanscrap.co":
            raise UrbanScrapError("Urban Scrap URL configuration is invalid")
        request = Request(
            source_url,
            headers={
                "User-Agent": settings.collector_user_agent,
                "Accept": "text/html,application/xhtml+xml",
            },
        )
        try:
            with urlopen(request, timeout=settings.collector_timeout_seconds) as response:
                content_type = response.headers.get_content_type()
                if content_type not in {"text/html", "application/xhtml+xml"}:
                    raise UrbanScrapError(f"Unexpected Urban Scrap content type: {content_type}")
                return response.read()
        except UrbanScrapError:
            raise
        except Exception as exc:
            raise UrbanScrapError(f"Urban Scrap rate page unavailable: {exc}") from exc

    def parse(self, raw: bytes) -> list[PublishedRate]:
        if not raw:
            raise UrbanScrapError("Urban Scrap page is empty")
        try:
            html = raw.decode("utf-8")
        except UnicodeDecodeError as exc:
            raise UrbanScrapError("Urban Scrap page is not valid UTF-8 HTML") from exc
        parser = _HeadingParser()
        parser.feed(html)
        rates: list[PublishedRate] = []
        previous_heading: str | None = None
        for heading in parser.headings:
            match = PRICE_PATTERN.fullmatch(heading.strip())
            if match and previous_heading:
                try:
                    price = Decimal(match.group(1).replace(",", ""))
                except InvalidOperation as exc:
                    raise UrbanScrapError(f"Invalid published price for {previous_heading}") from exc
                if price <= 0:
                    raise UrbanScrapError(f"Invalid published price for {previous_heading}")
                unit = "kg" if match.group(2).lower() in {"kg", "kilogram"} else "piece"
                rates.append(PublishedRate(previous_heading, price, unit))
            previous_heading = heading
        if not rates:
            raise UrbanScrapError("Urban Scrap page structure could not be parsed")
        self.last_extracted = rates
        return rates

    def normalize(self, rows: list[PublishedRate]) -> list[AdapterObservation]:
        collected_at = datetime.now(timezone.utc)
        observation_date = self.collected_on or collected_at.date()
        normalized: list[AdapterObservation] = []
        skipped: list[dict[str, str]] = []
        for row in rows:
            key = " ".join(row.source_material_name.strip().lower().split())
            material = MATERIAL_MAP.get(key)
            if row.unit != "kg":
                skipped.append({"source_material_name": row.source_material_name, "reason": "per-piece item excluded"})
                continue
            if material is None:
                reason = "unmapped material"
                if "wire" in key or "wiring" in key:
                    reason = "wire grade mapping requires review"
                skipped.append({"source_material_name": row.source_material_name, "reason": reason})
                continue
            normalized.append(
                AdapterObservation(
                    source=URBAN_SCRAP_SOURCE_SLUG,
                    material=material,
                    city="delhi",
                    date=observation_date,
                    low_price=row.price,
                    average_price=row.price,
                    high_price=row.price,
                    unit="kg",
                    raw_reference=URBAN_SCRAP_URL,
                    metadata={
                        "source_material_name": row.source_material_name,
                        "published_price": str(row.price),
                        "published_unit": "kg",
                        "source_url": URBAN_SCRAP_URL,
                        "collected_at": collected_at.isoformat(),
                        "region": "Delhi NCR",
                        "geography_strategy": "single regional quote attached once to default Delhi market",
                        "parser": "urban_scrap_headings_v1",
                    },
                    price_context="local_scrap",
                )
            )
        self.last_skipped = skipped
        if not normalized:
            raise UrbanScrapError("Urban Scrap page contained no supported ₹/kg materials")
        return normalized

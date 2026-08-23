from datetime import date
from pathlib import Path
from decimal import Decimal
import pytest

from app.ingestion.adapters.urban_scrap import UrbanScrapAdapter, UrbanScrapError

FIXTURES = Path(__file__).parent / "fixtures"

@pytest.fixture
def observations():
    adapter = UrbanScrapAdapter(collected_on=date(2026, 8, 23))
    parsed = adapter.parse((FIXTURES / "urban_scrap_rates.html").read_bytes())
    return adapter, adapter.normalize(parsed)

@pytest.mark.parametrize("material,price", [
    ("copper", Decimal("900")), ("brass", Decimal("600")),
    ("aluminium", Decimal("230")), ("iron", Decimal("26")),
    ("newspaper", Decimal("15")), ("cardboard", Decimal("8")),
])
def test_supported_material_parse(observations, material, price):
    _, rows = observations
    row = next(item for item in rows if item.material == material)
    assert (row.low_price, row.average_price, row.high_price) == (price, price, price)
    assert row.unit == "kg" and row.city == "delhi" and row.price_context == "local_scrap"

def test_rupees_per_kg_detection(observations):
    _, rows = observations
    assert len(rows) == 29 and all(row.unit == "kg" for row in rows)

def test_generic_plastic_not_mapped_to_pet(observations):
    _, rows = observations
    assert all(row.material != "pet-plastic" for row in rows)
    assert next(row for row in rows if row.metadata["source_material_name"] == "Plastic").material == "plastic"

def test_generic_steel_and_ambiguous_wire_remain_distinct(observations):
    adapter, _ = observations
    skipped = {item["source_material_name"]: item["reason"] for item in adapter.last_skipped}
    assert "requires review" in skipped["Copper Wire"]
    rows = observations[1]
    assert next(row for row in rows if row.metadata["source_material_name"] == "Steel").material == "steel"
    assert all(row.material != "stainless-steel" for row in rows)

def test_per_piece_item_excluded(observations):
    adapter, _ = observations
    assert any(item["source_material_name"] == "Split/ Window AC 1 Ton" and item["reason"] == "per-piece item excluded" for item in adapter.last_skipped)

def test_malformed_html_fails():
    adapter = UrbanScrapAdapter()
    with pytest.raises(UrbanScrapError, match="could not be parsed"):
        adapter.parse((FIXTURES / "urban_scrap_malformed.html").read_bytes())

def test_collection_date_changes_daily_identity():
    raw = (FIXTURES / "urban_scrap_rates.html").read_bytes()
    first = UrbanScrapAdapter(collected_on=date(2026, 8, 23)); second = UrbanScrapAdapter(collected_on=date(2026, 8, 24))
    first_row = first.normalize(first.parse(raw))[0]; second_row = second.normalize(second.parse(raw))[0]
    assert first_row.date != second_row.date
    assert (first_row.source, first_row.material, first_row.city) == (second_row.source, second_row.material, second_row.city)

def test_source_attribution_preserved(observations):
    _, rows = observations; copper = next(row for row in rows if row.material == "copper")
    assert copper.source == "urban-scrap"
    assert copper.metadata["source_material_name"] == "Copper"
    assert copper.metadata["published_price"] == "900"
    assert copper.metadata["region"] == "Delhi NCR"
    assert copper.raw_reference == "https://urbanscrap.co/scrap-rates/"

from datetime import date, timedelta
from decimal import Decimal
from math import sin

from sqlalchemy import func, select

from app.database import SessionLocal
from app.models import City, Material, MaterialCategory, MaterialGrade, PriceSource, ScrapPrice


CITIES = {"Delhi": 1.000, "Gurgaon": 1.018, "Noida": 0.993, "Faridabad": 0.982, "Ghaziabad": 0.977}
MATERIALS = [
    {"slug": "copper", "name": "Copper", "category": "Metal", "unit": "kg", "base": 742.0, "icon": "Cu", "description": "Copper wire, pipe, utensils and clean copper scrap."},
    {"slug": "brass", "name": "Brass", "category": "Metal", "unit": "kg", "base": 512.0, "icon": "Br", "description": "Brass fittings, utensils, sanitary and industrial scrap."},
    {"slug": "aluminium", "name": "Aluminium", "category": "Metal", "unit": "kg", "base": 176.0, "icon": "Al", "description": "Aluminium sheet, utensils, sections and mixed aluminium."},
    {"slug": "iron", "name": "Iron / MS", "category": "Metal", "unit": "kg", "base": 34.2, "icon": "Fe", "description": "Iron, mild steel, structural and fabrication scrap."},
    {"slug": "cardboard", "name": "Cardboard", "category": "Paper", "unit": "kg", "base": 14.6, "icon": "CB", "description": "Corrugated boxes, cartons and clean cardboard."},
    {"slug": "pet-plastic", "name": "PET Plastic", "category": "Plastic", "unit": "kg", "base": 29.5, "icon": "PET", "description": "PET bottles and sorted recyclable plastic."},
    {"slug": "newspaper", "name": "Newspaper", "category": "Paper", "unit": "kg", "base": 16.8, "icon": "NP", "description": "Old newspapers and clean printed paper."},
    {"slug": "stainless-steel", "name": "Stainless Steel", "category": "Metal", "unit": "kg", "base": 118.0, "icon": "SS", "description": "Stainless utensils, sheet, pipe and industrial scrap."},
    {"slug": "e-waste", "name": "E-waste Mixed", "category": "Electronics", "unit": "kg", "base": 86.0, "icon": "EW", "description": "Mixed non-hazardous electronic scrap; final rates depend on composition."},
]
GRADES = [("clean", "Clean", Decimal("1.0400")), ("standard", "Standard", Decimal("1.0000")), ("mixed", "Mixed", Decimal("0.9100"))]


def trend_value(base: float, index: int, city_factor: float) -> Decimal:
    drift = 1 + (index - 15) * 0.0017
    wave = 1 + sin(index / 3.15) * 0.018 + sin(index / 6.8) * 0.009
    return Decimal(str(round(base * city_factor * drift * wave, 2)))


def seed_demo_data() -> tuple[int, int]:
    with SessionLocal() as session:
        categories = {}
        for name in sorted({item["category"] for item in MATERIALS}):
            category = session.scalar(select(MaterialCategory).where(MaterialCategory.slug == name.lower()))
            if not category:
                category = MaterialCategory(slug=name.lower(), name=name)
                session.add(category); session.flush()
            categories[name] = category
        cities = {}
        for name in CITIES:
            slug = name.lower().replace(" ", "-")
            city = session.scalar(select(City).where(City.slug == slug))
            if not city:
                city = City(slug=slug, name=name)
                session.add(city); session.flush()
            cities[name] = city
        materials = {}
        for item in MATERIALS:
            material = session.scalar(select(Material).where(Material.slug == item["slug"]))
            if not material:
                material = Material(category_id=categories[item["category"]].id, slug=item["slug"], name=item["name"], unit=item["unit"], icon=item["icon"], description=item["description"])
                session.add(material); session.flush()
            materials[item["slug"]] = material
            for grade_slug, grade_name, multiplier in GRADES:
                grade_id = session.scalar(select(MaterialGrade.id).where(MaterialGrade.material_id == material.id, MaterialGrade.slug == grade_slug))
                if not grade_id:
                    session.add(MaterialGrade(material_id=material.id, slug=grade_slug, name=f"{grade_name} {material.name}", price_multiplier=multiplier))
        source = session.scalar(select(PriceSource).where(PriceSource.slug == "demo-generator"))
        if not source:
            source = PriceSource(
                slug="demo-generator",
                name="ScrapRate Demo Generator",
                source_type="admin",
                trust_score=Decimal("25.00"),
                is_verified=False,
                notes="System-generated indicative development data.",
            )
            session.add(source); session.flush()
        session.commit()

        today = date.today(); start_date = today - timedelta(days=29)
        existing = set(session.execute(select(ScrapPrice.material_id, ScrapPrice.city_id, ScrapPrice.price_date).where(ScrapPrice.source_id == source.id, ScrapPrice.material_grade_id.is_(None), ScrapPrice.price_date.between(start_date, today))).all())
        inserted = 0
        for item in MATERIALS:
            material = materials[item["slug"]]
            for city_name, city_factor in CITIES.items():
                city = cities[city_name]
                for offset in range(30):
                    price_date = start_date + timedelta(days=offset)
                    if (material.id, city.id, price_date) in existing:
                        continue
                    average = trend_value(item["base"], offset, city_factor)
                    spread = max(average * Decimal("0.018"), Decimal("0.60"))
                    session.add(ScrapPrice(material_id=material.id, city_id=city.id, price_date=price_date, price_low=(average-spread).quantize(Decimal("0.01")), price_high=(average+spread).quantize(Decimal("0.01")), price_average=average, unit=material.unit, source_id=source.id, source_type=source.source_type, confidence_score=Decimal("0.2500"), is_demo=True))
                    inserted += 1
        session.commit()
        total = session.scalar(select(func.count()).select_from(ScrapPrice))
        return inserted, int(total or 0)


if __name__ == "__main__":
    new_rows, total_rows = seed_demo_data()
    print(f"Demo seed complete: {new_rows} inserted, {total_rows} total price rows")

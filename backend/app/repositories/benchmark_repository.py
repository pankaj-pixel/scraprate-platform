from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload
from app.models import Material, PriceSource, ScrapPrice

def get_material(session: Session, slug: str):
    return session.scalar(select(Material).where(Material.slug == slug, Material.is_active.is_(True)))

def latest_two(session: Session, material_id: int):
    return list(session.scalars(select(ScrapPrice).options(joinedload(ScrapPrice.source)).join(PriceSource, ScrapPrice.source_id==PriceSource.id).where(
        ScrapPrice.material_id==material_id, ScrapPrice.price_context=="benchmark", ScrapPrice.material_grade_id.is_(None),
        PriceSource.source_type=="market_reference", PriceSource.is_active.is_(True)
    ).order_by(ScrapPrice.price_date.desc(),ScrapPrice.id.desc()).limit(2)).unique())

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session, joinedload

from app.models import City, Material, MaterialCategory, MaterialGrade, PriceSource


def get_city(session: Session, identifier: str) -> City | None:
    normalized = identifier.strip().lower()
    return session.scalar(
        select(City).where(
            City.is_active.is_(True),
            or_(City.slug == normalized, func.lower(City.name) == normalized),
        )
    )


def list_cities(session: Session) -> list[City]:
    return list(
        session.scalars(
            select(City).where(City.is_active.is_(True)).order_by(City.id)
        )
    )


def get_material(session: Session, slug: str) -> Material | None:
    return session.scalar(
        select(Material)
        .options(joinedload(Material.category), joinedload(Material.grades))
        .where(
            func.lower(Material.slug) == slug.strip().lower(),
            Material.is_active.is_(True),
        )
    )


def list_materials(
    session: Session,
    category: str | None = None,
    search: str | None = None,
) -> list[Material]:
    statement = (
        select(Material)
        .join(Material.category)
        .options(joinedload(Material.category))
        .where(Material.is_active.is_(True))
        .order_by(Material.display_order, Material.name)
    )
    if category and category.strip().lower() != "all":
        normalized_category = category.strip().lower()
        statement = statement.where(
            or_(
                MaterialCategory.slug == normalized_category,
                func.lower(MaterialCategory.name) == normalized_category,
            )
        )
    if search and (query := search.strip()):
        pattern = f"%{query}%"
        statement = statement.where(
            or_(
                Material.name.like(pattern),
                Material.slug.like(pattern),
                Material.description.like(pattern),
                Material.icon.like(pattern),
            )
        )
    return list(session.scalars(statement).unique())


def list_active_grades(material: Material) -> list[MaterialGrade]:
    return sorted(
        (grade for grade in material.grades if grade.is_active),
        key=lambda grade: grade.id,
    )


def get_grade(session: Session, material_id: int, slug: str) -> MaterialGrade | None:
    return session.scalar(
        select(MaterialGrade).where(
            MaterialGrade.material_id == material_id,
            func.lower(MaterialGrade.slug) == slug.strip().lower(),
            MaterialGrade.is_active.is_(True),
        )
    )


def list_price_sources(session: Session) -> list[PriceSource]:
    return list(
        session.scalars(
            select(PriceSource)
            .where(PriceSource.is_active.is_(True))
            .order_by(PriceSource.name)
        )
    )


def get_price_source(session: Session, identifier: str) -> PriceSource | None:
    normalized = identifier.strip().lower()
    return session.scalar(
        select(PriceSource).where(
            PriceSource.is_active.is_(True),
            or_(
                PriceSource.slug == normalized,
                func.lower(PriceSource.name) == normalized,
            ),
        )
    )

from sqlalchemy.orm import Session

from app.models import City, Material
from app.repositories import material_repository


def find_city(session: Session, identifier: str) -> City | None:
    return material_repository.get_city(session, identifier)


def get_cities(session: Session) -> list[City]:
    return material_repository.list_cities(session)


def find_material(session: Session, slug: str) -> Material | None:
    return material_repository.get_material(session, slug)


def get_materials(
    session: Session, category: str | None = None, search: str | None = None
) -> list[Material]:
    return material_repository.list_materials(session, category, search)


def get_active_grades(material: Material):
    return material_repository.list_active_grades(material)


def find_grade(session: Session, material: Material, slug: str):
    return material_repository.get_grade(session, material.id, slug)


def get_price_sources(session: Session):
    return material_repository.list_price_sources(session)


def find_price_source(session: Session, identifier: str):
    return material_repository.get_price_source(session, identifier)

from datetime import date

from sqlalchemy import func, select, tuple_
from sqlalchemy.orm import Session, joinedload

from app.models import City, Material, PriceSource, ScrapPrice


def load_reference_data(session: Session):
    cities = list(session.scalars(select(City).where(City.is_active.is_(True))))
    materials = list(
        session.scalars(
            select(Material)
            .options(joinedload(Material.grades))
            .where(Material.is_active.is_(True))
        ).unique()
    )
    sources = list(session.scalars(select(PriceSource)))
    return cities, materials, sources


def find_existing_identities(
    session: Session, identities: set[tuple[int, int, int, date, int, str]]
) -> set[tuple[int, int, int, date, int, str]]:
    if not identities:
        return set()
    grade_identity = func.coalesce(ScrapPrice.material_grade_id, 0)
    city_identity = func.coalesce(ScrapPrice.city_id, 0)
    rows = session.execute(
        select(
            ScrapPrice.material_id,
            grade_identity,
            city_identity,
            ScrapPrice.price_date,
            ScrapPrice.source_id,
            ScrapPrice.price_context,
        ).where(
            tuple_(
                ScrapPrice.material_id,
                grade_identity,
                city_identity,
                ScrapPrice.price_date,
                ScrapPrice.source_id,
                ScrapPrice.price_context,
            ).in_(identities)
        )
    ).all()
    return {tuple(row) for row in rows}


def insert_real_observations(session: Session, values: list[dict]) -> list[int]:
    observations = [ScrapPrice(**item) for item in values]
    session.add_all(observations)
    session.commit()
    return [observation.id for observation in observations]

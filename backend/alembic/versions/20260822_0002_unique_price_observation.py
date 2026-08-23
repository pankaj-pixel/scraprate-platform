"""Enforce unique scrap price observations.

Revision ID: 20260822_0002
Revises: 20260822_0001
Create Date: 2026-08-22
"""
from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "20260822_0002"
down_revision: str | None = "20260822_0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # MySQL unique indexes allow repeated NULL grade values. This stored column
    # normalizes a missing grade. Admin observations always require a valid
    # source, so the source foreign key can be indexed directly.
    op.add_column(
        "scrap_prices",
        sa.Column(
            "material_grade_identity",
            sa.Integer(),
            sa.Computed("COALESCE(material_grade_id, 0)", persisted=True),
            nullable=True,
        ),
    )
    op.create_index(
        "uq_scrap_prices_observation",
        "scrap_prices",
        [
            "material_id",
            "material_grade_identity",
            "city_id",
            "price_date",
            "source_id",
        ],
        unique=True,
    )


def downgrade() -> None:
    op.drop_index("uq_scrap_prices_observation", table_name="scrap_prices")
    op.drop_column("scrap_prices", "material_grade_identity")

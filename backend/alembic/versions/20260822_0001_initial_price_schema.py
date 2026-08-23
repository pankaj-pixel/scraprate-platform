"""Create the initial ScrapRate price intelligence schema.

Revision ID: 20260822_0001
Revises:
Create Date: 2026-08-22
"""
from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "20260822_0001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def timestamps() -> list[sa.Column]:
    return [
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    ]


def upgrade() -> None:
    op.create_table(
        "cities",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("slug", sa.String(length=80), nullable=False, unique=True),
        sa.Column("name", sa.String(length=120), nullable=False, unique=True),
        sa.Column("is_active", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        *timestamps(),
        mysql_engine="InnoDB", mysql_charset="utf8mb4", mysql_collate="utf8mb4_unicode_ci",
    )
    op.create_table(
        "material_categories",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("slug", sa.String(length=80), nullable=False, unique=True),
        sa.Column("name", sa.String(length=120), nullable=False, unique=True),
        *timestamps(),
        mysql_engine="InnoDB", mysql_charset="utf8mb4", mysql_collate="utf8mb4_unicode_ci",
    )
    op.create_table(
        "price_sources",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("slug", sa.String(length=100), nullable=False, unique=True),
        sa.Column("name", sa.String(length=180), nullable=False),
        sa.Column("source_type", sa.String(length=50), nullable=False),
        sa.Column("website_url", sa.String(length=500), nullable=True),
        sa.Column("is_active", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        *timestamps(),
        mysql_engine="InnoDB", mysql_charset="utf8mb4", mysql_collate="utf8mb4_unicode_ci",
    )
    op.create_table(
        "materials",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("category_id", sa.Integer(), sa.ForeignKey("material_categories.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("slug", sa.String(length=100), nullable=False, unique=True),
        sa.Column("name", sa.String(length=160), nullable=False),
        sa.Column("unit", sa.String(length=20), server_default="kg", nullable=False),
        sa.Column("icon", sa.String(length=12), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        *timestamps(),
        mysql_engine="InnoDB", mysql_charset="utf8mb4", mysql_collate="utf8mb4_unicode_ci",
    )
    op.create_index("ix_materials_category_id", "materials", ["category_id"])
    op.create_table(
        "material_grades",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("material_id", sa.Integer(), sa.ForeignKey("materials.id", ondelete="CASCADE"), nullable=False),
        sa.Column("slug", sa.String(length=100), nullable=False),
        sa.Column("name", sa.String(length=160), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("price_multiplier", sa.Numeric(8, 4), server_default="1", nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.CheckConstraint("price_multiplier > 0", name="ck_material_grades_positive_multiplier"),
        *timestamps(),
        mysql_engine="InnoDB", mysql_charset="utf8mb4", mysql_collate="utf8mb4_unicode_ci",
    )
    op.create_index("ix_material_grades_material_slug", "material_grades", ["material_id", "slug"], unique=True)
    op.create_table(
        "scrap_prices",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("material_id", sa.Integer(), sa.ForeignKey("materials.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("material_grade_id", sa.Integer(), sa.ForeignKey("material_grades.id", ondelete="RESTRICT"), nullable=True),
        sa.Column("city_id", sa.Integer(), sa.ForeignKey("cities.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("price_date", sa.Date(), nullable=False),
        sa.Column("price_low", sa.Numeric(12, 2), nullable=False),
        sa.Column("price_high", sa.Numeric(12, 2), nullable=False),
        sa.Column("price_average", sa.Numeric(12, 2), nullable=False),
        sa.Column("unit", sa.String(length=20), server_default="kg", nullable=False),
        sa.Column("source_id", sa.Integer(), sa.ForeignKey("price_sources.id", ondelete="SET NULL"), nullable=True),
        sa.Column("source_type", sa.String(length=50), nullable=False),
        sa.Column("confidence_score", sa.Numeric(5, 4), server_default="0", nullable=False),
        sa.Column("is_demo", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.CheckConstraint("price_low >= 0", name="ck_scrap_prices_low_nonnegative"),
        sa.CheckConstraint("price_high >= price_low", name="ck_scrap_prices_valid_range"),
        sa.CheckConstraint("price_average >= price_low AND price_average <= price_high", name="ck_scrap_prices_average_in_range"),
        sa.CheckConstraint("confidence_score >= 0 AND confidence_score <= 1", name="ck_scrap_prices_confidence_range"),
        *timestamps(),
        mysql_engine="InnoDB", mysql_charset="utf8mb4", mysql_collate="utf8mb4_unicode_ci",
    )
    op.create_index("ix_scrap_prices_material_city_date", "scrap_prices", ["material_id", "city_id", "price_date"])
    op.create_index("ix_scrap_prices_city_date", "scrap_prices", ["city_id", "price_date"])
    op.create_index("ix_scrap_prices_source_date", "scrap_prices", ["source_id", "price_date"])


def downgrade() -> None:
    op.drop_index("ix_scrap_prices_source_date", table_name="scrap_prices")
    op.drop_index("ix_scrap_prices_city_date", table_name="scrap_prices")
    op.drop_index("ix_scrap_prices_material_city_date", table_name="scrap_prices")
    op.drop_table("scrap_prices")
    op.drop_index("ix_material_grades_material_slug", table_name="material_grades")
    op.drop_table("material_grades")
    op.drop_index("ix_materials_category_id", table_name="materials")
    op.drop_table("materials")
    op.drop_table("price_sources")
    op.drop_table("material_categories")
    op.drop_table("cities")

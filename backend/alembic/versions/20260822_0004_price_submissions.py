"""Add reviewed dealer price submissions.

Revision ID: 20260822_0004
Revises: 20260822_0003
"""
from collections.abc import Sequence
from alembic import op
import sqlalchemy as sa

revision: str = "20260822_0004"
down_revision: str | None = "20260822_0003"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

def upgrade() -> None:
    op.create_table(
        "price_submissions",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("price_source_id", sa.Integer(), nullable=False),
        sa.Column("city_id", sa.Integer(), nullable=False),
        sa.Column("material_id", sa.Integer(), nullable=False),
        sa.Column("material_grade_id", sa.Integer(), nullable=True),
        sa.Column("price_date", sa.Date(), nullable=False),
        sa.Column("low_price", sa.Numeric(12, 2), nullable=False),
        sa.Column("average_price", sa.Numeric(12, 2), nullable=False),
        sa.Column("high_price", sa.Numeric(12, 2), nullable=False),
        sa.Column("unit", sa.String(20), server_default="kg", nullable=False),
        sa.Column("status", sa.String(20), server_default="pending", nullable=False),
        sa.Column("submitted_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column("reviewed_at", sa.DateTime(), nullable=True),
        sa.Column("review_notes", sa.Text(), nullable=True),
        sa.Column("approved_price_observation_id", sa.Integer(), nullable=True),
        sa.CheckConstraint("low_price > 0", name="ck_price_submissions_low_positive"),
        sa.CheckConstraint("average_price >= low_price AND average_price <= high_price", name="ck_price_submissions_average_range"),
        sa.CheckConstraint("status IN ('pending', 'approved', 'rejected')", name="ck_price_submissions_status"),
        sa.ForeignKeyConstraint(["price_source_id"], ["price_sources.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["city_id"], ["cities.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["material_id"], ["materials.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["material_grade_id"], ["material_grades.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["approved_price_observation_id"], ["scrap_prices.id"], ondelete="RESTRICT"),
        sa.UniqueConstraint("approved_price_observation_id", name="uq_price_submissions_approved_observation"),
        mysql_engine="InnoDB", mysql_charset="utf8mb4", mysql_collate="utf8mb4_unicode_ci",
    )
    op.create_index("ix_price_submissions_status_date", "price_submissions", ["status", "price_date"])
    op.create_index("ix_price_submissions_source_date", "price_submissions", ["price_source_id", "price_date"])

def downgrade() -> None:
    op.drop_table("price_submissions")

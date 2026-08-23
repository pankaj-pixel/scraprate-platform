"""Separate benchmark, local scrap, and transaction observations.

Revision ID: 20260822_0006
Revises: 20260822_0005
"""
from collections.abc import Sequence
from alembic import op
import sqlalchemy as sa

revision: str = "20260822_0006"
down_revision: str | None = "20260822_0005"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

def upgrade() -> None:
    op.add_column("scrap_prices", sa.Column("price_context", sa.String(30), server_default="local_scrap", nullable=False))
    op.alter_column("scrap_prices", "city_id", existing_type=sa.Integer(), nullable=True)
    op.add_column("scrap_prices", sa.Column("city_identity", sa.Integer(), sa.Computed("COALESCE(city_id, 0)", persisted=True), nullable=True))
    op.create_check_constraint("ck_scrap_prices_context", "scrap_prices", "price_context IN ('benchmark', 'local_scrap', 'transaction')")
    op.create_index("ix_scrap_prices_context_material_date", "scrap_prices", ["price_context", "material_id", "price_date"])
    op.create_index("uq_scrap_prices_context_observation", "scrap_prices", ["material_id", "material_grade_identity", "city_identity", "price_date", "source_id", "price_context"], unique=True)

def downgrade() -> None:
    op.drop_index("uq_scrap_prices_context_observation", table_name="scrap_prices")
    op.drop_index("ix_scrap_prices_context_material_date", table_name="scrap_prices")
    op.drop_constraint("ck_scrap_prices_context", "scrap_prices", type_="check")
    op.drop_column("scrap_prices", "city_identity")
    op.alter_column("scrap_prices", "city_id", existing_type=sa.Integer(), nullable=False)
    op.drop_column("scrap_prices", "price_context")

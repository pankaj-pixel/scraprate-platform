"""Add maintainable price source metadata.

Revision ID: 20260822_0003
Revises: 20260822_0002
Create Date: 2026-08-22
"""
from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "20260822_0003"
down_revision: str | None = "20260822_0002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("price_sources", sa.Column("city_id", sa.Integer(), nullable=True))
    op.add_column(
        "price_sources",
        sa.Column(
            "trust_score",
            sa.Numeric(5, 2),
            server_default="50",
            nullable=False,
        ),
    )
    op.add_column(
        "price_sources",
        sa.Column(
            "is_verified", sa.Boolean(), server_default=sa.text("false"), nullable=False
        ),
    )
    op.add_column("price_sources", sa.Column("notes", sa.Text(), nullable=True))
    op.create_index("ix_price_sources_city_id", "price_sources", ["city_id"])
    op.create_foreign_key(
        "fk_price_sources_city_id_cities",
        "price_sources",
        "cities",
        ["city_id"],
        ["id"],
        ondelete="SET NULL",
    )

    # Preserve the seeded source and classify it under the supported source
    # taxonomy. Its observations remain explicitly marked is_demo=true.
    op.execute(
        sa.text(
            "UPDATE price_sources "
            "SET source_type = 'admin', trust_score = 25.00, "
            "is_verified = false, "
            "notes = 'System-generated indicative development data.' "
            "WHERE slug = 'demo-generator'"
        )
    )
    op.create_check_constraint(
        "ck_price_sources_trust_score_range",
        "price_sources",
        "trust_score >= 0 AND trust_score <= 100",
    )
    op.create_check_constraint(
        "ck_price_sources_supported_type",
        "price_sources",
        "source_type IN ('admin', 'dealer', 'recycler', 'market_reference', 'transaction', 'external_api')",
    )


def downgrade() -> None:
    op.drop_constraint(
        "ck_price_sources_supported_type", "price_sources", type_="check"
    )
    op.drop_constraint(
        "ck_price_sources_trust_score_range", "price_sources", type_="check"
    )
    op.drop_constraint(
        "fk_price_sources_city_id_cities", "price_sources", type_="foreignkey"
    )
    op.drop_index("ix_price_sources_city_id", table_name="price_sources")
    op.drop_column("price_sources", "notes")
    op.drop_column("price_sources", "is_verified")
    op.drop_column("price_sources", "trust_score")
    op.drop_column("price_sources", "city_id")

"""Add privacy-conscious visitor analytics.

Revision ID: 20260825_0008
Revises: 20260823_0007
"""
from collections.abc import Sequence
from alembic import op
import sqlalchemy as sa

revision: str = "20260825_0008"
down_revision: str | None = "20260823_0007"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

def upgrade() -> None:
    op.create_table("visitor_events",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("occurred_at", sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("visitor_hash", sa.String(64), nullable=False),
        sa.Column("session_hash", sa.String(64), nullable=False),
        sa.Column("event_name", sa.String(50), nullable=False),
        sa.Column("path", sa.String(255), nullable=False),
        sa.Column("referrer_domain", sa.String(255)),
        sa.Column("device_type", sa.String(20), server_default="unknown", nullable=False),
        sa.Column("browser", sa.String(40), server_default="unknown", nullable=False),
        sa.Column("operating_system", sa.String(40), server_default="unknown", nullable=False),
        sa.Column("material_slug", sa.String(100)),
        sa.Column("city", sa.String(80)),
        mysql_engine="InnoDB", mysql_charset="utf8mb4", mysql_collate="utf8mb4_unicode_ci")
    op.create_index("ix_visitor_events_occurred_at", "visitor_events", ["occurred_at"])
    op.create_index("ix_visitor_events_visitor_occurred", "visitor_events", ["visitor_hash", "occurred_at"])
    op.create_index("ix_visitor_events_path_occurred", "visitor_events", ["path", "occurred_at"])

def downgrade() -> None:
    op.drop_table("visitor_events")

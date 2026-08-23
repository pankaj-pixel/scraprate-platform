"""Add automated source configuration and ingestion run auditing.

Revision ID: 20260822_0005
Revises: 20260822_0004
"""
from collections.abc import Sequence
from alembic import op
import sqlalchemy as sa

revision: str = "20260822_0005"
down_revision: str | None = "20260822_0004"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

def upgrade() -> None:
    op.add_column("scrap_prices", sa.Column("raw_reference", sa.String(500), nullable=True))
    op.add_column("scrap_prices", sa.Column("observation_metadata", sa.JSON(), nullable=True))
    op.create_table("source_adapter_configs",
        sa.Column("id", sa.Integer(), primary_key=True), sa.Column("source_id", sa.Integer(), nullable=False),
        sa.Column("adapter_name", sa.String(100), nullable=False), sa.Column("enabled", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("polling_frequency", sa.String(80)), sa.Column("endpoint_config_reference", sa.String(255)),
        sa.Column("last_success_at", sa.DateTime()), sa.Column("last_attempt_at", sa.DateTime()), sa.Column("last_error", sa.Text()),
        sa.Column("consecutive_failures", sa.Integer(), server_default="0", nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False), sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["source_id"], ["price_sources.id"], ondelete="CASCADE"), sa.UniqueConstraint("source_id", name="uq_source_adapter_configs_source_id"),
        mysql_engine="InnoDB", mysql_charset="utf8mb4", mysql_collate="utf8mb4_unicode_ci")
    op.create_table("ingestion_runs",
        sa.Column("id", sa.Integer(), primary_key=True), sa.Column("source_id", sa.Integer(), nullable=False),
        sa.Column("started_at", sa.DateTime(), server_default=sa.func.now(), nullable=False), sa.Column("completed_at", sa.DateTime()),
        sa.Column("status", sa.String(20), server_default="running", nullable=False),
        sa.Column("records_received", sa.Integer(), server_default="0", nullable=False), sa.Column("records_valid", sa.Integer(), server_default="0", nullable=False),
        sa.Column("records_inserted", sa.Integer(), server_default="0", nullable=False), sa.Column("duplicates", sa.Integer(), server_default="0", nullable=False),
        sa.Column("rejected", sa.Integer(), server_default="0", nullable=False), sa.Column("error_message", sa.Text()),
        sa.CheckConstraint("status IN ('running', 'success', 'partial', 'failed')", name="ck_ingestion_runs_status"),
        sa.ForeignKeyConstraint(["source_id"], ["price_sources.id"], ondelete="RESTRICT"),
        mysql_engine="InnoDB", mysql_charset="utf8mb4", mysql_collate="utf8mb4_unicode_ci")
    op.create_index("ix_ingestion_runs_source_started", "ingestion_runs", ["source_id", "started_at"])

def downgrade() -> None:
    op.drop_table("ingestion_runs"); op.drop_table("source_adapter_configs")
    op.drop_column("scrap_prices", "observation_metadata"); op.drop_column("scrap_prices", "raw_reference")

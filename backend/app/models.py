from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Computed,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    JSON,
    Numeric,
    String,
    Text,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.base import Base

MYSQL_TABLE_OPTIONS = {
    "mysql_engine": "InnoDB",
    "mysql_charset": "utf8mb4",
    "mysql_collate": "utf8mb4_unicode_ci",
}
PRICE_SOURCE_TYPES = (
    "admin",
    "dealer",
    "recycler",
    "market_reference",
    "transaction",
    "external_api",
)


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )


class City(TimestampMixin, Base):
    __tablename__ = "cities"
    __table_args__ = MYSQL_TABLE_OPTIONS

    id: Mapped[int] = mapped_column(primary_key=True)
    slug: Mapped[str] = mapped_column(String(80), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(120), unique=True, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, server_default="true", nullable=False)

    prices: Mapped[list["ScrapPrice"]] = relationship(back_populates="city")
    price_sources: Mapped[list["PriceSource"]] = relationship(back_populates="city")
    price_submissions: Mapped[list["PriceSubmission"]] = relationship(back_populates="city")


class MaterialCategory(TimestampMixin, Base):
    __tablename__ = "material_categories"
    __table_args__ = MYSQL_TABLE_OPTIONS

    id: Mapped[int] = mapped_column(primary_key=True)
    slug: Mapped[str] = mapped_column(String(80), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(120), unique=True, nullable=False)

    materials: Mapped[list["Material"]] = relationship(back_populates="category")


class Material(TimestampMixin, Base):
    __tablename__ = "materials"
    __table_args__ = MYSQL_TABLE_OPTIONS

    id: Mapped[int] = mapped_column(primary_key=True)
    category_id: Mapped[int] = mapped_column(ForeignKey("material_categories.id", ondelete="RESTRICT"), index=True)
    slug: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(160), nullable=False)
    unit: Mapped[str] = mapped_column(String(20), default="kg", server_default="kg", nullable=False)
    icon: Mapped[str] = mapped_column(String(12), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, server_default="true", nullable=False)
    seo_title: Mapped[str | None] = mapped_column(String(180))
    seo_description: Mapped[str | None] = mapped_column(String(320))
    display_order: Mapped[int] = mapped_column(Integer, default=100, server_default="100", nullable=False)
    image_reference: Mapped[str | None] = mapped_column(String(255))
    aliases: Mapped[list | None] = mapped_column(JSON)
    source_material_mapping: Mapped[dict | None] = mapped_column(JSON)

    category: Mapped[MaterialCategory] = relationship(back_populates="materials")
    grades: Mapped[list["MaterialGrade"]] = relationship(back_populates="material", cascade="all, delete-orphan")
    prices: Mapped[list["ScrapPrice"]] = relationship(back_populates="material")
    price_submissions: Mapped[list["PriceSubmission"]] = relationship(back_populates="material")


class MaterialGrade(TimestampMixin, Base):
    __tablename__ = "material_grades"
    __table_args__ = (
        CheckConstraint("price_multiplier > 0", name="ck_material_grades_positive_multiplier"),
        Index("ix_material_grades_material_slug", "material_id", "slug", unique=True),
        MYSQL_TABLE_OPTIONS,
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    material_id: Mapped[int] = mapped_column(ForeignKey("materials.id", ondelete="CASCADE"), nullable=False)
    slug: Mapped[str] = mapped_column(String(100), nullable=False)
    name: Mapped[str] = mapped_column(String(160), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    price_multiplier: Mapped[Decimal] = mapped_column(Numeric(8, 4), default=1, server_default="1", nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, server_default="true", nullable=False)

    material: Mapped[Material] = relationship(back_populates="grades")
    prices: Mapped[list["ScrapPrice"]] = relationship(back_populates="material_grade")
    price_submissions: Mapped[list["PriceSubmission"]] = relationship(back_populates="material_grade")


class PriceSource(TimestampMixin, Base):
    __tablename__ = "price_sources"
    __table_args__ = (
        CheckConstraint(
            "trust_score >= 0 AND trust_score <= 100",
            name="ck_price_sources_trust_score_range",
        ),
        CheckConstraint(
            "source_type IN ('admin', 'dealer', 'recycler', 'market_reference', 'transaction', 'external_api')",
            name="ck_price_sources_supported_type",
        ),
        MYSQL_TABLE_OPTIONS,
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    slug: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(180), nullable=False)
    source_type: Mapped[str] = mapped_column(String(50), nullable=False)
    city_id: Mapped[int | None] = mapped_column(
        ForeignKey("cities.id", ondelete="SET NULL"), index=True
    )
    trust_score: Mapped[Decimal] = mapped_column(
        Numeric(5, 2), default=50, server_default="50", nullable=False
    )
    is_verified: Mapped[bool] = mapped_column(
        Boolean, default=False, server_default="false", nullable=False
    )
    website_url: Mapped[str | None] = mapped_column(String(500))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, server_default="true", nullable=False)
    notes: Mapped[str | None] = mapped_column(Text)

    city: Mapped[City | None] = relationship(back_populates="price_sources")
    prices: Mapped[list["ScrapPrice"]] = relationship(back_populates="source")
    price_submissions: Mapped[list["PriceSubmission"]] = relationship(back_populates="source")
    adapter_config: Mapped["SourceAdapterConfig | None"] = relationship(back_populates="source", uselist=False)
    ingestion_runs: Mapped[list["IngestionRun"]] = relationship(back_populates="source")


class ScrapPrice(TimestampMixin, Base):
    __tablename__ = "scrap_prices"
    __table_args__ = (
        CheckConstraint("price_low >= 0", name="ck_scrap_prices_low_nonnegative"),
        CheckConstraint("price_high >= price_low", name="ck_scrap_prices_valid_range"),
        CheckConstraint("price_average >= price_low AND price_average <= price_high", name="ck_scrap_prices_average_in_range"),
        CheckConstraint("confidence_score >= 0 AND confidence_score <= 1", name="ck_scrap_prices_confidence_range"),
        CheckConstraint("price_context IN ('benchmark', 'local_scrap', 'transaction')", name="ck_scrap_prices_context"),
        Index("ix_scrap_prices_material_city_date", "material_id", "city_id", "price_date"),
        Index("ix_scrap_prices_city_date", "city_id", "price_date"),
        Index("ix_scrap_prices_source_date", "source_id", "price_date"),
        Index("ix_scrap_prices_context_material_date", "price_context", "material_id", "price_date"),
        Index(
            "uq_scrap_prices_observation",
            "material_id",
            "material_grade_identity",
            "city_id",
            "price_date",
            "source_id",
            unique=True,
        ),
        Index("uq_scrap_prices_context_observation", "material_id", "material_grade_identity", "city_identity", "price_date", "source_id", "price_context", unique=True),
        MYSQL_TABLE_OPTIONS,
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    material_id: Mapped[int] = mapped_column(ForeignKey("materials.id", ondelete="RESTRICT"), nullable=False)
    material_grade_id: Mapped[int | None] = mapped_column(ForeignKey("material_grades.id", ondelete="RESTRICT"))
    city_id: Mapped[int | None] = mapped_column(ForeignKey("cities.id", ondelete="RESTRICT"), nullable=True)
    price_date: Mapped[date] = mapped_column(Date, nullable=False)
    price_low: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    price_high: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    price_average: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    unit: Mapped[str] = mapped_column(String(20), default="kg", server_default="kg", nullable=False)
    source_id: Mapped[int | None] = mapped_column(ForeignKey("price_sources.id", ondelete="SET NULL"))
    material_grade_identity: Mapped[int] = mapped_column(
        Integer,
        Computed("COALESCE(material_grade_id, 0)", persisted=True),
        nullable=True,
    )
    city_identity: Mapped[int] = mapped_column(Integer, Computed("COALESCE(city_id, 0)", persisted=True), nullable=True)
    source_type: Mapped[str] = mapped_column(String(50), nullable=False)
    confidence_score: Mapped[Decimal] = mapped_column(Numeric(5, 4), default=0, server_default="0", nullable=False)
    is_demo: Mapped[bool] = mapped_column(Boolean, default=False, server_default="false", nullable=False)
    raw_reference: Mapped[str | None] = mapped_column(String(500))
    observation_metadata: Mapped[dict | None] = mapped_column(JSON)
    price_context: Mapped[str] = mapped_column(String(30), default="local_scrap", server_default="local_scrap", nullable=False)

    material: Mapped[Material] = relationship(back_populates="prices")
    material_grade: Mapped[MaterialGrade | None] = relationship(back_populates="prices")
    city: Mapped[City | None] = relationship(back_populates="prices")
    source: Mapped[PriceSource | None] = relationship(back_populates="prices")


class PriceSubmission(Base):
    __tablename__ = "price_submissions"
    __table_args__ = (
        CheckConstraint("low_price > 0", name="ck_price_submissions_low_positive"),
        CheckConstraint("average_price >= low_price AND average_price <= high_price", name="ck_price_submissions_average_range"),
        CheckConstraint("status IN ('pending', 'approved', 'rejected')", name="ck_price_submissions_status"),
        Index("ix_price_submissions_status_date", "status", "price_date"),
        Index("ix_price_submissions_source_date", "price_source_id", "price_date"),
        MYSQL_TABLE_OPTIONS,
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    price_source_id: Mapped[int] = mapped_column(ForeignKey("price_sources.id", ondelete="RESTRICT"), nullable=False)
    city_id: Mapped[int] = mapped_column(ForeignKey("cities.id", ondelete="RESTRICT"), nullable=False)
    material_id: Mapped[int] = mapped_column(ForeignKey("materials.id", ondelete="RESTRICT"), nullable=False)
    material_grade_id: Mapped[int | None] = mapped_column(ForeignKey("material_grades.id", ondelete="RESTRICT"))
    price_date: Mapped[date] = mapped_column(Date, nullable=False)
    low_price: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    average_price: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    high_price: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    unit: Mapped[str] = mapped_column(String(20), nullable=False, default="kg", server_default="kg")
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="pending", server_default="pending")
    submitted_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    review_notes: Mapped[str | None] = mapped_column(Text)
    approved_price_observation_id: Mapped[int | None] = mapped_column(ForeignKey("scrap_prices.id", ondelete="RESTRICT"), unique=True)

    source: Mapped[PriceSource] = relationship(back_populates="price_submissions")
    city: Mapped[City] = relationship(back_populates="price_submissions")
    material: Mapped[Material] = relationship(back_populates="price_submissions")
    material_grade: Mapped[MaterialGrade | None] = relationship(back_populates="price_submissions")
    approved_price_observation: Mapped[ScrapPrice | None] = relationship()


class SourceAdapterConfig(TimestampMixin, Base):
    __tablename__ = "source_adapter_configs"
    __table_args__ = MYSQL_TABLE_OPTIONS

    id: Mapped[int] = mapped_column(primary_key=True)
    source_id: Mapped[int] = mapped_column(ForeignKey("price_sources.id", ondelete="CASCADE"), unique=True, nullable=False)
    adapter_name: Mapped[str] = mapped_column(String(100), nullable=False)
    enabled: Mapped[bool] = mapped_column(Boolean, default=False, server_default="false", nullable=False)
    polling_frequency: Mapped[str | None] = mapped_column(String(80))
    endpoint_config_reference: Mapped[str | None] = mapped_column(String(255))
    last_success_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    last_attempt_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    last_error: Mapped[str | None] = mapped_column(Text)
    consecutive_failures: Mapped[int] = mapped_column(Integer, default=0, server_default="0", nullable=False)

    source: Mapped[PriceSource] = relationship(back_populates="adapter_config")


class IngestionRun(Base):
    __tablename__ = "ingestion_runs"
    __table_args__ = (
        CheckConstraint("status IN ('running', 'success', 'partial', 'failed')", name="ck_ingestion_runs_status"),
        Index("ix_ingestion_runs_source_started", "source_id", "started_at"),
        MYSQL_TABLE_OPTIONS,
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    source_id: Mapped[int] = mapped_column(ForeignKey("price_sources.id", ondelete="RESTRICT"), nullable=False)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    status: Mapped[str] = mapped_column(String(20), default="running", server_default="running", nullable=False)
    records_received: Mapped[int] = mapped_column(Integer, default=0, server_default="0", nullable=False)
    records_valid: Mapped[int] = mapped_column(Integer, default=0, server_default="0", nullable=False)
    records_inserted: Mapped[int] = mapped_column(Integer, default=0, server_default="0", nullable=False)
    duplicates: Mapped[int] = mapped_column(Integer, default=0, server_default="0", nullable=False)
    rejected: Mapped[int] = mapped_column(Integer, default=0, server_default="0", nullable=False)
    error_message: Mapped[str | None] = mapped_column(Text)

    source: Mapped[PriceSource] = relationship(back_populates="ingestion_runs")


class VisitorEvent(Base):
    __tablename__ = "visitor_events"
    __table_args__ = (
        Index("ix_visitor_events_occurred_at", "occurred_at"),
        Index("ix_visitor_events_visitor_occurred", "visitor_hash", "occurred_at"),
        Index("ix_visitor_events_path_occurred", "path", "occurred_at"),
        MYSQL_TABLE_OPTIONS,
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    visitor_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    session_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    event_name: Mapped[str] = mapped_column(String(50), nullable=False)
    path: Mapped[str] = mapped_column(String(255), nullable=False)
    referrer_domain: Mapped[str | None] = mapped_column(String(255))
    device_type: Mapped[str] = mapped_column(String(20), nullable=False, default="unknown", server_default="unknown")
    browser: Mapped[str] = mapped_column(String(40), nullable=False, default="unknown", server_default="unknown")
    operating_system: Mapped[str] = mapped_column(String(40), nullable=False, default="unknown", server_default="unknown")
    material_slug: Mapped[str | None] = mapped_column(String(100))
    city: Mapped[str | None] = mapped_column(String(80))

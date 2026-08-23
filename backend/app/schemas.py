from __future__ import annotations

from datetime import date as Date, datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, Field, model_validator


CityName = Literal["Delhi", "Gurgaon", "Noida", "Faridabad", "Ghaziabad"]
PriceSourceType = Literal[
    "admin",
    "dealer",
    "recycler",
    "market_reference",
    "transaction",
    "external_api",
]
ConfidenceLevel = Literal["LOW", "MEDIUM", "HIGH"]
FreshnessLevel = Literal["FRESH", "STALE", "VERY_STALE"]

class PublicSourceDetail(BaseModel):
    name: str
    source_type: str
    trust_score: float
    region: str | None = None
    collected_at: datetime | None = None
    source_url: str | None = None


class MaterialSummary(BaseModel):
    slug: str
    name: str
    category: str
    unit: str
    city: str
    price: float
    low: float
    high: float
    previous_price: float
    change: float
    change_pct: float
    description: str
    icon: str


class HistoryPoint(BaseModel):
    date: Date
    price: float


class MaterialHistory(BaseModel):
    slug: str
    city: str
    unit: str
    history: list[HistoryPoint]


class CityResponse(BaseModel):
    slug: str
    name: str


class CitiesResponse(BaseModel):
    cities: list[CityResponse]


class GradeResponse(BaseModel):
    slug: str
    name: str
    description: str | None
    price_multiplier: float


class MaterialResponse(BaseModel):
    slug: str
    name: str
    category: str
    unit: str
    description: str
    icon: str
    seo_title: str | None = None
    seo_description: str | None = None
    display_order: int = 100
    image_reference: str | None = None
    aliases: list[str] = Field(default_factory=list)


class MaterialDetailResponse(MaterialResponse):
    grades: list[GradeResponse]


class PriceResponse(BaseModel):
    material: str
    slug: str
    category: str
    city: str
    unit: str
    price: float
    low: float
    high: float
    previous_price: float
    change: float
    change_percent: float
    last_updated: datetime
    price_date: Date
    is_demo: bool
    description: str
    icon: str


class PriceHistoryPoint(HistoryPoint):
    low: float
    high: float
    is_demo: bool


class PriceHistoryResponse(BaseModel):
    material: str
    slug: str
    category: str
    city: str
    unit: str
    days: int
    history: list[PriceHistoryPoint]


class MarketOverviewResponse(BaseModel):
    city: str
    tracked_materials: int
    gainers: list[PriceResponse]
    losers: list[PriceResponse]
    updated_at: Date


class AdminPriceCreate(BaseModel):
    date: Date
    city: str = Field(min_length=1, max_length=80)
    material: str = Field(min_length=1, max_length=100)
    grade: str | None = Field(default=None, max_length=100)
    low_price: Decimal = Field(ge=0, max_digits=12, decimal_places=2)
    average_price: Decimal = Field(ge=0, max_digits=12, decimal_places=2)
    high_price: Decimal = Field(ge=0, max_digits=12, decimal_places=2)
    unit: str = Field(default="kg", min_length=1, max_length=20)
    source: str = Field(min_length=1, max_length=100)
    source_type: str | None = Field(default=None, max_length=50)
    confidence_score: Decimal = Field(ge=0, le=1, max_digits=5, decimal_places=4)
    is_demo: bool

    @model_validator(mode="after")
    def validate_price_range(self):
        if not self.low_price <= self.average_price <= self.high_price:
            raise ValueError("low_price must be <= average_price <= high_price")
        return self


class AdminPriceUpdate(BaseModel):
    date: Date | None = None
    city: str | None = Field(default=None, min_length=1, max_length=80)
    material: str | None = Field(default=None, min_length=1, max_length=100)
    grade: str | None = Field(default=None, max_length=100)
    low_price: Decimal | None = Field(default=None, ge=0, max_digits=12, decimal_places=2)
    average_price: Decimal | None = Field(default=None, ge=0, max_digits=12, decimal_places=2)
    high_price: Decimal | None = Field(default=None, ge=0, max_digits=12, decimal_places=2)
    unit: str | None = Field(default=None, min_length=1, max_length=20)
    source: str | None = Field(default=None, min_length=1, max_length=100)
    source_type: str | None = Field(default=None, max_length=50)
    confidence_score: Decimal | None = Field(default=None, ge=0, le=1, max_digits=5, decimal_places=4)
    is_demo: bool | None = None


class AdminPriceResponse(BaseModel):
    id: int
    date: Date
    city: str
    city_slug: str
    material: str
    material_slug: str
    grade: str | None
    grade_slug: str | None
    low_price: float
    average_price: float
    high_price: float
    unit: str
    source: str
    source_slug: str
    price_source_id: int
    source_type: str
    confidence_score: float
    is_demo: bool
    created_at: datetime
    updated_at: datetime


class AdminOption(BaseModel):
    slug: str
    name: str


class AdminMaterialOption(AdminOption):
    unit: str
    grades: list[AdminOption]


class AdminSourceOption(AdminOption):
    source_type: str


class AdminPriceOptionsResponse(BaseModel):
    cities: list[AdminOption]
    materials: list[AdminMaterialOption]
    sources: list[AdminSourceOption]


class PriceSourceCreate(BaseModel):
    name: str = Field(min_length=1, max_length=180)
    slug: str = Field(
        min_length=1, max_length=100, pattern=r"^[a-z0-9]+(?:-[a-z0-9]+)*$"
    )
    source_type: PriceSourceType
    city: str | None = Field(default=None, max_length=80)
    trust_score: Decimal = Field(ge=0, le=100, max_digits=5, decimal_places=2)
    is_verified: bool = False
    is_active: bool = True
    notes: str | None = Field(default=None, max_length=2000)


class PriceSourceUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=180)
    slug: str | None = Field(
        default=None,
        min_length=1,
        max_length=100,
        pattern=r"^[a-z0-9]+(?:-[a-z0-9]+)*$",
    )
    source_type: PriceSourceType | None = None
    city: str | None = Field(default=None, max_length=80)
    trust_score: Decimal | None = Field(
        default=None, ge=0, le=100, max_digits=5, decimal_places=2
    )
    is_verified: bool | None = None
    is_active: bool | None = None
    notes: str | None = Field(default=None, max_length=2000)


class PriceSourceResponse(BaseModel):
    id: int
    name: str
    slug: str
    source_type: PriceSourceType
    city: str | None
    city_slug: str | None
    trust_score: float
    is_verified: bool
    is_active: bool
    notes: str | None
    created_at: datetime
    updated_at: datetime


class IndicativeMarketPriceResponse(BaseModel):
    material: str
    slug: str
    city: str
    unit: str
    indicative_price: float
    low: float
    high: float
    median: float
    weighted_average: float
    source_count: int
    verified_source_count: int
    confidence: ConfidenceLevel
    data_type: Literal["demo", "real"]
    price_date: Date
    last_updated: datetime
    source_names: list[str] = Field(default_factory=list)
    source_details: list[PublicSourceDetail] = Field(default_factory=list)
    freshness: FreshnessLevel
    age_days: int
    freshness_label: str


class HomepageMarketMaterial(BaseModel):
    material: str
    slug: str
    category: str
    city: str
    unit: str
    indicative_price: float
    low: float
    high: float
    median: float
    previous_indicative_price: float | None
    change: float | None
    change_percent: float | None
    source_count: int
    verified_source_count: int
    confidence: ConfidenceLevel
    data_type: Literal["demo", "real"]
    price_date: Date
    last_updated: datetime
    description: str
    icon: str
    history: list[HistoryPoint]
    source_names: list[str] = Field(default_factory=list)
    source_details: list[PublicSourceDetail] = Field(default_factory=list)
    freshness: FreshnessLevel
    age_days: int
    freshness_label: str


class HomepageMarketOverviewResponse(BaseModel):
    city: str
    tracked_materials: int
    data_type: Literal["demo", "real", "mixed"]
    updated_at: datetime | None
    materials: list[HomepageMarketMaterial]


class ApprovedImportRow(BaseModel):
    row_number: int = Field(ge=1)
    date: Date
    city: str = Field(min_length=1, max_length=80)
    material: str = Field(min_length=1, max_length=100)
    grade: str | None = Field(default=None, max_length=100)
    low_price: Decimal = Field(ge=0, max_digits=12, decimal_places=2)
    average_price: Decimal = Field(ge=0, max_digits=12, decimal_places=2)
    high_price: Decimal = Field(ge=0, max_digits=12, decimal_places=2)
    unit: str = Field(min_length=1, max_length=20)
    source: str = Field(min_length=1, max_length=100)

    @model_validator(mode="after")
    def validate_import_price_range(self):
        if not self.low_price <= self.average_price <= self.high_price:
            raise ValueError("low_price must be <= average_price <= high_price")
        return self


class ImportValidRow(ApprovedImportRow):
    source_type: str
    source_trust_score: float
    source_is_verified: bool
    confidence_score: float
    is_demo: Literal[False]


class ImportRowIssue(BaseModel):
    row_number: int
    errors: list[str]
    raw: dict[str, str]


class PriceImportPreviewResponse(BaseModel):
    total_rows: int
    valid_rows: list[ImportValidRow]
    invalid_rows: list[ImportRowIssue]
    duplicate_rows: list[ImportRowIssue]
    unknown_materials: list[ImportRowIssue]
    unknown_cities: list[ImportRowIssue]
    unknown_grades: list[ImportRowIssue]
    unknown_sources: list[ImportRowIssue]


class PriceImportCommitRequest(BaseModel):
    rows: list[ApprovedImportRow] = Field(min_length=1, max_length=1000)


class PriceImportCommitResponse(BaseModel):
    approved_count: int
    inserted_count: int
    inserted_ids: list[int]
    invalid_rows: list[ImportRowIssue]
    duplicate_rows: list[ImportRowIssue]


SubmissionStatus = Literal["pending", "approved", "rejected"]


class PriceSubmissionCreate(BaseModel):
    source: str = Field(min_length=1, max_length=100)
    city: str = Field(min_length=1, max_length=80)
    material: str = Field(min_length=1, max_length=100)
    grade: str | None = Field(default=None, max_length=100)
    date: Date
    low: Decimal = Field(gt=0, max_digits=12, decimal_places=2)
    average: Decimal = Field(gt=0, max_digits=12, decimal_places=2)
    high: Decimal = Field(gt=0, max_digits=12, decimal_places=2)
    unit: str = Field(default="kg", min_length=1, max_length=20)

    @model_validator(mode="after")
    def validate_range(self):
        if not self.low <= self.average <= self.high:
            raise ValueError("low must be <= average <= high")
        return self


class PriceSubmissionReview(BaseModel):
    notes: str | None = Field(default=None, max_length=2000)


class PriceSubmissionResponse(BaseModel):
    id: int
    source: str
    source_slug: str
    source_type: Literal["dealer", "recycler"]
    city: str
    city_slug: str
    material: str
    material_slug: str
    grade: str | None
    grade_slug: str | None
    date: Date
    low: float
    average: float
    high: float
    unit: str
    status: SubmissionStatus
    submitted_at: datetime
    reviewed_at: datetime | None
    review_notes: str | None
    approved_price_observation_id: int | None


class IngestionRunResponse(BaseModel):
    id: int
    started_at: datetime
    completed_at: datetime | None
    status: Literal["running", "success", "partial", "failed"]
    records_received: int
    records_valid: int
    records_inserted: int
    duplicates: int
    rejected: int
    error_message: str | None


class DataSourceHealthResponse(BaseModel):
    id: int
    name: str
    slug: str
    source_type: PriceSourceType
    city: str | None
    is_active: bool
    is_verified: bool
    trust_score: float
    adapter_name: str | None
    adapter_enabled: bool
    adapter_registered: bool
    polling_frequency: str | None
    last_success_at: datetime | None
    last_attempt_at: datetime | None
    last_error: str | None
    consecutive_failures: int
    latest_run: IngestionRunResponse | None


class BenchmarkResponse(BaseModel):
    material: str
    slug: str
    benchmark_source: str
    date: Date
    close: float
    previous_close: float | None
    change: float | None
    change_percent: float | None
    high: float
    low: float
    contract: str | None
    unit: str
    source_reference: str | None
    last_updated: datetime

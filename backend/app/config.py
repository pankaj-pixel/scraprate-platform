from functools import lru_cache

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    database_url: str
    environment: str = "development"
    database_ssl: bool = False
    database_ssl_ca: str | None = None
    cors_origins: str = "http://localhost:5173,http://127.0.0.1:5173"
    mcx_bhavcopy_url: str | None = None
    price_fresh_days: int = 1
    price_stale_days: int = 3
    public_site_url: str = "http://localhost:5173"
    allowed_hosts: str = "localhost,127.0.0.1"
    urban_scrap_url: str = "https://urbanscrap.co/scrap-rates/"
    collector_user_agent: str = "ScrapRate-Public-Rate-Collector/1.0 (+price-source monitoring)"
    collector_timeout_seconds: int = 20

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @field_validator("database_url")
    @classmethod
    def validate_mysql_url(cls, value: str) -> str:
        if not value.startswith("mysql+pymysql://"):
            raise ValueError("DATABASE_URL must use the mysql+pymysql driver")
        return value

    @field_validator("environment")
    @classmethod
    def validate_environment(cls, value: str) -> str:
        normalized = value.lower()
        if normalized not in {"development", "test", "production"}:
            raise ValueError("ENVIRONMENT must be development, test, or production")
        return normalized

    @property
    def allowed_cors_origins(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]

    @property
    def trusted_hosts(self) -> list[str]:
        return [host.strip() for host in self.allowed_hosts.split(",") if host.strip()]

    def validate_production(self) -> None:
        if self.environment != "production":
            return
        if not self.public_site_url.startswith("https://"):
            raise ValueError("PUBLIC_SITE_URL must use HTTPS in production")
        if "localhost" in self.cors_origins or "127.0.0.1" in self.cors_origins or "*" in self.allowed_cors_origins:
            raise ValueError("CORS_ORIGINS must contain explicit HTTPS production origins")
        if not self.trusted_hosts or "*" in self.trusted_hosts:
            raise ValueError("ALLOWED_HOSTS must list explicit production hosts")

    @property
    def database_connect_args(self) -> dict[str, object]:
        if not self.database_ssl:
            return {}
        if self.database_ssl_ca:
            return {"ssl": {"ca": self.database_ssl_ca, "check_hostname": True}}
        return {"ssl": {"check_hostname": False}}


@lru_cache
def get_settings() -> Settings:
    settings = Settings()
    settings.validate_production()
    return settings

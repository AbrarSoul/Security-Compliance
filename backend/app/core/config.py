from functools import lru_cache
from typing import Literal

from pydantic import Field, PostgresDsn, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from app.services.files.supported_formats import DEFAULT_ALLOWED_EXTENSIONS


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    app_name: str = Field(default="Security Compliance API", alias="APP_NAME")
    app_env: Literal["development", "staging", "production"] = Field(
        default="development", alias="APP_ENV"
    )
    debug: bool = Field(default=False, alias="DEBUG")
    api_v1_prefix: str = Field(default="/api/v1", alias="API_V1_PREFIX")

    host: str = Field(default="0.0.0.0", alias="HOST")
    port: int = Field(default=8000, alias="PORT")

    database_url: PostgresDsn = Field(
        default="postgresql+asyncpg://compliance:compliance@localhost:5432/compliance",
        alias="DATABASE_URL",
    )

    jwt_secret_key: str = Field(..., alias="JWT_SECRET_KEY")
    jwt_algorithm: str = Field(default="HS256", alias="JWT_ALGORITHM")
    jwt_access_token_expire_minutes: int = Field(
        default=30, alias="JWT_ACCESS_TOKEN_EXPIRE_MINUTES"
    )
    jwt_refresh_token_expire_days: int = Field(
        default=7, alias="JWT_REFRESH_TOKEN_EXPIRE_DAYS"
    )

    cors_origins: str = Field(
        default="http://localhost:3000",
        alias="CORS_ORIGINS",
    )

    # File storage
    storage_backend: Literal["local"] = Field(default="local", alias="STORAGE_BACKEND")
    storage_local_path: str = Field(default="./uploads", alias="STORAGE_LOCAL_PATH")
    max_upload_size_mb: int = Field(default=50, alias="MAX_UPLOAD_SIZE_MB")
    allowed_file_extensions: str = Field(
        default=DEFAULT_ALLOWED_EXTENSIONS, alias="ALLOWED_FILE_EXTENSIONS"
    )
    metadata_preview_rows: int = Field(default=50, alias="METADATA_PREVIEW_ROWS")

    # Compliance scanner
    scan_max_sample_rows: int = Field(default=1000, alias="SCAN_MAX_SAMPLE_ROWS")
    scan_match_threshold: float = Field(default=0.05, alias="SCAN_MATCH_THRESHOLD")

    # Compliance scoring (key:value pairs comma-separated for weight maps)
    score_severity_weights: str = Field(
        default="low:5,medium:15,high:25,critical:40",
        alias="SCORE_SEVERITY_WEIGHTS",
    )
    score_finding_type_weights: str = Field(
        default="email:10,phone:10,password:35,api_key:40,name:5,sensitive_field:8",
        alias="SCORE_FINDING_TYPE_WEIGHTS",
    )
    score_compliant_max: int = Field(default=30, alias="SCORE_COMPLIANT_MAX")
    score_risky_max: int = Field(default=60, alias="SCORE_RISKY_MAX")
    score_max: int = Field(default=100, alias="SCORE_MAX")
    score_density_multiplier: int = Field(default=10, alias="SCORE_DENSITY_MULTIPLIER")
    score_classification_restricted_min: int = Field(
        default=70, alias="SCORE_CLASSIFICATION_RESTRICTED_MIN"
    )
    score_classification_confidential_min: int = Field(
        default=40, alias="SCORE_CLASSIFICATION_CONFIDENTIAL_MIN"
    )
    score_classification_internal_min: int = Field(
        default=15, alias="SCORE_CLASSIFICATION_INTERNAL_MIN"
    )
    score_critical_escalation_match_rate: float = Field(
        default=0.01, alias="SCORE_CRITICAL_ESCALATION_MATCH_RATE"
    )
    score_force_non_compliant_on_critical: bool = Field(
        default=True, alias="SCORE_FORCE_NON_COMPLIANT_ON_CRITICAL"
    )

    # Sprint 3 — monitoring pipeline
    monitoring_outbox_worker_enabled: bool = Field(
        default=True, alias="MONITORING_OUTBOX_WORKER_ENABLED"
    )
    monitoring_outbox_poll_seconds: float = Field(
        default=1.0, alias="MONITORING_OUTBOX_POLL_SECONDS"
    )
    monitoring_outbox_batch_size: int = Field(
        default=25, alias="MONITORING_OUTBOX_BATCH_SIZE"
    )

    # Sprint 3 — notification email
    smtp_enabled: bool = Field(default=False, alias="SMTP_ENABLED")
    smtp_host: str = Field(default="localhost", alias="SMTP_HOST")
    smtp_port: int = Field(default=587, alias="SMTP_PORT")
    smtp_user: str = Field(default="", alias="SMTP_USER")
    smtp_password: str = Field(default="", alias="SMTP_PASSWORD")
    smtp_from: str = Field(default="compliance@localhost", alias="SMTP_FROM")
    smtp_use_tls: bool = Field(default=True, alias="SMTP_USE_TLS")
    smtp_timeout_seconds: int = Field(default=15, alias="SMTP_TIMEOUT_SECONDS")

    # Sprint 3 — compliance gap analysis
    encryption_at_rest_enabled: bool = Field(default=False, alias="ENCRYPTION_AT_REST_ENABLED")

    # GPT-Lab model registry sync
    gptlab_api_key: str = Field(default="", alias="GPTLAB_API_KEY")
    gptlab_api_base: str = Field(
        default="https://gptlab.rd.tuni.fi/GPT-Lab/resources/GPU-farmi-004/v1",
        alias="GPTLAB_API_BASE",
    )

    @field_validator("database_url", mode="before")
    @classmethod
    def ensure_async_driver(cls, value: str) -> str:
        url = str(value)
        if url.startswith("postgresql://"):
            return url.replace("postgresql://", "postgresql+asyncpg://", 1)
        return url

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]

    @property
    def is_development(self) -> bool:
        return self.app_env == "development"

    @property
    def max_upload_size_bytes(self) -> int:
        return self.max_upload_size_mb * 1024 * 1024

    @property
    def allowed_extensions_set(self) -> set[str]:
        return {ext.strip().lower().lstrip(".") for ext in self.allowed_file_extensions.split(",")}


@lru_cache
def get_settings() -> Settings:
    return Settings()

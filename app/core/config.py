from functools import lru_cache
from typing import Literal

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings using pydantic-settings with fail-fast validation."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    APP_NAME: str = "TaskHub — Task Management API"
    APP_VERSION: str = "0.5.0"
    APP_ENV: Literal["development", "staging", "production", "test"] = "development"
    API_V1_PREFIX: str = "/api/v1"
    DEBUG: bool = False

    # Database
    DATABASE_URL: str = Field(
        default="sqlite+aiosqlite:///./app.db",
        description="Async SQLAlchemy database connection URL",
    )
    DB_ECHO: bool = False

    # JWT & Security (No insecure hardcoded default; loaded from .env or environment)
    SECRET_KEY: str = Field(
        ...,
        min_length=32,
        description="Secret key used to sign JWT tokens (must be >= 32 chars)",
    )
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(default=30, ge=1, le=1440)
    REFRESH_TOKEN_EXPIRE_DAYS: int = Field(default=7, ge=1, le=90)

    # Redis & Caching
    REDIS_URL: str = Field(
        default="redis://localhost:6379/0",
        description="Redis connection URL for caching and token revocation",
    )
    CACHE_TTL_SECONDS: int = Field(default=60, ge=5, le=86400)
    REDIS_RETRY_COOLDOWN_SECONDS: float = Field(default=5.0, ge=0.5, le=300.0)

    # CORS (Explicit origins instead of wildcard '*' when credentials are allowed)
    CORS_ORIGINS: list[str] = Field(
        default_factory=lambda: [
            "http://localhost:8000",
            "http://127.0.0.1:8000",
            "http://localhost:3000",
        ]
    )

    @field_validator("DATABASE_URL")
    @classmethod
    def validate_database_url(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("DATABASE_URL must not be empty")
        return cleaned

    @field_validator("CORS_ORIGINS")
    @classmethod
    def validate_cors_origins(cls, value: list[str]) -> list[str]:
        if "*" in value:
            raise ValueError(
                "Wildcard '*' is not allowed in CORS_ORIGINS when credentials are enabled"
            )
        return value


@lru_cache
def get_settings() -> Settings:
    """Return cached Settings instance."""
    return Settings()  # type: ignore[call-arg]


settings = get_settings()

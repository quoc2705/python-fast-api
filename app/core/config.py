import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    """Application settings for Session 2 (Database & SQLAlchemy 2.x Async)."""

    APP_NAME: str = "Task Management API"
    APP_VERSION: str = "0.2.0"
    API_V1_PREFIX: str = "/api/v1"
    DEBUG: bool = True
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL",
        "sqlite+aiosqlite:///./app.db",
    )
    DB_ECHO: bool = os.getenv("DB_ECHO", "false").lower() == "true"


settings = Settings()

from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    """Application settings for Session 1 (Core Setup)."""

    APP_NAME: str = "Task Management API"
    APP_VERSION: str = "0.1.0"
    API_V1_PREFIX: str = "/api/v1"
    DEBUG: bool = True


settings = Settings()


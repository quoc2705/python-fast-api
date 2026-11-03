from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.v1.router import api_router
from app.core.config import settings
from app.repositories.task_repository import task_repository_singleton


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
    """Application lifespan context manager for startup and shutdown events."""
    task_repository_singleton.seed_initial_data()
    yield


def create_app() -> FastAPI:
    """Create and configure the FastAPI application instance."""
    application = FastAPI(
        title=settings.APP_NAME,
        version=settings.APP_VERSION,
        description="Sample Task Management API built with FastAPI Layered Architecture",
        lifespan=lifespan,
    )
    application.include_router(api_router, prefix=settings.API_V1_PREFIX)

    @application.get("/health", tags=["Health"], summary="Health check endpoint")
    async def health_check() -> dict[str, str]:
        return {"status": "ok", "version": settings.APP_VERSION}

    return application


app = create_app()

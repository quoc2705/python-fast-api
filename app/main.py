from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

import app.models  # noqa: F401 - register all 8 TaskHub ORM models on metadata
from app.api.v1.router import api_router
from app.core.config import settings
from app.db.session import engine, init_db


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
    """Application lifespan context manager managing async database lifecycle."""
    await init_db()
    yield
    await engine.dispose()


def create_app() -> FastAPI:
    """Create and configure the TaskHub FastAPI application instance."""
    application = FastAPI(
        title=settings.APP_NAME,
        version=settings.APP_VERSION,
        description=(
            "TaskHub — Hệ thống quản lý công việc (Task Management API) built with "
            "Layered Architecture, SQLAlchemy 2.x Async, Generic BaseRepository[T], and Alembic"
        ),
        lifespan=lifespan,
    )
    application.include_router(api_router, prefix=settings.API_V1_PREFIX)

    @application.get("/health", tags=["Health"], summary="Health check endpoint")
    async def health_check() -> dict[str, str]:
        return {"status": "ok", "app": settings.APP_NAME, "version": settings.APP_VERSION}

    return application


app = create_app()

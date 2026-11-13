from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse

import app.models  # noqa: F401 - register all 8 TaskHub ORM models on metadata
from app.api.v1.router import api_router
from app.core.cache import cache_manager
from app.core.config import settings
from app.core.exceptions import register_exception_handlers
from app.core.logging import setup_logging
from app.core.middleware import RequestContextMiddleware
from app.db.session import engine, init_db

WEB_INDEX_PATH = Path(__file__).resolve().parent / "web" / "index.html"


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
    """Application lifespan context manager managing DB and Redis cache lifecycle."""
    setup_logging(debug=settings.DEBUG)
    await init_db()
    await cache_manager.connect()
    yield
    await cache_manager.close()
    await engine.dispose()


def create_app() -> FastAPI:
    """Create and configure the TaskHub FastAPI application instance."""
    application = FastAPI(
        title=settings.APP_NAME,
        version=settings.APP_VERSION,
        description=(
            "TaskHub — Hệ thống quản lý công việc (Task Management API) built with "
            "Layered Architecture, SQLAlchemy 2.x Async, JWT Auth, RBAC, Redis Cache, "
            "Background Tasks, and Alembic Migrations"
        ),
        lifespan=lifespan,
    )

    application.add_middleware(RequestContextMiddleware)
    application.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    register_exception_handlers(application)
    application.include_router(api_router, prefix=settings.API_V1_PREFIX)

    @application.get(
        "/",
        response_class=HTMLResponse,
        include_in_schema=False,
    )
    async def web_dashboard() -> HTMLResponse:
        return HTMLResponse(content=WEB_INDEX_PATH.read_text(encoding="utf-8"))

    @application.get("/health", tags=["Health"], summary="Health check endpoint")
    async def health_check() -> dict[str, str]:
        return {
            "status": "ok",
            "app": settings.APP_NAME,
            "version": settings.APP_VERSION,
            "env": settings.APP_ENV,
        }

    return application


app = create_app()

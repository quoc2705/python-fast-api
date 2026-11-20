from typing import Any

from pydantic import Field

from app.schemas.base import BaseSchema


class ErrorResponse(BaseSchema):
    """Standardized error payload returned by TaskHub exception handlers."""

    detail: str | dict[str, Any] | list[Any] = Field(
        ...,
        description="Human-readable error description",
    )
    error_code: str = Field(
        ...,
        description="Machine-readable error code",
        examples=["NOT_FOUND", "FORBIDDEN", "UNAUTHORIZED", "CONFLICT"],
    )
    errors: list[Any] | dict[str, Any] | None = Field(
        default=None,
        description="Additional structured validation or domain error items",
    )
    request_id: str | None = Field(
        default=None,
        description="Correlation X-Request-ID for tracing",
    )


class ProjectCacheStatsResponse(BaseSchema):
    """Response schema for project task cache statistics."""

    project_id: int
    namespace: str
    cache_prefix: str
    backend: str
    ttl_seconds: int
    hits: int
    misses: int
    hit_rate_percent: float
    invalidations: int


AUTH_ERROR_RESPONSES: dict[int | str, dict[str, Any]] = {
    401: {"model": ErrorResponse, "description": "Unauthorized (Missing or Invalid JWT)"},
    422: {"model": ErrorResponse, "description": "Request Validation Error"},
    500: {"model": ErrorResponse, "description": "Internal Server Error"},
}

RESOURCE_READ_RESPONSES: dict[int | str, dict[str, Any]] = {
    401: {"model": ErrorResponse, "description": "Unauthorized (Missing or Invalid JWT)"},
    403: {"model": ErrorResponse, "description": "Forbidden (Insufficient RBAC Role)"},
    404: {"model": ErrorResponse, "description": "Requested Resource Not Found"},
    422: {"model": ErrorResponse, "description": "Request Validation Error"},
    500: {"model": ErrorResponse, "description": "Internal Server Error"},
}

RESOURCE_WRITE_RESPONSES: dict[int | str, dict[str, Any]] = {
    400: {"model": ErrorResponse, "description": "Bad Request / Domain Rule Violation"},
    401: {"model": ErrorResponse, "description": "Unauthorized (Missing or Invalid JWT)"},
    403: {"model": ErrorResponse, "description": "Forbidden (Insufficient RBAC Role)"},
    404: {"model": ErrorResponse, "description": "Requested Resource Not Found"},
    409: {"model": ErrorResponse, "description": "Conflict with Existing Resource"},
    422: {"model": ErrorResponse, "description": "Request Validation Error"},
    500: {"model": ErrorResponse, "description": "Internal Server Error"},
}

COMMON_ERROR_RESPONSES = RESOURCE_WRITE_RESPONSES

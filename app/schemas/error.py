from typing import Any

from pydantic import BaseModel, Field


class ErrorResponse(BaseModel):
    """Standardized error payload returned by TaskHub exception handlers."""

    detail: str = Field(..., description="Human-readable error description")
    error_code: str = Field(
        ...,
        description="Machine-readable error code",
        examples=["NOT_FOUND", "FORBIDDEN", "UNAUTHORIZED", "CONFLICT"],
    )
    details: Any | None = Field(
        default=None,
        description="Additional structured error context if available",
    )
    request_id: str | None = Field(
        default=None,
        description="Correlation X-Request-ID for tracing",
    )


COMMON_ERROR_RESPONSES: dict[int | str, dict[str, Any]] = {
    400: {"model": ErrorResponse, "description": "Bad Request / Domain Rule Violation"},
    401: {"model": ErrorResponse, "description": "Unauthorized (Missing or Invalid JWT)"},
    403: {"model": ErrorResponse, "description": "Forbidden (Insufficient RBAC Role)"},
    404: {"model": ErrorResponse, "description": "Requested Resource Not Found"},
    409: {"model": ErrorResponse, "description": "Conflict with Existing Resource"},
    422: {"model": ErrorResponse, "description": "Request Validation Error"},
}

import re
import time
import uuid
from collections.abc import Awaitable, Callable

from fastapi import Request, Response, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.constants import REQUEST_ID_MAX_LENGTH
from app.core.logging import get_logger

logger = get_logger("app.middleware")

_VALID_REQUEST_ID_RE = re.compile(rf"^[A-Za-z0-9\-_]{{1,{REQUEST_ID_MAX_LENGTH}}}$")


def sanitize_request_id(raw_value: str | None) -> str:
    """Validate incoming X-Request-ID header; generate a fresh UUID4 if missing or malformed."""
    if raw_value and _VALID_REQUEST_ID_RE.fullmatch(raw_value):
        return raw_value
    return str(uuid.uuid4())


def apply_security_headers(response: Response) -> None:
    """Attach standard HTTP security headers to an outgoing response."""
    response.headers.setdefault("X-Content-Type-Options", "nosniff")
    response.headers.setdefault("X-Frame-Options", "DENY")
    response.headers.setdefault(
        "Referrer-Policy",
        "strict-origin-when-cross-origin",
    )


class RequestContextMiddleware(BaseHTTPMiddleware):
    """Middleware adding validated X-Request-ID, X-Process-Time-Ms, security headers, and access logging even on 500 errors."""

    async def dispatch(
        self,
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
        request_id = sanitize_request_id(request.headers.get("X-Request-ID"))
        request.state.request_id = request_id
        start_time = time.perf_counter()

        try:
            response = await call_next(request)
        except Exception:
            logger.exception(
                "Unhandled exception during %s %s [req_id=%s]",
                request.method,
                request.url.path,
                request_id,
            )
            response = JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content={
                    "detail": "Internal server error",
                    "error_code": "INTERNAL_SERVER_ERROR",
                    "errors": None,
                    "request_id": request_id,
                },
            )

        elapsed_ms = (time.perf_counter() - start_time) * 1000.0
        response.headers["X-Request-ID"] = request_id
        response.headers["X-Process-Time-Ms"] = f"{elapsed_ms:.2f}"
        apply_security_headers(response)

        logger.info(
            "%s %s -> %s (%.2f ms) [req_id=%s]",
            request.method,
            request.url.path,
            response.status_code,
            elapsed_ms,
            request_id,
        )
        return response


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Middleware injecting standard HTTP security headers into all API responses."""

    async def dispatch(
        self,
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
        response = await call_next(request)
        apply_security_headers(response)
        return response

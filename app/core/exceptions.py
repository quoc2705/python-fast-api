from typing import Any

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from sqlalchemy.exc import IntegrityError
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.core.logging import get_logger

logger = get_logger("app.exceptions")


class AppException(Exception):
    """Base domain exception for TaskHub."""

    def __init__(
        self,
        message: str,
        *,
        status_code: int = status.HTTP_400_BAD_REQUEST,
        error_code: str = "APP_ERROR",
        errors: list[Any] | dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.error_code = error_code
        self.errors = errors


class NotFoundException(AppException):
    """Raised when a requested resource does not exist."""

    def __init__(self, message: str = "Resource not found") -> None:
        super().__init__(
            message,
            status_code=status.HTTP_404_NOT_FOUND,
            error_code="NOT_FOUND",
        )


class ConflictException(AppException):
    """Raised when an operation conflicts with existing state."""

    def __init__(self, message: str = "Resource conflict") -> None:
        super().__init__(
            message,
            status_code=status.HTTP_409_CONFLICT,
            error_code="CONFLICT",
        )


class UnauthorizedException(AppException):
    """Raised when authentication credentials are missing or invalid."""

    def __init__(self, message: str = "Invalid or expired credentials") -> None:
        super().__init__(
            message,
            status_code=status.HTTP_401_UNAUTHORIZED,
            error_code="UNAUTHORIZED",
        )


class ForbiddenException(AppException):
    """Raised when the authenticated user lacks permission for an action."""

    def __init__(
        self,
        message: str = "You do not have permission to perform this action",
    ) -> None:
        super().__init__(
            message,
            status_code=status.HTTP_403_FORBIDDEN,
            error_code="FORBIDDEN",
        )


class BadRequestException(AppException):
    """Raised when client input violates domain rules."""

    def __init__(self, message: str = "Bad request") -> None:
        super().__init__(
            message,
            status_code=status.HTTP_400_BAD_REQUEST,
            error_code="BAD_REQUEST",
        )


def register_exception_handlers(app: FastAPI) -> None:
    """Register unified exception handlers on the FastAPI instance."""

    @app.exception_handler(AppException)
    async def handle_app_exception(
        request: Request,
        exc: AppException,
    ) -> JSONResponse:
        request_id = getattr(request.state, "request_id", None)
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "detail": exc.message,
                "error_code": exc.error_code,
                "errors": exc.errors,
                "request_id": request_id,
            },
        )

    @app.exception_handler(StarletteHTTPException)
    async def handle_http_exception(
        request: Request,
        exc: StarletteHTTPException,
    ) -> JSONResponse:
        request_id = getattr(request.state, "request_id", None)
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "detail": exc.detail,
                "error_code": f"HTTP_{exc.status_code}",
                "errors": None,
                "request_id": request_id,
            },
            headers=getattr(exc, "headers", None),
        )

    @app.exception_handler(RequestValidationError)
    async def handle_validation_error(
        request: Request,
        exc: RequestValidationError,
    ) -> JSONResponse:
        request_id = getattr(request.state, "request_id", None)
        sanitized_errors = [
            {
                "loc": list(err.get("loc", ())),
                "msg": str(err.get("msg", "")),
                "type": str(err.get("type", "")),
            }
            for err in exc.errors()
        ]
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={
                "detail": "Validation error",
                "error_code": "VALIDATION_ERROR",
                "errors": sanitized_errors,
                "request_id": request_id,
            },
        )

    @app.exception_handler(IntegrityError)
    async def handle_integrity_error(
        request: Request,
        _exc: IntegrityError,
    ) -> JSONResponse:
        request_id = getattr(request.state, "request_id", None)
        return JSONResponse(
            status_code=status.HTTP_409_CONFLICT,
            content={
                "detail": "Database integrity constraint violated",
                "error_code": "CONFLICT",
                "errors": None,
                "request_id": request_id,
            },
        )

    @app.exception_handler(Exception)
    async def handle_unexpected_exception(
        request: Request,
        _exc: Exception,
    ) -> JSONResponse:
        request_id = getattr(request.state, "request_id", None)
        logger.exception("Unhandled error on %s %s", request.method, request.url.path)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "detail": "Internal server error",
                "error_code": "INTERNAL_SERVER_ERROR",
                "errors": None,
                "request_id": request_id,
            },
        )

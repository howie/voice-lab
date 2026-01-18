"""Unified error response handler middleware.

T034: Implement unified error response format
"""

import traceback
from collections.abc import Callable

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from src.domain.errors import (
    AppError,
    AuthenticationError,
    ErrorCode,
    ForbiddenError,
    NotFoundError,
    RateLimitError,
    ServiceUnavailableError,
    ValidationError,
)


class ErrorResponse:
    """Standardized error response format."""

    @staticmethod
    def create(
        code: str,
        message: str,
        details: dict | None = None,
        request_id: str | None = None,
    ) -> dict:
        """Create standardized error response."""
        response = {
            "error": {
                "code": code,
                "message": message,
            }
        }

        if details:
            response["error"]["details"] = details

        if request_id:
            response["error"]["request_id"] = request_id

        return response


def setup_error_handlers(app: FastAPI) -> None:
    """Set up exception handlers for the FastAPI application."""

    @app.exception_handler(AppError)
    async def app_error_handler(request: Request, exc: AppError) -> JSONResponse:
        """Handle application errors."""
        request_id = getattr(request.state, "request_id", None)

        return JSONResponse(
            status_code=exc.status_code,
            content=ErrorResponse.create(
                code=exc.code.value,
                message=exc.message,
                details=exc.details if exc.details else None,
                request_id=request_id,
            ),
        )

    @app.exception_handler(ValidationError)
    async def validation_error_handler(request: Request, exc: ValidationError) -> JSONResponse:
        """Handle validation errors."""
        request_id = getattr(request.state, "request_id", None)

        return JSONResponse(
            status_code=400,
            content=ErrorResponse.create(
                code=exc.code.value,
                message=exc.message,
                details=exc.details if exc.details else None,
                request_id=request_id,
            ),
        )

    @app.exception_handler(AuthenticationError)
    async def auth_error_handler(request: Request, exc: AuthenticationError) -> JSONResponse:
        """Handle authentication errors."""
        request_id = getattr(request.state, "request_id", None)

        return JSONResponse(
            status_code=401,
            content=ErrorResponse.create(
                code=exc.code.value,
                message=exc.message,
                details=exc.details if exc.details else None,
                request_id=request_id,
            ),
            headers={"WWW-Authenticate": "Bearer"},
        )

    @app.exception_handler(ForbiddenError)
    async def forbidden_error_handler(request: Request, exc: ForbiddenError) -> JSONResponse:
        """Handle forbidden errors."""
        request_id = getattr(request.state, "request_id", None)

        return JSONResponse(
            status_code=403,
            content=ErrorResponse.create(
                code=exc.code.value,
                message=exc.message,
                details=exc.details if exc.details else None,
                request_id=request_id,
            ),
        )

    @app.exception_handler(NotFoundError)
    async def not_found_error_handler(request: Request, exc: NotFoundError) -> JSONResponse:
        """Handle not found errors."""
        request_id = getattr(request.state, "request_id", None)

        return JSONResponse(
            status_code=404,
            content=ErrorResponse.create(
                code=exc.code.value,
                message=exc.message,
                details=exc.details if exc.details else None,
                request_id=request_id,
            ),
        )

    @app.exception_handler(RateLimitError)
    async def rate_limit_error_handler(request: Request, exc: RateLimitError) -> JSONResponse:
        """Handle rate limit errors."""
        request_id = getattr(request.state, "request_id", None)
        headers = {}

        if exc.details and "retry_after" in exc.details:
            headers["Retry-After"] = str(exc.details["retry_after"])

        return JSONResponse(
            status_code=429,
            content=ErrorResponse.create(
                code=exc.code.value,
                message=exc.message,
                details=exc.details if exc.details else None,
                request_id=request_id,
            ),
            headers=headers,
        )

    @app.exception_handler(ServiceUnavailableError)
    async def service_unavailable_error_handler(
        request: Request, exc: ServiceUnavailableError
    ) -> JSONResponse:
        """Handle service unavailable errors."""
        request_id = getattr(request.state, "request_id", None)

        return JSONResponse(
            status_code=503,
            content=ErrorResponse.create(
                code=exc.code.value,
                message=exc.message,
                details=exc.details if exc.details else None,
                request_id=request_id,
            ),
        )

    @app.exception_handler(ValueError)
    async def value_error_handler(request: Request, exc: ValueError) -> JSONResponse:
        """Handle ValueError as validation error."""
        request_id = getattr(request.state, "request_id", None)

        return JSONResponse(
            status_code=400,
            content=ErrorResponse.create(
                code=ErrorCode.VALIDATION_ERROR.value,
                message=str(exc),
                request_id=request_id,
            ),
        )

    @app.exception_handler(Exception)
    async def general_exception_handler(request: Request, _exc: Exception) -> JSONResponse:
        """Handle unhandled exceptions."""
        request_id = getattr(request.state, "request_id", None)

        # Log the full traceback for debugging
        traceback.print_exc()

        return JSONResponse(
            status_code=500,
            content=ErrorResponse.create(
                code=ErrorCode.INTERNAL_ERROR.value,
                message="An internal error occurred",
                request_id=request_id,
            ),
        )


class RequestIdMiddleware(BaseHTTPMiddleware):
    """Middleware to add request ID to each request."""

    async def dispatch(self, request: Request, call_next: Callable) -> JSONResponse:
        """Add request ID to request state."""
        import uuid

        request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
        request.state.request_id = request_id

        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id

        return response

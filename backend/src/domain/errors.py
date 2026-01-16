"""Domain error codes and exceptions.

T035: Error codes (VALIDATION_ERROR, TEXT_TOO_LONG, SERVICE_UNAVAILABLE)
"""

from enum import Enum
from typing import Any


class ErrorCode(str, Enum):
    """Error codes for the TTS API."""

    # Validation errors (400)
    VALIDATION_ERROR = "VALIDATION_ERROR"
    TEXT_EMPTY = "TEXT_EMPTY"
    TEXT_TOO_LONG = "TEXT_TOO_LONG"
    INVALID_VOICE_ID = "INVALID_VOICE_ID"
    INVALID_PROVIDER = "INVALID_PROVIDER"
    INVALID_LANGUAGE = "INVALID_LANGUAGE"
    INVALID_SPEED = "INVALID_SPEED"
    INVALID_PITCH = "INVALID_PITCH"
    INVALID_VOLUME = "INVALID_VOLUME"
    INVALID_OUTPUT_FORMAT = "INVALID_OUTPUT_FORMAT"

    # Authentication errors (401)
    AUTHENTICATION_REQUIRED = "AUTHENTICATION_REQUIRED"
    INVALID_TOKEN = "INVALID_TOKEN"
    TOKEN_EXPIRED = "TOKEN_EXPIRED"

    # Authorization errors (403)
    FORBIDDEN = "FORBIDDEN"
    QUOTA_EXCEEDED = "QUOTA_EXCEEDED"

    # Not found errors (404)
    VOICE_NOT_FOUND = "VOICE_NOT_FOUND"
    PROVIDER_NOT_FOUND = "PROVIDER_NOT_FOUND"
    RESOURCE_NOT_FOUND = "RESOURCE_NOT_FOUND"

    # Service errors (500, 503)
    INTERNAL_ERROR = "INTERNAL_ERROR"
    SERVICE_UNAVAILABLE = "SERVICE_UNAVAILABLE"
    PROVIDER_ERROR = "PROVIDER_ERROR"
    SYNTHESIS_FAILED = "SYNTHESIS_FAILED"
    STORAGE_ERROR = "STORAGE_ERROR"

    # Rate limiting (429)
    RATE_LIMIT_EXCEEDED = "RATE_LIMIT_EXCEEDED"


class AppError(Exception):
    """Base application error."""

    def __init__(
        self,
        code: ErrorCode,
        message: str,
        details: dict[str, Any] | None = None,
        status_code: int = 500,
    ) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.details = details or {}
        self.status_code = status_code

    def to_dict(self) -> dict[str, Any]:
        """Convert error to dictionary for API response."""
        return {
            "error": {
                "code": self.code.value,
                "message": self.message,
                "details": self.details,
            }
        }


class ValidationError(AppError):
    """Validation error (400)."""

    def __init__(
        self,
        message: str,
        code: ErrorCode = ErrorCode.VALIDATION_ERROR,
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(code=code, message=message, details=details, status_code=400)


class TextTooLongError(ValidationError):
    """Text exceeds maximum length error."""

    def __init__(self, length: int, max_length: int) -> None:
        super().__init__(
            code=ErrorCode.TEXT_TOO_LONG,
            message=f"Text length ({length}) exceeds maximum allowed ({max_length})",
            details={"length": length, "max_length": max_length},
        )


class TextEmptyError(ValidationError):
    """Text is empty error."""

    def __init__(self) -> None:
        super().__init__(
            code=ErrorCode.TEXT_EMPTY,
            message="Text cannot be empty",
        )


class InvalidProviderError(ValidationError):
    """Invalid provider error."""

    def __init__(self, provider: str, valid_providers: list[str]) -> None:
        super().__init__(
            code=ErrorCode.INVALID_PROVIDER,
            message=f"Invalid provider: {provider}",
            details={"provider": provider, "valid_providers": valid_providers},
        )


class InvalidVoiceError(ValidationError):
    """Invalid voice ID error."""

    def __init__(self, voice_id: str, provider: str) -> None:
        super().__init__(
            code=ErrorCode.INVALID_VOICE_ID,
            message=f"Voice '{voice_id}' not found for provider '{provider}'",
            details={"voice_id": voice_id, "provider": provider},
        )


class AuthenticationError(AppError):
    """Authentication error (401)."""

    def __init__(
        self,
        message: str = "Authentication required",
        code: ErrorCode = ErrorCode.AUTHENTICATION_REQUIRED,
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(code=code, message=message, details=details, status_code=401)


class TokenExpiredError(AuthenticationError):
    """Token expired error."""

    def __init__(self) -> None:
        super().__init__(
            code=ErrorCode.TOKEN_EXPIRED,
            message="Authentication token has expired",
        )


class ForbiddenError(AppError):
    """Forbidden error (403)."""

    def __init__(
        self,
        message: str = "Access forbidden",
        code: ErrorCode = ErrorCode.FORBIDDEN,
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(code=code, message=message, details=details, status_code=403)


class NotFoundError(AppError):
    """Not found error (404)."""

    def __init__(
        self,
        message: str,
        code: ErrorCode = ErrorCode.RESOURCE_NOT_FOUND,
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(code=code, message=message, details=details, status_code=404)


class VoiceNotFoundError(NotFoundError):
    """Voice not found error."""

    def __init__(self, voice_id: str) -> None:
        super().__init__(
            code=ErrorCode.VOICE_NOT_FOUND,
            message=f"Voice not found: {voice_id}",
            details={"voice_id": voice_id},
        )


class ProviderNotFoundError(NotFoundError):
    """Provider not found error."""

    def __init__(self, provider: str) -> None:
        super().__init__(
            code=ErrorCode.PROVIDER_NOT_FOUND,
            message=f"Provider not found: {provider}",
            details={"provider": provider},
        )


class RateLimitError(AppError):
    """Rate limit exceeded error (429)."""

    def __init__(
        self,
        retry_after: int | None = None,
    ) -> None:
        super().__init__(
            code=ErrorCode.RATE_LIMIT_EXCEEDED,
            message="Rate limit exceeded",
            details={"retry_after": retry_after} if retry_after else {},
            status_code=429,
        )


class ServiceUnavailableError(AppError):
    """Service unavailable error (503)."""

    def __init__(
        self,
        message: str = "Service temporarily unavailable",
        code: ErrorCode = ErrorCode.SERVICE_UNAVAILABLE,
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(code=code, message=message, details=details, status_code=503)


class ProviderError(ServiceUnavailableError):
    """TTS provider error."""

    def __init__(self, provider: str, error_message: str) -> None:
        super().__init__(
            code=ErrorCode.PROVIDER_ERROR,
            message=f"Provider '{provider}' error: {error_message}",
            details={"provider": provider, "error": error_message},
        )


class SynthesisError(AppError):
    """Synthesis failed error."""

    def __init__(self, provider: str, error_message: str) -> None:
        super().__init__(
            code=ErrorCode.SYNTHESIS_FAILED,
            message=f"Speech synthesis failed: {error_message}",
            details={"provider": provider, "error": error_message},
            status_code=500,
        )


class StorageError(AppError):
    """Storage error."""

    def __init__(self, error_message: str) -> None:
        super().__init__(
            code=ErrorCode.STORAGE_ERROR,
            message=f"Storage error: {error_message}",
            details={"error": error_message},
            status_code=500,
        )

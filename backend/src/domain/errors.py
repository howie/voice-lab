"""Domain error codes and exceptions.

T035: Error codes (VALIDATION_ERROR, TEXT_TOO_LONG, SERVICE_UNAVAILABLE)
"""

from enum import StrEnum
from typing import Any


class ErrorCode(StrEnum):
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
    """Rate limit exceeded error (429).

    Supports both internal rate limiting (no provider) and external API
    rate limiting (with provider context).
    """

    def __init__(
        self,
        retry_after: int | None = None,
        provider: str | None = None,
        original_error: str | None = None,
    ) -> None:
        if provider:
            display_name = ProviderQuotaInfo.get(provider)["display_name"]
            message = f"{display_name} 請求過於頻繁，請稍後重試"
        else:
            message = "Rate limit exceeded"

        details: dict[str, Any] = {}
        if retry_after:
            details["retry_after"] = retry_after
        if provider:
            details["provider"] = provider
        if original_error:
            details["original_error"] = original_error

        super().__init__(
            code=ErrorCode.RATE_LIMIT_EXCEEDED,
            message=message,
            details=details,
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
    """TTS provider error.

    T068: Handle TTS provider unavailability with retry suggestion
    """

    # Default retry delays per provider (in seconds)
    RETRY_DELAYS: dict[str, int] = {
        "azure": 5,
        "gemini": 5,
        "elevenlabs": 10,
        "voai": 5,
    }

    # Alternative providers to suggest
    ALTERNATIVES: dict[str, list[str]] = {
        "azure": ["gemini", "elevenlabs"],
        "gemini": ["azure", "elevenlabs"],
        "elevenlabs": ["azure", "gemini"],
        "voai": ["azure", "gemini"],
    }

    def __init__(
        self,
        provider: str,
        error_message: str,
        retry_after: int | None = None,
        suggest_alternatives: bool = True,
    ) -> None:
        retry_delay = retry_after or self.RETRY_DELAYS.get(provider, 5)
        alternatives = self.ALTERNATIVES.get(provider, []) if suggest_alternatives else []

        details = {
            "provider": provider,
            "error": error_message,
            "retry_after_seconds": retry_delay,
            "suggestion": f"Please retry after {retry_delay} seconds",
        }

        if alternatives:
            details["alternative_providers"] = alternatives
            details["suggestion"] += f" or try alternative providers: {', '.join(alternatives)}"

        super().__init__(
            code=ErrorCode.PROVIDER_ERROR,
            message=f"Provider '{provider}' is temporarily unavailable: {error_message}",
            details=details,
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


class ProviderQuotaInfo:
    """Provider-specific quota information and suggestions.

    T001: Provides display names, help URLs, and actionable suggestions
    for each supported TTS/STT provider.
    """

    PROVIDERS: dict[str, dict[str, Any]] = {
        "gemini": {
            "display_name": "Gemini TTS",
            "help_url": "https://ai.google.dev/pricing",
            "default_retry_after": 3600,  # 1 hour
            "suggestions": [
                "檢查您的 Google AI Studio 用量統計",
                "考慮升級至付費方案",
                "暫時切換到其他 TTS 供應商",
            ],
        },
        "elevenlabs": {
            "display_name": "ElevenLabs",
            "help_url": "https://elevenlabs.io/subscription",
            "default_retry_after": 3600,
            "suggestions": [
                "檢查您的 ElevenLabs 用量統計",
                "購買額外的字元配額",
                "暫時切換到其他 TTS 供應商",
            ],
        },
        "azure": {
            "display_name": "Azure Speech",
            "help_url": "https://portal.azure.com",
            "default_retry_after": 60,
            "suggestions": [
                "檢查您的 Azure Portal 用量統計",
                "考慮升級服務層級",
                "暫時切換到其他語音服務",
            ],
        },
        "gcp": {
            "display_name": "Google Cloud Speech",
            "help_url": "https://console.cloud.google.com/apis",
            "default_retry_after": 60,
            "suggestions": [
                "檢查您的 GCP Console 配額用量",
                "申請增加配額限制",
                "暫時切換到其他語音服務",
            ],
        },
        "openai": {
            "display_name": "OpenAI Whisper",
            "help_url": "https://platform.openai.com/usage",
            "default_retry_after": 60,
            "suggestions": [
                "檢查您的 OpenAI 用量統計",
                "考慮升級方案",
                "暫時切換到其他 STT 供應商",
            ],
        },
        "deepgram": {
            "display_name": "Deepgram",
            "help_url": "https://console.deepgram.com",
            "default_retry_after": 60,
            "suggestions": [
                "檢查您的 Deepgram Console 用量",
                "考慮升級方案",
                "暫時切換到其他 STT 供應商",
            ],
        },
        "voai": {
            "display_name": "VoAI TTS",
            "help_url": "https://voai.ai",
            "default_retry_after": 60,
            "suggestions": [
                "檢查您的 VoAI 帳戶用量",
                "考慮升級方案",
                "暫時切換到其他 TTS 供應商",
            ],
        },
    }

    @classmethod
    def get(cls, provider: str) -> dict[str, Any]:
        """Get quota info for a provider, with fallback defaults."""
        return cls.PROVIDERS.get(
            provider,
            {
                "display_name": provider.title(),
                "help_url": None,
                "default_retry_after": 60,
                "suggestions": ["請稍後再試或切換到其他供應商"],
            },
        )


class QuotaExceededError(AppError):
    """API quota exceeded error (429).

    T001: Raised when an API provider reports that the usage quota has been exceeded.
    Provides provider-specific information and actionable suggestions.
    """

    def __init__(
        self,
        provider: str,
        provider_display_name: str | None = None,
        quota_type: str | None = None,
        retry_after: int | None = None,
        help_url: str | None = None,
        suggestions: list[str] | None = None,
        original_error: str | None = None,
    ) -> None:
        # Get provider-specific defaults
        provider_info = ProviderQuotaInfo.get(provider)

        # Use provided values or fall back to defaults
        display_name = provider_display_name or provider_info["display_name"]
        final_retry_after = retry_after or provider_info["default_retry_after"]
        final_help_url = help_url or provider_info["help_url"]
        final_suggestions = suggestions or provider_info["suggestions"]

        # Build details dict
        details: dict[str, Any] = {
            "provider": provider,
            "provider_display_name": display_name,
        }

        if final_retry_after is not None:
            details["retry_after"] = final_retry_after

        if quota_type:
            details["quota_type"] = quota_type

        if final_help_url:
            details["help_url"] = final_help_url

        if final_suggestions:
            details["suggestions"] = final_suggestions

        if original_error:
            details["original_error"] = original_error

        # Generate Chinese message
        message = f"{display_name} API 配額已用盡"

        super().__init__(
            code=ErrorCode.QUOTA_EXCEEDED,
            message=message,
            details=details,
            status_code=429,
        )

"""Speechmatics API Key Validator."""

import httpx

from src.infrastructure.providers.validators.base import (
    BaseProviderValidator,
    ValidationResult,
)

# HTTP status codes for rate limiting
RATE_LIMIT_STATUS_CODES = (429, 503)


class SpeechmaticsValidator(BaseProviderValidator):
    """Validator for Speechmatics API keys.

    Uses the GET /v2/jobs endpoint to validate keys.
    """

    BASE_URL = "https://asr.api.speechmatics.com/v2"

    @property
    def provider_id(self) -> str:
        return "speechmatics"

    async def validate(self, api_key: str) -> ValidationResult:
        """Validate a Speechmatics API key."""
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(
                    f"{self.BASE_URL}/jobs",
                    headers={"Authorization": f"Bearer {api_key}"},
                    params={"limit": 1},
                )

                if response.status_code == 200:
                    return ValidationResult(is_valid=True)
                elif response.status_code == 401:
                    return ValidationResult(
                        is_valid=False,
                        error_message="Invalid API key",
                    )
                elif response.status_code == 403:
                    return ValidationResult(
                        is_valid=False,
                        error_message="API key forbidden - check permissions",
                    )
                elif response.status_code in RATE_LIMIT_STATUS_CODES:
                    retry_after = response.headers.get("Retry-After", "unknown")
                    return ValidationResult(
                        is_valid=False,
                        error_message=f"Rate limited. Please retry after {retry_after} seconds",
                    )
                else:
                    return ValidationResult(
                        is_valid=False,
                        error_message=f"Validation failed with status {response.status_code}",
                    )
        except httpx.TimeoutException:
            return ValidationResult(
                is_valid=False,
                error_message="Request timed out",
            )
        except httpx.RequestError as e:
            return ValidationResult(
                is_valid=False,
                error_message=f"Network error: {str(e)}",
            )

    async def get_available_models(self, api_key: str) -> list[dict]:  # noqa: ARG002
        """Get available models from Speechmatics.

        Speechmatics uses operating points rather than discrete models.
        Returns operating point options as models.
        """
        return [
            {
                "id": "enhanced",
                "name": "Enhanced",
                "language": "multilingual",
                "gender": None,
                "description": "Highest accuracy model with enhanced operating point",
            },
            {
                "id": "standard",
                "name": "Standard",
                "language": "multilingual",
                "gender": None,
                "description": "Standard operating point for cost-effective transcription",
            },
        ]

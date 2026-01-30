"""VoAI API Key Validator."""

import httpx

from src.infrastructure.providers.validators.base import (
    BaseProviderValidator,
    ValidationResult,
)

# HTTP status codes for rate limiting
RATE_LIMIT_STATUS_CODES = (429, 503)


class VoAIValidator(BaseProviderValidator):
    """Validator for VoAI API keys.

    Uses the GET /api/v1/voices endpoint to validate keys.
    """

    BASE_URL = "https://connect.voai.ai/api/v1"

    @property
    def provider_id(self) -> str:
        return "voai"

    async def validate(self, api_key: str) -> ValidationResult:
        """Validate a VoAI API key."""
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(
                    f"{self.BASE_URL}/voices",
                    headers={"Authorization": f"Bearer {api_key}"},
                )

                if response.status_code == 200:
                    return ValidationResult(is_valid=True)
                elif response.status_code == 401:
                    return ValidationResult(
                        is_valid=False,
                        error_message="Invalid API key",
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

    async def get_available_models(self, api_key: str) -> list[dict]:
        """Get available voices from VoAI."""
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(
                    f"{self.BASE_URL}/voices",
                    headers={"Authorization": f"Bearer {api_key}"},
                )

                if response.status_code == 200:
                    data = response.json()
                    voices = data if isinstance(data, list) else data.get("voices", [])
                    return [
                        {
                            "id": voice.get("id") or voice.get("voice_id"),
                            "name": voice.get("name"),
                            "language": voice.get("language", "zh-TW"),
                            "gender": voice.get("gender"),
                            "description": voice.get("description"),
                        }
                        for voice in voices
                    ]
                return []
        except (httpx.TimeoutException, httpx.RequestError):
            return []

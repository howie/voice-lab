"""ElevenLabs API Key Validator."""

import httpx

from src.infrastructure.providers.validators.base import (
    BaseProviderValidator,
    ValidationResult,
)


class ElevenLabsValidator(BaseProviderValidator):
    """Validator for ElevenLabs API keys.

    Uses the GET /v1/user endpoint to validate keys,
    which returns user info if the key is valid.
    """

    BASE_URL = "https://api.elevenlabs.io/v1"

    @property
    def provider_id(self) -> str:
        return "elevenlabs"

    async def validate(self, api_key: str) -> ValidationResult:
        """Validate an ElevenLabs API key."""
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(
                    f"{self.BASE_URL}/user",
                    headers={"xi-api-key": api_key},
                )

                if response.status_code == 200:
                    user_data = response.json()
                    # Extract quota info if available
                    subscription = user_data.get("subscription", {})
                    quota_info = {
                        "character_count": subscription.get("character_count", 0),
                        "character_limit": subscription.get("character_limit", 0),
                    }
                    return ValidationResult(is_valid=True, quota_info=quota_info)
                elif response.status_code == 401:
                    return ValidationResult(
                        is_valid=False,
                        error_message="Invalid API key",
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
        """Get available voices from ElevenLabs."""
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(
                    f"{self.BASE_URL}/voices",
                    headers={"xi-api-key": api_key},
                )

                if response.status_code == 200:
                    data = response.json()
                    voices = data.get("voices", [])
                    return [
                        {
                            "id": voice.get("voice_id"),
                            "name": voice.get("name"),
                            "language": voice.get("labels", {}).get("language", "en"),
                            "gender": voice.get("labels", {}).get("gender"),
                            "description": voice.get("description"),
                        }
                        for voice in voices
                    ]
                return []
        except (httpx.TimeoutException, httpx.RequestError):
            return []

"""Google Cloud Platform API Key Validator."""

import httpx

from src.infrastructure.providers.validators.base import (
    BaseProviderValidator,
    ValidationResult,
)

# HTTP status codes for rate limiting
RATE_LIMIT_STATUS_CODES = (429, 503)


class GCPValidator(BaseProviderValidator):
    """Validator for GCP API keys.

    Uses the Text-to-Speech API voices endpoint to validate keys.
    """

    BASE_URL = "https://texttospeech.googleapis.com/v1"

    @property
    def provider_id(self) -> str:
        return "gcp"

    async def validate(self, api_key: str) -> ValidationResult:
        """Validate a GCP API key."""
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(
                    f"{self.BASE_URL}/voices",
                    params={"key": api_key},
                )

                if response.status_code == 200:
                    return ValidationResult(is_valid=True)
                elif response.status_code == 400:
                    error_data = response.json()
                    error_msg = error_data.get("error", {}).get("message", "Invalid API key")
                    return ValidationResult(
                        is_valid=False,
                        error_message=error_msg,
                    )
                elif response.status_code == 403:
                    return ValidationResult(
                        is_valid=False,
                        error_message="API key forbidden - check permissions or enable the API",
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
        """Get available voices from GCP TTS."""
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(
                    f"{self.BASE_URL}/voices",
                    params={"key": api_key},
                )

                if response.status_code == 200:
                    data = response.json()
                    voices = data.get("voices", [])
                    return [
                        {
                            "id": voice.get("name"),
                            "name": voice.get("name"),
                            "language": ",".join(voice.get("languageCodes", [])),
                            "gender": voice.get("ssmlGender", "").lower(),
                            "description": voice.get("naturalSampleRateHertz"),
                        }
                        for voice in voices
                    ]
                return []
        except (httpx.TimeoutException, httpx.RequestError):
            return []

"""Azure Cognitive Services API Key Validator."""

import httpx

from src.infrastructure.providers.validators.base import (
    BaseProviderValidator,
    ValidationResult,
)


class AzureValidator(BaseProviderValidator):
    """Validator for Azure Cognitive Services API keys.

    Uses the GET /cognitiveservices/voices/list endpoint to validate keys,
    which returns available voices if the key is valid.
    """

    # Default region - can be overridden
    DEFAULT_REGION = "eastus"

    @property
    def provider_id(self) -> str:
        return "azure"

    def _get_base_url(self, region: str | None = None) -> str:
        """Get the base URL for the Azure Speech API."""
        region = region or self.DEFAULT_REGION
        return f"https://{region}.tts.speech.microsoft.com/cognitiveservices"

    async def validate(self, api_key: str, region: str | None = None) -> ValidationResult:
        """Validate an Azure Speech API key.

        Note: Azure keys are region-specific. The key format may include region info,
        or it can be passed separately.
        """
        # Check if api_key contains region (format: key:region)
        if ":" in api_key:
            key_part, region_part = api_key.split(":", 1)
            api_key = key_part
            region = region_part

        base_url = self._get_base_url(region)

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(
                    f"{base_url}/voices/list",
                    headers={
                        "Ocp-Apim-Subscription-Key": api_key,
                    },
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
                        error_message="API key forbidden - check permissions or quota",
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

    async def get_available_models(
        self, api_key: str, region: str | None = None, language: str | None = None
    ) -> list[dict]:
        """Get available voices from Azure."""
        # Check if api_key contains region
        if ":" in api_key:
            key_part, region_part = api_key.split(":", 1)
            api_key = key_part
            region = region_part

        base_url = self._get_base_url(region)

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(
                    f"{base_url}/voices/list",
                    headers={
                        "Ocp-Apim-Subscription-Key": api_key,
                    },
                )

                if response.status_code == 200:
                    voices = response.json()
                    result = []
                    for voice in voices:
                        voice_language = voice.get("Locale", "")
                        # Filter by language if specified
                        if language and not voice_language.startswith(language):
                            continue
                        result.append(
                            {
                                "id": voice.get("ShortName"),
                                "name": voice.get("DisplayName"),
                                "language": voice_language,
                                "gender": voice.get("Gender", "").lower(),
                                "description": voice.get("VoiceType"),
                            }
                        )
                    return result
                return []
        except (httpx.TimeoutException, httpx.RequestError):
            return []

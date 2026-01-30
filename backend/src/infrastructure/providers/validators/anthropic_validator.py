"""Anthropic API Key Validator."""

import httpx

from src.infrastructure.providers.validators.base import (
    BaseProviderValidator,
    ValidationResult,
)

# HTTP status codes for rate limiting
RATE_LIMIT_STATUS_CODES = (429, 529)


class AnthropicValidator(BaseProviderValidator):
    """Validator for Anthropic API keys.

    Uses the GET /v1/models endpoint to validate keys.
    """

    BASE_URL = "https://api.anthropic.com/v1"

    @property
    def provider_id(self) -> str:
        return "anthropic"

    async def validate(self, api_key: str) -> ValidationResult:
        """Validate an Anthropic API key."""
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(
                    f"{self.BASE_URL}/models",
                    headers={
                        "x-api-key": api_key,
                        "anthropic-version": "2023-06-01",
                    },
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
        """Get available models from Anthropic."""
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(
                    f"{self.BASE_URL}/models",
                    headers={
                        "x-api-key": api_key,
                        "anthropic-version": "2023-06-01",
                    },
                )

                if response.status_code == 200:
                    data = response.json()
                    models = data.get("data", [])
                    return [
                        {
                            "id": model.get("id"),
                            "name": model.get("display_name") or model.get("id"),
                            "language": "multilingual",
                            "gender": None,
                            "description": model.get("type"),
                        }
                        for model in models
                    ]
                return []
        except (httpx.TimeoutException, httpx.RequestError):
            return []

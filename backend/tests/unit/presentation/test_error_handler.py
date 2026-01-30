"""Unit tests for QuotaExceededError handler in error_handler middleware.

T007: Unit test for error handler quota response
"""

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from src.domain.errors import QuotaExceededError
from src.presentation.api.middleware.error_handler import setup_error_handlers


@pytest.fixture()
def app() -> FastAPI:
    """Create a test FastAPI app with error handlers."""
    app = FastAPI()
    setup_error_handlers(app)

    @app.get("/test-quota-error")
    async def raise_quota_error():
        raise QuotaExceededError(provider="gemini")

    @app.get("/test-quota-error-custom")
    async def raise_quota_error_custom():
        raise QuotaExceededError(
            provider="elevenlabs",
            retry_after=7200,
            quota_type="characters",
            original_error="Character limit exceeded",
        )

    @app.get("/test-quota-error-unknown")
    async def raise_quota_error_unknown():
        raise QuotaExceededError(provider="unknown_provider")

    return app


@pytest.fixture()
async def client(app: FastAPI) -> AsyncClient:
    """Create an async test client."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client


class TestQuotaExceededErrorHandler:
    """T007: Unit tests for error handler quota response."""

    @pytest.mark.asyncio()
    async def test_returns_429_status(self, client: AsyncClient) -> None:
        """Quota error should return HTTP 429 status code."""
        response = await client.get("/test-quota-error")
        assert response.status_code == 429

    @pytest.mark.asyncio()
    async def test_response_has_quota_exceeded_code(self, client: AsyncClient) -> None:
        """Response body should contain QUOTA_EXCEEDED error code."""
        response = await client.get("/test-quota-error")
        body = response.json()

        assert body["error"]["code"] == "QUOTA_EXCEEDED"

    @pytest.mark.asyncio()
    async def test_response_has_chinese_message(self, client: AsyncClient) -> None:
        """Response message should be in Chinese."""
        response = await client.get("/test-quota-error")
        body = response.json()

        assert "配額已用盡" in body["error"]["message"]
        assert "Gemini TTS" in body["error"]["message"]

    @pytest.mark.asyncio()
    async def test_response_has_provider_details(self, client: AsyncClient) -> None:
        """Response should include provider details."""
        response = await client.get("/test-quota-error")
        body = response.json()
        details = body["error"]["details"]

        assert details["provider"] == "gemini"
        assert details["provider_display_name"] == "Gemini TTS"

    @pytest.mark.asyncio()
    async def test_retry_after_header_present(self, client: AsyncClient) -> None:
        """Retry-After header should be present with correct value."""
        response = await client.get("/test-quota-error")

        assert "retry-after" in response.headers
        assert response.headers["retry-after"] == "3600"

    @pytest.mark.asyncio()
    async def test_custom_retry_after_header(self, client: AsyncClient) -> None:
        """Custom retry_after should be reflected in Retry-After header."""
        response = await client.get("/test-quota-error-custom")

        assert response.headers["retry-after"] == "7200"

    @pytest.mark.asyncio()
    async def test_response_has_suggestions(self, client: AsyncClient) -> None:
        """Response should include suggestions list."""
        response = await client.get("/test-quota-error")
        body = response.json()
        details = body["error"]["details"]

        assert "suggestions" in details
        assert isinstance(details["suggestions"], list)
        assert len(details["suggestions"]) > 0

    @pytest.mark.asyncio()
    async def test_response_has_help_url(self, client: AsyncClient) -> None:
        """Response should include help_url."""
        response = await client.get("/test-quota-error")
        body = response.json()
        details = body["error"]["details"]

        assert "help_url" in details
        assert details["help_url"] == "https://ai.google.dev/pricing"

    @pytest.mark.asyncio()
    async def test_custom_fields_in_response(self, client: AsyncClient) -> None:
        """Custom fields should appear in response details."""
        response = await client.get("/test-quota-error-custom")
        body = response.json()
        details = body["error"]["details"]

        assert details["quota_type"] == "characters"
        assert details["original_error"] == "Character limit exceeded"

    @pytest.mark.asyncio()
    async def test_unknown_provider_still_returns_429(self, client: AsyncClient) -> None:
        """Unknown provider should still return 429 with fallback info."""
        response = await client.get("/test-quota-error-unknown")

        assert response.status_code == 429
        body = response.json()
        assert body["error"]["code"] == "QUOTA_EXCEEDED"

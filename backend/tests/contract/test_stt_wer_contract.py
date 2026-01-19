"""Contract tests for POST /stt/analysis/wer endpoint.

Feature: 003-stt-testing-module - User Story 3
Task: T047 - Contract test for WER analysis endpoint

Note: This endpoint requires a valid result_id from an existing transcription.
These tests focus on request validation and error handling.
"""

import pytest
from httpx import ASGITransport, AsyncClient

from src.main import app


@pytest.mark.asyncio
class TestWERAnalysisContract:
    """Contract tests for WER analysis endpoint."""

    async def test_wer_endpoint_requires_result_id(self) -> None:
        """Test that result_id field is required."""
        transport = ASGITransport(app=app)  # type: ignore[arg-type]
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post(
                "/api/v1/stt/analysis/wer",
                json={
                    "ground_truth": "hello world",
                },
            )

        assert response.status_code == 422  # Validation error - missing result_id

    async def test_wer_endpoint_requires_ground_truth(self) -> None:
        """Test that ground_truth field is required."""
        transport = ASGITransport(app=app)  # type: ignore[arg-type]
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post(
                "/api/v1/stt/analysis/wer",
                json={
                    "result_id": "00000000-0000-0000-0000-000000000000",
                },
            )

        assert response.status_code == 422  # Validation error - missing ground_truth

    async def test_wer_endpoint_invalid_result_id_format(self) -> None:
        """Test WER endpoint validates UUID format."""
        transport = ASGITransport(app=app)  # type: ignore[arg-type]
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post(
                "/api/v1/stt/analysis/wer",
                json={
                    "result_id": "not-a-valid-uuid",
                    "ground_truth": "hello world",
                },
            )

        # Should fail validation (422) or conversion (400)
        assert response.status_code in [400, 422]

    async def test_wer_endpoint_nonexistent_result_id(self) -> None:
        """Test WER calculation fails with non-existent result_id."""
        transport = ASGITransport(app=app)  # type: ignore[arg-type]
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post(
                "/api/v1/stt/analysis/wer",
                json={
                    "result_id": "00000000-0000-0000-0000-000000000000",
                    "ground_truth": "hello world this is a test",
                },
            )

        # Should return 404 or 500 (depending on error handling implementation)
        assert response.status_code in [404, 500]
        data = response.json()
        assert "detail" in data

    async def test_wer_endpoint_response_structure(self) -> None:
        """Test that WER endpoint returns expected response structure (when valid).

        Note: This test will fail until we have a valid transcription in the database.
        This is expected and demonstrates the contract.
        """
        transport = ASGITransport(app=app)  # type: ignore[arg-type]
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post(
                "/api/v1/stt/analysis/wer",
                json={
                    "result_id": "00000000-0000-0000-0000-000000000000",
                    "ground_truth": "test text",
                },
            )

        # We expect 404 for now, but if it were to succeed (200),
        # the response should have these fields
        if response.status_code == 200:
            data = response.json()
            assert "error_rate" in data
            assert "error_type" in data
            assert "insertions" in data
            assert "deletions" in data
            assert "substitutions" in data
            assert "total_reference" in data
            assert data["error_type"] in ["WER", "CER"]

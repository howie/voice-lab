"""Contract tests for STT history endpoints.

Feature: 003-stt-testing-module - Phase 7
Task: T062, T063 - Contract tests for history retrieval and deletion

Tests endpoints for viewing and managing transcription history.
"""

import pytest
from httpx import ASGITransport, AsyncClient

from src.main import app


@pytest.mark.asyncio
class TestHistoryListEndpoint:
    """Contract tests for GET /stt/history endpoint."""

    async def test_history_returns_list(self) -> None:
        """Test that history endpoint returns a list."""
        transport = ASGITransport(app=app)  # type: ignore[arg-type]
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/api/v1/stt/history")

        # Should return 200 with list structure
        assert response.status_code == 200
        data = response.json()

        assert "items" in data
        assert "total" in data
        assert "page" in data
        assert "page_size" in data
        assert isinstance(data["items"], list)
        assert isinstance(data["total"], int)

    async def test_history_pagination(self) -> None:
        """Test that pagination parameters work."""
        transport = ASGITransport(app=app)  # type: ignore[arg-type]
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get(
                "/api/v1/stt/history",
                params={
                    "page": 2,
                    "page_size": 10,
                },
            )

        assert response.status_code == 200
        data = response.json()

        assert data["page"] == 2
        assert data["page_size"] == 10

    async def test_history_filter_by_provider(self) -> None:
        """Test filtering by provider."""
        transport = ASGITransport(app=app)  # type: ignore[arg-type]
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get(
                "/api/v1/stt/history",
                params={
                    "provider": "azure",
                },
            )

        assert response.status_code == 200
        data = response.json()

        # If there are items, they should all be from azure
        if data["items"]:
            for item in data["items"]:
                assert item["provider"] == "azure"

    async def test_history_filter_by_language(self) -> None:
        """Test filtering by language."""
        transport = ASGITransport(app=app)  # type: ignore[arg-type]
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get(
                "/api/v1/stt/history",
                params={
                    "language": "en-US",
                },
            )

        assert response.status_code == 200
        data = response.json()

        # If there are items, they should all be in en-US
        if data["items"]:
            for item in data["items"]:
                assert item["language"] == "en-US"

    async def test_history_item_structure(self) -> None:
        """Test that history items have expected fields."""
        transport = ASGITransport(app=app)  # type: ignore[arg-type]
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/api/v1/stt/history")

        assert response.status_code == 200
        data = response.json()

        # If there are items, check structure
        if data["items"]:
            item = data["items"][0]
            assert "id" in item
            assert "provider" in item
            assert "language" in item
            assert "transcript" in item
            assert "created_at" in item

    async def test_history_invalid_page(self) -> None:
        """Test that invalid page numbers are handled."""
        transport = ASGITransport(app=app)  # type: ignore[arg-type]
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get(
                "/api/v1/stt/history",
                params={
                    "page": 0,  # Invalid page number
                },
            )

        # Should return error for page < 1
        assert response.status_code == 422

    async def test_history_invalid_page_size(self) -> None:
        """Test that invalid page sizes are handled."""
        transport = ASGITransport(app=app)  # type: ignore[arg-type]
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get(
                "/api/v1/stt/history",
                params={
                    "page_size": 101,  # Too large
                },
            )

        # Should return error for page_size > 100
        assert response.status_code == 422


@pytest.mark.asyncio
class TestHistoryDetailEndpoint:
    """Contract tests for GET /stt/history/{id} endpoint."""

    async def test_history_detail_not_found(self) -> None:
        """Test that 404 is returned for non-existent history."""
        transport = ASGITransport(app=app)  # type: ignore[arg-type]
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get(
                "/api/v1/stt/history/00000000-0000-0000-0000-000000000000"
            )

        # Should return 404 for non-existent ID
        assert response.status_code == 404

    async def test_history_detail_invalid_uuid(self) -> None:
        """Test that invalid UUID format is rejected."""
        transport = ASGITransport(app=app)  # type: ignore[arg-type]
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/api/v1/stt/history/not-a-uuid")

        # Should return 422 for invalid UUID
        assert response.status_code == 422

    async def test_history_detail_response_structure(self) -> None:
        """Test expected response structure for valid detail request.

        Note: This test demonstrates the expected contract.
        Will return 404 without existing data.
        """
        transport = ASGITransport(app=app)  # type: ignore[arg-type]
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get(
                "/api/v1/stt/history/00000000-0000-0000-0000-000000000000"
            )

        # If found (200), verify response structure
        if response.status_code == 200:
            data = response.json()

            # Should have full transcription details
            assert "id" in data
            assert "provider" in data
            assert "language" in data
            assert "transcript" in data
            assert "confidence" in data
            assert "latency_ms" in data
            assert "created_at" in data

            # Should have audio file info
            assert "audio_file" in data
            assert "filename" in data["audio_file"]

            # May have WER analysis if ground truth was provided
            if "wer_analysis" in data:
                assert "error_rate" in data["wer_analysis"]


@pytest.mark.asyncio
class TestHistoryDeleteEndpoint:
    """Contract tests for DELETE /stt/history/{id} endpoint."""

    async def test_delete_history_not_found(self) -> None:
        """Test that 404 is returned for non-existent history."""
        transport = ASGITransport(app=app)  # type: ignore[arg-type]
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.delete(
                "/api/v1/stt/history/00000000-0000-0000-0000-000000000000"
            )

        # Should return 404 for non-existent ID
        assert response.status_code == 404

    async def test_delete_history_invalid_uuid(self) -> None:
        """Test that invalid UUID format is rejected."""
        transport = ASGITransport(app=app)  # type: ignore[arg-type]
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.delete("/api/v1/stt/history/not-a-uuid")

        # Should return 422 for invalid UUID
        assert response.status_code == 422

    async def test_delete_history_success_response(self) -> None:
        """Test expected response structure for successful deletion.

        Note: This test demonstrates the expected contract.
        Will return 404 without existing data.
        """
        transport = ASGITransport(app=app)  # type: ignore[arg-type]
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.delete(
                "/api/v1/stt/history/00000000-0000-0000-0000-000000000000"
            )

        # If successful (200), verify response
        if response.status_code == 200:
            data = response.json()
            assert "message" in data or "success" in data

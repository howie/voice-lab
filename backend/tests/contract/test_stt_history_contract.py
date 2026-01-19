"""Contract tests for STT history endpoints.

Feature: 003-stt-testing-module - Phase 7
Task: T062, T063 - Contract tests for history retrieval and deletion

Tests endpoints for viewing and managing transcription history.
"""

import uuid
from unittest.mock import AsyncMock

import pytest
from httpx import ASGITransport, AsyncClient

from src.infrastructure.persistence.database import get_db_session
from src.main import app
from src.presentation.api.dependencies import get_transcription_repository
from src.presentation.api.middleware.auth import CurrentUser, get_current_user


@pytest.fixture
def mock_current_user() -> CurrentUser:
    """Create a mock current user."""
    return CurrentUser(
        id="00000000-0000-0000-0000-000000000001",
        email="test@example.com",
        name="Test User",
        picture_url=None,
        google_id="test-google-id",
    )


@pytest.mark.asyncio
class TestHistoryListEndpoint:
    """Contract tests for GET /stt/history endpoint."""

    @pytest.fixture(autouse=True)
    def setup_dependencies(self, mock_current_user: CurrentUser):
        """Override dependencies for all tests."""
        mock_session = AsyncMock()
        mock_session.commit = AsyncMock()
        mock_session.flush = AsyncMock()

        async def get_mock_session():
            yield mock_session

        async def get_mock_current_user():
            return mock_current_user

        app.dependency_overrides[get_db_session] = get_mock_session
        app.dependency_overrides[get_current_user] = get_mock_current_user
        yield
        app.dependency_overrides.clear()

    async def test_history_returns_list(self) -> None:
        """Test that history endpoint returns a list."""
        # Mock repository
        mock_repo = AsyncMock()
        mock_repo.list_transcriptions.return_value = ([], 0)

        app.dependency_overrides[get_transcription_repository] = lambda: mock_repo

        try:
            transport = ASGITransport(app=app)
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
        finally:
            app.dependency_overrides.pop(get_transcription_repository, None)

    async def test_history_pagination(self) -> None:
        """Test that pagination parameters work."""
        # Mock repository
        mock_repo = AsyncMock()
        mock_repo.list_transcriptions.return_value = ([], 0)

        app.dependency_overrides[get_transcription_repository] = lambda: mock_repo

        try:
            transport = ASGITransport(app=app)
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

            # Verify repository was called with correct parameters
            call_kwargs = mock_repo.list_transcriptions.call_args[1]
            assert call_kwargs["page"] == 2
            assert call_kwargs["page_size"] == 10
        finally:
            app.dependency_overrides.pop(get_transcription_repository, None)

    async def test_history_filter_by_provider(self) -> None:
        """Test filtering by provider."""
        # Mock repository with Azure-filtered results
        mock_items = [
            {
                "id": str(uuid.uuid4()),
                "provider": "azure",
                "language": "en-US",
                "transcript_preview": "test",
                "duration_ms": 5000,
                "confidence": 0.95,
                "has_ground_truth": False,
                "error_rate": None,
                "created_at": "2024-01-01T00:00:00Z",
            }
        ]
        mock_repo = AsyncMock()
        mock_repo.list_transcriptions.return_value = (mock_items, 1)

        app.dependency_overrides[get_transcription_repository] = lambda: mock_repo

        try:
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                response = await client.get(
                    "/api/v1/stt/history",
                    params={
                        "provider": "azure",
                    },
                )

            assert response.status_code == 200
            data = response.json()

            # Verify repository was called with provider filter
            call_kwargs = mock_repo.list_transcriptions.call_args[1]
            assert call_kwargs["provider"] == "azure"

            # If there are items, they should all be from azure
            if data["items"]:
                for item in data["items"]:
                    assert item["provider"] == "azure"
        finally:
            app.dependency_overrides.pop(get_transcription_repository, None)

    async def test_history_filter_by_language(self) -> None:
        """Test filtering by language."""
        # Mock repository with language-filtered results
        mock_items = [
            {
                "id": str(uuid.uuid4()),
                "provider": "azure",
                "language": "en-US",
                "transcript_preview": "test",
                "duration_ms": 5000,
                "confidence": 0.95,
                "has_ground_truth": False,
                "error_rate": None,
                "created_at": "2024-01-01T00:00:00Z",
            }
        ]
        mock_repo = AsyncMock()
        mock_repo.list_transcriptions.return_value = (mock_items, 1)

        app.dependency_overrides[get_transcription_repository] = lambda: mock_repo

        try:
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                response = await client.get(
                    "/api/v1/stt/history",
                    params={
                        "language": "en-US",
                    },
                )

            assert response.status_code == 200
            data = response.json()

            # Verify repository was called with language filter
            call_kwargs = mock_repo.list_transcriptions.call_args[1]
            assert call_kwargs["language"] == "en-US"

            # If there are items, they should all be in en-US
            if data["items"]:
                for item in data["items"]:
                    assert item["language"] == "en-US"
        finally:
            app.dependency_overrides.pop(get_transcription_repository, None)

    async def test_history_item_structure(self) -> None:
        """Test that history items have expected fields."""
        # Mock repository with sample item
        mock_items = [
            {
                "id": str(uuid.uuid4()),
                "provider": "azure",
                "language": "en-US",
                "transcript_preview": "test transcript",
                "duration_ms": 5000,
                "confidence": 0.95,
                "has_ground_truth": False,
                "error_rate": None,
                "created_at": "2024-01-01T00:00:00Z",
            }
        ]
        mock_repo = AsyncMock()
        mock_repo.list_transcriptions.return_value = (mock_items, 1)

        app.dependency_overrides[get_transcription_repository] = lambda: mock_repo

        try:
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                response = await client.get("/api/v1/stt/history")

            assert response.status_code == 200
            data = response.json()

            # Check structure
            assert len(data["items"]) > 0
            item = data["items"][0]
            assert "id" in item
            assert "provider" in item
            assert "language" in item
            assert "transcript_preview" in item
            assert "duration_ms" in item
            assert "confidence" in item
            assert "has_ground_truth" in item
            assert "created_at" in item
        finally:
            app.dependency_overrides.pop(get_transcription_repository, None)

    async def test_history_invalid_page(self) -> None:
        """Test that invalid page numbers are handled."""
        mock_repo = AsyncMock()
        mock_repo.list_transcriptions.return_value = ([], 0)
        app.dependency_overrides[get_transcription_repository] = lambda: mock_repo

        try:
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                response = await client.get(
                    "/api/v1/stt/history",
                    params={
                        "page": 0,  # Invalid page number
                    },
                )

            # Should return error for page < 1
            assert response.status_code == 422
        finally:
            app.dependency_overrides.pop(get_transcription_repository, None)

    async def test_history_invalid_page_size(self) -> None:
        """Test that invalid page sizes are handled."""
        mock_repo = AsyncMock()
        mock_repo.list_transcriptions.return_value = ([], 0)
        app.dependency_overrides[get_transcription_repository] = lambda: mock_repo

        try:
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                response = await client.get(
                    "/api/v1/stt/history",
                    params={
                        "page_size": 101,  # Too large
                    },
                )

            # Should return error for page_size > 100
            assert response.status_code == 422
        finally:
            app.dependency_overrides.pop(get_transcription_repository, None)


@pytest.mark.asyncio
class TestHistoryDetailEndpoint:
    """Contract tests for GET /stt/history/{id} endpoint."""

    @pytest.fixture(autouse=True)
    def setup_dependencies(self, mock_current_user: CurrentUser):
        """Override dependencies for all tests."""
        mock_session = AsyncMock()
        mock_session.commit = AsyncMock()
        mock_session.flush = AsyncMock()

        async def get_mock_session():
            yield mock_session

        async def get_mock_current_user():
            return mock_current_user

        app.dependency_overrides[get_db_session] = get_mock_session
        app.dependency_overrides[get_current_user] = get_mock_current_user
        yield
        app.dependency_overrides.clear()

    async def test_history_detail_not_found(self) -> None:
        """Test that 404 is returned for non-existent history."""
        # Mock repository returning None
        mock_repo = AsyncMock()
        mock_repo.get_transcription_detail.return_value = None

        app.dependency_overrides[get_transcription_repository] = lambda: mock_repo

        try:
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                response = await client.get(
                    "/api/v1/stt/history/00000000-0000-0000-0000-000000000000"
                )

            # Should return 404 for non-existent ID
            assert response.status_code == 404
        finally:
            app.dependency_overrides.pop(get_transcription_repository, None)

    async def test_history_detail_invalid_uuid(self) -> None:
        """Test that invalid UUID format is handled."""
        mock_repo = AsyncMock()
        app.dependency_overrides[get_transcription_repository] = lambda: mock_repo

        try:
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                response = await client.get("/api/v1/stt/history/invalid-uuid")

            # Should return 400 for invalid UUID
            assert response.status_code == 400
        finally:
            app.dependency_overrides.pop(get_transcription_repository, None)

    async def test_history_detail_response_structure(self) -> None:
        """Test that detail response has expected structure."""
        # Mock repository with detailed result
        audio_file_id = str(uuid.uuid4())
        mock_detail = {
            "id": str(uuid.uuid4()),
            "transcript": "detailed test transcript",
            "provider": "azure",
            "language": "en-US",
            "latency_ms": 150,
            "confidence": 0.95,
            "audio_duration_ms": 5000,
            "created_at": "2024-01-01T00:00:00Z",
            "audio_file": {
                "id": audio_file_id,
                "filename": "test.wav",
                "duration_ms": 5000,
                "format": "wav",
                "download_url": None,
            },
            "ground_truth": None,
            "child_mode": False,
        }
        mock_repo = AsyncMock()
        mock_repo.get_transcription_detail.return_value = mock_detail

        app.dependency_overrides[get_transcription_repository] = lambda: mock_repo

        try:
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                response = await client.get(f"/api/v1/stt/history/{mock_detail['id']}")

            assert response.status_code == 200
            data = response.json()

            # Verify structure
            assert "id" in data
            assert "provider" in data
            assert "language" in data
            assert "transcript" in data
            assert "created_at" in data
        finally:
            app.dependency_overrides.pop(get_transcription_repository, None)


@pytest.mark.asyncio
class TestHistoryDeleteEndpoint:
    """Contract tests for DELETE /stt/history/{id} endpoint."""

    @pytest.fixture(autouse=True)
    def setup_dependencies(self, mock_current_user: CurrentUser):
        """Override dependencies for all tests."""
        mock_session = AsyncMock()
        mock_session.commit = AsyncMock()
        mock_session.flush = AsyncMock()

        async def get_mock_session():
            yield mock_session

        async def get_mock_current_user():
            return mock_current_user

        app.dependency_overrides[get_db_session] = get_mock_session
        app.dependency_overrides[get_current_user] = get_mock_current_user
        yield
        app.dependency_overrides.clear()

    async def test_delete_history_not_found(self) -> None:
        """Test that 404 is returned when deleting non-existent history."""
        # Mock repository returning False (not found)
        mock_repo = AsyncMock()
        mock_repo.delete_transcription.return_value = False

        app.dependency_overrides[get_transcription_repository] = lambda: mock_repo

        try:
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                response = await client.delete(
                    "/api/v1/stt/history/00000000-0000-0000-0000-000000000000"
                )

            # Should return 404 for non-existent ID
            assert response.status_code == 404
        finally:
            app.dependency_overrides.pop(get_transcription_repository, None)

    async def test_delete_history_invalid_uuid(self) -> None:
        """Test that invalid UUID format is handled."""
        mock_repo = AsyncMock()
        app.dependency_overrides[get_transcription_repository] = lambda: mock_repo

        try:
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                response = await client.delete("/api/v1/stt/history/invalid-uuid")

            # Should return 400 for invalid UUID
            assert response.status_code == 400
        finally:
            app.dependency_overrides.pop(get_transcription_repository, None)

    async def test_delete_history_success_response(self) -> None:
        """Test successful deletion returns 204 No Content."""
        # Mock repository returning True (success)
        mock_repo = AsyncMock()
        mock_repo.delete_transcription.return_value = True

        app.dependency_overrides[get_transcription_repository] = lambda: mock_repo

        try:
            test_id = str(uuid.uuid4())
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                response = await client.delete(f"/api/v1/stt/history/{test_id}")

            # Should return 204 for successful deletion
            assert response.status_code == 204
            assert len(response.content) == 0  # No content in response
        finally:
            app.dependency_overrides.pop(get_transcription_repository, None)

"""Contract tests for Music Generation cancel/restart API endpoints.

Feature: 012-music-generation
Tests DELETE /music/jobs/{id} and POST /music/jobs/{id}/restart contracts.
"""

import uuid
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from httpx import ASGITransport, AsyncClient

from src.domain.entities.music import (
    MusicGenerationJob,
    MusicGenerationStatus,
    MusicGenerationType,
)
from src.main import app
from src.presentation.api.middleware.auth import CurrentUser, get_current_user

# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def mock_user_id() -> uuid.UUID:
    return uuid.UUID("12345678-1234-5678-1234-567812345678")


@pytest.fixture
def mock_current_user(mock_user_id: uuid.UUID) -> CurrentUser:
    return CurrentUser(
        id=str(mock_user_id),
        email="test@example.com",
        name="Test User",
        picture_url=None,
        google_id="test-google-id",
    )


def _make_music_job(
    user_id: uuid.UUID,
    status: MusicGenerationStatus = MusicGenerationStatus.PENDING,
    **kwargs,
) -> MusicGenerationJob:
    defaults = {
        "user_id": user_id,
        "type": MusicGenerationType.INSTRUMENTAL,
        "prompt": "test prompt for bgm generation",
        "model": "auto",
        "provider": "mureka",
    }
    defaults.update(kwargs)
    job = MusicGenerationJob(**defaults)
    job.status = status
    if status in (
        MusicGenerationStatus.COMPLETED,
        MusicGenerationStatus.FAILED,
        MusicGenerationStatus.CANCELLED,
    ):
        job.completed_at = datetime.utcnow()
    return job


def _setup_overrides(mock_current_user, mock_session):
    """Set up FastAPI dependency overrides for testing."""

    async def override_get_current_user():
        return mock_current_user

    async def override_get_db_session():
        return mock_session

    from src.presentation.api.routes import music as music_module

    app.dependency_overrides[get_current_user] = override_get_current_user
    app.dependency_overrides[music_module.get_db_session] = override_get_db_session


# =============================================================================
# DELETE /music/jobs/{id} — Cancel
# =============================================================================


class TestCancelMusicJob:
    """Contract tests for DELETE /api/v1/music/jobs/{id}."""

    @pytest.mark.asyncio
    async def test_cancel_pending_returns_200(
        self, mock_user_id: uuid.UUID, mock_current_user: CurrentUser
    ) -> None:
        """Cancel a pending job returns 200 with cancelled status."""
        job = _make_music_job(mock_user_id, MusicGenerationStatus.PENDING)
        mock_repo = AsyncMock()
        mock_repo.get_by_id.return_value = job
        mock_repo.update.return_value = job

        mock_session = MagicMock()
        mock_session.commit = AsyncMock()

        _setup_overrides(mock_current_user, mock_session)

        try:
            with (
                patch(
                    "src.presentation.api.routes.music.MusicGenerationJobRepository",
                    return_value=mock_repo,
                ),
                patch(
                    "src.presentation.api.routes.music.MusicProviderFactory",
                ),
            ):
                transport = ASGITransport(app=app)
                async with AsyncClient(transport=transport, base_url="http://test") as ac:
                    response = await ac.delete(f"/api/v1/music/jobs/{job.id}")

                assert response.status_code == 200
                data = response.json()
                assert data["status"] == "cancelled"
                assert data["id"] == str(job.id)
        finally:
            app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_cancel_completed_returns_409(
        self, mock_user_id: uuid.UUID, mock_current_user: CurrentUser
    ) -> None:
        """Cancel a completed job returns 409 Conflict."""
        job = _make_music_job(mock_user_id, MusicGenerationStatus.COMPLETED)
        mock_repo = AsyncMock()
        mock_repo.get_by_id.return_value = job

        mock_session = MagicMock()
        _setup_overrides(mock_current_user, mock_session)

        try:
            with (
                patch(
                    "src.presentation.api.routes.music.MusicGenerationJobRepository",
                    return_value=mock_repo,
                ),
                patch(
                    "src.presentation.api.routes.music.MusicProviderFactory",
                ),
            ):
                transport = ASGITransport(app=app)
                async with AsyncClient(transport=transport, base_url="http://test") as ac:
                    response = await ac.delete(f"/api/v1/music/jobs/{job.id}")

                assert response.status_code == 409
        finally:
            app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_cancel_nonexistent_returns_404(
        self, mock_user_id: uuid.UUID, mock_current_user: CurrentUser
    ) -> None:
        """Cancel a non-existent job returns 404."""
        mock_repo = AsyncMock()
        mock_repo.get_by_id.return_value = None

        mock_session = MagicMock()
        _setup_overrides(mock_current_user, mock_session)

        try:
            with (
                patch(
                    "src.presentation.api.routes.music.MusicGenerationJobRepository",
                    return_value=mock_repo,
                ),
                patch(
                    "src.presentation.api.routes.music.MusicProviderFactory",
                ),
            ):
                transport = ASGITransport(app=app)
                async with AsyncClient(transport=transport, base_url="http://test") as ac:
                    response = await ac.delete(f"/api/v1/music/jobs/{uuid.uuid4()}")

                assert response.status_code == 404
        finally:
            app.dependency_overrides.clear()


# =============================================================================
# POST /music/jobs/{id}/restart — Restart
# =============================================================================


class TestRestartMusicJob:
    """Contract tests for POST /api/v1/music/jobs/{id}/restart."""

    @pytest.mark.asyncio
    async def test_restart_cancelled_returns_201(
        self, mock_user_id: uuid.UUID, mock_current_user: CurrentUser
    ) -> None:
        """Restart a cancelled job returns 201 with new pending job."""
        original = _make_music_job(mock_user_id, MusicGenerationStatus.CANCELLED)
        mock_repo = AsyncMock()
        mock_repo.get_by_id.return_value = original
        mock_repo.count_daily_usage.return_value = 0
        mock_repo.count_monthly_usage.return_value = 0
        mock_repo.count_active_jobs.return_value = 0
        # Return the new job that was passed to save
        mock_repo.save.side_effect = lambda j: j

        mock_session = MagicMock()
        mock_session.commit = AsyncMock()

        _setup_overrides(mock_current_user, mock_session)

        try:
            with (
                patch(
                    "src.presentation.api.routes.music.MusicGenerationJobRepository",
                    return_value=mock_repo,
                ),
                patch(
                    "src.presentation.api.routes.music.MusicProviderFactory",
                ),
            ):
                transport = ASGITransport(app=app)
                async with AsyncClient(transport=transport, base_url="http://test") as ac:
                    response = await ac.post(f"/api/v1/music/jobs/{original.id}/restart")

                assert response.status_code == 201
                data = response.json()
                assert data["status"] == "pending"
                # New job should have a different ID
                assert data["id"] != str(original.id)
        finally:
            app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_restart_pending_returns_400(
        self, mock_user_id: uuid.UUID, mock_current_user: CurrentUser
    ) -> None:
        """Restart a pending job returns 400 Bad Request."""
        job = _make_music_job(mock_user_id, MusicGenerationStatus.PENDING)
        mock_repo = AsyncMock()
        mock_repo.get_by_id.return_value = job

        mock_session = MagicMock()
        _setup_overrides(mock_current_user, mock_session)

        try:
            with (
                patch(
                    "src.presentation.api.routes.music.MusicGenerationJobRepository",
                    return_value=mock_repo,
                ),
                patch(
                    "src.presentation.api.routes.music.MusicProviderFactory",
                ),
            ):
                transport = ASGITransport(app=app)
                async with AsyncClient(transport=transport, base_url="http://test") as ac:
                    response = await ac.post(f"/api/v1/music/jobs/{job.id}/restart")

                assert response.status_code == 400
        finally:
            app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_restart_quota_exceeded_returns_429(
        self, mock_user_id: uuid.UUID, mock_current_user: CurrentUser
    ) -> None:
        """Restart with quota exceeded returns 429."""
        job = _make_music_job(mock_user_id, MusicGenerationStatus.CANCELLED)
        mock_repo = AsyncMock()
        mock_repo.get_by_id.return_value = job
        mock_repo.count_daily_usage.return_value = 0
        mock_repo.count_monthly_usage.return_value = 0
        mock_repo.count_active_jobs.return_value = 999  # Exceed concurrent limit

        mock_session = MagicMock()
        _setup_overrides(mock_current_user, mock_session)

        try:
            with (
                patch(
                    "src.presentation.api.routes.music.MusicGenerationJobRepository",
                    return_value=mock_repo,
                ),
                patch(
                    "src.presentation.api.routes.music.MusicProviderFactory",
                ),
            ):
                transport = ASGITransport(app=app)
                async with AsyncClient(transport=transport, base_url="http://test") as ac:
                    response = await ac.post(f"/api/v1/music/jobs/{job.id}/restart")

                assert response.status_code == 429
        finally:
            app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_restart_nonexistent_returns_404(
        self, mock_user_id: uuid.UUID, mock_current_user: CurrentUser
    ) -> None:
        """Restart a non-existent job returns 404."""
        mock_repo = AsyncMock()
        mock_repo.get_by_id.return_value = None

        mock_session = MagicMock()
        _setup_overrides(mock_current_user, mock_session)

        try:
            with (
                patch(
                    "src.presentation.api.routes.music.MusicGenerationJobRepository",
                    return_value=mock_repo,
                ),
                patch(
                    "src.presentation.api.routes.music.MusicProviderFactory",
                ),
            ):
                transport = ASGITransport(app=app)
                async with AsyncClient(transport=transport, base_url="http://test") as ac:
                    response = await ac.post(f"/api/v1/music/jobs/{uuid.uuid4()}/restart")

                assert response.status_code == 404
        finally:
            app.dependency_overrides.clear()

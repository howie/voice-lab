"""Contract tests for Jobs API endpoints.

Feature: 007-async-job-mgmt
Tests the async job management API contracts.
"""

import uuid
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from httpx import ASGITransport, AsyncClient

from src.domain.entities.job import Job, JobStatus, JobType
from src.main import app
from src.presentation.api.middleware.auth import CurrentUser, get_current_user

# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def mock_user_id() -> uuid.UUID:
    """Generate a mock user ID for testing."""
    return uuid.UUID("12345678-1234-5678-1234-567812345678")


@pytest.fixture
def mock_current_user(mock_user_id: uuid.UUID) -> CurrentUser:
    """Create a mock current user for authentication."""
    return CurrentUser(
        id=str(mock_user_id),
        email="test@example.com",
        name="Test User",
        picture_url=None,
        google_id="test-google-id",
    )


@pytest.fixture
def sample_create_job_request() -> dict:
    """Sample request payload for creating a job."""
    return {
        "provider": "azure",
        "turns": [
            {"speaker": "A", "text": "你好，很高興認識你！", "index": 0},
            {"speaker": "B", "text": "我也很高興認識你！", "index": 1},
        ],
        "voice_assignments": [
            {"speaker": "A", "voice_id": "zh-TW-HsiaoYuNeural", "voice_name": "曉雨"},
            {"speaker": "B", "voice_id": "zh-TW-YunJheNeural", "voice_name": "雲哲"},
        ],
        "language": "zh-TW",
        "output_format": "mp3",
        "gap_ms": 300,
        "crossfade_ms": 50,
    }


@pytest.fixture
def sample_job(mock_user_id: uuid.UUID, sample_create_job_request: dict) -> Job:
    """Create a sample job for testing."""
    return Job(
        id=uuid.uuid4(),
        user_id=mock_user_id,
        job_type=JobType.MULTI_ROLE_TTS,
        status=JobStatus.PENDING,
        provider="azure",
        input_params=sample_create_job_request,
        created_at=datetime.utcnow(),
    )


# =============================================================================
# T015: Contract test for POST /jobs endpoint (201 response)
# =============================================================================


class TestCreateJobEndpoint:
    """Contract tests for POST /api/v1/jobs endpoint."""

    @pytest.mark.asyncio
    async def test_create_job_success(
        self,
        mock_user_id: uuid.UUID,
        mock_current_user: CurrentUser,
        sample_create_job_request: dict,
        sample_job: Job,
    ):
        """T015: Test successful job creation returns 201."""
        mock_job_repo = AsyncMock()
        mock_job_repo.count_active_jobs.return_value = 0
        mock_job_repo.save.return_value = sample_job

        mock_session = MagicMock()
        mock_session.commit = AsyncMock()

        async def override_get_current_user():
            return mock_current_user

        async def override_get_db_session():
            return mock_session

        # Import the jobs router module to override its dependencies
        from src.presentation.api.routes import jobs as jobs_module

        app.dependency_overrides[get_current_user] = override_get_current_user
        app.dependency_overrides[jobs_module.get_db_session] = override_get_db_session

        try:
            with patch(
                "src.presentation.api.routes.jobs.JobRepositoryImpl",
                return_value=mock_job_repo,
            ):
                transport = ASGITransport(app=app)
                async with AsyncClient(transport=transport, base_url="http://test") as ac:
                    response = await ac.post(
                        "/api/v1/jobs",
                        json=sample_create_job_request,
                        headers={"X-User-Id": str(mock_user_id)},
                    )

                assert response.status_code == 201
                data = response.json()

                # Verify response structure
                assert "id" in data
                assert data["status"] == "pending"
                assert data["job_type"] == "multi_role_tts"
                assert data["provider"] == "azure"
                assert "created_at" in data
        finally:
            app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_create_job_invalid_request(
        self,
        mock_user_id: uuid.UUID,
        mock_current_user: CurrentUser,
    ):
        """T015: Test job creation with invalid request returns 422."""
        mock_session = MagicMock()

        async def override_get_current_user():
            return mock_current_user

        async def override_get_db_session():
            return mock_session

        from src.presentation.api.routes import jobs as jobs_module

        app.dependency_overrides[get_current_user] = override_get_current_user
        app.dependency_overrides[jobs_module.get_db_session] = override_get_db_session

        try:
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as ac:
                # Missing required fields
                response = await ac.post(
                    "/api/v1/jobs",
                    json={"provider": "azure"},  # Missing turns and voice_assignments
                    headers={"X-User-Id": str(mock_user_id)},
                )

            assert response.status_code == 422
        finally:
            app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_create_job_unauthorized(self):
        """T015: Test job creation without authentication returns 401."""
        from fastapi import HTTPException, status

        async def override_get_current_user():
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Not authenticated",
            )

        app.dependency_overrides[get_current_user] = override_get_current_user

        try:
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as ac:
                response = await ac.post(
                    "/api/v1/jobs",
                    json={
                        "provider": "azure",
                        "turns": [{"speaker": "A", "text": "test", "index": 0}],
                        "voice_assignments": [{"speaker": "A", "voice_id": "test"}],
                    },
                )

            assert response.status_code == 401
        finally:
            app.dependency_overrides.clear()


# =============================================================================
# T016: Contract test for job concurrent limit (429 response)
# =============================================================================


class TestJobConcurrentLimit:
    """Contract tests for job concurrent limit (429 response)."""

    @pytest.mark.asyncio
    async def test_create_job_exceeds_limit(
        self,
        mock_user_id: uuid.UUID,
        mock_current_user: CurrentUser,
        sample_create_job_request: dict,
    ):
        """T016: Test job creation returns 429 when concurrent limit exceeded."""
        mock_job_repo = AsyncMock()
        # Return 3 active jobs (at the limit)
        mock_job_repo.count_active_jobs.return_value = 3

        mock_session = MagicMock()
        mock_session.commit = AsyncMock()

        async def override_get_current_user():
            return mock_current_user

        async def override_get_db_session():
            return mock_session

        from src.presentation.api.routes import jobs as jobs_module

        app.dependency_overrides[get_current_user] = override_get_current_user
        app.dependency_overrides[jobs_module.get_db_session] = override_get_db_session

        try:
            with patch(
                "src.presentation.api.routes.jobs.JobRepositoryImpl",
                return_value=mock_job_repo,
            ):
                transport = ASGITransport(app=app)
                async with AsyncClient(transport=transport, base_url="http://test") as ac:
                    response = await ac.post(
                        "/api/v1/jobs",
                        json=sample_create_job_request,
                        headers={"X-User-Id": str(mock_user_id)},
                    )

                assert response.status_code == 429
                data = response.json()

                # Verify error response structure
                assert "error" in data or "detail" in data
        finally:
            app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_create_job_at_limit_boundary(
        self,
        mock_user_id: uuid.UUID,
        mock_current_user: CurrentUser,
        sample_create_job_request: dict,
        sample_job: Job,
    ):
        """T016: Test job creation succeeds at exactly limit - 1."""
        mock_job_repo = AsyncMock()
        # Return 2 active jobs (one below limit)
        mock_job_repo.count_active_jobs.return_value = 2
        mock_job_repo.save.return_value = sample_job

        mock_session = MagicMock()
        mock_session.commit = AsyncMock()

        async def override_get_current_user():
            return mock_current_user

        async def override_get_db_session():
            return mock_session

        from src.presentation.api.routes import jobs as jobs_module

        app.dependency_overrides[get_current_user] = override_get_current_user
        app.dependency_overrides[jobs_module.get_db_session] = override_get_db_session

        try:
            with patch(
                "src.presentation.api.routes.jobs.JobRepositoryImpl",
                return_value=mock_job_repo,
            ):
                transport = ASGITransport(app=app)
                async with AsyncClient(transport=transport, base_url="http://test") as ac:
                    response = await ac.post(
                        "/api/v1/jobs",
                        json=sample_create_job_request,
                        headers={"X-User-Id": str(mock_user_id)},
                    )

                # Should succeed since we're below the limit
                assert response.status_code == 201
        finally:
            app.dependency_overrides.clear()


# =============================================================================
# T030: Contract test for GET /jobs (list with pagination)
# =============================================================================


class TestListJobsEndpoint:
    """Contract tests for GET /api/v1/jobs endpoint."""

    @pytest.mark.asyncio
    async def test_list_jobs_success(
        self,
        mock_user_id: uuid.UUID,
        mock_current_user: CurrentUser,
        sample_job: Job,
    ):
        """T030: Test listing jobs returns 200 with pagination."""
        mock_job_repo = AsyncMock()
        mock_job_repo.get_by_user_id.return_value = [sample_job]
        mock_job_repo.count_by_user_and_status.return_value = 1

        mock_session = MagicMock()

        async def override_get_current_user():
            return mock_current_user

        async def override_get_db_session():
            return mock_session

        from src.presentation.api.routes import jobs as jobs_module

        app.dependency_overrides[get_current_user] = override_get_current_user
        app.dependency_overrides[jobs_module.get_db_session] = override_get_db_session

        try:
            with patch(
                "src.presentation.api.routes.jobs.JobRepositoryImpl",
                return_value=mock_job_repo,
            ):
                transport = ASGITransport(app=app)
                async with AsyncClient(transport=transport, base_url="http://test") as ac:
                    response = await ac.get(
                        "/api/v1/jobs",
                        headers={"X-User-Id": str(mock_user_id)},
                    )

                assert response.status_code == 200
                data = response.json()

                # Verify response structure
                assert "items" in data
                assert "total" in data
                assert "limit" in data
                assert "offset" in data
                assert isinstance(data["items"], list)
        finally:
            app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_list_jobs_with_status_filter(
        self,
        mock_user_id: uuid.UUID,
        mock_current_user: CurrentUser,
        sample_job: Job,
    ):
        """T030: Test listing jobs with status filter."""
        mock_job_repo = AsyncMock()
        mock_job_repo.get_by_user_id.return_value = [sample_job]
        mock_job_repo.count_by_user_and_status.return_value = 1

        mock_session = MagicMock()

        async def override_get_current_user():
            return mock_current_user

        async def override_get_db_session():
            return mock_session

        from src.presentation.api.routes import jobs as jobs_module

        app.dependency_overrides[get_current_user] = override_get_current_user
        app.dependency_overrides[jobs_module.get_db_session] = override_get_db_session

        try:
            with patch(
                "src.presentation.api.routes.jobs.JobRepositoryImpl",
                return_value=mock_job_repo,
            ):
                transport = ASGITransport(app=app)
                async with AsyncClient(transport=transport, base_url="http://test") as ac:
                    response = await ac.get(
                        "/api/v1/jobs?status=pending",
                        headers={"X-User-Id": str(mock_user_id)},
                    )

                assert response.status_code == 200
        finally:
            app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_list_jobs_with_pagination(
        self,
        mock_user_id: uuid.UUID,
        mock_current_user: CurrentUser,
    ):
        """T030: Test listing jobs with pagination parameters."""
        mock_job_repo = AsyncMock()
        mock_job_repo.get_by_user_id.return_value = []
        mock_job_repo.count_by_user_and_status.return_value = 0

        mock_session = MagicMock()

        async def override_get_current_user():
            return mock_current_user

        async def override_get_db_session():
            return mock_session

        from src.presentation.api.routes import jobs as jobs_module

        app.dependency_overrides[get_current_user] = override_get_current_user
        app.dependency_overrides[jobs_module.get_db_session] = override_get_db_session

        try:
            with patch(
                "src.presentation.api.routes.jobs.JobRepositoryImpl",
                return_value=mock_job_repo,
            ):
                transport = ASGITransport(app=app)
                async with AsyncClient(transport=transport, base_url="http://test") as ac:
                    response = await ac.get(
                        "/api/v1/jobs?limit=10&offset=20",
                        headers={"X-User-Id": str(mock_user_id)},
                    )

                assert response.status_code == 200
                data = response.json()
                assert data["limit"] == 10
                assert data["offset"] == 20
        finally:
            app.dependency_overrides.clear()


# =============================================================================
# T031: Contract test for GET /jobs/{id} (detail)
# =============================================================================


class TestGetJobDetailEndpoint:
    """Contract tests for GET /api/v1/jobs/{id} endpoint."""

    @pytest.mark.asyncio
    async def test_get_job_success(
        self,
        mock_user_id: uuid.UUID,
        mock_current_user: CurrentUser,
        sample_job: Job,
    ):
        """T031: Test getting job detail returns 200."""
        mock_job_repo = AsyncMock()
        mock_job_repo.get_by_id.return_value = sample_job

        mock_session = MagicMock()

        async def override_get_current_user():
            return mock_current_user

        async def override_get_db_session():
            return mock_session

        from src.presentation.api.routes import jobs as jobs_module

        app.dependency_overrides[get_current_user] = override_get_current_user
        app.dependency_overrides[jobs_module.get_db_session] = override_get_db_session

        try:
            with patch(
                "src.presentation.api.routes.jobs.JobRepositoryImpl",
                return_value=mock_job_repo,
            ):
                transport = ASGITransport(app=app)
                async with AsyncClient(transport=transport, base_url="http://test") as ac:
                    response = await ac.get(
                        f"/api/v1/jobs/{sample_job.id}",
                        headers={"X-User-Id": str(mock_user_id)},
                    )

                assert response.status_code == 200
                data = response.json()

                # Verify detail response structure
                assert data["id"] == str(sample_job.id)
                assert "input_params" in data
                assert "retry_count" in data
        finally:
            app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_get_job_not_found(
        self,
        mock_user_id: uuid.UUID,
        mock_current_user: CurrentUser,
    ):
        """T031: Test getting non-existent job returns 404."""
        mock_job_repo = AsyncMock()
        mock_job_repo.get_by_id.return_value = None

        mock_session = MagicMock()

        async def override_get_current_user():
            return mock_current_user

        async def override_get_db_session():
            return mock_session

        from src.presentation.api.routes import jobs as jobs_module

        app.dependency_overrides[get_current_user] = override_get_current_user
        app.dependency_overrides[jobs_module.get_db_session] = override_get_db_session

        try:
            with patch(
                "src.presentation.api.routes.jobs.JobRepositoryImpl",
                return_value=mock_job_repo,
            ):
                transport = ASGITransport(app=app)
                async with AsyncClient(transport=transport, base_url="http://test") as ac:
                    response = await ac.get(
                        f"/api/v1/jobs/{uuid.uuid4()}",
                        headers={"X-User-Id": str(mock_user_id)},
                    )

                assert response.status_code == 404
        finally:
            app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_get_job_wrong_user(
        self,
        mock_user_id: uuid.UUID,
        mock_current_user: CurrentUser,
        sample_job: Job,
    ):
        """T031: Test getting another user's job returns 404."""
        # Create job owned by different user
        other_user_job = Job(
            id=uuid.uuid4(),
            user_id=uuid.uuid4(),  # Different user
            job_type=JobType.MULTI_ROLE_TTS,
            status=JobStatus.PENDING,
            provider="azure",
            input_params={},
            created_at=datetime.utcnow(),
        )

        mock_job_repo = AsyncMock()
        mock_job_repo.get_by_id.return_value = other_user_job

        mock_session = MagicMock()

        async def override_get_current_user():
            return mock_current_user

        async def override_get_db_session():
            return mock_session

        from src.presentation.api.routes import jobs as jobs_module

        app.dependency_overrides[get_current_user] = override_get_current_user
        app.dependency_overrides[jobs_module.get_db_session] = override_get_db_session

        try:
            with patch(
                "src.presentation.api.routes.jobs.JobRepositoryImpl",
                return_value=mock_job_repo,
            ):
                transport = ASGITransport(app=app)
                async with AsyncClient(transport=transport, base_url="http://test") as ac:
                    response = await ac.get(
                        f"/api/v1/jobs/{other_user_job.id}",
                        headers={"X-User-Id": str(mock_user_id)},
                    )

                # Should return 404 to avoid leaking info about other users' jobs
                assert response.status_code == 404
        finally:
            app.dependency_overrides.clear()


# =============================================================================
# T047: Contract test for GET /jobs/{id}/download (200 audio stream)
# =============================================================================


class TestDownloadJobAudioEndpoint:
    """Contract tests for GET /api/v1/jobs/{id}/download endpoint."""

    @pytest.mark.asyncio
    async def test_download_completed_job_success(
        self,
        mock_user_id: uuid.UUID,
        mock_current_user: CurrentUser,
    ):
        """T047: Test downloading completed job audio returns 200 with audio stream."""
        # Create a completed job with audio file
        audio_file_id = uuid.uuid4()
        completed_job = Job(
            id=uuid.uuid4(),
            user_id=mock_user_id,
            job_type=JobType.MULTI_ROLE_TTS,
            status=JobStatus.COMPLETED,
            provider="azure",
            input_params={},
            created_at=datetime.utcnow(),
            audio_file_id=audio_file_id,
        )

        mock_job_repo = AsyncMock()
        mock_job_repo.get_by_id.return_value = completed_job

        # Mock audio file retrieval
        mock_audio_content = b"fake audio content for testing"

        mock_session = MagicMock()

        async def override_get_current_user():
            return mock_current_user

        async def override_get_db_session():
            return mock_session

        from src.presentation.api.routes import jobs as jobs_module

        app.dependency_overrides[get_current_user] = override_get_current_user
        app.dependency_overrides[jobs_module.get_db_session] = override_get_db_session

        try:
            with (
                patch(
                    "src.presentation.api.routes.jobs.JobRepositoryImpl",
                    return_value=mock_job_repo,
                ),
                patch(
                    "src.presentation.api.routes.jobs.get_audio_file_content",
                    new_callable=AsyncMock,
                    return_value=(mock_audio_content, "audio/mpeg", "test.mp3"),
                ),
            ):
                transport = ASGITransport(app=app)
                async with AsyncClient(transport=transport, base_url="http://test") as ac:
                    response = await ac.get(
                        f"/api/v1/jobs/{completed_job.id}/download",
                        headers={"X-User-Id": str(mock_user_id)},
                    )

                assert response.status_code == 200
                assert response.headers["content-type"] == "audio/mpeg"
                assert "content-disposition" in response.headers
                assert response.content == mock_audio_content
        finally:
            app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_download_job_response_headers(
        self,
        mock_user_id: uuid.UUID,
        mock_current_user: CurrentUser,
    ):
        """T047: Test download response includes proper Content-Disposition header."""
        audio_file_id = uuid.uuid4()
        completed_job = Job(
            id=uuid.uuid4(),
            user_id=mock_user_id,
            job_type=JobType.MULTI_ROLE_TTS,
            status=JobStatus.COMPLETED,
            provider="azure",
            input_params={},
            created_at=datetime.utcnow(),
            audio_file_id=audio_file_id,
        )

        mock_job_repo = AsyncMock()
        mock_job_repo.get_by_id.return_value = completed_job

        mock_audio_content = b"fake audio content"

        mock_session = MagicMock()

        async def override_get_current_user():
            return mock_current_user

        async def override_get_db_session():
            return mock_session

        from src.presentation.api.routes import jobs as jobs_module

        app.dependency_overrides[get_current_user] = override_get_current_user
        app.dependency_overrides[jobs_module.get_db_session] = override_get_db_session

        try:
            with (
                patch(
                    "src.presentation.api.routes.jobs.JobRepositoryImpl",
                    return_value=mock_job_repo,
                ),
                patch(
                    "src.presentation.api.routes.jobs.get_audio_file_content",
                    new_callable=AsyncMock,
                    return_value=(mock_audio_content, "audio/mpeg", "synthesis_result.mp3"),
                ),
            ):
                transport = ASGITransport(app=app)
                async with AsyncClient(transport=transport, base_url="http://test") as ac:
                    response = await ac.get(
                        f"/api/v1/jobs/{completed_job.id}/download",
                        headers={"X-User-Id": str(mock_user_id)},
                    )

                assert response.status_code == 200
                content_disposition = response.headers.get("content-disposition", "")
                assert "attachment" in content_disposition
                assert "filename=" in content_disposition
        finally:
            app.dependency_overrides.clear()


# =============================================================================
# T048: Contract test for download non-completed job (404 response)
# =============================================================================


class TestDownloadNonCompletedJob:
    """Contract tests for downloading non-completed jobs (404 response)."""

    @pytest.mark.asyncio
    async def test_download_pending_job_returns_404(
        self,
        mock_user_id: uuid.UUID,
        mock_current_user: CurrentUser,
    ):
        """T048: Test downloading pending job returns 404."""
        pending_job = Job(
            id=uuid.uuid4(),
            user_id=mock_user_id,
            job_type=JobType.MULTI_ROLE_TTS,
            status=JobStatus.PENDING,
            provider="azure",
            input_params={},
            created_at=datetime.utcnow(),
            audio_file_id=None,
        )

        mock_job_repo = AsyncMock()
        mock_job_repo.get_by_id.return_value = pending_job

        mock_session = MagicMock()

        async def override_get_current_user():
            return mock_current_user

        async def override_get_db_session():
            return mock_session

        from src.presentation.api.routes import jobs as jobs_module

        app.dependency_overrides[get_current_user] = override_get_current_user
        app.dependency_overrides[jobs_module.get_db_session] = override_get_db_session

        try:
            with patch(
                "src.presentation.api.routes.jobs.JobRepositoryImpl",
                return_value=mock_job_repo,
            ):
                transport = ASGITransport(app=app)
                async with AsyncClient(transport=transport, base_url="http://test") as ac:
                    response = await ac.get(
                        f"/api/v1/jobs/{pending_job.id}/download",
                        headers={"X-User-Id": str(mock_user_id)},
                    )

                assert response.status_code == 404
                data = response.json()
                assert "detail" in data
        finally:
            app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_download_processing_job_returns_404(
        self,
        mock_user_id: uuid.UUID,
        mock_current_user: CurrentUser,
    ):
        """T048: Test downloading processing job returns 404."""
        processing_job = Job(
            id=uuid.uuid4(),
            user_id=mock_user_id,
            job_type=JobType.MULTI_ROLE_TTS,
            status=JobStatus.PROCESSING,
            provider="azure",
            input_params={},
            created_at=datetime.utcnow(),
            audio_file_id=None,
        )

        mock_job_repo = AsyncMock()
        mock_job_repo.get_by_id.return_value = processing_job

        mock_session = MagicMock()

        async def override_get_current_user():
            return mock_current_user

        async def override_get_db_session():
            return mock_session

        from src.presentation.api.routes import jobs as jobs_module

        app.dependency_overrides[get_current_user] = override_get_current_user
        app.dependency_overrides[jobs_module.get_db_session] = override_get_db_session

        try:
            with patch(
                "src.presentation.api.routes.jobs.JobRepositoryImpl",
                return_value=mock_job_repo,
            ):
                transport = ASGITransport(app=app)
                async with AsyncClient(transport=transport, base_url="http://test") as ac:
                    response = await ac.get(
                        f"/api/v1/jobs/{processing_job.id}/download",
                        headers={"X-User-Id": str(mock_user_id)},
                    )

                assert response.status_code == 404
        finally:
            app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_download_failed_job_returns_404(
        self,
        mock_user_id: uuid.UUID,
        mock_current_user: CurrentUser,
    ):
        """T048: Test downloading failed job returns 404."""
        failed_job = Job(
            id=uuid.uuid4(),
            user_id=mock_user_id,
            job_type=JobType.MULTI_ROLE_TTS,
            status=JobStatus.FAILED,
            provider="azure",
            input_params={},
            created_at=datetime.utcnow(),
            audio_file_id=None,
            error_message="Synthesis failed",
        )

        mock_job_repo = AsyncMock()
        mock_job_repo.get_by_id.return_value = failed_job

        mock_session = MagicMock()

        async def override_get_current_user():
            return mock_current_user

        async def override_get_db_session():
            return mock_session

        from src.presentation.api.routes import jobs as jobs_module

        app.dependency_overrides[get_current_user] = override_get_current_user
        app.dependency_overrides[jobs_module.get_db_session] = override_get_db_session

        try:
            with patch(
                "src.presentation.api.routes.jobs.JobRepositoryImpl",
                return_value=mock_job_repo,
            ):
                transport = ASGITransport(app=app)
                async with AsyncClient(transport=transport, base_url="http://test") as ac:
                    response = await ac.get(
                        f"/api/v1/jobs/{failed_job.id}/download",
                        headers={"X-User-Id": str(mock_user_id)},
                    )

                assert response.status_code == 404
        finally:
            app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_download_nonexistent_job_returns_404(
        self,
        mock_user_id: uuid.UUID,
        mock_current_user: CurrentUser,
    ):
        """T048: Test downloading non-existent job returns 404."""
        mock_job_repo = AsyncMock()
        mock_job_repo.get_by_id.return_value = None

        mock_session = MagicMock()

        async def override_get_current_user():
            return mock_current_user

        async def override_get_db_session():
            return mock_session

        from src.presentation.api.routes import jobs as jobs_module

        app.dependency_overrides[get_current_user] = override_get_current_user
        app.dependency_overrides[jobs_module.get_db_session] = override_get_db_session

        try:
            with patch(
                "src.presentation.api.routes.jobs.JobRepositoryImpl",
                return_value=mock_job_repo,
            ):
                transport = ASGITransport(app=app)
                async with AsyncClient(transport=transport, base_url="http://test") as ac:
                    response = await ac.get(
                        f"/api/v1/jobs/{uuid.uuid4()}/download",
                        headers={"X-User-Id": str(mock_user_id)},
                    )

                assert response.status_code == 404
        finally:
            app.dependency_overrides.clear()


# =============================================================================
# T056: Contract test for DELETE /jobs/{id} (200 cancelled)
# =============================================================================


class TestCancelJobEndpoint:
    """Contract tests for DELETE /api/v1/jobs/{id} endpoint."""

    @pytest.mark.asyncio
    async def test_cancel_pending_job_success(
        self,
        mock_user_id: uuid.UUID,
        mock_current_user: CurrentUser,
    ):
        """T056: Test cancelling a pending job returns 200."""
        pending_job = Job(
            id=uuid.uuid4(),
            user_id=mock_user_id,
            job_type=JobType.MULTI_ROLE_TTS,
            status=JobStatus.PENDING,
            provider="azure",
            input_params={},
            created_at=datetime.utcnow(),
        )

        # Create a cancelled version for the update response
        cancelled_job = Job(
            id=pending_job.id,
            user_id=mock_user_id,
            job_type=JobType.MULTI_ROLE_TTS,
            status=JobStatus.CANCELLED,
            provider="azure",
            input_params={},
            created_at=pending_job.created_at,
            completed_at=datetime.utcnow(),
        )

        mock_job_repo = AsyncMock()
        mock_job_repo.get_by_id.return_value = pending_job
        mock_job_repo.update.return_value = cancelled_job

        mock_session = MagicMock()
        mock_session.commit = AsyncMock()

        async def override_get_current_user():
            return mock_current_user

        async def override_get_db_session():
            return mock_session

        from src.presentation.api.routes import jobs as jobs_module

        app.dependency_overrides[get_current_user] = override_get_current_user
        app.dependency_overrides[jobs_module.get_db_session] = override_get_db_session

        try:
            with patch(
                "src.presentation.api.routes.jobs.JobRepositoryImpl",
                return_value=mock_job_repo,
            ):
                transport = ASGITransport(app=app)
                async with AsyncClient(transport=transport, base_url="http://test") as ac:
                    response = await ac.delete(
                        f"/api/v1/jobs/{pending_job.id}",
                        headers={"X-User-Id": str(mock_user_id)},
                    )

                assert response.status_code == 200
                data = response.json()

                # Verify response structure
                assert data["id"] == str(pending_job.id)
                assert data["status"] == "cancelled"
        finally:
            app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_cancel_job_returns_job_response(
        self,
        mock_user_id: uuid.UUID,
        mock_current_user: CurrentUser,
    ):
        """T056: Test cancel response includes correct JobResponse fields."""
        pending_job = Job(
            id=uuid.uuid4(),
            user_id=mock_user_id,
            job_type=JobType.MULTI_ROLE_TTS,
            status=JobStatus.PENDING,
            provider="azure",
            input_params={},
            created_at=datetime.utcnow(),
        )

        cancelled_job = Job(
            id=pending_job.id,
            user_id=mock_user_id,
            job_type=JobType.MULTI_ROLE_TTS,
            status=JobStatus.CANCELLED,
            provider="azure",
            input_params={},
            created_at=pending_job.created_at,
            completed_at=datetime.utcnow(),
        )

        mock_job_repo = AsyncMock()
        mock_job_repo.get_by_id.return_value = pending_job
        mock_job_repo.update.return_value = cancelled_job

        mock_session = MagicMock()
        mock_session.commit = AsyncMock()

        async def override_get_current_user():
            return mock_current_user

        async def override_get_db_session():
            return mock_session

        from src.presentation.api.routes import jobs as jobs_module

        app.dependency_overrides[get_current_user] = override_get_current_user
        app.dependency_overrides[jobs_module.get_db_session] = override_get_db_session

        try:
            with patch(
                "src.presentation.api.routes.jobs.JobRepositoryImpl",
                return_value=mock_job_repo,
            ):
                transport = ASGITransport(app=app)
                async with AsyncClient(transport=transport, base_url="http://test") as ac:
                    response = await ac.delete(
                        f"/api/v1/jobs/{pending_job.id}",
                        headers={"X-User-Id": str(mock_user_id)},
                    )

                assert response.status_code == 200
                data = response.json()

                # Verify all JobResponse fields
                assert "id" in data
                assert "status" in data
                assert "job_type" in data
                assert "provider" in data
                assert "created_at" in data
        finally:
            app.dependency_overrides.clear()


# =============================================================================
# T057: Contract test for cancel non-pending job (409 conflict)
# =============================================================================


class TestCancelNonPendingJob:
    """Contract tests for cancelling non-pending jobs (409 response)."""

    @pytest.mark.asyncio
    async def test_cancel_processing_job_returns_409(
        self,
        mock_user_id: uuid.UUID,
        mock_current_user: CurrentUser,
    ):
        """T057: Test cancelling a processing job returns 409 Conflict."""
        processing_job = Job(
            id=uuid.uuid4(),
            user_id=mock_user_id,
            job_type=JobType.MULTI_ROLE_TTS,
            status=JobStatus.PROCESSING,
            provider="azure",
            input_params={},
            created_at=datetime.utcnow(),
            started_at=datetime.utcnow(),
        )

        mock_job_repo = AsyncMock()
        mock_job_repo.get_by_id.return_value = processing_job

        mock_session = MagicMock()

        async def override_get_current_user():
            return mock_current_user

        async def override_get_db_session():
            return mock_session

        from src.presentation.api.routes import jobs as jobs_module

        app.dependency_overrides[get_current_user] = override_get_current_user
        app.dependency_overrides[jobs_module.get_db_session] = override_get_db_session

        try:
            with patch(
                "src.presentation.api.routes.jobs.JobRepositoryImpl",
                return_value=mock_job_repo,
            ):
                transport = ASGITransport(app=app)
                async with AsyncClient(transport=transport, base_url="http://test") as ac:
                    response = await ac.delete(
                        f"/api/v1/jobs/{processing_job.id}",
                        headers={"X-User-Id": str(mock_user_id)},
                    )

                assert response.status_code == 409
                data = response.json()
                assert "detail" in data
        finally:
            app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_cancel_completed_job_returns_409(
        self,
        mock_user_id: uuid.UUID,
        mock_current_user: CurrentUser,
    ):
        """T057: Test cancelling a completed job returns 409 Conflict."""
        completed_job = Job(
            id=uuid.uuid4(),
            user_id=mock_user_id,
            job_type=JobType.MULTI_ROLE_TTS,
            status=JobStatus.COMPLETED,
            provider="azure",
            input_params={},
            created_at=datetime.utcnow(),
            completed_at=datetime.utcnow(),
            audio_file_id=uuid.uuid4(),
        )

        mock_job_repo = AsyncMock()
        mock_job_repo.get_by_id.return_value = completed_job

        mock_session = MagicMock()

        async def override_get_current_user():
            return mock_current_user

        async def override_get_db_session():
            return mock_session

        from src.presentation.api.routes import jobs as jobs_module

        app.dependency_overrides[get_current_user] = override_get_current_user
        app.dependency_overrides[jobs_module.get_db_session] = override_get_db_session

        try:
            with patch(
                "src.presentation.api.routes.jobs.JobRepositoryImpl",
                return_value=mock_job_repo,
            ):
                transport = ASGITransport(app=app)
                async with AsyncClient(transport=transport, base_url="http://test") as ac:
                    response = await ac.delete(
                        f"/api/v1/jobs/{completed_job.id}",
                        headers={"X-User-Id": str(mock_user_id)},
                    )

                assert response.status_code == 409
        finally:
            app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_cancel_failed_job_returns_409(
        self,
        mock_user_id: uuid.UUID,
        mock_current_user: CurrentUser,
    ):
        """T057: Test cancelling a failed job returns 409 Conflict."""
        failed_job = Job(
            id=uuid.uuid4(),
            user_id=mock_user_id,
            job_type=JobType.MULTI_ROLE_TTS,
            status=JobStatus.FAILED,
            provider="azure",
            input_params={},
            created_at=datetime.utcnow(),
            completed_at=datetime.utcnow(),
            error_message="Synthesis failed",
        )

        mock_job_repo = AsyncMock()
        mock_job_repo.get_by_id.return_value = failed_job

        mock_session = MagicMock()

        async def override_get_current_user():
            return mock_current_user

        async def override_get_db_session():
            return mock_session

        from src.presentation.api.routes import jobs as jobs_module

        app.dependency_overrides[get_current_user] = override_get_current_user
        app.dependency_overrides[jobs_module.get_db_session] = override_get_db_session

        try:
            with patch(
                "src.presentation.api.routes.jobs.JobRepositoryImpl",
                return_value=mock_job_repo,
            ):
                transport = ASGITransport(app=app)
                async with AsyncClient(transport=transport, base_url="http://test") as ac:
                    response = await ac.delete(
                        f"/api/v1/jobs/{failed_job.id}",
                        headers={"X-User-Id": str(mock_user_id)},
                    )

                assert response.status_code == 409
        finally:
            app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_cancel_nonexistent_job_returns_404(
        self,
        mock_user_id: uuid.UUID,
        mock_current_user: CurrentUser,
    ):
        """T057: Test cancelling a non-existent job returns 404."""
        mock_job_repo = AsyncMock()
        mock_job_repo.get_by_id.return_value = None

        mock_session = MagicMock()

        async def override_get_current_user():
            return mock_current_user

        async def override_get_db_session():
            return mock_session

        from src.presentation.api.routes import jobs as jobs_module

        app.dependency_overrides[get_current_user] = override_get_current_user
        app.dependency_overrides[jobs_module.get_db_session] = override_get_db_session

        try:
            with patch(
                "src.presentation.api.routes.jobs.JobRepositoryImpl",
                return_value=mock_job_repo,
            ):
                transport = ASGITransport(app=app)
                async with AsyncClient(transport=transport, base_url="http://test") as ac:
                    response = await ac.delete(
                        f"/api/v1/jobs/{uuid.uuid4()}",
                        headers={"X-User-Id": str(mock_user_id)},
                    )

                assert response.status_code == 404
        finally:
            app.dependency_overrides.clear()

"""End-to-end integration tests for JobWorker with real database.

This test verifies the actual job pickup and status transition flow:
1. Create a job in the database (PENDING)
2. JobWorker picks it up and changes status to PROCESSING
3. Verify the PROCESSING status is committed to database immediately
4. Job completes (or fails with mock TTS)

Requires: PostgreSQL database running locally
"""

import os
import uuid
from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from src.domain.entities.job import JobStatus, JobType
from src.domain.entities.multi_role_tts import MultiRoleSupportType
from src.infrastructure.persistence.models import AudioFileModel, JobModel, User
from src.infrastructure.workers.job_worker import JobWorker

# Get database URL from environment or use default
DATABASE_URL = os.environ.get(
    "DATABASE_URL",
    "postgresql+asyncpg://voicelab:voicelab_dev@localhost:5432/voicelab_dev",
)


@pytest.fixture
def sample_job_params() -> dict:
    """Sample input parameters for a multi-role TTS job."""
    return {
        "provider": "azure",
        "turns": [
            {"speaker": "A", "text": "測試訊息一"},
            {"speaker": "B", "text": "測試訊息二"},
        ],
        "voice_assignments": [
            {"speaker": "A", "voice_id": "zh-TW-HsiaoYuNeural"},
            {"speaker": "B", "voice_id": "zh-TW-YunJheNeural"},
        ],
        "language": "zh-TW",
        "output_format": "mp3",
        "gap_ms": 300,
        "crossfade_ms": 50,
    }


@pytest.fixture
def mock_synthesis_result():
    """Mock TTS synthesis result."""
    result = MagicMock()
    result.audio_content = b"fake_audio_bytes_for_testing"
    result.content_type = "audio/mpeg"
    result.duration_ms = 3000
    result.latency_ms = 500
    result.synthesis_mode = MultiRoleSupportType.SEGMENTED
    return result


@pytest.fixture
async def db_session_factory():
    """Create a fresh database session factory for each test."""
    engine = create_async_engine(DATABASE_URL, echo=False)
    factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    yield factory
    await engine.dispose()


@pytest.fixture
async def test_user(db_session_factory):
    """Create a test user and clean up after test."""
    user_id = uuid.uuid4()

    async with db_session_factory() as session:
        user = User(
            id=user_id,
            email=f"test-{user_id}@example.com",
            name="Test User",
            picture_url=None,
            google_id=str(user_id),
        )
        session.add(user)
        await session.commit()

    yield user_id

    # Cleanup
    async with db_session_factory() as session:
        # Delete any audio files created
        await session.execute(delete(AudioFileModel).where(AudioFileModel.user_id == user_id))
        # Delete any jobs created
        await session.execute(delete(JobModel).where(JobModel.user_id == user_id))
        # Delete the user
        await session.execute(delete(User).where(User.id == user_id))
        await session.commit()


@pytest.mark.integration
class TestJobWorkerE2E:
    """End-to-end tests for JobWorker with real database."""

    @pytest.mark.asyncio
    async def test_job_status_transitions_with_real_database(
        self,
        db_session_factory,
        test_user,
        sample_job_params,
        mock_synthesis_result,
    ):
        """Test that job status transitions are properly committed to database.

        This test verifies the fix for the transaction commit timing issue:
        - Job is created as PENDING
        - Worker picks it up and commits PROCESSING status immediately
        - Job completes successfully
        """
        job_id = uuid.uuid4()

        # Step 1: Create a job directly in the database
        async with db_session_factory() as session:
            job_model = JobModel(
                id=job_id,
                user_id=test_user,
                job_type=JobType.MULTI_ROLE_TTS.value,
                status=JobStatus.PENDING.value,
                provider="azure",
                input_params=sample_job_params,
                retry_count=0,
                created_at=datetime.now(UTC),
            )
            session.add(job_model)
            await session.commit()

        # Verify job was created as PENDING
        async with db_session_factory() as session:
            result = await session.execute(select(JobModel).where(JobModel.id == job_id))
            job = result.scalar_one()
            assert job.status == JobStatus.PENDING.value, "Job should start as PENDING"

        # Step 2: Create worker and process the job
        with patch(
            "src.infrastructure.workers.job_worker.SynthesizeMultiRoleUseCase"
        ) as MockUseCase:
            mock_use_case = AsyncMock()
            mock_use_case.execute = AsyncMock(return_value=mock_synthesis_result)
            MockUseCase.return_value = mock_use_case

            with patch("src.infrastructure.workers.job_worker.LocalStorage") as MockStorage:
                mock_storage = MagicMock()
                mock_stored_file = MagicMock()
                mock_stored_file.key = f"jobs/azure/test/{job_id}.mp3"
                mock_stored_file.size_bytes = len(mock_synthesis_result.audio_content)
                mock_storage.upload = AsyncMock(return_value=mock_stored_file)
                MockStorage.return_value = mock_storage

                worker = JobWorker(session_factory=db_session_factory)
                await worker._process_next_job()

        # Step 3: Verify final job state in database
        async with db_session_factory() as session:
            result = await session.execute(select(JobModel).where(JobModel.id == job_id))
            final_job = result.scalar_one()

            assert final_job.status == JobStatus.COMPLETED.value, (
                f"Job should be COMPLETED, got {final_job.status}"
            )
            assert final_job.audio_file_id is not None, "Should have audio_file_id"
            assert final_job.started_at is not None, "Should have started_at"
            assert final_job.completed_at is not None, "Should have completed_at"
            assert final_job.result_metadata is not None, "Should have result_metadata"

    @pytest.mark.asyncio
    async def test_processing_status_committed_before_execution(
        self,
        db_session_factory,
        test_user,
        sample_job_params,
    ):
        """Test that PROCESSING status is committed BEFORE job execution starts.

        This is the critical fix - we need to verify that if execution fails,
        the job is still marked as PROCESSING (not stuck in PENDING).
        """
        job_id = uuid.uuid4()

        # Create a job with max retries already reached
        async with db_session_factory() as session:
            job_model = JobModel(
                id=job_id,
                user_id=test_user,
                job_type=JobType.MULTI_ROLE_TTS.value,
                status=JobStatus.PENDING.value,
                provider="azure",
                input_params=sample_job_params,
                retry_count=3,  # Already at max retries
                created_at=datetime.now(UTC),
            )
            session.add(job_model)
            await session.commit()

        # Track status during execution
        status_during_execution = None

        async def capture_status_and_fail(*args, **kwargs):
            """Mock that checks DB status before failing."""
            nonlocal status_during_execution
            # Check the job status in database during "execution"
            async with db_session_factory() as check_session:
                result = await check_session.execute(select(JobModel).where(JobModel.id == job_id))
                job = result.scalar_one()
                status_during_execution = job.status
            # Then fail
            raise Exception("Simulated TTS failure")

        # Process with failing TTS
        with patch(
            "src.infrastructure.workers.job_worker.SynthesizeMultiRoleUseCase"
        ) as MockUseCase:
            mock_use_case = AsyncMock()
            mock_use_case.execute = AsyncMock(side_effect=capture_status_and_fail)
            MockUseCase.return_value = mock_use_case

            with patch("src.infrastructure.workers.job_worker.LocalStorage"):
                worker = JobWorker(session_factory=db_session_factory)
                await worker._process_next_job()

        # THE KEY ASSERTION: Status was PROCESSING during execution
        assert status_during_execution == JobStatus.PROCESSING.value, (
            f"Status during execution should be PROCESSING, got {status_during_execution}. "
            "This means the commit after acquire_pending_job() is not working!"
        )

        # Verify final state is FAILED (since retry_count was already 3)
        async with db_session_factory() as session:
            result = await session.execute(select(JobModel).where(JobModel.id == job_id))
            final_job = result.scalar_one()
            assert final_job.status == JobStatus.FAILED.value

    @pytest.mark.asyncio
    async def test_no_pending_jobs_does_not_error(self, db_session_factory):
        """Test that worker handles no pending jobs gracefully."""
        worker = JobWorker(session_factory=db_session_factory)
        # Should complete without error
        await worker._process_next_job()

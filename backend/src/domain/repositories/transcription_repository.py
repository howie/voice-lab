"""Transcription Repository Interface.

Feature: 003-stt-testing-module
Repository interface for STT transcription persistence.
"""

from abc import ABC, abstractmethod
from uuid import UUID

from src.domain.entities.audio_file import AudioFile
from src.domain.entities.ground_truth import GroundTruth
from src.domain.entities.stt import STTResult
from src.domain.entities.wer_analysis import WERAnalysis


class ITranscriptionRepository(ABC):
    """Abstract repository interface for STT transcriptions.

    This interface defines the contract for transcription persistence.
    Handles AudioFile, transcription results, ground truth, and WER analysis.
    """

    # --- AudioFile Operations ---

    @abstractmethod
    async def save_audio_file(self, audio_file: AudioFile) -> AudioFile:
        """Save an audio file record.

        Args:
            audio_file: Audio file entity to save

        Returns:
            Saved audio file with generated ID if new
        """
        pass

    @abstractmethod
    async def get_audio_file(self, audio_file_id: UUID) -> AudioFile | None:
        """Get an audio file by ID.

        Args:
            audio_file_id: Audio file UUID

        Returns:
            Audio file if found, None otherwise
        """
        pass

    @abstractmethod
    async def delete_audio_file(self, audio_file_id: UUID) -> bool:
        """Delete an audio file record.

        Args:
            audio_file_id: Audio file UUID to delete

        Returns:
            True if deleted, False if not found
        """
        pass

    # --- Transcription Result Operations ---

    @abstractmethod
    async def save_transcription(
        self,
        result: STTResult,
        audio_file_id: UUID,
        user_id: UUID,
    ) -> tuple[UUID, UUID]:
        """Save a transcription result.

        Args:
            result: STT result entity
            audio_file_id: Associated audio file ID
            user_id: User who performed the transcription

        Returns:
            Tuple of (transcription record ID, result ID)
        """
        pass

    @abstractmethod
    async def get_transcription(self, transcription_id: UUID) -> STTResult | None:
        """Get a transcription result by ID.

        Args:
            transcription_id: Transcription UUID

        Returns:
            STT result if found, None otherwise
        """
        pass

    @abstractmethod
    async def list_transcriptions(
        self,
        user_id: UUID,
        provider: str | None = None,
        language: str | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[dict], int]:
        """List transcriptions for a user with pagination.

        Args:
            user_id: User UUID
            provider: Filter by provider
            language: Filter by language
            page: Page number (1-indexed)
            page_size: Items per page

        Returns:
            Tuple of (list of transcription summaries, total count)
        """
        pass

    @abstractmethod
    async def delete_transcription(self, transcription_id: UUID) -> bool:
        """Delete a transcription record.

        Args:
            transcription_id: Transcription UUID to delete

        Returns:
            True if deleted, False if not found
        """
        pass

    # --- Ground Truth Operations ---

    @abstractmethod
    async def save_ground_truth(self, ground_truth: GroundTruth) -> GroundTruth:
        """Save ground truth text for an audio file.

        Args:
            ground_truth: Ground truth entity

        Returns:
            Saved ground truth entity
        """
        pass

    @abstractmethod
    async def get_ground_truth(self, audio_file_id: UUID) -> GroundTruth | None:
        """Get ground truth for an audio file.

        Args:
            audio_file_id: Audio file UUID

        Returns:
            Ground truth if found, None otherwise
        """
        pass

    @abstractmethod
    async def update_ground_truth(
        self, audio_file_id: UUID, text: str, language: str
    ) -> GroundTruth | None:
        """Update ground truth text for an audio file.

        Args:
            audio_file_id: Audio file UUID
            text: New ground truth text
            language: Language code

        Returns:
            Updated ground truth if exists, None otherwise
        """
        pass

    # --- WER Analysis Operations ---

    @abstractmethod
    async def save_wer_analysis(self, analysis: WERAnalysis) -> WERAnalysis:
        """Save WER/CER analysis result.

        Args:
            analysis: WER analysis entity

        Returns:
            Saved analysis entity
        """
        pass

    @abstractmethod
    async def get_wer_analysis(self, result_id: UUID) -> WERAnalysis | None:
        """Get WER analysis for a transcription result.

        Args:
            result_id: Transcription result UUID

        Returns:
            WER analysis if found, None otherwise
        """
        pass

    # --- Detailed Retrieval ---

    @abstractmethod
    async def get_transcription_detail(self, transcription_id: UUID) -> dict | None:
        """Get detailed transcription information including audio file and WER.

        Args:
            transcription_id: Transcription UUID

        Returns:
            Dictionary with full transcription details, or None if not found
        """
        pass

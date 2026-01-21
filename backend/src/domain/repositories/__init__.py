"""Repository Interfaces - Abstract definitions for data access.

These interfaces define the contract for data persistence,
following the Dependency Inversion Principle.
"""

from src.domain.repositories.job_repository import IJobRepository
from src.domain.repositories.scenario_template_repository import (
    ScenarioTemplateRepository,
)
from src.domain.repositories.test_record_repository import ITestRecordRepository
from src.domain.repositories.transcription_repository import ITranscriptionRepository
from src.domain.repositories.voice_repository import IVoiceRepository

__all__ = [
    "IJobRepository",
    "ITestRecordRepository",
    "ITranscriptionRepository",
    "IVoiceRepository",
    "ScenarioTemplateRepository",
]

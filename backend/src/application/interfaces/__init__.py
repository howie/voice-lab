"""Application Interfaces (Ports) - External service contracts.

These interfaces define the contract for external services.
Infrastructure layer provides the implementations (adapters).
"""

from src.application.interfaces.llm_provider import ILLMProvider
from src.application.interfaces.storage_service import IStorageService
from src.application.interfaces.stt_provider import ISTTProvider
from src.application.interfaces.tts_provider import ITTSProvider

__all__ = [
    "ITTSProvider",
    "ISTTProvider",
    "ILLMProvider",
    "IStorageService",
]

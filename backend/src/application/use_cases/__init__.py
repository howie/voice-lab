"""Use Cases - Application-specific business rules.

Use cases orchestrate the flow of data to and from entities,
and direct those entities to use their domain logic.
"""

from src.application.use_cases.compare_providers import CompareProvidersUseCase
from src.application.use_cases.synthesize_speech import (
    SynthesizeSpeech,
    SynthesizeSpeechFactory,
)
from src.application.use_cases.transcribe_audio import TranscribeAudioUseCase
from src.application.use_cases.voice_interaction import VoiceInteractionUseCase

# Alias for backward compatibility
SynthesizeSpeechUseCase = SynthesizeSpeech

__all__ = [
    "SynthesizeSpeech",
    "SynthesizeSpeechFactory",
    "SynthesizeSpeechUseCase",
    "TranscribeAudioUseCase",
    "CompareProvidersUseCase",
    "VoiceInteractionUseCase",
]

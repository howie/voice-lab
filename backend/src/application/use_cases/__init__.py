"""Use Cases - Application-specific business rules.

Use cases orchestrate the flow of data to and from entities,
and direct those entities to use their domain logic.
"""

from src.application.use_cases.add_provider_credential import (
    AddCredentialInput,
    AddCredentialOutput,
    AddProviderCredentialError,
    AddProviderCredentialUseCase,
    CredentialAlreadyExistsError,
    ProviderNotFoundError,
    ValidationFailedError,
)
from src.application.use_cases.compare_providers import CompareProvidersUseCase
from src.application.use_cases.delete_provider_credential import (
    DeleteCredentialInput,
    DeleteCredentialOutput,
    DeleteProviderCredentialError,
    DeleteProviderCredentialUseCase,
)
from src.application.use_cases.list_provider_credentials import (
    ListCredentialsInput,
    ListCredentialsOutput,
    ListProviderCredentialsUseCase,
)
from src.application.use_cases.list_provider_models import (
    ListModelsInput,
    ListModelsOutput,
    ListProviderModelsError,
    ListProviderModelsUseCase,
    ProviderModelInfo,
)
from src.application.use_cases.revalidate_credential import (
    RevalidateCredentialError,
    RevalidateCredentialInput,
    RevalidateCredentialOutput,
    RevalidateCredentialUseCase,
)
from src.application.use_cases.synthesize_speech import (
    SynthesizeSpeech,
    SynthesizeSpeechFactory,
)
from src.application.use_cases.transcribe_audio import TranscribeAudioUseCase
from src.application.use_cases.update_provider_credential import (
    UpdateCredentialInput,
    UpdateCredentialOutput,
    UpdateProviderCredentialError,
    UpdateProviderCredentialUseCase,
)
from src.application.use_cases.validate_provider_key import (
    ValidateKeyInput,
    ValidateKeyOutput,
    ValidateProviderKeyUseCase,
)
from src.application.use_cases.voice_interaction import VoiceInteractionUseCase

# Alias for backward compatibility
SynthesizeSpeechUseCase = SynthesizeSpeech

__all__ = [
    # Speech use cases
    "SynthesizeSpeech",
    "SynthesizeSpeechFactory",
    "SynthesizeSpeechUseCase",
    "TranscribeAudioUseCase",
    "CompareProvidersUseCase",
    "VoiceInteractionUseCase",
    # Provider credential use cases
    "AddProviderCredentialUseCase",
    "AddCredentialInput",
    "AddCredentialOutput",
    "AddProviderCredentialError",
    "ProviderNotFoundError",
    "CredentialAlreadyExistsError",
    "ValidationFailedError",
    "ListProviderModelsUseCase",
    "ListModelsInput",
    "ListModelsOutput",
    "ListProviderModelsError",
    "ProviderModelInfo",
    "UpdateProviderCredentialUseCase",
    "UpdateCredentialInput",
    "UpdateCredentialOutput",
    "UpdateProviderCredentialError",
    "ValidateProviderKeyUseCase",
    "ValidateKeyInput",
    "ValidateKeyOutput",
    # Delete credential use case
    "DeleteProviderCredentialUseCase",
    "DeleteCredentialInput",
    "DeleteCredentialOutput",
    "DeleteProviderCredentialError",
    # List credentials use case
    "ListProviderCredentialsUseCase",
    "ListCredentialsInput",
    "ListCredentialsOutput",
    # Revalidate credential use case
    "RevalidateCredentialUseCase",
    "RevalidateCredentialInput",
    "RevalidateCredentialOutput",
    "RevalidateCredentialError",
]

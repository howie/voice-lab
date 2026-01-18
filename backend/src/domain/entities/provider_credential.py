"""Provider Credential domain entity."""

import uuid
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class UserProviderCredential:
    """User's API key credential for a TTS/STT provider.

    This entity represents a BYOL (Bring Your Own License) credential
    that a user has configured for a specific provider.
    """

    id: uuid.UUID
    user_id: uuid.UUID
    provider: str
    api_key: str  # Encrypted at rest in database
    is_valid: bool = True
    selected_model_id: str | None = None
    last_validated_at: datetime | None = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)

    def __post_init__(self) -> None:
        """Validate credential attributes."""
        if not self.user_id:
            raise ValueError("User ID cannot be empty")
        if not self.provider:
            raise ValueError("Provider cannot be empty")
        if not self.api_key:
            raise ValueError("API key cannot be empty")

    def mark_valid(self) -> None:
        """Mark the credential as valid after successful validation."""
        self.is_valid = True
        self.last_validated_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()

    def mark_invalid(self) -> None:
        """Mark the credential as invalid after failed validation."""
        self.is_valid = False
        self.last_validated_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()

    def update_api_key(self, new_api_key: str) -> None:
        """Update the API key."""
        if not new_api_key:
            raise ValueError("API key cannot be empty")
        self.api_key = new_api_key
        self.is_valid = True  # Will be validated
        self.last_validated_at = None
        self.updated_at = datetime.utcnow()

    def select_model(self, model_id: str | None) -> None:
        """Select a model for this credential."""
        self.selected_model_id = model_id
        self.updated_at = datetime.utcnow()

    @staticmethod
    def create(
        user_id: uuid.UUID,
        provider: str,
        api_key: str,
        selected_model_id: str | None = None,
    ) -> "UserProviderCredential":
        """Factory method to create a new credential."""
        return UserProviderCredential(
            id=uuid.uuid4(),
            user_id=user_id,
            provider=provider,
            api_key=api_key,
            is_valid=True,  # Will be validated before saving
            selected_model_id=selected_model_id,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )

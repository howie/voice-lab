"""VoiceCustomization domain entity.

Feature: 013-tts-role-mgmt
User customization settings for TTS voices (custom names, favorites, hidden).
"""

from dataclasses import dataclass
from datetime import datetime


@dataclass
class VoiceCustomization:
    """User customization settings for a TTS voice.

    This entity stores user preferences for TTS voices including:
    - Custom display name (e.g., "Puck" -> "陽光男孩聲")
    - Favorite status (shows voice at top of selection)
    - Hidden status (excludes voice from TTS selection)

    Note: This is not a frozen dataclass because we need to modify
    is_favorite when marking as hidden.
    """

    voice_cache_id: str  # References voice_cache.id (format: provider:voice_id)
    custom_name: str | None = None  # User-defined display name (max 50 chars)
    is_favorite: bool = False  # Favorite status
    is_hidden: bool = False  # Hidden status
    id: int | None = None  # Database primary key
    created_at: datetime | None = None
    updated_at: datetime | None = None

    def get_display_name(self, original_name: str) -> str:
        """Get the display name, preferring custom name if set.

        Args:
            original_name: The original voice name from the provider

        Returns:
            Custom name if set, otherwise the original name
        """
        return self.custom_name if self.custom_name else original_name

    def mark_as_hidden(self) -> None:
        """Mark the voice as hidden.

        Business rule: Hidden voices are automatically unfavorited
        because hidden voices don't appear in selection menus,
        so favorite status would be meaningless.
        """
        self.is_hidden = True
        self.is_favorite = False

    def mark_as_visible(self) -> None:
        """Mark the voice as visible (un-hidden)."""
        self.is_hidden = False

    def toggle_favorite(self) -> None:
        """Toggle the favorite status.

        Note: Cannot favorite a hidden voice. If the voice is hidden,
        it must first be made visible before favoriting.
        """
        if not self.is_hidden:
            self.is_favorite = not self.is_favorite

    def toggle_hidden(self) -> None:
        """Toggle the hidden status.

        If hiding, also unfavorites the voice.
        """
        if self.is_hidden:
            self.mark_as_visible()
        else:
            self.mark_as_hidden()

    def validate(self) -> list[str]:
        """Validate the entity fields.

        Returns:
            List of validation error messages (empty if valid)
        """
        errors: list[str] = []

        if self.custom_name and len(self.custom_name) > 50:
            errors.append("custom_name must be 50 characters or less")

        if not self.voice_cache_id:
            errors.append("voice_cache_id is required")

        # Business rule: cannot be both favorite and hidden
        if self.is_favorite and self.is_hidden:
            errors.append("Voice cannot be both favorite and hidden")

        return errors

    def is_default(self) -> bool:
        """Check if this represents default (unmodified) settings.

        Returns:
            True if all settings are at their default values
        """
        return self.custom_name is None and not self.is_favorite and not self.is_hidden

    @classmethod
    def create_default(cls, voice_cache_id: str) -> "VoiceCustomization":
        """Create a new VoiceCustomization with default values.

        Args:
            voice_cache_id: The voice cache ID to create customization for

        Returns:
            New VoiceCustomization with default settings
        """
        return cls(voice_cache_id=voice_cache_id)

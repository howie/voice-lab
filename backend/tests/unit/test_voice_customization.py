"""Unit tests for Voice Customization domain entity and use cases.

Feature: 013-tts-role-mgmt
T011: Unit tests for UpdateVoiceCustomizationUseCase
T026: Unit tests for favorite toggle logic
T033: Unit tests for filter logic
T041: Unit tests for hidden toggle logic (auto-unfavorite)
"""

from datetime import UTC, datetime
from unittest.mock import AsyncMock

import pytest

from src.application.use_cases.bulk_update_voice_customization import (
    BulkUpdateInput,
    BulkUpdateItem,
    BulkUpdateVoiceCustomizationUseCase,
)
from src.application.use_cases.get_voice_customization import (
    GetVoiceCustomizationUseCase,
)
from src.application.use_cases.update_voice_customization import (
    UpdateVoiceCustomizationInput,
    UpdateVoiceCustomizationUseCase,
)
from src.domain.entities.voice_customization import VoiceCustomization

# =============================================================================
# Domain Entity Tests
# =============================================================================


class TestVoiceCustomizationEntity:
    """Tests for VoiceCustomization domain entity."""

    def test_create_default(self):
        """Default customization has no custom name, not favorite, not hidden."""
        c = VoiceCustomization.create_default("gemini:Puck")
        assert c.voice_cache_id == "gemini:Puck"
        assert c.custom_name is None
        assert c.is_favorite is False
        assert c.is_hidden is False
        assert c.id is None

    def test_get_display_name_with_custom(self):
        """Custom name takes priority over original name."""
        c = VoiceCustomization(voice_cache_id="gemini:Puck", custom_name="陽光男孩聲")
        assert c.get_display_name("Puck") == "陽光男孩聲"

    def test_get_display_name_without_custom(self):
        """Falls back to original name when no custom name."""
        c = VoiceCustomization(voice_cache_id="gemini:Puck")
        assert c.get_display_name("Puck") == "Puck"

    def test_mark_as_hidden_unfavorites(self):
        """Hiding a voice automatically unfavorites it."""
        c = VoiceCustomization(
            voice_cache_id="gemini:Puck",
            is_favorite=True,
            is_hidden=False,
        )
        c.mark_as_hidden()
        assert c.is_hidden is True
        assert c.is_favorite is False

    def test_mark_as_visible(self):
        """Un-hiding a voice doesn't change favorite status."""
        c = VoiceCustomization(
            voice_cache_id="gemini:Puck",
            is_hidden=True,
            is_favorite=False,
        )
        c.mark_as_visible()
        assert c.is_hidden is False
        assert c.is_favorite is False

    def test_toggle_favorite_normal(self):
        """Toggle favorite on a visible voice."""
        c = VoiceCustomization(voice_cache_id="gemini:Puck")
        c.toggle_favorite()
        assert c.is_favorite is True
        c.toggle_favorite()
        assert c.is_favorite is False

    def test_toggle_favorite_on_hidden_does_nothing(self):
        """Cannot favorite a hidden voice."""
        c = VoiceCustomization(
            voice_cache_id="gemini:Puck",
            is_hidden=True,
        )
        c.toggle_favorite()
        assert c.is_favorite is False

    def test_toggle_hidden_hides_and_unfavorites(self):
        """Toggling hidden on a favorite voice unfavorites it."""
        c = VoiceCustomization(
            voice_cache_id="gemini:Puck",
            is_favorite=True,
            is_hidden=False,
        )
        c.toggle_hidden()
        assert c.is_hidden is True
        assert c.is_favorite is False

    def test_toggle_hidden_unhides(self):
        """Toggling hidden on a hidden voice makes it visible."""
        c = VoiceCustomization(
            voice_cache_id="gemini:Puck",
            is_hidden=True,
        )
        c.toggle_hidden()
        assert c.is_hidden is False

    def test_validate_valid(self):
        """Valid customization produces no errors."""
        c = VoiceCustomization(
            voice_cache_id="gemini:Puck",
            custom_name="My Voice",
        )
        assert c.validate() == []

    def test_validate_name_too_long(self):
        """Custom name over 50 chars is invalid."""
        c = VoiceCustomization(
            voice_cache_id="gemini:Puck",
            custom_name="A" * 51,
        )
        errors = c.validate()
        assert len(errors) == 1
        assert "50" in errors[0]

    def test_validate_empty_voice_cache_id(self):
        """Empty voice_cache_id is invalid."""
        c = VoiceCustomization(voice_cache_id="")
        errors = c.validate()
        assert any("voice_cache_id" in e for e in errors)

    def test_validate_favorite_and_hidden_conflict(self):
        """Cannot be both favorite and hidden."""
        c = VoiceCustomization(
            voice_cache_id="gemini:Puck",
            is_favorite=True,
            is_hidden=True,
        )
        errors = c.validate()
        assert any("both" in e.lower() for e in errors)

    def test_is_default_true(self):
        """Default customization is detected correctly."""
        c = VoiceCustomization.create_default("gemini:Puck")
        assert c.is_default() is True

    def test_is_default_false_with_custom_name(self):
        """Non-default customization is detected correctly."""
        c = VoiceCustomization(voice_cache_id="gemini:Puck", custom_name="Test")
        assert c.is_default() is False

    def test_is_default_false_with_favorite(self):
        c = VoiceCustomization(voice_cache_id="gemini:Puck", is_favorite=True)
        assert c.is_default() is False


# =============================================================================
# UpdateVoiceCustomizationUseCase Tests
# =============================================================================


class TestUpdateVoiceCustomizationUseCase:
    """Tests for UpdateVoiceCustomizationUseCase."""

    @pytest.fixture
    def mock_repo(self) -> AsyncMock:
        repo = AsyncMock()
        repo.save = AsyncMock()
        repo.get_by_voice_cache_id = AsyncMock(return_value=None)
        return repo

    @pytest.fixture
    def use_case(self, mock_repo: AsyncMock) -> UpdateVoiceCustomizationUseCase:
        return UpdateVoiceCustomizationUseCase(mock_repo)

    @pytest.mark.asyncio
    async def test_create_new_customization(self, use_case, mock_repo):
        """Creates a new customization when none exists."""
        mock_repo.get_by_voice_cache_id.return_value = None
        mock_repo.save.return_value = VoiceCustomization(
            id=1,
            voice_cache_id="gemini:Puck",
            custom_name="陽光男孩聲",
            is_favorite=False,
            is_hidden=False,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )

        result = await use_case.execute(
            UpdateVoiceCustomizationInput(
                voice_cache_id="gemini:Puck",
                custom_name="陽光男孩聲",
            )
        )

        assert result.created is True
        assert result.customization.custom_name == "陽光男孩聲"
        mock_repo.save.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_existing_customization(self, use_case, mock_repo):
        """Updates an existing customization."""
        existing = VoiceCustomization(
            id=1,
            voice_cache_id="gemini:Puck",
            custom_name="Old Name",
            is_favorite=False,
            is_hidden=False,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )
        mock_repo.get_by_voice_cache_id.return_value = existing
        mock_repo.save.return_value = VoiceCustomization(
            id=1,
            voice_cache_id="gemini:Puck",
            custom_name="New Name",
            is_favorite=False,
            is_hidden=False,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )

        result = await use_case.execute(
            UpdateVoiceCustomizationInput(
                voice_cache_id="gemini:Puck",
                custom_name="New Name",
            )
        )

        assert result.created is False
        assert result.customization.custom_name == "New Name"

    @pytest.mark.asyncio
    async def test_empty_string_clears_custom_name(self, use_case, mock_repo):
        """Empty string custom_name is treated as None (cleared)."""
        existing = VoiceCustomization(
            id=1,
            voice_cache_id="gemini:Puck",
            custom_name="Some Name",
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )
        mock_repo.get_by_voice_cache_id.return_value = existing
        mock_repo.save.return_value = VoiceCustomization(
            id=1,
            voice_cache_id="gemini:Puck",
            custom_name=None,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )

        await use_case.execute(
            UpdateVoiceCustomizationInput(
                voice_cache_id="gemini:Puck",
                custom_name="",
            )
        )

        # save should be called with custom_name=None
        saved_entity = mock_repo.save.call_args[0][0]
        assert saved_entity.custom_name is None

    @pytest.mark.asyncio
    async def test_hiding_auto_unfavorites(self, use_case, mock_repo):
        """Hiding a favorite voice automatically unfavorites it."""
        existing = VoiceCustomization(
            id=1,
            voice_cache_id="gemini:Puck",
            is_favorite=True,
            is_hidden=False,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )
        mock_repo.get_by_voice_cache_id.return_value = existing
        mock_repo.save.return_value = VoiceCustomization(
            id=1,
            voice_cache_id="gemini:Puck",
            is_favorite=False,
            is_hidden=True,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )

        await use_case.execute(
            UpdateVoiceCustomizationInput(
                voice_cache_id="gemini:Puck",
                is_hidden=True,
            )
        )

        saved_entity = mock_repo.save.call_args[0][0]
        assert saved_entity.is_hidden is True
        assert saved_entity.is_favorite is False

    @pytest.mark.asyncio
    async def test_cannot_favorite_hidden_voice(self, use_case, mock_repo):
        """Cannot set is_favorite=True on a hidden voice."""
        existing = VoiceCustomization(
            id=1,
            voice_cache_id="gemini:Puck",
            is_favorite=False,
            is_hidden=True,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )
        mock_repo.get_by_voice_cache_id.return_value = existing
        mock_repo.save.return_value = VoiceCustomization(
            id=1,
            voice_cache_id="gemini:Puck",
            is_favorite=False,
            is_hidden=True,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )

        await use_case.execute(
            UpdateVoiceCustomizationInput(
                voice_cache_id="gemini:Puck",
                is_favorite=True,
            )
        )

        saved_entity = mock_repo.save.call_args[0][0]
        # Should remain not favorited because the voice is hidden
        assert saved_entity.is_favorite is False

    @pytest.mark.asyncio
    async def test_none_values_dont_update(self, use_case, mock_repo):
        """None values in input don't change existing fields."""
        existing = VoiceCustomization(
            id=1,
            voice_cache_id="gemini:Puck",
            custom_name="My Voice",
            is_favorite=True,
            is_hidden=False,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )
        mock_repo.get_by_voice_cache_id.return_value = existing
        mock_repo.save.return_value = existing

        await use_case.execute(
            UpdateVoiceCustomizationInput(
                voice_cache_id="gemini:Puck",
                # All None = don't update anything
            )
        )

        saved_entity = mock_repo.save.call_args[0][0]
        assert saved_entity.custom_name == "My Voice"
        assert saved_entity.is_favorite is True


# =============================================================================
# GetVoiceCustomizationUseCase Tests
# =============================================================================


class TestGetVoiceCustomizationUseCase:
    """Tests for GetVoiceCustomizationUseCase."""

    @pytest.fixture
    def mock_repo(self) -> AsyncMock:
        return AsyncMock()

    @pytest.fixture
    def use_case(self, mock_repo: AsyncMock) -> GetVoiceCustomizationUseCase:
        return GetVoiceCustomizationUseCase(mock_repo)

    @pytest.mark.asyncio
    async def test_get_existing(self, use_case, mock_repo):
        """Returns existing customization."""
        expected = VoiceCustomization(
            id=1,
            voice_cache_id="gemini:Puck",
            custom_name="Test",
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )
        mock_repo.get_by_voice_cache_id.return_value = expected

        result = await use_case.execute("gemini:Puck")
        assert result is not None
        assert result.custom_name == "Test"

    @pytest.mark.asyncio
    async def test_get_nonexistent(self, use_case, mock_repo):
        """Returns None for non-existent customization."""
        mock_repo.get_by_voice_cache_id.return_value = None

        result = await use_case.execute("gemini:Unknown")
        assert result is None

    @pytest.mark.asyncio
    async def test_get_or_default_existing(self, use_case, mock_repo):
        """get_or_default returns existing customization."""
        expected = VoiceCustomization(
            id=1,
            voice_cache_id="gemini:Puck",
            is_favorite=True,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )
        mock_repo.get_by_voice_cache_id.return_value = expected

        result = await use_case.get_or_default("gemini:Puck")
        assert result.is_favorite is True

    @pytest.mark.asyncio
    async def test_get_or_default_returns_default(self, use_case, mock_repo):
        """get_or_default returns default when none exists."""
        mock_repo.get_by_voice_cache_id.return_value = None

        result = await use_case.get_or_default("gemini:Puck")
        assert result.voice_cache_id == "gemini:Puck"
        assert result.is_favorite is False
        assert result.is_hidden is False

    @pytest.mark.asyncio
    async def test_get_customization_map(self, use_case, mock_repo):
        """get_customization_map returns map of voice_cache_id -> customization."""
        mock_repo.get_customization_map.return_value = {
            "gemini:Puck": VoiceCustomization(
                id=1,
                voice_cache_id="gemini:Puck",
                is_favorite=True,
                created_at=datetime.now(UTC),
                updated_at=datetime.now(UTC),
            ),
        }

        result = await use_case.get_customization_map(["gemini:Puck", "azure:test"])
        assert "gemini:Puck" in result
        assert "azure:test" not in result


# =============================================================================
# BulkUpdateVoiceCustomizationUseCase Tests
# =============================================================================


class TestBulkUpdateVoiceCustomizationUseCase:
    """Tests for BulkUpdateVoiceCustomizationUseCase."""

    @pytest.fixture
    def mock_repo(self) -> AsyncMock:
        return AsyncMock()

    @pytest.fixture
    def use_case(self, mock_repo: AsyncMock) -> BulkUpdateVoiceCustomizationUseCase:
        return BulkUpdateVoiceCustomizationUseCase(mock_repo)

    @pytest.mark.asyncio
    async def test_bulk_update_success(self, use_case, mock_repo):
        """Successful bulk update returns correct counts."""
        mock_repo.bulk_update.return_value = (2, [])

        result = await use_case.execute(
            BulkUpdateInput(
                updates=[
                    BulkUpdateItem(voice_cache_id="gemini:Puck", is_favorite=True),
                    BulkUpdateItem(voice_cache_id="gemini:Kore", custom_name="溫柔女聲"),
                ]
            )
        )

        assert result.updated_count == 2
        assert result.failed == []

    @pytest.mark.asyncio
    async def test_bulk_update_with_failures(self, use_case, mock_repo):
        """Partial failures are reported correctly."""
        mock_repo.bulk_update.return_value = (1, [("gemini:Invalid", "Voice not found")])

        result = await use_case.execute(
            BulkUpdateInput(
                updates=[
                    BulkUpdateItem(voice_cache_id="gemini:Puck", is_favorite=True),
                    BulkUpdateItem(voice_cache_id="gemini:Invalid", is_favorite=True),
                ]
            )
        )

        assert result.updated_count == 1
        assert len(result.failed) == 1
        assert result.failed[0].voice_cache_id == "gemini:Invalid"

    @pytest.mark.asyncio
    async def test_bulk_update_exceeds_limit(self, use_case, mock_repo):
        """Raises ValueError when too many updates."""
        updates = [BulkUpdateItem(voice_cache_id=f"test:{i}") for i in range(51)]

        with pytest.raises(ValueError, match="Maximum 50"):
            await use_case.execute(BulkUpdateInput(updates=updates))

    @pytest.mark.asyncio
    async def test_bulk_update_applies_hidden_auto_unfavorite(self, use_case, mock_repo):
        """Hidden items have is_favorite set to False."""
        mock_repo.bulk_update.return_value = (1, [])

        await use_case.execute(
            BulkUpdateInput(
                updates=[
                    BulkUpdateItem(
                        voice_cache_id="gemini:Puck",
                        is_hidden=True,
                        is_favorite=True,
                    ),
                ]
            )
        )

        # Check the entity passed to bulk_update
        call_args = mock_repo.bulk_update.call_args[0][0]
        entity = call_args[0]
        assert entity.is_hidden is True
        assert entity.is_favorite is False  # Auto-unfavorited

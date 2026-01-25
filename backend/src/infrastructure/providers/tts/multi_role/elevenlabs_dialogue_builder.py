"""ElevenLabs Dialogue Builder for Multi-Role TTS.

Feature: 008-voai-multi-role-voice-generation
T012: Implement ElevenLabsDialogueBuilder.build_dialogue_request()

Builds request payloads for ElevenLabs Text to Dialogue API.
"""

from dataclasses import dataclass, field
from typing import Any

from src.domain.entities.multi_role_tts import DialogueTurn


@dataclass
class ElevenLabsDialogueConfig:
    """Configuration for ElevenLabs Dialogue API."""

    model_id: str = "eleven_v3"
    stability: float = 0.5
    similarity_boost: float = 0.75
    style: float = 0.0
    use_speaker_boost: bool = True


@dataclass
class DialogueInput:
    """Single input item for the dialogue API."""

    text: str
    voice_id: str


@dataclass
class ElevenLabsDialogueRequest:
    """Complete request payload for ElevenLabs Text to Dialogue API.

    API Endpoint: POST /v1/text-to-dialogue

    Example request body:
        {
            "model_id": "eleven_v3",
            "inputs": [
                {"text": "[excited] 你好！", "voice_id": "voice_id_A"},
                {"text": "[friendly] 嗨！", "voice_id": "voice_id_B"}
            ],
            "settings": {
                "stability": 0.5,
                "similarity_boost": 0.75
            }
        }
    """

    model_id: str
    inputs: list[dict[str, str]]
    settings: dict[str, Any] = field(default_factory=dict)


class ElevenLabsDialogueBuilder:
    """Builder for ElevenLabs Text to Dialogue API requests.

    Constructs request payloads for native multi-role dialogue synthesis
    using ElevenLabs' Text to Dialogue API.

    ElevenLabs Dialogue API Limits:
        - Max characters: 5,000 total across all inputs
        - Model requirement: eleven_v3
        - Max pronunciation dictionaries: 3 per request

    Supported Audio Tags (in text content):
        - Emotions: [sad], [angry], [happily], [excited], [sorrowful]
        - Expressions: [whispers], [shouts], [stuttering], [rushing]
        - Reactions: [laughs], [giggles], [clears throat], [sighs]
        - Flow: [interrupting], [overlapping], [hesitates], [pause]
        - Sound effects: [applause], [leaves rustling]
        - Accents: [strong French accent]
    """

    MAX_CHARS = 5000
    DEFAULT_MODEL = "eleven_v3"

    def __init__(self, config: ElevenLabsDialogueConfig | None = None):
        """Initialize the builder.

        Args:
            config: Optional configuration for dialogue generation.
        """
        self.config = config or ElevenLabsDialogueConfig()

    def build_dialogue_request(
        self,
        turns: list[DialogueTurn],
        voice_map: dict[str, str],
    ) -> ElevenLabsDialogueRequest:
        """Build dialogue request from turns.

        Args:
            turns: List of dialogue turns in order.
            voice_map: Mapping from speaker ID to ElevenLabs voice ID.

        Returns:
            ElevenLabsDialogueRequest ready for API call.

        Raises:
            ValueError: If turns exceed character limit or voice mapping is incomplete.
        """
        if not turns:
            raise ValueError("Turns cannot be empty")

        # Validate voice mappings
        missing_speakers = {t.speaker for t in turns} - set(voice_map.keys())
        if missing_speakers:
            raise ValueError(f"Missing voice mapping for speakers: {missing_speakers}")

        # Check character limit
        total_chars = sum(len(t.text) for t in turns)
        if total_chars > self.MAX_CHARS:
            raise ValueError(
                f"Total text exceeds character limit ({total_chars} > {self.MAX_CHARS}). "
                "Consider using segmented mode."
            )

        # Sort turns by index and build inputs
        sorted_turns = sorted(turns, key=lambda t: t.index)
        inputs = [{"text": turn.text, "voice_id": voice_map[turn.speaker]} for turn in sorted_turns]

        # Build settings
        settings = {
            "stability": self.config.stability,
            "similarity_boost": self.config.similarity_boost,
        }
        if self.config.style > 0:
            settings["style"] = self.config.style
        if self.config.use_speaker_boost:
            settings["use_speaker_boost"] = self.config.use_speaker_boost

        return ElevenLabsDialogueRequest(
            model_id=self.config.model_id,
            inputs=inputs,
            settings=settings,
        )

    def to_api_payload(self, request: ElevenLabsDialogueRequest) -> dict[str, Any]:
        """Convert request to API payload dictionary.

        Args:
            request: Dialogue request object.

        Returns:
            Dictionary ready for JSON serialization and API call.
        """
        return {
            "model_id": request.model_id,
            "inputs": request.inputs,
            "settings": request.settings,
        }

    def estimate_chars(self, turns: list[DialogueTurn]) -> int:
        """Estimate total character count.

        Args:
            turns: List of dialogue turns.

        Returns:
            Total character count of all turn texts.
        """
        return sum(len(t.text) for t in turns)

    def can_use_native(
        self,
        turns: list[DialogueTurn],
        voice_map: dict[str, str],  # noqa: ARG002
    ) -> bool:
        """Check if native mode can be used for the given turns.

        Args:
            turns: List of dialogue turns.
            voice_map: Mapping from speaker ID to voice ID (unused but kept for interface consistency).

        Returns:
            True if native mode is feasible, False otherwise.
        """
        return self.estimate_chars(turns) <= self.MAX_CHARS

    def add_emotion_tag(self, text: str, emotion: str) -> str:
        """Add emotion tag to text.

        Helper method for adding Audio Tags to dialogue text.

        Args:
            text: Original text content.
            emotion: Emotion tag (e.g., "excited", "sad", "whispers").

        Returns:
            Text with emotion tag prepended.

        Example:
            >>> builder.add_emotion_tag("你好！", "excited")
            "[excited] 你好！"
        """
        return f"[{emotion}] {text}"

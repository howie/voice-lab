"""Provider domain entity."""

from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class Provider:
    """Provider reference entity for TTS/STT providers."""

    id: str
    name: str
    display_name: str
    type: list[str]  # ['tts'], ['stt'], ['llm'], or combinations
    is_active: bool = True
    supported_models: dict | None = None
    created_at: datetime = field(default_factory=datetime.utcnow)

    def __post_init__(self) -> None:
        """Validate provider attributes."""
        if not self.id:
            raise ValueError("Provider ID cannot be empty")
        if not self.name:
            raise ValueError("Provider name cannot be empty")
        if not self.display_name:
            raise ValueError("Provider display_name cannot be empty")
        if not self.type or not all(t in ("tts", "stt", "llm") for t in self.type):
            raise ValueError("Provider type must be a list containing 'tts', 'stt', and/or 'llm'")

    @property
    def supports_tts(self) -> bool:
        """Check if provider supports TTS."""
        return "tts" in self.type

    @property
    def supports_stt(self) -> bool:
        """Check if provider supports STT."""
        return "stt" in self.type

    @property
    def supports_llm(self) -> bool:
        """Check if provider supports LLM."""
        return "llm" in self.type

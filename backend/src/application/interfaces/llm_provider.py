"""LLM Provider Interface (Port)."""

from abc import ABC, abstractmethod
from collections.abc import AsyncIterator
from dataclasses import dataclass


@dataclass(frozen=True)
class LLMMessage:
    """Chat message for LLM."""

    role: str  # 'system', 'user', 'assistant'
    content: str


@dataclass
class LLMResponse:
    """Response from LLM."""

    content: str
    latency_ms: int
    input_tokens: int = 0
    output_tokens: int = 0
    model: str = ""


class ILLMProvider(ABC):
    """Abstract interface for LLM providers.

    This interface defines the contract that all LLM provider
    implementations must follow.
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """Get provider name identifier (e.g., 'anthropic', 'openai')."""
        pass

    @property
    @abstractmethod
    def display_name(self) -> str:
        """Get human-readable provider name."""
        pass

    @property
    @abstractmethod
    def default_model(self) -> str:
        """Get default model name."""
        pass

    @abstractmethod
    async def generate(
        self,
        messages: list[LLMMessage],
        max_tokens: int = 150,
        temperature: float = 0.7,
    ) -> LLMResponse:
        """Generate a response from the LLM.

        Args:
            messages: List of chat messages (conversation history)
            max_tokens: Maximum tokens in response
            temperature: Sampling temperature (0.0 - 1.0)

        Returns:
            LLM response with generated text

        Raises:
            LLMProviderError: If generation fails
        """
        pass

    @abstractmethod
    async def generate_stream(
        self,
        messages: list[LLMMessage],
        max_tokens: int = 150,
        temperature: float = 0.7,
    ) -> AsyncIterator[str]:
        """Stream a response from the LLM.

        Args:
            messages: List of chat messages
            max_tokens: Maximum tokens in response
            temperature: Sampling temperature

        Yields:
            Response text chunks as they are generated

        Raises:
            LLMProviderError: If generation fails
        """
        pass

    async def health_check(self) -> bool:
        """Check if the provider is available.

        Returns:
            True if provider is healthy, False otherwise
        """
        return True

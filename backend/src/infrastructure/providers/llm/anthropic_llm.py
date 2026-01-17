"""Anthropic Claude LLM Provider."""

import time

import httpx

from src.application.interfaces.llm_provider import ILLMProvider, LLMMessage, LLMResponse


class AnthropicLLMProvider(ILLMProvider):
    """Anthropic Claude LLM provider implementation."""

    BASE_URL = "https://api.anthropic.com/v1/messages"

    def __init__(self, api_key: str, model: str = "claude-3-haiku-20240307"):
        """Initialize Anthropic LLM provider.

        Args:
            api_key: Anthropic API key
            model: Model to use (default: claude-3-haiku-20240307)
        """
        self._api_key = api_key
        self._model = model

    @property
    def name(self) -> str:
        return "anthropic"

    async def generate(
        self,
        messages: list[LLMMessage],
        max_tokens: int = 150,
        temperature: float = 0.7,
    ) -> LLMResponse:
        """Generate response using Anthropic API."""
        start_time = time.perf_counter()

        headers = {
            "x-api-key": self._api_key,
            "Content-Type": "application/json",
            "anthropic-version": "2023-06-01",
        }

        # Extract system message if present
        system_content = None
        user_messages = []

        for msg in messages:
            if msg.role == "system":
                system_content = msg.content
            else:
                user_messages.append({"role": msg.role, "content": msg.content})

        body = {
            "model": self._model,
            "messages": user_messages,
            "max_tokens": max_tokens,
            "temperature": temperature,
        }

        if system_content:
            body["system"] = system_content

        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(self.BASE_URL, headers=headers, json=body)

            if response.status_code != 200:
                error_detail = response.text
                raise RuntimeError(
                    f"Anthropic API failed with status {response.status_code}: {error_detail}"
                )

            result = response.json()

        latency_ms = int((time.perf_counter() - start_time) * 1000)

        # Extract content from response
        content = ""
        for block in result.get("content", []):
            if block.get("type") == "text":
                content += block.get("text", "")

        usage = result.get("usage", {})

        return LLMResponse(
            content=content,
            provider=self.name,
            model=self._model,
            latency_ms=latency_ms,
            input_tokens=usage.get("input_tokens"),
            output_tokens=usage.get("output_tokens"),
        )

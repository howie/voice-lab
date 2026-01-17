"""OpenAI LLM Provider."""

import time

import httpx

from src.application.interfaces.llm_provider import ILLMProvider, LLMMessage, LLMResponse


class OpenAILLMProvider(ILLMProvider):
    """OpenAI LLM provider implementation."""

    BASE_URL = "https://api.openai.com/v1/chat/completions"

    def __init__(self, api_key: str, model: str = "gpt-4o-mini"):
        """Initialize OpenAI LLM provider.

        Args:
            api_key: OpenAI API key
            model: Model to use (default: gpt-4o-mini)
        """
        self._api_key = api_key
        self._model = model

    @property
    def name(self) -> str:
        return "openai"

    async def generate(
        self,
        messages: list[LLMMessage],
        max_tokens: int = 150,
        temperature: float = 0.7,
    ) -> LLMResponse:
        """Generate response using OpenAI API."""
        start_time = time.perf_counter()

        headers = {
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type": "application/json",
        }

        body = {
            "model": self._model,
            "messages": [{"role": m.role, "content": m.content} for m in messages],
            "max_tokens": max_tokens,
            "temperature": temperature,
        }

        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(self.BASE_URL, headers=headers, json=body)

            if response.status_code != 200:
                error_detail = response.text
                raise RuntimeError(
                    f"OpenAI API failed with status {response.status_code}: {error_detail}"
                )

            result = response.json()

        latency_ms = int((time.perf_counter() - start_time) * 1000)

        content = result["choices"][0]["message"]["content"]
        usage = result.get("usage", {})

        return LLMResponse(
            content=content,
            provider=self.name,
            model=self._model,
            latency_ms=latency_ms,
            input_tokens=usage.get("prompt_tokens"),
            output_tokens=usage.get("completion_tokens"),
        )

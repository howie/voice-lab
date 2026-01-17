"""Google Gemini LLM Provider."""

import time
from collections.abc import AsyncIterator

import httpx

from src.application.interfaces.llm_provider import ILLMProvider, LLMMessage, LLMResponse


class GeminiLLMProvider(ILLMProvider):
    """Google Gemini LLM provider implementation."""

    BASE_URL = "https://generativelanguage.googleapis.com/v1beta/models"

    def __init__(self, api_key: str, model: str = "gemini-2.0-flash-exp"):
        """Initialize Gemini LLM provider.

        Args:
            api_key: Google AI Studio API key
            model: Model to use (default: gemini-2.0-flash-exp)
        """
        self._api_key = api_key
        self._model = model

    @property
    def name(self) -> str:
        """Get provider name identifier."""
        return "gemini"

    @property
    def display_name(self) -> str:
        """Get human-readable provider name."""
        return "Google Gemini"

    @property
    def default_model(self) -> str:
        """Get default model name."""
        return "gemini-2.0-flash-exp"

    async def generate(
        self,
        messages: list[LLMMessage],
        max_tokens: int = 150,
        temperature: float = 0.7,
    ) -> LLMResponse:
        """Generate response using Gemini API.

        Args:
            messages: List of chat messages (conversation history)
            max_tokens: Maximum tokens in response
            temperature: Sampling temperature (0.0 - 1.0)

        Returns:
            LLM response with generated text

        Raises:
            RuntimeError: If API call fails
        """
        start_time = time.perf_counter()

        # Convert messages to Gemini format
        contents = []
        system_instruction = None

        for msg in messages:
            if msg.role == "system":
                # Gemini handles system messages separately
                system_instruction = msg.content
            else:
                # Map 'assistant' to 'model' for Gemini
                role = "model" if msg.role == "assistant" else "user"
                contents.append({"role": role, "parts": [{"text": msg.content}]})

        # Build request body
        body = {
            "contents": contents,
            "generationConfig": {
                "temperature": temperature,
                "maxOutputTokens": max_tokens,
            },
        }

        # Add system instruction if present
        if system_instruction:
            body["systemInstruction"] = {"parts": [{"text": system_instruction}]}

        # Build URL with API key
        url = f"{self.BASE_URL}/{self._model}:generateContent?key={self._api_key}"

        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(url, json=body)

            if response.status_code != 200:
                error_detail = response.text
                raise RuntimeError(
                    f"Gemini API failed with status {response.status_code}: {error_detail}"
                )

            result = response.json()

        latency_ms = int((time.perf_counter() - start_time) * 1000)

        # Extract content from response
        content = ""
        if "candidates" in result and len(result["candidates"]) > 0:
            candidate = result["candidates"][0]
            if "content" in candidate and "parts" in candidate["content"]:
                for part in candidate["content"]["parts"]:
                    if "text" in part:
                        content += part["text"]

        # Extract token usage if available
        usage_metadata = result.get("usageMetadata", {})
        input_tokens = usage_metadata.get("promptTokenCount", 0)
        output_tokens = usage_metadata.get("candidatesTokenCount", 0)

        return LLMResponse(
            content=content,
            provider=self.name,
            model=self._model,
            latency_ms=latency_ms,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
        )

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
            RuntimeError: If streaming is not supported or fails
        """
        # Convert messages to Gemini format
        contents = []
        system_instruction = None

        for msg in messages:
            if msg.role == "system":
                system_instruction = msg.content
            else:
                role = "model" if msg.role == "assistant" else "user"
                contents.append({"role": role, "parts": [{"text": msg.content}]})

        # Build request body
        body = {
            "contents": contents,
            "generationConfig": {
                "temperature": temperature,
                "maxOutputTokens": max_tokens,
            },
        }

        if system_instruction:
            body["systemInstruction"] = {"parts": [{"text": system_instruction}]}

        # Build URL with API key for streaming
        url = f"{self.BASE_URL}/{self._model}:streamGenerateContent?key={self._api_key}&alt=sse"

        async with httpx.AsyncClient(timeout=60.0) as client:  # noqa: SIM117
            async with client.stream("POST", url, json=body) as response:
                if response.status_code != 200:
                    error_detail = await response.aread()
                    raise RuntimeError(
                        f"Gemini streaming API failed with status {response.status_code}: {error_detail.decode()}"
                    )

                async for line in response.aiter_lines():
                    if line.startswith("data: "):
                        try:
                            import json

                            data = json.loads(line[6:])  # Remove "data: " prefix
                            if "candidates" in data and len(data["candidates"]) > 0:
                                candidate = data["candidates"][0]
                                if "content" in candidate and "parts" in candidate["content"]:
                                    for part in candidate["content"]["parts"]:
                                        if "text" in part:
                                            yield part["text"]
                        except json.JSONDecodeError:
                            continue

    async def health_check(self) -> bool:
        """Check if the Gemini API is available.

        Returns:
            True if provider is healthy, False otherwise
        """
        try:
            # Simple health check with minimal message
            test_messages = [LLMMessage(role="user", content="Hi")]
            await self.generate(test_messages, max_tokens=5)
            return True
        except Exception:
            return False

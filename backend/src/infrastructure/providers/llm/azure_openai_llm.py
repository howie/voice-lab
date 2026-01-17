"""Azure OpenAI LLM Provider."""

import time

import httpx

from src.application.interfaces.llm_provider import ILLMProvider, LLMMessage, LLMResponse


class AzureOpenAILLMProvider(ILLMProvider):
    """Azure OpenAI LLM provider implementation."""

    def __init__(
        self,
        api_key: str,
        endpoint: str,
        deployment_name: str,
        api_version: str = "2024-02-01",
    ):
        """Initialize Azure OpenAI LLM provider.

        Args:
            api_key: Azure OpenAI API key
            endpoint: Azure OpenAI endpoint URL
            deployment_name: Model deployment name
            api_version: API version
        """
        self._api_key = api_key
        self._endpoint = endpoint.rstrip("/")
        self._deployment_name = deployment_name
        self._api_version = api_version

    @property
    def name(self) -> str:
        return "azure-openai"

    async def generate(
        self,
        messages: list[LLMMessage],
        max_tokens: int = 150,
        temperature: float = 0.7,
    ) -> LLMResponse:
        """Generate response using Azure OpenAI API."""
        start_time = time.perf_counter()

        url = (
            f"{self._endpoint}/openai/deployments/{self._deployment_name}"
            f"/chat/completions?api-version={self._api_version}"
        )

        headers = {
            "api-key": self._api_key,
            "Content-Type": "application/json",
        }

        body = {
            "messages": [{"role": m.role, "content": m.content} for m in messages],
            "max_tokens": max_tokens,
            "temperature": temperature,
        }

        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(url, headers=headers, json=body)

            if response.status_code != 200:
                error_detail = response.text
                raise RuntimeError(
                    f"Azure OpenAI API failed with status {response.status_code}: {error_detail}"
                )

            result = response.json()

        latency_ms = int((time.perf_counter() - start_time) * 1000)

        content = result["choices"][0]["message"]["content"]
        usage = result.get("usage", {})

        return LLMResponse(
            content=content,
            provider=self.name,
            model=self._deployment_name,
            latency_ms=latency_ms,
            input_tokens=usage.get("prompt_tokens"),
            output_tokens=usage.get("completion_tokens"),
        )

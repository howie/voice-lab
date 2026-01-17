"""Compare Providers Use Case."""

import asyncio
from dataclasses import dataclass, field
from typing import Any

from src.application.interfaces.stt_provider import ISTTProvider
from src.application.interfaces.tts_provider import ITTSProvider
from src.domain.entities.audio import AudioData
from src.domain.entities.stt import STTRequest, STTResult
from src.domain.entities.tts import TTSRequest, TTSResult


@dataclass
class TTSComparisonInput:
    """Input for TTS comparison."""

    text: str
    voice_ids: dict[str, str]  # provider_name -> voice_id
    language: str = "zh-TW"
    speed: float = 1.0
    pitch: float = 0.0


@dataclass
class TTSComparisonResult:
    """Result of TTS comparison for a single provider."""

    provider: str
    success: bool
    result: TTSResult | None = None
    error: str | None = None


@dataclass
class TTSComparisonOutput:
    """Output from TTS comparison."""

    results: list[TTSComparisonResult]
    fastest_provider: str | None = None
    summary: dict[str, Any] = field(default_factory=dict)


@dataclass
class STTComparisonInput:
    """Input for STT comparison."""

    audio: AudioData
    providers: list[str]
    language: str = "zh-TW"
    child_mode: bool = False
    ground_truth: str | None = None


@dataclass
class STTComparisonResult:
    """Result of STT comparison for a single provider."""

    provider: str
    success: bool
    result: STTResult | None = None
    wer: float | None = None
    cer: float | None = None
    error: str | None = None


@dataclass
class STTComparisonOutput:
    """Output from STT comparison."""

    results: list[STTComparisonResult]
    most_accurate_provider: str | None = None
    fastest_provider: str | None = None
    summary: dict[str, Any] = field(default_factory=dict)


class CompareProvidersUseCase:
    """Use case for comparing multiple providers side-by-side.

    This use case runs the same request against multiple providers
    concurrently and compares the results.
    """

    def __init__(
        self,
        tts_providers: dict[str, ITTSProvider],
        stt_providers: dict[str, ISTTProvider],
    ):
        """Initialize use case with dependencies.

        Args:
            tts_providers: Dictionary of TTS providers
            stt_providers: Dictionary of STT providers
        """
        self._tts_providers = tts_providers
        self._stt_providers = stt_providers

    async def compare_tts(self, input_data: TTSComparisonInput) -> TTSComparisonOutput:
        """Compare TTS providers.

        Args:
            input_data: Comparison input with text and voice mappings

        Returns:
            Comparison output with results from all providers
        """
        tasks = []
        for provider_name, voice_id in input_data.voice_ids.items():
            provider = self._tts_providers.get(provider_name)
            if provider:
                request = TTSRequest(
                    text=input_data.text,
                    voice_id=voice_id,
                    provider=provider_name,
                    language=input_data.language,
                    speed=input_data.speed,
                    pitch=input_data.pitch,
                )
                tasks.append(self._run_tts(provider_name, provider, request))

        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Process results
        comparison_results = []
        for result in results:
            if isinstance(result, Exception):
                continue
            comparison_results.append(result)

        # Find fastest
        fastest = None
        min_latency = float("inf")
        for r in comparison_results:
            if r.success and r.result and r.result.latency_ms < min_latency:
                min_latency = r.result.latency_ms
                fastest = r.provider

        # Build summary
        summary = {
            "total_providers": len(comparison_results),
            "successful": sum(1 for r in comparison_results if r.success),
            "failed": sum(1 for r in comparison_results if not r.success),
        }

        return TTSComparisonOutput(
            results=comparison_results,
            fastest_provider=fastest,
            summary=summary,
        )

    async def _run_tts(
        self, provider_name: str, provider: ITTSProvider, request: TTSRequest
    ) -> TTSComparisonResult:
        """Run TTS synthesis for a single provider."""
        try:
            result = await provider.synthesize(request)
            return TTSComparisonResult(
                provider=provider_name,
                success=True,
                result=result,
            )
        except Exception as e:
            return TTSComparisonResult(
                provider=provider_name,
                success=False,
                error=str(e),
            )

    async def compare_stt(self, input_data: STTComparisonInput) -> STTComparisonOutput:
        """Compare STT providers.

        Args:
            input_data: Comparison input with audio and providers

        Returns:
            Comparison output with results from all providers
        """
        tasks = []
        for provider_name in input_data.providers:
            provider = self._stt_providers.get(provider_name)
            if provider:
                request = STTRequest(
                    provider=provider_name,
                    audio=input_data.audio,
                    language=input_data.language,
                    child_mode=input_data.child_mode,
                )
                tasks.append(
                    self._run_stt(provider_name, provider, request, input_data.ground_truth)
                )

        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Process results
        comparison_results = []
        for result in results:
            if isinstance(result, Exception):
                continue
            comparison_results.append(result)

        # Find most accurate (lowest WER)
        most_accurate = None
        min_wer = float("inf")
        for r in comparison_results:
            if r.success and r.wer is not None and r.wer < min_wer:
                min_wer = r.wer
                most_accurate = r.provider

        # Find fastest
        fastest = None
        min_latency = float("inf")
        for r in comparison_results:
            if r.success and r.result and r.result.latency_ms < min_latency:
                min_latency = r.result.latency_ms
                fastest = r.provider

        # Build summary
        summary = {
            "total_providers": len(comparison_results),
            "successful": sum(1 for r in comparison_results if r.success),
            "failed": sum(1 for r in comparison_results if not r.success),
        }

        return STTComparisonOutput(
            results=comparison_results,
            most_accurate_provider=most_accurate,
            fastest_provider=fastest,
            summary=summary,
        )

    async def _run_stt(
        self,
        provider_name: str,
        provider: ISTTProvider,
        request: STTRequest,
        ground_truth: str | None,
    ) -> STTComparisonResult:
        """Run STT transcription for a single provider."""
        try:
            result = await provider.transcribe(request)

            wer = None
            cer = None
            if ground_truth:
                from src.domain.services import calculate_cer, calculate_wer

                wer = calculate_wer(ground_truth, result.transcript)
                cer = calculate_cer(ground_truth, result.transcript)

            return STTComparisonResult(
                provider=provider_name,
                success=True,
                result=result,
                wer=wer,
                cer=cer,
            )
        except Exception as e:
            return STTComparisonResult(
                provider=provider_name,
                success=False,
                error=str(e),
            )

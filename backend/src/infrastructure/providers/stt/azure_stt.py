"""Azure Cognitive Services Speech-to-Text Provider."""

import asyncio
from collections.abc import AsyncIterator

import azure.cognitiveservices.speech as speechsdk

from src.domain.entities.audio import AudioData, AudioFormat
from src.domain.entities.stt import STTRequest, STTResult, WordTiming
from src.domain.errors import QuotaExceededError
from src.infrastructure.providers.stt.base import BaseSTTProvider


class AzureSTTProvider(BaseSTTProvider):
    """Azure Cognitive Services STT provider implementation."""

    def __init__(self, subscription_key: str, region: str):
        """Initialize Azure STT provider.

        Args:
            subscription_key: Azure subscription key
            region: Azure region (e.g., "eastasia")
        """
        super().__init__("azure")
        self._subscription_key = subscription_key
        self._region = region

    @property
    def display_name(self) -> str:
        return "Azure Cognitive Services STT"

    @property
    def supported_languages(self) -> list[str]:
        return ["zh-TW", "zh-CN", "en-US", "ja-JP", "ko-KR"]

    def _create_speech_config(self, language: str) -> speechsdk.SpeechConfig:
        """Create speech config for recognition."""
        config = speechsdk.SpeechConfig(
            subscription=self._subscription_key,
            region=self._region,
        )
        config.speech_recognition_language = self._map_language(language)
        config.request_word_level_timestamps()
        config.enable_dictation()

        return config

    @property
    def supports_child_mode(self) -> bool:
        return True

    async def _do_transcribe(
        self, request: STTRequest
    ) -> tuple[str, list[WordTiming] | None, float | None]:
        """Transcribe audio using Azure STT."""
        if request.audio is None and request.audio_url is None:
            raise ValueError("Either audio or audio_url must be provided")

        config = self._create_speech_config(request.language)

        # Create audio config from bytes or URL
        if request.audio:
            import os
            import tempfile

            audio_bytes = request.audio.data

            # Azure SDK only supports WAV files via AudioConfig(filename=...)
            # Convert non-WAV formats (e.g. WebM from browser recording) to WAV
            if request.audio.format != AudioFormat.WAV:
                audio_bytes = self._convert_to_wav(audio_bytes, request.audio.format, request.audio)

            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
                f.write(audio_bytes)
                temp_path = f.name

            try:
                audio_config = speechsdk.AudioConfig(filename=temp_path)
                result = await self._recognize(config, audio_config, request.child_mode)
            finally:
                os.unlink(temp_path)
        else:
            # URL not directly supported, would need to download first
            raise NotImplementedError("Azure STT does not support URL input directly")

        return result

    async def _recognize(
        self,
        speech_config: speechsdk.SpeechConfig,
        audio_config: speechsdk.AudioConfig,
        child_mode: bool = False,
    ) -> tuple[str, list[WordTiming] | None, float | None]:
        """Perform recognition."""
        recognizer = speechsdk.SpeechRecognizer(
            speech_config=speech_config,
            audio_config=audio_config,
        )

        if child_mode:
            # Add phrase hints for child speech optimization
            grammar = speechsdk.PhraseListGrammar.from_recognizer(recognizer)
            phrases = [
                "媽媽",
                "爸爸",
                "老師",
                "小朋友",
                "學校",
                "吃飯",
                "睡覺",
                "玩遊戲",
                "開心",
                "難過",
                "生氣",
                "mommy",
                "daddy",
                "teacher",
                "school",
                "play",
                "game",
                "happy",
                "sad",
            ]
            for phrase in phrases:
                grammar.addPhrase(phrase)

        # Collect results
        transcript_parts = []
        word_timings = []
        done = asyncio.Event()
        error = None

        def on_recognized(evt):
            if evt.result.reason == speechsdk.ResultReason.RecognizedSpeech:
                transcript_parts.append(evt.result.text)

                # Extract word timings from JSON
                try:
                    import json

                    details = json.loads(
                        evt.result.properties.get(
                            speechsdk.PropertyId.SpeechServiceResponse_JsonResult, "{}"
                        )
                    )

                    for word in details.get("NBest", [{}])[0].get("Words", []):
                        offset_ticks = word.get("Offset", 0)
                        duration_ticks = word.get("Duration", 0)
                        word_timings.append(
                            WordTiming(
                                word=word.get("Word", ""),
                                start_ms=int(offset_ticks / 10000),
                                end_ms=int((offset_ticks + duration_ticks) / 10000),
                                confidence=word.get("Confidence", 0.0),
                            )
                        )
                except Exception:
                    pass

        def on_canceled(evt):
            nonlocal error
            if evt.reason == speechsdk.CancellationReason.Error:
                error_details = evt.error_details or ""
                # T015: Detect 429 quota exceeded from Azure error details
                if "429" in error_details or "quota" in error_details.lower():
                    error = QuotaExceededError(
                        provider="azure",
                        original_error=error_details,
                    )
                else:
                    error = RuntimeError(f"Azure STT error: {error_details}")
            done.set()

        def on_session_stopped(_evt):
            done.set()

        recognizer.recognized.connect(on_recognized)
        recognizer.canceled.connect(on_canceled)
        recognizer.session_stopped.connect(on_session_stopped)

        # Start recognition
        await asyncio.to_thread(recognizer.start_continuous_recognition)

        # Wait for completion
        await done.wait()

        await asyncio.to_thread(recognizer.stop_continuous_recognition)

        if error:
            raise error

        transcript = " ".join(transcript_parts)
        avg_confidence = (
            sum(w.confidence for w in word_timings) / len(word_timings) if word_timings else None
        )
        return transcript, word_timings if word_timings else None, avg_confidence

    async def transcribe_stream(
        self, audio_stream: AsyncIterator[bytes], language: str = "zh-TW"
    ) -> AsyncIterator[STTResult]:
        """Stream transcription using Azure STT."""
        config = self._create_speech_config(language)

        # Create push stream
        push_stream = speechsdk.audio.PushAudioInputStream()
        audio_config = speechsdk.AudioConfig(stream=push_stream)

        recognizer = speechsdk.SpeechRecognizer(
            speech_config=config,
            audio_config=audio_config,
        )

        result_queue: asyncio.Queue = asyncio.Queue()
        done = asyncio.Event()

        def on_recognizing(evt):
            if evt.result.reason == speechsdk.ResultReason.RecognizingSpeech:
                asyncio.run_coroutine_threadsafe(
                    result_queue.put(
                        STTResult(
                            transcript=evt.result.text,
                            provider=self.name,
                            language=language,
                            latency_ms=0,
                            is_final=False,
                        )
                    ),
                    asyncio.get_event_loop(),
                )

        def on_recognized(evt):
            if evt.result.reason == speechsdk.ResultReason.RecognizedSpeech:
                asyncio.run_coroutine_threadsafe(
                    result_queue.put(
                        STTResult(
                            transcript=evt.result.text,
                            provider=self.name,
                            language=language,
                            latency_ms=0,
                            is_final=True,
                        )
                    ),
                    asyncio.get_event_loop(),
                )

        def on_session_stopped(_evt):
            done.set()

        recognizer.recognizing.connect(on_recognizing)
        recognizer.recognized.connect(on_recognized)
        recognizer.session_stopped.connect(on_session_stopped)

        # Start recognition
        await asyncio.to_thread(recognizer.start_continuous_recognition)

        try:
            # Feed audio chunks
            async for chunk in audio_stream:
                push_stream.write(chunk)

            push_stream.close()

            # Yield results until done
            while not done.is_set() or not result_queue.empty():
                try:
                    result = await asyncio.wait_for(result_queue.get(), timeout=0.1)
                    yield result
                except TimeoutError:
                    continue
        finally:
            await asyncio.to_thread(recognizer.stop_continuous_recognition)

    @property
    def supports_streaming(self) -> bool:
        return True

    @staticmethod
    def _convert_to_wav(
        audio_bytes: bytes,
        audio_format: AudioFormat,
        audio_data: AudioData,
    ) -> bytes:
        """Convert non-WAV audio bytes to WAV format for Azure SDK.

        Args:
            audio_bytes: Raw audio bytes to convert.
            audio_format: The source audio format.
            audio_data: AudioData with metadata (sample_rate, channels).

        Returns:
            WAV-encoded bytes.

        Raises:
            RuntimeError: If conversion fails.
        """
        import io

        from pydub import AudioSegment

        try:
            if audio_format == AudioFormat.PCM:
                segment = AudioSegment(
                    data=audio_bytes,
                    sample_width=2,
                    frame_rate=audio_data.sample_rate,
                    channels=audio_data.channels,
                )
            else:
                segment = AudioSegment.from_file(io.BytesIO(audio_bytes), format=audio_format.value)
            wav_buffer = io.BytesIO()
            segment.export(wav_buffer, format="wav")
            return wav_buffer.getvalue()
        except Exception as e:
            raise RuntimeError(
                f"Failed to convert {audio_format.value} to WAV for Azure STT: {e}"
            ) from e

    def _map_language(self, language: str) -> str:
        """Map language code to Azure format."""
        mapping = {
            "zh-TW": "zh-TW",
            "zh-CN": "zh-CN",
            "en-US": "en-US",
            "ja-JP": "ja-JP",
        }
        return mapping.get(language, language)

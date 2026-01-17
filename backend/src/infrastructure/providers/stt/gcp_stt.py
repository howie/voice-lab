"""Google Cloud Speech-to-Text Provider."""

from collections.abc import AsyncIterator

from google.cloud import speech_v1 as speech

from src.domain.entities.audio import AudioData, AudioFormat
from src.domain.entities.stt import STTRequest, STTResult, WordTiming
from src.infrastructure.providers.stt.base import BaseSTTProvider


class GCPSTTProvider(BaseSTTProvider):
    """Google Cloud STT provider implementation."""

    _ENCODING_MAP = {
        AudioFormat.WAV: speech.RecognitionConfig.AudioEncoding.LINEAR16,
        AudioFormat.MP3: speech.RecognitionConfig.AudioEncoding.MP3,
        AudioFormat.OGG: speech.RecognitionConfig.AudioEncoding.OGG_OPUS,
        AudioFormat.WEBM: speech.RecognitionConfig.AudioEncoding.WEBM_OPUS,
        AudioFormat.FLAC: speech.RecognitionConfig.AudioEncoding.FLAC,
    }

    def __init__(self, credentials_path: str | None = None):
        """Initialize GCP STT provider.

        Args:
            credentials_path: Path to GCP service account JSON file.
                            If None, uses default credentials.
        """
        super().__init__("gcp")

        if credentials_path:
            self._client = speech.SpeechClient.from_service_account_json(
                credentials_path
            )
        else:
            self._client = speech.SpeechClient()

    async def _do_transcribe(
        self, request: STTRequest
    ) -> tuple[str, list[WordTiming] | None, float | None]:
        """Transcribe audio using GCP STT."""
        import asyncio

        if request.audio is None and request.audio_url is None:
            raise ValueError("Either audio or audio_url must be provided")

        # Build recognition config
        config = speech.RecognitionConfig(
            encoding=self._get_encoding(request.audio),
            sample_rate_hertz=request.audio.sample_rate if request.audio else 16000,
            language_code=self._map_language(request.language),
            enable_word_time_offsets=True,
            enable_automatic_punctuation=True,
            model="latest_long" if not request.child_mode else "command_and_search",
        )

        # Add child mode specific config
        if request.child_mode:
            # Use alternative language models that work better with children
            config = speech.RecognitionConfig(
                encoding=self._get_encoding(request.audio),
                sample_rate_hertz=request.audio.sample_rate if request.audio else 16000,
                language_code=self._map_language(request.language),
                enable_word_time_offsets=True,
                enable_automatic_punctuation=True,
                model="command_and_search",
                speech_contexts=[
                    speech.SpeechContext(
                        phrases=["媽媽", "爸爸", "老師", "小朋友"],
                        boost=10.0,
                    )
                ],
            )

        # Build audio
        if request.audio:
            audio = speech.RecognitionAudio(content=request.audio.data)
        else:
            audio = speech.RecognitionAudio(uri=request.audio_url)

        # Call API
        response = await asyncio.to_thread(
            self._client.recognize,
            config=config,
            audio=audio,
        )

        # Process results
        if not response.results:
            return "", None, None

        transcript_parts = []
        word_timings = []
        confidences = []

        for result in response.results:
            if not result.alternatives:
                continue

            alternative = result.alternatives[0]
            transcript_parts.append(alternative.transcript)
            confidences.append(alternative.confidence)

            # Extract word timings
            for word_info in alternative.words:
                word_timings.append(
                    WordTiming(
                        word=word_info.word,
                        start_time=word_info.start_time.total_seconds(),
                        end_time=word_info.end_time.total_seconds(),
                        confidence=alternative.confidence,
                    )
                )

        transcript = " ".join(transcript_parts)
        avg_confidence = sum(confidences) / len(confidences) if confidences else None

        return transcript, word_timings if word_timings else None, avg_confidence

    async def transcribe_stream(
        self, audio_stream: AsyncIterator[bytes], language: str = "zh-TW"
    ) -> AsyncIterator[STTResult]:
        """Stream transcription using GCP STT."""
        import asyncio
        import queue
        import threading

        # Create streaming config
        config = speech.RecognitionConfig(
            encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
            sample_rate_hertz=16000,
            language_code=self._map_language(language),
            enable_automatic_punctuation=True,
        )

        streaming_config = speech.StreamingRecognitionConfig(
            config=config,
            interim_results=True,
        )

        # Use queue for thread communication
        audio_queue: queue.Queue = queue.Queue()
        result_queue: queue.Queue = queue.Queue()
        stop_event = threading.Event()

        def request_generator():
            # First request with config
            yield speech.StreamingRecognizeRequest(streaming_config=streaming_config)

            while not stop_event.is_set():
                try:
                    chunk = audio_queue.get(timeout=0.1)
                    if chunk is None:
                        break
                    yield speech.StreamingRecognizeRequest(audio_content=chunk)
                except queue.Empty:
                    continue

        def run_streaming():
            try:
                responses = self._client.streaming_recognize(request_generator())
                for response in responses:
                    for result in response.results:
                        if result.alternatives:
                            result_queue.put(result)
            except Exception as e:
                result_queue.put(e)
            finally:
                result_queue.put(None)

        # Start streaming thread
        thread = threading.Thread(target=run_streaming)
        thread.start()

        try:
            # Feed audio chunks
            async for chunk in audio_stream:
                audio_queue.put(chunk)

            audio_queue.put(None)  # Signal end

            # Yield results
            while True:
                try:
                    result = await asyncio.to_thread(result_queue.get, timeout=1.0)
                    if result is None:
                        break
                    if isinstance(result, Exception):
                        raise result

                    alternative = result.alternatives[0]
                    yield STTResult(
                        transcript=alternative.transcript,
                        provider=self.name,
                        language=language,
                        latency_ms=0,
                        confidence=alternative.confidence,
                        is_final=result.is_final,
                    )
                except queue.Empty:
                    continue
        finally:
            stop_event.set()
            thread.join(timeout=5.0)

    @property
    def supports_streaming(self) -> bool:
        return True

    def _get_encoding(self, audio: AudioData | None) -> speech.RecognitionConfig.AudioEncoding:
        """Get encoding for audio format."""
        if audio is None:
            return speech.RecognitionConfig.AudioEncoding.ENCODING_UNSPECIFIED

        return self._ENCODING_MAP.get(
            audio.format,
            speech.RecognitionConfig.AudioEncoding.ENCODING_UNSPECIFIED,
        )

    def _map_language(self, language: str) -> str:
        """Map language code to GCP format."""
        mapping = {
            "zh-TW": "cmn-Hant-TW",
            "zh-CN": "cmn-Hans-CN",
            "en-US": "en-US",
            "ja-JP": "ja-JP",
        }
        return mapping.get(language, language)

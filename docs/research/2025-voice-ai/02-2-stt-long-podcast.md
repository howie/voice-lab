# STT 長時間音檔處理研究

> 最後更新：2026-01

## 概述

本文研究各家 STT 服務對長時間音檔（如 Podcast、會議錄音）的支援情況，包括原生支援的時長限制、分段處理策略，以及自行實作的最佳實踐。

## 各服務商時長限制比較

| 服務 | 最大時長 | 最大檔案大小 | 處理方式 | 備註 |
|------|---------|-------------|---------|------|
| **ElevenLabs** | 10 小時 | 3 GB | 批次（內部並行分段） | 🏆 最長支援 |
| **Google Cloud** | 8 小時 (480 分鐘) | 依據 GCS | 批次（非同步） | 需存放 Cloud Storage |
| **AssemblyAI** | 無明確限制 | 無明確限制 | 批次/串流 | 按時長計費 |
| **Deepgram** | 10-20 分鐘處理時間 | 無明確限制 | 批次/串流 | Nova: 10 分鐘, Whisper: 20 分鐘 |
| **Azure Speech** | 依據方案 | 依據方案 | 批次/串流 | 企業方案較寬 |
| **OpenAI Whisper API** | 25 分鐘 | 25 MB | 批次 | GPT-4o-transcribe |
| **OpenAI Whisper (自架)** | 無限制 | 無限制 | 自行控制 | 需自行分段 |

---

## 各服務商詳細說明

### 1. ElevenLabs Scribe (推薦)

**最大支援**: 10 小時 / 3 GB

**特點**:
- 🟢 原生支援超長音檔
- 🟢 內部自動分段並行處理（8 分鐘以上自動切成 4 段）
- 🟢 處理速度：20-50x 即時速度

**API 使用**:
```python
from elevenlabs import ElevenLabs

client = ElevenLabs(api_key=api_key)

# 直接上傳長音檔，無需自行分段
result = client.speech_to_text.convert(
    audio=open("podcast_2hours.mp3", "rb"),
    model_id="scribe_v2",
    language_code="zh"
)
```

**定價**: $0.40/hour

**參考**: [ElevenLabs Speech to Text](https://elevenlabs.io/docs/capabilities/speech-to-text)

---

### 2. Google Cloud Speech-to-Text

**最大支援**: 8 小時 (批次非同步模式)

**限制**:
- 同步請求: 60 秒
- 串流請求: 5 分鐘
- 非同步請求: 480 分鐘 (8 小時)
- 串流訊息: 10 MB

**使用方式**:
```python
from google.cloud import speech

client = speech.SpeechClient()

# 長音檔需存放 Cloud Storage
audio = speech.RecognitionAudio(uri="gs://bucket/long_podcast.wav")

config = speech.RecognitionConfig(
    encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
    language_code="zh-TW",
    enable_automatic_punctuation=True
)

# 使用非同步 API
operation = client.long_running_recognize(config=config, audio=audio)
response = operation.result(timeout=3600)  # 等待最多 1 小時
```

**注意**: 非同步請求需將音檔上傳至 Google Cloud Storage

**參考**: [Google Cloud Batch Recognize](https://cloud.google.com/speech-to-text/v2/docs/batch-recognize)

---

### 3. AssemblyAI

**最大支援**: 無明確時長限制

**特點**:
- 🟢 支援超長音檔
- 🟢 可透過 URL 或直接上傳
- 🟢 自動處理，無需手動分段

**API 使用**:
```python
import assemblyai as aai

aai.settings.api_key = "YOUR_API_KEY"

transcriber = aai.Transcriber()

# 直接轉錄長音檔
transcript = transcriber.transcribe(
    "https://example.com/long_podcast.mp3",
    config=aai.TranscriptionConfig(
        language_code="zh",
        speaker_labels=True
    )
)
```

**定價**: $0.15/hour (所有語言同價)

**參考**: [AssemblyAI Docs](https://www.assemblyai.com/docs)

---

### 4. Deepgram

**最大處理時間**:
- Nova/Base/Enhanced 模型: 10 分鐘處理時間
- Whisper 模型: 20 分鐘處理時間

**注意**: 這是「處理時間」限制，非音檔時長限制。超時會返回 504 Gateway Timeout。

**建議**: 長音檔需自行分段處理

**API 使用**:
```python
from deepgram import DeepgramClient

deepgram = DeepgramClient(api_key)

# 對於長音檔，建議分段處理
# 或使用串流方式逐步傳送
```

**參考**: [Deepgram Pre-recorded](https://developers.deepgram.com/docs/pre-recorded-audio)

---

### 5. OpenAI Whisper API

**限制**:
- GPT-4o-transcribe: 25 分鐘 (1500 秒)
- Whisper API: 25 MB 檔案大小

**超過限制時**: 必須自行分段

**API 使用**:
```python
import openai

# 短音檔直接使用
response = openai.Audio.transcribe(
    model="whisper-1",
    file=open("short_audio.mp3", "rb")
)

# 長音檔需分段處理 (見下方策略)
```

**參考**: [OpenAI Speech to Text](https://platform.openai.com/docs/guides/speech-to-text)

---

## 自行分段處理策略

當 STT 服務有時長限制時，需要自行實作分段處理。

### 策略 1: 固定時長分段

**優點**: 實作簡單
**缺點**: 可能在句子中間切斷

```python
from pydub import AudioSegment

def split_audio_fixed(audio_path: str, chunk_minutes: int = 10):
    """固定時長分段"""
    audio = AudioSegment.from_file(audio_path)
    chunk_length_ms = chunk_minutes * 60 * 1000

    chunks = []
    for i, start in enumerate(range(0, len(audio), chunk_length_ms)):
        chunk = audio[start:start + chunk_length_ms]
        chunk_path = f"/tmp/chunk_{i}.mp3"
        chunk.export(chunk_path, format="mp3")
        chunks.append({
            "path": chunk_path,
            "start_ms": start,
            "index": i
        })

    return chunks
```

### 策略 2: 靜音偵測分段 (推薦)

**優點**: 在自然停頓處切分，避免截斷句子
**缺點**: 分段長度不一致

```python
from pydub import AudioSegment
from pydub.silence import split_on_silence

def split_audio_on_silence(
    audio_path: str,
    min_silence_len: int = 700,      # 最小靜音長度 (ms)
    silence_thresh: int = -40,        # 靜音閾值 (dB)
    max_chunk_length: int = 600000    # 最大分段長度 10 分鐘 (ms)
):
    """基於靜音偵測分段"""
    audio = AudioSegment.from_file(audio_path)

    chunks = split_on_silence(
        audio,
        min_silence_len=min_silence_len,
        silence_thresh=silence_thresh,
        keep_silence=200  # 保留部分靜音作為緩衝
    )

    # 合併過短的分段，分割過長的分段
    processed_chunks = []
    current_chunk = AudioSegment.empty()

    for chunk in chunks:
        if len(current_chunk) + len(chunk) < max_chunk_length:
            current_chunk += chunk
        else:
            if len(current_chunk) > 0:
                processed_chunks.append(current_chunk)
            current_chunk = chunk

    if len(current_chunk) > 0:
        processed_chunks.append(current_chunk)

    return processed_chunks
```

### 策略 3: VAD (Voice Activity Detection) 分段

**優點**: 更精確的語音邊界偵測
**缺點**: 需要額外依賴

```python
import webrtcvad
import wave

def split_audio_vad(audio_path: str, aggressiveness: int = 2):
    """使用 WebRTC VAD 進行分段"""
    vad = webrtcvad.Vad(aggressiveness)  # 0-3, 3 最激進

    # 讀取音檔 (需要 16-bit PCM)
    with wave.open(audio_path, 'rb') as wf:
        sample_rate = wf.getframerate()
        frames = wf.readframes(wf.getnframes())

    # VAD 需要 10/20/30 ms 的 frame
    frame_duration_ms = 30
    frame_size = int(sample_rate * frame_duration_ms / 1000) * 2

    segments = []
    current_segment_start = 0
    is_speech = False

    for i in range(0, len(frames), frame_size):
        frame = frames[i:i + frame_size]
        if len(frame) < frame_size:
            break

        speech_detected = vad.is_speech(frame, sample_rate)

        if speech_detected and not is_speech:
            current_segment_start = i
            is_speech = True
        elif not speech_detected and is_speech:
            segments.append((current_segment_start, i))
            is_speech = False

    return segments
```

---

## 分段後合併轉錄結果

### 時間戳校正

分段後每個 chunk 的時間戳是相對的，需要校正為絕對時間：

```python
def merge_transcripts_with_timestamps(
    transcripts: list,
    chunk_start_times: list[float]  # 每個 chunk 的起始時間 (秒)
) -> dict:
    """合併多個分段的轉錄結果，校正時間戳"""
    merged_words = []
    merged_text = []

    for i, transcript in enumerate(transcripts):
        offset = chunk_start_times[i]

        # 校正 word-level 時間戳
        if "words" in transcript:
            for word in transcript["words"]:
                merged_words.append({
                    "word": word["word"],
                    "start": word["start"] + offset,
                    "end": word["end"] + offset,
                    "confidence": word.get("confidence", 1.0)
                })

        merged_text.append(transcript.get("text", ""))

    return {
        "text": " ".join(merged_text),
        "words": merged_words
    }
```

### 處理邊界問題

分段邊界可能導致：
1. **句子被截斷**: 使用前一段最後幾秒作為 context
2. **重複內容**: 分段有重疊時去重
3. **說話者標籤不一致**: 需要跨段落重新識別

```python
def transcribe_with_overlap(
    audio_chunks: list,
    overlap_seconds: float = 5.0,
    transcribe_fn: callable
) -> str:
    """帶重疊的分段轉錄"""
    results = []
    prev_context = ""

    for i, chunk in enumerate(audio_chunks):
        # 使用前一段的結尾作為 prompt
        transcript = transcribe_fn(
            chunk,
            prompt=prev_context  # 提供上下文
        )

        # 去除重疊部分的重複文字
        if i > 0:
            transcript = remove_overlap(results[-1], transcript, overlap_seconds)

        results.append(transcript)
        prev_context = transcript[-200:]  # 保留最後 200 字作為下一段 context

    return " ".join(results)
```

---

## 並行處理加速

對於超長音檔，可並行處理多個分段：

```python
import asyncio
from concurrent.futures import ThreadPoolExecutor

async def transcribe_parallel(
    audio_chunks: list,
    transcribe_fn: callable,
    max_workers: int = 4
) -> list:
    """並行轉錄多個分段"""
    loop = asyncio.get_event_loop()

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        tasks = [
            loop.run_in_executor(executor, transcribe_fn, chunk)
            for chunk in audio_chunks
        ]
        results = await asyncio.gather(*tasks)

    return results


# 使用範例
async def process_long_podcast(audio_path: str):
    # 1. 分段
    chunks = split_audio_on_silence(audio_path)

    # 2. 並行轉錄
    transcripts = await transcribe_parallel(chunks, transcribe_fn)

    # 3. 合併結果
    final = merge_transcripts_with_timestamps(transcripts, chunk_times)

    return final
```

---

## 推薦方案

### 依音檔長度選擇

| 音檔長度 | 推薦方案 | 原因 |
|---------|---------|------|
| < 25 分鐘 | OpenAI Whisper | 簡單、高品質 |
| 25 分鐘 - 2 小時 | AssemblyAI / Deepgram | 原生支援、性價比高 |
| 2 - 10 小時 | ElevenLabs Scribe | 內建並行、最長支援 |
| > 8 小時或自控需求 | Google Cloud 非同步 | 8 小時上限、企業級 |
| 無限制 + 成本敏感 | Whisper 自架 + 分段 | 完全自控 |

### 成本估算 (10 小時 Podcast)

| 服務 | 估算成本 | 備註 |
|------|---------|------|
| ElevenLabs | $4.00 | 原生支援，最簡單 |
| AssemblyAI | $1.50 | 性價比最高 |
| Deepgram | ~$2.60 | 需確認處理時間限制 |
| Google Cloud | ~$9.60 | 企業級 |
| Whisper (自架) | 電費+GPU 成本 | 需自行維護 |

---

## 實作建議

### 1. 優先使用原生長音檔支援

如果預算允許，直接使用 ElevenLabs 或 AssemblyAI 的原生長音檔支援，避免自行實作分段邏輯。

### 2. 必須自行分段時

1. **使用靜音偵測**而非固定時長分段
2. **加入重疊區域**處理邊界問題
3. **保留上下文**作為下一段的 prompt
4. **並行處理**加速整體速度
5. **校正時間戳**確保最終結果正確

### 3. 監控與錯誤處理

```python
def transcribe_with_retry(
    chunk: bytes,
    max_retries: int = 3,
    timeout: int = 300
) -> dict:
    """帶重試機制的轉錄"""
    for attempt in range(max_retries):
        try:
            return transcribe_fn(chunk, timeout=timeout)
        except TimeoutError:
            if attempt == max_retries - 1:
                raise
            # 可能是 chunk 太大，嘗試再分段
            continue
        except RateLimitError:
            time.sleep(2 ** attempt)  # 指數退避
            continue

    raise Exception("Max retries exceeded")
```

---

## 更新日誌

| 日期 | 變更 |
|------|------|
| 2026-01 | 初始版本 |

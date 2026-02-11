# Quickstart: Long Text TTS

## Overview

Long Text TTS 讓使用者可以合成超過 provider 字數限制的文字。系統會自動在語意邊界（句號、逗號等）分段，逐段合成後合併成完整音訊。

## Usage

### API — 無需任何改動

現有的 `POST /api/v1/tts/synthesize` endpoint 會自動偵測並處理超長文字：

```bash
# 短文字 (< provider limit) — 走原有快速路徑
curl -X POST http://localhost:8000/api/v1/tts/synthesize \
  -H "Content-Type: application/json" \
  -d '{
    "text": "你好世界",
    "provider": "gemini",
    "voice_id": "Kore"
  }'

# 長文字 (> provider limit) — 自動分段合成
curl -X POST http://localhost:8000/api/v1/tts/synthesize \
  -H "Content-Type: application/json" \
  -d '{
    "text": "這是一段非常長的文字，包含多個段落和句子...（2000+ 字）",
    "provider": "gemini",
    "voice_id": "Kore",
    "segment_gap_ms": 100,
    "segment_crossfade_ms": 30
  }'
```

### Preview Segmentation

在合成前預覽分段計畫：

```bash
curl -X POST http://localhost:8000/api/v1/tts/synthesize/preview \
  -H "Content-Type: application/json" \
  -d '{
    "text": "這是一段非常長的文字...",
    "provider": "gemini"
  }'

# Response:
# {
#   "needs_segmentation": true,
#   "segment_count": 5,
#   "segments": [
#     {"index": 0, "text_preview": "這是一段非常長的文字，包含...", "char_length": 420, "byte_length": 1260, "boundary_type": "sentence"},
#     ...
#   ],
#   "estimated_duration_seconds": 25.0
# }
```

### Response Metadata

當分段合成發生時，response 會包含額外的 `metadata`：

```json
{
  "audio_content": "base64...",
  "content_type": "audio/mpeg",
  "duration_ms": 45000,
  "latency_ms": 25000,
  "metadata": {
    "segmented": true,
    "segment_count": 5,
    "total_text_chars": 2100,
    "total_text_bytes": 6300,
    "segment_timings": [
      {"index": 0, "start_ms": 0, "end_ms": 9200},
      {"index": 1, "start_ms": 9300, "end_ms": 18100},
      ...
    ]
  }
}
```

## Provider Limits Reference

| Provider | Limit Type | Max per Segment | Effective CJK Chars |
|----------|-----------|-----------------|---------------------|
| gemini | bytes | 4,000 | ~1,333 |
| azure | chars | 5,000 | 5,000 |
| elevenlabs | chars | 5,000 | 5,000 |
| gcp | chars | 5,000 | 5,000 |
| openai | chars | 4,096 | 4,096 |
| voai | chars | 500 | 500 |

## Configuration

### Segment Gap & Crossfade

| Parameter | Default | Range | Description |
|-----------|---------|-------|-------------|
| `segment_gap_ms` | 100 | 0-2000 | Silence between segments |
| `segment_crossfade_ms` | 30 | 0-500 | Crossfade overlap for smooth transition |

**Tip**: 對於旁白/朗讀場景，`gap_ms=100` + `crossfade_ms=30` 效果最自然。對話場景可以加大 gap 到 200-300ms。

### Global Max Text Length

系統的絕對上限是 **50,000 字元**。這足以涵蓋大多數使用場景（約 30 分鐘的中文語音）。

## Testing

```bash
# Run long text TTS tests
pytest backend/tests -k "long_text" -v

# Run text splitter unit tests
pytest backend/tests -k "text_splitter" -v
```

## Architecture

```
POST /api/v1/tts/synthesize
    │
    ├── text <= provider_limit → SynthesizeSpeech (existing, no change)
    │
    └── text > provider_limit  → SynthesizeLongText (new use case)
            │
            ├── TextSplitter.split(text) → TextSegment[]
            │
            ├── Wrap as DialogueTurn[] (same speaker)
            │
            └── SegmentedMergerService.synthesize_and_merge()
                    ├── Per-segment TTS synthesis
                    ├── pydub audio merge (gap + crossfade)
                    └── Volume normalization
```

# Data Model: Multi-Role TTS

**Feature**: 005-multi-role-tts
**Date**: 2025-01-19

## Domain Entities

### DialogueTurn

對話中的單一發言單位。

```python
@dataclass
class DialogueTurn:
    """Represents a single turn in a dialogue."""

    speaker: str
    """Speaker identifier (e.g., 'A', 'B', 'Host')."""

    text: str
    """The text content of this turn."""

    index: int
    """Position in the dialogue sequence (0-based)."""
```

**Validation Rules**:
- `speaker`: 非空字串，最長 50 字元
- `text`: 非空字串
- `index`: >= 0

### VoiceAssignment

說話者與語音的對應關係。

```python
@dataclass
class VoiceAssignment:
    """Maps a speaker to a voice."""

    speaker: str
    """Speaker identifier matching DialogueTurn.speaker."""

    voice_id: str
    """Provider-specific voice ID."""

    voice_name: str | None = None
    """Human-readable voice name (optional, for display)."""
```

**Validation Rules**:
- `speaker`: 非空字串
- `voice_id`: 非空字串，符合 Provider 的 voice ID 格式

### MultiRoleSupportType

Provider 多角色支援類型列舉。

```python
from enum import Enum

class MultiRoleSupportType(str, Enum):
    """Type of multi-role support a provider offers."""

    NATIVE = "native"
    """Provider supports multi-role natively in a single request."""

    SEGMENTED = "segmented"
    """Provider requires separate requests per speaker, merged afterward."""

    UNSUPPORTED = "unsupported"
    """Provider does not support multi-role TTS."""
```

### ProviderMultiRoleCapability

Provider 的多角色能力描述。

```python
@dataclass
class ProviderMultiRoleCapability:
    """Describes a provider's multi-role capabilities."""

    provider_name: str
    """Provider identifier (e.g., 'elevenlabs', 'azure')."""

    support_type: MultiRoleSupportType
    """Type of multi-role support."""

    max_speakers: int
    """Maximum number of speakers supported."""

    character_limit: int
    """Maximum total characters for the dialogue."""

    advanced_features: list[str]
    """List of advanced features (e.g., 'interrupting', 'overlapping')."""

    notes: str | None = None
    """Additional notes about this provider's capabilities."""
```

**Provider Capability Data**:

| Provider | support_type | max_speakers | character_limit | advanced_features |
|----------|--------------|--------------|-----------------|-------------------|
| elevenlabs | native | 10 | 5000 | interrupting, overlapping, laughs |
| azure | native | 10 | 10000 | express-as styles |
| gcp | native | 6 | 5000 | - |
| openai | segmented | 6 | 4096 | steerability |
| cartesia | segmented | 6 | 3000 | - |
| deepgram | segmented | 6 | 2000 | - |

### MultiRoleTTSRequest

多角色 TTS 請求。

```python
@dataclass
class MultiRoleTTSRequest:
    """Request for multi-role TTS synthesis."""

    provider: str
    """TTS provider to use."""

    turns: list[DialogueTurn]
    """List of dialogue turns to synthesize."""

    voice_assignments: list[VoiceAssignment]
    """Voice assignment for each speaker."""

    language: str = "zh-TW"
    """Language code for synthesis."""

    output_format: str = "mp3"
    """Output audio format."""

    # Segmented merge options (only used when provider requires merging)
    gap_ms: int = 300
    """Gap between turns in milliseconds (for segmented mode)."""

    crossfade_ms: int = 50
    """Crossfade duration in milliseconds (for segmented mode)."""
```

**Validation Rules**:
- `turns`: 非空列表，最少 1 個，最多依 Provider 限制
- `voice_assignments`: 必須涵蓋所有 `turns` 中出現的 speaker
- `gap_ms`: 0-2000 範圍
- `crossfade_ms`: 0-500 範圍

**Note**: API 層接收 `dialogue_text` (raw string)，由後端透過 `parse_dialogue()` 轉換為 `turns` list。`MultiRoleTTSRequest` 為內部領域模型，使用已解析的 `turns`；API 請求模型（見 [contracts/multi-role-tts-api.yaml](./contracts/multi-role-tts-api.yaml)）則接受原始文字。

### MultiRoleTTSResult

多角色 TTS 結果。

```python
@dataclass
class MultiRoleTTSResult:
    """Result of multi-role TTS synthesis."""

    audio_content: bytes
    """Raw audio content."""

    content_type: str
    """MIME type (e.g., 'audio/mpeg')."""

    duration_ms: int
    """Total audio duration in milliseconds."""

    latency_ms: int
    """Total processing latency in milliseconds."""

    provider: str
    """Provider used for synthesis."""

    synthesis_mode: MultiRoleSupportType
    """Whether native or segmented mode was used."""

    turn_timings: list[TurnTiming] | None = None
    """Optional timing information for each turn."""

    storage_path: str | None = None
    """Path where audio was stored (if applicable)."""


@dataclass
class TurnTiming:
    """Timing information for a single turn."""

    turn_index: int
    """Index of the turn."""

    start_ms: int
    """Start time in milliseconds."""

    end_ms: int
    """End time in milliseconds."""
```

## Frontend Types (TypeScript)

```typescript
// types/multi-role-tts.ts

export interface DialogueTurn {
  speaker: string
  text: string
  index: number
}

export interface VoiceAssignment {
  speaker: string
  voiceId: string
  voiceName?: string
}

export type MultiRoleSupportType = 'native' | 'segmented' | 'unsupported'

export interface ProviderMultiRoleCapability {
  providerName: string
  supportType: MultiRoleSupportType
  maxSpeakers: number
  characterLimit: number
  advancedFeatures: string[]
  notes?: string
}

export interface MultiRoleTTSRequest {
  provider: string
  dialogue_text: string  // Raw dialogue text to be parsed by backend
  voice_assignments: VoiceAssignment[]
  language?: string
  output_format?: string
  gap_ms?: number
  crossfade_ms?: number
}

export interface MultiRoleTTSResult {
  audio_content: string  // Base64 encoded
  content_type: string
  duration_ms: number
  latency_ms: number
  provider: string
  synthesis_mode: MultiRoleSupportType
  turn_timings?: TurnTiming[]
  storage_path?: string
}

export interface TurnTiming {
  turn_index: number
  start_ms: number
  end_ms: number
}

// Frontend-specific types
export interface ParsedDialogue {
  turns: DialogueTurn[]
  speakers: string[]  // Unique speakers extracted
  totalCharacters: number
  isValid: boolean
  error?: string
}
```

## Entity Relationships

```
┌─────────────────────┐
│ MultiRoleTTSRequest │
├─────────────────────┤
│ provider            │
│ turns[]             │──────┐
│ voice_assignments[] │──┐   │
│ language            │  │   │
│ output_format       │  │   │
│ gap_ms              │  │   │
│ crossfade_ms        │  │   │
└─────────────────────┘  │   │
                         │   │
    ┌────────────────────┘   │
    ▼                        ▼
┌─────────────────┐    ┌─────────────┐
│ VoiceAssignment │    │ DialogueTurn│
├─────────────────┤    ├─────────────┤
│ speaker         │◄───│ speaker     │
│ voice_id        │    │ text        │
│ voice_name      │    │ index       │
└─────────────────┘    └─────────────┘

┌──────────────────────────┐
│ ProviderMultiRoleCapability│
├──────────────────────────┤
│ provider_name            │
│ support_type             │◄── MultiRoleSupportType
│ max_speakers             │
│ character_limit          │
│ advanced_features[]      │
└──────────────────────────┘

┌─────────────────────┐
│ MultiRoleTTSResult  │
├─────────────────────┤
│ audio_content       │
│ content_type        │
│ duration_ms         │
│ latency_ms          │
│ provider            │
│ synthesis_mode      │◄── MultiRoleSupportType
│ turn_timings[]      │──┐
│ storage_path        │  │
└─────────────────────┘  │
                         ▼
               ┌─────────────┐
               │ TurnTiming  │
               ├─────────────┤
               │ turn_index  │
               │ start_ms    │
               │ end_ms      │
               └─────────────┘
```

## State Transitions

### Dialogue Parsing State

```
[Empty] ──(user input)──► [Parsing] ──(success)──► [Parsed]
                              │
                              └──(error)──► [ParseError]
```

### Synthesis State

```
[Idle] ──(submit)──► [Validating] ──(valid)──► [Synthesizing]
            │              │                        │
            │              └──(invalid)──► [ValidationError]
            │                                       │
            │        ┌──────────────────────────────┘
            │        ▼
            │   [Processing]
            │        │
            │        ├──(native success)──► [Complete]
            │        │
            │        └──(segmented)──► [MergingSegments] ──► [Complete]
            │                                │
            └──────────────────────(error)───┴──► [SynthesisError]
```

## Database Considerations

此功能主要使用暫存資料，無需新增持久化表格。產生的音訊檔案沿用現有 `storage/{provider}/{uuid}.mp3` 結構。

如需記錄使用歷史，可擴展現有 `test_records` 表：
- 新增 `test_type = 'multi_role_tts'`
- `metadata` JSON 欄位存儲 dialogue turns 和 voice assignments

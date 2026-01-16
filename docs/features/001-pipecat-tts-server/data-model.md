# Data Model: Pipecat TTS Server

**Feature**: `001-pipecat-tts-server`

## Domain Entities

### TTSRequest

Represents a request to synthesize speech from text.

| Field | Type | Required | Description | Constraints |
|-------|------|----------|-------------|-------------|
| `text` | string | Yes | The text to synthesize | Max 5000 chars |
| `voice_id` | string | Yes | The ID of the voice to use | Provider specific |
| `provider` | string | Yes | The TTS provider to use | `azure`, `gcp`, `elevenlabs` |
| `language` | string | No | Language code | e.g., `zh-TW`, `en-US` |
| `speed` | float | No | Speech rate | 0.5 - 2.0 (default 1.0) |
| `pitch` | float | No | Voice pitch | -20 to +20 (default 0.0) |
| `volume` | float | No | Voice volume | 0.0 - 2.0 (default 1.0) |
| `output_format` | enum | No | Audio format | `mp3`, `wav`, `pcm` |

### TTSResult

Represents the result of a synthesis operation.

| Field | Type | Description |
|-------|------|-------------|
| `request` | TTSRequest | The original request |
| `audio` | bytes | The synthesized audio data |
| `duration_ms` | int | Duration of audio in milliseconds |
| `latency_ms` | int | Time taken to synthesize |
| `cost_estimate` | float | Estimated cost of this request |
| `metadata` | dict | Additional provider info |
| `created_at` | datetime | Timestamp |

### VoiceProfile

Represents an available voice from a provider.

| Field | Type | Description |
|-------|------|-------------|
| `id` | string | Unique voice identifier |
| `name` | string | Human readable name |
| `provider` | string | Source provider |
| `language` | string | Language code |
| `gender` | enum | `male`, `female`, `neutral` |
| `styles` | list[str] | Available styles (e.g., 'cheerful') |

## Database Schema (PostgreSQL)

### Table: `synthesis_logs`

Records all TTS requests for monitoring and debugging (FR-010).

```sql
CREATE TABLE synthesis_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    provider VARCHAR(50) NOT NULL,
    voice_id VARCHAR(255) NOT NULL,
    characters_count INTEGER NOT NULL,
    duration_ms INTEGER,
    latency_ms INTEGER,
    status VARCHAR(20) NOT NULL, -- 'success', 'failed'
    error_message TEXT,
    client_ip VARCHAR(50),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    request_params JSONB -- Stores speed, pitch, etc.
);
```

### Table: `voice_cache` (Optional)

Cache available voices to reduce upstream API calls.

```sql
CREATE TABLE voice_cache (
    id VARCHAR(255) PRIMARY KEY, -- provider:voice_id
    provider VARCHAR(50) NOT NULL,
    name VARCHAR(255) NOT NULL,
    language VARCHAR(20) NOT NULL,
    metadata JSONB,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
```
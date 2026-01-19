# WebSocket API Contract: Voice Interaction

**Version**: 1.0.0
**Date**: 2026-01-19
**Feature**: 004-interaction-module

## Connection

### Endpoint
```
ws://{host}/api/v1/interaction/ws
```

### Authentication
WebSocket 連線需在 URL query parameter 或首次訊息中提供認證 token：
```
ws://{host}/api/v1/interaction/ws?token={jwt_token}
```

### Connection Lifecycle
1. Client 建立 WebSocket 連線
2. Server 驗證 token，成功後發送 `connection_ready`
3. Client 發送 `start_session` 開始會話
4. 雙向訊息交換
5. Client 發送 `end_session` 或連線中斷時結束

---

## Client → Server Messages

### start_session

開始新的互動會話。

```typescript
{
  type: "start_session";
  mode: "realtime" | "cascade";
  config: {
    // Realtime 模式
    realtime_provider?: "openai";
    voice?: string;  // "alloy" | "shimmer" | "nova" | "echo" | "fable" | "onyx"

    // Cascade 模式
    stt_provider?: string;   // "deepgram" | "assemblyai" | ...
    stt_model?: string;
    llm_provider?: string;   // "openai" | "gemini"
    llm_model?: string;      // "gpt-4o" | "gemini-2.0-flash"
    tts_provider?: string;   // "azure" | "google" | "elevenlabs" | ...
    tts_voice?: string;
  };
  system_prompt?: string;
  template_id?: string;  // 使用預設模板
  barge_in_enabled?: boolean;  // default: true
}
```

**Response**: `session_started` 或 `error`

---

### audio_chunk

發送音訊資料。

```typescript
{
  type: "audio_chunk";
  audio: string;  // Base64 encoded PCM16, 16kHz mono
  timestamp?: number;  // 可選的 client timestamp (ms)
}
```

**Notes**:
- 建議每 100ms 發送一次
- 音訊格式：PCM16, 16000Hz, mono
- 單次 chunk 大小建議：1600 samples (100ms)

---

### end_turn

明確標記使用者發言結束（當 VAD 未偵測時使用）。

```typescript
{
  type: "end_turn";
}
```

---

### interrupt

使用者主動打斷 AI 回應。

```typescript
{
  type: "interrupt";
}
```

---

### end_session

結束互動會話。

```typescript
{
  type: "end_session";
}
```

**Response**: `session_ended`

---

### ping

心跳檢測。

```typescript
{
  type: "ping";
  timestamp: number;
}
```

**Response**: `pong`

---

## Server → Client Messages

### connection_ready

連線建立成功。

```typescript
{
  type: "connection_ready";
  server_time: string;  // ISO 8601
}
```

---

### session_started

會話開始成功。

```typescript
{
  type: "session_started";
  session_id: string;  // UUID
  mode: "realtime" | "cascade";
  config: {
    // 實際使用的配置
    ...
  };
}
```

---

### speech_started

偵測到使用者開始說話（VAD）。

```typescript
{
  type: "speech_started";
  timestamp: string;  // ISO 8601
}
```

---

### speech_ended

偵測到使用者停止說話（VAD）。

```typescript
{
  type: "speech_ended";
  timestamp: string;  // ISO 8601
  duration_ms: number;
}
```

---

### transcript

語音轉文字結果（僅 Cascade 模式）。

```typescript
{
  type: "transcript";
  text: string;
  is_final: boolean;
  confidence?: number;  // 0.0 - 1.0
}
```

---

### response_started

AI 開始回應。

```typescript
{
  type: "response_started";
  turn_number: number;
  timestamp: string;
}
```

---

### audio_chunk (server)

AI 回應音訊資料。

```typescript
{
  type: "audio_chunk";
  audio: string;  // Base64 encoded audio
  format: "pcm16" | "mp3";
  sample_rate: number;  // 16000 or 24000
  is_final: boolean;
}
```

---

### text_delta

AI 回應文字增量（可選，用於顯示）。

```typescript
{
  type: "text_delta";
  delta: string;
  full_text?: string;
}
```

---

### response_ended

AI 回應結束。

```typescript
{
  type: "response_ended";
  turn_number: number;
  latency: {
    total_ms: number;
    stt_ms?: number;      // Cascade only
    llm_ttft_ms?: number; // Cascade only
    tts_ttfb_ms?: number; // Cascade only
    realtime_ms?: number; // Realtime only
  };
  interrupted: boolean;
}
```

---

### interrupted

AI 回應被打斷。

```typescript
{
  type: "interrupted";
  turn_number: number;
  timestamp: string;
}
```

Client 收到此訊息應立即停止音訊播放。

---

### session_ended

會話結束。

```typescript
{
  type: "session_ended";
  session_id: string;
  summary: {
    total_turns: number;
    total_duration_ms: number;
    avg_latency_ms: number;
    interrupted_count: number;
  };
  status: "completed" | "disconnected" | "error";
}
```

---

### error

錯誤訊息。

```typescript
{
  type: "error";
  code: string;
  message: string;
  recoverable: boolean;
  details?: object;
}
```

**Error Codes**:
| Code | Description | Recoverable |
|------|-------------|-------------|
| `AUTH_FAILED` | 認證失敗 | No |
| `SESSION_EXISTS` | 已有進行中的會話 | Yes |
| `INVALID_MODE` | 無效的模式 | Yes |
| `PROVIDER_ERROR` | 外部提供者錯誤 | Yes |
| `QUOTA_EXCEEDED` | API 配額超限 | No |
| `INVALID_AUDIO` | 音訊格式錯誤 | Yes |
| `INTERNAL_ERROR` | 內部錯誤 | No |

---

### pong

心跳回應。

```typescript
{
  type: "pong";
  client_timestamp: number;
  server_timestamp: number;
}
```

---

## Sequence Diagrams

### Normal Conversation Flow

```
Client                          Server                          OpenAI/Providers
  │                               │                                    │
  │──── start_session ───────────▶│                                    │
  │                               │──── connect to provider ──────────▶│
  │◀──── session_started ─────────│◀──── connection ready ─────────────│
  │                               │                                    │
  │──── audio_chunk ─────────────▶│                                    │
  │──── audio_chunk ─────────────▶│──── forward audio ────────────────▶│
  │◀──── speech_started ──────────│◀──── VAD: speech start ────────────│
  │──── audio_chunk ─────────────▶│──── forward audio ────────────────▶│
  │◀──── speech_ended ────────────│◀──── VAD: speech end ──────────────│
  │                               │                                    │
  │◀──── transcript ──────────────│◀──── transcription ────────────────│
  │◀──── response_started ────────│                                    │
  │◀──── audio_chunk ─────────────│◀──── audio response ───────────────│
  │◀──── audio_chunk ─────────────│◀──── audio response ───────────────│
  │◀──── response_ended ──────────│◀──── response complete ────────────│
  │                               │                                    │
  │──── end_session ─────────────▶│                                    │
  │◀──── session_ended ───────────│──── disconnect ───────────────────▶│
  │                               │                                    │
```

### Barge-in Flow

```
Client                          Server
  │                               │
  │ (AI audio playing)            │
  │◀──── audio_chunk ─────────────│
  │◀──── audio_chunk ─────────────│
  │                               │
  │──── audio_chunk ─────────────▶│ (user starts speaking)
  │◀──── interrupted ─────────────│
  │ (stop playback)               │
  │◀──── speech_started ──────────│
  │──── audio_chunk ─────────────▶│
  │                               │
  │ (new response cycle)          │
```

---

## Rate Limits

| Limit | Value | Description |
|-------|-------|-------------|
| Max audio chunk rate | 20/sec | 每秒最多 20 個 audio_chunk |
| Max message size | 64KB | 單一訊息最大大小 |
| Session timeout | 30 min | 無活動超時 |
| Max concurrent sessions | 1 | 每個使用者同時只能有 1 個會話 |

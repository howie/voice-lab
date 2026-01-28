# Plan: Native Server-Side VAD for Gemini Live Interaction

## Context

The current implementation uses a "Manual VAD" approach where the Frontend detects silence and signals the Backend to end the turn. This has resulted in:

1. **High Latency**: The "double-check" and signal propagation delay responses.
2. **Blocking Issues**: Misalignment between Frontend and Server states causes the system to "block" or ignore user input.
3. **Unnatural Flow**: Unlike the native Gemini App, the conversation feels turn-based rather than fluid.

To achieve a "Gemini App-like" experience, we must switch to **Native Server-Side VAD**, allowing Gemini's model to naturally detect end-of-speech and interruptions.

## Objectives

- **Zero-Blocking**: Ensure the user can speak at any time without the system entering a "blocked" state.
- **Low Latency**: Reduce response time by removing the Frontend VAD decision overhead.
- **Natural Interruption**: Enable true "Barge-in" where the user can interrupt the AI mid-sentence, and the AI handles it natively (or via immediate signal).

## Success Criteria

| 指標 | 目標 | 測量方式 |
|------|------|---------|
| End-to-First-Audio Latency (P50) | < 800ms | `end_turn_time` → `first_audio_time` |
| End-to-First-Audio Latency (P95) | < 1500ms | 同上 |
| Barge-in Response Time | < 200ms | 偵測到語音 → AI 音訊停止 |
| False End-of-Turn Rate | < 5% | 用戶還想說但被切斷的次數 |
| Blocked State Count | 0 | 日誌中 "BLOCKED" 出現次數 |
| User can interrupt AI naturally | Yes | 用戶說話時 AI 立即停止 |
| Conversation continues fluidly | Yes | 無需點擊按鈕即可持續對話 |

## Technical Architecture Changes

### State Transition Diagram (Server VAD Mode)

```
                                    ┌────────────────────────────────────┐
                                    │         user barge-in              │
                                    │   (vol > SPEAKING_THRESHOLD)       │
                                    v                                    │
┌─────────┐  connect   ┌───────────────┐                          ┌─────┴─────┐
│  idle   │ ─────────> │   listening   │ <─────────────────────── │ speaking  │
└─────────┘            └───────┬───────┘    server:turnComplete   └─────┬─────┘
                               │                                        ^
                               │ server:speech_started                  │
                               v                                        │
                       ┌───────────────┐                                │
                       │   listening   │                                │
                       │   (active)    │                                │
                       └───────┬───────┘                                │
                               │                                        │
                               │ server:speech_ended                    │
                               v                                        │
                       ┌───────────────┐    server:response_started     │
                       │  processing   │ ───────────────────────────────┘
                       └───────────────┘
```

### Gemini Server VAD Events

啟用 `automatic_activity_detection` 後，Gemini 會自動發送以下事件：

| 事件 | 觸發時機 | 對應 ResponseEvent |
|------|---------|-------------------|
| `serverContent.inputTranscription` | 用戶語音轉文字（streaming） | `transcript` |
| `serverContent.modelTurn` | AI 開始回應（含音訊） | `audio` |
| `serverContent.turnComplete` | AI 回應結束 | `response_ended` |
| `serverContent.interrupted` | 用戶打斷 AI | `interrupted` |

**注意**：Server VAD 模式下，Gemini 會自動判斷語音結束，不需要 Frontend 發送 `client_content.turn_complete`。

### 1. Backend (`src/domain/services/interaction/gemini_realtime.py`)

#### 1.1 Enable Automatic Activity Detection

修改 `_send_setup` 方法 (L206-227)：

```python
# Before (Manual VAD)
"realtime_input_config": {
    "automatic_activity_detection": {
        "disabled": True
    }
},

# After (Server VAD)
"realtime_input_config": {
    "automatic_activity_detection": {
        "start_of_speech_sensitivity": "MEDIUM",
        "end_of_speech_sensitivity": "LOW",  # 適合幼兒語速較慢
        "prefix_padding_ms": 300,  # 保留語音開始前 300ms
        "silence_duration_ms": 700,  # 靜音 700ms 視為結束
    }
},
```

#### 1.2 Server VAD Configuration Parameters

| 參數 | 說明 | 建議值 |
|------|------|--------|
| `start_of_speech_sensitivity` | 語音開始偵測靈敏度 | `MEDIUM` (LOW/MEDIUM/HIGH) |
| `end_of_speech_sensitivity` | 語音結束偵測靈敏度 | `LOW` (幼兒語速慢，避免誤判) |
| `prefix_padding_ms` | 語音開始前保留的音訊 | 200-500ms |
| `silence_duration_ms` | 靜音多久視為結束 | 500-1000ms |

#### 1.3 Remove Manual Signals from `send_audio`

修改 `send_audio` 方法 (L260-298)：

```python
async def send_audio(self, audio: AudioChunk) -> None:
    # ... existing code ...

    # REMOVE these lines (L282-285):
    # if current_count == 0:
    #     _log("AUDIO_IN", "sending activity_start")
    #     await self._send_message({"realtime_input": {"activity_start": {}}})

    # Keep only the media_chunks sending
    message = {
        "realtime_input": {"media_chunks": [{"mime_type": mime_type, "data": audio_b64}]}
    }
    await self._send_message(message)
```

#### 1.4 Modify `end_turn` for Dual Mode Support

修改 `end_turn` 方法 (L300-327) 支援兩種模式：

```python
async def end_turn(self, force: bool = False) -> None:
    """Signal end of user speech.

    Args:
        force: If True, always send the signal (for Force Send button).
               If False, only send in Manual VAD mode.
    """
    if not self._connected or not self._ws:
        return

    # In Server VAD mode, only send if force=True (Force Send button)
    if self._vad_mode == "server" and not force:
        _log("END_TURN", "skipped (Server VAD mode)")
        return

    # ... existing client_content sending code ...
```

#### 1.5 Add VAD Mode Configuration

新增 VAD 模式配置支援：

```python
def __init__(self, api_key: str) -> None:
    # ... existing code ...
    self._vad_mode: str = "server"  # "server" or "manual"

async def connect(
    self,
    session_id: UUID,
    config: dict[str, Any],
    system_prompt: str = "",
) -> None:
    # ... existing code ...
    self._vad_mode = config.get("vad_mode", "server")
```

### 2. Frontend (`src/components/interaction/InteractionPanel.tsx` & Hooks)

#### 2.1 Modify VAD Logic for Server VAD Mode

修改 `onVolumeChange` 回呼 (L511-602)：

```typescript
onVolumeChange: (vol: number) => {
  setInputVolume(vol)
  inputVolumeRef.current = vol

  const currentState = interactionStateRef.current

  // Server VAD Mode: Only handle barge-in, no end_turn detection
  if (options.vadMode === 'server') {
    // Barge-in: If AI is speaking and user speaks loudly, send interrupt
    if (currentState === 'speaking' && options.bargeInEnabled) {
      if (vol > SPEAKING_THRESHOLD) {
        speakingFrameCountRef.current++
        if (speakingFrameCountRef.current >= SPEAKING_FRAMES_REQUIRED) {
          log('BARGE_IN', `user interrupted AI (vol=${(vol * 100).toFixed(1)}%)`)
          sendMessage('interrupt', {})
          stopAudio()
          // Don't change state here - wait for server 'interrupted' event
        }
      } else {
        speakingFrameCountRef.current = 0
      }
    }
    return  // Skip Manual VAD logic
  }

  // Manual VAD Mode: Existing silence detection logic
  // ... existing code (L518-602) ...
}
```

#### 2.2 Update State Management

修改 `handleMessage` 中的狀態轉換 (L260-436)：

```typescript
// Server VAD mode: Respect server-driven state changes
case 'speech_started':
  // Server detected user started speaking
  setInteractionState('listening')
  clearTranscripts()
  // Reset turn timing
  setTurnTiming({
    speakingStartedAt: Date.now(),
    endTurnSentAt: null,
    responseStartedAt: null,
    firstAudioAt: null,
    responseEndedAt: null,
  })
  log('SERVER_VAD', 'speech_started')
  break

case 'speech_ended':
  // Server detected user stopped speaking
  setInteractionState('processing')
  setTurnTiming((prev) => ({ ...prev, endTurnSentAt: Date.now() }))
  log('SERVER_VAD', 'speech_ended')
  break
```

#### 2.3 Add VAD Mode to Options

更新 `interactionStore` 和配置：

```typescript
interface InteractionOptions {
  // ... existing fields ...
  vadMode: 'server' | 'manual'  // NEW
}

// Default to server VAD
const defaultOptions: InteractionOptions = {
  // ... existing defaults ...
  vadMode: 'server',
}
```

#### 2.4 Keep Force Send Button

保留「結束發言」按鈕作為備用（當 Server VAD 誤判時）：

```typescript
{/* Force Send Button - works in both VAD modes */}
{interactionState === 'listening' && isRecording && (
  <button
    onClick={() => {
      stopRecording()
      sendMessage('end_turn', { force: true })  // force=true for Server VAD
      setInteractionState('processing')
    }}
    className="rounded-lg bg-blue-500 px-4 py-2 text-sm font-medium text-white hover:bg-blue-600"
  >
    結束發言
  </button>
)}
```

### 3. Fallback Mechanism

如果 Server VAD 表現不佳，可透過配置切換回 Manual VAD：

```typescript
// In PerformanceSettings.tsx or a new VADModeSelector component
<select
  value={options.vadMode}
  onChange={(e) => setVadMode(e.target.value as 'server' | 'manual')}
  disabled={isConnected}
>
  <option value="server">Server VAD (推薦)</option>
  <option value="manual">Manual VAD (備用)</option>
</select>
```

## Implementation Steps

### Phase 1: Backend Configuration (Server VAD)

| Task | File | Lines | Description |
|------|------|-------|-------------|
| 1.1 | `gemini_realtime.py` | L94-117 | 新增 `_vad_mode` 屬性 |
| 1.2 | `gemini_realtime.py` | L206-227 | 修改 `_send_setup` 啟用 Server VAD |
| 1.3 | `gemini_realtime.py` | L282-285 | 移除 `activity_start` 發送 |
| 1.4 | `gemini_realtime.py` | L300-327 | 修改 `end_turn` 支援 `force` 參數 |
| 1.5 | `interaction_handler.py` | TBD | 傳遞 `vad_mode` 配置到 service |

### Phase 2: Frontend "Always Listening" & Barge-in

| Task | File | Lines | Description |
|------|------|-------|-------------|
| 2.1 | `interactionStore.ts` | TBD | 新增 `vadMode` 選項 |
| 2.2 | `InteractionPanel.tsx` | L511-602 | 修改 `onVolumeChange` 支援雙模式 |
| 2.3 | `InteractionPanel.tsx` | L260-436 | 處理 `speech_started`/`speech_ended` 事件 |
| 2.4 | `InteractionPanel.tsx` | L931-938 | 更新 Force Send 按鈕邏輯 |
| 2.5 | `PerformanceSettings.tsx` | TBD | 新增 VAD 模式選擇器 |

### Phase 3: Testing & Tuning

#### Unit Tests

- [ ] Server VAD 配置正確發送到 Gemini
- [ ] `speech_started` / `speech_ended` 事件正確處理
- [ ] Barge-in 自動觸發邏輯（vol > threshold + frames > required）
- [ ] `end_turn(force=True)` 在 Server VAD 模式下仍然發送訊號
- [ ] `end_turn(force=False)` 在 Server VAD 模式下被跳過

#### Integration Tests

- [ ] 正常對話流程（說話 → 停頓 → AI 回應 → 繼續說話）
- [ ] 快速來回對話（用戶和 AI 交替說話）
- [ ] 長句子不被誤判為結束（模擬幼兒慢速說話）
- [ ] 打斷場景（AI 說話中用戶插話，AI 立即停止）
- [ ] 回退測試（切換到 Manual VAD 後功能正常）

#### Performance Tests

- [ ] 測量 100 輪對話的延遲分佈（P50, P95, P99）
- [ ] 比較 Manual VAD vs Server VAD 的延遲差異
- [ ] 測量 Barge-in 響應時間

#### Tuning Parameters Log

| 測試日期 | end_of_speech_sensitivity | silence_duration_ms | 誤判率 | P50 延遲 | 備註 |
|---------|---------------------------|---------------------|--------|---------|------|
| TBD     | LOW                       | 700                 | TBD    | TBD     | 初始值 |
| TBD     | MEDIUM                    | 500                 | TBD    | TBD     | 如果誤判率低 |

## Risk Assessment

| 風險 | 可能性 | 影響 | 緩解措施 |
|------|--------|------|---------|
| Server VAD 對中文支援不佳 | 中 | 高 | 保留 Manual VAD 作為回退選項 |
| Gemini 2.0 vs 2.5 API 差異 | 低 | 中 | 兩個模型都測試，確認參數相容 |
| 網路延遲導致狀態不同步 | 中 | 中 | Frontend 維持獨立的 timeout 機制 |
| 幼兒說話模式特殊（慢、斷斷續續） | 高 | 中 | 使用 `end_of_speech_sensitivity: LOW` |
| Barge-in 過於敏感 | 中 | 低 | 調整 `SPEAKING_THRESHOLD` 和 `SPEAKING_FRAMES_REQUIRED` |

## Rollback Plan

如果 Server VAD 上線後出現嚴重問題：

1. **快速回退**：將 `vadMode` 預設值改回 `'manual'`
2. **配置開關**：透過環境變數 `GEMINI_VAD_MODE=manual` 強制使用 Manual VAD
3. **用戶選擇**：在 UI 中顯示 VAD 模式選擇器，讓用戶自行選擇

## References

- [Gemini Live API Documentation](https://ai.google.dev/gemini-api/docs/live)
- [Voice Activity Detection Config](https://ai.google.dev/api/generate-content#VoiceActivityDetectionConfig)
- [Gemini 2.5 Native Audio](https://ai.google.dev/gemini-api/docs/audio)

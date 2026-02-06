# Gemini V2V 直連優化完整歷程

日期：2026-02-06

## 概述

記錄 Gemini Live API Voice-to-Voice (V2V) 從初始版本到目前對話品質的完整優化歷程，包含所有嘗試過的方案、失敗經驗和關鍵發現。

## 初始狀況

- Turn 1 延遲：~4.5 秒
- Turn 2 延遲：~7.4 秒
- Turn 3+：有時完全沒有回應
- 對話品質：中文辨識不穩定、思考文字污染、transcript 重複

## 演進階段

### Phase 1：基礎建設

**關鍵 Commits:**
- `8b0a6c9` feat(interaction): implement realtime API clients
- `926fe46` feat(interaction): implement barge-in/interrupt (US5)
- `f9220dd` feat(interaction): implement latency measurement (US3)

**架構設計:**
- `GeminiRealtimeService` 實現 `InteractionModeService` 抽象介面
- WebSocket 連接到 `wss://generativelanguage.googleapis.com/ws/...BidiGenerateContent`
- async event queue 解耦訊息接收與事件處理
- Factory pattern 支援 Realtime / Cascade 模式切換

---

### Phase 2：延遲調校（最關鍵的學習階段）

**關鍵 Commits:**
- `2324f14` perf: optimize V2V latency and add default Chinese teacher prompt
- `411723e` feat: add V2V feature toggles for performance A/B testing
- `35a3257` docs: add Gemini Live API latency tuning lesson learned

#### 嘗試過的 VAD 方案

| # | 策略 | 設定 | 結果 | 教訓 |
|---|------|------|------|------|
| 1 | Gemini Server VAD 高靈敏度 | `END_SENSITIVITY_HIGH`, `silence_duration_ms=500` | 更糟，延遲 19.7s | Gemini VAD 太敏感，用戶說「好」就被打斷 |
| 2 | 降低 Gemini VAD 靈敏度 | `END_SENSITIVITY_LOW`, `silence_duration_ms=1000` | 延遲 **65 秒** | 等待時間過長，頻繁被 interrupted |
| 3 | 完全禁用 Gemini VAD | `disabled=True` | **完全沒有回應** | `audioStreamEnd` 在 VAD disabled 時無效 |

#### 根本原因發現

```
| VAD 設定              | 應發送的訊號                     |
|-----------------------|----------------------------------|
| disabled=false（預設） | audioStreamEnd ✅                |
| disabled=true         | activityStart + activityEnd     |
```

當 `disabled=true` 時發送 `audioStreamEnd` → Gemini 完全忽略 → 無回應。
這是 API 文檔中的一行備註，但造成了數小時的除錯。

#### 成功的優化

| 優化項目 | Commit | 減少延遲 | 原理 |
|---------|--------|---------|------|
| 關閉 thinking | `2324f14` | -200~500ms | `thinking_budget: 0` 避免 Gemini 先推理再說話 |
| 純 async 等待 | `2324f14` | -100ms | 移除 `timeout=0.1` polling，用 `await queue.get()` |
| Lightweight mode | `2324f14` | -50~100ms | 跳過每個 audio chunk 的同步檔案儲存 |
| Feature toggles | `411723e` | 可配置 | A/B 測試不同組合的效能影響 |

---

### Phase 3：音訊傳輸優化

**關鍵 Commits:**
- `0e3c435` perf(interaction): optimize audio latency - Phase 0
- `f9d9204` perf: audio latency optimization with AudioWorklet and binary transmission

#### 三層優化

**Layer 1 - VAD 參數 (Phase 0):**
```
靜音門檻: 1.2s → 0.6s
感知延遲減少: ~600ms
```
配合 barge-in 機制處理 false positive。

**Layer 2 - AudioWorklet (Phase 1):**
```
ScriptProcessorNode → AudioWorklet
Buffer: 4096 → 1024 samples
取樣延遲: 256ms → 64ms
執行環境: Main thread → Dedicated thread
```
消除 UI blocking，瀏覽器 deprecation warning 消失。

**Layer 3 - Binary WebSocket (Phase 2):**
```
Base64 JSON → Binary frame
格式: [4 bytes uint32 LE sample_rate] + [PCM16 audio data]
封包大小: 減少 ~33%
CPU overhead: 省去 encode/decode
```

---

### Phase 4：對話品質修正

**關鍵 Commits:**
- `9fde714` fix(gemini): filter out thinking/reasoning text from modelTurn
- `5cb0b39` fix(gemini): fix transcript deduplication logic
- `5713471` feat(interaction): add Chinese language preamble
- `2155b0d` fix(interaction): prevent VAD from triggering immediately after AI response

#### 問題與修正

**1. 思考文字污染 (`9fde714`)**

Gemini 在音訊回應前會輸出思考文字（如 "**Initiating the Story**"），出現在 `modelTurn.parts[].text` 中。
在音訊模式 (`response_modalities: ["AUDIO"]`) 下應忽略這些文字，只用 `outputTranscription` 作為語音轉錄來源。

**2. Transcript 去重 bug (`5cb0b39`)**

原本邏輯：
```python
# ❌ 錯誤：substring 檢查
if text not in self._accumulated_input_transcript:
```
問題：「No No No」只保留第一個 "No"，「A cat is a cat」的第二個 "a cat" 被過濾。

修正：改用 consecutive duplicate 比對。

**3. 中文支援 (`5713471`)**

加入語言前導指令：
```python
chinese_language_preamble = (
    "[語言設定] 這是一個中文對話。"
    "請你全程使用繁體中文理解使用者的語音輸入，並用繁體中文回覆。..."
)
```

**4. VAD 空回合迴圈 (`2155b0d`)**

問題：AI 回應結束 → 重啟錄音 → 靜音偵測立即觸發 end_turn → 空回合。
修正：加入 `hasUserSpokenRef`，只有使用者真的開始說話後才啟動靜音偵測。

---

### Phase 5：穩定性與可觀測性

**關鍵 Commits:**
- `88f72ac` fix(interaction): resolve WebSocket resource leak on disconnect
- `4509531` fix(gemini-live): handle Blob WebSocket messages before JSON parsing
- `8b1cb1e` fix(interaction): clean up Gemini realtime logging noise
- `a72181d` feat(gemini-live-test): add direct Gemini Live API test page

#### WebSocket 資源洩漏 (`88f72ac`)

四個互相影響的 bug：
1. AudioWorklet `process()` 永遠回傳 true → 不停止
2. `onAudioChunk` 透過 closure 捕獲 stale `wsStatus`
3. `useMicrophone` 缺少重複啟動防護 → AudioWorklet 洩漏
4. InteractionPanel 缺少 unmount cleanup

#### Blob 訊息處理 (`4509531`)

瀏覽器 WebSocket 預設 `binaryType="blob"`，Gemini 的二進位回應以 Blob 送達。
原本直接 `JSON.parse(event.data)` → 得到 `"[object Blob]"` 解析錯誤。
修正：先檢查是否為 Blob，用 `Blob.text()` 轉換後再 parse。

#### 直連測試頁面 (`a72181d`)

建立前端直連 Gemini 的測試頁面（繞過 backend），用於：
- 測量 Gemini API 的裸延遲基準線
- 區分「Gemini 延遲」和「Backend 架構延遲」
- 有首音訊歷史圖表，方便觀察延遲趨勢

---

## 最終架構

```
Frontend                          Backend                         Gemini Live API
┌──────────────┐        ┌────────────────────────┐        ┌──────────────────┐
│ AudioWorklet │──binary──→ interaction_handler.py │──JSON──→ BidiGenerate     │
│ (64ms buffer)│        │                        │        │ Content WS       │
│              │        │ gemini_realtime.py      │        │                  │
│ VAD (0.6s)   │        │ - async queue (no poll) │        │ - thinking: off  │
│              │←─binary──│ - lightweight mode     │←─JSON──│ - voice: Kore    │
│ PCM16 player │        │ - transcript dedup      │        │ - 中文 preamble   │
└──────────────┘        └────────────────────────┘        └──────────────────┘
```

## 延遲改善總結

| 優化項目 | 延遲減少 | 類別 |
|---------|---------|------|
| `thinking_budget: 0` | -200~500ms | 模型配置 |
| VAD 靜音門檻 1.2s → 0.6s | -600ms | 感知延遲 |
| AudioWorklet (buffer 4096→1024) | -192ms | 前端架構 |
| Binary WebSocket | -30~50ms | 協議優化 |
| 純 async 等待 (移除 polling) | -100ms | 後端架構 |
| Lightweight mode (跳過同步儲存) | -50~100ms | 後端 I/O |
| 過濾思考文字 | 間接減少 | 品質改善 |

**累積效果：感知延遲從 ~4.5s+ 降至接近 Gemini API 的裸延遲基準線**

## 核心教訓

### 1. 雙重控制者問題
前端 VAD + 伺服端 VAD 同時運作 = 不可預測。明確選定一個控制者，避免「兩個人同時踩煞車」。

### 2. API 文檔細節致命
`audioStreamEnd` 只在 `automatic_activity_detection` 啟用時有效。一行文檔備註讓系統完全無回應，浪費數小時除錯。

### 3. 感知延遲比實際延遲更重要
VAD 門檻調整、thinking 關閉、首音訊追蹤 — 這些不是傳輸優化，而是「讓使用者更快聽到聲音」的感知優化。使用者體驗是由「從說完話到聽到回應」的時間決定的。

### 4. 逐層剝洋蔥式優化
不要試圖一次解決所有問題：
- Phase 0: 參數調校（純配置，零 code change）
- Phase 1: 前端架構改良（AudioWorklet）
- Phase 2: 協議層改良（Binary WebSocket）
- 每層帶來 30-50% 改善，疊加效果顯著

### 5. 基準線測試不可少
直連測試頁面讓我們能分辨「Gemini 本身的延遲」和「我們架構的延遲」，這對 debug 和優化決策至關重要。

### 6. 模型名稱 ≠ 模型能力
- `gemini-2.5-flash` ≠ `gemini-2.5-flash-native-audio-preview-12-2025`
- 不是每個 Gemini 模型都支援 Live API
- Google AI Studio 和 Vertex AI 用不同的模型名稱格式

### 7. 前端生命週期管理
WebSocket + AudioWorklet + VAD 三者的生命週期必須同步管理，否則會出現資源洩漏、stale closure、重複啟動等問題。

## 相關文件

- `backend/src/domain/services/interaction/gemini_realtime.py` — 核心 Gemini 客戶端
- `backend/src/infrastructure/websocket/interaction_handler.py` — WebSocket 整合層
- `backend/src/domain/services/interaction/latency_tracker.py` — 延遲測量
- `frontend/src/hooks/useGeminiLive.ts` — 直連測試 hook
- `frontend/public/worklets/audio-processor.js` — AudioWorklet
- `frontend/src/lib/audioProcessor.ts` — 音訊處理抽象層
- `docs/lesson-learn/2026-01-28-gemini-live-api-latency-tuning.md` — 早期延遲調校記錄

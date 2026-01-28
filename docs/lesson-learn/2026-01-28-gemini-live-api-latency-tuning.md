# Gemini Live API V2V 延遲調校記錄

日期：2026-01-28

## 問題描述

使用 Gemini Live API 進行 Voice-to-Voice (V2V) 對話時，回應延遲過高，特別是第二輪對話之後延遲更明顯。

## 初始狀況

- 第一輪對話：end_turn → first_audio 約 **4.5 秒**
- 第二輪對話：end_turn → first_audio 約 **7.4 秒**
- 第三輪以後：有時完全沒有回應

## 嘗試過的方案

### 1. 啟用 Gemini Server-Side VAD（高靈敏度）

```python
"realtime_input_config": {
    "automatic_activity_detection": {
        "disabled": False,
        "start_of_speech_sensitivity": "START_SENSITIVITY_HIGH",
        "end_of_speech_sensitivity": "END_SENSITIVITY_HIGH",
        "silence_duration_ms": 500,
    }
}
```

**結果**：❌ 更糟
- Gemini VAD 太敏感，用戶說「好」就被打斷
- 第二輪延遲反而增加到 19.7 秒
- 頻繁收到 `interrupted` 事件

### 2. 調低 Gemini VAD 靈敏度

```python
"realtime_input_config": {
    "automatic_activity_detection": {
        "disabled": False,
        "start_of_speech_sensitivity": "START_SENSITIVITY_HIGH",
        "end_of_speech_sensitivity": "END_SENSITIVITY_LOW",
        "silence_duration_ms": 1000,
    }
}
```

**結果**：❌ 更糟
- 第一輪延遲增加到 **65 秒**（09:46:59 → 09:48:05）
- 後續回合頻繁被 interrupted
- 系統行為不穩定

### 3. 完全禁用 Gemini VAD

```python
"realtime_input_config": {
    "automatic_activity_detection": {
        "disabled": True,
    }
}
```

**結果**：❌ 完全沒有回應
- 用戶說了 53 秒，發送了 2499 個 audio chunks
- 發送 `audio_stream_end` 後完全沒有回應
- 連線直接關閉

**根本原因（重要發現）**：

根據 [Gemini Live API 文檔](https://ai.google.dev/api/live)：

> **`audioStreamEnd`**: "This should only be sent **when automatic activity detection is enabled** (which is the default)."

當 `disabled=true` 時：
- **不應該發送 `audioStreamEnd`**
- **應該發送 `activityStart` 和 `activityEnd`** 來手動控制 turn-taking

| VAD 設定 | 應發送的訊號 |
|---------|-------------|
| `disabled=false`（預設） | `audioStreamEnd` ✅ |
| `disabled=true` | `activityStart` + `activityEnd` |

我們的程式碼在 `disabled=true` 時仍然發送 `audioStreamEnd`，這是 Gemini 完全不回應的根本原因。

## 觀察到的問題

### 1. 雙重 VAD 衝突
- **前端 VAD**：檢測用戶停止說話 → 發送 `end_turn`
- **Gemini Server VAD**：也在檢測用戶停止說話
- 兩者同時運作導致不可預測的行為

### 2. `audio_stream_end` 的影響
- 我們發送 `audio_stream_end` 是否會干擾 Gemini 的處理？
- Gemini 可能在等待更多音訊，但收到 `audio_stream_end` 後又需要重新處理

### 3. 長音訊處理延遲
- 用戶說話時間越長，STT 處理延遲越大
- 16 秒音訊 → 6.5 秒處理時間
- 可能是 Gemini 需要一次處理整段音訊

### 4. 角色設定未正確傳遞
- 前端設定 `aiRole: '幼兒園老師'`
- 但 log 顯示 `role: 'AI 助理'`
- 需要檢查 config 傳遞流程

## 可能的解決方向

### 方向 A：完全禁用 Gemini VAD，只用前端 VAD

```python
"realtime_input_config": {
    "automatic_activity_detection": {
        "disabled": True,  # 完全禁用 Gemini VAD
    }
}
```

**優點**：
- 避免雙重 VAD 衝突
- 前端完全控制 turn-taking

**缺點**：
- 可能無法利用 Gemini 的低延遲優勢
- 延遲仍取決於前端 VAD 的判斷速度

### 方向 B：完全禁用前端 VAD，只用 Gemini VAD

- 移除前端的靜音檢測邏輯
- 不發送 `audio_stream_end`
- 讓 Gemini 完全決定何時開始回應

**優點**：
- Gemini 可以更快開始回應
- 減少不必要的延遲

**缺點**：
- 持續傳輸音訊（頻寬/成本）
- 背景噪音可能觸發回應

### 方向 C：調整前端 VAD 靈敏度

- 縮短前端 VAD 的靜音門檻（目前 ~1 秒）
- 更快發送 `end_turn`
- 但可能會截斷用戶說話

### 方向 D：使用 Gemini 2.0 Flash 而非 2.5

- 2.5 是 preview 版本，可能有 bug
- 2.0 Flash Live 可能更穩定

```python
model = "gemini-2.0-flash-live-001"  # 而非 2.5 preview
```

### 方向 E：檢查網路和連線狀態

- 65 秒的延遲可能是連線問題
- 需要監控 WebSocket 連線狀態
- 考慮加入重連邏輯

### 方向 F：串流處理優化

- 確認音訊是真正串流發送，而非批次
- 檢查 AudioWorklet 的 buffer size 設定
- 考慮減小 buffer 以降低延遲

## 下一步建議

1. **先嘗試方向 A**：禁用 Gemini VAD，使用純前端 VAD
2. **如果還是慢**：嘗試方向 D，換回 2.0 Flash Live 模型
3. **加入更多監控**：
   - 記錄每個音訊 chunk 的發送時間
   - 記錄 Gemini 連線狀態
   - 記錄 `audio_stream_end` 發送後的回應時間

## 重要發現：Google AI Studio vs Vertex AI

**這是兩個完全不同的 API 服務，使用不同的模型名稱格式！**

### 比較表

| 項目 | Google AI Studio | Vertex AI |
|-----|------------------|-----------|
| **文檔網址** | `ai.google.dev` | `cloud.google.com/vertex-ai` |
| **WebSocket Endpoint** | `generativelanguage.googleapis.com` | `vertexai.googleapis.com` |
| **認證方式** | API Key | Service Account / OAuth |
| **計費** | 免費額度 + 按量計費 | GCP 計費 |
| **模型名稱格式** | **簡短** (`gemini-2.5-flash`) | **長格式** (`gemini-live-2.5-flash-native-audio`) |

### 支援 Live API (bidiGenerateContent) 的模型

**重要：不是所有 Gemini 模型都支援 Live API！**

| 模型 ID | 支援 Live API | 備註 |
|---------|---------------|------|
| `gemini-2.5-flash-native-audio-preview-12-2025` | ✅ 是 | 支援中文，Native Audio |
| `gemini-2.0-flash-live-001` | ✅ 是 | 穩定版 |
| `gemini-2.5-flash` | ❌ 否 | 錯誤：不支援 bidiGenerateContent |
| `gemini-2.0-flash` | ❌ 否 | 錯誤：不支援 bidiGenerateContent |

### 錯誤案例

```python
# ❌ 錯誤：使用不支援 Live API 的模型
model = "gemini-2.5-flash"  # 錯誤！不支援 bidiGenerateContent
# 結果：1008 policy violation - models/gemini-2.5-flash is not found for API version v1alpha

# ❌ 錯誤：使用 Vertex AI 格式的模型名稱
model = "gemini-live-2.5-flash-native-audio"  # 這是 Vertex AI 的名稱
# 結果：setup timeout

# ✅ 正確：使用支援 Live API 的完整模型名稱
model = "gemini-2.5-flash-native-audio-preview-12-2025"
```

### 關鍵教訓

1. **Live API 只支援特定模型**，不能用通用的 `gemini-2.5-flash`
2. **錯誤訊息 "not supported for bidiGenerateContent"** 表示模型不支援 Live API
3. **WebSocket URL 中需要加 `models/` 前綴**
4. **Google AI Studio 和 Vertex AI 使用不同的模型名稱格式**

**目前決定**：使用 `gemini-2.5-flash-native-audio-preview-12-2025`（支援 Live API + 中文）

## 相關程式碼位置

- 後端 Gemini 設定：`backend/src/domain/services/interaction/gemini_realtime.py`
- 前端 VAD 邏輯：`frontend/src/components/interaction/InteractionPanel.tsx`
- 前端 AudioWorklet：`frontend/public/worklets/audio-processor.js`
- 角色設定傳遞：`backend/src/infrastructure/websocket/interaction_handler.py`

## 參考資料

- [Gemini Live API VAD 設定文檔](https://ai.google.dev/gemini-api/docs/live-guide)
- `realtime_input_config.automatic_activity_detection` 參數說明

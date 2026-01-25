# Test Cases: Gemini V2V Transcript Display

**Feature Branch**: `feat/gemini-transcript-display`
**Related Module**: 004-interaction-module
**Created**: 2026-01-25
**Status**: Ready for Testing

## Overview

本測試案例涵蓋 Gemini V2V 模式下的轉錄顯示功能，包含：
- Gemini 模型選擇 UI
- 語音選擇功能
- 使用者語音轉文字（User Transcript）
- AI 回應文字串流（AI Response Text）

---

## Test Environment

### Prerequisites
- [ ] Google AI API Key 已設定 (`GOOGLE_AI_API_KEY`)
- [ ] 瀏覽器支援麥克風存取
- [ ] 後端服務運行中 (`make run-backend`)
- [ ] 前端服務運行中 (`make run-frontend`)

### Test Data
| 項目 | 值 |
|------|-----|
| 測試模型 | `gemini-2.0-flash-live-001` |
| 測試語音 | `Kore` (女聲), `Puck` (男聲) |
| 測試情境 | 預設幼教老師情境 |

---

## Test Cases

### TC-001: Gemini 模型選擇 UI 顯示

**Priority**: P1
**Type**: UI / Functional

**Preconditions**:
1. 使用者已登入系統
2. 前端頁面已載入

**Steps**:
| Step | Action | Expected Result |
|------|--------|-----------------|
| 1 | 進入 Interaction 頁面 | 頁面正常載入 |
| 2 | 在 Mode 選擇 Realtime | 顯示 Provider 選擇器 |
| 3 | 在 Provider 選擇 Gemini | 顯示 Gemini 專屬的 Model 選擇器 |
| 4 | 展開 Model 下拉選單 | 顯示三個模型選項 |

**Expected Model Options**:
- `gemini-2.0-flash-live-001` - 穩定版本（推薦）
- `gemini-2.5-flash-native-audio-preview` - 預覽版，30 種 HD 語音
- `gemini-2.0-flash-exp` - 實驗版，2026年3月退役

**Pass Criteria**:
- [ ] Model 選擇器僅在選擇 Gemini 時顯示
- [ ] 預設選中 `gemini-2.0-flash-live-001`
- [ ] 各選項顯示正確的描述文字

---

### TC-002: Gemini 語音選擇功能

**Priority**: P1
**Type**: UI / Functional

**Preconditions**:
1. Provider 已選擇 Gemini

**Steps**:
| Step | Action | Expected Result |
|------|--------|-----------------|
| 1 | 展開 Voice 下拉選單 | 顯示 5 個語音選項 |
| 2 | 選擇 `Kore` | 語音選項更新為 Kore |
| 3 | 選擇 `Puck` | 語音選項更新為 Puck |

**Expected Voice Options**:
| Voice | Gender | Description |
|-------|--------|-------------|
| Kore | Female | 預設語音，適合幼教情境 |
| Aoede | Female | 女聲 |
| Puck | Male | 男聲 |
| Charon | Male | 男聲 |
| Fenrir | Male | 男聲 |

**Pass Criteria**:
- [ ] 預設選中 `Kore`
- [ ] 所有 5 個語音選項皆可選擇
- [ ] 切換語音後狀態正確保存

---

### TC-003: WebSocket 連線與設定

**Priority**: P1
**Type**: Integration

**Preconditions**:
1. Gemini Provider 和 Model 已選擇
2. 角色與情境已設定

**Steps**:
| Step | Action | Expected Result |
|------|--------|-----------------|
| 1 | 點擊「開始對話」按鈕 | WebSocket 開始連線 |
| 2 | 觀察網路請求 | 發送 setup message |
| 3 | 檢查後端日誌 | 記錄 setup message 內容 |

**Expected Setup Message Content**:
```json
{
  "setup": {
    "model": "models/gemini-2.0-flash-live-001",
    "generation_config": {
      "response_modalities": ["TEXT", "AUDIO"],
      "speech_config": {
        "voice_config": {
          "prebuilt_voice_config": {
            "voice_name": "Kore"
          }
        }
      }
    },
    "system_instruction": { ... }
  }
}
```

**Pass Criteria**:
- [ ] WebSocket 連線成功建立
- [ ] Setup message 包含 `response_modalities: ["TEXT", "AUDIO"]`
- [ ] 選擇的 model 和 voice 正確傳送
- [ ] 後端日誌記錄完整的 setup message

---

### TC-004: 使用者語音轉錄顯示 (User Transcript)

**Priority**: P1
**Type**: E2E / Functional

**Preconditions**:
1. WebSocket 連線已建立
2. 麥克風權限已授權

**Steps**:
| Step | Action | Expected Result |
|------|--------|-----------------|
| 1 | 開始錄音（說話） | 收音狀態指示器亮起 |
| 2 | 說一句話（如：「你好」） | 前端接收 transcript 事件 |
| 3 | 觀察 TranscriptDisplay 組件 | 顯示使用者說的話 |
| 4 | 繼續說話 | 轉錄文字持續更新 |

**Expected Behavior**:
- 後端接收 `inputTranscription` 事件
- 轉換為 `ResponseEvent(type="transcript")`
- 前端更新 `userTranscript` 狀態
- UI 即時顯示使用者發言

**Backend Event Format**:
```python
ResponseEvent(
    type="transcript",
    data={"text": "你好", "is_final": True}
)
```

**Pass Criteria**:
- [ ] 使用者說話時即時顯示轉錄文字
- [ ] 文字顯示延遲 < 500ms
- [ ] `is_final` 標記正確（中間結果 vs 最終結果）
- [ ] 多輪對話時，轉錄紀錄正確累積

---

### TC-005: AI 回應文字串流顯示 (AI Response Text)

**Priority**: P1
**Type**: E2E / Functional

**Preconditions**:
1. 使用者已發送語音訊息
2. Gemini API 正在回應

**Steps**:
| Step | Action | Expected Result |
|------|--------|-----------------|
| 1 | 等待 AI 開始回應 | 收到 modelTurn 事件 |
| 2 | 觀察 TranscriptDisplay | 文字開始逐步顯示 |
| 3 | 持續觀察 | 文字串流完整顯示 |
| 4 | AI 回應結束 | 完整文字保留在畫面上 |

**Expected Behavior**:
- 後端接收包含 `text` 的 `modelTurn` 事件
- 轉換為 `ResponseEvent(type="text_delta")`
- 前端呼叫 `appendAIResponse(text)`
- UI 逐步顯示 AI 回應

**Backend Event Format**:
```python
ResponseEvent(
    type="text_delta",
    data={"text": "你好！今天想聽什麼故事呢？"}
)
```

**Pass Criteria**:
- [ ] AI 回應時即時顯示文字
- [ ] 文字以串流方式逐步顯示（非一次性全部顯示）
- [ ] 回應結束後文字完整保留
- [ ] 文字與音訊內容一致

---

### TC-006: 文字與音訊同步

**Priority**: P2
**Type**: E2E / UX

**Preconditions**:
1. 對話進行中
2. AI 正在回應

**Steps**:
| Step | Action | Expected Result |
|------|--------|-----------------|
| 1 | 觀察 AI 回應 | 文字和音訊同時開始 |
| 2 | 比對內容 | 文字與語音內容一致 |
| 3 | 測試長回應 | 文字串流與音訊同步 |

**Pass Criteria**:
- [ ] 文字顯示與音訊播放基本同步（誤差 < 1 秒）
- [ ] 文字內容與語音內容語意一致
- [ ] 長回應時不會出現明顯不同步

---

### TC-007: 轉錄顯示開關

**Priority**: P2
**Type**: UI / Configuration

**Preconditions**:
1. 系統正常運行

**Steps**:
| Step | Action | Expected Result |
|------|--------|-----------------|
| 1 | 確認 showTranscripts 預設值 | 預設為 true |
| 2 | 進行對話測試 | 轉錄正常顯示 |
| 3 | 關閉 showTranscripts | 轉錄區域隱藏 |
| 4 | 重新開啟 | 轉錄區域恢復顯示 |

**Pass Criteria**:
- [ ] 預設啟用轉錄顯示
- [ ] 可動態切換顯示/隱藏
- [ ] 隱藏時不影響對話功能

---

### TC-008: 打斷時的轉錄處理

**Priority**: P2
**Type**: E2E / Edge Case

**Preconditions**:
1. AI 正在播放語音回應
2. 轉錄顯示功能已啟用

**Steps**:
| Step | Action | Expected Result |
|------|--------|-----------------|
| 1 | 等待 AI 開始回應 | 文字開始串流顯示 |
| 2 | 在 AI 說話中途打斷 | 音訊停止播放 |
| 3 | 觀察文字顯示 | 已顯示的文字保留 |
| 4 | 開始新的發言 | 新的使用者轉錄開始 |

**Pass Criteria**:
- [ ] 打斷時已顯示的 AI 文字保留
- [ ] 新的使用者轉錄正確開始
- [ ] 對話歷史正確記錄（標記為中斷）

---

### TC-009: 多輪對話轉錄累積

**Priority**: P1
**Type**: E2E / Functional

**Preconditions**:
1. 對話已開始

**Steps**:
| Step | Action | Expected Result |
|------|--------|-----------------|
| 1 | 進行第一輪對話 | 使用者和 AI 轉錄顯示 |
| 2 | 進行第二輪對話 | 新轉錄追加到歷史 |
| 3 | 進行第三輪對話 | 所有對話輪次可見 |
| 4 | 檢查轉錄區域 | 可捲動查看所有歷史 |

**Pass Criteria**:
- [ ] 每輪對話的使用者發言有記錄
- [ ] 每輪對話的 AI 回應有記錄
- [ ] 對話順序正確
- [ ] 可捲動查看完整歷史

---

### TC-010: 錯誤情境 - API 連線失敗

**Priority**: P2
**Type**: Error Handling

**Preconditions**:
1. 故意設定錯誤的 API Key
2. 或網路連線中斷

**Steps**:
| Step | Action | Expected Result |
|------|--------|-----------------|
| 1 | 嘗試開始對話 | 連線失敗 |
| 2 | 觀察錯誤處理 | 顯示友善錯誤訊息 |
| 3 | 檢查轉錄區域 | 保持空白或顯示錯誤狀態 |

**Pass Criteria**:
- [ ] 錯誤訊息清楚說明問題
- [ ] 不會顯示空白或亂碼轉錄
- [ ] 提供重試或切換提供者的建議

---

### TC-011: 效能測試 - 長時間對話

**Priority**: P3
**Type**: Performance

**Preconditions**:
1. 系統正常運行

**Steps**:
| Step | Action | Expected Result |
|------|--------|-----------------|
| 1 | 開始對話 | 正常開始 |
| 2 | 持續對話 10 分鐘 | 轉錄持續正常 |
| 3 | 持續對話 30 分鐘 | 系統穩定 |
| 4 | 檢查記憶體使用 | 無明顯記憶體洩漏 |

**Pass Criteria**:
- [ ] 30 分鐘對話轉錄顯示正常
- [ ] 無明顯效能下降
- [ ] 頁面不會崩潰或凍結

---

## Test Matrix

### 模型 x 語音 組合測試

| Model | Kore | Aoede | Puck | Charon | Fenrir |
|-------|:----:|:-----:|:----:|:------:|:------:|
| gemini-2.0-flash-live-001 | P1 | P2 | P2 | P3 | P3 |
| gemini-2.5-flash-native-audio-preview | P2 | P3 | P3 | P3 | P3 |
| gemini-2.0-flash-exp | P2 | P3 | P3 | P3 | P3 |

**P1**: 必須測試
**P2**: 應該測試
**P3**: 選擇性測試

---

## Regression Tests

確保此功能不影響現有功能：

- [ ] OpenAI Realtime 模式仍正常運作
- [ ] Cascade 模式仍正常運作
- [ ] 對話歷史記錄功能正常
- [ ] 延遲測量功能正常
- [ ] BYOL 憑證管理功能正常

---

## Sign-off

| 角色 | 姓名 | 日期 | 狀態 |
|------|------|------|------|
| Developer | | | Pending |
| QA | | | Pending |
| Product Owner | | | Pending |

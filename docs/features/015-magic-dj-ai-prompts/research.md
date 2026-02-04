# Research: Magic DJ AI Prompt Templates

**Feature**: 015-magic-dj-ai-prompts
**Date**: 2026-02-04

## Research Questions

### RQ-001: Gemini text_input 在 V2V 模式中的行為

**Decision**: 使用現有的 `send_text()` 方法透過 WebSocket 發送 `text_input` 訊息

**Rationale**:
- `GeminiRealtimeService.send_text()` 已在 `gemini_realtime.py:269-293` 實作
- 使用 `client_content.turns[{role: "user", parts: [{text: ...}]}]` 格式
- 後端 `_handle_text_input` handler 已在 `interaction_handler.py:348` 實作
- 前端透過 `sendMessage('text_input', { text: ... })` 即可使用

**Alternatives considered**:
- ❌ 建立新的 WebSocket message type：不必要，text_input 已可用
- ❌ 修改 system_prompt 再重新連線：延遲太高，會中斷對話流程
- ❌ 透過 REST API 發送：無法利用現有 WebSocket 連線，增加延遲

### RQ-002: AI 對話模式四欄佈局架構

**Decision**: 重新設計 `DJControlPanel` 的 AI 對話模式分支，用 `PromptTemplatePanel` + `StoryPromptPanel` 替代原 `AIVoiceChannelStrip` 的救場語音功能

**Rationale**:
- 現有 `DJControlPanel.tsx:158-186` 的 AI 模式已包含 `AIVoiceChannelStrip` + `ChannelBoard`
- 新佈局將 AI 控制（mic, status, interrupt）移至頂部常駐區域
- 第一欄改為 `PromptTemplatePanel`（互動式 prompt 按鈕）
- 第二欄改為 `StoryPromptPanel`（故事模板 + 自由輸入）
- 第三欄和第四欄（音效、音樂）維持現有 `ChannelStrip` 結構

**Alternatives considered**:
- ❌ 保留 AIVoiceChannelStrip 不變，另加 tab 切換：操作步驟多，不直覺
- ❌ 使用側邊抽屜 (drawer) 放 prompt template：遮擋主畫面，不利快速操作

### RQ-003: Prompt Template 資料儲存策略

**Decision**: 使用 localStorage + Zustand persist，與現有 magicDJStore 整合

**Rationale**:
- 現有 `magicDJStore.ts` 已使用 Zustand persist middleware（`persist` + `onRehydrateStorage`）
- Prompt template 資料量小（純文字），不需要 IndexedDB
- 與 tracks/settings 同一 store，方便 preset import/export
- 已有 preset 匯出/匯入機制（`TrackConfigPanel`），可自然擴展

**Alternatives considered**:
- ❌ 後端資料庫儲存：過度工程，此功能為純前端
- ❌ IndexedDB：資料量小，不需要
- ❌ 獨立 store：增加複雜度，且 preset 匯出需跨 store 同步

### RQ-004: 音效/音樂與 AI 語音同時播放

**Decision**: 利用現有多頻道架構，確保 AI 語音（WebSocket audio output）與前端音效/音樂（Web Audio API）互不干擾

**Rationale**:
- AI 語音透過 WebSocket 接收 PCM16 data，在前端透過 AudioContext 播放
- 音效/音樂已透過 `useMultiTrackPlayer` hook 使用獨立 AudioContext 播放
- 各頻道（voice, sfx, music）已有獨立音量控制和 mute 功能
- 瀏覽器 Web Audio API 原生支援多音軌同時播放

**Alternatives considered**:
- ❌ 使用 HTML5 Audio elements：已驗證 Web Audio API 更可靠
- ❌ Server-side audio mixing：延遲太高，不適合即時互動

### RQ-005: 預設 Prompt Template 內容設計

**Decision**: 提供 8 個預設 prompt template，針對 4-6 歲兒童互動場景

**Rationale**: 基於實際測試場景中 RD 最常需要的 AI 行為控制需求：

| 名稱 | Prompt 內容 | 使用場景 |
|------|------------|----------|
| 裝傻 | 「假裝你沒聽到剛才的問題，用可愛的方式岔開話題，不要直接回答。」 | 小孩問奇怪/敏感問題 |
| 轉移話題 | 「自然地轉移話題到一個有趣的新話題，比如問小朋友喜歡什麼動物或顏色。」 | 對話卡住或偏離 |
| 鼓勵 | 「用非常熱情和鼓勵的語氣讚美小朋友，告訴他做得很棒！」 | 小孩完成任務 |
| 等一下 | 「告訴小朋友你需要想一想，請他等一下，可以先唱首歌或數數。」 | 需要延遲時間 |
| 結束故事 | 「開始收尾這個故事，用一個溫馨的結局，然後跟小朋友說再見。」 | 準備結束互動 |
| 回到主題 | 「把對話帶回我們正在進行的故事或活動，自然地引導回來。」 | 小孩分心 |
| 簡短回答 | 「接下來的回覆請用一句話就好，不要說太長。」 | AI 回覆太冗長 |
| 多問問題 | 「多問小朋友問題，引導他多說話，表現出對他說的話很有興趣。」 | 鼓勵小孩表達 |

**Alternatives considered**:
- ❌ 更少的預設（4個）：覆蓋不足，常見場景會遺漏
- ❌ 更多的預設（15+個）：按鈕太多反而干擾快速操作

### RQ-006: 預設 Story Prompt 模板

**Decision**: 提供 4 個預設故事模板，涵蓋常見兒童互動場景

| 名稱 | Prompt 內容概要 | 場景 |
|------|----------------|------|
| 魔法森林 | 帶小朋友進入一座神奇的森林，遇到會說話的動物和精靈 | 探索冒險 |
| 海底冒險 | 和小朋友一起潛入海底，尋找寶藏，遇到海洋生物 | 海洋探索 |
| 太空旅行 | 搭乘太空船到不同星球，遇到外星朋友 | 科幻冒險 |
| 動物運動會 | 森林裡的動物們舉辦運動會，需要小朋友幫忙 | 體育活動 |

## Technology Stack Confirmation

- **Frontend**: TypeScript 5.3+, React 18.2+, Zustand, Tailwind CSS, Radix UI
- **WebSocket**: 現有 `useWebSocket` hook + 後端 `interaction_handler`
- **Audio**: Web Audio API（`useMultiTrackPlayer` hook）
- **Storage**: localStorage via Zustand persist
- **Backend**: 無新增後端功能，使用現有 `text_input` WebSocket handler

# Feature Specification: Pipecat TTS Server

**Feature Branch**: `001-pipecat-tts-server`
**Created**: 2026-01-16
**Status**: Draft
**Input**: User description: "建立基於 Pipecat 的 TTS API 伺服器與 Web 介面"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - 文字轉語音基本功能 (Priority: P1)

作為一個開發者，我想透過 API 將文字轉換為語音，以便將語音合成功能整合到我的應用程式中。

**Why this priority**: 這是 TTS 服務的核心價值，沒有這個功能，其他功能都沒有意義。

**Independent Test**: 可以透過發送一段文字到 API 端點，並驗證返回的音訊檔案是否可播放來完整測試。

**Acceptance Scenarios**:

1. **Given** 伺服器已啟動且運行中，**When** 用戶發送包含文字內容的請求，**Then** 系統返回對應的音訊資料
2. **Given** 伺服器已啟動，**When** 用戶發送空白文字請求，**Then** 系統返回適當的錯誤訊息
3. **Given** 伺服器已啟動，**When** 用戶發送超長文字（超過 5000 字元），**Then** 系統返回文字過長的錯誤訊息

---

### User Story 2 - Web 介面試聽 (Priority: P2)

作為一個用戶，我想透過 Web 介面輸入文字並即時試聽語音合成結果，以便評估語音品質。

**Why this priority**: Web 介面提供直觀的測試方式，對於評估和展示 TTS 功能至關重要，但依賴於 P1 的 API 功能。

**Independent Test**: 可以透過瀏覽器訪問 Web 頁面，輸入文字並點擊播放按鈕來測試。

**Acceptance Scenarios**:

1. **Given** 用戶在 Web 介面上，**When** 輸入文字並點擊「合成」按鈕，**Then** 頁面顯示音訊播放器並可即時播放
2. **Given** 用戶已合成語音，**When** 點擊「下載」按鈕，**Then** 音訊檔案下載到本機
3. **Given** 用戶在 Web 介面上，**When** 語音合成處理中，**Then** 顯示載入狀態指示器
4. **Given** 用戶選擇串流模式，**When** 點擊「合成」按鈕，**Then** 音訊邊合成邊播放，並顯示即時波形或進度
5. **Given** 用戶在 Web 介面上，**When** 從選單中選擇特定的 TTS 提供者（如 Azure, Google, ElevenLabs 或 VoAI），**Then** 系統使用該指定提供者進行後續的語音合成

---

### User Story 3 - 語音參數調整 (Priority: P3)

作為一個用戶，我想調整語音合成的參數（如語速、音調、音色），以便獲得符合需求的語音輸出。

**Why this priority**: 參數調整是進階功能，提升用戶體驗但非核心必要功能。

**Independent Test**: 可以透過 API 或 Web 介面發送帶有不同參數的請求，並比較輸出音訊的差異。

**Acceptance Scenarios**:

1. **Given** 用戶透過 API 或 Web 介面，**When** 指定語速參數（0.5x - 2.0x），**Then** 輸出音訊的語速符合指定值
2. **Given** 用戶透過 API 或 Web 介面，**When** 選擇不同的音色選項，**Then** 輸出音訊使用指定的音色

---

### Edge Cases

- 當 TTS 服務後端不可用時，系統應返回服務暫時不可用的錯誤，並提供重試建議
- 當用戶快速連續發送多個請求時，系統應正確處理並發請求或實施合理的速率限制
- 當輸入文字包含特殊字元或表情符號時，系統應適當處理或過濾
- 當網路連線中斷時，Web 介面應顯示適當的錯誤訊息

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: 系統 MUST 提供 API 端點接收文字輸入並返回音訊資料
- **FR-002**: 系統 MUST 支援至少一種音訊輸出格式（預設為 MP3）
- **FR-003**: 系統 MUST 提供 Web 介面讓用戶輸入文字並試聽結果
- **FR-004**: Web 介面 MUST 提供音訊播放器功能
- **FR-005**: Web 介面 MUST 提供音訊檔案下載功能
- **FR-006**: 系統 MUST 驗證輸入文字長度（上限 5000 字元）
- **FR-007**: 系統 MUST 在處理失敗時返回有意義的錯誤訊息
- **FR-008**: 系統 MUST 支援語速調整（0.5x - 2.0x 範圍）
- **FR-009**: 系統 SHOULD 支援多種音色選項（依各提供者提供的音色）
- **FR-010**: 系統 MUST 記錄所有 API 請求以供除錯與監控
- **FR-011**: 系統 MUST 支援 Azure Speech、ElevenLabs、Google Cloud TTS 與 **VoAI** 四個提供者
- **FR-012**: 用戶 MUST 能夠在請求時指定使用的 TTS 提供者
- **FR-013**: 系統 MUST 支援多語言合成，至少包含：中文（繁體/簡體）、英文、日文、韓文
- **FR-014**: 用戶 MUST 能夠在請求時指定輸出語言
- **FR-015**: 系統 MUST 支援批次合成模式（完整合成後返回音訊）
- **FR-016**: 系統 MUST 支援即時串流模式（邊合成邊輸出音訊）
- **FR-017**: 用戶 MUST 能夠在請求時指定輸出模式（批次或串流）
- **FR-018**: Web 介面 MUST 支援串流播放模式（邊接收邊播放）
- **FR-019**: Web 介面 MUST 在串流播放時顯示即時波形或進度指示，使用 **WaveSurfer.js** 實作
- **FR-020**: 系統 MUST 支援 Google SSO 登入進行身份驗證，Scope 限制為 `openid profile email`
- **FR-021**: 系統 MUST 永久儲存合成後的音訊檔案，目錄結構為 `storage/{provider}/{uuid}.mp3`，保留策略為用戶手動管理
- **FR-022**: Web 前端 MUST 使用 React + Vite 架構開發

### Key Entities

- **TTSRequest**: 代表一次語音合成請求，包含輸入文字、TTS 提供者選擇、語言選擇、輸出模式（批次/串流）、語音參數（語速、音色）、輸出格式偏好
- **TTSResult**: 代表語音合成結果，包含音訊資料、音訊格式、處理耗時、元資料（字數、音訊長度）、存儲路徑
- **VoiceOption**: 代表可用的音色選項，包含音色識別碼、名稱、語言、描述

## Clarifications

### Session 2026-01-16

- Q: 初始實作應支援哪些 TTS 服務提供者？ → A: 同時支援 Azure Speech、ElevenLabs、Google Cloud TTS 與 VoAI 四個提供者，MVP 即支援切換
- Q: 系統需支援哪些語言？ → A: 多語言支援，包含中文（繁/簡）、英文、日文、韓文等亞洲主要語言
- Q: 音訊輸出模式為何？ → A: 兩者皆支援，批次合成與即時串流可透過 API 參數切換
- Q: Web 介面是否支援串流播放？ → A: 是，Web 介面需支援串流播放，即時顯示波形/進度
- Q: 系統應使用何種身份驗證方式？ → A: 使用 Google SSO 登入
- Q: 合成後的音訊檔案應如何處理？ → A: 永久儲存 (Permanent)
- Q: Web 前端應使用何種框架？ → A: React + Vite
- Q: Google SSO 需要哪些權限 Scope？ → A: `openid profile email`
- Q: 音訊檔案存儲結構為何？ → A: `storage/{provider}/{uuid}.mp3`
- Q: 波形視覺化使用哪個庫？ → A: WaveSurfer.js
- Q: 音訊檔案保留多久？ → A: 由用戶手動管理 (User Managed)

## Assumptions

- Pipecat 框架已可正常運作並支援 TTS 功能
- 需要 Azure Speech、ElevenLabs、Google Cloud TTS 與 VoAI 四個提供者的 API 金鑰
- 目標用戶為開發者和技術人員
- 單一伺服器部署，不考慮分散式架構
- Web 介面僅供測試和展示用途，不需要支援高併發

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 用戶從輸入文字到聽到語音的等待時間不超過 5 秒（100 字以內的文字）
- **SC-002**: 系統可同時處理至少 10 個並發請求而不會失敗
- **SC-003**: 90% 的合成請求在首次嘗試即成功完成
- **SC-004**: Web 介面在主流瀏覽器（Chrome、Firefox、Safari、Edge 最新版本）上正常運作
- **SC-005**: API 錯誤訊息清晰到用戶可以自行理解問題所在並採取行動
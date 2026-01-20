# Feature Specification: Multi-Role TTS

**Feature Branch**: `005-multi-role-tts`
**Created**: 2025-01-19
**Status**: Draft
**Input**: User description: "在左側menu tts 測試下面加一個新的多角色 tts 功能頁面，這個頁面可以選擇 provider，根據不同 provider 支援的功能和角色文字定義，頁面會產生不同的表格提供選擇"

## Clarifications

### Session 2025-01-19

- Q: 系統支援的最大說話者數量？ → A: 最多 6 位說話者（小組對話）
- Q: 對話逐字稿總長度限制？ → A: 預設 5000 字元，依 Provider 實際上限動態調整並顯示警告
- Q: 不支援原生多角色的 Provider 處理方式？ → A: 顯示提示並提供選項，讓使用者選擇是否繼續使用分段合併方式

## User Scenarios & Testing *(mandatory)*

### User Story 1 - 輸入對話逐字稿並選擇多角色語音 (Priority: P1)

使用者想要將多角色對話逐字稿（如 A: 你好 B: 嗨 A: 今天天氣很好）轉換為包含多種聲音的音訊檔案。使用者進入多角色 TTS 頁面後，首先選擇 TTS Provider，系統會根據該 Provider 的多角色支援能力顯示相應的設定介面。使用者輸入對話逐字稿，系統自動解析出說話者（A、B 等），並為每位說話者分配一個獨立的語音選擇欄位。

**Why this priority**: 這是多角色 TTS 功能的核心價值，沒有這個功能，整個頁面就沒有意義。

**Independent Test**: 可以透過選擇 Provider、輸入對話文字、為每個角色指定聲音、然後產生音訊來完整測試，最終可聽到多角色交替說話的音檔。

**Acceptance Scenarios**:

1. **Given** 使用者在多角色 TTS 頁面且已選擇支援原生多角色的 Provider（如 ElevenLabs），**When** 使用者輸入「A: 你好 B: 嗨」格式的逐字稿，**Then** 系統自動解析出 A 和 B 兩個說話者，並顯示兩個獨立的語音選擇下拉選單。

2. **Given** 使用者已完成說話者語音配對設定，**When** 使用者點擊「產生語音」按鈕，**Then** 系統產生一段音訊，包含 A 和 B 交替說話的聲音。

3. **Given** 使用者選擇不支援原生多角色的 Provider（如 OpenAI），**When** 使用者輸入多角色對話，**Then** 系統顯示提示說明將使用「分段合併」方式處理，並提供選項讓使用者確認是否繼續。

---

### User Story 2 - 切換 Provider 並查看功能差異 (Priority: P2)

使用者想要比較不同 TTS Provider 對多角色對話的支援程度。使用者可以切換 Provider，系統會即時更新介面以反映該 Provider 的能力，包括是否支援原生多聲音、支援的特殊功能（如打斷效果、重疊說話）等。

**Why this priority**: 這是 Voice Lab 比較工具的核心價值，幫助使用者選擇最適合的 Provider。

**Independent Test**: 切換不同 Provider 後，觀察介面變化和功能提示是否正確反映各家能力。

**Acceptance Scenarios**:

1. **Given** 使用者在多角色 TTS 頁面，**When** 使用者從 ElevenLabs 切換到 Azure，**Then** 介面顯示 Azure 的 SSML 多聲音支援資訊，並更新可用的語音清單。

2. **Given** 使用者選擇 ElevenLabs v3，**When** 頁面載入完成，**Then** 顯示該 Provider 支援的進階功能列表（如 [interrupting]、[overlapping]、[laughs] 等 Audio Tags）。

---

### User Story 3 - 預覽與下載多角色音訊 (Priority: P3)

使用者完成多角色 TTS 設定後，想要預覽產生的音訊並下載保存。

**Why this priority**: 輸出結果的播放和下載是完成整個流程的必要功能，但相對核心功能較為次要。

**Independent Test**: 產生音訊後，可在頁面上播放預覽，並下載為 MP3 檔案。

**Acceptance Scenarios**:

1. **Given** 系統已成功產生多角色音訊，**When** 使用者點擊播放按鈕，**Then** 音訊在頁面內播放，使用者可聽到多角色交替說話。

2. **Given** 音訊已產生且播放正常，**When** 使用者點擊下載按鈕，**Then** 瀏覽器下載該音訊檔案。

---

### Edge Cases

- 使用者輸入的逐字稿無法解析出說話者（如純文字沒有標示角色）時，系統提示格式錯誤並顯示正確格式範例。
- 使用者輸入超過 6 位說話者時，系統顯示「最多支援 6 位說話者」的限制提示。
- 網路錯誤導致 TTS 請求失敗時，顯示錯誤訊息並允許重試。
- 使用者在音訊產生過程中切換 Provider，系統取消前一個請求或提示確認。

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: 系統 MUST 在側邊選單的「TTS 測試」項目下方新增「多角色 TTS」導航項目。
- **FR-002**: 系統 MUST 提供 Provider 選擇器，顯示支援的 TTS Provider 清單（ElevenLabs、Azure、Google Cloud、OpenAI、Cartesia、Deepgram）。
- **FR-003**: 系統 MUST 根據所選 Provider 顯示其多角色支援能力的資訊卡片（原生支援、需分段合併、不支援等）。
- **FR-003a**: 當使用者選擇不支援原生多角色的 Provider 時，系統 MUST 顯示提示並提供選項讓使用者確認是否使用分段合併方式繼續。
- **FR-004**: 系統 MUST 提供逐字稿輸入區域，接受格式如「A: 文字內容」或「[A] 文字內容」的多角色對話，預設上限 5000 字元，並依所選 Provider 的實際字元上限動態調整限制，在使用者接近上限時顯示即時警告。
- **FR-005**: 系統 MUST 自動解析輸入文字中的說話者標識（最多支援 6 位說話者），並為每位說話者顯示獨立的語音選擇器。
- **FR-006**: 系統 MUST 為每個 Provider 載入其可用的語音清單，供使用者為每位說話者分配語音。
- **FR-007**: 系統 MUST 提供「產生語音」按鈕，點擊後呼叫後端 API 產生多角色音訊。
- **FR-008**: 系統 MUST 顯示音訊播放器，支援播放、暫停、進度調整。
- **FR-009**: 系統 MUST 提供音訊下載功能。
- **FR-010**: 系統 MUST 顯示產生結果的元資料（延遲時間、音訊長度、使用的 Provider）。
- **FR-011**: 系統 MUST 在處理過程中顯示載入指示器。
- **FR-012**: 系統 MUST 在發生錯誤時顯示使用者友善的錯誤訊息。

### Key Entities

- **Provider**: TTS 服務提供者，具有名稱、多角色支援類型（native/segmented/unsupported）、可用語音清單、進階功能清單等屬性。
- **DialogueTurn**: 對話中的單一發言，包含說話者標識和文字內容。
- **VoiceAssignment**: 說話者與語音的對應關係，包含說話者標識和選定的語音 ID。
- **MultiRoleTTSRequest**: 多角色 TTS 請求，包含 Provider、對話內容、語音分配等。
- **MultiRoleTTSResult**: 多角色 TTS 結果，包含音訊資料、延遲時間、時長等元資料。

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 使用者可在 3 分鐘內完成首次多角色 TTS 操作（從進入頁面到聽到產生的音訊）。
- **SC-002**: 系統正確解析至少 95% 符合規定格式的多角色逐字稿。
- **SC-003**: 產生的多角色音訊中，每位說話者的聲音可明顯區分。
- **SC-004**: 頁面在不同 Provider 之間切換時，介面更新在 1 秒內完成。
- **SC-005**: 使用者首次使用時無需額外說明即可理解如何輸入多角色對話（透過介面提示或範例）。

## Assumptions

- 後端已實作或將實作多角色 TTS API 端點，支援呼叫各 Provider 產生音訊。
- 各 Provider 的 API 金鑰已透過現有的「API 金鑰」設定頁面配置。
- 前端使用現有的 React + TypeScript 技術棧和 UI 元件庫。
- 各 Provider 的語音清單可透過現有的 API 取得。

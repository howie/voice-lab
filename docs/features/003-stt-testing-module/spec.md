# Feature Specification: STT Speech-to-Text Testing Module

**Feature Branch**: `003-stt-testing-module`
**Created**: 2026-01-18
**Status**: Draft
**Input**: User description: "STT Speech-to-Text Testing Module - Build a testing platform for Speech-to-Text across different providers with microphone recording, file upload, and WER calculation"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Upload Audio File for Transcription (Priority: P1)

使用者想要上傳預錄的音檔，透過不同的 STT 服務進行語音辨識，比較各家的辨識結果。

**Why this priority**: 這是 STT 測試的核心功能，讓使用者能夠用相同的音檔測試多家 STT 服務，進行公平比較。這是評估 STT 準確度的基礎功能。

**Independent Test**: 可透過上傳一個測試音檔，選擇一個 STT Provider，並驗證返回的轉錄文字來完整測試。

**Acceptance Scenarios**:

1. **Given** 使用者已登入系統, **When** 使用者上傳一個 MP3/WAV 音檔並選擇 Azure STT, **Then** 系統顯示該音檔的轉錄文字結果
2. **Given** 使用者已上傳音檔, **When** 使用者切換到 GCP STT Provider, **Then** 系統使用新的 Provider 重新辨識並顯示結果
3. **Given** 使用者上傳一個損壞的音檔, **When** 系統處理該檔案, **Then** 系統顯示友善的錯誤訊息說明檔案無法處理

---

### User Story 2 - Real-time Microphone Recording (Priority: P2)

使用者想要直接使用麥克風錄音，錄音完成後進行 STT 辨識測試。

**Why this priority**: 即時錄音讓使用者能夠快速測試不同的語音場景，無需預先準備音檔，提升測試效率。

**Independent Test**: 可透過點擊錄音按鈕、說一段話、停止錄音，並驗證轉錄結果來完整測試。

**Acceptance Scenarios**:

1. **Given** 使用者已授權麥克風權限, **When** 使用者點擊錄音按鈕並說話, **Then** 系統顯示錄音波形並在停止後進行辨識
2. **Given** 使用者正在錄音, **When** 使用者點擊停止按鈕, **Then** 系統自動將錄音傳送至選定的 STT Provider 進行批次辨識
3. **Given** 使用者未授權麥克風權限, **When** 使用者嘗試錄音, **Then** 系統顯示提示訊息引導使用者授權

---

### User Story 3 - WER Calculation and Ground Truth Comparison (Priority: P3)

使用者想要輸入正確答案（Ground Truth），計算各家 STT 的 Word Error Rate (WER)，量化比較辨識準確度。

**Why this priority**: WER 是評估 STT 準確度的業界標準指標，讓使用者能客觀比較不同 Provider 的表現。

**Independent Test**: 可透過輸入 Ground Truth 文字、執行辨識、並驗證 WER 計算結果來完整測試。

**Acceptance Scenarios**:

1. **Given** 使用者已完成一次 STT 辨識, **When** 使用者輸入正確的 Ground Truth 文字, **Then** 系統計算並顯示 WER、插入錯誤、刪除錯誤、替換錯誤的詳細數據
2. **Given** 使用者使用多個 Provider 辨識同一音檔, **When** 使用者查看比較結果, **Then** 系統以表格形式顯示各 Provider 的 WER 比較
3. **Given** Ground Truth 和辨識結果完全相同, **When** 系統計算 WER, **Then** 顯示 WER 為 0%

---

### User Story 4 - Child Voice Mode Testing (Priority: P4)

使用者想要測試各家 STT 對兒童語音的辨識效果，因為兒童語音辨識是常見的困難場景。

**Why this priority**: 兒童語音是 STT 的重要應用場景（教育、親子互動），但辨識準確度通常較低，需要專門測試。

**Independent Test**: 可透過上傳兒童語音音檔或錄製兒童語音，啟用兒童模式，並比較開啟/關閉兒童模式的辨識結果來完整測試。

**Acceptance Scenarios**:

1. **Given** 使用者上傳一段兒童語音, **When** 使用者啟用「兒童語音模式」, **Then** 系統使用針對兒童語音優化的參數進行辨識
2. **Given** 使用者已完成兒童語音辨識, **When** 使用者切換兒童模式開/關, **Then** 系統顯示兩種模式的辨識結果差異比較

---

### Edge Cases

- 當音檔長度超過 Provider 限制時，系統自動將音檔分段處理，分別辨識後合併結果並標示分段邊界
- 當音檔格式不支援時，系統顯示支援的格式清單並建議轉換
- 當 STT Provider API 回傳錯誤或逾時時，系統顯示具體錯誤原因並建議解決方案
- 當使用者的 Provider API Key 額度用盡時，系統顯示額度狀態並建議更換 Provider 或更新 Key
- 當音檔中完全無語音（靜音）時，系統辨識後顯示「未偵測到語音」

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST support uploading audio files in MP3, WAV, M4A, and FLAC formats
- **FR-002**: System MUST integrate with the following STT Providers (Batch API):
    - **Cloud Standard**: Google Cloud Speech-to-Text, Azure Speech Services
    - **Market Leaders**: OpenAI Whisper, Deepgram (Nova-2), AssemblyAI, ElevenLabs Scribe, Speechmatics
- **FR-003**: Users MUST be able to select which STT Provider to use for each transcription request via a dropdown menu. The dropdown MUST only display Providers for which the user has configured a valid API Key (consistent with TTS Provider selector behavior)
- **FR-004**: System MUST support browser-based microphone recording with visual waveform feedback
- **FR-005**: System MUST process all transcriptions in batch mode (recording completes before transcription begins)
- **FR-006**: System MUST calculate and display error rate when Ground Truth is provided: WER (Word Error Rate) for English, CER (Character Error Rate) for CJK languages (zh-TW, zh-CN, ja-JP, ko-KR)
- **FR-007**: System MUST display detailed error breakdown: insertion errors, deletion errors, and substitution errors (at word level for English, character level for CJK)
- **FR-008**: System MUST support multiple languages: Traditional Chinese (zh-TW), Simplified Chinese (zh-CN), English (en-US), Japanese (ja-JP), and Korean (ko-KR)
- **FR-009**: System MUST provide a "Child Voice Mode" option that applies child-optimized parameters when available
- **FR-010**: System MUST permanently save transcription results to history for later review and comparison
- **FR-011**: System MUST provide a history list view where users can browse past transcription records and manually delete unwanted entries
- **FR-012**: System MUST use user-provided API keys (BYOL) when available, falling back to system keys
- **FR-013**: System MUST display Provider-specific metadata with results (confidence scores, word timestamps when available)
- **FR-014**: System MUST allow side-by-side comparison of transcription results from multiple Providers
- **FR-015**: System MUST enforce Provider-specific file size and duration limits, displaying the applicable constraints for the currently selected Provider
- **FR-016**: System MUST automatically segment and merge results when audio exceeds a Provider's single-request limit

### Key Entities

- **TranscriptionRequest**: Represents a single STT request, including source audio reference, selected Provider, language, and options (child mode)
- **TranscriptionResult**: Contains the transcribed text, confidence score, word-level timestamps (if available), processing time, and Provider metadata
- **AudioFile**: Uploaded or recorded audio, including format, duration, sample rate, and storage reference
- **WERAnalysis**: Calculated WER metrics for a transcription, including total WER percentage, insertion/deletion/substitution counts, and aligned text comparison
- **GroundTruth**: User-provided correct transcription text for WER calculation, linked to a specific audio file

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Users can complete a full STT test cycle (upload/record → transcribe → view result) in under 2 minutes for audio files up to 1 minute
- **SC-002**: System supports at least 3 concurrent STT transcription requests without degradation
- **SC-003**: WER calculation completes and displays within 1 second after Ground Truth is submitted
- **SC-004**: 95% of users successfully complete their first STT test without requiring help documentation
- **SC-005**: System maintains transcription history for comparison, accessible within 3 clicks from the main STT page
- **SC-006**: Side-by-side Provider comparison is available for at least 3 Providers simultaneously
- **SC-007**: Audio recording quality is sufficient for accurate transcription (16kHz sample rate minimum)

## Clarifications

### Session 2026-01-18

- Q: 長音檔處理策略（超過 Provider 限制時）？ → A: 自動分段處理，系統自動將長音檔切分，分別辨識後合併結果
- Q: 中日韓文的錯誤率計算方式？ → A: CJK 語言使用 CER（字元錯誤率），英文使用 WER（詞錯誤率）
- Q: 轉錄歷史紀錄保留期限？ → A: 永久保留，提供歷史紀錄清單讓使用者查看並可手動刪除
- Q: 音檔上傳大小限制？ → A: 依各 Provider 規格而定，系統動態顯示當前所選 Provider 的檔案大小/時長限制
- Q: Streaming 辨識是否納入本功能？ → A: **否，Streaming STT 延後至 Phase 4 Interaction 模組**。本模組專注於批次模式的準確度測試（WER/CER），Streaming 更適合即時對話場景。

## Assumptions

- Users have already set up their Provider API keys via the existing Provider Management Interface (002 feature)
- Users have modern browsers (Chrome, Firefox, Safari, Edge) that support MediaRecorder API for microphone access
- STT Providers maintain their current API stability and rate limits
- Audio files uploaded are primarily speech content (not music or environmental sounds)
- The existing authentication system (Google SSO) from feature 001 is available and functional
- Streaming transcription will be implemented in Phase 4 (Interaction Module) for real-time conversation testing

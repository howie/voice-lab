# Feature Specification: Audiobook Production System

**Feature Branch**: `009-audiobook-production`
**Created**: 2026-01-22
**Status**: Draft
**Input**: 建立類似「豬探長」風格的多角色有聲故事製作系統，支援 10-20 分鐘長篇內容、角色編輯、非同步分段生成與背景音樂融合

---

## Problem Statement

目前 VoAI 多角色 TTS 系統（008 功能）專注於短篇對話合成，無法滿足長篇有聲故事製作的需求：

### 1. 缺乏長篇內容支援

- 現有 Native 模式限制（Azure 50,000 字元、ElevenLabs 5,000 字元）無法處理 10-20 分鐘故事
- 無劇本（Script）管理介面
- 無章節分段功能

### 2. 缺乏角色管理系統

- 無角色（Character）定義與持久化
- 無法為角色指定聲音、年齡、性別、語調等屬性
- 無法跨專案重用角色設定

### 3. 缺乏非同步生產工作流

- 長篇內容需要非同步分段生成
- 需要進度追蹤與狀態管理
- 需要失敗重試與斷點續傳

### 4. 缺乏後製功能

- 無背景音樂融合功能
- 無音訊混音（Mixing）功能
- 無最終輸出匯出功能

---

## Clarifications

### Session 2026-01-22

- Q: 目標故事長度？ → A: 10-20 分鐘（約 2,000-4,000 字中文）
- Q: 角色數量上限？ → A: 建議 10 個角色以內，不設硬性限制
- Q: 背景音樂來源？ → A: 使用者上傳，支援 MP3/WAV 格式
- Q: 輸出格式？ → A: MP3（主要）、WAV（可選）
- Q: 是否需要即時預覽？ → A: 單一片段可即時預覽，完整故事需等待生成完成

---

## Dependencies

- **008-voai-multi-role-voice-generation**: Voice 資料庫與篩選功能
- **007-async-job-mgmt**: 背景任務管理框架
- **005-multi-role-tts**: 基礎 TTS 合成能力

---

## User Scenarios & Testing

### User Story 1 - 建立故事專案與劇本編輯 (Priority: P1)

使用者想要建立一個有聲故事專案，輸入多角色劇本（類似劇本格式），系統自動識別角色並允許編輯。

**Why this priority**: 沒有劇本輸入功能，後續所有功能都無法運作。這是整個系統的入口。

**Independent Test**: 建立專案、貼上劇本、驗證角色自動識別並可編輯

**Acceptance Scenarios**:

1. **Given** 使用者在專案列表頁面，**When** 使用者點擊「建立新專案」並輸入名稱，**Then** 系統建立空白專案並進入編輯頁面。

2. **Given** 使用者在專案編輯頁面，**When** 使用者貼上劇本文字（格式：`角色名：台詞`），**Then** 系統自動解析並識別所有角色。

3. **Given** 系統已識別劇本中的角色，**When** 使用者檢視角色列表，**Then** 系統顯示所有角色並允許編輯其屬性（聲音、性別、年齡、語調）。

4. **Given** 使用者在劇本編輯器中，**When** 使用者修改台詞內容，**Then** 系統即時更新並保存變更。

---

### User Story 2 - 角色聲音設定與預覽 (Priority: P1)

使用者想要為每個角色選擇適合的聲音，並可預覽該角色的語音效果。

**Why this priority**: 聲音是有聲故事的核心，使用者必須能夠選擇和預覽聲音才能確保品質。

**Independent Test**: 選擇角色聲音、預覽單句台詞、確認聲音符合預期

**Acceptance Scenarios**:

1. **Given** 使用者在角色設定頁面，**When** 使用者點擊「選擇聲音」，**Then** 系統顯示聲音選擇器（支援依 provider、語言、性別、年齡篩選）。

2. **Given** 使用者已選擇角色聲音，**When** 使用者點擊「預覽」，**Then** 系統使用該聲音合成角色的第一句台詞並播放。

3. **Given** 使用者想要微調聲音，**When** 使用者調整語速、音調參數，**Then** 系統即時更新預覽效果。

---

### User Story 3 - 非同步故事生成 (Priority: P1)

使用者想要生成完整的有聲故事，系統以非同步方式分段生成所有角色台詞。

**Why this priority**: 這是核心功能，長篇內容必須以非同步方式處理才能完成。

**Independent Test**: 啟動生成、查看進度、等待完成、下載結果

**Acceptance Scenarios**:

1. **Given** 使用者已完成劇本和角色設定，**When** 使用者點擊「開始生成」，**Then** 系統建立非同步 Job 並顯示進度頁面。

2. **Given** 生成 Job 正在執行，**When** 使用者查看進度頁面，**Then** 系統顯示已完成/總數片段數、預估剩餘時間、目前處理的角色/台詞。

3. **Given** 單一片段生成失敗，**When** 系統偵測到錯誤，**Then** 系統自動重試（最多 3 次），仍失敗則標記該片段並繼續處理其他片段。

4. **Given** 所有片段生成完成，**When** 使用者查看結果，**Then** 系統自動合併所有片段為完整音訊，並提供下載連結。

---

### User Story 4 - 背景音樂融合 (Priority: P2)

使用者想要為故事加入背景音樂，並調整音樂與旁白的音量平衡。

**Why this priority**: 背景音樂提升專業度，但非核心功能，可在 MVP 後加入。

**Independent Test**: 上傳背景音樂、調整音量、預覽混音效果、匯出最終版本

**Acceptance Scenarios**:

1. **Given** 使用者在專案設定頁面，**When** 使用者上傳背景音樂檔案（MP3/WAV），**Then** 系統儲存檔案並顯示音樂資訊（時長、格式）。

2. **Given** 使用者已上傳背景音樂，**When** 使用者調整音樂音量（0-100%），**Then** 系統記錄設定。

3. **Given** 故事已生成完成且已設定背景音樂，**When** 使用者點擊「混音」，**Then** 系統將背景音樂與旁白混合，並提供預覽。

4. **Given** 背景音樂比故事短，**When** 系統執行混音，**Then** 系統自動循環播放背景音樂直到故事結束。

---

### User Story 5 - 專案管理與匯出 (Priority: P2)

使用者想要管理多個故事專案，並匯出最終成品。

**Why this priority**: 專案管理是基本功能，但不影響單一故事製作流程。

**Independent Test**: 列出專案、複製專案、匯出為 MP3/WAV

**Acceptance Scenarios**:

1. **Given** 使用者有多個專案，**When** 使用者查看專案列表，**Then** 系統顯示所有專案及其狀態（草稿/生成中/完成）。

2. **Given** 使用者想要基於現有專案建立新版本，**When** 使用者點擊「複製專案」，**Then** 系統複製所有設定（劇本、角色、音樂）到新專案。

3. **Given** 故事已完成生成與混音，**When** 使用者點擊「匯出」並選擇格式，**Then** 系統提供 MP3（預設）或 WAV 格式下載。

---

### User Story 6 - 章節與書籤功能 (Priority: P3)

使用者想要將長篇故事分成多個章節，並在特定位置加入書籤。

**Why this priority**: 進階功能，適用於超長篇內容，MVP 可延後。

**Independent Test**: 建立章節、設定章節標題、在輸出中包含章節標記

**Acceptance Scenarios**:

1. **Given** 使用者在劇本編輯器中，**When** 使用者插入章節分隔符，**Then** 系統識別章節邊界並允許設定章節標題。

2. **Given** 故事有多個章節，**When** 使用者匯出為 MP3，**Then** 系統在 MP3 metadata 中包含章節資訊（ID3 chapters）。

---

### Edge Cases

- 劇本格式錯誤時，系統提示錯誤位置並建議修正
- 角色名稱重複時，系統合併為同一角色
- 生成過程中使用者關閉頁面，Job 繼續在背景執行
- 背景音樂檔案過大（>50MB）時，提示壓縮或使用較短版本
- 角色使用的聲音被 Provider 移除時，提示使用者重新選擇
- 生成中途取消時，保留已生成的片段供後續使用

---

## Requirements

### Functional Requirements

**專案與劇本管理**

- **FR-001**: 系統 MUST 提供專案 CRUD 功能（建立、讀取、更新、刪除）
- **FR-002**: 系統 MUST 支援劇本格式解析（`角色名：台詞` 或 `角色名: 台詞`）
- **FR-003**: 系統 MUST 自動從劇本中識別並提取角色
- **FR-004**: 系統 MUST 支援劇本即時編輯與自動儲存
- **FR-005**: 系統 SHOULD 支援劇本匯入（TXT、純文字格式）

**角色管理**

- **FR-006**: 系統 MUST 允許為每個角色設定聲音（voice_id）
- **FR-007**: 系統 MUST 允許為每個角色設定屬性（性別、年齡、語調）
- **FR-008**: 系統 MUST 整合 008 功能的聲音篩選 API（依 age_group、gender、style 篩選）
- **FR-009**: 系統 MUST 提供單一台詞預覽功能
- **FR-010**: 系統 SHOULD 支援角色範本儲存與重用

**非同步生成**

- **FR-011**: 系統 MUST 以非同步 Job 方式處理長篇故事生成
- **FR-012**: 系統 MUST 將故事拆分為多個片段（每個台詞為一個片段）
- **FR-013**: 系統 MUST 提供生成進度追蹤（已完成/總數、百分比、預估時間）
- **FR-014**: 系統 MUST 在片段生成失敗時自動重試（最多 3 次）
- **FR-015**: 系統 MUST 在所有片段完成後自動合併為完整音訊
- **FR-016**: 系統 SHOULD 支援暫停/繼續生成

**背景音樂**

- **FR-017**: 系統 MUST 支援背景音樂上傳（MP3、WAV 格式）
- **FR-018**: 系統 MUST 支援背景音樂音量調整（0-100%）
- **FR-019**: 系統 MUST 支援旁白與背景音樂混音
- **FR-020**: 系統 MUST 在背景音樂較短時自動循環
- **FR-021**: 系統 SHOULD 支援淡入淡出效果

**匯出與輸出**

- **FR-022**: 系統 MUST 支援 MP3 格式匯出
- **FR-023**: 系統 SHOULD 支援 WAV 格式匯出
- **FR-024**: 系統 SHOULD 在 MP3 中包含 ID3 metadata（標題、作者、章節）

---

### Key Entities

**AudiobookProject（有聲書專案）**
```python
class AudiobookProject:
    id: UUID
    name: str                      # 專案名稱
    description: str | None        # 專案描述
    status: ProjectStatus          # draft, generating, completed, failed
    script_content: str            # 劇本原始內容
    language: str                  # 預設語言 (zh-TW)
    background_music_id: UUID | None
    background_music_volume: float # 0.0 - 1.0
    output_audio_url: str | None   # 最終輸出
    created_at: datetime
    updated_at: datetime
    user_id: UUID                  # 所屬使用者
```

**Character（角色）**
```python
class Character:
    id: UUID
    project_id: UUID
    name: str                      # 角色名稱（從劇本提取）
    voice_id: str                  # provider:voice_id
    gender: str | None             # male, female, neutral
    age_group: str | None          # child, young, adult, senior
    style: str | None              # cheerful, sad, etc.
    speech_rate: float             # 語速 0.5 - 2.0
    pitch: float                   # 音調 -50% - +50%
    created_at: datetime
    updated_at: datetime
```

**ScriptTurn（劇本台詞）**
```python
class ScriptTurn:
    id: UUID
    project_id: UUID
    character_id: UUID
    sequence: int                  # 順序
    text: str                      # 台詞內容
    chapter: str | None            # 章節名稱
    audio_url: str | None          # 生成的音訊 URL
    duration_ms: int | None        # 音訊時長
    status: TurnStatus             # pending, generating, completed, failed
    error_message: str | None
    created_at: datetime
```

**AudiobookGenerationJob（生成任務）**
```python
class AudiobookGenerationJob:
    id: UUID
    project_id: UUID
    status: JobStatus              # pending, running, completed, failed
    total_turns: int
    completed_turns: int
    failed_turns: int
    started_at: datetime | None
    completed_at: datetime | None
    error_message: str | None
    created_at: datetime
```

**BackgroundMusic（背景音樂）**
```python
class BackgroundMusic:
    id: UUID
    project_id: UUID
    filename: str
    file_url: str
    duration_ms: int
    format: str                    # mp3, wav
    file_size_bytes: int
    uploaded_at: datetime
```

---

## Success Criteria

### Measurable Outcomes

- **SC-001**: 使用者可在 5 分鐘內完成專案建立與劇本輸入
- **SC-002**: 系統正確識別 95% 以上的角色（標準劇本格式）
- **SC-003**: 10 分鐘故事（約 2,000 字）的生成時間 < 15 分鐘
- **SC-004**: 生成失敗率 < 5%（單一片段）
- **SC-005**: 使用者可在任何時候查看生成進度，延遲 < 3 秒
- **SC-006**: 混音後的音訊品質評分 > 4/5（使用者調查）
- **SC-007**: 90% 的使用者可在無教學情況下完成第一個故事

---

## Technical Design Notes

### 劇本格式解析

```python
# 支援的格式
「角色名：台詞內容」      # 中文冒號
「角色名: 台詞內容」      # 英文冒號
「角色名：『台詞內容』」   # 引號包裹

# 解析正則
pattern = r'^([^：:]+)[：:]\s*(.+)$'
```

### 生成流程

```text
1. 解析劇本 → 產生 ScriptTurn 列表
2. 建立 AudiobookGenerationJob
3. 對每個 ScriptTurn：
   a. 查詢 Character 的聲音設定
   b. 呼叫 TTS API 生成音訊
   c. 儲存音訊檔案
   d. 更新 ScriptTurn 狀態
4. 所有 Turn 完成後，使用 pydub 合併
5. 若有背景音樂，執行混音
6. 更新 Project 狀態與輸出 URL
```

### 音訊處理

```python
# 合併片段
from pydub import AudioSegment

combined = AudioSegment.empty()
for turn in turns:
    audio = AudioSegment.from_file(turn.audio_url)
    combined += audio
    combined += AudioSegment.silent(duration=300)  # 台詞間隔

# 背景音樂混音
if background_music:
    bg = AudioSegment.from_file(bg_music_url)
    # 循環至足夠長度
    while len(bg) < len(combined):
        bg += bg
    bg = bg[:len(combined)]
    # 調整音量
    bg = bg - (20 * (1 - volume))  # volume: 0-1
    # 混合
    final = combined.overlay(bg)
```

---

## Scope Boundaries

### In Scope

- 專案與劇本 CRUD
- 角色自動識別與設定
- 聲音選擇與預覽
- 非同步分段生成
- 進度追蹤
- 背景音樂混音
- MP3/WAV 匯出

### Out of Scope

- 即時協作編輯（多人同時編輯）
- AI 劇本生成
- 音效庫（僅支援背景音樂）
- 影片生成（僅音訊）
- 多語言混合（單一專案單一語言）
- 付費牆與計費（由其他系統處理）

---

## Migration Plan

### Phase 1: 專案與劇本基礎 (Week 1)

1. 建立 AudiobookProject 資料模型與 API
2. 實作劇本格式解析
3. 實作角色自動識別
4. 建立專案編輯頁面

### Phase 2: 角色與聲音設定 (Week 2)

1. 建立 Character 資料模型
2. 整合 008 聲音篩選 API
3. 實作聲音選擇器 UI
4. 實作單一台詞預覽

### Phase 3: 非同步生成 (Week 3)

1. 建立 AudiobookGenerationJob 資料模型
2. 實作分段生成 Worker
3. 實作進度追蹤 API
4. 實作音訊合併邏輯

### Phase 4: 背景音樂與匯出 (Week 4)

1. 實作背景音樂上傳
2. 實作混音功能
3. 實作匯出功能
4. 完成 UI 整合與測試

---

## Assumptions

- 使用者熟悉基本劇本格式（角色名：台詞）
- 008 功能的聲音資料庫已可用
- 007 功能的 JobWorker 架構已可用
- pydub 可處理所需的音訊操作
- 使用者上傳的背景音樂為合法使用

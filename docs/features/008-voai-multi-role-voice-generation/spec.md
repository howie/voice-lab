# Feature Specification: VoAI Multi-Role Voice Generation Enhancement

**Feature Branch**: `008-voai-multi-role-voice-generation`
**Created**: 2026-01-22
**Status**: Draft
**Input**: Analysis of missing features for native multi-role synthesis and voice metadata storage

---

## Problem Statement

目前 VoAI 多角色語音生成存在以下限制：

### 1. Native 多角色合成僅有 Placeholder

```python
# backend/src/application/use_cases/synthesize_multi_role.py:96-115
async def _synthesize_native(...) -> MultiRoleTTSResult:
    # For now, fall back to segmented mode
    # Native implementations for specific providers will be added later
    return await self._synthesize_segmented(input_data, voice_map)  # 直接 fallback!
```

- 能力註冊表宣稱 Azure/ElevenLabs/GCP 支援 Native，但實際都 fallback 到 Segmented
- 無 Azure SSML 多角色標籤實作
- 無 ElevenLabs Audio Tags `[S1][S2]` 語法實作
- 無 GCP SSML 多聲音支援

### 2. 聲音資料庫儲存機制未啟用

- `VoiceCache` 資料庫模型已定義但從未被使用
- 聲音查詢每次都直接呼叫 Provider API（無快取）
- 僅有 In-Memory Repository 實作
- 缺少 `age_group` 欄位供使用者篩選

### 3. 聲音同步機制不存在

- 無背景任務從各 Provider 拉取並同步聲音清單
- 聲音 metadata（性別、年齡、風格）未持久化
- Provider 新增聲音時無法自動更新

---

## Clarifications

### Session 2026-01-22

- Q: Native 多角色合成的優先實作順序？ → A: Azure SSML 最成熟，優先實作；其次 ElevenLabs Audio Tags
- Q: 聲音資料需要哪些 metadata？ → A: gender（性別）、age_group（年齡層）、language（語言）、style（風格）、use_case（用途）
- Q: 聲音同步頻率？ → A: 每日一次背景同步，或手動觸發
- Q: 是否需要支援使用者自訂聲音？ → A: 暫不需要，僅同步 Provider 提供的聲音
- Q: Azure SSML 字元限制閾值？ → A: 保守設定 50,000 字元（以 Unicode 字元數計算，1 個中文字 = 1 字元），超過則 fallback 到 segmented 模式
- Q: 聲音同步失敗時的重試策略？ → A: 指數退避重試最多 3 次（1s, 2s, 4s），之後記錄失敗並等待下次排程

---

## Gap Analysis: Current vs Required

### Native Multi-Role Synthesis

| Provider | 宣稱能力 | 實際實作 | 技術方案 | 優先級 |
|----------|---------|---------|---------|--------|
| Azure | Native | ❌ Placeholder | SSML `<voice>` 多角色標籤 | P1 |
| ElevenLabs | Native | ❌ Placeholder | Audio Tags `[dialogue][S1][S2]` | P2 |
| GCP | Native | ❌ Placeholder | SSML `<voice>` 標籤 | P3 |
| OpenAI | Segmented | ✅ 已實作 | 分段合成 + pydub 合併 | - |
| Cartesia | Segmented | ✅ 已實作 | 分段合成 + pydub 合併 | - |
| Deepgram | Segmented | ✅ 已實作 | 分段合成 + pydub 合併 | - |

### Voice Database Storage

| 功能 | 現狀 | 需求 | 優先級 |
|------|------|------|--------|
| VoiceCache DB Table | 已定義未使用 | 啟用並填充資料 | P1 |
| VoiceCacheRepository | 僅 In-Memory | 實作 DB-backed Repository | P1 |
| age_group 欄位 | ❌ 不存在 | 新增到 schema | P1 |
| style 欄位 | ❌ 不存在 | 新增到 schema | P2 |
| use_case 欄位 | ❌ 不存在 | 新增到 schema | P3 |
| sample_audio_url | 定義但未填充 | 從 Provider 同步 | P2 |

### Voice Synchronization

| 功能 | 現狀 | 需求 | 優先級 |
|------|------|------|--------|
| 背景同步任務 | ❌ 不存在 | 定時從 Provider 拉取聲音 | P1 |
| 手動觸發同步 | ❌ 不存在 | API endpoint 觸發同步 | P2 |
| 差異更新 | ❌ 不存在 | 只更新變更的聲音 | P3 |

---

## User Scenarios & Testing

### User Story 1 - Native 多角色語音合成 (Priority: P1)

使用者選擇支援 Native 多角色的 Provider（如 Azure）時，系統應使用 SSML 一次性合成多角色對話，而非分段合成再合併。

**Why this priority**: Native 合成可減少 API 呼叫次數、降低延遲、提升音訊品質（無合併接縫）。

**Independent Test**: 選擇 Azure Provider，輸入多角色對話，驗證系統使用 SSML 多聲音標籤一次完成合成。

**Acceptance Scenarios**:

1. **Given** 使用者選擇 Azure 作為 Provider，**When** 使用者提交「A: 你好 B: 嗨」的多角色對話，**Then** 系統使用 SSML `<voice>` 標籤一次性合成，而非多次呼叫 API。

2. **Given** Azure SSML 合成成功，**When** 使用者播放音訊，**Then** 角色之間無明顯的合併接縫或音量不一致。

3. **Given** 使用者選擇 ElevenLabs，**When** 使用者提交多角色對話，**Then** 系統使用 Audio Tags 語法 `[S1]...[S2]...` 一次性合成。

---

### User Story 2 - 依年齡層篩選聲音 (Priority: P1)

使用者想要為不同角色選擇適合的聲音年齡層（如兒童、青年、成人、長者），系統應提供年齡層篩選功能。

**Why this priority**: 多角色對話常需要不同年齡的聲音，缺少此功能會大幅降低使用體驗。

**Independent Test**: 在聲音選擇器中使用年齡層篩選，驗證結果正確。

**Acceptance Scenarios**:

1. **Given** 使用者在聲音選擇器中，**When** 使用者選擇「兒童」年齡層，**Then** 系統只顯示標記為兒童聲音的選項。

2. **Given** 聲音資料庫已同步，**When** 使用者查看聲音詳情，**Then** 顯示該聲音的年齡層資訊。

3. **Given** 使用者透過 API 查詢聲音，**When** 使用者帶入 `age_group=child` 參數，**Then** API 只返回兒童聲音。

---

### User Story 3 - 聲音資料庫同步 (Priority: P2)

系統定期從各 TTS Provider 同步最新的聲音清單，包含 metadata（性別、年齡、語言等），供使用者快速查詢。

**Why this priority**: 避免每次查詢都呼叫 Provider API，提升回應速度並減少 API 費用。

**Independent Test**: 觸發同步後，驗證資料庫中的聲音資料與 Provider 一致。

**Acceptance Scenarios**:

1. **Given** 系統啟動後，**When** 背景同步任務執行，**Then** 從所有啟用的 Provider 拉取聲音清單並儲存到資料庫。

2. **Given** 聲音已同步到資料庫，**When** 使用者查詢聲音列表，**Then** 系統從資料庫返回結果（不呼叫 Provider API）。

3. **Given** 管理員想要立即更新聲音清單，**When** 管理員呼叫手動同步 API，**Then** 系統立即執行同步並返回結果。

---

### User Story 4 - 依風格篩選聲音 (Priority: P3)

使用者想要選擇特定風格的聲音（如新聞播報、對話、歡快等）。

**Why this priority**: 進階功能，提升使用者體驗但非核心需求。

**Acceptance Scenarios**:

1. **Given** 使用者在聲音選擇器中，**When** 使用者選擇「新聞播報」風格，**Then** 系統顯示適合新聞播報的聲音。

---

### Edge Cases

- Provider API 不可用時，系統從快取返回聲音清單（標示為快取資料）
- 同步過程中遇到部分 Provider 失敗，以指數退避重試最多 3 次（1s, 2s, 4s），仍失敗則記錄錯誤並繼續同步其他 Provider
- 聲音被 Provider 移除時，標記為 deprecated 而非直接刪除（避免影響現有設定）
- Azure SSML 超過 50,000 字元限制時（以 Unicode 字元數計算，1 個中文字 = 1 字元，含 SSML 標籤），自動 fallback 到 segmented 模式
- ElevenLabs Audio Tags 不支援的特殊字元需要跳脫處理

---

## Requirements

### Functional Requirements

**Native Multi-Role Synthesis**

- **FR-001**: 系統 MUST 實作 Azure SSML 多角色合成，使用 `<voice>` 標籤在單一請求中合成多角色對話。
- **FR-002**: 系統 MUST 實作 ElevenLabs Audio Tags 多角色合成，使用 `[dialogue]` 和 `[Sn]` 語法。
- **FR-003**: 系統 SHOULD 實作 GCP SSML 多角色合成。
- **FR-004**: 系統 MUST 在 Native 合成失敗時自動 fallback 到 Segmented 模式。
- **FR-004a**: 系統 MUST 在 Azure SSML 內容超過 50,000 字元（Unicode 字元數，1 中文字 = 1 字元）時，自動切換至 Segmented 模式。
- **FR-005**: 系統 MUST 在合成結果中標示使用的合成模式（native/segmented）。

**Voice Database Storage**

- **FR-006**: 系統 MUST 實作 `VoiceCacheRepositoryImpl` 連接 PostgreSQL 資料庫。
- **FR-007**: 系統 MUST 在 `VoiceCache` 模型中新增 `age_group` 欄位，支援值：`child`、`young`、`adult`、`senior`。
- **FR-008**: 系統 SHOULD 在 `VoiceCache` 模型中新增 `styles` 欄位（JSON array）。
- **FR-009**: 系統 SHOULD 在 `VoiceCache` 模型中新增 `use_cases` 欄位（JSON array）。
- **FR-010**: 系統 MUST 在聲音查詢時優先從資料庫讀取，僅在快取過期時呼叫 Provider API。

**Voice Synchronization**

- **FR-011**: 系統 MUST 提供背景任務定期（每日）從各 Provider 同步聲音清單。
- **FR-012**: 系統 MUST 提供 API endpoint 供管理員手動觸發聲音同步。
- **FR-013**: 系統 MUST 在同步時保留聲音的 metadata（gender、age_group、language、styles）。
- **FR-014**: 系統 MUST 記錄每次同步的時間戳記和結果（成功/失敗、新增/更新/移除數量）。
- **FR-014a**: 系統 MUST 在單一 Provider 同步失敗時，以指數退避策略重試最多 3 次（間隔 1s, 2s, 4s），仍失敗則記錄錯誤並繼續處理其他 Provider。

**Voice API Enhancement**

- **FR-015**: `GET /api/v1/voices` MUST 支援 `age_group` 查詢參數。
- **FR-016**: `GET /api/v1/voices` SHOULD 支援 `style` 查詢參數。
- **FR-017**: 聲音詳情 API MUST 返回完整的 metadata（包含 age_group、styles、use_cases）。

---

### Key Entities

**VoiceCache (Enhanced)**
```python
class VoiceCache(Base):
    id: str                    # provider:voice_id
    provider: str              # azure, gcp, elevenlabs
    voice_id: str              # 原始 voice ID
    name: str                  # 顯示名稱
    language: str              # zh-TW, en-US
    gender: str | None         # male, female, neutral
    age_group: str | None      # child, young, adult, senior (NEW)
    styles: list[str]          # news, conversation, cheerful (NEW)
    use_cases: list[str]       # narration, assistant, character (NEW)
    sample_audio_url: str | None
    is_deprecated: bool        # 標記已移除的聲音 (NEW)
    metadata_: dict            # 額外 provider-specific 資料
    synced_at: datetime        # 最後同步時間 (NEW)
    updated_at: datetime
```

**VoiceSyncJob (New)**
```python
class VoiceSyncJob:
    id: UUID
    provider: str | None       # None = all providers
    status: str                # pending, running, completed, failed
    voices_added: int
    voices_updated: int
    voices_deprecated: int
    error_message: str | None
    started_at: datetime
    completed_at: datetime | None
```

**AzureSSMLBuilder (New)**
```python
class AzureSSMLBuilder:
    def build_multi_voice_ssml(
        turns: list[DialogueTurn],
        voice_assignments: dict[str, str],
        language: str
    ) -> str:
        """
        產生多角色 SSML：
        <speak version="1.0" xmlns="...">
            <voice name="zh-TW-HsiaoYuNeural">你好</voice>
            <voice name="zh-TW-YunJheNeural">嗨</voice>
        </speak>
        """
```

**ElevenLabsAudioTagsBuilder (New)**
```python
class ElevenLabsAudioTagsBuilder:
    def build_dialogue_text(
        turns: list[DialogueTurn],
        voice_assignments: dict[str, str]
    ) -> str:
        """
        產生 Audio Tags 格式：
        [dialogue]
        [S1] 你好
        [S2] 嗨
        """
```

---

## Success Criteria

### Measurable Outcomes

- **SC-001**: Azure Native 多角色合成的延遲比 Segmented 模式減少至少 30%。
- **SC-002**: 聲音查詢 API 的平均回應時間從 ~500ms（直接呼叫 Provider）降至 <50ms（從資料庫）。
- **SC-003**: 95% 的聲音資料包含正確的 age_group 標記。
- **SC-004**: 聲音同步任務每日成功執行，失敗率 <5%。
- **SC-005**: 使用者可在 10 秒內透過 age_group 篩選找到適合的聲音。

---

## Technical Design Notes

### Azure SSML Multi-Voice Structure

```xml
<speak version="1.0" xmlns="http://www.w3.org/2001/10/synthesis"
       xmlns:mstts="http://www.w3.org/2001/mstts" xml:lang="zh-TW">
    <voice name="zh-TW-HsiaoYuNeural">
        <prosody rate="0%" pitch="0%">你好，我是 A</prosody>
    </voice>
    <break time="300ms"/>
    <voice name="zh-TW-YunJheNeural">
        <prosody rate="0%" pitch="0%">嗨，我是 B</prosody>
    </voice>
</speak>
```

### ElevenLabs Audio Tags Structure

```
[dialogue]
[S1] 你好，我是 A
[S2] 嗨，我是 B
[S1] 今天天氣很好
```

需要在 API 請求中指定 voice mapping：
```json
{
  "text": "[dialogue]\n[S1] 你好\n[S2] 嗨",
  "voice_settings": {
    "dialogue_voices": {
      "S1": "voice_id_1",
      "S2": "voice_id_2"
    }
  }
}
```

### Voice Age Group Mapping

| Provider | 原始資料 | age_group 對應 |
|----------|---------|---------------|
| Azure | `VoiceStyleName` 含 "Child" | child |
| Azure | 預設 | adult |
| GCP | `naturalSampleRateHertz` + name pattern | 推斷 |
| ElevenLabs | `labels.age` | 直接對應 |

---

## Scope Boundaries

### In Scope

- Azure SSML 多角色合成實作
- ElevenLabs Audio Tags 多角色合成實作
- Voice 資料庫儲存與快取
- age_group 欄位與篩選功能
- 背景聲音同步任務
- 手動觸發同步 API

### Out of Scope

- GCP Native 多角色合成（P3，延後實作）
- 使用者自訂聲音上傳
- 即時聲音更新推播
- 聲音評分/收藏功能
- 多租戶聲音權限隔離

---

## Dependencies

- **005-multi-role-tts**: 現有的多角色 TTS 框架
- **007-async-job-mgmt**: 背景任務管理（用於聲音同步）
- **002-provider-mgmt-interface**: Provider API 金鑰管理

---

## Migration Plan

### Phase 1: Voice Database (Week 1)

1. 新增 `age_group`, `styles`, `use_cases`, `is_deprecated`, `synced_at` 欄位到 `VoiceCache`
2. 實作 `VoiceCacheRepositoryImpl` (DB-backed)
3. 建立 Alembic migration
4. 修改 Voice API 使用資料庫

### Phase 2: Voice Sync (Week 2)

1. 實作各 Provider 的聲音拉取邏輯
2. 實作 age_group 推斷邏輯
3. 建立背景同步任務（使用現有 JobWorker 架構）
4. 新增手動同步 API endpoint

### Phase 3: Native Synthesis (Week 3-4)

1. 實作 `AzureSSMLBuilder`
2. 修改 `_synthesize_native()` 呼叫 Azure SSML API
3. 實作 `ElevenLabsAudioTagsBuilder`
4. 新增 Native 合成的整合測試

---

## Assumptions

- Azure TTS API 支援單一請求中多個 `<voice>` 標籤
- ElevenLabs v3 API 支援 Audio Tags 多角色語法
- 各 Provider 的聲音清單 API 回應時間 <5 秒
- 聲音數量：Azure ~400、GCP ~300、ElevenLabs ~100，資料庫可容納

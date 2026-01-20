# Research: Multi-Role TTS

**Feature**: 005-multi-role-tts
**Date**: 2025-01-19
**Status**: Complete

## Overview

本研究整合 `docs/research/2025-voice-ai/04-1-tts-multiple-role.md` 和 `04-2-tts-long-podcast.md` 的發現，為多角色 TTS 功能實作提供技術決策依據。

## Research Topics

### 1. Provider Multi-Role Support Analysis

**Decision**: 採用三層支援策略

| Provider | 支援類型 | 實作方式 |
|----------|---------|---------|
| ElevenLabs | Native (v3 Audio Tags) | 單一請求，使用 `[dialogue][S1][S2]` 語法 |
| Azure | Native (SSML) | 單一請求，使用 `<voice>` 元素切換 |
| Google Cloud | Native (SSML) | 單一請求，使用 `<voice>` 標籤 |
| OpenAI | Segmented | 分段生成 + pydub 合併 |
| Cartesia | Segmented | 分段生成 + pydub 合併 |
| Deepgram | Segmented | 分段生成 + pydub 合併 |

**Rationale**:
- ElevenLabs v3 和 Azure SSML 提供最佳原生體驗
- 分段合併策略可統一處理不支援原生多角色的 Provider
- 使用者可選擇是否接受分段合併方式

**Alternatives considered**:
- 僅支援原生多角色 Provider → 拒絕：限制使用者選擇
- 全部使用分段合併 → 拒絕：浪費原生支援的效能優勢

### 2. Dialogue Parsing Strategy

**Decision**: 使用正則表達式解析兩種格式

支援格式：
```
格式 1: A: 文字內容
格式 2: [A] 文字內容
格式 3: [Speaker Name]: 文字內容
```

**解析規則**:
```python
pattern = r'(?:\[([^\]]+)\]|([A-Z]))\s*[:：]\s*(.+?)(?=(?:\[[^\]]+\]|[A-Z])[:：]|$)'
```

**Rationale**:
- 涵蓋常見對話逐字稿格式
- 支援中英文冒號（`:` 和 `：`）
- 允許自訂說話者名稱（如 `[主持人]`）

**Alternatives considered**:
- JSON 結構化輸入 → 拒絕：使用者體驗差
- 只支援單一格式 → 拒絕：彈性不足

### 3. Audio Merging Strategy

**Decision**: 使用 pydub 進行音訊合併

**技術細節**:
- 預設段落間隔：300ms
- 可選交叉淡入淡出：50ms
- 音量正規化：-20 dBFS
- 輸出格式：MP3 192kbps

**Rationale**:
- pydub 是 Python 音訊處理的業界標準
- 提供簡潔 API 進行音訊串接和處理
- 支援多種輸入/輸出格式

**Alternatives considered**:
- ffmpeg 直接呼叫 → 拒絕：API 不夠友善
- 不處理間隔 → 拒絕：聲音切換會不自然

### 4. Character Limit Handling

**Decision**: 動態字元限制策略

| Provider | 單次上限 | 建議上限 |
|----------|---------|---------|
| ElevenLabs | 5,000 | 5,000 |
| Azure | 10,000 | 5,000 |
| Google Cloud | 5,000 | 5,000 |
| OpenAI | 4,096 | 4,000 |
| Cartesia | 無明確限制 | 3,000 |
| Deepgram | 2,000 | 2,000 |

**實作方式**:
1. 前端依選擇的 Provider 動態調整上限
2. 接近上限 80% 時顯示警告
3. 超過上限時阻止提交並提示

**Rationale**:
- 避免因超過限制導致 API 錯誤
- 提供即時回饋改善使用者體驗

### 5. ElevenLabs v3 Audio Tags Implementation

**Decision**: 優先使用 v3 Audio Tags 語法

**格式轉換**:
```
用戶輸入:
A: 你好
B: 嗨

轉換為 ElevenLabs v3:
[dialogue]
[S1] 你好
[S2] 嗨
[/dialogue]
```

**進階功能** (未來可擴展):
- `[interrupting]` - 打斷效果
- `[overlapping]` - 重疊說話
- `[laughs]` - 笑聲

**Rationale**:
- v3 Audio Tags 是 ElevenLabs 推薦的多角色對話方式
- 單一請求即可完成，減少 API 呼叫次數

### 6. Azure SSML Multi-Voice Implementation

**Decision**: 使用標準 SSML `<voice>` 元素

**格式轉換**:
```xml
<speak version="1.0" xmlns="http://www.w3.org/2001/10/synthesis"
       xmlns:mstts="http://www.w3.org/2001/mstts" xml:lang="zh-TW">
    <voice name="zh-TW-HsiaoChenNeural">
        你好
    </voice>
    <voice name="zh-TW-YunJheNeural">
        嗨
    </voice>
</speak>
```

**Rationale**:
- SSML 是 W3C 標準，Azure 完整支援
- 可搭配 `<mstts:express-as>` 調整情感風格

## Frontend Architecture Decisions

### State Management

**Decision**: 使用 Zustand 建立獨立 store

**狀態結構**:
```typescript
interface MultiRoleTTSState {
  // Input
  dialogueText: string
  provider: string
  parsedTurns: DialogueTurn[]
  voiceAssignments: Record<string, string>

  // Provider info
  providerCapability: 'native' | 'segmented' | 'unsupported'
  characterLimit: number

  // Output
  result: MultiRoleTTSResult | null
  isLoading: boolean
  error: string | null
}
```

**Rationale**:
- 與現有 ttsStore 分離，避免互相干擾
- 清晰的狀態邊界有助測試

### Component Structure

**Decision**: 三個主要元件

1. `DialogueInput` - 對話輸入區域
   - 即時解析說話者
   - 顯示字元計數和警告

2. `SpeakerVoiceTable` - 說話者語音對應表
   - 動態顯示解析出的說話者
   - 為每位說話者提供語音選擇器

3. `ProviderCapabilityCard` - Provider 能力卡片
   - 顯示原生支援/分段合併/不支援狀態
   - 列出進階功能（如 Audio Tags）

## Backend Architecture Decisions

### Interface Extension

**Decision**: 新增 `IMultiRoleTTSProvider` 介面

```python
class IMultiRoleTTSProvider(ABC):
    @property
    @abstractmethod
    def multi_role_support(self) -> MultiRoleSupportType:
        """Return native, segmented, or unsupported."""
        pass

    @abstractmethod
    async def synthesize_multi_role(
        self,
        turns: list[DialogueTurn],
        voice_map: dict[str, str]
    ) -> TTSResult:
        """Synthesize multi-role dialogue."""
        pass
```

**Rationale**:
- 保持與現有 ITTSProvider 的向後相容
- 明確區分單角色和多角色功能

### Segmented Merger Service

**Decision**: 建立通用合併服務

```python
class SegmentedMergerService:
    async def synthesize_and_merge(
        self,
        provider: ITTSProvider,
        turns: list[DialogueTurn],
        voice_map: dict[str, str],
        gap_ms: int = 300
    ) -> TTSResult:
        """Generate segments and merge into single audio."""
        pass
```

**Rationale**:
- 統一處理所有不支援原生多角色的 Provider
- 可重用於未來新增的 Provider

## Security Considerations

1. **輸入驗證**: 對話文字需過濾潛在的注入攻擊（特別是 SSML）
2. **字元限制**: 嚴格執行以防止資源濫用
3. **API 金鑰**: 沿用現有的安全儲存機制

## Performance Considerations

1. **原生支援優先**: 減少 API 呼叫次數和合併處理時間
2. **並行生成**: 分段合併時可並行呼叫各段 TTS
3. **快取語音清單**: 減少重複載入

## Summary of Decisions

| Topic | Decision | Impact |
|-------|----------|--------|
| Provider 支援策略 | 三層：Native/Segmented/Unsupported | 高 - 核心架構 |
| 對話解析 | 正則表達式支援兩種格式 | 中 - 使用者體驗 |
| 音訊合併 | pydub + 300ms 間隔 | 中 - 輸出品質 |
| 字元限制 | 動態調整 + 警告 | 低 - 錯誤預防 |
| 狀態管理 | 獨立 Zustand store | 中 - 程式碼組織 |
| 後端介面 | 新增 IMultiRoleTTSProvider | 高 - 架構擴展性 |

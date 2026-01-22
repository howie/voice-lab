# Research: VoAI Multi-Role Voice Generation Enhancement

**Date**: 2026-01-22
**Feature**: 008-voai-multi-role-voice-generation

---

## 1. Azure SSML Multi-Voice Synthesis

### Decision
使用 Azure Speech Service 的 SSML multi-voice 功能實作 Native 多角色合成。

### Rationale
- Azure 官方文件確認支援單一 SSML 請求中包含多個 `<voice>` 標籤
- 現有 voice-lab 能力註冊表已宣告 Azure 支援 NATIVE 模式（最多 10 speakers）
- 基礎 SSML 建構功能已存在於 `azure_tts.py`

### Technical Details

**字元限制**：
| API 模式 | 限制 | 說明 |
|----------|------|------|
| Real-time (WebSocket) | **64 KB** | 最大 SSML 訊息大小 |
| Batch Synthesis API | 2 MB | JSON payload 大小 |
| Max voice/audio tags | 50 tags | 適用於 Free 和 Standard 層級 |

> **重要更新**：規格中的 50,000 字元限制需調整。Azure 官方 WebSocket 限制為 **64 KB (≈65,536 bytes)**。考慮到 SSML 標籤開銷，建議保守設定為 **50,000 Unicode 字元**（約 150 KB UTF-8），但實際應檢查 bytes 而非字元數。

**SSML 結構**：
```xml
<speak version="1.0"
       xmlns="http://www.w3.org/2001/10/synthesis"
       xmlns:mstts="https://www.w3.org/2001/mstts"
       xml:lang="zh-TW">
    <voice name="zh-TW-HsiaoYuNeural">
        <prosody rate="0%" pitch="0%">你好，我是 A</prosody>
    </voice>
    <break time="300ms"/>
    <voice name="zh-TW-YunJheNeural">
        <prosody rate="0%" pitch="0%">嗨，我是 B</prosody>
    </voice>
</speak>
```

**XML 特殊字元跳脫**：
- `&` → `&amp;`
- `<` → `&lt;`
- `>` → `&gt;`
- `"` → `&quot;`
- `'` → `&apos;`

### Constraints
- 每個 SSML 最多 50 個 voice/audio tags
- 最多 10 個 speakers（依能力註冊表）
- 音訊輸出最長 10 分鐘
- User-Agent header 須少於 255 字元

### Alternatives Considered
1. **Batch Synthesis API**：雖然限制較寬鬆（2 MB），但為非同步 API，不適合即時場景
2. **個別請求 + pydub 合併**：目前 fallback 做法，延遲較高且有接縫問題

### Source
- [Azure Speech Service SSML Voice and Sound Guide](https://learn.microsoft.com/en-us/azure/ai-services/speech-service/speech-synthesis-markup-voice)
- [Speech Synthesis Markup Language Overview](https://learn.microsoft.com/en-us/azure/ai-services/speech-service/speech-synthesis-markup)
- [Azure Speech Service Quotas and Limits](https://learn.microsoft.com/en-us/azure/ai-services/speech-service/speech-services-quotas-and-limits)

---

## 2. ElevenLabs Text to Dialogue API

### Decision
使用 ElevenLabs 的 **Text to Dialogue API** (`/v1/text-to-dialogue`) 實作 Native 多角色合成，而非原先假設的 `[S1][S2]` Audio Tags 語法。

### Rationale
- ElevenLabs 官方文件確認支援多 speaker 對話合成
- 使用 `eleven_v3` 模型支援 Audio Tags（情感、表達控制）
- 每個 speaker 由 `voice_id` 識別，無需特殊標籤語法

### Technical Details

**API Endpoint**：`POST /v1/text-to-dialogue`

**重要發現**：ElevenLabs 不使用 `[S1]`、`[S2]` 語法！Speaker 是透過 voice_id 在 dialogue array 中指定。

**Request 結構**：
```json
{
  "model_id": "eleven_v3",
  "inputs": [
    {
      "text": "[excited] 你好！",
      "voice_id": "voice_id_A"
    },
    {
      "text": "[friendly] 嗨！",
      "voice_id": "voice_id_B"
    }
  ],
  "settings": {
    "stability": 0.5
  }
}
```

**Audio Tags（情感/表達控制）**：
- 情感：`[sad]`, `[angry]`, `[happily]`, `[excited]`, `[sorrowful]`
- 表達：`[whispers]`, `[shouts]`, `[stuttering]`, `[rushing]`
- 人聲反應：`[laughs]`, `[giggles]`, `[clears throat]`, `[sighs]`
- 對話流程：`[interrupting]`, `[overlapping]`, `[hesitates]`, `[pause]`
- 音效：`[applause]`, `[leaves rustling]`
- 口音：`[strong French accent]`

### Constraints
- **字元限制**：每個請求最多 5,000 字元（所有 speaker 合計）
- **模型要求**：必須使用 `eleven_v3` 模型
- **Pronunciation Dictionaries**：每個請求最多 3 個
- **特殊字元**：非文字字元如 `{`, `}`, `[`, `]`（非 tag 用途）會導致低品質輸出
- **Tag 大小寫**：不區分大小寫（`[WHISPER]` = `[whisper]`）
- **Voice 相容性**：不同 voice 對 tag 的響應程度不同

### Alternatives Considered
1. **原假設的 `[dialogue][S1][S2]` 語法**：經研究確認此語法不存在，需更新規格
2. **個別請求 + pydub 合併**：目前 fallback 做法

### Source
- [Eleven v3 Audio Tags: Multi-Character Dialogue](https://elevenlabs.io/blog/eleven-v3-audio-tags-bringing-multi-character-dialogue-to-life)
- [Text to Dialogue | ElevenLabs Documentation](https://elevenlabs.io/docs/overview/capabilities/text-to-dialogue)
- [Create dialogue API Reference](https://elevenlabs.io/docs/api-reference/text-to-dialogue/convert)
- [Text to Dialogue quickstart](https://elevenlabs.io/docs/developers/guides/cookbooks/text-to-dialogue)

---

## 3. Voice Metadata Synchronization

### Decision
使用現有 JobWorker 架構建立背景同步任務，定期從各 Provider 拉取聲音清單。

### Rationale
- 007-async-job-mgmt 已建立完整的背景任務框架
- 避免每次查詢都呼叫 Provider API，減少延遲和費用
- 集中管理聲音 metadata，支援跨 Provider 搜尋

### Technical Details

**同步策略**：
- 頻率：每日一次（排程），支援手動觸發
- 重試：指數退避最多 3 次（1s, 2s, 4s）
- 差異更新：比對 voice_id，只更新變更項目
- 移除處理：標記為 `is_deprecated`，不直接刪除

**Age Group 推斷邏輯**：
| Provider | 原始資料 | age_group 對應 |
|----------|---------|---------------|
| Azure | `VoiceStyleName` 含 "Child" | `child` |
| Azure | 預設 | `adult` |
| GCP | name pattern + `naturalSampleRateHertz` | 推斷 |
| ElevenLabs | `labels.age` | 直接對應 |

### Constraints
- 各 Provider API 回應時間假設 <5 秒
- 聲音數量：Azure ~400, GCP ~300, ElevenLabs ~100
- 同步任務應在非尖峰時段執行

### Alternatives Considered
1. **即時 API 呼叫 + 短期快取**：延遲較高，API 費用較高
2. **WebSocket 推播更新**：過於複雜，Provider 不支援

---

## 4. Spec Updates Required

基於研究發現，以下規格項目需更新：

### 4.1 ElevenLabs 語法修正
- **原規格**：使用 `[dialogue][S1][S2]` 語法
- **實際**：使用 Text to Dialogue API，speaker 由 `voice_id` 在 array 中指定
- **影響**：`ElevenLabsAudioTagsBuilder` 需重新設計為 `ElevenLabsDialogueBuilder`

### 4.2 字元限制說明
- **Azure**：64 KB (bytes)，建議以 bytes 計算而非字元數
- **ElevenLabs**：5,000 字元（所有 speaker 合計）
- **影響**：需分別處理兩個 Provider 的限制

### 4.3 API 參數更新
```json
// ElevenLabs 正確格式
{
  "model_id": "eleven_v3",
  "inputs": [
    {"text": "內容", "voice_id": "voice_id"}
  ]
}
```

---

## Summary

| 項目 | 研究結果 | 影響 |
|------|---------|------|
| Azure Multi-Voice | ✅ 確認支援 | 需實作 `AzureSSMLBuilder`，注意 64 KB 限制 |
| ElevenLabs Dialogue | ✅ 確認支援（語法不同） | 需實作 `ElevenLabsDialogueBuilder`（非 AudioTagsBuilder） |
| 字元限制 | Azure: 64 KB, ElevenLabs: 5,000 chars | 需分別處理 |
| 背景同步 | 使用現有 JobWorker | 無額外依賴 |

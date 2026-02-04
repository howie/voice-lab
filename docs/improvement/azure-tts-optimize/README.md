# Azure TTS 優化計畫

## 1. 語速修正（已完成）

### 問題

`azure_tts.py` 的 `_build_ssml` 將 speed 轉為百分比時使用絕對格式，
Azure SSML `<prosody rate>` 把百分比當成**相對變化量**，導致語速異常。

| speed 值 | 修正前 | Azure 解讀 | 修正後 | Azure 解讀 |
|----------|--------|-----------|--------|-----------|
| 1.0（正常）| `"100%"` | 快 100% = 兩倍速 | `"+0%"` | 正常速度 |
| 1.5 | `"150%"` | 快 150% = 2.5 倍速 | `"+50%"` | 快 50% |
| 0.5 | `"50%"` | 快 50% | `"-50%"` | 慢 50% |

### 已修改檔案

- `backend/src/infrastructure/providers/tts/azure_tts.py` — speed 轉為相對百分比
- `backend/src/infrastructure/providers/tts/multi_role/azure_ssml_builder.py` — 預設 rate `"0%"` → `"+0%"`

---

## 2. 多角色 TTS Azure 格式範例（已完成）

### 問題

選擇 Azure 作為多角色 TTS provider 時，UI 沒有顯示 Azure 專屬的格式範例。
Gemini 和 ElevenLabs 都有各自的指引區塊，Azure 缺失。

### 已修改檔案

- `frontend/src/components/multi-role-tts/DialogueInput.tsx` — 新增 Azure 格式指引區塊（天藍色），顯示輸入範例和 SSML 結構
- `frontend/src/components/multi-role-tts/ProviderCapabilityCard.tsx` — 新增 `AZURE_FEATURES` tooltip 描述

---

## 3. Azure Express-As 語氣選擇功能（待實作）

### 目標

讓使用者在多角色 TTS 選擇 Azure 時，可為每位說話者選擇語氣風格（cheerful、sad、angry 等），
透過 Azure SSML `<mstts:express-as>` 元素實現。

### 現有基礎

- `VoiceProfile` 後端已有 `styles: tuple[str, ...]` 欄位（`voice.py:37`）
- 前端 `VoiceProfile` 已有 `supported_styles?: string[]`（`api.ts:83`）
- Azure SDK voice 物件有 `style_list` 屬性
- **缺口**：`azure_tts.py` 的 `list_voices` 沒有填入 `styles`，前端拿不到資料

### UI 設計

SpeakerVoiceTable 在 provider=azure 時，擴充為四欄：

```
┌──────────┬──────────────┬─────────┬───────┐
│ 說話者    │ 語音          │ 語氣     │ 強度  │
├──────────┼──────────────┼─────────┼───────┤
│ (A)  A   │ ▾ HsiaoChen  │ ▾ 開心   │ ━●━━  │
│ (B)  B   │ ▾ YunJhe     │ ▾ 冷靜   │ ━━●━  │
└──────────┴──────────────┴─────────┴───────┘
```

規則：
- 「語氣」「強度」欄位只在 provider=azure 時顯示
- 語氣下拉選項 = 選定語音的 `supported_styles`
- 沒有 styles 的語音不顯示語氣欄
- 強度 slider：0.01–2.0（預設 1.0）

### 資料流

```
目前：
  VoiceAssignment { speaker, voiceId, voiceName }
  → voice_map: { "A": "zh-TW-HsiaoChenNeural" }
  → SSML: <voice> → <prosody> → text

改動後：
  VoiceAssignment { speaker, voiceId, voiceName, style?, styleDegree? }
  → voice_map:  { "A": "zh-TW-HsiaoChenNeural" }
  → style_map:  { "A": { style: "cheerful", degree: 1.5 } }
  → SSML: <voice> → <mstts:express-as> → <prosody> → text
```

### 產生的 SSML 結構

無語氣設定時（向下相容）：

```xml
<voice name="zh-TW-HsiaoChenNeural">
  <prosody rate="+0%" pitch="+0Hz">
    太好了，歡迎大家！
  </prosody>
</voice>
```

有語氣設定時：

```xml
<voice name="zh-TW-HsiaoChenNeural">
  <mstts:express-as style="cheerful" styledegree="1.5">
    <prosody rate="+0%" pitch="+0Hz">
      太好了，歡迎大家！
    </prosody>
  </mstts:express-as>
</voice>
```

### 改動清單

| # | 檔案 | 改動內容 |
|---|------|---------|
| 1 | `backend/src/infrastructure/providers/tts/azure_tts.py` | `list_voices` 讀取 `voice.style_list` 填入 `VoiceProfile.styles` |
| 2 | `backend/src/domain/entities/multi_role_tts.py` | `VoiceAssignment` 加 `style: str \| None`, `style_degree: float \| None` |
| 3 | `backend/src/presentation/api/routes/multi_role_tts.py` | `VoiceAssignmentRequest` schema 加 `style`, `style_degree` 欄位 |
| 4 | `backend/src/infrastructure/providers/tts/multi_role/azure_ssml_builder.py` | 接收 style_map 參數，產生 `<mstts:express-as>` 標籤 |
| 5 | `backend/src/application/use_cases/synthesize_multi_role.py` | 從 voice_assignments 建構 style_map 傳給 builder |
| 6 | `frontend/src/types/multi-role-tts.ts` | `VoiceAssignment` 加 `style?: string`, `styleDegree?: number` |
| 7 | `frontend/src/components/multi-role-tts/SpeakerVoiceTable.tsx` | 加「語氣」下拉和「強度」slider 欄位（azure only） |
| 8 | `frontend/src/stores/multiRoleTTSStore.ts` | `setVoiceAssignment` 傳遞 style 和 styleDegree |

### 注意事項

- **不是所有 Azure 語音都支援 styles** — `style_list` 為空的語音不顯示語氣欄位
- **Per-speaker 設計** — 每位說話者整段對話維持同一語氣，比 per-turn 簡單且符合多數使用情境
- **向下相容** — style 和 styleDegree 都是 optional，不傳時行為與現有完全一致
- **Azure 文件參考** — [SSML Voice and Sound](https://learn.microsoft.com/en-us/azure/ai-services/speech-service/speech-synthesis-markup-voice)

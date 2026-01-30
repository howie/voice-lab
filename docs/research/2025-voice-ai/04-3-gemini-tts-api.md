# Gemini TTS API 語音調教研究

> 最後更新：2026-01-30

## 概述

本文件深入研究 Google Gemini TTS API 的語音控制機制。與傳統 TTS（如 Azure、ElevenLabs）不同，Gemini TTS **不使用離散參數**（如 speed=1.2, pitch=+5）來控制語音風格，而是透過**自然語言指令 (Style Prompt)**、**SSML 標記**和**行內情緒標籤**三種方式進行調教。

### 兩種 API 介面

| 介面 | Endpoint | 特點 |
|------|----------|------|
| **Gemini API** (本專案使用) | `generativelanguage.googleapis.com/v1beta/models/{model}:generateContent` | Style prompt 寫在 text 中 |
| **Cloud TTS API** | `texttospeech.googleapis.com/v1/text:synthesize` | 有獨立的 `input.prompt` 欄位 |

### 可用模型

| Model ID | 用途 | 狀態 |
|----------|------|------|
| `gemini-2.5-pro-tts` | 最高品質，風格指令遵循度最佳 | GA |
| `gemini-2.5-flash-tts` | 低延遲，性價比高 | GA |
| `gemini-2.5-flash-lite-preview-tts` | 最輕量，速度最快 | Preview |

---

## 1. 自然語言 Style Prompt（主要控制方式）

Gemini TTS 的核心特色是用**自然語言描述**控制語音風格，而非數值參數。

### 1.1 基本格式

**Gemini API（本專案）**: 將 style prompt 前置於文字內容：

```
{style_prompt}: {text}
```

```python
# 本專案 gemini_tts.py 的做法 (line 98-99)
if style_prompt:
    text = f"{style_prompt}: {text}"
```

**Cloud TTS API**: 使用獨立的 `input.prompt` 欄位：

```json
{
  "input": {
    "text": "今天天氣真好，要不要出去走走？",
    "prompt": "用溫暖友善的語氣說以下的話"
  }
}
```

> **注意**: Cloud TTS API 的 `input.text` 上限 4,000 bytes，`input.prompt` 上限 4,000 bytes，兩者合計上限 8,000 bytes。

### 1.2 Google 推薦的「電影導演」結構化 Prompt

Google 官方建議用電影導演的思維來構建 prompt，包含以下要素：

| 要素 | 說明 | 範例 |
|------|------|------|
| **Audio Profile** | 角色核心身份與聲音特質 | 「你是一位 50 歲、經驗豐富的自然紀錄片旁白」 |
| **Scene** | 環境氛圍與情緒基調 | 「你正站在黎明時分寧靜的森林邊緣」 |
| **Director's Notes** | 具體表演指導 | 「用輕柔的英式口音，句間略作停頓以加強效果」 |
| **Sample Context** | 前情提要 | 「這是旁白開場的第一段話」 |
| **Transcript** | 實際要說的文字 | （實際文本內容） |

### 1.3 常用 Style Prompt 範例

#### 語氣控制

```
# 情緒
Say this cheerfully with excitement: {text}
用悲傷的語氣說: {text}
Speak with a sarcastic tone: {text}
用溫柔安慰的口吻說: {text}

# 專業場景
Use a professional news anchor tone: {text}
用播客主持人輕鬆聊天的語氣: {text}
Narrate this like a nature documentary: {text}
像老師在課堂上耐心講解一樣: {text}

# 語速
Say the following very fast but still be intelligible: {text}
Speak slowly and calmly, with deliberate pauses: {text}
用正常偏慢的語速，清晰地朗讀: {text}

# 複合指令
You are a storyteller for a mystery novel. Start with a nervous tone
that accelerates into excitement and relief: {text}
```

#### 中文場景推薦 prompt

```
# 客服
你是一位親切有耐心的客服人員，用溫和專業的語氣說: {text}

# 新聞播報
你是一位專業的新聞主播，用穩重清晰的播報語氣說: {text}

# 故事朗讀
你是一位說故事的人，用生動活潑的語氣，適當加入情緒起伏: {text}

# 教學
你是一位溫和的老師，用清楚且有條理的語氣講解: {text}

# 廣告旁白
用充滿活力和熱情的語氣，像電視廣告旁白一樣: {text}
```

### 1.4 Style Prompt 最佳實踐

1. **Pro 模型對 style prompt 的遵循度明顯優於 Flash** — 需要精確風格控制時優先使用 Pro
2. **英文 prompt 效果通常比中文好** — 模型對英文指令理解更精確
3. **具體描述優於抽象形容** — 「像老師在課堂上講解」比「用教學語氣」更有效
4. **避免過長的 prompt** — 簡短明確的指令比冗長複雜的描述效果更好
5. **聲音選擇與 prompt 搭配** — 選擇基調接近目標風格的聲音，再用 prompt 微調

---

## 2. SSML 標記支援

Gemini TTS 支援部分 SSML 標籤，可與 style prompt 混合使用。

### 2.1 支援的標籤

| 標籤 | 用途 | 範例 |
|------|------|------|
| `<prosody>` | 語速、音高、音量 | `<prosody rate="slow" pitch="+2st">你好</prosody>` |
| `<break>` | 插入停頓 | `<break time="2s"/>` |
| `<emphasis>` | 強調字詞 | `<emphasis level="strong">重點</emphasis>` |
| `<say-as>` | 讀法控制 | `<say-as interpret-as="date">2026-01-30</say-as>` |
| `<sub>` | 替代發音 | `<sub alias="人工智慧">AI</sub>` |
| `<s>` | 句子邊界 | `<s>這是一個句子。</s>` |
| `<par>` | 並行音訊 | 多音訊元素同時播放 |
| `<seq>` | 序列音訊 | 多音訊元素依序播放 |

### 2.2 `<prosody>` 屬性值

**rate（語速）:**
- 描述詞: `"x-slow"`, `"slow"`, `"medium"`, `"fast"`, `"x-fast"`
- 百分比: `"125%"`, `"75%"`

**pitch（音高）:**
- 半音: `"+2st"`, `"-3st"`
- 描述詞: `"x-low"`, `"low"`, `"medium"`, `"high"`, `"x-high"`

**volume（音量）:**
- 描述詞: `"silent"`, `"x-soft"`, `"soft"`, `"medium"`, `"loud"`, `"x-loud"`
- 分貝: `"+6dB"`, `"-3dB"`

### 2.3 SSML 使用範例

```xml
<!-- 基本語速控制 -->
<prosody rate="slow">慢慢地說這段話。</prosody>

<!-- 組合使用 -->
<prosody rate="fast" pitch="+2st">興奮地加快語速！</prosody>

<!-- 插入停頓 -->
今天的重點是<break time="1s"/>人工智慧的未來發展。

<!-- 強調 + 停頓 -->
這個功能<emphasis level="strong">非常重要</emphasis>，<break time="500ms"/>請大家注意。

<!-- 日期讀法 -->
活動日期是 <say-as interpret-as="date">2026-01-30</say-as>。

<!-- 替代發音 -->
<sub alias="每秒影格數">FPS</sub> 是衡量流暢度的指標。
```

### 2.4 SSML 注意事項

- **Pro 模型** 對 SSML 的處理明顯優於 Flash
- `<say-as>` 能正確處理字元、數字、日期、時間，但**貨幣、電話號碼格式可能失敗**
- 長篇且包含大量 SSML 標籤的文本，模型偶爾會**將標籤本身讀出來**而非解讀 — 解決方案是將文本切成較小片段
- **不支援** `<audio>` 標籤（插入外部音檔）

---

## 3. 行內情緒 / 動作標籤

Gemini TTS 支援用方括號 `[tag]` 在文本中標記局部的情緒或動作。

### 3.1 支援的標籤

```
[sigh] 唉，算了吧。
[chuckling] 哈，這太有趣了。
[coughs] 不好意思。
[laughing] 你不是認真的吧！
[whispering] 不要告訴別人...
[sad] 我好想念那些日子。
[excited] 這太棒了！
```

### 3.2 停頓標籤

```
# 方括號停頓（SSML <break> 的替代寫法）
[PAUSE=2s] 效果等同 <break time="2s"/>
```

### 3.3 混合使用

行內標籤可以與 SSML 和 style prompt 混合：

```
# Style Prompt + 行內標籤
用故事朗讀的語氣: [whispering] 很久很久以前 [PAUSE=1s] 有一座魔法森林...

# 行內標籤 + SSML
[sad] <break time="1s"/> 我想一切都結束了。
```

### 3.4 使用建議

- 行內標籤適合**局部、瞬間的情緒/動作**（嘆氣、笑、咳嗽）
- 整體語調用 **style prompt** 控制更有效
- 兩者結合可實現「整體語調穩定 + 局部情緒變化」的效果

---

## 4. 聲音選擇（30 個預建聲音）

所有 30 個聲音支援 **24 種語言、80+ 個地區語言變體**。模型會自動偵測輸入語言。

### 4.1 聲音列表與特性

| 聲音名稱 | 特質描述 | 建議場景 |
|----------|----------|----------|
| **Achernar** | 柔和溫柔 | 睡前故事、ASMR |
| **Achird** | 友善親切 | 客服、助理 |
| **Algenib** | 粗獷質感 | 角色扮演、旁白 |
| **Algieba** | 平滑悅耳 | 有聲書、冥想 |
| **Alnilam** | 堅定有力 | 演講、激勵 |
| **Aoede** | 旋律優雅 | 文學朗讀 |
| **Autonoe** | 明亮樂觀 | 廣告、品牌 |
| **Callirrhoe** | 輕鬆自在 | 播客、閒聊 |
| **Charon** | 資訊清晰 | 新聞播報、教學 |
| **Despina** | 流暢平滑 | 旁白、導覽 |
| **Enceladus** | 氣聲柔軟 | 冥想、ASMR |
| **Erinome** | 清晰精確 | 專業報告 |
| **Fenrir** | 興奮活潑 | 遊戲、娛樂 |
| **Gacrux** | 成熟穩重 | 紀錄片、財經 |
| **Iapetus** | 清楚流利 | 教學、說明 |
| **Kore** | 堅定自信 | 企業、品牌（中文佳） |
| **Laomedeia** | 開朗活潑 | 兒童內容、娛樂 |
| **Leda** | 年輕有活力 | 社群、短影片 |
| **Orus** | 堅定果斷 | 決策、指揮 |
| **Puck** | 活潑有勁（預設聲音） | 通用 |
| **Pulcherrima** | 前衛表達力強 | 藝術、創意 |
| **Rasalgethi** | 資訊專業 | 企業報告 |
| **Sadachbia** | 生動有趣 | 動畫、兒童 |
| **Sadaltager** | 知識權威 | 學術、專業 |
| **Schedar** | 關懷支持 | 醫療、諮詢 |
| **Sulafat** | 溫暖歡迎 | 接待、引導 |
| **Umbriel** | 神秘引人 | 懸疑、故事 |
| **Vindemiatrix** | 溫柔善良 | 療癒、陪伴 |
| **Zephyr** | 明亮歡快 | 生活風格 |
| **Zubenelgenubi** | 平衡中性 | 通用 |

> **本專案預設聲音**: Kore（`config.py` 中 `gemini_tts_default_voice`），適合中文場景。

### 4.2 聲音 + Style Prompt 搭配建議

```
# 搭配原則：選基調接近的聲音，用 prompt 微調
Kore + "用溫和但專業的語氣"     → 企業客服
Charon + "用嚴肅的新聞播報語氣" → 新聞播報
Fenrir + "用充滿活力的語氣"     → 廣告旁白
Schedar + "用關心的語氣輕聲說"   → 醫療提醒
Umbriel + "用低沉神秘的語氣"     → 懸疑有聲書
```

---

## 5. 多角色對話 (Multi-Speaker)

Gemini TTS 原生支援最多 **2 位說話者** 的多角色對話。

### 5.1 Gemini API 多角色格式

```python
from google import genai
from google.genai import types

client = genai.Client(api_key="GEMINI_API_KEY")

response = client.models.generate_content(
    model="gemini-2.5-flash-preview-tts",
    contents="""
    小明: 你有試過新的多角色功能嗎？
    小華: 有啊！我超興奮的。
    小明: 我也是！聽起來好自然。
    """,
    config=types.GenerateContentConfig(
        response_modalities=["AUDIO"],
        speech_config=types.SpeechConfig(
            multi_speaker_voice_config=types.MultiSpeakerVoiceConfig(
                speaker_voice_configs=[
                    types.SpeakerVoiceConfig(
                        speaker="小明",
                        voice_config=types.VoiceConfig(
                            prebuilt_voice_config=types.PrebuiltVoiceConfig(
                                voice_name="Charon"
                            )
                        ),
                    ),
                    types.SpeakerVoiceConfig(
                        speaker="小華",
                        voice_config=types.VoiceConfig(
                            prebuilt_voice_config=types.PrebuiltVoiceConfig(
                                voice_name="Kore"
                            )
                        ),
                    ),
                ]
            ),
        ),
    ),
)
```

### 5.2 REST API 格式

```json
{
  "contents": [
    {
      "parts": [
        {
          "text": "小明: 你有試過新的多角色功能嗎？\n小華: 有啊！我超興奮的。"
        }
      ]
    }
  ],
  "generationConfig": {
    "responseModalities": ["AUDIO"],
    "speechConfig": {
      "multiSpeakerVoiceConfig": {
        "speakerVoiceConfigs": [
          {
            "speaker": "小明",
            "voiceConfig": {
              "prebuiltVoiceConfig": { "voiceName": "Charon" }
            }
          },
          {
            "speaker": "小華",
            "voiceConfig": {
              "prebuiltVoiceConfig": { "voiceName": "Kore" }
            }
          }
        ]
      }
    }
  }
}
```

### 5.3 限制

- 目前最多支援 **2 位** 說話者
- 文本格式必須是 `{speaker_name}: {text}` 的對話格式
- 對話中角色名稱必須與 `speakerVoiceConfigs` 中的 `speaker` 對應

---

## 6. 本專案現有實作與 API 差異

### 6.1 目前實作狀態

| 功能 | 現狀 | 檔案位置 |
|------|------|----------|
| Style Prompt | ✅ 已支援（前置於 text） | `gemini_tts.py:98-99` |
| 單聲音合成 | ✅ 已支援 | `gemini_tts.py` |
| 多角色對話 | ❌ 未實作 | — |
| SSML | ⚠️ 可直接寫在 text 中使用，未特別封裝 | — |
| 行內情緒標籤 | ⚠️ 可直接寫在 text 中使用，未特別封裝 | — |
| `languageCode` | ❌ 未在 speechConfig 中設定 | — |
| 串流合成 | ❌ 模擬串流（合成後分段） | `gemini_tts.py` |

### 6.2 Cloud TTS API 獨有功能

本專案使用 Gemini API (`generateContent`)，以下功能僅在 Cloud TTS API (`text:synthesize`) 中可用：

| 功能 | 說明 |
|------|------|
| `input.prompt` 獨立欄位 | text 與 style prompt 分離，各有 4,000 bytes 上限 |
| `audioConfig.speakingRate` | 數值化語速控制 (0.5-2.0) |
| `audioConfig.volumeGainDb` | 數值化音量控制 |
| `advancedVoiceOptions.relaxSafetyFilters` | 放寬內容安全過濾 |
| 原生串流 (`streaming_synthesize`) | 真正的伺服器端串流 |
| 直接輸出 MP3/OGG | 無需手動轉換格式 |

---

## 7. 音訊輸出格式

### 7.1 Gemini API 輸出

- 固定格式: `audio/L16;codec=pcm;rate=24000`（16-bit PCM, 24kHz, 單聲道）
- 不含 WAV header — 需自行轉換
- 回應位置: `response.candidates[0].content.parts[0].inline_data.data`（base64 編碼）

```python
# PCM → WAV 轉換
import wave, base64

audio_data = base64.b64decode(response_data)
with wave.open("output.wav", "wb") as wf:
    wf.setnchannels(1)
    wf.setsampwidth(2)  # 16-bit
    wf.setframerate(24000)
    wf.writeframes(audio_data)
```

### 7.2 Cloud TTS API 輸出

`audioConfig.audioEncoding` 支援: `LINEAR16`, `MP3`, `OGG_OPUS`, `MULAW`

> **已知問題**: Gemini TTS 模型可能忽略 encoding 參數，無論請求什麼格式都回傳 LINEAR16 PCM。

---

## 8. 定價與限制

### 8.1 定價（2026-01）

| 模型 | Input (text) | Output (audio) |
|------|-------------|----------------|
| gemini-2.5-pro-tts | $1.00 / 1M tokens | $20.00 / 1M tokens |
| gemini-2.5-flash-tts | $0.50 / 1M tokens | $10.00 / 1M tokens |

Free tier 有較低的速率限制但不收費。

### 8.2 速率限制（每個 Project）

| 層級 | RPM | TPM |
|------|-----|-----|
| Free (Flash) | ~15 | 250,000 |
| Free (Pro) | ~5 | 250,000 |
| 付費 | 依專案而異 | 依專案而異 |

### 8.3 請求限制

| 限制 | 值 |
|------|-----|
| `input.text` 上限 | 4,000 bytes |
| `input.prompt` 上限 | 4,000 bytes |
| text + prompt 合計上限 | 8,000 bytes |
| 輸出音訊最大長度 | ~655 秒 |
| Context window | 32,000 tokens |
| 最大說話者數 | 2 |

---

## 9. 實用調教技巧

### 9.1 語氣調教三層架構

```
第一層：聲音選擇 → 決定基礎音色（如 Kore 堅定、Schedar 關懷）
第二層：Style Prompt → 設定整體語調（如「用溫暖專業的語氣」）
第三層：行內標籤/SSML → 控制局部情緒（如 [excited]、<break>）
```

### 9.2 中文 TTS 優化

```python
# 1. 加入適當標點控制停頓
text = "人工智慧，正在改變世界。"  # ✅ 有停頓
text = "人工智慧正在改變世界"      # ❌ 一口氣讀完

# 2. 英文縮寫加注讀法
text = '<sub alias="人工智慧">AI</sub> 技術日新月異'

# 3. 數字讀法控制
text = '<say-as interpret-as="cardinal">110</say-as>'  # 一百一十
```

### 9.3 效果排序

根據實測，以下控制方式的**可靠度排序**：

```
聲音選擇 > Style Prompt > SSML <prosody> > 行內 [tag] > SSML <say-as>
   最穩定                                              最不穩定
```

---

## 10. 參考連結

- [Google AI - Speech Generation](https://ai.google.dev/gemini-api/docs/speech-generation)
- [Google Cloud - Gemini TTS](https://cloud.google.com/text-to-speech/docs/tts-model-gemini)
- [Google Blog - Improving Gemini TTS](https://blog.google/technology/developers/gemini-2-5-text-to-speech/)
- [Gemini Cookbook - TTS Quickstart](https://github.com/google-gemini/cookbook/blob/main/quickstarts/Get_started_TTS.ipynb)
- [Gemini API Pricing](https://ai.google.dev/gemini-api/docs/pricing)
- [Dev.to - Gemini TTS with Emotion & SSML](https://dev.to/abdalrohman/deep-dive-i-tested-googles-new-gemini-25-pro-tts-with-emotion-ssml-tags-5d3i)

## 更新日誌

| 日期 | 變更 |
|------|------|
| 2026-01-30 | 初始版本：Style Prompt、SSML、行內標籤、多角色、聲音選擇 |

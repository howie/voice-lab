# Google Gemini / Lyria 音樂生成研究

> 研究日期: 2026-02-19

## 目錄

- [一、概覽](#一概覽)
- [二、模型版本](#二模型版本)
- [三、Lyria 3 (最新)](#三lyria-3-最新)
- [四、Lyria 2 — Vertex AI API](#四lyria-2--vertex-ai-api)
- [五、Lyria RealTime — Gemini API (實驗性)](#五lyria-realtime--gemini-api-實驗性)
- [六、Prompt 撰寫指南](#六prompt-撰寫指南)
- [七、安全與治理](#七安全與治理)
- [八、費用](#八費用)
- [九、與本專案整合評估](#九與本專案整合評估)
- [十、與現有方案比較](#十與現有方案比較)
- [十一、結論與建議](#十一結論與建議)

---

## 一、概覽

Google DeepMind 的 **Lyria** 系列是 Google 用於音樂生成的基礎模型。目前有三個主要版本/接入方式：

| 版本 | 模型代號 | 發布時間 | 接入方式 | 人聲 | 歌詞 | 最大長度 |
|---|---|---|---|---|---|---|
| **Lyria 3** | `lyria-003-experimental` (預覽) | 2026-02-18 | Gemini App / YouTube Dream Track / Vertex AI (預覽) | ✅ | ✅ (自動生成) | 30s |
| **Lyria 2** | `lyria-002` | 2025 | Vertex AI REST API (GA) | ❌ (純器樂) | ❌ | ~32.8s |
| **Lyria RealTime** | `lyria-realtime-exp` | 2025 (實驗性) | Gemini API WebSocket (`v1alpha`) | ❌ (純器樂 + Vocalization 模式) | ❌ | 串流 (無限制) |

**關鍵特點**：
- 所有 Lyria 生成的音訊均內嵌 **SynthID** 不可聽見浮水印（自 2023 年起已累計標記超過 100 億筆資產）
- Google 對 Vertex AI 企業客戶提供雙重 **IP 侵權賠償保障**（訓練資料 + 生成內容）
- 48 kHz stereo 高品質音訊輸出
- Vertex AI 是目前**唯一橫跨影片、圖片、語音、音樂四大模態**的統一生成式 AI 平台

---

## 二、模型版本

### Lyria 3 — 最高擬真度全功能模型

Google DeepMind 最高擬真度的音樂模型，擅長處理複雜的樂器編制、人聲特徵以及長達 30 秒以上的音樂片段。

- **多模態輸入**：文字描述、圖片、影片均可作為生成提示
- **自動歌詞生成**：無需提供歌詞，模型根據提示自動創作
- **人聲支援**：支援多語言人聲演唱
- **風格控制**：可調整曲風、人聲風格、節奏等
- **4 首變體**：每次生成 4 首不同風格的變體供選擇
- **迭代修改**：可在選定作品上要求調整（如「加快速度」、「加入女聲」）
- **封面圖生成**：整合 Nano Banana 自動生成專輯封面
- **長上下文窗口**：應用於音訊波形，使生成的片段能維持結構完整性（verse → chorus → bridge）

### Lyria 2 (`lyria-002`) — 企業級 REST API (GA)

透過 Vertex AI 提供的正式 API，適合生產環境整合：

- 純器樂生成（無人聲）
- ~32.8 秒 WAV 輸出 (48 kHz stereo)
- 支援 `negative_prompt`（排除不想要的元素）
- 可指定 `seed` 以重現結果
- 批量生成 (`sample_count`)
- **已正式發布 (GA)**，全球可用

### Lyria RealTime (`lyria-realtime-exp`) — 即時串流 WebSocket

實驗性的即時音樂生成 API：

- 雙向 WebSocket 即時串流
- 2 秒音訊區塊連續生成（延遲 ≤ 2 秒）
- 可即時調整風格、節奏、密度等參數
- 加權提示 (weighted prompts) 混合多種風格
- **Vocalization 模式**：可生成類人聲作為額外樂器
- 支援分軌控制（靜音鼓組、靜音低音、僅鼓組+低音）

---

## 三、Lyria 3 (最新)

### 功能特點

| 功能 | 詳情 |
|---|---|
| 人聲 + 歌詞 | ✅ 自動生成歌詞及人聲演唱 |
| 多模態輸入 | 文字、圖片、影片 |
| 最大長度 | 30 秒 |
| 音質 | 高擬真度，48 kHz stereo |
| 曲風覆蓋 | lo-fi、EDM、pop ballad、cinematic、funk、Motown 等 |
| 音樂結構 | intro → verse → chorus → bridge → outro |
| 每次生成 | 4 首變體 |
| 迭代修改 | ✅ 可在選定作品上繼續調整 |
| 封面圖 | ✅ 整合 Nano Banana 自動生成 |

### 支援語言

英語、德語、西班牙語、法語、印地語、日語、韓語、葡萄牙語（8 種）

### 限制

- **30 秒上限**：目前單次生成上限 30 秒
- **無藝人模仿**：提及特定藝人僅作為風格參考，不會模仿
- **Beta 狀態**：仍在測試階段
- **18+ 年齡限制**

### 接入方式

| 管道 | 狀態 | 模型代號 | 說明 |
|---|---|---|---|
| Gemini App | ✅ 已上線 | — | 桌面版已發布，行動版陸續推出 |
| YouTube Dream Track | ✅ 全球擴展中 | — | 原僅限美國，現全球推出 |
| Vertex AI API | 🧪 預覽版 | `lyria-003-experimental` | 企業用戶可透過預覽申請存取 |
| Gemini API (開發者) | ⏳ 未確認 | — | 尚無獨立的 Lyria 3 開發者 API 文檔 |

> **注意**：`lyria-003-experimental` 已出現於 Vertex AI API 參考文檔中作為預覽版模型代號。正式 GA 版本的發布時間尚未確認。

---

## 四、Lyria 2 — Vertex AI API

### 端點

```
POST https://{LOCATION}-aiplatform.googleapis.com/v1/projects/{PROJECT_ID}/locations/{LOCATION}/publishers/google/models/lyria-002:predict
```

### 認證

使用 Google Cloud 服務帳號 + OAuth 2.0 Bearer Token：

```bash
curl -X POST \
  -H "Authorization: Bearer $(gcloud auth print-access-token)" \
  -H "Content-Type: application/json" \
  "https://us-central1-aiplatform.googleapis.com/v1/projects/${PROJECT_ID}/locations/us-central1/publishers/google/models/lyria-002:predict" \
  -d '{
    "instances": [
      {
        "prompt": "Upbeat, Rhythmic Peruvian Cumbia with a psychedelic edge",
        "negative_prompt": "vocals, distortion"
      }
    ],
    "parameters": {
      "sample_count": 1
    }
  }'
```

### 請求參數

| 參數 | 位置 | 類型 | 必填 | 說明 |
|---|---|---|---|---|
| `prompt` | `instances` | string | ✅ | 音樂描述（限美式英文） |
| `negative_prompt` | `instances` | string | ❌ | 排除不想要的元素 |
| `seed` | `instances` | int | ❌ | 用於重現結果，**不可與 `sample_count` 並用** |
| `sample_count` | `parameters` | int | ❌ | 生成數量，**不可與 `seed` 並用** |

### 回應格式

```json
{
  "predictions": [
    {
      "audioContent": "BASE64_ENCODED_WAV_STRING",
      "mimeType": "audio/wav"
    }
  ],
  "deployedModelId": "xxxxxxxxxxxxxxx",
  "model": "projects/{PROJECT_ID}/locations/{LOCATION}/publishers/google/models/lyria-002",
  "modelDisplayName": "Lyria 2"
}
```

### Python 程式碼範例

```python
import base64

import google.auth
import google.auth.transport.requests
import requests

PROJECT_ID = "your-project-id"
LOCATION = "us-central1"

# 取得 access token
credentials, _ = google.auth.default()
credentials.refresh(google.auth.transport.requests.Request())

endpoint = (
    f"https://{LOCATION}-aiplatform.googleapis.com/v1/"
    f"projects/{PROJECT_ID}/locations/{LOCATION}/"
    f"publishers/google/models/lyria-002:predict"
)

payload = {
    "instances": [
        {
            "prompt": "A serene ambient track with gentle piano and strings",
            "negative_prompt": "drums, electric guitar, distortion",
        }
    ],
    "parameters": {"sample_count": 2},
}

response = requests.post(
    endpoint,
    headers={
        "Authorization": f"Bearer {credentials.token}",
        "Content-Type": "application/json",
    },
    json=payload,
)
result = response.json()

# 解碼 base64 音訊
for i, prediction in enumerate(result["predictions"]):
    audio_bytes = base64.b64decode(prediction["audioContent"])
    with open(f"output_{i}.wav", "wb") as f:
        f.write(audio_bytes)
```

### 輸出格式

- ~32.8 秒 WAV 音訊 (48 kHz stereo)
- Base64 編碼於 JSON 回應中
- 僅限器樂（無人聲）
- SynthID 浮水印已嵌入

### 限制

- 僅支援美式英文 prompt
- 僅器樂輸出
- ~32.8 秒固定長度（文檔記為「30 秒」）
- 無 webhook 回呼機制
- 僅 200 回應碼計費（4xx/5xx 不計費）

### 官方 Notebook

- [lyria2_music_generation.ipynb (GitHub)](https://github.com/GoogleCloudPlatform/generative-ai/blob/main/audio/music/getting-started/lyria2_music_generation.ipynb)
- [Open in Colab](https://colab.research.google.com/github/GoogleCloudPlatform/generative-ai/blob/main/audio/music/getting-started/lyria2_music_generation.ipynb)

---

## 五、Lyria RealTime — Gemini API (實驗性)

### WebSocket 端點

```
wss://generativelanguage.googleapis.com/ws/google.ai.generativelanguage.v1alpha.GenerativeService.BidiGenerateMusic
```

### 認證

```python
from google import genai

# 使用 API Key（不支援 Ephemeral Token）
client = genai.Client(
    api_key="GEMINI_API_KEY",
    http_options={'api_version': 'v1alpha'}
)
```

### WebSocket 訊息類型

#### 客戶端 → 伺服器

JSON 物件必須包含以下其中一個欄位：

| 欄位 | 類型 | 說明 |
|---|---|---|
| `setup` | `BidiGenerateMusicSetup` | 僅限第一條訊息，設定模型 |
| `client_content` | `BidiGenerateMusicClientContent` | 發送加權提示 |
| `music_generation_config` | `BidiGenerateMusicGenerationConfig` | 更新生成參數 |
| `playback_control` | `BidiGenerateMusicPlaybackControl` | 播放控制：`play`、`pause`、`stop`、`reset_context` |

#### 伺服器 → 客戶端

| 欄位 | 說明 |
|---|---|
| `BidiGenerateMusicSetupComplete` | 空訊息，確認 setup 完成（需等此訊息後才能發送其他訊息） |
| `server_content` | 包含 `audio_chunks[0].data`（增量音訊資料） |
| `filtered_prompt` | 提示觸發安全過濾時的說明 |

### Python 完整程式碼範例

```python
import asyncio

import pyaudio
from google import genai
from google.genai import types

# 常數
CHANNELS = 2
FORMAT = pyaudio.paInt16
OUTPUT_RATE = 48000
MODEL = 'models/lyria-realtime-exp'

client = genai.Client(http_options={'api_version': 'v1alpha'})


async def main():
    async with client.aio.live.music.connect(model=MODEL) as session:

        # 背景接收音訊的任務
        async def receive_audio():
            async for message in session.receive():
                audio_data = message.server_content.audio_chunks[0].data
                # 處理/播放 audio_data (2 秒 PCM 區塊)...

        # 設定加權提示（可混合多種風格）
        await session.set_weighted_prompts(
            prompts=[
                types.WeightedPrompt(text='piano jazz', weight=0.6),
                types.WeightedPrompt(text='electronic ambient', weight=0.4),
            ]
        )

        # 設定音樂生成參數（必須設定完整參數，否則未設定的欄位會重設為預設值）
        await session.set_music_generation_config(
            config=types.LiveMusicGenerationConfig(
                bpm=90,
                density=0.5,
                brightness=0.6,
                guidance=4.0,
                temperature=1.1,
                scale=types.Scale.D_MAJOR_B_MINOR,
                music_generation_mode=types.MusicGenerationMode.QUALITY,
            )
        )

        # 開始串流
        await session.play()

        # 在背景接收音訊
        asyncio.create_task(receive_audio())

        # 保持 session 活躍...
        await asyncio.sleep(60)


asyncio.run(main())
```

### 即時控制參數 (`LiveMusicGenerationConfig`)

| 參數 | 類型 | 範圍 | 預設值 | 說明 | 即時生效 |
|---|---|---|---|---|---|
| `guidance` | float | 0.0 – 6.0 | 4.0 | 提示遵循強度（越高越忠實，但轉場更突兀） | ✅ |
| `bpm` | int | 60 – 200 | 模型決定 | 每分鐘拍數 | ❌ 需 `reset_context()` |
| `density` | float | 0.0 – 1.0 | 模型決定 | 音符密度（低=稀疏，高=繁密） | ✅ |
| `brightness` | float | 0.0 – 1.0 | 模型決定 | 音色亮度（基於 log-mel 頻譜質心） | ✅ |
| `scale` | Scale enum | 見下表 | 模型決定 | 音階/調性 | ❌ 需 `reset_context()` |
| `temperature` | float | 0.0 – 3.0 | 1.1 | 隨機性/創意度 | ✅ |
| `top_k` | int | 1 – 1,000 | 40 | Top-K 取樣 | ✅ |
| `seed` | int | 0 – 2,147,483,647 | 隨機 | 隨機種子 | — |
| `mute_bass` | bool | — | `False` | 降低低音輸出 | ✅ |
| `mute_drums` | bool | — | `False` | 降低鼓組輸出 | ✅ |
| `only_bass_and_drums` | bool | — | `False` | 僅輸出低音和鼓組 | ✅ |
| `music_generation_mode` | enum | 見下方 | `QUALITY` | 生成焦點模式 | ✅ |

> **重要**：更新參數時必須設定**完整的** config 物件，否則未指定的欄位會重設為預設值。

### `MusicGenerationMode` 列舉

| 值 | 說明 |
|---|---|
| `QUALITY` | 預設。聚焦於輸出品質 |
| `DIVERSITY` | 聚焦於音樂多樣性/變化 |
| `VOCALIZATION` | 生成類人聲作為額外樂器（非歌詞演唱） |

### `Scale` 列舉（音階/調性）

模型不區分關係大小調，每個 enum 值同時對應大調與關係小調：

| Enum 值 | 調號 |
|---|---|
| `C_MAJOR_A_MINOR` | 無升降號 |
| `G_MAJOR_E_MINOR` | 1 升 |
| `D_MAJOR_B_MINOR` | 2 升 |
| `A_MAJOR_F_SHARP_MINOR` | 3 升 |
| `E_MAJOR_C_SHARP_MINOR` | 4 升 |
| `B_MAJOR_G_SHARP_MINOR` | 5 升 |
| `F_SHARP_MAJOR_D_SHARP_MINOR` | 6 升 |
| `D_FLAT_MAJOR_B_FLAT_MINOR` | 5 降 |
| `A_FLAT_MAJOR_F_MINOR` | 4 降 |
| `E_FLAT_MAJOR_C_MINOR` | 3 降 |
| `B_FLAT_MAJOR_G_MINOR` | 2 降 |
| `F_MAJOR_D_MINOR` | 1 降 |

### 播放控制

| 方法 | 說明 |
|---|---|
| `session.play()` | 開始/恢復音樂生成 |
| `session.pause()` | 暫停生成 |
| `session.reset_context()` | 硬重設（BPM/Scale 變更後需呼叫，不會中斷串流但轉場會較生硬） |

### 輸出規格

- 48 kHz stereo PCM 連續串流
- 每次生成約 2 秒音訊區塊
- SynthID 浮水印已嵌入

### 限制

- **實驗性** (`v1alpha`)：API 可能變動
- **以器樂為主**：`VOCALIZATION` 模式可生成類人聲音效，但非歌詞演唱
- 需要客戶端實作音訊緩衝以確保播放流暢
- 不支援 Ephemeral Token（僅支援長期 API Key）
- 安全過濾器會靜默忽略違規提示（透過 `filtered_prompt` 回報）

### 官方範例

- [Get_started_LyriaRealTime.py (Gemini Cookbook)](https://github.com/google-gemini/cookbook/blob/main/quickstarts/Get_started_LyriaRealTime.py)
- [Lyria RealTime — Magenta](https://magenta.withgoogle.com/lyria-realtime)

---

## 六、Prompt 撰寫指南

> 基於 [Vertex AI — Lyria 音樂生成提示指南](https://docs.cloud.google.com/vertex-ai/generative-ai/docs/music/music-gen-prompt-guide)

### 核心結構

以核心音樂概念為起點，逐步加入關鍵詞和修飾語：

1. **曲風與時代** (Genre & Era)：主要類別 + 風格特徵
2. **情緒與氛圍** (Mood & Emotion)：期望的感受
3. **樂器配置** (Instrumentation)：具體樂器
4. **節奏與速度** (Tempo & Rhythm)：節拍和韻律特徵

### 撰寫原則

| 原則 | 說明 |
|---|---|
| 具體且描述性 | 使用形容詞/副詞描繪清晰的音效畫面 |
| 指明曲風、情緒、風格 | 明確陳述類別、感受、特徵 |
| 指定樂器和節奏 | 點名樂器，描述節拍和韻律 |
| 善用 negative prompt | 列出要排除的元素 |
| 迭代與實驗 | 逐步微調 prompt |

### Prompt 範例

**簡單**：
```
prompt: "An uplifting and hopeful orchestral piece with a soaring string melody and triumphant brass"
negative_prompt: "dissonant, minor key"
```

**詳細/結構化**：
```
prompt: "Create a track that merges 1970s funk with modern electronic synthwave.
         Tempo should be 110 BPM. Use instruments like slap bass, guitar,
         Moog synthesizer, and a crisp drum machine with heavy reverb."
```

**品牌音效場景**：
```
prompt: "Upbeat, Rhythmic Peruvian Cumbia with a psychedelic edge, LA, Live performance
         at a Latin music Festival, incorporating electric guitars, bass, and often
         utilizing a prominent timbales percussion section, creating a powerful and
         danceable vibe. Vibrant and energetic."
negative_prompt: "vocals, distortion"
```

### 常用曲風/時代關鍵詞

`90s trip-hop`、`Baroque chamber music`、`80s synth-pop`、`Metal and rap fusion`、`Indie folk`、`Old country`、`Early 90s hip-hop`、`K-pop`、`Lo-fi beats`、`Cinematic orchestral`

### 常用情緒/描述詞

`Acoustic`、`Ambient`、`Bright Tones`、`Chill`、`Crunchy Distortion`、`Danceable`、`Dreamy`、`Echo`、`Emotional`、`Ethereal Ambience`、`Experimental`、`Funky`、`Lo-fi`、`Ominous Drone`、`Psychedelic`、`Rich Orchestration`、`Upbeat`、`Virtuoso`

### 支援樂器（部分列表）

`303 Acid Bass`、`808 Hip Hop Beat`、`Accordion`、`Alto Saxophone`、`Bagpipes`、`Banjo`、`Cello`、`Djembe`、`Flamenco Guitar`、`Glockenspiel`、`Harp`、`Harpsichord`、`Kalimba`、`Koto`、`Mandolin`、`Marimba`、`Mellotron`、`Moog Oscillations`、`Rhodes Piano`、`Shamisen`、`Sitar`、`Steel Drum`、`Tabla`、`Trumpet`、`Vibraphone`

### 速度控制差異

| API | 控制方式 |
|---|---|
| Lyria 2 (Vertex AI) | 在 prompt 文字中描述（如 "120 BPM"、"slow ballad"） |
| Lyria RealTime | 專用 `bpm` 參數 (60–200) |

---

## 七、安全與治理

### SynthID 數位浮水印

- 在每個影像、影片、音訊幀中嵌入不可聽見的浮水印
- 即使壓縮為 MP3、降速或透過麥克風錄製仍可偵測
- 自 2023 年推出以來已標記超過 **100 億筆** 資產
- 跨 Imagen、Veo、Lyria、Chirp 所有輸出

### 安全過濾器

- 輸入提示和輸出內容均經過安全過濾器評估
- 企業客戶可設定過濾器的嚴格程度
- 內建藝人意圖檢查（防止模仿特定藝人）
- 內建背誦檢查（防止重現已有作品）
- 遵循 Google 負責任 AI 原則

### 資料治理

- Google **不使用客戶資料**訓練模型
- 客戶資料僅按照客戶指示處理
- 受服務特定條款約束

### IP 侵權賠償保障（雙重保障）

1. **訓練資料賠償**：涵蓋因 Google 使用訓練資料而被指控侵犯第三方 IP 的情況
2. **生成內容賠償**：涵蓋因生成內容被指控侵犯第三方 IP 的情況

> **條件**：客戶必須按設計使用安全過濾器；若故意創建侵權內容則不適用賠償。

---

## 八、費用

| 方案 | 費用 | 說明 |
|---|---|---|
| **Lyria 3 (Gemini App)** | 免費 (有限額) | AI Plus/Pro/Ultra 訂閱有更高額度 |
| **Lyria 2 (Vertex AI)** | $0.06 / 30 秒 | 僅 200 回應計費；新帳號有 $300 試用額度 |
| **Lyria RealTime (Gemini API)** | 實驗性免費 | 目前免費使用，正式發布後預計收費 |

### 費用估算（以月 500 首 BGM 計算）

| 方案 | 月費 |
|---|---|
| Lyria 2 (Vertex AI) | $30 (500 × $0.06) |
| Mureka (已整合) | $60–75 (500 × $0.12–0.15/min) |
| MiniMax Music 2.5 | $2–17.50 |

---

## 九、與本專案整合評估

### 可行整合方案

#### 方案 A：Lyria 2 via Vertex AI (立即可用 — GA)

**優點**：
- 正式 REST API，文檔完整，已 GA
- 本專案已有 Google Cloud 整合基礎 (GCP Terraform 部署)
- 雙重 IP 賠償保障，企業級安全
- $0.06/30s 價格合理

**缺點**：
- 僅器樂，無人聲/歌詞
- ~32.8 秒固定長度
- 僅支援英文 prompt

**整合難度**：低 — 標準 REST API，可直接加入現有 Factory Pattern

```python
# 預估整合路徑
backend/src/infrastructure/providers/music/
├── interface.py          # IMusicProvider (已有)
├── lyria_provider.py     # 新增：LyriaVertexAIProvider
└── factory.py            # 在 Factory 中註冊
```

#### 方案 B：Lyria RealTime via Gemini API (實驗性)

**優點**：
- 即時串流，可持續生成
- 豐富的即時控制參數（BPM、密度、亮度、音階、分軌控制）
- Vocalization 模式可生成類人聲
- 適合互動式音樂場景

**缺點**：
- 實驗性 API (`v1alpha`)，可能變動
- WebSocket 架構與現有 REST 模式不同
- 以器樂為主
- 需實作音訊緩衝
- 更新參數必須傳送完整 config

**整合難度**：中 — 需要 WebSocket 客戶端及音訊串流處理

#### 方案 C：Lyria 3 via Vertex AI (預覽版)

**優點**：
- 全功能：人聲 + 歌詞 + 器樂
- 最高音質
- 多模態輸入
- 多語言支援（8 種語言）

**缺點**：
- ⚠️ `lyria-003-experimental` 為預覽版，需申請存取權限
- 30 秒上限
- API 規格可能尚不穩定

**整合難度**：中 — 預覽版 API 可能有變動，需密切追蹤

### 建議整合策略

1. **短期**：整合 **Lyria 2** (`lyria-002`) 作為純器樂 BGM 生成選項，補充 Mureka 的功能
2. **中期**：申請 **Lyria 3** (`lyria-003-experimental`) 預覽版存取權限進行測試，待 GA 後正式整合
3. **可選**：若有即時互動音樂需求，可評估 **Lyria RealTime** 實驗性 API

---

## 十、與現有方案比較

| 面向 | Google Lyria 2 | Google Lyria 3 | Mureka (已整合) | MiniMax Music 2.5 | ElevenLabs Music |
|---|---|---|---|---|---|
| API 狀態 | ✅ GA | 🧪 預覽 (`lyria-003-experimental`) | ✅ 正式 | ✅ 正式 | ✅ 正式 |
| 人聲 | ❌ | ✅ | ✅ | ✅ | ✅ |
| 歌詞 | ❌ | ✅ 自動生成 | ✅ 需提供 | ✅ | ✅ |
| 最大長度 | ~32.8s | 30s | 5 min | 60s | 5 min |
| 多模態輸入 | ❌ | ✅ (文字+圖片+影片) | 部分 (文字+參考音訊) | 部分 (文字+參考音訊) | ✅ (文字+Composition Plan) |
| 即時串流 | ✅ (RealTime) | ❌ | ❌ | ❌ | ❌ |
| IP 保障 | ✅ 雙重賠償保障 | ✅ SynthID + 賠償 | ❌ | ❌ | ❌ |
| 費用 | $0.06/30s | 預覽免費 | $0.12–0.15/min | $0.004–0.035/次 | Credit-based |
| 多語言 | ❌ (英文) | ✅ (8 種) | ✅ (10 種) | — | ✅ (多種) |
| 本專案整合 | 🔧 低難度 | 🧪 需申請預覽 | ✅ 已整合 | 🔧 低難度 | 🔧 低難度 |

---

## 十一、結論與建議

### 核心發現

1. **Lyria 3 是重大突破**：首次在消費者級產品中提供完整的人聲+歌詞+器樂 AI 音樂生成，音質擬真度高。`lyria-003-experimental` 已作為預覽版出現於 Vertex AI。

2. **Lyria 2 立即可用**：透過 Vertex AI 提供穩定的 GA REST API，適合純器樂 BGM 場景，且本專案已有 GCP 基礎設施。雙重 IP 賠償保障是重要企業優勢。

3. **Lyria RealTime 獨特定位**：即時串流音樂生成是市場上獨一無二的功能，提供豐富的即時控制參數（BPM、密度、亮度、音階、分軌控制、Vocalization 模式），適合互動式應用。

4. **統一平台優勢**：Vertex AI 是唯一橫跨影片 (Veo)、圖片 (Imagen)、語音 (Chirp)、音樂 (Lyria) 四大模態的平台，本專案已有 GCP 基礎設施可直接利用。

### 建議

| 優先序 | 行動 | 理由 |
|---|---|---|
| 1️⃣ | **持續使用 Mureka** 作為主要音樂生成 provider | 已整合、5 分鐘長度、支援人聲和歌詞 |
| 2️⃣ | **整合 Lyria 2** 作為器樂 BGM 替代方案 | GA 穩定版、GCP 已有基礎設施、雙重 IP 賠償保障、$0.06/30s 低價 |
| 3️⃣ | **申請 Lyria 3 預覽版** (`lyria-003-experimental`) | 測試全功能音樂生成能力，為 GA 發布做準備 |
| 4️⃣ | **評估 Lyria RealTime** 用於互動式場景 | 若產品需要即時音樂生成功能 |

---

## 官方文件來源

1. [Google AI for Developers — Music generation using Lyria RealTime](https://ai.google.dev/gemini-api/docs/music-generation) — Gemini API WebSocket 即時音樂生成
2. [Vertex AI — Lyria API Reference](https://docs.cloud.google.com/vertex-ai/generative-ai/docs/model-reference/lyria-music-generation) — REST API 參考（`lyria-002` + `lyria-003-experimental`）
3. [Google DeepMind — Lyria 3 & Lyria RealTime](https://deepmind.google/models/lyria/) — 模型架構與技術報告
4. [Google Cloud Blog — Expanding generative media for enterprise](https://cloud.google.com/blog/products/ai-machine-learning/expanding-generative-media-for-enterprise-on-vertex-ai) — 企業應用與 Vertex AI 整合
5. [Vertex AI — Lyria Prompt Guide](https://docs.cloud.google.com/vertex-ai/generative-ai/docs/music/music-gen-prompt-guide) — Prompt 撰寫實務指南

## 其他參考

- [Google Blog — Lyria 3 公告](https://blog.google/innovation-and-ai/products/gemini-app/lyria-3/)
- [Gemini API — Live Music WebSocket Reference](https://ai.google.dev/api/live_music)
- [Vertex AI — Lyria 音樂生成](https://docs.cloud.google.com/vertex-ai/generative-ai/docs/music/generate-music)
- [Vertex AI — Lyria 2 Model Card](https://docs.cloud.google.com/vertex-ai/generative-ai/docs/models/lyria/lyria-002)
- [Vertex AI Pricing](https://cloud.google.com/vertex-ai/generative-ai/pricing)
- [Get_started_LyriaRealTime.py (Gemini Cookbook)](https://github.com/google-gemini/cookbook/blob/main/quickstarts/Get_started_LyriaRealTime.py)
- [lyria2_music_generation.ipynb (Colab)](https://colab.research.google.com/github/GoogleCloudPlatform/generative-ai/blob/main/audio/music/getting-started/lyria2_music_generation.ipynb)
- [TechCrunch — Google adds music-generation to Gemini](https://techcrunch.com/2026/02/18/google-adds-music-generation-capabilities-to-the-gemini-app/)
- [9to5Google — Gemini Lyria 3 rollout](https://9to5google.com/2026/02/18/gemini-app-music-lyria-3/)
- [MarkTechPost — Lyria 3 release](https://www.marktechpost.com/2026/02/18/google-deepmind-releases-lyria-3-an-advanced-music-generation-ai-model-that-turns-photos-and-text-into-custom-tracks-with-included-lyrics-and-vocals/)
- [Lyria RealTime — Magenta](https://magenta.withgoogle.com/lyria-realtime)

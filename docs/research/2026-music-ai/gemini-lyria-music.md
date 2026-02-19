# Google Gemini / Lyria 音樂生成研究

> 研究日期: 2026-02-19

## 目錄

- [一、概覽](#一概覽)
- [二、模型版本](#二模型版本)
- [三、Lyria 3 (最新)](#三lyria-3-最新)
- [四、Lyria 2 — Vertex AI API](#四lyria-2--vertex-ai-api)
- [五、Lyria RealTime — Gemini API (實驗性)](#五lyria-realtime--gemini-api-實驗性)
- [六、費用](#六費用)
- [七、與本專案整合評估](#七與本專案整合評估)
- [八、與現有方案比較](#八與現有方案比較)
- [九、結論與建議](#九結論與建議)

---

## 一、概覽

Google DeepMind 的 **Lyria** 系列是 Google 用於音樂生成的基礎模型。目前有三個主要版本/接入方式：

| 版本 | 發布時間 | 接入方式 | 人聲 | 歌詞 | 最大長度 |
|---|---|---|---|---|---|
| **Lyria 3** | 2026-02-18 | Gemini App / YouTube Dream Track | ✅ | ✅ (自動生成) | 30s |
| **Lyria 2** (`lyria-002`) | 2025 | Vertex AI REST API | ❌ (純器樂) | ❌ | 30s |
| **Lyria RealTime** (`lyria-realtime-exp`) | 2025 (實驗性) | Gemini API WebSocket | ❌ (純器樂) | ❌ | 串流 (無限制) |

**關鍵特點**：
- 所有 Lyria 生成的音訊均內嵌 **SynthID** 不可聽見浮水印
- Google 對 Vertex AI 企業客戶提供 **IP 侵權賠償保障**
- 48 kHz 高品質音訊輸出

---

## 二、模型版本

### Lyria 3 — 消費者級全功能模型

Google DeepMind 最高擬真度的音樂模型，擅長處理複雜的樂器編制、人聲特徵以及 30 秒音樂片段。

- **多模態輸入**：文字描述、圖片、影片均可作為生成提示
- **自動歌詞生成**：無需提供歌詞，模型根據提示自動創作
- **人聲支援**：支援多語言人聲演唱
- **風格控制**：可調整曲風、人聲風格、節奏等
- **4 首變體**：每次生成 4 首不同風格的變體供選擇
- **迭代修改**：可在選定作品上要求調整（如「加快速度」、「加入女聲」）
- **封面圖生成**：整合 Nano Banana 自動生成專輯封面

### Lyria 2 (`lyria-002`) — 企業級 REST API

透過 Vertex AI 提供的正式 API，適合生產環境整合：

- 純器樂生成（無人聲）
- 30 秒 WAV 輸出 (48 kHz)
- 支援 negative prompt（排除不想要的元素）
- 可指定 seed 以重現結果
- 批量生成 (`sample_count`)

### Lyria RealTime (`lyria-realtime-exp`) — 即時串流 WebSocket

實驗性的即時音樂生成 API：

- 雙向 WebSocket 即時串流
- 2 秒音訊區塊連續生成
- 可即時調整風格、節奏、密度等參數
- 加權提示 (weighted prompts) 混合多種風格

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

| 管道 | 狀態 | 說明 |
|---|---|---|
| Gemini App | ✅ 已上線 | 桌面版已發布，行動版陸續推出 |
| YouTube Dream Track | ✅ 全球擴展中 | 原僅限美國，現全球推出 |
| Vertex AI API | ⏳ 尚未文檔化 | 已宣布整合，`lyria-003` 端點尚未公開 |
| Gemini API (開發者) | ⏳ 未確認 | 尚無獨立的 Lyria 3 API 文檔 |

> **注意**：截至 2026-02-19，Lyria 3 尚無公開的 REST API 端點供開發者整合。目前僅可透過 Gemini App 和 YouTube Dream Track 使用。預計 Vertex AI 將陸續推出 `lyria-003` 端點。

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
  "https://us-central1-aiplatform.googleapis.com/v1/projects/MY_PROJECT/locations/us-central1/publishers/google/models/lyria-002:predict" \
  -d '{
    "instances": [{"prompt": "A calm acoustic folk song with gentle guitar"}],
    "parameters": {"sample_count": 2}
  }'
```

### 請求參數

| 參數 | 位置 | 類型 | 必填 | 說明 |
|---|---|---|---|---|
| `prompt` | `instances` | string | ✅ | 音樂描述（限英文） |
| `negative_prompt` | `instances` | string | ❌ | 排除不想要的元素 |
| `seed` | `instances` | int | ❌ | 用於重現結果，不可與 `sample_count` 並用 |
| `sample_count` | `parameters` | int | ❌ | 生成數量，不可與 `seed` 並用 |

### 請求範例

```json
{
  "instances": [
    {
      "prompt": "A calm acoustic folk song with a gentle guitar melody and soft strings.",
      "negative_prompt": "drums, electric guitar"
    }
  ],
  "parameters": {
    "sample_count": 2
  }
}
```

### 輸出格式

- 30 秒 WAV 音訊 (48 kHz)
- Base64 編碼於 JSON 回應中
- 僅限器樂（無人聲）

### 限制

- 僅支援英文 prompt
- 僅器樂輸出
- 30 秒固定長度
- 無 webhook 回呼機制

---

## 五、Lyria RealTime — Gemini API (實驗性)

### WebSocket 端點

```
wss://generativelanguage.googleapis.com/ws/google.ai.generativelanguage.v1alpha.GenerativeService.BidiGenerateMusic
```

### 認證

```python
from google import genai

# 使用 API Key
client = genai.Client(
    api_key="GEMINI_API_KEY",
    http_options={'api_version': 'v1alpha'}
)
```

### Python 程式碼範例

```python
import asyncio
from google import genai
from google.genai import types

client = genai.Client(
    api_key="GEMINI_API_KEY",
    http_options={'api_version': 'v1alpha'}
)

async def main():
    async with client.aio.live.music.connect(
        model='models/lyria-realtime-exp'
    ) as session:
        # 設定加權提示（可混合多種風格）
        await session.set_weighted_prompts(
            prompts=[
                types.WeightedPrompt(text='piano jazz', weight=0.6),
                types.WeightedPrompt(text='electronic ambient', weight=0.4),
            ]
        )

        # 設定音樂生成參數
        await session.set_music_generation_config(
            config=types.LiveMusicGenerationConfig(
                bpm=90,
                density=0.5,
                brightness=0.6,
                guidance=4.0,
                temperature=1.1,
                scale=types.Scale.D_MAJOR_B_MINOR,
            )
        )

        # 開始播放
        await session.play()

        # 接收音訊區塊
        async for message in session.receive():
            audio_data = message.server_content.audio_chunks[0].data
            # 處理 2 秒音訊區塊...

asyncio.run(main())
```

### 即時控制參數 (`LiveMusicGenerationConfig`)

| 參數 | 類型 | 範圍 | 預設值 | 說明 |
|---|---|---|---|---|
| `guidance` | float | 0.0 – 6.0 | 4.0 | 提示遵循強度（越高越忠實，但轉場更突兀） |
| `bpm` | int | 60 – 200 | — | 每分鐘拍數（需 reset context 生效） |
| `density` | float | 0.0 – 1.0 | — | 音符密度（低=稀疏，高=繁密） |
| `brightness` | float | 0.0 – 1.0 | — | 音色亮度（基於 log-mel 頻譜質心分析） |
| `scale` | Scale enum | — | — | 音階/調性（需 reset context 生效） |
| `temperature` | float | 0.0 – 3.0 | 1.1 | 隨機性/創意度 |
| `top_k` | int | 1 – 1000 | 40 | Top-K 取樣 |
| `seed` | int | 0 – 2,147,483,647 | 隨機 | 隨機種子 |

> **即時生效**：`density`、`brightness`、`guidance`、`temperature`
> **需 reset context**：`bpm`、`scale`

### 限制

- **實驗性** (`v1alpha`)：API 可能變動
- **僅器樂**：無人聲支援
- 需要客戶端實作音訊緩衝以確保播放流暢
- 不支援 Ephemeral Token（僅支援長期 API Key）

---

## 六、費用

| 方案 | 費用 | 說明 |
|---|---|---|
| **Lyria 3 (Gemini App)** | 免費 (有限額) | 付費訂閱 (AI Plus/Pro/Ultra) 有更高額度 |
| **Lyria 2 (Vertex AI)** | $0.06 / 30 秒 | 僅成功 (200) 回應計費；新帳號有 $300 試用額度 |
| **Lyria RealTime (Gemini API)** | 實驗性免費 | 目前免費使用，正式發布後預計收費 |

### 費用估算（以月 500 首 BGM 計算）

| 方案 | 月費 |
|---|---|
| Lyria 2 (Vertex AI) | $30 (500 × $0.06) |
| Mureka (已整合) | $60–75 (500 × $0.12–0.15/min) |
| MiniMax Music 2.5 | $2–17.50 |

---

## 七、與本專案整合評估

### 可行整合方案

#### 方案 A：Lyria 2 via Vertex AI (立即可用)

**優點**：
- 正式 REST API，文檔完整
- 本專案已有 Google Cloud 整合基礎 (GCP Terraform 部署)
- IP 賠償保障，企業級安全
- $0.06/30s 價格合理

**缺點**：
- 僅器樂，無人聲/歌詞
- 30 秒固定長度
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
- 豐富的即時控制參數
- 適合互動式音樂場景

**缺點**：
- 實驗性 API (`v1alpha`)，可能變動
- WebSocket 架構與現有 REST 模式不同
- 僅器樂
- 需實作音訊緩衝

**整合難度**：中 — 需要 WebSocket 客戶端及音訊串流處理

#### 方案 C：Lyria 3 (等待 API 公開)

**優點**：
- 全功能：人聲 + 歌詞 + 器樂
- 最高音質
- 多模態輸入
- 多語言支援

**缺點**：
- ⚠️ **尚無公開 API 端點**（僅 Gemini App / YouTube）
- 30 秒上限
- 預計 Vertex AI 將推出 `lyria-003`，但時間未定

**整合難度**：不可行（需等待 API 發布）

### 建議整合策略

1. **短期**：整合 **Lyria 2** (`lyria-002`) 作為純器樂 BGM 生成選項，補充 Mureka 的功能
2. **中期**：監控 **Lyria 3** Vertex AI API 發布狀態，一旦 `lyria-003` 端點公開即整合
3. **可選**：若有即時互動音樂需求，可評估 **Lyria RealTime** 實驗性 API

---

## 八、與現有方案比較

| 面向 | Google Lyria 2 | Google Lyria 3 | Mureka (已整合) | MiniMax Music 2.5 | ElevenLabs Music |
|---|---|---|---|---|---|
| API 狀態 | ✅ 正式 | ⏳ 等待公開 API | ✅ 正式 | ✅ 正式 | ✅ 正式 |
| 人聲 | ❌ | ✅ | ✅ | ✅ | ✅ |
| 歌詞 | ❌ | ✅ 自動生成 | ✅ 需提供 | ✅ | ✅ |
| 最大長度 | 30s | 30s | 5 min | 60s | 5 min |
| 多模態輸入 | ❌ | ✅ (文字+圖片+影片) | 部分 (文字+參考音訊) | 部分 (文字+參考音訊) | ✅ (文字+Composition Plan) |
| 即時串流 | ✅ (RealTime) | ❌ | ❌ | ❌ | ❌ |
| IP 保障 | ✅ 賠償保障 | ✅ SynthID | ❌ | ❌ | ❌ |
| 費用 | $0.06/30s | 免費 (有限額) | $0.12–0.15/min | $0.004–0.035/次 | Credit-based |
| 多語言 | ❌ (英文) | ✅ (8 種) | ✅ (10 種) | — | ✅ (多種) |
| 本專案整合 | 🔧 低難度 | ⏳ 等待 API | ✅ 已整合 | 🔧 低難度 | 🔧 低難度 |

---

## 九、結論與建議

### 核心發現

1. **Lyria 3 是重大突破**：首次在消費者級產品中提供完整的人聲+歌詞+器樂 AI 音樂生成，音質擬真度高，但**目前無公開開發者 API**。

2. **Lyria 2 立即可用**：透過 Vertex AI 提供穩定的 REST API，適合純器樂 BGM 場景，且本專案已有 GCP 基礎設施。

3. **Lyria RealTime 獨特定位**：即時串流音樂生成是獨特賣點，適合互動式應用，但仍處實驗階段。

### 建議

| 優先序 | 行動 | 理由 |
|---|---|---|
| 1️⃣ | **持續使用 Mureka** 作為主要音樂生成 provider | 已整合、5 分鐘長度、支援人聲和歌詞 |
| 2️⃣ | **整合 Lyria 2** 作為器樂 BGM 替代方案 | GCP 已有基礎設施、IP 賠償保障、$0.06/30s 低價 |
| 3️⃣ | **追蹤 Lyria 3 API 發布** | 一旦 `lyria-003` Vertex AI 端點公開，立即評估整合 |
| 4️⃣ | **評估 Lyria RealTime** 用於互動式場景 | 若產品需要即時音樂生成功能 |

---

## 來源

- [Google Blog — Lyria 3 公告](https://blog.google/innovation-and-ai/products/gemini-app/lyria-3/)
- [Google DeepMind — Lyria](https://deepmind.google/models/lyria/)
- [Gemini API — Music Generation (Lyria RealTime)](https://ai.google.dev/gemini-api/docs/music-generation)
- [Gemini API — Live Music WebSocket Reference](https://ai.google.dev/api/live_music)
- [Vertex AI — Lyria 音樂生成](https://docs.cloud.google.com/vertex-ai/generative-ai/docs/music/generate-music)
- [Vertex AI — Lyria API Reference](https://docs.cloud.google.com/vertex-ai/generative-ai/docs/model-reference/lyria-music-generation)
- [Vertex AI — Lyria 2 Model Card](https://docs.cloud.google.com/vertex-ai/generative-ai/docs/models/lyria/lyria-002)
- [Vertex AI — Lyria Prompt Guide](https://docs.cloud.google.com/vertex-ai/generative-ai/docs/music/music-gen-prompt-guide)
- [Vertex AI Pricing](https://cloud.google.com/vertex-ai/generative-ai/pricing)
- [TechCrunch — Google adds music-generation to Gemini](https://techcrunch.com/2026/02/18/google-adds-music-generation-capabilities-to-the-gemini-app/)
- [9to5Google — Gemini Lyria 3 rollout](https://9to5google.com/2026/02/18/gemini-app-music-lyria-3/)
- [MarkTechPost — Lyria 3 release](https://www.marktechpost.com/2026/02/18/google-deepmind-releases-lyria-3-an-advanced-music-generation-ai-model-that-turns-photos-and-text-into-custom-tracks-with-included-lyrics-and-vocals/)
- [Google Gemini Cookbook (GitHub)](https://github.com/google-gemini/cookbook)

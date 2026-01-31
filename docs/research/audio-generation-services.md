# 音效 (SFX) 與背景音樂 (BGM) 生成服務研究

> 研究日期: 2026-01-31

## 目錄

- [一、雲端 API 服務](#一雲端-api-服務)
  - [音效 (SFX)](#音效-sfx-生成)
  - [背景音樂 (BGM)](#背景音樂-bgm-生成)
- [二、開源模型 / 自架方案](#二開源模型--自架方案)
- [三、本專案現有整合](#三本專案現有整合)
- [四、推薦方案](#四推薦方案)

---

## 一、雲端 API 服務

### 音效 (SFX) 生成

| 服務 | API | 最大長度 | 音質 | 費用 | 商用授權 |
|---|---|---|---|---|---|
| **ElevenLabs SFX V2** | REST + Python/TS SDK | 30s | 48 kHz | ~200 credits/次 (免費 10k credits/月) | ✅ |
| **Stable Audio 2.5** | REST + Replicate/fal.ai | 3 min | 44.1 kHz stereo | ~$0.20/次 | ✅ |
| **CassetteAI** (fal.ai) | REST (queue-based + webhook) | 30s | 44.1 kHz | ~$0.20/次 | ✅ |
| **OptimizerAI** | REST + Discord | 60s | 44.1 kHz stereo | Freemium (免費額度) | ✅ |
| **SFX Engine** | Web + API | — | 標準 | Credit-based | ✅ |

**重點服務詳述：**

#### ElevenLabs SFX V2
- 本專案已整合 ElevenLabs TTS，加入 SFX 較為簡單
- V2 模型 (2025-09)：48 kHz, seamless looping, 30s max
- 支援自然語言 prompt 及音訊術語
- C2PA 內容簽章
- Docs: https://elevenlabs.io/docs/api-reference/text-to-sound-effects/convert

#### Stable Audio 2.5
- 同時支援 SFX + 音樂
- 有開源版本 (Stable Audio Open) 可自架
- 支援 audio-to-audio 變換及 audio inpainting
- 第三方託管：Replicate (~$0.20/track), fal.ai (~$0.20/次)

#### CassetteAI
- 特色：Video-to-SFX（自動為影片生成同步音效）
- 生成速度 ~1 秒
- Queue-based + webhook callback

---

### 背景音樂 (BGM) 生成

| 服務 | API | 最大長度 | 人聲 | 費用 | 商用授權 |
|---|---|---|---|---|---|
| **ElevenLabs Eleven Music** | REST + Python/TS SDK | 5 min | ✅ | Credit-based | ✅ (licensed data) |
| **Mureka** ⭐ 已整合 | REST + SDK + webhook | 5 min | ✅ | $0.12-0.15/min | ✅ |
| **Google Lyria 2** | Vertex AI REST | 30s | ❌ (純器樂) | $0.06/30s | ✅ + IP 賠償保障 |
| **MiniMax Music 2.5** | REST + fal.ai | 60s | ✅ | $0.004-0.035/次 | ✅ |
| **Mubert** | REST 3.0 + WebRTC | 25 min | ❌ | $0.01/min 串流 | ✅ (Pro+) |
| **Soundverse** | REST + SDK | 不限 | ✅ | $99+/月 | ✅ |
| **AIVA** | 有限 API | 不限 | ❌ | EUR 15-49/月 | ✅ (Pro) |
| Suno | ❌ 無官方 API | — | ✅ | 第三方 ~$0.04-0.14/call | ⚠️ 風險 |
| Udio | ❌ 無官方 API | — | ✅ | 第三方定價不一 | ⚠️ 風險 |

**重點服務詳述：**

#### ElevenLabs Eleven Music
- 與 SFX 同帳號/SDK，整合成本低
- Composition Plans (JSON) 精細控制段落（verse/chorus/bridge）
- Inpainting API 可局部編輯已生成曲目
- Stem Separation（人聲/伴奏分離）
- 多語言歌詞 (EN, ES, DE, JA 等)
- 5 分鐘最長、4,100 字 prompt

#### Google Lyria 2
- 透過 Vertex AI 或 Gemini API 存取
- 限 30 秒器樂片段
- SynthID 浮水印
- Google 提供 IP 侵權賠償保障
- 新用戶有 $300 免費額度

#### MiniMax Music 2.5
- 極低價格 ($0.004/次 via 直接 API)
- 免費層 10,000 credits/月
- 支援 reference track 風格學習
- 目前限 60 秒，計畫延長至 3 分鐘

#### Mubert
- 特色：即時串流 (WebRTC)
- 適合環境音樂、冥想、專注音樂
- 預生成 12,000+ 曲目庫 + 即時混音
- DJ mix 最長 25 分鐘

---

## 二、開源模型 / 自架方案

### 可商用授權 ✅

| 模型 | 用途 | 授權 | 最低 VRAM | 品質 | 維護狀態 |
|---|---|---|---|---|---|
| **ACE-Step v1.5** | 完整歌曲 + 人聲 | Apache 2.0 | <4 GB | 極高 | 非常活躍 |
| **AudioLDM 2** | SFX + 音樂 + 語音 | MIT | 8-12 GB | 很好 (SFX 尤佳) | 穩定 |
| **Bark** | 語音 + 基本 SFX/音樂 | MIT (含 weights) | 4-12 GB | 語音優秀，音樂普通 | 趨緩 |
| **Stable Audio Open** | SFX + 鼓點 + 環境音 | Community (<$1M) | 中等 | 很好 | 活躍 |
| **YuE** | 完整歌曲 + 人聲 | Apache 2.0 | 24-80 GB | 高 (接近 Suno) | 活躍 |
| **Amphion** | 語音 + 音樂 + 音訊 | MIT | 依模型 | 研究級 | 非常活躍 |
| **Google Magenta RT** | 即時互動音樂 | Apache 2.0 | TPU/GPU | 好 | 活躍 |

### 非商用 / 限制授權 ⚠️

| 模型 | 用途 | 授權 | 最低 VRAM | 備註 |
|---|---|---|---|---|
| **AudioCraft (MusicGen/AudioGen)** | 音樂 + SFX | CC-BY-NC 4.0 | 8 GB | 品質很高但不可商用 |
| **TangoFlux** | SFX + 環境音 | Non-commercial | ~8 GB | 30 秒/次，速度極快 |
| **Riffusion** | 音樂 loop | OpenRAIL-M | ~8 GB | 開源版已過時 |

**重點開源方案詳述：**

#### ACE-Step v1.5 (推薦)
- Apache 2.0 完全開放商用
- 消費級 GPU <4 GB VRAM 即可執行
- RTX 3090 上 <10 秒生成完整歌曲
- 支援 19 種語言、聲音複製、remix、分軌
- ComfyUI node 可用

#### AudioLDM 2 (SFX 推薦)
- MIT 授權（含 weights），商用無限制
- 基於 latent diffusion (類似 Stable Diffusion 但用於音訊)
- HuggingFace Diffusers 整合：
  ```python
  from diffusers import AudioLDM2Pipeline
  pipe = AudioLDM2Pipeline.from_pretrained("cvssp/audioldm2")
  pipe = pipe.to("cuda")
  audio = pipe("heavy rain with thunder").audios[0]
  ```
- 多個 checkpoint：general, 48k hi-fi, large

#### Meta AudioCraft (MusicGen + AudioGen)
- 品質出色但 **CC-BY-NC 4.0 不可商用**
- MusicGen: 音樂, AudioGen: 音效, EnCodec: 壓縮
  ```python
  from audiocraft.models import MusicGen
  model = MusicGen.get_pretrained('facebook/musicgen-small')
  model.set_generation_params(duration=8)
  wav = model.generate(['happy electronic dance music'])
  ```

---

## 三、本專案現有整合

| 類別 | 已整合服務 | 程式碼位置 |
|---|---|---|
| TTS | ElevenLabs, Azure, Google Cloud, Gemini, VoAI | `backend/src/infrastructure/providers/tts/` |
| STT | Azure, Google Cloud, OpenAI Whisper, Speechmatics | `backend/src/infrastructure/providers/stt/` |
| 音樂生成 | **Mureka** | `backend/src/infrastructure/adapters/mureka/` |
| SFX 生成 | ❌ 尚無 | — |
| BGM 生成 | 部分 (透過 Mureka) | — |

**架構模式**：Factory + Interface + Base class，新增 provider 只需：
1. 實作 interface / 繼承 base class
2. 在 factory 註冊
3. 加入 config 設定

---

## 四、推薦方案

### SFX 生成

| 優先序 | 方案 | 理由 |
|---|---|---|
| 1️⃣ | **ElevenLabs SFX V2** | 專案已有 ElevenLabs 整合，SDK 共用，48kHz 品質，商用安全 |
| 2️⃣ | **Stable Audio 2.5** (API) | SFX + 音樂雙用，有開源版可自架降成本 |
| 3️⃣ | **AudioLDM 2** (自架) | MIT 完全開放，自架零 API 費用，SFX 品質優異 |

### BGM 生成

| 優先序 | 方案 | 理由 |
|---|---|---|
| 1️⃣ | **Mureka** (已有) | 已整合，5 分鐘、200+ 風格、多模態輸入 |
| 2️⃣ | **ElevenLabs Eleven Music** | 與 SFX 同帳號，Composition Plans 精細控制 |
| 3️⃣ | **MiniMax Music 2.5** | 極低價 ($0.004/次)，適合大量生成場景 |
| 4️⃣ | **Google Lyria 2** | 企業級 + IP 賠償，但限 30 秒器樂 |
| 5️⃣ | **ACE-Step v1.5** (自架) | Apache 2.0，消費級 GPU 可跑，零 API 費用 |

### ⚠️ 不建議

- **Suno / Udio**：無官方 API，第三方 wrapper 有法律與穩定性風險
- **AudioCraft (MusicGen)**：CC-BY-NC 不可商用
- **TangoFlux**：僅限非商用/學術

---

## 附錄：費用粗估

假設月生成量 1,000 次 SFX + 500 次 BGM：

| 方案組合 | SFX 月費 | BGM 月費 | 合計 |
|---|---|---|---|
| ElevenLabs (SFX + Music) | ~$33 (Creator plan) | 含在同方案 | ~$33-99/月 |
| ElevenLabs SFX + Mureka BGM | ~$33 | ~$60-75 | ~$93-108/月 |
| Stable Audio + MiniMax | ~$200 | ~$2-17.5 | ~$202-218/月 |
| AudioLDM (自架) + ACE-Step (自架) | GPU 費用 | GPU 費用 | ~$50-200/月 (GPU) |

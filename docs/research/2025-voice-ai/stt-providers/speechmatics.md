# Speechmatics 深入研究

> 最後更新：2026-01

## 概述

Speechmatics 是英國劍橋的語音辨識公司，以自監督學習 (SSL) 技術著稱，特別在**兒童語音辨識**領域領先業界。

| 項目 | 說明 |
|------|------|
| 官網 | https://www.speechmatics.com |
| 文件 | https://docs.speechmatics.com |
| GitHub SDK | https://github.com/speechmatics/speechmatics-python |
| 狀態 | ✅ 生產推薦 (兒童語音最佳) |

---

## 版本與產品

| 產品 | 用途 | 特點 |
|------|------|------|
| Batch API | 批次轉錄 | 高準確度 |
| Real-time API | 即時串流 | 低延遲 |
| Speechmatics Flow | 整合方案 | STT + LLM + TTS |
| On-premises | 私有部署 | 容器化部署 |

---

## 定價

| 方案 | 價格 | 備註 |
|------|------|------|
| Free | 8 小時/月 | 免費試用 |
| Pay As You Grow (Batch) | $0.30/hour 起 | 依用量遞減 |
| Pay As You Grow (Real-time) | $1.04/hour 起 | 依用量遞減 |
| Enterprise | 客製 | 私有部署、SLA |

200+ 小時/月有批量折扣。

---

## API 串接

### 安裝 (新版 SDK - 2025+)

```bash
# 依需求安裝
pip install speechmatics-batch    # 批次轉錄
pip install speechmatics-rt       # 即時串流
pip install speechmatics-voice    # 語音助理
pip install speechmatics-tts      # 文字轉語音

# 或安裝舊版完整套件 (維護至 2025-12-31)
pip install speechmatics-python
```

### 批次轉錄

```python
from speechmatics.models import ConnectionSettings
from speechmatics.batch_client import BatchClient

settings = ConnectionSettings(
    url="https://asr.api.speechmatics.com/v2",
    auth_token="your-api-key"
)

with BatchClient(settings) as client:
    job_id = client.submit_job(
        audio="audio.mp3",
        transcription_config={
            "language": "zh",
            "diarization": "speaker",
            "operating_point": "enhanced"  # 或 "standard"
        }
    )

    transcript = client.wait_for_completion(job_id)
    print(transcript)
```

### 即時串流

```python
import asyncio
from speechmatics.models import ConnectionSettings, TranscriptionConfig
from speechmatics import WebsocketClient

settings = ConnectionSettings(
    url="wss://eu2.rt.speechmatics.com/v2",
    auth_token="your-api-key"
)

config = TranscriptionConfig(
    language="zh",
    enable_partials=True,
    max_delay=2.0  # 延遲與準確度權衡
)

async def transcribe():
    async with WebsocketClient(settings) as client:
        await client.run(
            audio="audio.wav",
            transcription_config=config
        )

asyncio.run(transcribe())
```

### 麥克風即時轉錄

```python
import pyaudio
from speechmatics.client import WebsocketClient
from speechmatics.models import AudioSettings, TranscriptionConfig

audio_settings = AudioSettings(
    encoding="pcm_s16le",
    sample_rate=16000,
    chunk_size=1024
)

config = TranscriptionConfig(
    language="en",
    enable_partials=True
)

def on_transcript(msg):
    if msg["message"] == "AddTranscript":
        print(msg["metadata"]["transcript"])

client = WebsocketClient(settings)
client.add_event_handler("AddTranscript", on_transcript)

# 使用 pyaudio 串流麥克風
p = pyaudio.PyAudio()
stream = p.open(format=pyaudio.paInt16, channels=1, rate=16000, input=True)

client.run_synchronously(stream, config, audio_settings)
```

---

## 🧒 兒童語音辨識深入解析

Speechmatics 在兒童語音辨識領域是業界公認的領導者，這是他們的核心競爭優勢。

### 為什麼兒童語音辨識困難？

| 挑戰 | 說明 |
|------|------|
| **音高差異** | 兒童聲音頻率較高，與成人差異大 |
| **發音模式不同** | 兒童會過度強調、斷句方式不同、節奏不規律 |
| **詞彙發展中** | 持續學習新詞彙，發音不穩定 |
| **訓練數據稀缺** | 傳統 ASR 訓練數據以成人為主 |

### SSL 技術突破

Speechmatics 使用**自監督學習 (Self-Supervised Learning, SSL)** 技術突破兒童語音辨識瓶頸：

| 指標 | SSL 之前 | SSL 之後 |
|------|----------|----------|
| 訓練音訊時數 | 30,000 小時 | **1,100,000 小時** |
| 資料來源 | 標註資料（主要成人） | 網路未標註資料（含大量兒童） |
| 兒童語音樣本 | 極少 | **指數級增長** |

> SSL 技術允許從未標註的網路音訊（如社群媒體、Podcast）中學習，大幅增加兒童語音樣本覆蓋率。

### 準確度基準測試（Common Voice 資料集）

| 提供商 | 兒童語音準確度 | 與 Speechmatics 差距 |
|--------|---------------|---------------------|
| **Speechmatics** | **91.8%** ⭐ | - |
| Google | 83.4% | -8.4% |
| Deepgram | 82.3% | -9.5% |
| Amazon | ~80% | ~-12% |
| Microsoft | ~79% | ~-13% |

### ⚠️ 重要限制：無專用兒童模式 API 參數

**Speechmatics 沒有提供專門針對「兒童語音」的 API 參數或開關。**

兒童語音辨識的優異表現來自於：
1. 模型訓練層面的改進（SSL 技術）
2. 核心模型本身已包含兒童語音能力
3. 無需額外設定即可享受兒童語音優化

這意味著：
- ✅ 使用標準 API 即可獲得最佳兒童語音辨識效果
- ✅ 不需要指定特殊模式或參數
- ❌ 無法針對「純兒童場景」進一步調優
- ❌ 無法取得兒童 vs 成人的區分標記

---

## 🇹🇼 中文支援詳解

### 語言代碼

| 語言 | 代碼 | 說明 |
|------|------|------|
| 普通話 (Mandarin) | `cmn` | 主要中文支援 |
| 粵語 (Cantonese) | `yue` | 廣東話 |

### 口音覆蓋

Speechmatics 的 `cmn` 語言包採用**全球優先 (Global-First)** 方法，單一語言包支援多種口音：

- 🇨🇳 中國大陸
- 🇹🇼 台灣
- 🇸🇬 新加坡
- 🇲🇾 馬來西亞
- 其他華語地區

> 不需要針對不同口音選擇不同模型，系統會自動適應。

### 輸出字元設定

可透過 `output_locale` 參數控制輸出繁體或簡體字：

```python
transcription_config = {
    "language": "cmn",
    "output_locale": "cmn-Hant",  # 繁體中文
    # "output_locale": "cmn-Hans",  # 簡體中文
}
```

| output_locale | 說明 |
|---------------|------|
| `cmn-Hant` | 繁體中文輸出 |
| `cmn-Hans` | 簡體中文輸出 |
| 未指定 | 系統預設（通常簡體） |

### 雙語/多語包

適合中英混雜或多語環境：

| 語言包代碼 | 支援語言 | 適用場景 |
|------------|----------|----------|
| `cmn_en` | 中文 + 英文 | 中英混雜對話、會議 |
| `cmn_en_ms_ta` | 中文 + 英文 + 馬來文 + 坦米爾文 | 新加坡/馬來西亞多語環境 |

```python
# 中英雙語設定範例
transcription_config = {
    "language": "cmn_en",  # 自動識別中英混雜
    "operating_point": "enhanced",
}
```

### 中文兒童語音辨識現況

| 項目 | 狀態 | 說明 |
|------|------|------|
| 中文兒童語音支援 | ⚠️ 未明確公開 | 官方基準測試主要針對英語兒童 |
| 預期效果 | 🔶 應優於競品 | SSL 技術對所有語言都有幫助 |
| 官方數據 | ❌ 無 | 91.8% 準確度數據來自英語 Common Voice |

**建議：** 如需中文兒童語音辨識，建議：
1. 先使用免費額度進行實際測試
2. 聯繫 Speechmatics 銷售團隊詢問中文兒童語音基準數據
3. 使用 `enhanced` operating point 以獲得最佳準確度

---

## ⚙️ 兒童語音最佳化 API 設定

雖然沒有專用兒童參數，但以下設定可最大化兒童語音辨識效果：

### 建議配置

```python
# 兒童語音最佳化設定（中文）
transcription_config = {
    "language": "cmn",                    # 中文
    "output_locale": "cmn-Hant",          # 繁體輸出（台灣）
    "operating_point": "enhanced",        # ⭐ 強烈建議：最高準確度
    "diarization": "speaker",             # 多人場景可區分說話者
    "enable_entities": True,              # 實體辨識（數字、日期等）
    "punctuation_overrides": {
        "permitted_marks": ["。", "，", "？", "！"]  # 中文標點
    }
}
```

### operating_point 參數詳解

| 值 | 準確度 | 速度 | 價格 | 建議場景 |
|----|--------|------|------|----------|
| `standard` | 標準 | 較快 | 標準價 | 一般成人語音、低延遲需求 |
| `enhanced` | **最高** ⭐ | 較慢 | 加價 | **兒童語音**、噪音環境、多元口音 |

> **兒童語音強烈建議使用 `enhanced`**：在複雜音訊（噪音環境、多元口音）下表現更好

### 即時串流設定（教室/互動場景）

```python
# 即時兒童語音辨識設定
realtime_config = {
    "language": "cmn",
    "operating_point": "enhanced",
    "enable_partials": True,              # 顯示部分結果（即時回饋）
    "max_delay": 2.0,                     # 延遲容忍度（秒）
    "max_delay_mode": "flexible",         # 彈性延遲模式
}
```

| 參數 | 說明 | 兒童場景建議 |
|------|------|-------------|
| `enable_partials` | 顯示中間結果 | `True` - 提供即時回饋 |
| `max_delay` | 最大延遲秒數 | `2.0` - 平衡準確度與即時性 |
| `max_delay_mode` | 延遲模式 | `flexible` - 允許系統優化 |

### 自訂詞彙（提高特定詞彙辨識率）

兒童教育場景常有特定詞彙，可透過 `additional_vocab` 提高辨識率：

```python
transcription_config = {
    "language": "cmn",
    "operating_point": "enhanced",
    "additional_vocab": [
        {"content": "ㄅㄆㄇ"},           # 注音符號
        {"content": "九九乘法表"},
        {"content": "小明"},              # 常見人名
        {"content": "老師好"},
        {
            "content": "Speechmatics",
            "sounds_like": ["史比馬提克斯"]  # 外來語發音提示
        }
    ]
}
```

---

## 功能特點

### ✅ 優點

1. **🏆 兒童語音辨識業界最佳**
   - 91.8% 準確度 (vs Google 83.4%, Deepgram 82.3%)
   - 使用自監督學習 (SSL) 技術突破

2. **噪音環境表現優異**
   - 教室、公共場所等環境
   - 遠超競品的抗噪能力

3. **多元口音支援**
   - 非裔美國人語音準確度提升 45%
   - 廣泛方言和口音覆蓋

4. **50+ 語言支援**
   - 商業語言全面覆蓋
   - 持續新增中

5. **彈性部署**
   - 雲端、本地、混合部署
   - 企業資料安全需求

6. **優質客戶支援**
   - 評價普遍稱讚支援團隊
   - 協作式客戶服務

7. **醫療場景優化**
   - 醫療聽寫錯誤率降至 1%
   - 對話捕捉準確度高

### ❌ 缺點

1. **即時延遲問題**
   - 在語音助理場景 latency 較高
   - 相比 Deepgram 不適合即時對話

2. **整合語言限制**
   - 僅支援 Python, JavaScript, .Net, Rust
   - 部分用戶覺得不足

3. **輸出格式限制**
   - PDF 無法編輯
   - 無 Word 輸出選項

4. **無完成通知**
   - 需手動刷新檢查狀態

5. **定價較高**
   - 即時版 $1.04/hr 起
   - 相比競品偏貴

6. **100% 準確度不可能**
   - 背景噪音、含糊發音仍需人工校正

---

## 網路評價

### 評分彙整

| 來源 | 評分 | 評論數 |
|------|------|--------|
| G2 | 4.5/5 ⭐ | 42+ |
| Software Advice | 96% 滿意度 | - |
| Capterra | 正面 | - |

### 常見評價

**正面:**
- "兒童語音辨識遠超任何競品"
- "支援團隊非常專業且即時"
- "噪音環境下表現令人印象深刻"
- "醫療聽寫準確度大幅提升"

**負面:**
- "即時版延遲在語音助理場景不夠理想"
- "價格相對較高"
- "需要人工校正的情況還是存在"

---

## 與競品比較

| 項目 | Speechmatics | Deepgram | AssemblyAI |
|------|--------------|----------|------------|
| 兒童語音 | 91.8% ⭐ | 82.3% | - |
| 即時延遲 | 較高 | ~100ms ⭐ | ~300ms |
| 批次定價/hr | $0.30 | ~$0.26 | $0.15 ⭐ |
| 即時定價/hr | $1.04 | - | - |
| 私有部署 | ✅ | ❌ | ❌ |
| 語言數 | 50+ | 36+ | 100+ |

---

## 適用場景

| 場景 | 適合度 | 說明 |
|------|--------|------|
| 兒童教育 / eLearning | ⭐⭐⭐⭐⭐ | 業界最佳 |
| 噪音環境 (教室) | ⭐⭐⭐⭐⭐ | 抗噪能力強 |
| 醫療聽寫 | ⭐⭐⭐⭐⭐ | 1% 錯誤率 |
| 多元口音環境 | ⭐⭐⭐⭐⭐ | 口音覆蓋廣 |
| 私有部署需求 | ⭐⭐⭐⭐ | 支援本地部署 |
| 即時語音助理 | ⭐⭐⭐ | 延遲較高 |
| 預算有限 | ⭐⭐ | 定價較高 |

---

## 參考連結

### 官方資源
- [官方文件](https://docs.speechmatics.com)
- [Python SDK](https://github.com/speechmatics/speechmatics-python)
- [Speechmatics Academy](https://www.speechmatics.com/developers)
- [支援語言列表](https://docs.speechmatics.com/speech-to-text/languages)
- [API 參考](https://docs.speechmatics.com/api-ref)

### 兒童語音相關
- [兒童語音研究文章](https://www.speechmatics.com/company/articles-and-news/understanding-childrens-voices-how-voice-to-text-assists-elearning)
- [SSL 技術突破公告](https://www.speechmatics.com/company/articles-and-news/breakthrough-ai-bias-inclusion)
- [SSL 技術說明](https://www.speechmatics.com/company/articles-and-news/boosting-sample-efficiency-through-self-supervised-learning)

### 評價與比較
- [G2 評價](https://www.g2.com/products/speechmatics/reviews)

---

## 更新追蹤

| 日期 | 事件 |
|------|------|
| 2021-10 | Autonomous Speech Recognition 發布，SSL 技術導入 |
| 2021-10 | 兒童語音 91.8% 準確度達成（Common Voice 基準） |
| 2024 | Speechmatics Flow 發布 (STT + LLM + TTS) |
| 2024 | Ursa 2 模型發布，支援 50+ 語言 |
| 2025 | 新版 Python SDK 發布 (分包架構) |
| 2026-01 | 新增兒童語音辨識深入解析與中文支援章節 |

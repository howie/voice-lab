# Research: Speechmatics 兒童語音辨識整合

**Date**: 2026-01-20
**Feature Branch**: `003-stt-testing-module`
**目標**: 整合 Speechmatics STT provider 以測試中文兒童語音辨識

---

## 研究摘要

### 為什麼選擇 Speechmatics？

Speechmatics 在兒童語音辨識領域是**業界公認的領導者**：

| 提供商 | 兒童語音準確度 | 資料來源 |
|--------|---------------|----------|
| **Speechmatics** | **91.8%** ⭐ | Common Voice |
| Google | 83.4% | Common Voice |
| Deepgram | 82.3% | Common Voice |
| Amazon | ~80% | 估計 |
| Microsoft | ~79% | 估計 |

> 來源: [Speechmatics SSL 技術突破公告](https://www.speechmatics.com/company/articles-and-news/breakthrough-ai-bias-inclusion) (2021-10)

---

## 技術原理：為什麼 Speechmatics 兒童語音辨識更好？

### 兒童語音辨識的挑戰

| 挑戰 | 說明 |
|------|------|
| 音高差異 | 兒童聲音頻率較高，與成人差異大 |
| 發音模式不同 | 兒童會過度強調、斷句方式不同、節奏不規律 |
| 詞彙發展中 | 持續學習新詞彙，發音不穩定 |
| 訓練數據稀缺 | 傳統 ASR 訓練數據以成人為主 |

### SSL (Self-Supervised Learning) 技術突破

Speechmatics 使用自監督學習技術突破瓶頸：

| 指標 | SSL 之前 | SSL 之後 |
|------|----------|----------|
| 訓練音訊時數 | 30,000 小時 | **1,100,000 小時** |
| 資料來源 | 標註資料（主要成人） | 網路未標註資料（含大量兒童） |
| 兒童語音樣本 | 極少 | 指數級增長 |

---

## 重要發現：無專用兒童模式 API

### ⚠️ 關鍵限制

**Speechmatics 沒有提供專門針對「兒童語音」的 API 參數或開關。**

兒童語音辨識的優異表現來自於：
1. 模型訓練層面的改進（SSL 技術）
2. 核心模型本身已包含兒童語音能力
3. 無需額外設定即可享受兒童語音優化

### 實作意涵

| 項目 | 狀態 | 說明 |
|------|------|------|
| 專用 `child_mode` 參數 | ❌ 不存在 | Speechmatics API 無此參數 |
| 使用標準 API | ✅ 即可 | 模型本身已優化兒童語音 |
| `operating_point: enhanced` | ✅ 建議 | 最高準確度，適合複雜音訊 |

---

## 中文支援詳情

### 語言代碼

| 語言 | Speechmatics 代碼 | 我們的代碼 |
|------|-------------------|-----------|
| 普通話 (Mandarin) | `cmn` | `zh-TW`, `zh-CN` |
| 粵語 (Cantonese) | `yue` | 未支援 |

### 口音覆蓋

Speechmatics 的 `cmn` 語言包採用 **Global-First** 方法，單一語言包支援：
- 🇨🇳 中國大陸
- 🇹🇼 台灣
- 🇸🇬 新加坡
- 🇲🇾 馬來西亞

### 輸出字元設定

可透過 `output_locale` 控制輸出繁體或簡體：

```python
transcription_config = {
    "language": "cmn",
    "output_locale": "cmn-Hant",  # 繁體中文
    # "output_locale": "cmn-Hans",  # 簡體中文
}
```

### 中文兒童語音準確度

| 項目 | 狀態 | 說明 |
|------|------|------|
| 官方中文兒童語音數據 | ❌ 無 | 91.8% 來自英語 Common Voice |
| 預期效果 | 🔶 應優於競品 | SSL 技術對所有語言都有幫助 |
| 建議 | ⚠️ 需實測驗證 | 使用免費額度測試 |

---

## API 參數研究

### transcription_config 可用參數

| 參數 | 類型 | 說明 | 兒童場景建議 |
|------|------|------|-------------|
| `language` | string | 語言代碼 | `cmn` |
| `operating_point` | string | `standard` 或 `enhanced` | **`enhanced`** ⭐ |
| `output_locale` | string | 輸出字元 | `cmn-Hant` (繁體) |
| `diarization` | string | 說話者分離 | `none` 或 `speaker` |
| `enable_entities` | bool | 實體辨識 | `true` |
| `additional_vocab` | list | 自訂詞彙 | 兒童常用詞 |

### operating_point 選擇

| 值 | 準確度 | 速度 | 價格 | 建議場景 |
|----|--------|------|------|----------|
| `standard` | 標準 | 較快 | 標準價 | 一般成人語音 |
| `enhanced` | **最高** ⭐ | 較慢 | 加價 | **兒童語音**、噪音環境 |

### additional_vocab 範例（兒童場景）

```python
additional_vocab = [
    {"content": "媽媽"},
    {"content": "爸爸"},
    {"content": "老師"},
    {"content": "小朋友"},
    {"content": "ㄅㄆㄇ"},
    {"content": "九九乘法表"},
]
```

---

## 實作計畫

### 現有程式碼狀態

| 檔案 | 狀態 | 說明 |
|------|------|------|
| `speechmatics_stt.py` | ✅ 已存在 | 但 `supports_child_mode = False` |
| `factory.py` | ⚠️ 已註解 | Speechmatics 目前停用 |

### 需要修改的項目

#### 1. `speechmatics_stt.py`

```python
# 變更 1: 啟用兒童模式支援
@property
def supports_child_mode(self) -> bool:
    return True  # 改為 True

# 變更 2: 兒童模式優化設定
config = {
    "type": "transcription",
    "transcription_config": {
        "language": self._map_language(request.language),
        "operating_point": "enhanced",
        "output_locale": self._get_output_locale(request.language),  # 新增
        # 兒童模式時添加常用詞彙
        **({"additional_vocab": CHILD_VOCAB} if request.child_mode else {}),
    },
}
```

#### 2. `factory.py`

```python
# 取消註解 import
from src.infrastructure.providers.stt.speechmatics_stt import SpeechmaticsSTTProvider

# 取消註解 create 方法中的 speechmatics case
elif provider_name == "speechmatics":
    return cls._create_speechmatics(credentials)

# 更新 PROVIDER_INFO
"speechmatics": {
    ...
    "supports_child_mode": True,  # 改為 True
}
```

---

## 測試計畫

### 測試案例

| 測試案例 | 音檔類型 | 預期結果 |
|----------|----------|----------|
| 成人中文語音 | 標準錄音 | 基準準確度 |
| 兒童中文語音 (6-10歲) | 清晰發音 | 應優於 Azure/GCP |
| 兒童中文語音 (3-5歲) | 稚嫩發音 | 評估可用性 |
| 教室環境兒童語音 | 有背景噪音 | 測試抗噪能力 |

### WER/CER 比較基準

需收集中文兒童語音測試集，與以下 provider 比較：
- Azure Speech Services (child_mode)
- Google Cloud STT (child_mode)
- OpenAI Whisper
- **Speechmatics** (enhanced)

---

## 風險與限制

| 風險 | 影響 | 緩解措施 |
|------|------|----------|
| 中文兒童準確度未知 | 可能不如預期 | 先用免費額度測試 |
| 無專用兒童參數 | 無法進一步調優 | 使用 additional_vocab 補償 |
| SDK 相容性 | 可能有問題 | 已有基礎實現可驗證 |
| 定價較高 | 成本考量 | 僅用於準確度要求高的場景 |

---

## 參考資源

- [Speechmatics 官方文檔](https://docs.speechmatics.com)
- [兒童語音研究文章](https://www.speechmatics.com/company/articles-and-news/understanding-childrens-voices-how-voice-to-text-assists-elearning)
- [SSL 技術突破公告](https://www.speechmatics.com/company/articles-and-news/breakthrough-ai-bias-inclusion)
- [支援語言列表](https://docs.speechmatics.com/speech-to-text/languages)
- [整合指南](../../integrations/speechmatics.md)
- [深入研究](../../research/2025-voice-ai/stt-providers/speechmatics.md)

---

## 結論

1. **Speechmatics 是兒童語音辨識的最佳選擇**（英語基準 91.8%）
2. **中文兒童語音效果需實測驗證**（無官方數據）
3. **無專用兒童 API 參數**，但核心模型已優化
4. **建議使用 `enhanced` operating point** 以獲得最佳準確度
5. **可透過 `additional_vocab` 提高特定詞彙辨識率**

---

*Last updated: 2026-01-20*

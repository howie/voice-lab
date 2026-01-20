# ElevenLabs Integration

ElevenLabs 是專注於高品質 AI 語音合成的服務，以自然語調、情感表達和語音克隆技術聞名。

## Step 1: 建立 ElevenLabs 帳戶

1. 前往 [ElevenLabs](https://elevenlabs.io/)

2. 點擊「**Sign Up**」註冊

3. 可使用 Google 帳號或 Email 註冊

4. 免費帳戶每月提供 10,000 字元額度

## Step 2: 取得 API Key

1. 登入 [ElevenLabs](https://elevenlabs.io/)

2. 點擊右上角的個人頭像

3. 選擇「**Profile + API key**」

4. 在 API Key 區塊，點擊眼睛圖示顯示 API Key

5. 點擊複製圖示複製 API Key

或直接前往：[https://elevenlabs.io/app/settings/api-keys](https://elevenlabs.io/app/settings/api-keys)

## Step 3: 設定環境變數

```bash
# .env
ELEVENLABS_API_KEY=your_api_key_here
```

## API 使用方式

### REST API 端點

| 服務 | 端點 |
|------|------|
| 語音合成 | `https://api.elevenlabs.io/v1/text-to-speech/{voice_id}` |
| 語音合成（串流） | `https://api.elevenlabs.io/v1/text-to-speech/{voice_id}/stream` |
| 語音列表 | `https://api.elevenlabs.io/v1/voices` |
| 模型列表 | `https://api.elevenlabs.io/v1/models` |
| 用量查詢 | `https://api.elevenlabs.io/v1/user/subscription` |

### 認證方式

使用 `xi-api-key` header：

```bash
curl -X GET "https://api.elevenlabs.io/v1/voices" \
  -H "xi-api-key: YOUR_API_KEY"
```

## 實作範例

### Python (elevenlabs SDK)

```python
from elevenlabs import ElevenLabs

def elevenlabs_tts(text: str, voice_id: str = "21m00Tcm4TlvDq8ikWAM"):
    """ElevenLabs TTS synthesis using SDK."""
    client = ElevenLabs(api_key="YOUR_API_KEY")

    audio = client.text_to_speech.convert(
        voice_id=voice_id,
        text=text,
        model_id="eleven_multilingual_v2",
        output_format="mp3_44100_128",
    )

    # audio 是一個 generator，需要讀取所有 chunks
    audio_bytes = b"".join(audio)
    return audio_bytes
```

### Python (REST API with httpx)

```python
import httpx

async def elevenlabs_tts_rest(
    text: str,
    voice_id: str = "21m00Tcm4TlvDq8ikWAM",
):
    """ElevenLabs TTS synthesis using REST API."""
    url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"

    headers = {
        "xi-api-key": "YOUR_API_KEY",
        "Content-Type": "application/json",
    }

    body = {
        "text": text,
        "model_id": "eleven_multilingual_v2",
        "voice_settings": {
            "stability": 0.5,
            "similarity_boost": 0.75,
            "style": 0.0,
            "use_speaker_boost": True,
        },
    }

    async with httpx.AsyncClient() as client:
        response = await client.post(url, headers=headers, json=body)
        response.raise_for_status()
        return response.content  # MP3 audio data
```

### Python (串流)

```python
import httpx

async def elevenlabs_tts_stream(
    text: str,
    voice_id: str = "21m00Tcm4TlvDq8ikWAM",
):
    """ElevenLabs TTS streaming synthesis."""
    url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}/stream"

    headers = {
        "xi-api-key": "YOUR_API_KEY",
        "Content-Type": "application/json",
    }

    body = {
        "text": text,
        "model_id": "eleven_multilingual_v2",
        "voice_settings": {
            "stability": 0.5,
            "similarity_boost": 0.75,
        },
    }

    async with httpx.AsyncClient() as client:
        async with client.stream("POST", url, headers=headers, json=body) as response:
            async for chunk in response.aiter_bytes():
                yield chunk  # 即時串流音訊 chunks
```

### cURL

```bash
curl -X POST \
  "https://api.elevenlabs.io/v1/text-to-speech/21m00Tcm4TlvDq8ikWAM" \
  -H "xi-api-key: YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "text": "你好，這是 ElevenLabs 語音測試。",
    "model_id": "eleven_multilingual_v2",
    "voice_settings": {
      "stability": 0.5,
      "similarity_boost": 0.75
    }
  }' \
  --output voice.mp3
```

## 模型選擇

| 模型 ID | 名稱 | 特色 | 延遲 |
|---------|------|------|------|
| `eleven_multilingual_v2` | Multilingual v2 | 29 種語言、最自然 | 中等 |
| `eleven_turbo_v2_5` | Turbo v2.5 | 32 種語言、低延遲 | 低 |
| `eleven_turbo_v2` | Turbo v2 | 英語優化、最低延遲 | 最低 |
| `eleven_monolingual_v1` | English v1 | 僅英語、經典模型 | 低 |

> 推薦：中文使用 `eleven_multilingual_v2` 或 `eleven_turbo_v2_5`

## 預設語音

### 取得語音列表

```bash
curl "https://api.elevenlabs.io/v1/voices" \
  -H "xi-api-key: YOUR_API_KEY" \
  | jq '.voices[] | {voice_id, name, labels}'
```

### 常用預設語音

| Voice ID | 名稱 | 性別 | 特色 |
|----------|------|------|------|
| `21m00Tcm4TlvDq8ikWAM` | Rachel | 女聲 | 美式英語、平靜 |
| `AZnzlk1XvdvUeBnXmlld` | Domi | 女聲 | 有力、自信 |
| `EXAVITQu4vr4xnSDxMaL` | Bella | 女聲 | 柔和、敘事 |
| `ErXwobaYiN019PkySvjV` | Antoni | 男聲 | 溫暖、友善 |
| `MF3mGyEYCl7XYWbV9V6O` | Elli | 女聲 | 年輕、活潑 |
| `TxGEqnHWrfWFTfGW9XjX` | Josh | 男聲 | 深沉、敘事 |
| `VR6AewLTigWG4xSOukaG` | Arnold | 男聲 | 有力、權威 |
| `pNInz6obpgDQGcFmaJgB` | Adam | 男聲 | 深沉、旁白 |
| `yoZ06aMxZJJ28mfd3POQ` | Sam | 男聲 | 沙啞、動態 |

## 語音設定參數

| 參數 | 範圍 | 預設 | 說明 |
|------|------|------|------|
| `stability` | 0.0 - 1.0 | 0.5 | 穩定性。較低 = 更有表情變化；較高 = 更一致 |
| `similarity_boost` | 0.0 - 1.0 | 0.75 | 相似度。較高 = 更接近原始語音 |
| `style` | 0.0 - 1.0 | 0.0 | 風格強度。較高 = 更誇張（僅 v2 模型） |
| `use_speaker_boost` | boolean | true | 增強語音清晰度 |

### 參數建議

| 使用場景 | stability | similarity_boost | style |
|----------|-----------|------------------|-------|
| 旁白、有聲書 | 0.7 | 0.8 | 0.0 |
| 對話、角色扮演 | 0.3 | 0.7 | 0.5 |
| 新聞播報 | 0.8 | 0.9 | 0.0 |
| 廣告、行銷 | 0.5 | 0.75 | 0.3 |

## 音訊輸出格式

| 格式 | `output_format` 值 | 說明 |
|------|-------------------|------|
| MP3 44.1kHz 128kbps | `mp3_44100_128` | 預設，高品質 |
| MP3 44.1kHz 64kbps | `mp3_44100_64` | 較小檔案 |
| MP3 44.1kHz 32kbps | `mp3_44100_32` | 最小檔案 |
| MP3 22.05kHz 32kbps | `mp3_22050_32` | 低品質 |
| PCM 16kHz | `pcm_16000` | 原始音訊 |
| PCM 22.05kHz | `pcm_22050` | 原始音訊 |
| PCM 24kHz | `pcm_24000` | 原始音訊 |
| PCM 44.1kHz | `pcm_44100` | 最高品質原始 |
| μ-law 8kHz | `ulaw_8000` | 電話品質 |

## 定價方案

| 方案 | 價格 | 字元配額/月 | 特色 |
|------|------|------------|------|
| **Free** | $0 | 10,000 | 基本功能 |
| **Starter** | $5 | 30,000 | 商業授權 |
| **Creator** | $22 | 100,000 | 專業語音克隆 |
| **Pro** | $99 | 500,000 | 高用量、優先支援 |
| **Scale** | $330 | 2,000,000 | 企業級 |

## 配額與限制

| 限制項目 | Free | Starter | Creator+ |
|----------|------|---------|----------|
| 每次請求最大字元數 | 2,500 | 5,000 | 10,000 |
| 並行請求數 | 2 | 3 | 5+ |
| 語音克隆 | 3 個 | 10 個 | 30+ 個 |

## 查詢用量

```bash
curl "https://api.elevenlabs.io/v1/user/subscription" \
  -H "xi-api-key: YOUR_API_KEY" \
  | jq '{character_count, character_limit, next_reset}'
```

## 進階功能

### 語音克隆（Voice Cloning）

上傳音訊樣本建立自訂語音：

```bash
curl -X POST "https://api.elevenlabs.io/v1/voices/add" \
  -H "xi-api-key: YOUR_API_KEY" \
  -F "name=My Custom Voice" \
  -F "files=@sample1.mp3" \
  -F "files=@sample2.mp3" \
  -F "description=Custom cloned voice"
```

### Projects API（長篇內容）

適合有聲書、Podcast 等長篇內容製作。

## 故障排除

### 常見錯誤

| 錯誤代碼 | 說明 | 解決方案 |
|----------|------|----------|
| `401` | 認證失敗 | 檢查 API Key 是否正確 |
| `422` | 參數錯誤 | 檢查 voice_id、model_id 是否有效 |
| `429` | 請求過多或配額用盡 | 降低請求頻率或升級方案 |

### 驗證設定

```bash
# 測試 API Key 是否有效
curl "https://api.elevenlabs.io/v1/user" \
  -H "xi-api-key: YOUR_API_KEY"

# 檢查配額
curl "https://api.elevenlabs.io/v1/user/subscription" \
  -H "xi-api-key: YOUR_API_KEY" \
  | jq '{character_count, character_limit}'
```

### 語音 ID 查詢

如果不確定 voice_id：

```bash
# 列出所有可用語音
curl "https://api.elevenlabs.io/v1/voices" \
  -H "xi-api-key: YOUR_API_KEY" \
  | jq '.voices[] | {voice_id, name}'
```

## 相關資源

- [ElevenLabs 官網](https://elevenlabs.io/)
- [API 文檔](https://elevenlabs.io/docs/api-reference)
- [Python SDK](https://github.com/elevenlabs/elevenlabs-python)
- [定價資訊](https://elevenlabs.io/pricing)
- [語音庫](https://elevenlabs.io/voice-library)
- [Discord 社群](https://discord.gg/elevenlabs)

---

*Last updated: 2026-01-20*

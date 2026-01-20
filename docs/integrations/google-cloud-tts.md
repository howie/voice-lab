# Google Cloud Text-to-Speech Integration

Google Cloud Text-to-Speech 是 Google 提供的語音合成服務，支援多語言和 WaveNet 高品質語音。

## Step 1: 建立 Google Cloud 帳戶

1. 前往 [Google Cloud Console](https://console.cloud.google.com/)
2. 如果沒有帳戶，使用 Google 帳號登入並註冊
3. 新帳戶可獲得 $300 美元免費額度（90 天內使用）

## Step 2: 建立專案

### 透過 Cloud Console

1. 登入 [Google Cloud Console](https://console.cloud.google.com/)

2. 點擊頂部的專案下拉選單

3. 點擊「**新增專案**」(New Project)

4. 填寫專案資訊：

   | 欄位 | 說明 | 建議值 |
   |------|------|--------|
   | **專案名稱** (Project name) | 專案的顯示名稱 | `voice-lab` |
   | **專案 ID** (Project ID) | 全域唯一識別碼 | `voice-lab-xxxxx` (自動產生) |
   | **機構** (Organization) | 選擇機構（可選） | 依情況選擇 |

5. 點擊「**建立**」(Create)

6. 等待專案建立完成

### 透過 gcloud CLI

```bash
# 登入 Google Cloud
gcloud auth login

# 建立專案
gcloud projects create voice-lab-project \
  --name="Voice Lab"

# 設定預設專案
gcloud config set project voice-lab-project
```

## Step 3: 啟用 Text-to-Speech API

### 透過 Cloud Console

1. 確保已選擇正確的專案

2. 前往 [API 程式庫](https://console.cloud.google.com/apis/library)

3. 搜尋「**Text-to-Speech**」

4. 點擊「**Cloud Text-to-Speech API**」

5. 點擊「**啟用**」(Enable)

6. 等待 API 啟用完成

### 透過 gcloud CLI

```bash
# 啟用 Text-to-Speech API
gcloud services enable texttospeech.googleapis.com
```

## Step 4: 建立服務帳戶並取得金鑰

### 透過 Cloud Console

1. 前往 [IAM 與管理 > 服務帳戶](https://console.cloud.google.com/iam-admin/serviceaccounts)

2. 點擊「**+ 建立服務帳戶**」(Create Service Account)

3. 填寫服務帳戶資訊：

   | 欄位 | 說明 | 建議值 |
   |------|------|--------|
   | **服務帳戶名稱** | 顯示名稱 | `voice-lab-tts` |
   | **服務帳戶 ID** | 唯一識別碼 | `voice-lab-tts` |
   | **說明** | 用途描述（可選） | `TTS service account` |

4. 點擊「**建立並繼續**」(Create and Continue)

5. 授予角色（可選，TTS 不需要特殊角色）：
   - 可跳過或選擇「Cloud Text-to-Speech User」

6. 點擊「**完成**」(Done)

7. 在服務帳戶列表中，點擊剛建立的帳戶

8. 切換到「**金鑰**」(Keys) 標籤

9. 點擊「**新增金鑰**」>「**建立新金鑰**」

10. 選擇「**JSON**」格式

11. 點擊「**建立**」- 金鑰檔案會自動下載

12. 妥善保存下載的 JSON 金鑰檔案

### 透過 gcloud CLI

```bash
# 建立服務帳戶
gcloud iam service-accounts create voice-lab-tts \
  --display-name="Voice Lab TTS"

# 建立並下載金鑰
gcloud iam service-accounts keys create ./credentials.json \
  --iam-account=voice-lab-tts@voice-lab-project.iam.gserviceaccount.com
```

## Step 5: 設定環境變數

```bash
# .env
GOOGLE_APPLICATION_CREDENTIALS=/path/to/credentials.json
GOOGLE_CLOUD_PROJECT=voice-lab-project
```

或直接設定環境變數：

```bash
export GOOGLE_APPLICATION_CREDENTIALS="/path/to/credentials.json"
```

## 替代方案：使用 API Key

如果不想使用服務帳戶，可以建立 API Key：

### 透過 Cloud Console

1. 前往 [API 與服務 > 憑證](https://console.cloud.google.com/apis/credentials)

2. 點擊「**+ 建立憑證**」>「**API 金鑰**」

3. 複製產生的 API Key

4. （建議）點擊「編輯 API 金鑰」限制使用範圍：
   - 設定應用程式限制（IP、HTTP 參照網址等）
   - 設定 API 限制，只允許 Text-to-Speech API

### 環境變數設定

```bash
# .env
GOOGLE_CLOUD_API_KEY=your_api_key_here
```

## API 使用方式

### REST API 端點

| 服務 | 端點 |
|------|------|
| 語音合成 | `https://texttospeech.googleapis.com/v1/text:synthesize` |
| 語音列表 | `https://texttospeech.googleapis.com/v1/voices` |

### 認證方式

**使用服務帳戶（推薦）：**
```bash
# 取得 access token
ACCESS_TOKEN=$(gcloud auth application-default print-access-token)

curl -X POST \
  "https://texttospeech.googleapis.com/v1/text:synthesize" \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  -H "Content-Type: application/json"
```

**使用 API Key：**
```bash
curl -X POST \
  "https://texttospeech.googleapis.com/v1/text:synthesize?key=YOUR_API_KEY" \
  -H "Content-Type: application/json"
```

## 實作範例

### Python (google-cloud-texttospeech SDK)

```python
from google.cloud import texttospeech

def google_tts(text: str, voice: str = "zh-TW-Standard-A"):
    """Google Cloud TTS synthesis using SDK."""
    client = texttospeech.TextToSpeechClient()

    synthesis_input = texttospeech.SynthesisInput(text=text)

    voice_params = texttospeech.VoiceSelectionParams(
        language_code="zh-TW",
        name=voice,
    )

    audio_config = texttospeech.AudioConfig(
        audio_encoding=texttospeech.AudioEncoding.MP3,
        sample_rate_hertz=24000,
    )

    response = client.synthesize_speech(
        input=synthesis_input,
        voice=voice_params,
        audio_config=audio_config,
    )

    return response.audio_content  # MP3 audio data
```

### Python (REST API with httpx)

```python
import httpx
import base64

async def google_tts_rest(text: str, voice: str = "zh-TW-Standard-A"):
    """Google Cloud TTS synthesis using REST API."""
    url = "https://texttospeech.googleapis.com/v1/text:synthesize"

    # 使用 API Key
    params = {"key": "YOUR_API_KEY"}

    body = {
        "input": {"text": text},
        "voice": {
            "languageCode": "zh-TW",
            "name": voice,
        },
        "audioConfig": {
            "audioEncoding": "MP3",
            "sampleRateHertz": 24000,
        },
    }

    async with httpx.AsyncClient() as client:
        response = await client.post(url, params=params, json=body)
        response.raise_for_status()
        result = response.json()
        # 回傳的音訊是 base64 編碼
        return base64.b64decode(result["audioContent"])
```

### cURL

```bash
curl -X POST \
  "https://texttospeech.googleapis.com/v1/text:synthesize?key=YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "input": {
      "text": "你好，這是 Google Cloud 語音測試。"
    },
    "voice": {
      "languageCode": "zh-TW",
      "name": "zh-TW-Standard-A"
    },
    "audioConfig": {
      "audioEncoding": "MP3",
      "sampleRateHertz": 24000
    }
  }' | jq -r '.audioContent' | base64 -d > voice.mp3
```

## 常用台灣中文語音

### Standard 語音

| 語音名稱 | 性別 | 特色 |
|----------|------|------|
| `zh-TW-Standard-A` | 女聲 | 標準品質 |
| `zh-TW-Standard-B` | 男聲 | 標準品質 |
| `zh-TW-Standard-C` | 男聲 | 標準品質 |

### WaveNet 語音（高品質）

| 語音名稱 | 性別 | 特色 |
|----------|------|------|
| `zh-TW-Wavenet-A` | 女聲 | 高品質、自然 |
| `zh-TW-Wavenet-B` | 男聲 | 高品質、自然 |
| `zh-TW-Wavenet-C` | 男聲 | 高品質、自然 |

### Neural2 語音（最新）

| 語音名稱 | 性別 | 特色 |
|----------|------|------|
| `zh-TW-Neural2-A` | 女聲 | 最新技術、最自然 |
| `zh-TW-Neural2-B` | 男聲 | 最新技術、最自然 |
| `zh-TW-Neural2-C` | 男聲 | 最新技術、最自然 |

### 取得完整語音列表

```bash
curl "https://texttospeech.googleapis.com/v1/voices?key=YOUR_API_KEY" \
  | jq '.voices[] | select(.languageCodes[] | contains("zh-TW"))'
```

## 音訊輸出格式

| 格式 | `audioEncoding` 值 | 說明 |
|------|-------------------|------|
| MP3 | `MP3` | 壓縮格式，檔案較小 |
| WAV | `LINEAR16` | 無損格式，16-bit PCM |
| OGG | `OGG_OPUS` | Opus 編碼，適合串流 |
| MULAW | `MULAW` | 電話音質 |
| ALAW | `ALAW` | 電話音質 |

## 定價比較

| 語音類型 | 免費配額 | 價格（超出免費配額後） |
|----------|----------|----------------------|
| **Standard** | 400 萬字元/月 | $4 USD/百萬字元 |
| **WaveNet** | 100 萬字元/月 | $16 USD/百萬字元 |
| **Neural2** | 100 萬字元/月 | $16 USD/百萬字元 |

> 注意：免費配額每月重置

## SSML 支援

Google Cloud TTS 支援 SSML 語法：

```python
ssml_text = """
<speak>
  <p>
    <s>這是第一句。</s>
    <s><break time="500ms"/>這是第二句，有停頓。</s>
  </p>
  <p>
    <prosody rate="slow" pitch="+2st">這句話比較慢，音調較高。</prosody>
  </p>
</speak>
"""

# 使用 SSML input
synthesis_input = texttospeech.SynthesisInput(ssml=ssml_text)
```

## 配額與限制

| 限制項目 | 數值 |
|----------|------|
| 每次請求最大字元數 | 5,000 字元 |
| 每分鐘請求數 | 1,000 次 |
| 每分鐘字元數 | 100 萬字元 |

## 故障排除

### 常見錯誤

| 錯誤代碼 | 說明 | 解決方案 |
|----------|------|----------|
| `403 PERMISSION_DENIED` | API 未啟用或無權限 | 確認 API 已啟用、憑證正確 |
| `400 INVALID_ARGUMENT` | 參數錯誤 | 檢查語音名稱、語言代碼是否正確 |
| `429 RESOURCE_EXHAUSTED` | 配額用盡 | 等待配額重置或提升配額 |

### 驗證設定

```bash
# 測試 API Key 是否有效
curl "https://texttospeech.googleapis.com/v1/voices?key=YOUR_API_KEY" \
  | head -20

# 測試服務帳戶
gcloud auth application-default print-access-token
```

### 檢查 API 是否啟用

```bash
gcloud services list --enabled | grep texttospeech
```

## 相關資源

- [Google Cloud Text-to-Speech 文檔](https://cloud.google.com/text-to-speech/docs)
- [支援的語言和語音列表](https://cloud.google.com/text-to-speech/docs/voices)
- [SSML 參考](https://cloud.google.com/text-to-speech/docs/ssml)
- [定價資訊](https://cloud.google.com/text-to-speech/pricing)
- [Google Cloud Console](https://console.cloud.google.com/)
- [Python SDK 文檔](https://cloud.google.com/python/docs/reference/texttospeech/latest)

---

*Last updated: 2026-01-20*

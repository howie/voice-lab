# Azure Speech Service Integration

Azure Cognitive Services Speech 是微軟提供的語音服務，支援多語言 TTS 和 STT。

## Step 1: 建立 Azure 帳戶

1. 前往 [Azure Portal](https://portal.azure.com/)
2. 如果沒有帳戶，點擊「免費開始」註冊
3. 新帳戶可獲得 $200 美元免費額度（30 天內使用）

## Step 2: 建立 Speech Service 資源

### 透過 Azure Portal

1. 登入 [Azure Portal](https://portal.azure.com/)

2. 點擊左上角「**+ 建立資源**」(Create a resource)

3. 在搜尋框輸入「**Speech**」，選擇「**Speech**」服務

4. 點擊「**建立**」(Create)

5. 填寫資源設定：

   | 欄位 | 說明 | 建議值 |
   |------|------|--------|
   | **訂用帳戶** (Subscription) | 選擇你的訂閱 | 你的訂閱名稱 |
   | **資源群組** (Resource group) | 新建或選擇現有群組 | `voice-lab-rg` |
   | **區域** (Region) | 選擇離你最近的區域 | `East Asia` 或 `Southeast Asia` |
   | **名稱** (Name) | 資源的唯一名稱 | `voice-lab-speech` |
   | **定價層** (Pricing tier) | 選擇方案 | `Free F0` (開發測試) 或 `Standard S0` (正式環境) |

6. 點擊「**檢閱 + 建立**」(Review + create)

7. 確認設定後，點擊「**建立**」(Create)

8. 等待部署完成（約 1-2 分鐘）

### 透過 Azure CLI

```bash
# 登入 Azure
az login

# 建立資源群組（如果不存在）
az group create \
  --name voice-lab-rg \
  --location eastasia

# 建立 Speech Service 資源
az cognitiveservices account create \
  --name voice-lab-speech \
  --resource-group voice-lab-rg \
  --kind SpeechServices \
  --sku F0 \
  --location eastasia \
  --yes
```

## Step 3: 取得 API Key 和 Region

### 透過 Azure Portal

1. 進入你建立的 Speech Service 資源

2. 在左側選單點擊「**金鑰和端點**」(Keys and Endpoint)

3. 你會看到：
   - **金鑰 1** (KEY 1): 你的 API Key（可使用任一個金鑰）
   - **金鑰 2** (KEY 2): 備用 API Key
   - **位置/區域** (Location/Region): 例如 `eastasia`
   - **端點** (Endpoint): REST API 端點 URL

4. 點擊「複製」圖示複製金鑰

### 透過 Azure CLI

```bash
# 取得 API Keys
az cognitiveservices account keys list \
  --name voice-lab-speech \
  --resource-group voice-lab-rg

# 輸出範例：
# {
#   "key1": "xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
#   "key2": "yyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyy"
# }

# 取得端點資訊
az cognitiveservices account show \
  --name voice-lab-speech \
  --resource-group voice-lab-rg \
  --query "{endpoint:properties.endpoint, region:location}"
```

## Step 4: 設定環境變數

```bash
# .env
AZURE_SPEECH_KEY=your_api_key_here
AZURE_SPEECH_REGION=eastasia
```

## API 使用方式

### REST API 端點

| 服務 | 端點格式 |
|------|----------|
| TTS | `https://{region}.tts.speech.microsoft.com/cognitiveservices/v1` |
| STT | `https://{region}.stt.speech.microsoft.com/speech/recognition/conversation/cognitiveservices/v1` |
| 語音列表 | `https://{region}.tts.speech.microsoft.com/cognitiveservices/voices/list` |

### 認證方式

使用 `Ocp-Apim-Subscription-Key` header：

```bash
curl -X GET \
  "https://eastasia.tts.speech.microsoft.com/cognitiveservices/voices/list" \
  -H "Ocp-Apim-Subscription-Key: YOUR_API_KEY"
```

## 實作範例

### Python (azure-cognitiveservices-speech SDK)

```python
import azure.cognitiveservices.speech as speechsdk

def azure_tts(text: str, voice: str = "zh-TW-HsiaoChenNeural"):
    """Azure TTS synthesis using SDK."""
    speech_config = speechsdk.SpeechConfig(
        subscription="YOUR_API_KEY",
        region="eastasia"
    )
    speech_config.speech_synthesis_voice_name = voice

    synthesizer = speechsdk.SpeechSynthesizer(
        speech_config=speech_config,
        audio_config=None  # 返回音訊資料而非播放
    )

    result = synthesizer.speak_text_async(text).get()

    if result.reason == speechsdk.ResultReason.SynthesizingAudioCompleted:
        return result.audio_data
    else:
        raise Exception(f"Synthesis failed: {result.reason}")
```

### Python (REST API with httpx)

```python
import httpx

async def azure_tts_rest(text: str, voice: str = "zh-TW-HsiaoChenNeural"):
    """Azure TTS synthesis using REST API."""
    region = "eastasia"
    url = f"https://{region}.tts.speech.microsoft.com/cognitiveservices/v1"

    headers = {
        "Ocp-Apim-Subscription-Key": "YOUR_API_KEY",
        "Content-Type": "application/ssml+xml",
        "X-Microsoft-OutputFormat": "audio-16khz-128kbitrate-mono-mp3",
    }

    ssml = f"""
    <speak version='1.0' xmlns='http://www.w3.org/2001/10/synthesis' xml:lang='zh-TW'>
        <voice name='{voice}'>{text}</voice>
    </speak>
    """

    async with httpx.AsyncClient() as client:
        response = await client.post(url, headers=headers, content=ssml)
        response.raise_for_status()
        return response.content  # MP3 audio data
```

### cURL

```bash
curl -X POST \
  "https://eastasia.tts.speech.microsoft.com/cognitiveservices/v1" \
  -H "Ocp-Apim-Subscription-Key: YOUR_API_KEY" \
  -H "Content-Type: application/ssml+xml" \
  -H "X-Microsoft-OutputFormat: audio-16khz-128kbitrate-mono-mp3" \
  -d "<speak version='1.0' xmlns='http://www.w3.org/2001/10/synthesis' xml:lang='zh-TW'>
        <voice name='zh-TW-HsiaoChenNeural'>你好，這是 Azure 語音測試。</voice>
      </speak>" \
  --output voice.mp3
```

## 常用台灣中文語音

| 語音名稱 | 性別 | 特色 |
|----------|------|------|
| `zh-TW-HsiaoChenNeural` | 女聲 | 自然、通用 |
| `zh-TW-YunJheNeural` | 男聲 | 自然、通用 |
| `zh-TW-HsiaoYuNeural` | 女聲 | 活潑、年輕 |

### 取得完整語音列表

```bash
curl "https://eastasia.tts.speech.microsoft.com/cognitiveservices/voices/list" \
  -H "Ocp-Apim-Subscription-Key: YOUR_API_KEY" | jq '.[] | select(.Locale == "zh-TW")'
```

## 音訊輸出格式

常用的 `X-Microsoft-OutputFormat` 值：

| 格式 | 說明 |
|------|------|
| `audio-16khz-128kbitrate-mono-mp3` | MP3, 16kHz, 128kbps |
| `audio-24khz-160kbitrate-mono-mp3` | MP3, 24kHz, 160kbps |
| `audio-48khz-192kbitrate-mono-mp3` | MP3, 48kHz, 192kbps |
| `riff-16khz-16bit-mono-pcm` | WAV, 16kHz, 16bit |
| `riff-24khz-16bit-mono-pcm` | WAV, 24kHz, 16bit |

## 定價層比較

| 層級 | 免費配額 | 價格 | 適用場景 |
|------|----------|------|----------|
| **Free (F0)** | 500 萬字元/月 | 免費 | 開發測試 |
| **Standard (S0)** | 無免費配額 | $16 USD/百萬字元 | 正式環境 |

> 注意：每個訂閱只能建立一個 Free 層資源

## 配額與限制

- **並行請求**: Standard 層最多 200 個並行請求
- **字元限制**: 單次請求最多 10,000 字元（SSML）
- **請求速率**: Free 層限制較多，建議正式環境使用 Standard 層

## 故障排除

### 常見錯誤

| 錯誤代碼 | 說明 | 解決方案 |
|----------|------|----------|
| `401` | 認證失敗 | 檢查 API Key 是否正確 |
| `403` | 配額用盡或區域錯誤 | 檢查配額或確認 region 設定 |
| `429` | 請求過多 | 降低請求頻率或升級方案 |

### 驗證設定

```bash
# 測試 API Key 是否有效
curl -I "https://eastasia.tts.speech.microsoft.com/cognitiveservices/voices/list" \
  -H "Ocp-Apim-Subscription-Key: YOUR_API_KEY"

# 成功會返回 200 OK
```

## 相關資源

- [Azure Speech Service 文檔](https://docs.microsoft.com/azure/cognitive-services/speech-service/)
- [支援的語言和語音列表](https://docs.microsoft.com/azure/cognitive-services/speech-service/language-support)
- [SSML 語法參考](https://docs.microsoft.com/azure/cognitive-services/speech-service/speech-synthesis-markup)
- [定價資訊](https://azure.microsoft.com/pricing/details/cognitive-services/speech-services/)
- [Azure Portal](https://portal.azure.com/)

---

*Last updated: 2026-01-20*

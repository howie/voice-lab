# VoAI TTS API Integration

VoAI (網際智慧) 是台灣本土的語音合成服務提供商，專注於高品質的台灣中文語音。

## API 文檔

- **Swagger**: https://connect.voai.ai/swagger/index.html
- **Endpoint**: `https://connect.voai.ai`

## 認證

使用 `x-api-key` header 進行認證：

```bash
curl -H "x-api-key: YOUR_API_KEY" https://connect.voai.ai/TTS/GetSpeaker
```

## 主要端點

### 1. GET /TTS/GetSpeaker

獲取所有可用的 speakers。

**Headers:**
- `x-api-key`: API key

**Response:**
```json
{
  "data": {
    "models": [
      {
        "info": { "version": "Classic" },
        "speakers": [...]
      },
      {
        "info": { "version": "Neo" },
        "speakers": [...]
      }
    ]
  }
}
```

### 2. POST /TTS/Speech

生成語音（簡單介面）。

**Headers:**
- `x-api-key`: API key
- `x-output-format`: `wav`, `pcm`, 或 `mp3`
- `x-sample-rate`: `8000`, `16000`, `32000`, `44100` (Neo 最高 32000)
- `Content-Type`: `application/json`

**Request Body:**
```json
{
  "version": "Neo",
  "text": "網際智慧的聲音，是業界的標竿。",
  "speaker": "佑希",
  "style": "預設",
  "speed": 1.0,
  "pitch_shift": 0,
  "style_weight": 0,
  "breath_pause": 0
}
```

**Parameters:**
- `version`: `Classic` 或 `Neo`
  - **Classic**: 高速生成，優化效率和穩定性
  - **Neo**: 情感聚焦，適合短影音和故事講述
- `text`: 要合成的文字
- `speaker`: Speaker 名稱（見下方列表）
- `style`: 語音風格（見 speaker 支援的 styles）
- `speed`: 速度 [0.5, 1.5]，預設 1.0
- `pitch_shift`: 音高偏移 [-5, 5]，預設 0
- `style_weight`: 風格權重 [0, 1]，預設 0（僅 Classic）
- `breath_pause`: 呼吸停頓 [0, 10] 秒，預設 0

### 3. POST /TTS/generate-voice

使用停頓標籤生成語音（進階）。

支援停頓標籤格式：`[:seconds]`，最多 5 秒。

**Example:**
```json
{
  "text": "歡迎[:1]來到網際智慧[:2]的世界。"
}
```

### 4. POST /TTS/generate-dialogue

生成多角色對話。

自動串接多個語音片段。

### 5. GET /Key/Usage

查詢配額使用情況。

## 常用 Speakers

### Classic 模型

| Speaker | 性別 | 年齡 | 分類 | Styles | 適用場景 |
|---------|------|------|------|--------|----------|
| 佑希 | 男聲 | 22 | 真實聲線 | 預設, 平靜, 哭腔, 生氣, 激動, 嚴肅 | 廣播, 教學, 新聞, 動畫, 叫賣, 商務談話, 家庭對話, 廣告, 客服 |
| 雨榛 | 女聲 | 25 | 真實聲線 | 預設, 平靜, 難過, 高興, 生氣 | 冥想, 廣播, 科幻小說, 教學, 新聞, 商務談話, 言情小說, 廣告, 客服 |
| 子墨 | 男聲 | 37 | 真實聲線 | 預設, 平靜, 厭世 | 夜間DJ, 冥想, 旁白, 動畫, 言情小說, 家庭對話, 廣告 |
| 柔洢 | 女聲 | 26 | 真實聲線 | 預設, 可愛, 難過, 生氣, 溫暖 | 夜間DJ, 冥想, 旁白, 廣播, 日常對話, 言情小說, 廣告 |
| 竹均 | 女聲 | 22 | 真實聲線 | 預設, 平靜, 開心, 生氣, 難過 | 日常對話, 言情小說, 家庭對話 |

### Neo 模型

| Speaker | 性別 | 年齡 | 分類 | Styles | 適用場景 |
|---------|------|------|------|--------|----------|
| 佑希 | 男聲 | 22 | 真實聲線 | 預設, 聊天, 穩重, 激昂 | 廣播, 教學, 新聞, 動畫, 叫賣, 商務談話, 家庭對話, 廣告, 客服 |
| 雨榛 | 女聲 | 25 | 真實聲線 | 預設, 聊天, 輕柔, 輕鬆 | 冥想, 廣播, 科幻小說, 教學, 新聞, 商務談話, 言情小說, 廣告, 客服 |
| 子墨 | 男聲 | 37 | 真實聲線 | 預設, 穩健 | 夜間DJ, 冥想, 旁白, 動畫, 言情小說, 家庭對話, 廣告 |
| 昊宇 | 男聲 | 36 | - | 預設, 溫暖, 開心, 難過 | 夜間DJ, 商務談話, 廣播, 科幻小說, 新聞, 日常對話, 言情小說, 家庭對話 |
| 采芸 | 女聲 | 25 | - | 預設, 感性, 難過, 懸疑, 生氣 | 夜間DJ, 冥想, 旁白, 廣播, 恐怖小說, 新聞, 日常對話, 廣告, 客服 |
| 樂晰 | 女聲 | 30 | 真實聲線 | 預設, 聊天, 可愛 | 旁白, 廣播, 科幻小說, 兒童教材, 童話故事, 教學, 新聞, 動畫, 叫賣, 商務談話, 日常對話, 家庭對話, 廣告, 客服 |

### 特殊語音

| Speaker | 性別 | 年齡 | 特色 | 適用場景 |
|---------|------|------|------|----------|
| 品妍 | 女聲 | 6 | 兒童聲線 | 兒童教材, 童話故事, 動畫, 叫賣, 日常對話, 家庭對話, 廣告 |
| 子睿 | 男聲 | 5 | 兒童聲線 | 兒童教材, 童話故事, 動畫, 日常對話, 家庭對話, 廣告 |
| 春枝 | 女聲 | 67 | 長者聲線 | 講古, 童話故事, 恐怖小說, 動畫, 日常對話, 家庭對話, 廣告 |
| 麗珠 | 女聲 | 73 | 長者聲線 | 動畫, 叫賣, 日常對話, 家庭對話, 廣告 |

## 完整 Speakers 列表

### Classic 模型 (35 speakers)

子墨, 雨榛, 李晴, 品妍, 春枝, 婉婷, 淑芬, 麗珠, 柔洢, 璦廷, 竹均, 佑希, 汪一誠, 楷心, 美霞, 子睿, 惠婷, 辰辰, 語安, 虹葳, 欣妤, 柏翰, 凡萱, 韻菲, 士倫, 袁祺裕, 阿偉, 皓軒, 靜芝, 昊宇, 采芸, 渝函, 文彬, 怡婷

### Neo 模型 (46 speakers)

子墨, 雨榛, 李晴, 品妍, 春枝, 婉婷, 淑芬, 柔洢, 璦廷, 竹均, 佑希, 汪一誠, 楷心, 美霞, 惠婷, 辰辰, 語安, 虹葳, 欣妤, 柏翰, 凡萱, 韻菲, 士倫, 袁祺裕, 皓軒, 靜芝, 昊宇, 采芸, 渝函, 文彬, 怡婷, 娜娜, 文澤, 諭書, 鳳姊, 悅青, 俊傑, 詠芯, 建忠, 立安, 樂晰, 昱翔, 佩綺, 豪哥, 政德, 喬喬, 軒軒, 阿皮, 布丁, 明達, 泡泡, 佳雯, 雅琪

## 實作範例

### Python (httpx)

```python
import httpx

async def voai_tts(text: str, speaker: str = "佑希", style: str = "預設"):
    """VoAI TTS synthesis."""
    url = "https://connect.voai.ai/TTS/Speech"
    headers = {
        "x-api-key": "YOUR_API_KEY",
        "x-output-format": "mp3",
        "Content-Type": "application/json",
    }
    body = {
        "version": "Neo",
        "text": text,
        "speaker": speaker,
        "style": style,
        "speed": 1.0,
        "pitch_shift": 0,
        "style_weight": 0,
        "breath_pause": 0,
    }

    async with httpx.AsyncClient() as client:
        response = await client.post(url, headers=headers, json=body)
        return response.content  # MP3 audio data
```

### cURL

```bash
curl --location 'https://connect.voai.ai/TTS/Speech' \
  --header 'x-output-format: mp3' \
  --header 'x-api-key: YOUR_API_KEY' \
  --header 'Content-Type: application/json' \
  --data '{
    "version": "Neo",
    "text": "網際智慧的聲音，是業界的標竿。",
    "speaker": "佑希",
    "style": "預設",
    "speed": 1,
    "pitch_shift": 0,
    "style_weight": 0,
    "breath_pause": 0
  }' \
  --output voice.mp3
```

## 環境變數設定

```bash
# .env
VOAI_API_KEY=your_api_key_here
VOAI_API_ENDPOINT=connect.voai.ai
```

## 注意事項

1. **Neo 模型限制**: 最高取樣率 32000 Hz
2. **停頓標籤**: 最多支援 5 秒停頓
3. **語音風格**: 不同 speaker 支援的 styles 不同，參考 `/TTS/GetSpeaker` 端點
4. **字數限制**: 建議單次請求不超過 500 字
5. **語言支援**: 主要支援繁體中文（台灣），部分 speakers 支援簡體中文和英文

## 效能指標

- **Latency**: ~1.5-2.0 秒（包含網路延遲）
- **Quality**: 高品質台灣中文語音
- **Streaming**: 支援 PCM 格式即時傳輸

## 相關資源

- [VoAI 官網](https://www.voai.ai/)
- [API Swagger 文檔](https://connect.voai.ai/swagger/index.html)
- [聯絡支援](https://www.voai.ai/contact)

---

*Last updated: 2026-01-17*

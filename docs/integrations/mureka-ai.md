# Mureka AI Integration

Mureka AI 是 AI 音樂生成領域首個官方 API 平台，由昆侖科技開發，採用 SkyMusic 2.0 模型，可根據歌詞、描述、風格等輸入生成完整歌曲、純音樂（BGM）和歌詞。

## Step 1: 建立 Mureka 帳戶

1. 前往 [Mureka Platform](https://platform.mureka.ai/)

2. 點擊「**Sign Up**」或「**Get Started**」註冊

3. 完成帳戶驗證流程

4. 選擇適合的方案（免費試用或付費方案）

## Step 2: 取得 API Key

1. 登入 [Mureka Platform](https://platform.mureka.ai/)

2. 前往 API Keys 頁面：[https://platform.mureka.ai/apiKeys](https://platform.mureka.ai/apiKeys)

3. 點擊「**Create API Key**」建立新的 API Key

4. 複製並安全保存 API Key

> **安全提醒**: 請勿將 API Key 嵌入前端程式碼或分享給他人，建議定期輪換 API Key。

## Step 3: 設定環境變數

```bash
# .env
MUREKA_API_KEY=your_api_key_here
MUREKA_API_URL=https://api.mureka.ai
```

## API 使用方式

### Base URL

```
https://api.mureka.ai
```

### 認證方式

使用 Bearer Token 認證：

```bash
curl -X POST "https://api.mureka.ai/v1/song/generate" \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json"
```

### REST API 端點

| 服務 | 方法 | 端點 | 說明 |
|------|------|------|------|
| 歌曲生成 | POST | `/v1/song/generate` | 根據歌詞和風格生成歌曲 |
| 歌曲查詢 | GET | `/v1/song/query/{task_id}` | 查詢歌曲生成任務狀態 |
| 純音樂生成 | POST | `/v1/instrumental/generate` | 生成背景音樂/純音樂 |
| 純音樂查詢 | GET | `/v1/instrumental/query/{task_id}` | 查詢純音樂生成任務狀態 |
| 歌詞生成 | POST | `/v1/lyrics/generate` | 根據提示詞生成歌詞 |
| 歌詞延伸 | POST | `/v1/lyrics/extend` | 延伸現有歌詞 |

## 實作範例

### Python (REST API with httpx)

```python
import httpx
import asyncio
from typing import Any

MUREKA_API_URL = "https://api.mureka.ai"
MUREKA_API_KEY = "YOUR_API_KEY"


async def generate_song(
    lyrics: str,
    prompt: str,
    model: str = "auto",
) -> dict[str, Any]:
    """
    生成歌曲（非同步任務）。

    Args:
        lyrics: 歌詞內容，可包含段落標記如 [Verse], [Chorus]
        prompt: 風格描述，如 "pop, upbeat, female vocal"
        model: 模型選擇，可選 "auto", "mureka-01", "v7.5", "v6"

    Returns:
        包含 task_id 的任務資訊
    """
    url = f"{MUREKA_API_URL}/v1/song/generate"

    headers = {
        "Authorization": f"Bearer {MUREKA_API_KEY}",
        "Content-Type": "application/json",
    }

    body = {
        "lyrics": lyrics,
        "prompt": prompt,
        "model": model,
    }

    async with httpx.AsyncClient() as client:
        response = await client.post(url, headers=headers, json=body, timeout=60)
        response.raise_for_status()
        return response.json()


async def query_song_task(task_id: str) -> dict[str, Any]:
    """
    查詢歌曲生成任務狀態。

    Args:
        task_id: 任務 ID

    Returns:
        任務狀態與結果（包含 mp3_url）
    """
    url = f"{MUREKA_API_URL}/v1/song/query/{task_id}"

    headers = {
        "Authorization": f"Bearer {MUREKA_API_KEY}",
    }

    async with httpx.AsyncClient() as client:
        response = await client.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        return response.json()


async def generate_song_and_wait(
    lyrics: str,
    prompt: str,
    model: str = "auto",
    poll_interval: float = 5.0,
    max_wait: float = 300.0,
) -> dict[str, Any]:
    """
    生成歌曲並等待完成。

    Args:
        lyrics: 歌詞內容
        prompt: 風格描述
        model: 模型選擇
        poll_interval: 輪詢間隔（秒）
        max_wait: 最大等待時間（秒）

    Returns:
        完成的歌曲資訊（包含 mp3_url）
    """
    # 1. 提交生成任務
    task_info = await generate_song(lyrics, prompt, model)
    task_id = task_info["id"]
    print(f"Task submitted: {task_id}")

    # 2. 輪詢等待完成
    elapsed = 0.0
    while elapsed < max_wait:
        result = await query_song_task(task_id)
        status = result.get("status")

        if status == "completed":
            return result
        elif status == "failed":
            raise Exception(f"Song generation failed: {result}")

        await asyncio.sleep(poll_interval)
        elapsed += poll_interval

    raise TimeoutError(f"Song generation timed out after {max_wait}s")
```

### Python (歌詞生成)

```python
async def generate_lyrics(prompt: str | None = None) -> dict[str, Any]:
    """
    生成歌詞。

    Args:
        prompt: 歌詞主題/風格提示，如 "a song about space exploration"
                若不提供則隨機生成

    Returns:
        包含生成歌詞的回應
    """
    url = f"{MUREKA_API_URL}/v1/lyrics/generate"

    headers = {
        "Authorization": f"Bearer {MUREKA_API_KEY}",
        "Content-Type": "application/json",
    }

    body = {}
    if prompt:
        body["prompt"] = prompt

    async with httpx.AsyncClient() as client:
        response = await client.post(url, headers=headers, json=body, timeout=60)
        response.raise_for_status()
        return response.json()
```

### Python (純音樂/BGM 生成)

```python
async def generate_instrumental(
    prompt: str,
    model: str = "auto",
) -> dict[str, Any]:
    """
    生成純音樂/背景音樂。

    Args:
        prompt: 場景描述，如 "relaxing coffee shop ambiance, acoustic guitar"
        model: 模型選擇

    Returns:
        包含 task_id 的任務資訊
    """
    url = f"{MUREKA_API_URL}/v1/instrumental/generate"

    headers = {
        "Authorization": f"Bearer {MUREKA_API_KEY}",
        "Content-Type": "application/json",
    }

    body = {
        "prompt": prompt,
        "model": model,
    }

    async with httpx.AsyncClient() as client:
        response = await client.post(url, headers=headers, json=body, timeout=60)
        response.raise_for_status()
        return response.json()
```

### cURL 範例

```bash
# 生成歌曲
curl -X POST "https://api.mureka.ai/v1/song/generate" \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "lyrics": "[Verse]\n星光點點照亮夜空\n我們一起追逐夢想\n[Chorus]\n勇敢向前不要停\n美好未來等著你",
    "prompt": "pop, upbeat, chinese, female vocal",
    "model": "auto"
  }'

# 查詢任務狀態
curl -X GET "https://api.mureka.ai/v1/song/query/{task_id}" \
  -H "Authorization: Bearer YOUR_API_KEY"

# 生成歌詞
curl -X POST "https://api.mureka.ai/v1/lyrics/generate" \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "a cheerful song about friendship for children"
  }'

# 生成純音樂
curl -X POST "https://api.mureka.ai/v1/instrumental/generate" \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "magical fantasy background music, orchestral, whimsical",
    "model": "auto"
  }'
```

## 模型選擇

| 模型 ID | 名稱 | 特色 |
|---------|------|------|
| `auto` | 自動選擇 | 系統根據輸入自動選擇最佳模型 |
| `mureka-01` | Mureka O1 | 最新模型，最高品質，支援複雜編曲 |
| `v7.5` | V7.5 | 平衡品質與速度 |
| `v6` | V6 | 經典模型，穩定可靠 |

> 推薦：一般使用 `auto`，系統會自動選擇最適合的模型

## 任務狀態

| 狀態 | 說明 |
|------|------|
| `preparing` | 任務準備中 |
| `processing` | 生成處理中 |
| `completed` | 生成完成，可取得結果 |
| `failed` | 生成失敗 |

## 回應格式

### 歌曲生成回應

```json
{
  "id": "task_abc123",
  "created_at": "2026-01-29T10:00:00Z",
  "model": "mureka-01",
  "status": "preparing",
  "trace_id": "trace_xyz789"
}
```

### 歌曲查詢回應（完成時）

```json
{
  "id": "task_abc123",
  "status": "completed",
  "song": {
    "song_id": "song_def456",
    "title": "夢想之歌",
    "duration_milliseconds": 180000,
    "mp3_url": "https://cdn.mureka.ai/songs/xxx.mp3",
    "cover": "https://cdn.mureka.ai/covers/xxx.jpg",
    "lyrics": "[Verse]\n星光點點...",
    "state": "completed"
  }
}
```

## 定價方案

### Web 訂閱方案

| 方案 | 價格 | 配額 |
|------|------|------|
| **Free** | $0 | 有限試用額度 |
| **Pro** | $10/月 | 500 首歌曲 或 250 分鐘語音 |
| **Premier** | $30/月 | 2,000 首歌曲 或 1,000 分鐘語音 |

### API 方案

| 方案 | 價格 | 配額 | 並發數 |
|------|------|------|--------|
| **基礎** | $30 起 | 依用量 | 5 |
| **標準** | $1,000/月 | 依用量 | 5 |
| **企業** | $5,000+ | 依用量 | 10+ |

> 每首歌成本約 $0.015 - $0.03（依方案而定）

### 配額說明

- 每個帳戶最多支援 **10 個並發生成任務**
- 平均生成時間約 **45 秒**
- 每次生成產出 **2 首歌曲**
- 歌曲最長可達 **5 分鐘**
- 支援 **10 種語言**（中文品質最佳）

### 額度有效期

- 充值後啟動 **12 個月**有效期
- 後續充值會延長所有現有額度的有效期
- 消費時優先使用付費額度，再使用贈送額度（FIFO 原則）
- 不支援退款

## 商業授權

透過付費 API 生成的所有內容皆享有：
- 完整使用權
- 商業授權
- 可用於商業產品、平台發布、廣告、影片等商業場景
- 免版稅（Royalty-Free）

## MCP Server 整合

Mureka 提供官方 MCP (Model Context Protocol) Server，可與 Claude Desktop、OpenAI Agents 等整合：

### 安裝

```bash
# 安裝 uv 套件管理器
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### Claude Desktop 設定

編輯 `claude_desktop_config.json`：

```json
{
  "mcpServers": {
    "Mureka": {
      "command": "uvx",
      "args": ["mureka-mcp"],
      "env": {
        "MUREKA_API_KEY": "<your-api-key>",
        "MUREKA_API_URL": "https://api.mureka.ai",
        "TIME_OUT_SECONDS": "300"
      }
    }
  }
}
```

### MCP 可用工具

| 工具 | 說明 |
|------|------|
| `generate_lyrics` | 根據提示詞生成歌詞 |
| `generate_song` | 根據歌詞和風格生成完整歌曲 |
| `generate_bgm` | 生成背景音樂/純音樂 |

## 故障排除

### 常見錯誤

| 錯誤代碼 | 說明 | 解決方案 |
|----------|------|----------|
| `401` | 認證失敗 | 檢查 API Key 是否正確 |
| `402` | 額度不足 | 充值或升級方案 |
| `429` | 請求過多/並發上限 | 降低請求頻率或等待任務完成 |
| `500` | 伺服器錯誤 | 稍後重試 |

### 任務逾時

- 預設逾時時間：60 秒
- 可調整至最長 300 秒
- 若經常逾時，建議增加輪詢間隔

### 驗證設定

```bash
# 測試 API Key 是否有效（透過歌詞生成測試）
curl -X POST "https://api.mureka.ai/v1/lyrics/generate" \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"prompt": "test"}'
```

## 相關資源

- [Mureka Platform](https://platform.mureka.ai/)
- [API 文檔](https://platform.mureka.ai/docs/)
- [Mureka 官網](https://www.mureka.ai/)
- [MCP Server (GitHub)](https://github.com/SkyworkAI/Mureka-mcp)
- [定價資訊](https://platform.mureka.ai/pricing)
- [FAQ](https://platform.mureka.ai/docs/en/faq.html)

---

*Last updated: 2026-01-29*

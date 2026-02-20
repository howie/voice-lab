# Data Model: Gemini Lyria 音樂生成整合

**Feature**: 016-integration-gemini-lyria-music
**Date**: 2026-02-19

---

## 概覽

本功能**不需要新增資料庫表或欄位**。完全複用 012-music-generation 建立的 `music_generation_jobs` 表結構，僅需新增 enum 值。

---

## Entity 變更

### 1. MusicProvider Enum — 新增 `LYRIA`

**位置**: `backend/src/domain/entities/music.py`

```python
class MusicProvider(StrEnum):
    MUREKA = "mureka"
    SUNO = "suno"
    LYRIA = "lyria"      # 新增
```

### 2. MusicGenerationJob — 無結構變更

現有 `music_generation_jobs` 表的 `provider` 欄位（VARCHAR）可直接存放 `"lyria"` 值，無需 schema migration。

**既有欄位對應 Lyria 資料**：

| 欄位 | Mureka 對應 | Lyria 對應 | 說明 |
|------|-------------|------------|------|
| `provider` | `"mureka"` | `"lyria"` | Provider 標識 |
| `type` | song/instrumental/lyrics | `instrumental` (僅器樂) | Lyria 2 僅支援 instrumental |
| `prompt` | 風格描述 | 英文音樂描述 | Lyria 限英文 |
| `model` | `"auto"` / `"mureka-01"` 等 | `"lyria-002"` | 模型代號 |
| `provider_task_id` | Mureka task_id | N/A (同步 API) | Lyria 2 為同步回應，不需 task_id |
| `result_url` | 本地 MP3 路徑 | 本地 MP3 路徑 (WAV→MP3 轉換後) | 統一 MP3 格式 |
| `original_url` | Mureka CDN URL | N/A (base64 回傳) | Lyria 直接回傳 base64，無 CDN URL |
| `duration_ms` | 由 API 回傳 | 固定 ~32,800ms | Lyria 2 固定長度 |
| `cover_url` | Mureka 封面 URL | N/A | Lyria 2 不生成封面 |
| `generated_lyrics` | AI 生成歌詞 | N/A | Lyria 2 不生成歌詞 |
| `lyrics` | 輸入歌詞 | N/A | Lyria 2 不接受歌詞 |

### 3. MusicProviderEnum (Pydantic) — 新增 `LYRIA`

**位置**: `backend/src/presentation/api/routes/music.py` (或 schemas)

```python
class MusicProviderEnum(str, Enum):
    MUREKA = "mureka"
    LYRIA = "lyria"      # 新增
```

---

## 新增實體

### LyriaVertexAIClient

**位置**: `backend/src/infrastructure/adapters/lyria/client.py`

低層級 Vertex AI REST API 客戶端。

```python
@dataclass
class LyriaGenerationResult:
    """Lyria Vertex AI API 回應結果"""
    audio_content: bytes       # 解碼後的 WAV 音訊資料
    mime_type: str             # "audio/wav"
    sample_rate: int           # 48000
    duration_ms: int           # ~32800


class LyriaVertexAIClient:
    """Google Vertex AI Lyria 2 REST API 客戶端"""

    def __init__(
        self,
        project_id: str | None = None,
        location: str = "us-central1",
        model: str = "lyria-002",
        timeout: float = 30.0,
    ) -> None: ...

    async def generate_instrumental(
        self,
        *,
        prompt: str,
        negative_prompt: str | None = None,
        seed: int | None = None,
        sample_count: int | None = None,
    ) -> list[LyriaGenerationResult]: ...

    async def health_check(self) -> bool: ...
```

**認證流程**：
```python
import google.auth
import google.auth.transport.requests

credentials, project_id = google.auth.default()
credentials.refresh(google.auth.transport.requests.Request())
# 使用 credentials.token 作為 Bearer token
```

### LyriaMusicProvider

**位置**: `backend/src/infrastructure/providers/music/lyria_music.py`

實作 `IMusicProvider` 介面的 Lyria provider。

```python
class LyriaMusicProvider(IMusicProvider):
    """Google Lyria 音樂生成 Provider"""

    @property
    def name(self) -> str:
        return "lyria"

    @property
    def display_name(self) -> str:
        return "Google Lyria"

    async def generate_instrumental(
        self, *, prompt: str, model: str | None = None
    ) -> MusicSubmitResult: ...

    async def generate_song(
        self, *, lyrics: str | None, prompt: str | None, model: str | None
    ) -> MusicSubmitResult:
        raise NotSupportedError("Lyria 2 does not support song generation with vocals")

    async def generate_lyrics(
        self, *, prompt: str
    ) -> MusicSubmitResult:
        raise NotSupportedError("Lyria 2 does not support lyrics generation")

    async def query_task(
        self, task_id: str, task_type: str
    ) -> MusicTaskResult: ...

    async def health_check(self) -> bool: ...
```

**關鍵設計**：
- `generate_song` 和 `generate_lyrics` 拋出 `NotSupportedError`（Lyria 2 不支援）
- `generate_instrumental` 呼叫 `LyriaVertexAIClient` 後直接處理結果（同步 API）
- `query_task` 對 Lyria 而言永遠回傳 COMPLETED 或 FAILED（無 PROCESSING 中間狀態）

---

## 設定新增

**位置**: `backend/src/config.py`

```python
# Google Lyria Music Generation (Feature 016)
lyria_gcp_project_id: str = ""          # GCP Project ID (或使用 ADC 自動偵測)
lyria_gcp_location: str = "us-central1" # Vertex AI 部署區域
lyria_model: str = "lyria-002"          # 模型代號
lyria_timeout: float = 30.0             # API 請求逾時（秒）
```

**環境變數**：

| 環境變數 | 預設值 | 說明 |
|---|---|---|
| `LYRIA_GCP_PROJECT_ID` | `""` (ADC 自動偵測) | GCP Project ID |
| `LYRIA_GCP_LOCATION` | `us-central1` | Vertex AI 部署區域 |
| `LYRIA_MODEL` | `lyria-002` | 模型代號（未來可切換至 `lyria-003-experimental`） |
| `LYRIA_TIMEOUT` | `30.0` | API 請求逾時秒數 |

---

## Database Migration

**不需要 Alembic migration**。

`music_generation_jobs.provider` 欄位為 VARCHAR，可直接存放新的 `"lyria"` 字串值。`music_generation_jobs.type` 欄位已支援 `"instrumental"` 值。

---

## 狀態轉換差異

### Mureka（非同步 polling）

```
PENDING → PROCESSING (worker 提交至 Mureka) → COMPLETED (polling 確認完成)
                                              → FAILED (polling 確認失敗/逾時)
```

### Lyria（同步回應）

```
PENDING → PROCESSING (worker 開始處理) → COMPLETED (Vertex AI 回應 + WAV→MP3 完成)
                                        → FAILED (API 錯誤/安全過濾/轉換失敗)
```

> **差異**：Lyria 的 PROCESSING 狀態非常短暫（~10s），因為 Vertex AI 為同步 API。Worker 提交後直接收到結果，不需要 polling。

---

*Last updated: 2026-02-19*

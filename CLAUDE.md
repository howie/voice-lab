# voice-lab Development Guidelines

Auto-generated from all feature plans. Last updated: 2026-01-16

## Active Technologies
- Python 3.11+ (Backend), TypeScript 5.3+ (Frontend) (001-pipecat-tts-server)
- Local filesystem (`storage/{provider}/{uuid}.mp3`), SQLAlchemy + PostgreSQL (metadata) (001-pipecat-tts-server)
- Python 3.11+ (Backend), TypeScript 5.3+ (Frontend) + FastAPI 0.109+, SQLAlchemy 2.0+, Pydantic 2.0+, React 18+ (002-provider-mgmt-interface)
- PostgreSQL with TDE (Transparent Data Encryption) (002-provider-mgmt-interface)
- PostgreSQL (transcription history), Local filesystem (uploaded audio) (003-stt-testing-module)
- PostgreSQL 16 (對話歷史), Local filesystem (音訊檔案), Redis 7 (快取) (004-interaction-module)
- Python 3.11+ (Backend), TypeScript 5.3+ (Frontend) + FastAPI 0.109+, Pydantic 2.0+, React 18+, Zustand, pydub (音訊合併) (005-multi-role-tts)
- Local filesystem (音訊檔案), PostgreSQL (元資料) (005-multi-role-tts)
- Terraform 1.6+ (HCL), Python 3.11+ (Backend), TypeScript 5.3+ (Frontend) (006-gcp-terraform-deploy)
- PostgreSQL (工作元資料), Local filesystem / S3 (音檔儲存) (007-async-job-mgmt)
- Python 3.11+ (Backend), TypeScript 5.3+ (Frontend) + FastAPI 0.109+, SQLAlchemy 2.0+, Pydantic 2.0+, React 18+, httpx (Mureka API client) (012-music-generation)
- PostgreSQL (任務元資料), Local filesystem / S3 (音檔儲存) (012-music-generation)

- Python 3.11+ + FastAPI 0.109+, azure-cognitiveservices-speech, google-cloud-texttospeech, elevenlabs, httpx (001-pipecat-tts-server)

## Project Structure

```text
src/
tests/
```

## Commands

cd src [ONLY COMMANDS FOR ACTIVE TECHNOLOGIES][ONLY COMMANDS FOR ACTIVE TECHNOLOGIES] pytest [ONLY COMMANDS FOR ACTIVE TECHNOLOGIES][ONLY COMMANDS FOR ACTIVE TECHNOLOGIES] ruff check .

## Code Style

Python 3.11+: Follow standard conventions

## Recent Changes
- 012-music-generation: Added Python 3.11+ (Backend), TypeScript 5.3+ (Frontend) + FastAPI 0.109+, SQLAlchemy 2.0+, Pydantic 2.0+, React 18+, httpx (Mureka API client)
- 007-async-job-mgmt: Added Python 3.11+ (Backend), TypeScript 5.3+ (Frontend)
- 006-gcp-terraform-deploy: Added Terraform 1.6+ (HCL), Python 3.11+ (Backend), TypeScript 5.3+ (Frontend)


<!-- MANUAL ADDITIONS START -->

## Development Workflow (CRITICAL)

### Before ANY Code Changes

1. **When editing files, ALWAYS follow these rules**:
   - Use Python 3.10+ type annotations: `X | Y` instead of `Union[X, Y]`
   - Import `Sequence` from `collections.abc` not `typing`
   - Follow ruff formatting rules (proper indentation, line breaks, spacing)
   - No wildcard imports (`from module import *`)
   - Organize imports: stdlib, third-party, local (with blank lines between)

2. **Before EVERY commit**:
   ```bash
   make check  # MUST pass completely
   ```
   This runs:
   - `ruff check` (linting)
   - `ruff format --check` (formatting)
   - `mypy` (type checking)
   - `eslint` (frontend)
   - `tsc` (frontend type checking)

3. **If make check fails**:
   - Fix issues BEFORE committing
   - Use `ruff format .` to auto-format
   - Use `ruff check . --fix` to auto-fix lint issues
   - Never commit code that doesn't pass `make check`

### Why This Matters

- Prevents CI failures
- Maintains code quality
- Saves time (no back-and-forth fixes)
- Professional development standards

### Adding Dependencies or Enabling Providers (CRITICAL)

**⚠️ 本地能跑 ≠ CI 能跑**

When adding new dependencies or enabling existing providers:

1. **Check existing dependencies FIRST**:
   ```bash
   grep -i <package-name> backend/pyproject.toml
   ```

2. **Update `pyproject.toml`, NOT local pip install**:
   - Local `pip install` is temporary and won't reflect in CI
   - Always add dependencies to `pyproject.toml`

3. **Verify import paths match package**:
   - Different packages may have different import structures
   - e.g., `speechmatics-python` vs `speechmatics-batch` have different APIs

4. **Use project install to test**:
   ```bash
   cd backend && uv sync  # or pip install -e .
   ```

5. **Wait for CI to pass** before considering work complete

**Checklist for enabling a provider**:
```
- [ ] Check pyproject.toml for existing related dependencies
- [ ] Update pyproject.toml if new dependency needed
- [ ] Run `uv sync` to install via project config (not pip install)
- [ ] Verify import paths match the installed package
- [ ] Run `make check` and `make test` locally
- [ ] Push and verify CI passes
```

### Code Format Requirements

**Python**:
```python
# ✅ CORRECT
def foo(x: str | None = None) -> str | int:
    pass

# ❌ WRONG
def foo(x: Union[str, None] = None) -> Union[str, int]:
    pass
```

**Imports**:
```python
# ✅ CORRECT
import asyncio
from collections.abc import Sequence

from alembic import context
from sqlalchemy import pool

from src.domain.models import User

# ❌ WRONG
from typing import Sequence, Union
from src.domain.models import *
```

### 004-Interaction-Module Specifics

**WebSocket Connection**:
```bash
# Connect to WebSocket for voice interaction
ws://localhost:8000/api/v1/interaction/ws
```

**WebSocket Message Types**:
- `configure`: Set interaction mode (realtime/cascade), voice settings
- `start_listening`: Begin voice capture
- `stop_listening`: Stop voice capture
- `audio_chunk`: Send audio data (base64 encoded)
- `interrupt`: Barge-in/stop AI response

**API Endpoints**:
```bash
# List interaction sessions
GET /api/v1/interaction/sessions

# Get session details
GET /api/v1/interaction/sessions/{session_id}

# Get session turns
GET /api/v1/interaction/sessions/{session_id}/turns

# Get latency stats
GET /api/v1/interaction/sessions/{session_id}/latency

# Get turn audio
GET /api/v1/interaction/sessions/{session_id}/turns/{turn_id}/audio
```

**Testing Interaction Module**:
```bash
# Run interaction-specific tests
pytest backend/tests -k interaction

# Run with coverage
pytest backend/tests --cov=backend/src/domain/services/interaction
```

### GCP Deployment (CRITICAL)

#### Docker Build for Cloud Run

**⚠️ 必須指定 platform，否則 ARM 架構的 image 無法在 Cloud Run 上運行**

```bash
# ✅ CORRECT - 指定 amd64 架構
docker build --platform linux/amd64 -f backend/Dockerfile -t <image> .
docker build --platform linux/amd64 -f frontend/Dockerfile -t <image> .

# ❌ WRONG - 預設使用本機架構 (Mac M1/M2 是 ARM)
docker build -f backend/Dockerfile -t <image> .
```

**錯誤訊息**: `exec format error` 表示架構不匹配

#### Terraform 環境變數格式

**⚠️ Backend config 預期逗號分隔格式，不是 JSON array**

```hcl
# ✅ CORRECT - 使用 join() 產生逗號分隔字串
env {
  name  = "ALLOWED_DOMAINS"
  value = join(",", var.allowed_domains)  # 輸出: "heyuai.com.tw,example.com"
}

# ❌ WRONG - jsonencode() 產生 JSON array
env {
  name  = "ALLOWED_DOMAINS"
  value = jsonencode(var.allowed_domains)  # 輸出: ["heyuai.com.tw","example.com"]
}
```

**受影響的環境變數**:
- `ALLOWED_DOMAINS` - OAuth 允許的 email 網域
- `CORS_ORIGINS` - CORS 允許的來源

#### 環境變數名稱一致性

**⚠️ Terraform 和 Backend 的環境變數名稱必須匹配**

| Terraform 設定 | Backend 讀取 |
|---|---|
| `GOOGLE_OAUTH_CLIENT_ID` | `GOOGLE_OAUTH_CLIENT_ID` 或 `GOOGLE_CLIENT_ID` |
| `GOOGLE_OAUTH_CLIENT_SECRET` | `GOOGLE_OAUTH_CLIENT_SECRET` 或 `GOOGLE_CLIENT_SECRET` |

**教訓**: 修改環境變數時，必須同時檢查 Terraform 和 Backend 程式碼

#### 部署前檢查清單

```
- [ ] Docker build 使用 --platform linux/amd64
- [ ] Terraform 環境變數使用 join() 而非 jsonencode()
- [ ] 環境變數名稱在 Terraform 和 Backend 中一致
- [ ] 測試本地 health endpoint: curl localhost:8000/api/v1/health
- [ ] 部署後測試 production health endpoint
- [ ] 測試 OAuth 登入流程
```

<!-- MANUAL ADDITIONS END -->

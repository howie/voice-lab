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
- 006-gcp-terraform-deploy: Added Terraform 1.6+ (HCL), Python 3.11+ (Backend), TypeScript 5.3+ (Frontend)
- 005-multi-role-tts: Added Python 3.11+ (Backend), TypeScript 5.3+ (Frontend) + FastAPI 0.109+, Pydantic 2.0+, React 18+, Zustand, pydub (音訊合併)
- 004-interaction-module: Added Python 3.11+ (Backend), TypeScript 5.3+ (Frontend)
- 003-stt-testing-module: Added Python 3.11+ (Backend), TypeScript 5.3+ (Frontend)


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

<!-- MANUAL ADDITIONS END -->

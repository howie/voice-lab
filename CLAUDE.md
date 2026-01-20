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
- 005-multi-role-tts: Added Python 3.11+ (Backend), TypeScript 5.3+ (Frontend) + FastAPI 0.109+, Pydantic 2.0+, React 18+, Zustand, pydub (音訊合併)
- 004-interaction-module: Added Python 3.11+ (Backend), TypeScript 5.3+ (Frontend)
- 003-stt-testing-module: Added Python 3.11+ (Backend), TypeScript 5.3+ (Frontend)
- 002-provider-mgmt-interface: Added Python 3.11+ (Backend), TypeScript 5.3+ (Frontend) + FastAPI 0.109+, SQLAlchemy 2.0+, Pydantic 2.0+, React 18+


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

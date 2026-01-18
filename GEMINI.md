# voice-lab Development Guidelines

Auto-generated from all feature plans. Last updated: 2026-01-18

## Active Technologies

- Python 3.11+ (001-pipecat-tts-server)
- TypeScript/React (001-pipecat-tts-server, 002-provider-mgmt-interface)
- PostgreSQL 16 (002-provider-mgmt-interface)

## Project Structure

```text
backend/src/
backend/tests/
frontend/src/
```

## Commands

cd backend && uv run uvicorn src.main:app --reload
cd frontend && npm run dev
cd backend && uv run pytest
cd backend && uv run ruff check .

## Code Style

Python 3.11+: Follow standard conventions
TypeScript: React 18+ best practices

## Recent Changes

- 002-provider-mgmt-interface: Implemented BYOL credential management with encryption and audit logging.
- 001-pipecat-tts-server: Implemented unified TTS server with multi-provider support.

<!-- MANUAL ADDITIONS START -->
<!-- MANUAL ADDITIONS END -->

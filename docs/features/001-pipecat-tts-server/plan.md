# Implementation Plan: Pipecat TTS Server

**Branch**: `001-pipecat-tts-server` | **Date**: 2026-01-16 | **Spec**: [docs/features/001-pipecat-tts-server/spec.md](./spec.md)
**Input**: Feature specification from `docs/features/001-pipecat-tts-server/spec.md`

## Summary

This feature implements a unified TTS (Text-to-Speech) API server using FastAPI, supporting Azure, Google, and ElevenLabs providers. It includes a Web Interface for testing and demonstrating TTS capabilities. The implementation follows Clean Architecture and integrates `pipecat-ai` for future real-time capabilities.

## Technical Context

**Language/Version**: Python 3.11+
**Primary Dependencies**:
- Web Framework: `fastapi`, `uvicorn`
- Voice: `pipecat-ai` (to be added), `azure-cognitiveservices-speech`, `google-cloud-texttospeech`, `elevenlabs`
- Database: `sqlalchemy`, `asyncpg` (PostgreSQL)
- Frontend: React, Vite, Tailwind CSS
**Storage**: Local filesystem (dev) / S3 (prod) for audio files; PostgreSQL for request logs.
**Testing**: `pytest`, `pytest-asyncio`
**Target Platform**: Docker container (Linux)
**Project Type**: Full-stack (FastAPI Backend + React Frontend)
**Performance Goals**: <200ms TTFB for cached/fast providers; support 10 concurrent requests.
**Constraints**: Single server deployment initially.
**Scale/Scope**: MVP focus, extensible to distributed later.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- [x] **I. TDD**: Plan includes contract and integration tests.
- [x] **II. Unified API**: `ITTSProvider` interface already exists; implementation will adhere to it.
- [x] **III. Performance**: Benchmarking included in requirements (SC-001).
- [x] **IV. Documentation First**: Plan includes generating `contracts/` and `quickstart.md` before coding.
- [x] **V. Clean Architecture**: Existing project structure enforces this.

## Project Structure

### Documentation (this feature)

```text
docs/features/001-pipecat-tts-server/
├── plan.md              # This file
├── research.md          # Technology decisions
├── data-model.md        # Entity definitions
├── quickstart.md        # Setup guide
├── contracts/           # OpenAPI spec
│   └── openapi.yaml
└── tasks.md             # Implementation tasks
```

### Source Code (repository root)

```text
backend/
├── src/
│   ├── application/
│   │   ├── interfaces/
│   │   │   └── tts_provider.py  # Existing Interface
│   │   └── use_cases/
│   │       ├── synthesize_speech.py
│   │       └── list_voices.py
│   ├── domain/
│   │   └── entities/
│   │       ├── tts.py          # Request/Result models
│   │       └── voice.py        # Voice models
│   ├── infrastructure/
│   │   ├── persistence/        # SQLAlchemy repositories
│   │   └── providers/
│   │       └── tts/            # Pipecat/GCP/Azure/ElevenLabs adapters
│   └── presentation/
│       └── api/
│           └── routes/
│               └── tts.py
└── tests/
    ├── contract/               # Provider API tests
    └── integration/            # End-to-end API tests

frontend/
├── src/
│   ├── components/
│   │   └── tts/
│   │       ├── TTSForm.tsx
│   │       └── AudioPlayer.tsx
│   ├── services/
│   │   └── api.ts
│   └── routes/
│       └── tts/
│           └── TTSPage.tsx
```

**Structure Decision**: Option 2: Web application (Separate Backend/Frontend).

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| None | N/A | N/A |
# Research: Pipecat TTS Server

**Feature**: `001-pipecat-tts-server`
**Date**: 2026-01-16

## Decisions

### 1. Framework Selection
*   **Decision**: Use **FastAPI** for the backend REST API.
*   **Rationale**:
    *   Project already uses FastAPI (`backend/pyproject.toml`).
    *   High performance (async support) crucial for TTS latency.
    *   Excellent OpenAPI integration (Constitution Principle II: Unified API).
*   **Alternatives Considered**:
    *   Django: Too heavy for this microservice-like requirement.
    *   Flask: Lack of native async support makes handling concurrent TTS requests less efficient.

### 2. Pipecat Integration
*   **Decision**: Add `pipecat-ai` as a dependency.
*   **Rationale**:
    *   Feature name is "Pipecat TTS Server".
    *   Spec explicitly states "Assumption: Pipecat framework is already functional".
    *   Pipecat provides robust transport layers and pipeline abstractions useful for the future streaming/real-time interaction features (User Story 1 & 2).
*   **Note**: Currently missing from `pyproject.toml`. Will be added during implementation.

### 3. Database
*   **Decision**: Use **PostgreSQL** (via `asyncpg` + `SQLAlchemy`).
*   **Rationale**:
    *   Already configured in `.env.example` and dependencies.
    *   Required for "FR-010: Record all API requests".
    *   Robustness over SQLite for concurrent writes (benchmarking).

### 4. Storage for Audio
*   **Decision**: Use **Local Filesystem** initially, with interface for S3.
*   **Rationale**:
    *   Simple for MVP ("FR-005: Download function").
    *   `STORAGE_TYPE` env var already exists in `.env.example`.

### 5. Frontend
*   **Decision**: Use **React** + **Vite** + **Tailwind**.
*   **Rationale**:
    *   Existing `frontend/` directory structure supports this.
    *   Fast iteration for Web Interface (User Story 2).

## Clarifications Resolved

*   **Database Usage**: Confirmed PostgreSQL is the intended target via `.env.example`.
*   **Pipecat Status**: Confirmed it's missing from dependencies and needs to be added to fulfill the "Pipecat-based" requirement.
*   **Architecture**: Validated Clean Architecture structure in `backend/src`.

## References
*   [FastAPI Documentation](https://fastapi.tiangolo.com/)
*   [Pipecat AI Docs](https://docs.pipecat.ai/)
*   [Voice Lab Constitution](../../../.specify/memory/constitution.md)
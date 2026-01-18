# Voice Lab Roadmap

**Last Updated**: 2026-01-18
**Current Status**: Phase 2 Complete (Foundational & TTS)

---

## 🚀 Completed Features

### 001: Pipecat TTS Server
- **Status**: ✅ COMPLETED (2026-01-16)
- **Description**: Unified TTS abstraction layer using Pipecat, supporting Azure, GCP, ElevenLabs, and VoAI.
- **Key Capabilities**:
  - Batch and Streaming synthesis modes.
  - Multi-provider support (Azure, Google, ElevenLabs, VoAI).
  - Parameter control (Speed, Pitch, Volume).
  - Web UI for testing and listening.
  - Integration with WaveSurfer.js for waveform display.
  - Google SSO Authentication.

### 002: Provider API Key Management Interface
- **Status**: ✅ COMPLETED (2026-01-18)
- **Description**: Enable users to manage their own TTS/STT provider API keys at runtime (BYOL - Bring Your Own License).
- **Key Capabilities**:
  - Secure storage and validation of user-specific API keys.
  - Support for ElevenLabs, Azure, and Google Gemini.
  - Model selection persistence per provider.
  - Full audit trail for all credential operations and usage.
  - Rate limit handling and status visibility.
  - Automatic fallback to system-level credentials when user keys are unavailable.

---

## 📅 Upcoming Roadmap

### Phase 3: STT (Speech-to-Text) Module (Current Goal)
- **Objective**: Build a testing platform for Speech-to-Text across different providers.
- **Key Tasks**:
  - Implement STT Abstraction Layer.
  - Integrate GCP, Azure, and VoAI STT.
  - Microphone recording and file upload functionality.
  - Streaming transcription via WebSocket.
  - WER (Word Error Rate) calculation and ground-truth comparison.
  - "Child Voice Mode" optimization testing.

### Phase 4: Interaction Module
- **Objective**: Test end-to-end real-time voice interaction (STT + LLM + TTS).
- **Key Tasks**:
  - Real-time voice chat interface.
  - End-to-end latency measurement (STT -> LLM -> TTS).
  - System Prompt configuration and scenario templates.
  - Support for打斷 (Barge-in) testing.

### Phase 5: Polish & Advanced Features
- **Objective**: Professional-grade features and reporting.
- **Key Tasks**:
  - Batch processing (CSV/Excel upload for TTS/STT).
  - Comparative reports (Excel/PDF export).
  - Audio post-processing (Mixing background music, EQ).
  - Advanced performance optimization.

---

## 📈 Milestones

| Milestone | Status | Target Date | Actual Date |
|-----------|--------|-------------|-------------|
| **M1: TTS MVP** | ✅ | 2026-01-18 | 2026-01-16 |
| **M2: BYOL Credential Mgmt** | ✅ | 2026-01-20 | 2026-01-18 |
| **M3: STT Complete** | ⏳ | 2026-02-15 | - |
| **M4: Interaction Complete** | ⏳ | 2026-03-15 | - |
| **M5: Production Ready** | ⏳ | 2026-04-15 | - |

---

## 🛠 Active Technologies
- **Backend**: Python 3.11+ (FastAPI, SQLAlchemy, Pipecat-AI, Alembic)
- **Frontend**: React 18 (Vite, TypeScript, Tailwind CSS, Shadcn/ui)
- **Database**: PostgreSQL 16
- **Cache**: Redis 7

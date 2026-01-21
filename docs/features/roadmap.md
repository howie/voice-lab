# Voice Lab Roadmap

**Last Updated**: 2026-01-20
**Current Status**: Phase 3.5 Complete (Infrastructure & Multi-Role TTS)

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

### 003: STT Speech-to-Text Testing Module
- **Status**: ✅ COMPLETED (2026-01-19)
- **Description**: Comprehensive testing platform for Batch & High-Accuracy STT across leading providers.
- **Key Capabilities**:
  - STT Abstraction Layer with unified provider interface.
  - **8 Providers Supported**:
    - **Cloud Giants**: Azure Speech, Google Cloud STT.
    - **Specialized Leaders**: OpenAI Whisper, Deepgram (Nova-2), AssemblyAI, ElevenLabs Scribe, Speechmatics.
  - Microphone recording (WebM/MP4) and file upload (MP3, WAV, M4A, FLAC, WEBM).
  - WER (Word Error Rate) & CER (Character Error Rate) calculation with alignment visualization.
  - "Child Voice Mode" optimization for Azure and GCP.
  - Multi-provider side-by-side comparison with parallel processing.
  - Transcription history with search and filtering.
  - Provider-specific file size/duration limit display.

### 005: Multi-Role TTS
- **Status**: ✅ COMPLETED (2026-01-20)
- **Description**: 多角色 TTS 合成功能，支援對話逐字稿轉換為多聲音音訊檔案。
- **Key Capabilities**:
  - 對話逐字稿解析（自動識別 A:、B: 等說話者標記）。
  - 最多支援 6 位說話者。
  - Provider 原生多角色支援（ElevenLabs Audio Tags）。
  - 不支援原生多角色的 Provider 使用分段合併方式。
  - 各 Provider 能力差異比較與功能提示。
  - 進階音效標籤支援（interrupting、overlapping、laughs 等）。

### 006: GCP Terraform Deploy
- **Status**: ✅ COMPLETED (2026-01-20)
- **Description**: 使用 Terraform 將 Voice Lab 部署到 GCP，支援網域限制登入。
- **Key Capabilities**:
  - 一鍵 Terraform 部署（`terraform apply`）。
  - 特定網域登入限制（如 heyuai.com.tw）。
  - 成本最佳化配置。
  - Cloud Run 服務部署。
  - Cloud SQL (PostgreSQL) 與 Redis Memorystore。
  - Cloud Storage 音訊檔案儲存。

### 007: Async Job Management
- **Status**: ✅ COMPLETED (2026-01-20)
- **Description**: 背景工作管理系統，支援 TTS 合成工作在背景執行。
- **Key Capabilities**:
  - 背景工作執行（離開頁面不中斷）。
  - Job 狀態追蹤（pending/processing/completed/failed）。
  - 歷史記錄查詢（最近 30 天）。
  - 音檔重播與下載。
  - 原始參數保留。

---

## 📅 Upcoming Roadmap

### Phase 4: Interaction Module (Current Goal)
- **Objective**: Test end-to-end **Real-time Voice Agent** interaction (Streaming STT + LLM + TTS).
- **Key Tasks**:
  - **Streaming STT Integration** (Low Latency):
    - Deepgram (Nova-2/Flux), AssemblyAI Streaming, OpenAI Realtime API.
  - Real-time voice chat interface.
  - End-to-end latency measurement (STT -> LLM -> TTS).
  - System Prompt configuration and scenario templates.
  - Support for Interruption (Barge-in) testing.

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
| **M3: STT Complete** | ✅ | 2026-02-15 | 2026-01-19 |
| **M3.5: Multi-Role TTS** | ✅ | - | 2026-01-20 |
| **M3.6: GCP Deployment** | ✅ | - | 2026-01-20 |
| **M3.7: Async Job Mgmt** | ✅ | - | 2026-01-20 |
| **M4: Interaction Complete** | ⏳ | 2026-03-15 | - |
| **M5: Production Ready** | ⏳ | 2026-04-15 | - |

---

## 🛠 Active Technologies
- **Backend**: Python 3.11+ (FastAPI, SQLAlchemy, Pipecat-AI, Alembic)
- **Frontend**: React 18 (Vite, TypeScript, Tailwind CSS, Shadcn/ui)
- **Database**: PostgreSQL 16
- **Cache**: Redis 7
- **Infrastructure**: Terraform 1.6+ (GCP Cloud Run, Cloud SQL, Memorystore)

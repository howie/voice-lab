# Research: Pipecat TTS Server

## 4. TTS Provider Engine
**Decision**: 使用 Pipecat 內建的 TTS Services

**Pipecat 內建 TTS 提供者**:

| Provider | Pipecat Service | 備註 |
|----------|-----------------|------|
| Azure Speech | `pipecat.services.azure.tts.AzureTTSService` | 完整支援串流 |
| ElevenLabs | `pipecat.services.elevenlabs.tts.ElevenLabsTTSService` | 高品質語音 |
| Google Cloud | `pipecat.services.google.tts.GoogleTTSService` | 支援 gRPC 串流 |
| VoAI | 需自訂 `BaseTTSService` | 台灣本土供應商 |

**Rationale**:
- Pipecat 已封裝各提供者的串流邏輯，減少重複開發
- 統一的 Frame 介面（TextFrame → AudioRawFrame）
- VoAI 需建立自訂 Service，但可繼承 `BaseTTSService` 快速實作

**VoAI 自訂 Service 範例**:

```python
from pipecat.services.ai_services import TTSService
from pipecat.frames.frames import AudioRawFrame, TextFrame
import httpx
from typing import AsyncGenerator

class VoAITTSService(TTSService):
    def __init__(self, api_key: str, voice_id: str):
        super().__init__()
        self.api_key = api_key
        self.voice_id = voice_id

    async def run_tts(self, text: str) -> AsyncGenerator[AudioRawFrame, None]:
        async with httpx.AsyncClient() as client:
            async with client.stream("POST", VOAI_ENDPOINT, json={...}) as response:
                async for chunk in response.aiter_bytes():
                    yield AudioRawFrame(audio=chunk, sample_rate=24000, num_channels=1)
```

### 5. Web 前端串流播放

**Decision**: 使用 Web Audio API + MediaSource Extensions

**Rationale**:
- Web Audio API 支援即時音訊處理與波形視覺化
- MediaSource Extensions (MSE) 支援串流音訊播放
- 主流瀏覽器（Chrome、Firefox、Safari、Edge）皆支援

**Technical Approach**:

```javascript
// 串流播放
const mediaSource = new MediaSource();
audioElement.src = URL.createObjectURL(mediaSource);

mediaSource.addEventListener('sourceopen', () => {
  const sourceBuffer = mediaSource.addSourceBuffer('audio/mpeg');
  // 接收音訊 chunk 並加入 buffer
});

// 波形視覺化
const audioContext = new AudioContext();
const analyser = audioContext.createAnalyser();
// 使用 requestAnimationFrame 繪製波形
```

**Alternatives Considered**:
- 使用第三方播放器庫（如 Howler.js）：增加依賴，但簡化開發
- 完全自建播放器：控制度高但開發成本高
- **採用混合方案**：基礎使用原生 API，複雜功能引入 WaveSurfer.js

### 6. 語言支援

**Decision**: 延用現有語言映射機制

**Supported Languages**:
- 中文（繁體）：zh-TW
- 中文（簡體）：zh-CN / cmn-CN
- 英文：en-US
- 日文：ja-JP
- 韓文：ko-KR

**Rationale**:
- 現有提供者實作已包含語言映射邏輯
- 各提供者語言代碼格式不同，統一由內部映射處理

### 7. 效能目標

**Decision**: 依據規格定義的成功標準

| Metric | Target | Measurement |
|--------|--------|-------------|
| TTFB (Time to First Byte) | < 500ms | 串流模式首 chunk 延遲 |
| 完整合成延遲 | < 5s (100字) | 批次模式總耗時 |
| 並發處理 | 10 concurrent | 同時請求數 |
| 成功率 | 90%+ | 首次請求成功比例 |

## Technical Stack Summary

### Backend

- **Framework**: FastAPI 0.109+ (REST API) + Pipecat 0.0.50+ (Pipeline)
- **Runtime**: Python 3.11+, asyncio
- **Core Dependencies**:
  - `pipecat-ai[azure,elevenlabs,google]` - Pipeline 框架與 TTS Services
  - `fastapi` + `uvicorn` - REST API 伺服器
  - `websockets` - WebSocket Transport
  - `httpx` - VoAI 自訂 Service
- **Streaming**: Pipecat Pipeline + WebSocket Transport
- **Testing**: pytest, pytest-asyncio

### Frontend

- **Framework**: React (based on project structure)
- **Audio**: Web Audio API, MediaSource Extensions
- **Visualization**: WaveSurfer.js (建議)
- **HTTP Client**: fetch API with ReadableStream

### Infrastructure

- **Server**: Uvicorn (ASGI)
- **Configuration**: Environment variables, pydantic-settings
- **Logging**: structlog (structured logging)

## Resolved Clarifications

| Item | Resolution |
|------|------------|
| Pipecat 整合必要性 | **必要** - PRD 規劃 Interaction 模組需要完整 Pipeline |
| 串流技術選型 | Pipecat Pipeline + WebSocket Transport（保留 HTTP Streaming 備用） |
| 前端播放器 | Web Audio API + WaveSurfer.js |
| 提供者優先順序 | Azure、ElevenLabs、GCP（Pipecat 內建），VoAI（自訂 Service） |

## Risks & Mitigations

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| Pipecat 版本更新頻繁 | Medium | Medium | 鎖定穩定版本，定期追蹤更新 |
| VoAI 自訂 Service 開發成本 | Low | Low | 參考 Pipecat 官方 Service 實作 |
| 瀏覽器相容性問題 | Low | Medium | 提供降級方案（批次模式） |
| Pipeline 架構學習曲線 | Medium | Low | 建立開發文件與範例 |

## Next Steps

1. **Phase 1**: 建立 Pipecat Pipeline 基礎架構
2. **Phase 1**: 整合 Azure/ElevenLabs/GCP TTS Services
3. **Phase 1**: 實作 VoAI 自訂 TTS Service
4. **Phase 1**: 建立 WebSocket Transport 與 FastAPI 整合
5. **Phase 1**: 前端串流播放與波形視覺化
6. **Phase 2**: 整合測試與效能驗證

## References
*   [FastAPI Documentation](https://fastapi.tiangolo.com/)
*   [Pipecat AI Docs](https://docs.pipecat.ai/)
*   [Voice Lab Constitution](../../../.specify/memory/constitution.md)

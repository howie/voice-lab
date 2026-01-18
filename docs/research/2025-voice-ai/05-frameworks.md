# Voice AI 框架研究

> 最後更新：2025-01

## 概述

Voice AI 框架提供完整的 pipeline 管理，整合 STT、LLM、TTS 等元件。選擇合適的框架可大幅加速開發。

## 框架比較

### Pipecat

**狀態**: ✅ 推薦 - 快速開發

| 項目 | 說明 |
|------|------|
| 開發者 | Daily |
| 授權 | BSD-2-Clause |
| 語言 | Python |
| GitHub | [pipecat-ai/pipecat](https://github.com/pipecat-ai/pipecat) |

**架構**:
```
┌─────────────────────────────────────────────┐
│                  Pipeline                    │
├──────┬──────┬──────┬──────┬──────┬──────────┤
│ VAD  │ STT  │ LLM  │ TTS  │ Audio│ Transport│
└──────┴──────┴──────┴──────┴──────┴──────────┘
```

**特點**:
- 簡潔的 Pipeline API
- 豐富的服務整合 (20+ 服務)
- 內建 VAD、中斷處理
- 支援 Daily、WebSocket、WebRTC
- 活躍的社群

**優點**:
- 學習曲線平緩
- 程式碼簡潔
- 快速原型開發
- 文件完整

**缺點**:
- 大規模部署需自行處理
- 預設使用 Daily (付費)
- 自訂性較 LiveKit 低

**範例**:
```python
import asyncio
from pipecat.pipeline.pipeline import Pipeline
from pipecat.pipeline.runner import PipelineRunner
from pipecat.services.deepgram import DeepgramSTTService
from pipecat.services.openai import OpenAILLMService
from pipecat.services.cartesia import CartesiaTTSService
from pipecat.transports.services.daily import DailyTransport

async def main():
    transport = DailyTransport(
        room_url="https://your-domain.daily.co/room",
        token="your-token"
    )

    stt = DeepgramSTTService(api_key=DEEPGRAM_API_KEY)
    llm = OpenAILLMService(api_key=OPENAI_API_KEY, model="gpt-4o")
    tts = CartesiaTTSService(api_key=CARTESIA_API_KEY, voice_id="voice-id")

    pipeline = Pipeline([
        transport.input(),
        stt,
        llm,
        tts,
        transport.output()
    ])

    runner = PipelineRunner()
    await runner.run(pipeline)

asyncio.run(main())
```

**適用場景**: 快速原型、小中型專案、學習用途

---

### LiveKit

**狀態**: ✅ 推薦 - 生產級

| 項目 | 說明 |
|------|------|
| 開發者 | LiveKit Inc. |
| 授權 | Apache-2.0 |
| 語言 | Go (Server), Python/JS (SDK) |
| GitHub | [livekit/livekit](https://github.com/livekit/livekit) |

**架構**:
```
┌─────────────────────────────────────────────┐
│              LiveKit Server (SFU)           │
├─────────────────────────────────────────────┤
│              Agents Framework               │
├──────┬──────┬──────┬──────┬─────────────────┤
│ VAD  │ STT  │ LLM  │ TTS  │ Custom Plugins  │
└──────┴──────┴──────┴──────┴─────────────────┘
```

**特點**:
- 完整的 WebRTC SFU
- Agents Framework for Voice AI
- 可自行部署
- 企業級可擴展性
- 豐富的 SDK (Go, Python, JS, Swift, Kotlin)

**優點**:
- 生產級可靠性
- 高度可擴展
- 自部署選項
- 完整的房間管理

**缺點**:
- 學習曲線較陡
- 架構較複雜
- 自部署需要維運

**範例**:
```python
from livekit import agents
from livekit.agents import JobContext, WorkerOptions
from livekit.agents.voice_assistant import VoiceAssistant
from livekit.plugins import deepgram, openai, cartesia

async def entrypoint(ctx: JobContext):
    await ctx.connect()

    assistant = VoiceAssistant(
        vad=ctx.proc.userdata["vad"],
        stt=deepgram.STT(),
        llm=openai.LLM(model="gpt-4o"),
        tts=cartesia.TTS(),
    )

    assistant.start(ctx.room)
    await assistant.say("你好，有什麼我可以幫你的？")

if __name__ == "__main__":
    agents.cli.run_app(WorkerOptions(entrypoint_fnc=entrypoint))
```

**部署選項**:
| 選項 | 說明 |
|------|------|
| LiveKit Cloud | 全託管，最簡單 |
| Self-hosted | 完全控制，需維運 |
| Hybrid | Cloud + 自有 agents |

**適用場景**: 生產環境、大規模部署、企業應用

---

## 功能比較表

| 功能 | Pipecat | LiveKit |
|------|---------|---------|
| 學習曲線 | 平緩 | 中等 |
| Pipeline 設計 | 線性 | 事件驅動 |
| WebRTC 內建 | ❌ (透過 Daily) | ✅ |
| SFU 伺服器 | ❌ | ✅ |
| 自部署 | ⚠️ 部分 | ✅ |
| 中斷處理 | ✅ | ✅ |
| VAD | ✅ | ✅ |
| Function Calling | ✅ | ✅ |
| 企業支援 | ⚠️ | ✅ |

## 選型決策樹

```
                    ┌─────────────────────┐
                    │ 需要自部署 WebRTC？  │
                    └──────────┬──────────┘
                               │
              ┌────────────────┴────────────────┐
              ▼                                 ▼
             是                                否
              │                                 │
              ▼                                 │
         ┌─────────┐                           │
         │ LiveKit │                           │
         └─────────┘                           │
                                               │
                           ┌───────────────────┤
                           ▼                   │
                    ┌─────────────┐            │
                    │ 快速原型？   │            │
                    └──────┬──────┘            │
                           │                   │
              ┌────────────┴────────────┐      │
              ▼                         ▼      │
             是                        否      │
              │                         │      │
              ▼                         ▼      ▼
         ┌─────────┐              ┌─────────────┐
         │ Pipecat │              │ 評估兩者皆可│
         └─────────┘              └─────────────┘
```

## 延遲優化

### Pipecat
```python
# 啟用 VAD，減少靜音處理
pipeline = Pipeline([
    vad,  # Silero VAD
    stt,
    UserIdleProcessor(timeout=5.0),  # 處理用戶靜默
    llm,
    SentenceAggregator(),  # 分句處理
    tts,
    transport.output()
])
```

### LiveKit
```python
assistant = VoiceAssistant(
    vad=silero.VAD.load(),
    stt=deepgram.STT(),
    llm=openai.LLM(model="gpt-4o"),
    tts=cartesia.TTS(),
    # 調整中斷敏感度
    interrupt_min_words=2,
    # 啟用預先合成
    preemptive_synthesis=True,
)
```

## 部署架構

### Pipecat + Daily
```
┌─────────┐     ┌─────────────┐     ┌──────────────┐
│ 瀏覽器  │────▶│ Daily Cloud │────▶│ Pipecat Bot  │
└─────────┘     └─────────────┘     └──────────────┘
                                           │
                              ┌────────────┼────────────┐
                              ▼            ▼            ▼
                          ┌─────┐     ┌─────┐     ┌─────┐
                          │ STT │     │ LLM │     │ TTS │
                          └─────┘     └─────┘     └─────┘
```

### LiveKit Self-hosted
```
┌─────────┐     ┌───────────────┐     ┌────────────────┐
│ 瀏覽器  │────▶│ LiveKit Server│────▶│ LiveKit Agent  │
└─────────┘     │    (SFU)      │     └────────────────┘
                └───────────────┘            │
                       │           ┌────────┼────────┐
                       │           ▼        ▼        ▼
                       │       ┌─────┐  ┌─────┐  ┌─────┐
                       │       │ STT │  │ LLM │  │ TTS │
                       │       └─────┘  └─────┘  └─────┘
                       ▼
              ┌─────────────────┐
              │ Redis (可選)    │
              └─────────────────┘
```

## 成本比較

### Pipecat + Daily

| 項目 | 成本 |
|------|------|
| Daily | $0.004/min/participant |
| 服務費 (STT+LLM+TTS) | 依用量 |
| 伺服器 | Bot hosting |

### LiveKit

| 選項 | 成本 |
|------|------|
| Cloud | $0.006/participant-min |
| Self-hosted | 伺服器 + 維運成本 |
| 服務費 | 依用量 |

## 學習資源

### Pipecat
- [官方文件](https://docs.pipecat.ai/)
- [範例庫](https://github.com/pipecat-ai/pipecat/tree/main/examples)
- [Discord 社群](https://discord.gg/pipecat)

### LiveKit
- [官方文件](https://docs.livekit.io/)
- [Agents 文件](https://docs.livekit.io/agents/)
- [範例庫](https://github.com/livekit/agents)
- [Slack 社群](https://livekit.io/slack)

## 遷移考量

### Pipecat → LiveKit
- 需重寫 Pipeline 為事件驅動
- Transport 層完全不同
- 服務 Plugin 大多相容

### LiveKit → Pipecat
- 簡化架構，可能失去部分功能
- 需要外部 Transport (Daily)
- 更快的開發迭代

## 參考連結

- [Pipecat GitHub](https://github.com/pipecat-ai/pipecat)
- [LiveKit GitHub](https://github.com/livekit/livekit)
- [Daily Developer Platform](https://www.daily.co/developers/)
- [LiveKit Cloud](https://cloud.livekit.io/)

## 更新日誌

| 日期 | 變更 |
|------|------|
| 2025-01 | 初始版本 |

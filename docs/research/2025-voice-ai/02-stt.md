# STT (語音轉文字) 服務研究

> 最後更新：2025-01

## 概述

STT 是 Voice AI pipeline 的第一環，將用戶語音轉換為文字供 LLM 處理。關鍵指標：延遲、準確度、支援語言。

## 服務比較

### Deepgram

**狀態**: ✅ 生產推薦

| 項目 | 說明 |
|------|------|
| 延遲 | ~100-200ms (streaming) |
| 準確度 | WER ~5-8% (英文) |
| 定價 | $0.0043/min (Pay-as-you-go) |

**特點**:
- Nova-2 模型表現優異
- 串流支援佳
- 多語言支援 (36+ 語言)
- Diarization (說話者分離)
- 自訂詞彙表

**API 範例**:
```python
from deepgram import DeepgramClient, LiveTranscriptionEvents

deepgram = DeepgramClient(api_key)
connection = deepgram.listen.live.v("1")

connection.on(LiveTranscriptionEvents.Transcript, handle_transcript)
await connection.start({"model": "nova-2", "language": "zh-TW"})
```

**適用場景**: 通用 Voice AI、客服、會議記錄

---

### Gladia

**狀態**: ✅ 生產就緒

| 項目 | 說明 |
|------|------|
| 延遲 | ~150-250ms (streaming) |
| 準確度 | 與 Deepgram 相當 |
| 定價 | $0.000193/sec (~$0.012/min) |

**特點**:
- 基於 Whisper 優化
- 強大的多語言支援 (99 語言)
- 自動語言偵測
- 代碼切換支援
- 自訂提示詞

**API 範例**:
```python
import gladia

client = gladia.Client(api_key)
result = await client.transcribe_live(
    audio_stream,
    language="zh",
    enable_code_switching=True
)
```

**適用場景**: 多語言環境、需要高語言覆蓋率

---

### Qwen3-ASR-Flash (Self-hosted)

**狀態**: 🔬 新興選項

| 項目 | 說明 |
|------|------|
| 延遲 | 取決於硬體 |
| 準確度 | 接近商用水準 |
| 成本 | 僅硬體成本 |

**特點**:
- 開源可自行部署
- 中文支援優異
- 可針對領域微調
- 資料完全私有

**部署需求**:
```yaml
# 推薦配置
GPU: NVIDIA A10G 或更高
VRAM: >= 16GB
框架: vLLM / TGI
```

**適用場景**: 資料敏感、大規模部署、需要客製化

---

## 功能比較表

| 功能 | Deepgram | Gladia | Qwen3-ASR |
|------|----------|--------|-----------|
| 串流轉錄 | ✅ | ✅ | ⚠️ 需實作 |
| 中文支援 | ✅ | ✅ | ✅✅ |
| 台語支援 | ⚠️ | ⚠️ | 🔬 |
| 說話者分離 | ✅ | ✅ | ⚠️ |
| 自訂詞彙 | ✅ | ✅ | ✅ (微調) |
| 自動語言偵測 | ✅ | ✅ | ✅ |
| 時間戳 | ✅ 字級 | ✅ 字級 | ✅ |
| 私有部署 | ❌ | ❌ | ✅ |

## 延遲優化策略

### 1. VAD (Voice Activity Detection)
```
[音訊] → [VAD] → [僅傳送有語音片段] → [STT]
```
減少傳輸和處理的靜音段落。

### 2. Endpointing 調整
- 縮短 silence timeout (預設通常 1-2 秒)
- 平衡：太短會截斷、太長增加延遲

### 3. 串流模式
- 使用 WebSocket 而非 REST
- 即時返回中間結果 (interim results)

## 選型建議

```
                    ┌─────────────────┐
                    │   主要考量？     │
                    └────────┬────────┘
                             │
        ┌────────────────────┼────────────────────┐
        ▼                    ▼                    ▼
   延遲/品質            多語言支援            成本/隱私
        │                    │                    │
        ▼                    ▼                    ▼
   ┌─────────┐         ┌─────────┐         ┌──────────┐
   │Deepgram │         │ Gladia  │         │Qwen3-ASR │
   └─────────┘         └─────────┘         └──────────┘
```

## 成本估算

假設：每日 10,000 分鐘通話

| 服務 | 月成本 (估算) |
|------|--------------|
| Deepgram | ~$1,290 |
| Gladia | ~$3,600 |
| Qwen3 (self) | ~$500-1,000 (GPU) |

## 整合注意事項

### Pipecat 整合
```python
from pipecat.services.deepgram import DeepgramSTTService

stt = DeepgramSTTService(
    api_key=os.getenv("DEEPGRAM_API_KEY"),
    model="nova-2",
    language="zh-TW"
)
```

### LiveKit 整合
```python
from livekit.agents.stt import StreamAdapter
from livekit.plugins import deepgram

stt = deepgram.STT(model="nova-2")
```

## 參考連結

- [Deepgram Docs](https://developers.deepgram.com/)
- [Gladia Docs](https://docs.gladia.io/)
- [Qwen3 ASR](https://github.com/QwenLM/Qwen-Audio)

## 更新日誌

| 日期 | 變更 |
|------|------|
| 2025-01 | 初始版本 |

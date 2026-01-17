# LLM (大型語言模型) 選擇研究

> 最後更新：2026-01-17

## 概述

LLM 是 Voice AI 的核心，負責理解用戶意圖並生成回應。Voice AI 場景對 LLM 有特殊要求：低延遲 (TTFT)、串流輸出、對話能力。

## 2026 年 LLM 格局

```
┌─────────────────────────────────────────────────────────────────────┐
│  2025-2026 主要發布                                                  │
├─────────────────────────────────────────────────────────────────────┤
│  2025-08  GPT-5 發布                                                │
│  2025-09  Claude 4.5 Haiku                                          │
│  2025-10  Claude 4.5 Sonnet                                         │
│  2025-11  Gemini 3 Pro, Claude 4.5 Opus                             │
│  2025-12  GPT-5.2, Gemini 3 Flash, DeepSeek V3.2                    │
│  2026-02  DeepSeek V4 (預計)                                        │
│  2026-H1  Meta Avocado/Mango (預計)                                 │
└─────────────────────────────────────────────────────────────────────┘
```

## TTFT 比較總覽

Voice AI 對 TTFT 極度敏感，以下是各模型的延遲比較：

```
TTFT 排名 (2026-01 測試，p50 延遲)

Groq + Llama 4       ████░░░░░░░░░░░░░░░░ ~50-100ms   ⚡ 最快
Gemini 3 Flash       █████░░░░░░░░░░░░░░░ ~70-150ms   ⚡ 極快
DeepSeek V3.2        ██████░░░░░░░░░░░░░░ ~100-200ms  💰 最便宜
GPT-5.2 Instant      ██████░░░░░░░░░░░░░░ ~100-200ms  🆕
Claude 4.5 Haiku     ███████░░░░░░░░░░░░░ ~150-250ms  🆕
Gemini 3 Pro         ████████░░░░░░░░░░░░ ~150-300ms
Claude 4.5 Sonnet    █████████░░░░░░░░░░░ ~200-350ms  🆕
GPT-5.2 Thinking     ██████████░░░░░░░░░░ ~250-400ms  🆕
GPT-5.2 Pro          ████████████████░░░░ ~400-800ms  🆕
Claude 4.5 Opus      ████████████████░░░░ ~350-600ms  🆕
```

### TTFT 詳細數據表

| 模型 | p50 TTFT | p95 TTFT | 適合 Voice AI | 備註 |
|------|----------|----------|---------------|------|
| Groq + Llama 4 | ~70ms | ~150ms | ✅✅ 最佳 | 開源首選 |
| Gemini 3 Flash | ~80ms | ~180ms | ✅✅ 極佳 | 性價比王 |
| DeepSeek V3.2 | ~120ms | ~250ms | ✅✅ 極佳 | 超低成本 |
| GPT-5.2 Instant | ~130ms | ~280ms | ✅✅ 極佳 | 簡單任務 |
| Claude 4.5 Haiku | ~180ms | ~350ms | ✅ 良好 | 快速版 |
| Gemini 3 Pro | ~200ms | ~400ms | ✅ 良好 | 頂級推理 |
| Claude 4.5 Sonnet | ~250ms | ~450ms | ⚠️ 可接受 | 均衡選擇 |
| GPT-5.2 Thinking | ~300ms | ~600ms | ⚠️ 可接受 | 含推理 |
| Claude 4.5 Opus | ~400ms | ~700ms | ⚠️ 勉強 | 最強品質 |
| GPT-5.2 Pro | ~500ms | ~1000ms | ❌ 不建議 | 複雜任務 |

---

## 模型比較

### GPT-5.2 (OpenAI) 🆕

**狀態**: ✅ 最新旗艦 - 2025-12-11 發布

| 變體 | TTFT | 定價 (input/output per 1M) | 用途 |
|------|------|---------------------------|------|
| **Instant** | ~100-200ms | $1.75 / $14 | 日常快速任務 |
| **Thinking** | ~250-400ms | $1.75 / $14 | 複雜推理 |
| **Pro** | ~400-800ms | $21 / $168 | 最高品質研究 |

**特點**:
- 400K context window (業界最大)
- 128K output tokens
- AIME 2025 100%、ARC-AGI-1 >90%、FrontierMath 40.3%
- Thinking 模式會產生隱藏推理 tokens（計入 output 費用）
- Cached inputs 90% 折扣 ($0.175/1M)
- Batch API 50% 折扣

**API 範例**:
```python
from openai import OpenAI

client = OpenAI()

# GPT-5.2 Instant - Voice AI 推薦
response = client.chat.completions.create(
    model="gpt-5.2",  # 預設為 Instant
    messages=[{"role": "user", "content": "你好"}],
    stream=True
)

# GPT-5.2 Thinking - 複雜問題
response = client.chat.completions.create(
    model="gpt-5.2-thinking",
    messages=[{"role": "user", "content": "解釋量子糾纏"}],
    stream=True
)
```

**適用場景**:
- Instant: Voice AI、日常對話
- Thinking: 複雜推理、程式碼
- Pro: 研究、高風險決策

---

### Claude 4.5 (Anthropic) 🆕

**狀態**: ✅ 生產推薦 - 2025-09~11 發布

| 變體 | TTFT | 定價 (input/output per 1M) | 用途 |
|------|------|---------------------------|------|
| **Haiku 4.5** | ~150-250ms | $1 / $5 | 快速任務 |
| **Sonnet 4.5** | ~200-350ms | $3 / $15 | 均衡選擇 |
| **Opus 4.5** | ~350-600ms | $5 / $25 | 最高品質 |

**特點**:
- 比 Claude 4 便宜 67%
- SWE-bench Verified 77.2% (Sonnet 領先)
- Terminal-Bench 2.0 首個突破 60%
- 200K context (Sonnet beta 支援 1M)
- Extended Thinking 支援
- Prompt caching 90% 折扣

**API 範例**:
```python
import anthropic

client = anthropic.Anthropic()

# Claude 4.5 Haiku - Voice AI 推薦
response = client.messages.create(
    model="claude-4.5-haiku",
    max_tokens=1024,
    messages=[{"role": "user", "content": "你好"}],
    stream=True
)

# Claude 4.5 Sonnet with Extended Thinking
response = client.messages.create(
    model="claude-4.5-sonnet",
    max_tokens=16000,
    thinking={"type": "enabled", "budget_tokens": 10000},
    messages=[{"role": "user", "content": "分析這段程式碼的效能問題"}]
)
```

**適用場景**:
- Haiku: Voice AI、簡單對話
- Sonnet: 程式碼生成、Agentic 應用
- Opus: 複雜推理、長文分析

---

### Gemini 3 (Google)

**狀態**: ✅ **Voice AI 首選** - 2025-11~12 發布

| 變體 | TTFT | 定價 (input/output per 1M) | 用途 |
|------|------|---------------------------|------|
| **Flash** | ~70-150ms | $0.50 / $3 | 🏆 Voice AI 首選 |
| **Pro** | ~150-300ms | $2-4 / $12-18 | 頂級推理 |

**Gemini 3 Flash 特點**:
- 超越 Gemini 2.5 Pro 品質，快 3 倍
- 218 tokens/sec throughput
- 1M context window，64K output tokens
- Dynamic Thinking (`thinking_level` 參數)
- SWE-bench 78%、WebDev Arena #1 (1487 Elo)
- 原生語音 I/O (Live API)

**Gemini 3 Pro 特點**:
- LMArena Elo 1501 (首個破 1500)
- GPQA Diamond 91.9% (超越人類專家)
- Deep Think: Humanity's Last Exam 41%
- ARC-AGI-2 45.1%

**API 範例**:
```python
import google.generativeai as genai

genai.configure(api_key=API_KEY)

# Gemini 3 Flash - Voice AI 首選
model = genai.GenerativeModel("gemini-3-flash")
response = model.generate_content(
    "你好",
    stream=True,
    generation_config={"thinking_level": "low"}  # 降低延遲
)

# Gemini 3 Pro with Deep Think
model = genai.GenerativeModel("gemini-3-pro")
response = model.generate_content(
    "證明哥德巴赫猜想",
    generation_config={"thinking_level": "high"}
)
```

**適用場景**:
- Flash: Voice AI、即時對話、程式碼
- Pro: 複雜推理、研究、數學

---

### DeepSeek V3.2 / V4 🆕

**狀態**: ✅ 成本王者

| 變體 | TTFT | 定價 (input/output per 1M) | 用途 |
|------|------|---------------------------|------|
| **V3.2-Exp** | ~100-200ms | $0.028 / $0.14 | 超低成本 |
| **V4** (2026-02) | TBD | 預計更低 | 程式碼專家 |

**特點**:
- **極致低成本**：GPT-5 的 1/60 價格
- 128K context window
- V4 預計超越 Claude/GPT 在程式碼生成
- 新架構：Manifold-Constrained Hyper-Connections
- Engram 條件式記憶系統

**API 範例**:
```python
from openai import OpenAI

# DeepSeek 使用 OpenAI 相容 API
client = OpenAI(
    api_key="your-deepseek-key",
    base_url="https://api.deepseek.com"
)

response = client.chat.completions.create(
    model="deepseek-chat",  # V3.2
    messages=[{"role": "user", "content": "你好"}],
    stream=True
)
```

**適用場景**: 大規模部署、成本敏感、程式碼生成

---

### Llama 4 + Groq

**狀態**: ✅ 開源速度王

| 項目 | 說明 |
|------|------|
| TTFT | ~50-100ms (Groq LPU) |
| 定價 | $0.05/1M input, $0.10/1M output |
| Context | 128K |

**特點**:
- Groq LPU 提供業界最低延遲
- 開源可自部署
- Meta 官方 API 合作夥伴
- Scout (小) 和 Maverick (大) 版本
- Behemoth 仍在訓練中

**即將推出 (2026 H1)**:
- **Avocado**: 新一代文字 LLM，強化程式碼和推理
- **Mango**: 多模態圖像/視訊生成

**API 範例**:
```python
from groq import Groq

client = Groq()
response = client.chat.completions.create(
    model="llama-4-maverick",
    messages=[{"role": "user", "content": "你好"}],
    stream=True
)
```

**適用場景**: 極致延遲、開源需求、自部署

---

## 功能比較表

| 功能 | GPT-5.2 | Claude 4.5 | Gemini 3 | DeepSeek V3.2 | Llama 4 |
|------|---------|------------|----------|---------------|---------|
| 串流輸出 | ✅ | ✅ | ✅ | ✅ | ✅ |
| Function Calling | ✅ | ✅ | ✅ | ✅ | ✅ |
| 中文能力 | ✅✅ | ✅✅ | ✅✅ | ✅✅✅ | ✅ |
| Context 長度 | 400K | 200K/1M | 1M | 128K | 128K |
| Output 長度 | 128K | 8K | 64K | 8K | 8K |
| 原生語音 I/O | ✅ | ❌ | ✅ | ❌ | ❌ |
| Extended Thinking | ✅ | ✅ | ✅ | ❌ | ❌ |
| 自部署 | ❌ | ❌ | ❌ | ⚠️ | ✅ |
| Grounding/Search | ✅ | ❌ | ✅ | ❌ | ❌ |

## 定價比較總表 (2026-01)

| 模型 | Input $/1M | Output $/1M | 性價比 | Voice AI 適合度 |
|------|------------|-------------|--------|-----------------|
| DeepSeek V3.2-Exp | $0.028 | $0.14 | ⭐⭐⭐⭐⭐ | ✅✅ |
| Llama 4 (Groq) | $0.05 | $0.10 | ⭐⭐⭐⭐⭐ | ✅✅ |
| **Gemini 3 Flash** | $0.50 | $3.00 | ⭐⭐⭐⭐⭐ | ✅✅ 🏆 |
| Claude 4.5 Haiku | $1.00 | $5.00 | ⭐⭐⭐⭐ | ✅✅ |
| GPT-5.2 Instant | $1.75 | $14.00 | ⭐⭐⭐ | ✅✅ |
| Gemini 3 Pro | $2-4 | $12-18 | ⭐⭐⭐ | ✅ |
| Claude 4.5 Sonnet | $3.00 | $15.00 | ⭐⭐⭐ | ✅ |
| Claude 4.5 Opus | $5.00 | $25.00 | ⭐⭐ | ⚠️ |
| GPT-5.2 Pro | $21.00 | $168.00 | ⭐ | ❌ |

## 成本估算

假設：每日 10,000 次對話，每次平均 500 input + 200 output tokens

| 模型 | 日成本 | 月成本 | 備註 |
|------|--------|--------|------|
| DeepSeek V3.2 | ~$0.42 | ~$13 | 💰 最便宜 |
| Llama 4 (Groq) | ~$0.45 | ~$14 | ⚡ 最快 |
| Gemini 3 Flash | ~$8.50 | ~$255 | 🏆 最佳平衡 |
| Claude 4.5 Haiku | ~$15 | ~$450 | 快速 + 品質 |
| GPT-5.2 Instant | ~$37 | ~$1,110 | OpenAI 生態 |
| Claude 4.5 Sonnet | ~$45 | ~$1,350 | Agentic 首選 |
| Gemini 3 Pro | ~$50 | ~$1,500 | 頂級推理 |
| Claude 4.5 Opus | ~$75 | ~$2,250 | 最高品質 |
| GPT-5.2 Pro | ~$441 | ~$13,230 | 研究用途 |

> ⚠️ GPT-5.2 Thinking 模式的隱藏推理 tokens 會額外增加成本

## Voice AI 專屬考量

### 1. 延遲預算分配

理想的 Voice AI 總延遲 < 1 秒：

```
用戶說完 → STT (~100ms) → LLM TTFT → TTS TTFB (~100ms) → 播放
                              ↑
                     目標 < 300ms
```

**推薦組合**:
| 優先級 | STT | LLM | TTS | 預估總延遲 |
|--------|-----|-----|-----|-----------|
| 延遲優先 | Deepgram | Gemini 3 Flash | Cartesia | ~400ms |
| 成本優先 | Deepgram | DeepSeek V3.2 | Deepgram | ~500ms |
| 品質優先 | Gladia | Claude 4.5 Haiku | ElevenLabs | ~700ms |

### 2. 串流輸出品質

| 模型 | Throughput | 穩定性 | 備註 |
|------|------------|--------|------|
| Gemini 3 Flash | 218 t/s | ⭐⭐⭐⭐⭐ | 專為即時設計 |
| Groq + Llama 4 | 300+ t/s | ⭐⭐⭐⭐ | 偶有 burst |
| DeepSeek V3.2 | 150 t/s | ⭐⭐⭐⭐ | 穩定 |
| GPT-5.2 Instant | 125 t/s | ⭐⭐⭐⭐⭐ | 非常穩定 |
| Claude 4.5 Haiku | 100 t/s | ⭐⭐⭐⭐ | 偶有停頓 |

### 3. Thinking/Reasoning 模式對比

| 功能 | GPT-5.2 | Claude 4.5 | Gemini 3 |
|------|---------|------------|----------|
| 名稱 | Thinking mode | Extended Thinking | Dynamic Thinking |
| 控制方式 | 選擇模型變體 | `thinking.budget_tokens` | `thinking_level` |
| 計費 | 推理 tokens 計入 output | 推理 tokens 計入 output | 包含在定價內 |
| Voice AI 建議 | 用 Instant | 關閉或低 budget | `thinking_level: low` |

### 4. System Prompt 優化

```
你是一個語音助理。請注意：
1. 回答要簡潔（1-3句）
2. 避免使用 markdown 格式
3. 不要列點，用自然語言
4. 適當使用語氣詞讓對話更自然
5. 如果需要確認，直接詢問
```

## 場景選型建議

### 場景 1：即時對話 Voice AI（延遲優先）

```
推薦順序：
1. Gemini 3 Flash   ← 🏆 最佳平衡（快 + 品質 + 成本）
2. Groq + Llama 4   ← 極致延遲
3. DeepSeek V3.2    ← 極致成本
4. GPT-5.2 Instant  ← OpenAI 生態
```

### 場景 2：企業級客服（品質 + 安全）

```
推薦順序：
1. Claude 4.5 Sonnet ← Agentic 能力 + 安全性
2. GPT-5.2 Thinking  ← 複雜推理
3. Gemini 3 Pro      ← Google 生態整合
```

### 場景 3：大規模部署（成本優先）

```
推薦順序：
1. DeepSeek V3.2    ← 💰 極致低成本
2. Llama 4 (Groq)   ← 開源 + 低成本
3. Gemini 3 Flash   ← 品質 + 合理成本
```

### 場景 4：程式碼生成

```
推薦順序：
1. Claude 4.5 Sonnet ← SWE-bench #1
2. Gemini 3 Flash    ← WebDev Arena #1
3. DeepSeek V4       ← (2026-02 後) 程式碼專家
```

### 場景 5：複雜推理 / 研究

```
推薦順序：
1. Gemini 3 Pro      ← GPQA 91.9%, LMArena #1
2. GPT-5.2 Pro       ← FrontierMath 40.3%
3. Claude 4.5 Opus   ← 長文理解
```

### 場景 6：中文應用

```
推薦順序：
1. DeepSeek V3.2    ← 中國團隊，中文最強
2. Gemini 3 Flash   ← 多語言優秀
3. Claude 4.5       ← 中文理解佳
```

### 選型決策樹

```
                           ┌─────────────────────┐
                           │    主要考量是？      │
                           └──────────┬──────────┘
                                      │
    ┌──────────┬──────────┬───────────┼───────────┬──────────┬──────────┐
    ▼          ▼          ▼           ▼           ▼          ▼          ▼
 延遲優先   品質優先   成本優先    程式碼      複雜推理    中文      安全性
    │          │          │           │           │          │          │
    ▼          ▼          ▼           ▼           ▼          ▼          ▼
┌────────┐┌────────┐┌─────────┐┌─────────┐┌────────┐┌────────┐┌────────┐
│Gemini 3││Gemini 3││DeepSeek ││Claude   ││Gemini 3││DeepSeek││Claude  │
│Flash 🏆││Pro     ││V3.2 💰  ││4.5      ││Pro     ││V3.2    ││4.5     │
└────────┘└────────┘└─────────┘│Sonnet   │└────────┘└────────┘│Sonnet  │
                               └─────────┘                    └────────┘
```

## 整合範例

### Pipecat
```python
from pipecat.services.google import GoogleLLMService
from pipecat.services.openai import OpenAILLMService
from pipecat.services.anthropic import AnthropicLLMService

# Gemini 3 Flash (推薦)
llm = GoogleLLMService(
    api_key=os.getenv("GOOGLE_API_KEY"),
    model="gemini-3-flash"
)

# GPT-5.2 Instant
llm = OpenAILLMService(
    api_key=os.getenv("OPENAI_API_KEY"),
    model="gpt-5.2"
)

# Claude 4.5 Haiku
llm = AnthropicLLMService(
    api_key=os.getenv("ANTHROPIC_API_KEY"),
    model="claude-4.5-haiku"
)
```

### LiveKit
```python
from livekit.plugins import google, openai, anthropic

# Gemini 3 Flash (推薦)
llm = google.LLM(model="gemini-3-flash")

# GPT-5.2 Instant
llm = openai.LLM(model="gpt-5.2")

# Claude 4.5 Haiku
llm = anthropic.LLM(model="claude-4.5-haiku")
```

## Benchmark 比較 (2026-01)

| Benchmark | GPT-5.2 Pro | Gemini 3 Pro | Claude 4.5 Opus | 說明 |
|-----------|-------------|--------------|-----------------|------|
| LMArena Elo | ~1480 | **1501** | ~1450 | 整體排名 |
| GPQA Diamond | ~88% | **91.9%** | ~85% | 專家知識 |
| AIME 2025 | **100%** | ~95% | ~90% | 數學 |
| FrontierMath | **40.3%** | ~35% | ~30% | 前沿數學 |
| ARC-AGI-1 | **>90%** | ~88% | ~82% | AGI 測試 |
| ARC-AGI-2 | ~40% | **45.1%** | ~35% | AGI 測試 v2 |
| SWE-bench | ~75% | 78% | **77.2%** | 程式碼 |
| Terminal-Bench | ~55% | ~58% | **>60%** | CLI 程式碼 |
| HLE | ~38% | **41%** | ~35% | 人類最後考試 |

## 參考連結

- [GPT-5.2 官方介紹](https://openai.com/index/introducing-gpt-5-2/)
- [GPT-5.2 API 文件](https://platform.openai.com/docs/models/gpt-5.2)
- [Claude 4.5 Opus 官方介紹](https://www.anthropic.com/news/claude-opus-4-5)
- [Claude 定價](https://platform.claude.com/docs/en/about-claude/pricing)
- [Gemini 3 Flash 官方介紹](https://blog.google/products/gemini/gemini-3-flash/)
- [Gemini 3 Pro 官方介紹](https://blog.google/products/gemini/gemini-3/)
- [DeepSeek API 定價](https://api-docs.deepseek.com/quick_start/pricing)
- [Groq 支援模型](https://console.groq.com/docs/models)
- [LLM Leaderboard 2026](https://llm-stats.com/leaderboards/llm-leaderboard)
- [LLM Latency Benchmark](https://research.aimultiple.com/llm-latency-benchmark/)

## 更新日誌

| 日期 | 變更 |
|------|------|
| 2026-01-17 | 🆕 全面更新：GPT-5.2, Claude 4.5, DeepSeek V3.2 |
| 2026-01-17 | 更新定價比較、Benchmark、場景選型 |
| 2026-01 | 新增 Gemini 3 Flash/Pro |
| 2025-01 | 初始版本 |

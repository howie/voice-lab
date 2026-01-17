# LLM (大型語言模型) 選擇研究

> 最後更新：2026-01

## 概述

LLM 是 Voice AI 的核心，負責理解用戶意圖並生成回應。Voice AI 場景對 LLM 有特殊要求：低延遲 (TTFT)、串流輸出、對話能力。

## TTFT 比較總覽

Voice AI 對 TTFT 極度敏感，以下是各模型的延遲比較：

```
TTFT 排名 (2026-01 測試，p50 延遲)

Groq + Llama 4       ████░░░░░░░░░░░░░░░░ ~50-100ms   ⚡ 最快
Gemini 3 Flash       █████░░░░░░░░░░░░░░░ ~70-150ms   ⚡ 極快 🆕
Gemini 2.0 Flash     ██████░░░░░░░░░░░░░░ ~80-150ms   ⚡ 極快
GPT-4o-mini          ████████░░░░░░░░░░░░ ~100-200ms
Gemini 1.5 Flash     ████████░░░░░░░░░░░░ ~100-200ms
Gemini 3 Pro         ██████████░░░░░░░░░░ ~150-300ms  🆕
Claude 3.5 Sonnet    ████████████░░░░░░░░ ~200-300ms
GPT-4o               ████████████████░░░░ ~200-400ms
Gemini 2.0 Pro       ████████████████░░░░ ~200-400ms
```

### TTFT 詳細數據表

| 模型 | p50 TTFT | p95 TTFT | 適合 Voice AI |
|------|----------|----------|---------------|
| Groq + Llama 4 | ~70ms | ~150ms | ✅✅ 最佳 |
| Gemini 3 Flash | ~80ms | ~180ms | ✅✅ 極佳 🆕 |
| Gemini 2.0 Flash | ~100ms | ~200ms | ✅✅ 極佳 |
| GPT-4o-mini | ~150ms | ~300ms | ✅ 良好 |
| Gemini 1.5 Flash | ~150ms | ~350ms | ✅ 良好 |
| Gemini 3 Pro | ~200ms | ~400ms | ✅ 良好 🆕 |
| Claude 3.5 Sonnet | ~250ms | ~500ms | ⚠️ 可接受 |
| GPT-4o | ~300ms | ~600ms | ⚠️ 可接受 |
| Gemini 2.0 Pro | ~300ms | ~600ms | ⚠️ 可接受 |

---

## 模型比較

### Gemini 3 Flash (Google) 🆕

**狀態**: ✅ **2026 首選** - 速度、品質、成本最佳平衡

| 項目 | 說明 |
|------|------|
| 發布日期 | 2025-12-17 |
| TTFT | ~70-150ms (sub-500ms 保證) |
| 品質 | 頂級 (超越 Gemini 2.5 Pro) |
| 定價 | $0.50/1M input, $3.00/1M output |
| Throughput | 218 tokens/sec |

**特點**:
- 超越 2.5 Pro 的品質，同時快 3 倍
- 1M context window，64K output tokens
- Dynamic Thinking 支援 (可調整推理深度)
- 原生多模態 (音訊、視訊、圖像)
- SWE-bench 78%，優於 3 Pro
- WebDev Arena 1487 Elo

**API 範例**:
```python
import google.generativeai as genai

genai.configure(api_key=API_KEY)
model = genai.GenerativeModel("gemini-3-flash")

response = model.generate_content(
    "你好",
    stream=True,
    generation_config={"thinking_level": "low"}  # 降低推理深度以減少延遲
)
for chunk in response:
    print(chunk.text, end="")
```

**適用場景**: Voice AI 首選、即時對話、Agentic 應用、程式碼生成

---

### Gemini 3 Pro (Google) 🆕

**狀態**: ✅ 生產推薦 - 最強推理能力

| 項目 | 說明 |
|------|------|
| 發布日期 | 2025-11-18 |
| TTFT | ~150-300ms |
| 品質 | 頂級 |
| 定價 | $2-4/1M input, $12-18/1M output (依 context) |

**特點**:
- Gemini 系列最強推理能力
- Deep Think 模式：GPQA Diamond 93.8%
- ARC-AGI-2 達 45.1% (突破性)
- 最佳 vibe coding 和 agentic coding 模型
- 支援 Google AI Studio、Vertex AI、Gemini CLI

**適用場景**: 複雜推理、高品質程式碼、研究任務

---

### Gemini 2.0 Flash (Google)

**狀態**: ✅ 穩定版本 - 仍然優秀

| 項目 | 說明 |
|------|------|
| TTFT | ~80-150ms |
| 品質 | 優秀 |
| 定價 | $0.10/1M input, $0.40/1M output |

**特點**:
- 極低延遲，專為即時互動設計
- 原生多模態 (支援音訊輸入/輸出)
- 1M context window
- 內建 Google Search grounding
- 價格極具競爭力

**適用場景**: 成本敏感的 Voice AI、穩定性需求

---

### GPT-4o (OpenAI)

**狀態**: ✅ 生產推薦 - 可靠性首選

| 項目 | 說明 |
|------|------|
| TTFT | ~200-400ms |
| 品質 | 頂級 |
| 定價 | $2.50/1M input, $10/1M output |

**特點**:
- 多模態 (文字、圖像、音訊)
- 原生語音模式 (Voice Mode / Realtime API)
- 極強的指令遵循能力
- 穩定的 API 可用性

**API 範例**:
```python
from openai import OpenAI

client = OpenAI()
response = client.chat.completions.create(
    model="gpt-4o",
    messages=[{"role": "user", "content": "你好"}],
    stream=True
)
for chunk in response:
    print(chunk.choices[0].delta.content, end="")
```

**適用場景**: 高品質要求、複雜對話、企業級應用

---

### GPT-4o-mini (OpenAI)

**狀態**: ✅ 成本效益之選

| 項目 | 說明 |
|------|------|
| TTFT | ~100-200ms |
| 品質 | 優秀 |
| 定價 | $0.15/1M input, $0.60/1M output |

**特點**:
- GPT-4o 約 1/15 成本
- 更快的回應速度
- 適合大多數對話場景
- 128K context window

**適用場景**: 成本敏感、一般對話、開發測試

---

### Llama 4 + Groq

**狀態**: ✅ 速度首選

| 項目 | 說明 |
|------|------|
| TTFT | ~50-100ms |
| 品質 | 接近 GPT-4 |
| 定價 | $0.05/1M input, $0.10/1M output (Groq) |

**特點**:
- 極低延遲 (Groq LPU)
- 開源模型可自部署
- 高 throughput
- 持續改進中

**API 範例**:
```python
from groq import Groq

client = Groq()
response = client.chat.completions.create(
    model="llama-4-scout-17b-16e-instruct",
    messages=[{"role": "user", "content": "你好"}],
    stream=True
)
```

**適用場景**: 延遲敏感、大規模部署、預算有限

---

### Claude 3.5 Sonnet (Anthropic)

**狀態**: ✅ 生產就緒

| 項目 | 說明 |
|------|------|
| TTFT | ~200-300ms |
| 品質 | 頂級 |
| 定價 | $3/1M input, $15/1M output |

**特點**:
- 優秀的推理能力
- 長 context (200K)
- 更好的安全性設計

**適用場景**: 複雜推理、長對話、安全敏感

---

## 功能比較表

| 功能 | Gemini 3 Flash | Gemini 3 Pro | GPT-4o | GPT-4o-mini | Gemini 2.0 Flash | Llama 4+Groq | Claude 3.5 |
|------|----------------|--------------|--------|-------------|------------------|--------------|------------|
| 串流輸出 | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| Function Calling | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| 中文能力 | ✅✅ | ✅✅ | ✅✅ | ✅ | ✅✅ | ✅ | ✅✅ |
| Context 長度 | 1M | 1M | 128K | 128K | 1M | 128K | 200K |
| Output 長度 | 64K | 64K | 16K | 16K | 8K | 8K | 8K |
| 原生語音 I/O | ✅ | ✅ | ✅ | ❌ | ✅ | ❌ | ❌ |
| Dynamic Thinking | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ |
| 自部署 | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ | ❌ |
| Grounding/Search | ✅ | ✅ | ❌ | ❌ | ✅ | ❌ | ❌ |

## Voice AI 專屬考量

### 1. TTFT (Time To First Token)

Voice AI 對 TTFT 極度敏感，因為用戶期待即時回應。

```
用戶說完 → STT → [LLM TTFT] → TTS 開始
                     ↑
              這裡要快！
```

**Voice AI 推薦排名** (2026-01):
| 排名 | 模型 | TTFT | 推薦指數 |
|------|------|------|----------|
| 1 | Groq + Llama 4 | ~50-100ms | ⭐⭐⭐⭐⭐ |
| 2 | **Gemini 3 Flash** | ~70-150ms | ⭐⭐⭐⭐⭐ 🏆 |
| 3 | Gemini 2.0 Flash | ~80-150ms | ⭐⭐⭐⭐⭐ |
| 4 | GPT-4o-mini | ~100-200ms | ⭐⭐⭐⭐ |
| 5 | Gemini 1.5 Flash | ~100-200ms | ⭐⭐⭐⭐ |
| 6 | Gemini 3 Pro | ~150-300ms | ⭐⭐⭐⭐ |
| 7 | Claude 3.5 Sonnet | ~200-300ms | ⭐⭐⭐ |
| 8 | GPT-4o | ~200-400ms | ⭐⭐⭐ |

### 2. 串流輸出品質

- **Gemini 3 Flash**: 極快且穩定，218 tokens/sec
- **GPT-4o**: 穩定的 token 間隔
- **Gemini 2.0 Flash**: 極快且穩定
- **Groq**: 極快但可能有 burst
- **Claude**: 穩定但偶有停頓

### 3. Dynamic Thinking (Gemini 3 獨有)

Gemini 3 支援調整推理深度，對 Voice AI 很有用：

```python
# 快速回應模式 - Voice AI 推薦
generation_config = {"thinking_level": "low"}

# 深度思考模式 - 複雜問題
generation_config = {"thinking_level": "high"}
```

### 4. 原生語音模式比較

| 模型 | 語音輸入 | 語音輸出 | 即時對話 |
|------|----------|----------|----------|
| Gemini 3 Flash | ✅ | ✅ | ✅ Live API |
| Gemini 3 Pro | ✅ | ✅ | ✅ Live API |
| GPT-4o | ✅ | ✅ | ✅ Realtime API |
| Gemini 2.0 Flash | ✅ | ✅ | ✅ Live API |
| 其他 | ❌ | ❌ | ❌ 需 STT+TTS |

### 5. System Prompt 優化

Voice AI 的 system prompt 應包含：

```
你是一個語音助理。請注意：
1. 回答要簡潔（1-3句）
2. 避免使用 markdown 格式
3. 不要列點，用自然語言
4. 適當使用語氣詞讓對話更自然
5. 如果需要確認，直接詢問
```

## 延遲優化策略

### 1. 使用更快的模型
對於簡單對話，優先選擇：
- Groq + Llama 4 (最快)
- **Gemini 3 Flash** (快 + 品質最佳平衡) 🏆
- Gemini 2.0 Flash (便宜 + 快)

### 2. Gemini 3 Thinking Level 調整
```python
# Voice AI 場景：降低 thinking level
model.generate_content(
    prompt,
    generation_config={"thinking_level": "low"}
)
```

### 3. 縮短 Prompt
```python
# 不好
system = "你是一個非常有幫助的助理，會盡可能詳細地回答問題..."

# 好
system = "語音助理。簡潔回答，1-3句。"
```

### 4. 智慧路由
```python
def select_model(user_input):
    complexity = analyze_complexity(user_input)

    if complexity == "simple":
        return "gemini-3-flash"   # 快速回應 🆕
    elif complexity == "medium":
        return "gemini-2.0-flash" # 成本效益
    else:
        return "gemini-3-pro"     # 複雜任務 🆕
```

## 成本估算

假設：每日 10,000 次對話，每次平均 500 input + 200 output tokens

| 模型 | 日成本 | 月成本 | 性價比 |
|------|--------|--------|--------|
| Llama 4 (Groq) | ~$0.45 | ~$14 | ⭐⭐⭐⭐⭐ |
| Gemini 2.0 Flash | ~$1.30 | ~$39 | ⭐⭐⭐⭐⭐ |
| **Gemini 3 Flash** | ~$8.50 | ~$255 | ⭐⭐⭐⭐ 🆕 |
| GPT-4o-mini | ~$1.95 | ~$59 | ⭐⭐⭐⭐ |
| GPT-4o | ~$32.50 | ~$975 | ⭐⭐ |
| Gemini 3 Pro | ~$46 | ~$1,380 | ⭐⭐ 🆕 |
| Claude 3.5 | ~$45 | ~$1,350 | ⭐⭐ |

> 注意：Gemini 3 Flash 雖然比 2.0 貴，但品質大幅提升（超越 2.5 Pro），性價比仍然很高。

## 場景選型建議

### 場景 1：即時對話 Voice AI（延遲優先）

```
推薦順序：
1. Gemini 3 Flash   ← 🏆 2026 首選（快速 + 頂級品質）
2. Groq + Llama 4   ← 極致延遲 + 最低成本
3. Gemini 2.0 Flash ← 成本敏感時的選擇
```

### 場景 2：企業級客服（品質優先）

```
推薦順序：
1. Gemini 3 Pro     ← 🆕 最強推理
2. GPT-4o           ← 最可靠、生態成熟
3. Claude 3.5       ← 安全性佳
```

### 場景 3：大規模部署（成本優先）

```
推薦順序：
1. Groq + Llama 4   ← 最低成本
2. Gemini 2.0 Flash ← 極低成本 + 良好品質
3. GPT-4o-mini      ← 穩定可靠
```

### 場景 4：多模態應用（原生語音）

```
推薦順序：
1. Gemini 3 Flash   ← 🆕 原生語音 + 低延遲 + 頂級品質
2. GPT-4o Realtime  ← 成熟的原生語音
3. Gemini 2.0 Flash ← 成本效益
```

### 場景 5：複雜推理 / Agentic 應用

```
推薦順序：
1. Gemini 3 Pro     ← 🆕 ARC-AGI-2 45.1%，Deep Think
2. Gemini 3 Flash   ← 🆕 SWE-bench 78%
3. GPT-4o           ← 穩定可靠
```

### 場景 6：程式碼生成

```
推薦順序：
1. Gemini 3 Flash   ← 🆕 WebDev Arena #1 (1487 Elo)
2. Gemini 3 Pro     ← 🆕 最佳 vibe coding
3. Claude 3.5       ← 程式碼品質佳
```

### 選型決策樹

```
                        ┌─────────────────────┐
                        │    主要考量是？      │
                        └──────────┬──────────┘
                                   │
       ┌───────────┬───────────┬───┴───┬───────────┬───────────┐
       ▼           ▼           ▼       ▼           ▼           ▼
    延遲優先    品質優先    成本優先  多模態     複雜推理    程式碼
       │           │           │       │           │           │
       ▼           ▼           ▼       ▼           ▼           ▼
  ┌─────────┐ ┌────────┐ ┌────────┐ ┌───────┐ ┌─────────┐ ┌────────┐
  │Gemini 3 │ │Gemini 3│ │Llama 4 │ │Gemini │ │Gemini 3 │ │Gemini 3│
  │Flash 🏆 │ │Pro     │ │+ Groq  │ │3 Flash│ │Pro      │ │Flash   │
  └─────────┘ └────────┘ └────────┘ └───────┘ └─────────┘ └────────┘
```

## 整合範例

### Pipecat
```python
from pipecat.services.google import GoogleLLMService

# Gemini 3 Flash (推薦)
llm = GoogleLLMService(
    api_key=os.getenv("GOOGLE_API_KEY"),
    model="gemini-3-flash"
)
```

### LiveKit
```python
from livekit.plugins import google

# Gemini 3 Flash (推薦)
llm = google.LLM(model="gemini-3-flash")
```

### 直接使用 Gemini 3 API
```python
import google.generativeai as genai

genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

# Gemini 3 Flash with thinking level control
model = genai.GenerativeModel(
    "gemini-3-flash",
    system_instruction="語音助理。簡潔回答，1-3句。"
)

chat = model.start_chat()
response = chat.send_message(
    "你好",
    stream=True,
    generation_config={"thinking_level": "low"}  # Voice AI 優化
)

for chunk in response:
    print(chunk.text, end="", flush=True)
```

## 參考連結

- [Gemini 3 Flash 官方介紹](https://blog.google/products/gemini/gemini-3-flash/)
- [Gemini 3 Pro 官方介紹](https://blog.google/products/gemini/gemini-3/)
- [Gemini API Pricing](https://ai.google.dev/gemini-api/docs/pricing)
- [Google AI Studio](https://aistudio.google.com/)
- [OpenAI API](https://platform.openai.com/docs)
- [Groq API](https://console.groq.com/docs)
- [Anthropic API](https://docs.anthropic.com/)

## 更新日誌

| 日期 | 變更 |
|------|------|
| 2026-01 | 🆕 新增 Gemini 3 Flash、Gemini 3 Pro |
| 2026-01 | 更新 TTFT 比較表、場景選型建議 |
| 2026-01 | 新增 Dynamic Thinking 說明 |
| 2025-01 | 新增 Google Gemini 2.0 系列 |
| 2025-01 | 初始版本 |

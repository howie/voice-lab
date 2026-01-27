# 音訊延遲優化計畫

## 背景

前端語音互動模組存在多個延遲來源，影響用戶體驗。本計畫整合所有優化項目，按優先順序執行。

### 瀏覽器警告
```
[Deprecation] The ScriptProcessorNode is deprecated. Use AudioWorkletNode instead.
```

---

## 延遲分析總覽

| 延遲來源 | 現況 | 影響 | 優先級 |
|----------|------|------|--------|
| **VAD 靜音等待** | 1200ms | 用戶講完後「發呆」1.2 秒 | 🔴 P0 |
| **採樣延遲** | 256ms (4096 buffer) | 硬性物理延遲 | 🟠 P1 |
| **傳輸開銷** | Base64 +33% | 網路與 CPU 開銷 | 🟡 P2 |
| **主線程阻塞** | ScriptProcessorNode | UI 卡頓、音訊斷續 | 🟠 P1 |

**總延遲估算**: ~1.5 秒 (VAD 1.2s + 採樣 0.256s + 處理)

---

## 問題詳細分析

### 1. 互動邏輯延遲 - VAD 設定 (P0，最快見效)

**位置**: `frontend/src/components/interaction/InteractionPanel.tsx`

```typescript
const SILENCE_DURATION_MS = 1200 // Auto send end_turn after 1.2s of silence
```

**問題**:
- 用戶講完話後，系統等待 1.2 秒確認不再說話才開始處理
- 這是**體感延遲最大的來源**
- 用戶會覺得系統「發呆」了

**建議**:
- 調整為 500ms - 800ms
- 配合 Barge-in (打斷) 功能，誤判時用戶可直接打斷 AI

---

### 2. 採樣延遲 - Buffer Size (P1)

**位置**: `frontend/src/hooks/useMicrophone.ts:155`

```typescript
const bufferSize = 4096
const processor = audioContext.createScriptProcessor(bufferSize, channelCount, channelCount)
```

**問題**:
- 4096 samples @ 16kHz = **256ms** 硬性延遲
- 必須填滿 buffer 才會觸發 `onaudioprocess`

**影響計算**:
| Buffer Size | 延遲 (@ 16kHz) |
|-------------|----------------|
| 4096 | 256ms |
| 2048 | 128ms |
| 1024 | 64ms |
| 128 (AudioWorklet) | 8ms |

---

### 3. 主線程阻塞 - ScriptProcessorNode (P1)

**問題**:
| 項目 | ScriptProcessorNode | AudioWorkletNode |
|------|---------------------|------------------|
| 執行線程 | 主線程 | 獨立音訊渲染線程 |
| Buffer 大小 | 固定 (256-16384) | 固定 128 frames |
| 延遲 | 高 | 低 (~8ms @ 16kHz) |
| UI 影響 | 阻塞 | 無影響 |
| 狀態 | **已棄用** | 現代標準 |

---

### 4. 傳輸延遲 - Base64 編碼 (P2)

**位置**: `frontend/src/components/interaction/InteractionPanel.tsx`

```typescript
const base64Audio = btoa(
  String.fromCharCode(...new Uint8Array(pcm16Buffer))
)
sendMessage('audio_chunk', {
  audio: base64Audio,
  format: 'pcm16',
  sample_rate: actualSampleRate,
})
```

**問題**:
- Base64 編碼使數據量增加 **~33%**
- 前端編碼 + 後端解碼都需要 CPU 時間
- 在持續串流中會累積

**建議**:
- 改用 Binary (ArrayBuffer) 直接傳輸
- 前端: `ws.send(pcm16Buffer)`
- 後端: 區分 Text Message (控制) 與 Binary Message (音訊)

## 技術方案

### 架構變更

**重要**: 必須保留 `Source -> AnalyserNode` 的連接，否則 UI 音量指示器會失效。

```
┌──────────────────────────────────────────────────────────────────────┐
│                           Main Thread                                 │
│  ┌────────────────────────────────────────────────────────────┐      │
│  │                    useMicrophone Hook                       │      │
│  │  - 建立 AudioContext                                        │      │
│  │  - 載入 AudioWorkletProcessor                               │      │
│  │  - 建立 AudioWorkletNode                                    │      │
│  │  - 接收 MessagePort 訊息                                    │      │
│  │  - 透過 AnalyserNode 計算音量 (requestAnimationFrame)       │      │
│  └────────────────────────────────────────────────────────────┘      │
│                              │                                        │
│                       MessagePort                                     │
│                              │                                        │
└──────────────────────────────┼───────────────────────────────────────┘
                               │
┌──────────────────────────────┼───────────────────────────────────────┐
│                              ▼           Audio Worklet Thread         │
│                                                                       │
│     ┌─────────────┐      ┌──────────────────┐                        │
│     │ MediaStream │      │  AnalyserNode    │──► (音量監測,主線程)    │
│     │   Source    │──┬──►│  (fftSize=256)   │                        │
│     └─────────────┘  │   └──────────────────┘                        │
│                      │                                                │
│                      │   ┌──────────────────────────────────────┐    │
│                      └──►│      AudioWorkletProcessor           │    │
│                          │  - process() 每 128 frames 執行一次  │    │
│                          │  - 累積到 4096 buffer 後傳送         │    │
│                          │  - 透過 MessagePort 傳送音訊資料     │    │
│                          └──────────────────────────────────────┘    │
│                                          │                            │
│                                          ▼                            │
│                                   ┌─────────────┐                    │
│                                   │ Destination │                    │
│                                   └─────────────┘                    │
└──────────────────────────────────────────────────────────────────────┘
```

### 音訊節點連接 (重要)

```
Source ──┬──► AnalyserNode (音量監測，維持在主線程)
         │
         └──► AudioWorkletNode ──► Destination (音訊處理)
```

### 檔案變更清單

| 檔案 | 動作 | 說明 |
|------|------|------|
| `frontend/public/worklets/audio-processor.js` | 新增 | AudioWorkletProcessor 實作 |
| `frontend/src/hooks/useMicrophone.ts` | 修改 | 改用 AudioWorkletNode |
| `frontend/src/lib/audioProcessor.ts` | 新增 | 音訊處理器抽象層 (Worklet/ScriptProcessor) |
| `frontend/src/hooks/__tests__/useMicrophone.test.ts` | 修改 | 更新測試 |

## 實作細節

### 1. AudioWorkletProcessor (`audio-processor.js`)

**⚠️ 重要**: Buffer Size 決定實際採樣延遲，必須根據需求選擇：

| Buffer Size | 延遲 @ 16kHz | 適用場景 |
|-------------|--------------|----------|
| 128 | 8ms | 極低延遲 (封包頻繁，需評估網路開銷) |
| 1024 | 64ms | 即時對話 (推薦) |
| 2048 | 128ms | 平衡延遲與穩定性 |
| 4096 | 256ms | 與舊版相同 (無延遲改善) |

```javascript
// frontend/public/worklets/audio-processor.js
class AudioProcessor extends AudioWorkletProcessor {
  constructor() {
    super()
    // ⚠️ 關鍵設定: Buffer Size 決定採樣延遲
    // 1024 samples @ 16kHz = 64ms 延遲 (推薦值)
    // 若需更低延遲可改為 512 (32ms)，但封包會更頻繁
    this.bufferSize = 1024
    this.buffer = new Float32Array(this.bufferSize)
    this.bufferIndex = 0
  }

  process(inputs, outputs, parameters) {
    const input = inputs[0]
    if (!input || !input[0]) return true

    const channelData = input[0]

    // 累積到 buffer (每次 process 只有 128 frames = 8ms)
    for (let i = 0; i < channelData.length; i++) {
      this.buffer[this.bufferIndex++] = channelData[i]

      // Buffer 滿了，傳送到主線程
      if (this.bufferIndex >= this.bufferSize) {
        const audioData = this.buffer.slice()

        // 使用 Transferable Objects 避免記憶體拷貝 (Zero-copy)
        this.port.postMessage({
          type: 'audio',
          audioData: audioData,
          sampleRate: sampleRate
        }, [audioData.buffer])  // Transfer ownership

        this.bufferIndex = 0
      }
    }

    return true // 保持 processor 活躍
  }
}

registerProcessor('audio-processor', AudioProcessor)
```

**Transferable Objects 說明**:
- `postMessage(data, [audioData.buffer])` 將 ArrayBuffer 的所有權轉移給主線程
- 避免記憶體拷貝，減少 CPU 開銷
- 傳輸後 Worklet 端的 buffer 變為 detached (不可用)，所以需要 `slice()` 複製

### 2. 音訊處理器抽象層 (`audioProcessor.ts`)

為了保持程式碼整潔並支援 fallback，將音訊處理邏輯抽離成獨立模組：

```typescript
// frontend/src/lib/audioProcessor.ts

export interface AudioProcessorOptions {
  audioContext: AudioContext
  source: MediaStreamAudioSourceNode
  onAudioChunk: (chunk: Float32Array, sampleRate: number) => void
}

export interface AudioProcessorResult {
  node: AudioWorkletNode | ScriptProcessorNode
  cleanup: () => void
}

/**
 * 建立音訊處理器，優先使用 AudioWorklet，不支援時 fallback 到 ScriptProcessor
 */
export async function createAudioProcessor(
  options: AudioProcessorOptions
): Promise<AudioProcessorResult> {
  const { audioContext, source, onAudioChunk } = options

  const supportsAudioWorklet = 'audioWorklet' in AudioContext.prototype

  if (supportsAudioWorklet) {
    return createWorkletProcessor(audioContext, source, onAudioChunk)
  } else {
    console.warn('AudioWorklet not supported, falling back to ScriptProcessorNode')
    return createScriptProcessor(audioContext, source, onAudioChunk)
  }
}

async function createWorkletProcessor(
  audioContext: AudioContext,
  source: MediaStreamAudioSourceNode,
  onAudioChunk: (chunk: Float32Array, sampleRate: number) => void
): Promise<AudioProcessorResult> {
  // 使用 BASE_URL 確保子路徑部署正確
  const workletPath = `${import.meta.env.BASE_URL}worklets/audio-processor.js`
  await audioContext.audioWorklet.addModule(workletPath)

  const workletNode = new AudioWorkletNode(audioContext, 'audio-processor')

  workletNode.port.onmessage = (event) => {
    if (event.data.type === 'audio') {
      const chunk = new Float32Array(event.data.audioData)
      onAudioChunk(chunk, event.data.sampleRate)
    }
  }

  source.connect(workletNode)
  workletNode.connect(audioContext.destination)

  return {
    node: workletNode,
    cleanup: () => {
      // 1. 移除 event listener，避免殘餘訊息觸發 callback
      workletNode.port.onmessage = null

      // 2. 關閉 MessagePort
      workletNode.port.close()

      // 3. 斷開節點連接
      workletNode.disconnect()
    }
  }
}

function createScriptProcessor(
  audioContext: AudioContext,
  source: MediaStreamAudioSourceNode,
  onAudioChunk: (chunk: Float32Array, sampleRate: number) => void
): AudioProcessorResult {
  const bufferSize = 4096
  const processor = audioContext.createScriptProcessor(bufferSize, 1, 1)

  processor.onaudioprocess = (event) => {
    const audioData = event.inputBuffer.getChannelData(0)
    onAudioChunk(new Float32Array(audioData), audioContext.sampleRate)
  }

  source.connect(processor)
  processor.connect(audioContext.destination)

  return {
    node: processor,
    cleanup: () => {
      processor.onaudioprocess = null
      processor.disconnect()
    }
  }
}
```

### 3. useMicrophone Hook 修改重點

```typescript
// 主要變更點

import { createAudioProcessor, type AudioProcessorResult } from '@/lib/audioProcessor'

// 1. Ref 類型變更
const processorRef = useRef<AudioProcessorResult | null>(null)

// 2. startRecording 內使用抽象層
const startRecording = useCallback(async () => {
  // ... 建立 AudioContext 和 source ...

  // ⚠️ 重要: 保留 AnalyserNode 連接供音量監測使用
  const analyser = audioContext.createAnalyser()
  analyser.fftSize = 256
  analyserRef.current = analyser
  source.connect(analyser) // 分支 A: 音量監測

  // 建立音訊處理器 (分支 B: 錄音)
  const processor = await createAudioProcessor({
    audioContext,
    source,
    onAudioChunk: (chunk, sampleRate) => {
      recordedChunksRef.current.push(chunk)
      onAudioChunk?.(chunk, sampleRate)
    }
  })
  processorRef.current = processor

  // ... 其餘邏輯 ...
}, [/* deps */])

// 3. stopRecording 內使用 cleanup
const stopRecording = useCallback(() => {
  // 使用抽象層提供的 cleanup function
  if (processorRef.current) {
    processorRef.current.cleanup()
    processorRef.current = null
  }

  // ... 其餘清理邏輯 (AudioContext, MediaStream 等) ...
}, [])
```

### 4. 資源清理檢查清單

| 資源 | 清理動作 | 重要性 |
|------|----------|--------|
| `workletNode.port.onmessage` | 設為 `null` | 高 - 避免殘餘訊息觸發 callback |
| `workletNode.port` | 呼叫 `close()` | 中 - 明確關閉 MessagePort |
| `workletNode` | 呼叫 `disconnect()` | 高 - 斷開節點連接 |
| `analyserRef` | 設為 `null` | 中 - 參考清理 |
| `audioContext` | 呼叫 `close()` | 高 - 釋放系統資源 |
| `mediaStream` | 呼叫 `track.stop()` | 高 - 停止麥克風存取 |

### 5. Buffer Size 決策

| Buffer Size | 延遲 (@ 16kHz) | 封包頻率 | 適用場景 |
|-------------|----------------|----------|----------|
| 4096 | 256ms | ~4/秒 | 與舊版相同 (無延遲改善) |
| 2048 | 128ms | ~8/秒 | 保守選擇 |
| **1024** | **64ms** | **~16/秒** | **即時對話 (推薦)** ✅ |
| 512 | 32ms | ~31/秒 | 極低延遲 (封包較頻繁) |
| 128 | 8ms | ~125/秒 | 最低延遲 (高網路開銷) |

**選擇 1024 (64ms)** 作為預設值，平衡延遲與網路開銷。

> **後端相容性**: 後端 `_handle_audio_chunk` 只做 append 和 forward，
> 不強制要求固定 chunk size，只要是合法的 PCM 串流即可。

## 瀏覽器支援

| 瀏覽器 | AudioWorklet 支援 |
|--------|-------------------|
| Chrome | 66+ (2018-04) |
| Firefox | 76+ (2020-05) |
| Safari | 14.1+ (2021-04) |
| Edge | 79+ (2020-01) |

### Fallback 策略

已在 `audioProcessor.ts` 抽象層實作，Hook 本身無需關心底層 API：

```typescript
// 抽象層內部自動判斷
const supportsAudioWorklet = 'audioWorklet' in AudioContext.prototype

if (supportsAudioWorklet) {
  return createWorkletProcessor(...)  // 優先使用
} else {
  console.warn('AudioWorklet not supported, falling back to ScriptProcessorNode')
  return createScriptProcessor(...)   // 降級使用
}
```

**優點**:
- Hook 程式碼簡潔，專注狀態管理
- 抽象層統一處理兩種 API 的差異
- cleanup function 封裝各自的清理邏輯

## 測試計畫

### 單元測試

```typescript
// frontend/src/lib/__tests__/audioProcessor.test.ts

describe('createAudioProcessor', () => {
  beforeEach(() => {
    // Mock AudioContext.audioWorklet.addModule
    // Mock AudioWorkletNode
    // Mock MessagePort
  })

  it('should load audio worklet module with correct path', async () => {
    // 驗證 addModule 使用 BASE_URL
  })

  it('should create AudioWorkletNode when supported', async () => {
    // 驗證 AudioWorkletNode 被建立
  })

  it('should receive audio data via MessagePort', async () => {
    // 驗證 onAudioChunk callback 被呼叫
  })

  it('should fallback to ScriptProcessorNode when AudioWorklet not supported', async () => {
    // 模擬 'audioWorklet' in AudioContext.prototype = false
    // 驗證 createScriptProcessor 被使用
  })

  it('should cleanup MessagePort on cleanup()', async () => {
    // 驗證 port.onmessage = null
    // 驗證 port.close() 被呼叫
  })
})

// frontend/src/hooks/__tests__/useMicrophone.test.ts

describe('useMicrophone', () => {
  it('should maintain AnalyserNode connection for volume metering', async () => {
    // 驗證 source.connect(analyser) 被呼叫
    // 驗證 onVolumeChange callback 被觸發
  })

  it('should cleanup all resources on stopRecording', async () => {
    // 驗證 processor.cleanup() 被呼叫
    // 驗證 audioContext.close() 被呼叫
    // 驗證 mediaStream tracks 被停止
  })
})
```

### 整合測試 (手動)

#### 測試環境準備

```bash
# 1. 啟動前端開發伺服器
cd frontend && npm run dev

# 2. 開啟瀏覽器 DevTools Console
# 3. 確認沒有 ScriptProcessorNode deprecation 警告
```

#### 測試案例

**Phase 0 測試 (VAD 調整)**

| # | 測試項目 | 步驟 | 預期結果 |
|---|----------|------|----------|
| 0-1 | 對話流暢度 | 說一句話後等待 AI 回應 | AI 在 ~0.6s 內開始回應 (不再等 1.2s) |
| 0-2 | 換氣測試 | 說話中故意停頓 0.3s 再繼續 | 不會誤判為結束 |
| 0-3 | Barge-in | AI 回應時打斷說話 | 能成功打斷 AI |

**Phase 1 測試 (AudioWorklet)**

| # | 測試項目 | 步驟 | 預期結果 |
|---|----------|------|----------|
| 1-1 | 基本錄音 | 點擊錄音 → 說話 → 停止 | 音訊正常錄製，無 deprecation 警告 |
| 1-2 | **音量顯示** ⚠️ | 錄音時觀察音量指示器 | **音量隨說話即時變化** (驗證 AnalyserNode) |
| 1-3 | 長時間錄音 | 持續錄音 5 分鐘 | 無記憶體洩漏，效能穩定 |
| 1-4 | 多次開關 | 重複開始/停止錄音 10 次 | 資源正確釋放，無錯誤 |
| 1-5 | WebSocket 串流 | 啟動語音互動 | 音訊正確傳送到後端 |
| 1-6 | Safari 相容性 | 在 Safari 上測試 | 功能正常運作 (或正確 fallback) |
| 1-7 | Firefox 相容性 | 在 Firefox 上測試 | 功能正常運作 |
| 1-8 | 子路徑部署 | 部署到 `/app/` 子路徑 | Worklet 正確載入，無 404 |

**Phase 2 測試 (Binary 傳輸)**

| # | 測試項目 | 步驟 | 預期結果 |
|---|----------|------|----------|
| 2-1 | Binary 接收 | 後端收到音訊訊息 | 正確解析為 PCM16 |
| 2-2 | 混合訊息 | 傳送控制訊息和音訊 | 各自正確處理 |

**⚠️ 特別注意**: 測試案例 1-2 是驗證 AnalyserNode 連接是否保留的關鍵。

#### 效能測試

```javascript
// 在 DevTools Console 執行
// 測試 UI 是否被阻塞

let frameCount = 0
let lastTime = performance.now()

function measureFPS() {
  frameCount++
  const now = performance.now()
  if (now - lastTime >= 1000) {
    console.log(`FPS: ${frameCount}`)
    frameCount = 0
    lastTime = now
  }
  requestAnimationFrame(measureFPS)
}

measureFPS()
// 開始錄音後，FPS 應維持在 55-60
```

#### 延遲測試

```javascript
// 測量音訊處理延遲
// 在 worklet processor 加入時間戳記
// 比較主線程收到訊息的時間差
```

### CI 測試

```yaml
# 確保現有測試通過
- npm run test
- npm run lint
- npm run type-check
```

## 實作順序

按優先級分階段執行，每階段完成後可獨立驗證效果。

---

### Phase 0: 快速調參 (立即見效) 🔴

**目標**: 調整 VAD 參數，減少 ~600ms 延遲

1. [ ] 修改 `InteractionPanel.tsx`
   ```typescript
   // Before
   const SILENCE_DURATION_MS = 1200

   // After (建議值)
   const SILENCE_DURATION_MS = 600  // 或 800
   ```

2. [ ] 手動測試對話流暢度
3. [ ] 確認 Barge-in 功能正常

**預期效果**: 用戶講完後反應時間從 1.2s 降至 0.6s

---

### Phase 1: AudioWorklet 重構 (治本) 🟠

**目標**: 解決採樣延遲與主線程阻塞

1. [ ] 建立 `frontend/public/worklets/audio-processor.js`
2. [ ] 建立 `frontend/src/lib/audioProcessor.ts` 抽象層
3. [ ] 修改 `frontend/src/hooks/useMicrophone.ts`
   - [ ] 改用 `createAudioProcessor` 抽象層
   - [ ] 確保 AnalyserNode 連接保留 (音量監測)
   - [ ] 更新清理邏輯
4. [ ] 更新單元測試
   - [ ] Mock AudioWorklet API
   - [ ] 測試 fallback 邏輯
5. [ ] 手動整合測試
   - [ ] 音量指示器正常運作
   - [ ] 錄音功能正常
6. [ ] 跨瀏覽器測試 (Chrome, Firefox, Safari)

**預期效果**:
- 採樣延遲從 256ms 降至 ~8ms
- 消除 deprecation 警告
- UI 不再因音訊處理而卡頓

---

### Phase 2: Binary 傳輸優化 🟡

**目標**: 減少傳輸開銷

1. [ ] 修改前端 WebSocket 傳輸
   ```typescript
   // Before: JSON + Base64
   sendMessage('audio_chunk', { audio: base64Audio, ... })

   // After: Binary
   ws.send(pcm16Buffer)
   ```

2. [ ] 修改後端 WebSocket Handler
   - [ ] 區分 Text Message (控制訊號)
   - [ ] 區分 Binary Message (音訊數據)

3. [ ] 定義 Binary 協議格式 (如需 metadata)

**預期效果**:
- 傳輸數據量減少 ~33%
- 減少編解碼 CPU 開銷

---

### Phase 3: 驗證與調優

1. [ ] 端到端延遲測量
   - [ ] 錄製用戶說話到 AI 回應的時間
   - [ ] 比較優化前後數據

2. [ ] 效能監控
   - [ ] FPS 監控確認 UI 流暢
   - [ ] 記憶體使用檢查

3. [ ] Code review

## 風險評估

### Phase 0 風險 (VAD 調整)

| 風險 | 機率 | 影響 | 緩解措施 |
|------|------|------|----------|
| 誤判用戶換氣為結束 | 中 | 低 | Barge-in 功能讓用戶可打斷 |
| 對話節奏太快 | 低 | 低 | 可微調至 700-800ms |

### Phase 1 風險 (AudioWorklet)

| 風險 | 機率 | 影響 | 緩解措施 |
|------|------|------|----------|
| Safari 相容性問題 | 中 | 高 | 實作 fallback，充分測試 |
| Worklet 載入失敗 | 低 | 高 | 錯誤處理，自動 fallback 機制 |
| MessagePort 記憶體洩漏 | 低 | 中 | cleanup 函式明確清理 port |
| 效能不如預期 | 低 | 低 | 保留 ScriptProcessor 選項 |
| 音量監測失效 | 低 | 中 | 確保 AnalyserNode 連接獨立於處理器 |
| 子路徑部署 404 | 低 | 高 | 使用 `import.meta.env.BASE_URL` |

### Phase 2 風險 (Binary 傳輸)

| 風險 | 機率 | 影響 | 緩解措施 |
|------|------|------|----------|
| 後端 breaking change | 中 | 高 | 版本協商，漸進遷移 |
| Proxy 不支援 Binary WS | 低 | 中 | 保留 Base64 fallback |

## 回滾計畫

如果發現問題：

```bash
# 1. 切回 main branch
git checkout main

# 2. 或 revert commit
git revert <commit-hash>
```

由於實作了 fallback 機制，也可以透過 feature flag 快速切換：

```typescript
const USE_AUDIO_WORKLET = false // 設為 false 強制使用舊 API
```

## 參考資料

- [MDN: AudioWorkletNode](https://developer.mozilla.org/en-US/docs/Web/API/AudioWorkletNode)
- [MDN: AudioWorkletProcessor](https://developer.mozilla.org/en-US/docs/Web/API/AudioWorkletProcessor)
- [Web Audio API Specification](https://webaudio.github.io/web-audio-api/#audioworklet)
- [Google Developers: Audio Worklet](https://developer.chrome.com/blog/audio-worklet/)

## 預期效果總結

| 階段 | 優化項目 | 延遲減少 | 累計效果 |
|------|----------|----------|----------|
| Phase 0 | VAD 1200ms → 600ms | **-600ms** | 體感延遲減半 |
| Phase 1 | Buffer 256ms → 64ms | **-192ms** | 採樣延遲降 75% |
| Phase 2 | Base64 → Binary | -數十 ms | 傳輸更高效 |

**優化前總延遲**: ~1.5 秒 (VAD 1.2s + 採樣 256ms + 處理)
**優化後總延遲**: ~0.7 秒 (VAD 0.6s + 採樣 64ms + 處理)

> **註**: Phase 1 採用 bufferSize=1024 (64ms)。若需更低延遲可改為 512 (32ms)，
> 但需評估網路封包頻率增加的影響。

---

## 工作量估計

| 階段 | 變更範圍 | 複雜度 |
|------|----------|--------|
| Phase 0 | 1 行常數 | ⭐ 極低 |
| Phase 1 | ~200 行，3 個檔案 | ⭐⭐⭐ 中等 |
| Phase 2 | 前後端各 ~50 行 | ⭐⭐ 低 |

# Research: Magic DJ Controller

**Date**: 2026-01-28
**Feature**: 010-magic-dj-controller

## Research Topics

### 1. 多音軌同時播放 (Multi-Track Playback)

**問題**: 系統需要支援同時播放多個音軌（背景音樂 + 音效疊加），現有 `useAudioPlayback` hook 主要用於單一音訊串流。

**Decision**: 使用 Web Audio API 的 AudioContext 和多個獨立 GainNode

**Rationale**:
- Web Audio API 原生支援多個音源同時播放
- 每個音軌使用獨立的 AudioBufferSourceNode → GainNode → destination
- 可個別控制每個音軌的音量
- 現有 `useAudioPlayback` 已有 AudioContext 管理邏輯可複用

**Alternatives Considered**:
1. HTML5 Audio 元素：簡單但延遲較高，不支援細緻控制
2. Howler.js 第三方庫：功能強大但增加依賴，現有 Web Audio 實作足夠

**Implementation Notes**:
```typescript
// 多音軌播放器架構
interface MultiTrackPlayer {
  tracks: Map<string, {
    buffer: AudioBuffer
    source: AudioBufferSourceNode | null
    gainNode: GainNode
    isPlaying: boolean
  }>

  loadTrack(id: string, url: string): Promise<void>
  playTrack(id: string, loop?: boolean): void
  stopTrack(id: string): void
  setVolume(id: string, volume: number): void
  playAll(): void
  stopAll(): void
}
```

---

### 2. Gemini 2.5 Native Audio 整合

**問題**: 需要整合 Gemini 2.5 Native Audio API 進行即時語音對話，並支援手動控制（繞過自動 VAD）。

**Decision**: 複用現有 `useWebSocket` hook 和 `interactionStore`，擴展支援手動 VAD 控制

**Rationale**:
- 現有 004-interaction-module 已實作完整的 Gemini WebSocket 通訊
- `useWebSocket` 支援 `interrupt` 訊息類型
- `interactionStore` 已有 `enableVAD` 和 `bargeInEnabled` 設定
- 只需新增「強制送出」功能，直接觸發 `end_turn` 訊息

**Alternatives Considered**:
1. 新建獨立的 Gemini 連線邏輯：重複工作，難以維護
2. 修改後端 API：增加複雜度，現有 WebSocket 協議已足夠

**Implementation Notes**:
```typescript
// 擴展 interactionStore 的 actions
interface DJControlActions {
  // 手動觸發結束輪次（繞過 VAD）
  forceEndTurn: () => void

  // 中斷 AI 回應
  interruptAI: () => void

  // 設定 System Prompt（兒童友善）
  setChildFriendlyPrompt: (prompt: string) => void
}
```

---

### 3. 鍵盤熱鍵實作

**問題**: RD 需要透過熱鍵快速觸發音效和控制，類似 DJ 操作。

**Decision**: 使用 React 的 `useEffect` + `keydown` 事件監聽

**Rationale**:
- 原生瀏覽器事件效能最佳
- 不需額外依賴
- 可配置熱鍵映射
- 支援組合鍵（Ctrl+Space 等）

**Alternatives Considered**:
1. react-hotkeys-hook 庫：功能完整但增加依賴
2. Mousetrap.js：老牌庫但維護較少

**Implementation Notes**:
```typescript
// 預設熱鍵配置
const DEFAULT_HOTKEYS = {
  forceSubmit: ' ',           // 空白鍵
  interrupt: 'Escape',        // ESC
  fillerSound: 'f',           // F 鍵
  rescueWait: 'w',            // W 鍵
  rescueEnd: 'e',             // E 鍵
  toggleMode: 'm',            // M 鍵
  track1: '1',                // 數字鍵 1-9
  track2: '2',
  // ...
}

// Hook 實作
function useDJHotkeys(actions: DJActions) {
  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      if (e.key === ' ' && !e.repeat) {
        e.preventDefault()
        actions.forceSubmit()
      }
      // ...
    }
    window.addEventListener('keydown', handler)
    return () => window.removeEventListener('keydown', handler)
  }, [actions])
}
```

---

### 4. 音訊檔案預載和管理

**問題**: 預錄音檔需要預先載入以確保播放延遲 < 100ms。

**Decision**: 在元件掛載時預載所有音檔到 AudioBuffer

**Rationale**:
- 預載確保零延遲播放
- AudioBuffer 在記憶體中，播放即時
- 音檔數量有限（約 10-15 個），記憶體佔用可接受

**Alternatives Considered**:
1. 按需載入：首次播放會有延遲
2. Service Worker 快取：增加複雜度，純前端快取已足夠

**Implementation Notes**:
```typescript
// 聲音項目配置（與 data-model.md SoundItem 一致）
// 完整型別定義見 data-model.md

const DEFAULT_SOUND_LIBRARY: SoundItem[] = [
  { id: 'voice_intro', name: '開場白', channel: 'voice', priority: 'normal', url: '/audio/intro.mp3', hotkey: '1' },
  { id: 'music_cleanup', name: '收玩具歌', channel: 'music', priority: 'normal', url: '/audio/cleanup.mp3', hotkey: '2', loop: true },
  { id: 'sfx_success', name: '成功獎勵', channel: 'sfx', priority: 'normal', url: '/audio/success.mp3', hotkey: '3' },
  { id: 'sfx_thinking', name: '思考音效', channel: 'sfx', priority: 'normal', url: '/audio/thinking.mp3', hotkey: 'f' },
  { id: 'voice_wait', name: '等待填補', channel: 'voice', priority: 'rescue', url: '/audio/wait.mp3', hotkey: 'w' },
  { id: 'voice_end', name: '緊急結束', channel: 'voice', priority: 'rescue', url: '/audio/end.mp3', hotkey: 'e' },
]
```

---

### 5. 播放清單 (Cue List) 拖曳功能

**問題**: RD 需要從聲音庫拖曳項目到播放清單，並支援在清單內重新排序。

**Decision**: 優先使用 HTML5 Drag and Drop API；若跨區域拖曳（Sound Library → Cue List）體驗不佳，升級至 @dnd-kit/core

**Rationale**:
- HTML5 Drag and Drop 是原生 API，無需額外依賴，適合基礎場景
- Cue List 需要兩種拖曳：跨區域（Sound Library → Cue List）和區內排序（Cue List 內重新排序）
- HTML5 DnD 在區內排序的視覺回饋較弱，可能需要 @dnd-kit 補強
- @dnd-kit 是 react-beautiful-dnd 的現代替代方案，維護活躍

**Alternatives Considered**:
1. react-beautiful-dnd：功能強大但已停止維護（deprecated）
2. @dnd-kit/core：現代方案，支援跨容器拖曳和排序，作為升級備選
3. 純 HTML5 DnD：基礎方案，先嘗試此方案

**升級判斷標準**：若 HTML5 DnD 在以下任一場景表現不佳，則升級至 @dnd-kit：
- 跨區域拖曳的視覺回饋延遲 > 200ms（SC-007）
- 區內排序的拖曳體驗不流暢
- 觸控裝置支援不足

**Implementation Notes**:
```typescript
// 拖曳 Hook 設計
interface UseDragAndDropOptions {
  onDragStart?: (item: DragItem) => void
  onDragEnd?: (item: DragItem, target: DropTarget) => void
  onDragOver?: (item: DragItem, target: DropTarget) => void
}

interface DragItem {
  id: string
  type: 'sound-item' | 'cue-item'
  data: SoundItem | CueItem
}

interface DropTarget {
  type: 'cue-list' | 'sound-library' | 'cue-list-reorder'
  index?: number  // 用於排序時的目標位置
}

// 拖曳到 Cue List
const handleDropToCueList = (item: DragItem) => {
  if (item.type === 'sound-item') {
    addToCueList(item.data.id)
  }
}

// 在 Cue List 內重新排序
const handleCueListReorder = (fromIndex: number, toIndex: number) => {
  reorderCueList(fromIndex, toIndex)
}
```

**視覺回饋**:
- 拖曳時顯示半透明的項目預覽
- 目標區域高亮顯示可放置狀態
- 放置動畫使用 CSS transitions
- 拖曳延遲 < 200ms

---

## Summary

| 研究主題 | 決策 | 影響 |
|----------|------|------|
| 多音軌播放 | Web Audio API + 獨立 GainNode | 新增 `useMultiTrackPlayer` hook |
| Gemini 整合 | 複用現有 WebSocket + 擴展控制 | 擴展 interactionStore actions |
| 鍵盤熱鍵 | 原生 keydown 事件 | 新增 `useDJHotkeys` hook |
| 音檔預載 | 元件掛載時預載到 AudioBuffer | TrackPlayer 元件處理 |
| 播放清單拖曳 | HTML5 Drag and Drop API | 新增 `useDragAndDrop` hook |

---

## Dependencies

無需新增外部依賴，完全複用現有套件：
- zustand (已有)
- Web Audio API (瀏覽器原生)
- React hooks (已有)

## Risks and Mitigations

| 風險 | 機率 | 影響 | 緩解措施 |
|------|------|------|----------|
| AudioContext 被瀏覽器暫停 | 中 | 高 | 使用者互動後恢復（現有實作已處理） |
| Gemini API 延遲過高 | 中 | 高 | 救場語音機制，RD 手動處理 |
| 熱鍵與其他功能衝突 | 低 | 低 | 可配置熱鍵，避免常用組合 |

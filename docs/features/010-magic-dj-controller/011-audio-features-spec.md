# Magic DJ Audio Features Enhancement

## Overview

增強 Magic DJ 的音軌管理功能，支援直接上傳 MP3 檔案以及調整各音軌音量。

**功能目標**：
1. **Phase 1**: MP3 上傳功能 - 讓使用者除了 TTS 生成外，可以直接上傳 MP3 檔案作為音軌
2. **Phase 2**: 音量控制功能 - 讓每個音軌可以獨立調整音量，方便同時播放時區分

---

## Phase 1: MP3 上傳功能

### 需求描述

目前 Magic DJ 音軌只能透過 TTS 生成，需要增加直接上傳 MP3 檔案的選項，讓使用者可以使用自己準備的音效、音樂或錄音。

### 使用情境

1. RD 有預先錄製好的背景音樂想直接使用
2. 使用外部工具（如 Adobe Audition）製作的音效
3. 使用其他 TTS 服務生成的音檔
4. 版權音樂或特殊音效素材

### 技術規格

#### 1.1 Track 類型擴充

```typescript
// frontend/src/types/magic-dj.ts

// 新增音軌來源類型
type TrackSource = 'tts' | 'upload';

interface Track {
  id: string;
  name: string;
  type: TrackType;
  url: string;
  hotkey?: string;
  loop?: boolean;
  duration?: number;
  isCustom?: boolean;
  textContent?: string;
  audioBase64?: string;

  // 新增欄位
  source: TrackSource;           // 音軌來源：'tts' | 'upload'
  originalFileName?: string;     // 上傳時的原始檔名
}
```

#### 1.2 TrackEditorModal 修改

**UI 變更**:

```
┌─────────────────────────────────────────────────────┐
│  編輯音軌                                      [X]  │
├─────────────────────────────────────────────────────┤
│                                                     │
│  音軌名稱: [________________]                       │
│                                                     │
│  音軌類型: [下拉選單 ▼]                            │
│                                                     │
│  快捷鍵:   [1-5 或留空]                            │
│                                                     │
│  ─────────────────────────────────────────────────  │
│                                                     │
│  音源方式:  ○ TTS 生成    ● 上傳 MP3               │
│                                                     │
│  ┌─────────────────────────────────────────────┐   │
│  │  [TTS 設定區域 - 當選擇 TTS 時顯示]         │   │
│  │                                              │   │
│  │  文字內容: [多行輸入框______________]       │   │
│  │  TTS 供應商: [VoAI ▼]                       │   │
│  │  語音:      [小美 ▼]                        │   │
│  │  語速:      [1.0x ▼]                        │   │
│  │                                              │   │
│  │  [生成語音]                                 │   │
│  └─────────────────────────────────────────────┘   │
│                                                     │
│  ┌─────────────────────────────────────────────┐   │
│  │  [上傳區域 - 當選擇上傳時顯示]              │   │
│  │                                              │   │
│  │  ┌───────────────────────────────────────┐  │   │
│  │  │                                        │  │   │
│  │  │   拖放 MP3 檔案至此處                  │  │   │
│  │  │        或                              │  │   │
│  │  │   [選擇檔案]                           │  │   │
│  │  │                                        │  │   │
│  │  │   支援格式: MP3, WAV, OGG              │  │   │
│  │  │   檔案大小上限: 10MB                   │  │   │
│  │  │                                        │  │   │
│  │  └───────────────────────────────────────┘  │   │
│  │                                              │   │
│  │  已選擇: background_music.mp3 (2.3MB)       │   │
│  │                                              │   │
│  └─────────────────────────────────────────────┘   │
│                                                     │
│  ─────────────────────────────────────────────────  │
│                                                     │
│  音訊預覽:  [▶ 播放]  [⏹ 停止]   00:00 / 01:23    │
│                                                     │
│  ─────────────────────────────────────────────────  │
│                                                     │
│                        [取消]    [儲存]             │
│                                                     │
└─────────────────────────────────────────────────────┘
```

#### 1.3 檔案處理邏輯

```typescript
// frontend/src/components/magic-dj/TrackEditorModal.tsx

interface FileUploadState {
  file: File | null;
  fileName: string;
  fileSize: number;
  audioUrl: string | null;      // blob URL for preview
  audioBase64: string | null;   // for persistence
  duration: number | null;
  error: string | null;
  isProcessing: boolean;
}

// 支援的音訊格式
const SUPPORTED_AUDIO_TYPES = [
  'audio/mpeg',      // MP3
  'audio/wav',       // WAV
  'audio/ogg',       // OGG
  'audio/webm',      // WebM
];

// 檔案大小限制 (10MB)
const MAX_FILE_SIZE = 10 * 1024 * 1024;

// 檔案處理流程
async function processUploadedFile(file: File): Promise<FileUploadState> {
  // 1. 驗證檔案類型
  if (!SUPPORTED_AUDIO_TYPES.includes(file.type)) {
    throw new Error('不支援的檔案格式');
  }

  // 2. 驗證檔案大小
  if (file.size > MAX_FILE_SIZE) {
    throw new Error('檔案大小超過 10MB 限制');
  }

  // 3. 讀取檔案為 ArrayBuffer
  const arrayBuffer = await file.arrayBuffer();

  // 4. 轉換為 base64
  const base64 = arrayBufferToBase64(arrayBuffer);

  // 5. 建立 blob URL 供預覽
  const blob = new Blob([arrayBuffer], { type: file.type });
  const blobUrl = URL.createObjectURL(blob);

  // 6. 取得音訊時長
  const duration = await getAudioDuration(blobUrl);

  return {
    file,
    fileName: file.name,
    fileSize: file.size,
    audioUrl: blobUrl,
    audioBase64: base64,
    duration,
    error: null,
    isProcessing: false,
  };
}
```

#### 1.4 拖放上傳元件

```typescript
// frontend/src/components/magic-dj/AudioDropzone.tsx

interface AudioDropzoneProps {
  onFileAccepted: (file: File) => void;
  onError: (error: string) => void;
  isProcessing: boolean;
  currentFile?: {
    name: string;
    size: number;
  };
}

// 使用原生 HTML5 drag-and-drop API
// 或整合 react-dropzone 套件
```

#### 1.5 資料遷移

既有音軌需要加上 `source: 'tts'` 預設值：

```typescript
// 在 store 初始化時處理
const migrateTrackData = (track: Track): Track => ({
  ...track,
  source: track.source || 'tts',
});
```

### 驗收標準 (Phase 1)

- [ ] 可以切換音源方式：TTS 生成 / 上傳 MP3
- [ ] 支援拖放上傳 MP3/WAV/OGG 檔案
- [ ] 支援點擊選擇檔案上傳
- [ ] 顯示已選擇的檔案名稱和大小
- [ ] 檔案大小超過 10MB 時顯示錯誤訊息
- [ ] 不支援的檔案格式顯示錯誤訊息
- [ ] 上傳的音訊可以預覽播放
- [ ] 上傳的音訊可以正確儲存並持久化（localStorage）
- [ ] 重新載入頁面後，上傳的音軌仍可正常播放
- [ ] TrackList 中顯示音軌來源圖示（TTS / 上傳）

---

## Phase 2: 音量控制功能

### 需求描述

目前雖然播放器內部支援音量控制，但沒有持久化且 UI 上沒有明顯的控制項。需要增加每個音軌的獨立音量控制，並持久化設定。

### 使用情境

1. 背景音樂需要比語音小聲，避免蓋過說話聲
2. 音效需要比對話聲大聲，確保兒童注意到
3. 不同來源的音軌錄音音量不一致，需要平衡
4. 同時播放多軌時，需要調整各軌平衡

### 技術規格

#### 2.1 Track 類型擴充

```typescript
// frontend/src/types/magic-dj.ts

interface Track {
  // ... 現有欄位

  // Phase 2 新增
  volume: number;  // 0.0 ~ 1.0，預設 1.0
}
```

#### 2.2 TrackPlayer UI 修改

```
┌─────────────────────────────────────────────────────────────┐
│ [▶]  開場白介紹                              [1] [✏] [🗑]   │
│      ──────────────────────────────── 00:15                │
│      🔊 ────────●──────── 80%                              │
└─────────────────────────────────────────────────────────────┘

Legend:
- [▶] 播放/暫停按鈕
- 進度條
- 🔊 音量圖示 + 滑桿 + 百分比顯示
- [1] 快捷鍵
- [✏] 編輯
- [🗑] 刪除
```

#### 2.3 音量滑桿元件

```typescript
// frontend/src/components/magic-dj/VolumeSlider.tsx

interface VolumeSliderProps {
  value: number;           // 0.0 ~ 1.0
  onChange: (value: number) => void;
  disabled?: boolean;
  size?: 'sm' | 'md';      // 緊湊版 vs 標準版
}

// 功能：
// - 滑桿拖動調整音量
// - 點擊音量圖示切換靜音
// - 顯示音量百分比
// - 音量圖示隨音量大小變化（🔇 🔈 🔉 🔊）
```

#### 2.4 音量圖示對應

| 音量範圍 | 圖示 |
|---------|------|
| 0%      | 🔇 (靜音) |
| 1-33%   | 🔈 (低音量) |
| 34-66%  | 🔉 (中音量) |
| 67-100% | 🔊 (高音量) |

#### 2.5 Store 更新

```typescript
// frontend/src/stores/magicDJStore.ts

interface MagicDJStore {
  // ... 現有欄位

  // Phase 2 新增 actions
  setTrackVolume: (trackId: string, volume: number) => void;
  toggleTrackMute: (trackId: string) => void;
}

// 音量值會自動持久化到 localStorage
```

#### 2.6 TrackEditorModal 音量設定

在編輯音軌時也可以設定預設音量：

```
┌─────────────────────────────────────────────────────┐
│  編輯音軌                                      [X]  │
├─────────────────────────────────────────────────────┤
│                                                     │
│  ...（其他欄位）...                                 │
│                                                     │
│  ─────────────────────────────────────────────────  │
│                                                     │
│  預設音量:  🔊 ────────●──────── 80%               │
│                                                     │
│  ─────────────────────────────────────────────────  │
│                                                     │
│                        [取消]    [儲存]             │
│                                                     │
└─────────────────────────────────────────────────────┘
```

#### 2.7 TrackList 整體佈局調整

```
┌─────────────────────────────────────────────────────────────────────┐
│  音軌列表                                              [+ 新增音軌] │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ≡  [▶]  開場白介紹           🎤  🔊 ──●── 80%   [1]  [✏] [🗑]    │
│                                                                     │
│  ≡  [⏸]  背景音樂             📁  🔉 ●──── 40%   [2]  [✏] [🗑]    │
│       ████████░░░░░░░░░░░░░░░ 00:45 / 02:30                        │
│                                                                     │
│  ≡  [▶]  轉場音效             🎤  🔊 ────●  100%  [3]  [✏] [🗑]    │
│                                                                     │
│  ≡  [▶]  歡呼聲               📁  🔊 ───●─  90%   [4]  [✏] [🗑]    │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘

Legend:
- ≡    拖動排序手柄
- [▶]  播放按鈕
- [⏸]  播放中（點擊停止）
- 🎤   TTS 生成的音軌
- 📁   上傳的音軌
- 🔊   音量滑桿
- [1]  快捷鍵
- [✏]  編輯
- [🗑]  刪除
```

### 驗收標準 (Phase 2)

- [ ] 每個音軌顯示音量滑桿
- [ ] 可以拖動滑桿調整音量 (0% ~ 100%)
- [ ] 點擊音量圖示可以切換靜音
- [ ] 音量圖示隨音量大小變化
- [ ] 音量設定自動持久化
- [ ] 重新載入頁面後音量設定保留
- [ ] 播放時音量設定即時生效
- [ ] 編輯音軌時可以設定預設音量
- [ ] 多軌同時播放時，各軌音量獨立控制
- [ ] Master volume 仍然可以控制整體音量

---

## 實作計畫

### Phase 1 任務分解

| 任務 | 預估複雜度 | 相依性 |
|-----|----------|--------|
| 1.1 擴充 Track 類型定義 | 低 | - |
| 1.2 實作 AudioDropzone 元件 | 中 | - |
| 1.3 修改 TrackEditorModal - 加入音源切換 | 中 | 1.1 |
| 1.4 實作檔案處理邏輯 | 中 | - |
| 1.5 整合 AudioDropzone 到 TrackEditorModal | 低 | 1.2, 1.3 |
| 1.6 處理資料遷移（舊資料相容） | 低 | 1.1 |
| 1.7 TrackList 顯示來源圖示 | 低 | 1.1 |
| 1.8 測試與除錯 | 中 | All |

### Phase 2 任務分解

| 任務 | 預估複雜度 | 相依性 |
|-----|----------|--------|
| 2.1 擴充 Track 類型 - 加入 volume | 低 | - |
| 2.2 實作 VolumeSlider 元件 | 中 | - |
| 2.3 修改 TrackPlayer 加入 VolumeSlider | 低 | 2.2 |
| 2.4 Store 新增 setTrackVolume action | 低 | 2.1 |
| 2.5 整合音量控制到播放器 hook | 低 | 2.4 |
| 2.6 TrackEditorModal 加入預設音量設定 | 低 | 2.2 |
| 2.7 處理資料遷移（舊資料預設音量 1.0） | 低 | 2.1 |
| 2.8 測試與除錯 | 中 | All |

---

## 技術考量

### 儲存空間

- 上傳的音檔會以 base64 存儲在 localStorage
- localStorage 通常限制 5-10MB
- 建議：
  - 單檔限制 10MB
  - 可考慮壓縮音訊或降低取樣率
  - 未來可考慮 IndexedDB 或後端儲存

### 效能

- base64 編碼會增加約 33% 的資料大小
- 大量音軌可能影響頁面載入速度
- 建議：延遲載入音訊資料，只在需要時解碼

### 瀏覽器相容性

- Web Audio API: 所有現代瀏覽器支援
- Drag and Drop API: 所有現代瀏覽器支援
- File API: 所有現代瀏覽器支援

### 向後相容

- 舊版資料自動遷移
- `source` 預設為 `'tts'`
- `volume` 預設為 `1.0`

---

## 未來擴充可能

1. **後端儲存**: 將音檔上傳至後端，解決 localStorage 限制
2. **音訊裁剪**: 上傳後可以裁剪音訊片段
3. **音訊效果**: 淡入淡出、迴音等效果
4. **波形顯示**: 顯示音訊波形圖
5. **音軌分組**: 將音軌分組管理（如：背景音樂、音效、對話）
6. **預設音量模板**: 儲存常用的音量配置

---

## 檔案變更清單

### Phase 1 新增/修改檔案

```
frontend/src/
├── types/
│   └── magic-dj.ts                    # 修改 - Track 類型擴充
├── components/magic-dj/
│   ├── AudioDropzone.tsx              # 新增 - 拖放上傳元件
│   ├── TrackEditorModal.tsx           # 修改 - 加入上傳功能
│   └── TrackList.tsx                  # 修改 - 顯示來源圖示
└── stores/
    └── magicDJStore.ts                # 修改 - 資料遷移處理
```

### Phase 2 新增/修改檔案

```
frontend/src/
├── types/
│   └── magic-dj.ts                    # 修改 - 加入 volume 欄位
├── components/magic-dj/
│   ├── VolumeSlider.tsx               # 新增 - 音量滑桿元件
│   ├── TrackPlayer.tsx                # 修改 - 加入音量控制
│   ├── TrackEditorModal.tsx           # 修改 - 加入預設音量設定
│   └── TrackList.tsx                  # 修改 - 調整佈局
├── hooks/
│   └── useMultiTrackPlayer.ts         # 修改 - 整合持久化音量
└── stores/
    └── magicDJStore.ts                # 修改 - 新增 setTrackVolume
```

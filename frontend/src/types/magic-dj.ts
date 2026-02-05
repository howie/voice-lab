/**
 * Magic DJ Controller Types
 * Feature: 010-magic-dj-controller
 * Feature: 011-magic-dj-audio-features
 * Feature: 015-magic-dj-ai-prompts
 *
 * T003: TypeScript types and interfaces for Magic DJ module.
 * 011-T001~T005: Audio features enhancement types.
 * 015-T001~T005: AI prompt template types.
 */

// =============================================================================
// Track Types
// =============================================================================

/**
 * Track type classification
 */
export type TrackType =
  | 'intro' // 開場
  | 'transition' // 過場
  | 'effect' // 音效
  | 'song' // 歌曲
  | 'filler' // 填補音效（思考中）
  | 'rescue' // 救場語音

// =============================================================================
// Channel Types (DD-001: 4-Channel Vertical Layout)
// =============================================================================

/**
 * Playback channel type - 4 vertical channels in DJ Mixer layout
 */
export type ChannelType = 'rescue' | 'voice' | 'sfx' | 'music'

/**
 * Channel configuration - defines which track types belong to each channel
 */
export interface ChannelConfig {
  type: ChannelType
  label: string
  description: string
  /** Track types accepted by this channel */
  acceptTypes: TrackType[]
}

/**
 * A queued item in a channel (same track can appear multiple times)
 */
export interface ChannelQueueItem {
  /** Unique instance ID (UUID) */
  id: string
  /** Reference to Sound Library track ID */
  trackId: string
}

/**
 * Per-channel playback state
 */
export interface ChannelState {
  /** Current playback position index in queue (-1 = none) */
  currentIndex: number
  /** Channel volume 0.0 ~ 1.0 */
  volume: number
  /** Whether channel is muted */
  isMuted: boolean
}

/**
 * Track source type (011-T001)
 * - tts: 透過 TTS 服務生成
 * - upload: 使用者上傳的音檔
 */
export type TrackSource = 'tts' | 'upload'

/**
 * Track configuration (011-T002)
 */
export interface Track {
  /** 唯一識別碼，如 'track_01_intro' */
  id: string
  /** 顯示名稱，如 '開場' */
  name: string
  /** 類型分類 */
  type: TrackType
  /** 音檔 URL，如 '/audio/intro.mp3' 或 blob URL */
  url: string
  /** 熱鍵，如 '1' */
  hotkey?: string
  /** 是否循環播放 */
  loop?: boolean
  /** 時長（毫秒），載入後填入 */
  duration?: number
  /** 是否為自訂音軌（動態新增的） */
  isCustom?: boolean
  /** 原始文字內容（用於編輯） */
  textContent?: string
  /** Base64 編碼的音訊資料（用於 localStorage 持久化） */
  audioBase64?: string

  // === 011 Audio Features Enhancement ===
  /** 音軌來源：'tts' | 'upload' (011-T002) */
  source: TrackSource
  /** 上傳時的原始檔名，僅 upload 類型 (011-T002) */
  originalFileName?: string
  /** 音量 0.0 ~ 1.0，預設 1.0 (011-T002) */
  volume: number

  // === 011 Phase 4: IndexedDB Storage ===
  /** 是否有本地音訊儲存在 IndexedDB */
  hasLocalAudio?: boolean
}

/**
 * Track playback state (011-T005)
 */
export interface TrackPlaybackState {
  trackId: string
  isPlaying: boolean
  isLoaded: boolean
  isLoading: boolean
  /** 載入或播放錯誤 */
  error: string | null
  /** 當前播放位置（毫秒） */
  currentTime: number
  /** 音量 0-1 */
  volume: number

  // === 011 Audio Features Enhancement (T005) ===
  /** 是否靜音 */
  isMuted: boolean
  /** 靜音前的音量（用於恢復） */
  previousVolume: number
}

/**
 * File upload state (011-T003)
 */
export interface FileUploadState {
  /** 原始 File 物件 */
  file: File | null
  /** 檔案名稱 */
  fileName: string
  /** 檔案大小 (bytes) */
  fileSize: number
  /** blob URL (用於預覽) */
  audioUrl: string | null
  /** base64 編碼 (用於儲存) */
  audioBase64: string | null
  /** 音訊時長 (毫秒) */
  duration: number | null
  /** 錯誤訊息 */
  error: string | null
  /** 是否處理中 */
  isProcessing: boolean
}

// =============================================================================
// Audio Features Constants (011-T004)
// =============================================================================

/** 支援的音訊 MIME 類型 */
export const SUPPORTED_AUDIO_TYPES = [
  'audio/mpeg', // MP3
  'audio/wav', // WAV
  'audio/ogg', // OGG
  'audio/webm', // WebM
] as const

/** 檔案大小上限 (10MB) */
export const MAX_FILE_SIZE = 10 * 1024 * 1024

/** 同時播放上限 */
export const MAX_CONCURRENT_TRACKS = 5

/** 音量圖示對應 */
export const VOLUME_ICONS = {
  muted: '🔇', // 0%
  low: '🔈', // 1-33%
  medium: '🔉', // 34-66%
  high: '🔊', // 67-100%
} as const

// =============================================================================
// Cue List Types (US3 - FR-028~FR-037)
// =============================================================================

/**
 * Cue item status in the cue list
 */
export type CueItemStatus = 'pending' | 'playing' | 'played' | 'invalid'

/**
 * A single item in the cue list, referencing a track from Sound Library.
 * The same track can appear multiple times in the cue list (FR-036).
 */
export interface CueItem {
  /** Unique instance ID (UUID) */
  id: string
  /** Reference to Sound Library track ID */
  trackId: string
  /** Display order (1-based) */
  order: number
  /** Current status */
  status: CueItemStatus
}

/**
 * Cue list for prerecorded mode (FR-028~FR-037).
 * Stored in localStorage (FR-037).
 */
export interface CueList {
  /** List identifier */
  id: string
  /** List name */
  name: string
  /** Ordered items */
  items: CueItem[]
  /** Current playback position (0-based index, -1 = not started) */
  currentPosition: number
  /** Created timestamp */
  createdAt: number
  /** Updated timestamp */
  updatedAt: number
}

/** Default empty cue list */
export const DEFAULT_CUE_LIST: CueList = {
  id: 'default',
  name: '預設播放清單',
  items: [],
  currentPosition: -1,
  createdAt: Date.now(),
  updatedAt: Date.now(),
}

// =============================================================================
// Operation Mode Types
// =============================================================================

/**
 * Operation mode for the DJ controller
 */
export type OperationMode = 'prerecorded' | 'ai-conversation'

// =============================================================================
// Session & Observation Types (T040)
// =============================================================================

/**
 * Operation log entry for session tracking
 */
export interface OperationLog {
  /** 時間戳 (ISO 8601) */
  timestamp: string
  /** 操作類型 */
  action:
    | 'force_submit'
    | 'interrupt'
    | 'play_track'
    | 'stop_track'
    | 'play_filler'
    | 'play_rescue_wait'
    | 'play_rescue_end'
    | 'mode_switch'
    | 'session_start'
    | 'session_end'
    | 'send_prompt_template'
    | 'send_story_prompt'
  /** 相關資料 */
  data?: Record<string, unknown>
}

/**
 * Observation entry for researcher notes
 */
export interface ObservationEntry {
  /** 時間戳 (ISO 8601) */
  timestamp: string
  /** 經過時間（秒） */
  elapsedSeconds: number
  /** 觀察備註 */
  note: string
  /** 標籤 */
  tags?: string[]
}

/**
 * Session record for persistence
 */
export interface SessionRecord {
  /** Session ID (UUID) */
  id: string
  /** 開始時間 (ISO 8601) */
  startTime: string
  /** 結束時間 (ISO 8601) */
  endTime: string | null
  /** 總持續時間（秒） */
  durationSeconds: number
  /** 操作紀錄 */
  operationLogs: OperationLog[]
  /** 觀察紀錄 */
  observations: ObservationEntry[]
  /** 模式切換次數 */
  modeSwitchCount: number
  /** AI 互動次數 */
  aiInteractionCount: number
}

// =============================================================================
// Settings Types
// =============================================================================

/**
 * DJ Controller settings
 */
export interface DJSettings {
  /** 預設會話時間（秒），預設 30 分鐘 (1800 秒) */
  sessionTimeLimit: number
  /** 警告時間（秒），預設 25 分鐘 (1500 秒) */
  timeWarningAt: number
  /** 強制送出時自動播放思考音效 */
  autoPlayFillerOnSubmit: boolean
  /** AI 回應超時警告（秒） */
  aiResponseTimeout: number
  /** 熱鍵配置 */
  hotkeys: Record<string, string>
  /** Gemini System Prompt (兒童友善) */
  childFriendlyPrompt: string
}

// =============================================================================
// Store State Types
// =============================================================================

/**
 * Operation priority levels (EC-002)
 * Lower number = higher priority
 */
export enum OperationPriority {
  INTERRUPT = 1,
  EMERGENCY_END = 2,
  FORCE_SUBMIT = 3,
  PLAYBACK = 4,
}

/**
 * Pending operation for priority queue
 */
export interface PendingOperation {
  type: 'interrupt' | 'emergency_end' | 'force_submit' | 'playback'
  priority: OperationPriority
  timestamp: number
  trackId?: string
}

/**
 * Preset summary (from backend)
 * Feature: 011-magic-dj-audio-features Phase 3
 */
export interface PresetSummary {
  id: string
  name: string
  description: string | null
  is_default: boolean
  created_at: string
  updated_at: string
}

/**
 * Magic DJ Store state
 */
export interface MagicDJState {
  // === 音軌管理 (Sound Library) ===
  tracks: Track[]
  trackStates: Record<string, TrackPlaybackState>
  masterVolume: number

  // === 頻道佇列 (DD-001: 4-Channel Layout) ===
  channelQueues: Record<ChannelType, ChannelQueueItem[]>
  channelStates: Record<ChannelType, ChannelState>

  // === 操作模式 ===
  currentMode: OperationMode
  isAIConnected: boolean

  // === 計時器 ===
  isSessionActive: boolean
  sessionStartTime: number | null
  elapsedTime: number

  // === AI 回應計時 ===
  aiRequestTime: number | null
  isWaitingForAI: boolean

  // === 設定 ===
  settings: DJSettings

  // === Session 資料 ===
  currentSession: SessionRecord | null

  // === Operation Priority Queue (EC-002) ===
  pendingOperations: PendingOperation[]
  lastOperationTime: number

  // === Cue List (US3: FR-028~FR-037) ===
  cueList: CueList

  // === AI Prompt Templates (015) ===
  /** Available prompt templates (ordered) */
  promptTemplates: PromptTemplate[]
  /** Available story prompts (ordered) */
  storyPrompts: StoryPrompt[]
  /** Last sent prompt template ID (for visual feedback) */
  lastSentPromptId: string | null
  /** Timestamp of last sent prompt */
  lastSentPromptTime: number | null

  // === Backend Sync (011 Phase 3) ===
  /** Current preset ID (null = localStorage mode) */
  currentPresetId: string | null
  /** Available presets from backend */
  presets: PresetSummary[]
  /** Loading state for async operations */
  isLoading: boolean
  /** Syncing state for background sync */
  isSyncing: boolean
  /** Last sync error */
  syncError: string | null
  /** Whether user is authenticated (can use backend) */
  isAuthenticated: boolean
}

// =============================================================================
// Default Values
// =============================================================================

/**
 * Default tracks - no audio files by default.
 * Users should generate audio via TTS for each track.
 * textContent provides suggested text for TTS generation.
 */
export const DEFAULT_TRACKS: Track[] = [
  {
    id: 'track_01_intro',
    name: '開場',
    type: 'intro',
    url: '',
    textContent: '嗨！歡迎來到魔法世界！今天我們要一起探險喔！',
    source: 'tts',
    volume: 1.0,
  },
  {
    id: 'track_02_cleanup',
    name: '收玩具歌',
    type: 'song',
    url: '',
    textContent: '收玩具、收玩具，大家一起來收玩具！',
    source: 'tts',
    volume: 1.0,
  },
  {
    id: 'track_03_success',
    name: '成功獎勵',
    type: 'effect',
    url: '',
    textContent: '太棒了！你做得很好！',
    source: 'tts',
    volume: 1.0,
  },
  {
    id: 'track_04_book',
    name: '魔法書過場',
    type: 'transition',
    url: '',
    textContent: '讓我們翻開魔法書，看看裡面有什麼故事...',
    source: 'tts',
    volume: 1.0,
  },
  {
    id: 'track_05_forest',
    name: '迷霧森林',
    type: 'transition',
    url: '',
    textContent: '我們來到了神秘的迷霧森林...',
    source: 'tts',
    volume: 1.0,
  },
  {
    id: 'sound_thinking',
    name: '思考音效',
    type: 'filler',
    url: '',
    textContent: '嗯...讓我想一想...',
    source: 'tts',
    volume: 1.0,
  },
  {
    id: 'filler_wait',
    name: '等待填補',
    type: 'rescue',
    url: '',
    textContent: '等我一下下喔，我正在準備一些很棒的東西！',
    source: 'tts',
    volume: 1.0,
  },
  {
    id: 'track_end',
    name: '緊急結束',
    type: 'rescue',
    url: '',
    textContent: '好的，今天的冒險就到這裡！下次再見囉！',
    source: 'tts',
    volume: 1.0,
  },
]

export const DEFAULT_HOTKEYS: Record<string, string> = {
  // 控制
  forceSubmit: ' ', // 空白鍵 - 強制送出
  interrupt: 'Escape', // ESC - 中斷 AI
  toggleMode: 'm', // M - 切換模式

  // 音效
  fillerSound: 'f', // F - 思考音效
  rescueWait: 'w', // W - 等待填補
  rescueEnd: 'e', // E - 緊急結束

  // 音軌
  track1: '1',
  track2: '2',
  track3: '3',
  track4: '4',
  track5: '5',
}

export const DEFAULT_CHILD_FRIENDLY_PROMPT = `You are a friendly, curious 5-year-old monster companion.
Tone: Enthusiastic, simple vocabulary, use metaphors.
Constraint: Keep answers UNDER 3 SENTENCES.
Always end with a simple follow-up question.
Language: Traditional Chinese (Taiwan).`

export const DEFAULT_DJ_SETTINGS: DJSettings = {
  sessionTimeLimit: 1800, // 30 分鐘
  timeWarningAt: 1500, // 25 分鐘
  autoPlayFillerOnSubmit: true,
  aiResponseTimeout: 4, // 4 秒
  hotkeys: DEFAULT_HOTKEYS,
  childFriendlyPrompt: DEFAULT_CHILD_FRIENDLY_PROMPT,
}

// =============================================================================
// Channel Configuration (DD-001)
// =============================================================================

/** 4-channel configuration ordered left to right */
export const CHANNEL_CONFIGS: ChannelConfig[] = [
  {
    type: 'rescue',
    label: '救場語音',
    description: '等待填補、緊急結束等',
    acceptTypes: ['filler', 'rescue'],
  },
  {
    type: 'voice',
    label: '主語音',
    description: 'TTS 語音',
    acceptTypes: ['intro', 'transition'],
  },
  {
    type: 'sfx',
    label: '音效',
    description: '串場音效',
    acceptTypes: ['effect'],
  },
  {
    type: 'music',
    label: '音樂',
    description: '背景音樂',
    acceptTypes: ['song'],
  },
]

/** Map TrackType to its default ChannelType */
export const TRACK_TYPE_TO_CHANNEL: Record<TrackType, ChannelType> = {
  filler: 'rescue',
  rescue: 'rescue',
  intro: 'voice',
  transition: 'voice',
  effect: 'sfx',
  song: 'music',
}

/** All channel types in display order */
export const ALL_CHANNEL_TYPES: ChannelType[] = ['rescue', 'voice', 'sfx', 'music']

/** Default empty channel queues */
export const DEFAULT_CHANNEL_QUEUES: Record<ChannelType, ChannelQueueItem[]> = {
  rescue: [],
  voice: [],
  sfx: [],
  music: [],
}

/** Default channel states */
export const DEFAULT_CHANNEL_STATES: Record<ChannelType, ChannelState> = {
  rescue: { currentIndex: -1, volume: 1.0, isMuted: false },
  voice: { currentIndex: -1, volume: 1.0, isMuted: false },
  sfx: { currentIndex: -1, volume: 1.0, isMuted: false },
  music: { currentIndex: -1, volume: 1.0, isMuted: false },
}

// =============================================================================
// AI Prompt Template Types (015-magic-dj-ai-prompts)
// =============================================================================

/** Prompt template button color */
export type PromptTemplateColor =
  | 'blue'
  | 'green'
  | 'yellow'
  | 'red'
  | 'purple'
  | 'orange'
  | 'pink'
  | 'cyan'

/**
 * A clickable AI behavior control button.
 * Clicking sends the hidden `prompt` text to Gemini via WebSocket text_input.
 */
export interface PromptTemplate {
  /** Unique ID */
  id: string
  /** Display name (2-4 chars), e.g. "裝傻" */
  name: string
  /** Hidden prompt content sent to AI */
  prompt: string
  /** Button color */
  color: PromptTemplateColor
  /** Optional lucide icon name */
  icon?: string
  /** Sort order (lower = first) */
  order: number
  /** Default templates can be edited but not deleted */
  isDefault: boolean
  /** Created timestamp (ISO 8601) */
  createdAt: string
}

/**
 * A story prompt template for guiding AI into specific story scenarios.
 */
export interface StoryPrompt {
  /** Unique ID */
  id: string
  /** Display name, e.g. "魔法森林" */
  name: string
  /** Full story instruction prompt */
  prompt: string
  /** Category, e.g. "adventure" */
  category: string
  /** Optional lucide icon name */
  icon?: string
  /** Sort order */
  order: number
  /** Whether this is a built-in prompt */
  isDefault: boolean
}

// =============================================================================
// Default Prompt Templates (015)
// =============================================================================

export const DEFAULT_PROMPT_TEMPLATES: PromptTemplate[] = [
  {
    id: 'pt_01_play_dumb',
    name: '裝傻',
    prompt:
      '假裝你沒聽到剛才的問題，用可愛的方式岔開話題，不要直接回答。可以說「咦？我剛剛在想一個好玩的事情！」',
    color: 'blue',
    icon: 'smile',
    order: 1,
    isDefault: true,
    createdAt: '2026-02-04T00:00:00Z',
  },
  {
    id: 'pt_02_change_topic',
    name: '轉移話題',
    prompt:
      '自然地轉移話題到一個有趣的新話題，比如問小朋友喜歡什麼動物或顏色。不要提到之前的話題。',
    color: 'blue',
    icon: 'shuffle',
    order: 2,
    isDefault: true,
    createdAt: '2026-02-04T00:00:00Z',
  },
  {
    id: 'pt_03_encourage',
    name: '鼓勵',
    prompt: '用非常熱情和鼓勵的語氣讚美小朋友，告訴他做得很棒！可以拍手、歡呼。',
    color: 'green',
    icon: 'thumbs-up',
    order: 3,
    isDefault: true,
    createdAt: '2026-02-04T00:00:00Z',
  },
  {
    id: 'pt_04_wait',
    name: '等一下',
    prompt:
      '告訴小朋友你需要想一想，請他等一下。可以建議他先數到十或唱一首歌。語氣要輕鬆有趣。',
    color: 'yellow',
    icon: 'clock',
    order: 4,
    isDefault: true,
    createdAt: '2026-02-04T00:00:00Z',
  },
  {
    id: 'pt_05_end_story',
    name: '結束故事',
    prompt:
      '開始收尾這個故事，用一個溫馨快樂的結局。然後跟小朋友說今天的冒險結束了，下次再見！',
    color: 'red',
    icon: 'flag',
    order: 5,
    isDefault: true,
    createdAt: '2026-02-04T00:00:00Z',
  },
  {
    id: 'pt_06_back_to_topic',
    name: '回到主題',
    prompt:
      '把對話帶回我們正在進行的故事或活動，自然地引導回來。可以說「對了！我們剛才說到哪裡了？」',
    color: 'purple',
    icon: 'undo',
    order: 6,
    isDefault: true,
    createdAt: '2026-02-04T00:00:00Z',
  },
  {
    id: 'pt_07_short_answer',
    name: '簡短回答',
    prompt: '接下來的回覆請用一到兩句話就好，不要說太長。保持簡潔有力。',
    color: 'purple',
    icon: 'minus',
    order: 7,
    isDefault: true,
    createdAt: '2026-02-04T00:00:00Z',
  },
  {
    id: 'pt_08_ask_more',
    name: '多問問題',
    prompt:
      '多問小朋友問題，引導他多說話。表現出對他說的話很有興趣，用「真的嗎？」「然後呢？」「你覺得呢？」這類的回應。',
    color: 'green',
    icon: 'help-circle',
    order: 8,
    isDefault: true,
    createdAt: '2026-02-04T00:00:00Z',
  },
]

export const DEFAULT_STORY_PROMPTS: StoryPrompt[] = [
  {
    id: 'sp_01_magic_forest',
    name: '魔法森林',
    prompt:
      '現在開始一個魔法森林的故事。你帶著小朋友走進一座神奇的森林，裡面有會說話的大樹、調皮的精靈和友善的動物。用生動的描述讓小朋友感受到森林的神奇。問小朋友他想先去哪裡探險。',
    category: 'adventure',
    icon: 'trees',
    order: 1,
    isDefault: true,
  },
  {
    id: 'sp_02_ocean',
    name: '海底冒險',
    prompt:
      '現在開始一個海底冒險的故事。你和小朋友一起潛入美麗的海底世界，遇到各種海洋生物：彩色的魚、大海龜、可愛的海豚。有一個神秘的寶箱藏在珊瑚礁裡。引導小朋友一起尋找寶藏。',
    category: 'adventure',
    icon: 'waves',
    order: 2,
    isDefault: true,
  },
  {
    id: 'sp_03_space',
    name: '太空旅行',
    prompt:
      '現在開始一個太空旅行的故事。你和小朋友搭乘太空船出發，要去拜訪不同的星球。每個星球都有特別的東西：糖果星球、彩虹星球、動物星球。問小朋友想先去哪個星球。',
    category: 'adventure',
    icon: 'rocket',
    order: 3,
    isDefault: true,
  },
  {
    id: 'sp_04_animal_sports',
    name: '動物運動會',
    prompt:
      '現在開始一個動物運動會的故事。森林裡的動物們要舉辦運動會！有兔子跑步、大象舉重、猴子爬樹。但是裁判生病了，需要小朋友來幫忙當裁判。引導小朋友參與判斷比賽結果。',
    category: 'activity',
    icon: 'trophy',
    order: 4,
    isDefault: true,
  },
]

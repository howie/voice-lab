/**
 * Magic DJ Controller Types
 * Feature: 010-magic-dj-controller
 *
 * T003: TypeScript types and interfaces for Magic DJ module.
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

/**
 * Track configuration
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
}

/**
 * Track playback state
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
 * Magic DJ Store state
 */
export interface MagicDJState {
  // === 音軌管理 ===
  tracks: Track[]
  trackStates: Record<string, TrackPlaybackState>
  masterVolume: number

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
}

// =============================================================================
// Default Values
// =============================================================================

export const DEFAULT_TRACKS: Track[] = [
  {
    id: 'track_01_intro',
    name: '開場',
    type: 'intro',
    url: '/audio/intro.mp3',
    hotkey: '1',
  },
  {
    id: 'track_02_cleanup',
    name: '收玩具歌',
    type: 'song',
    url: '/audio/cleanup.mp3',
    hotkey: '2',
  },
  {
    id: 'track_03_success',
    name: '成功獎勵',
    type: 'effect',
    url: '/audio/success.mp3',
    hotkey: '3',
  },
  {
    id: 'track_04_book',
    name: '魔法書過場',
    type: 'transition',
    url: '/audio/book.mp3',
    hotkey: '4',
  },
  {
    id: 'track_05_forest',
    name: '迷霧森林',
    type: 'transition',
    url: '/audio/forest.mp3',
    hotkey: '5',
  },
  {
    id: 'sound_thinking',
    name: '思考音效',
    type: 'filler',
    url: '/audio/thinking.mp3',
    hotkey: 'f',
  },
  {
    id: 'filler_wait',
    name: '等待填補',
    type: 'rescue',
    url: '/audio/wait.mp3',
    hotkey: 'w',
  },
  {
    id: 'track_end',
    name: '緊急結束',
    type: 'rescue',
    url: '/audio/end.mp3',
    hotkey: 'e',
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

# Data Model: Magic DJ AI Prompt Templates

**Feature**: 015-magic-dj-ai-prompts
**Date**: 2026-02-04

## Entities

### PromptTemplate

代表一個可點擊的 AI 行為控制按鈕。RD 按下後，hidden prompt 透過 WebSocket `text_input` 發送給 Gemini。

```typescript
interface PromptTemplate {
  /** Unique ID (UUID) */
  id: string
  /** 顯示名稱（2-4 字）, e.g. "裝傻" */
  name: string
  /** 隱藏的完整 prompt 內容，發送給 AI */
  prompt: string
  /** 按鈕顏色 (tailwind color name), e.g. "blue", "red", "green" */
  color: PromptTemplateColor
  /** 可選圖示 (lucide icon name), e.g. "smile", "shield" */
  icon?: string
  /** 排序順序 (lower = first) */
  order: number
  /** 是否為預設 template（預設 template 可編輯但不可刪除） */
  isDefault: boolean
  /** 建立時間 (ISO 8601) */
  createdAt: string
}
```

**Validation Rules**:
- `name`: 1-20 characters, non-empty
- `prompt`: 1-500 characters, non-empty
- `color`: Must be one of predefined `PromptTemplateColor` values
- `order`: Non-negative integer

**State Transitions**: N/A (stateless entity)

### StoryPrompt

代表一個預設的故事模板，用於引導 AI 進入特定場景。

```typescript
interface StoryPrompt {
  /** Unique ID (UUID) */
  id: string
  /** 顯示名稱, e.g. "魔法森林" */
  name: string
  /** 完整故事指令 prompt */
  prompt: string
  /** 分類, e.g. "adventure", "fantasy" */
  category: string
  /** 可選圖示 */
  icon?: string
  /** 排序順序 */
  order: number
  /** 是否為預設 */
  isDefault: boolean
}
```

**Validation Rules**:
- `name`: 1-30 characters, non-empty
- `prompt`: 1-2000 characters, non-empty
- `category`: 1-50 characters

### PromptTemplateColor (Enum)

```typescript
type PromptTemplateColor =
  | 'blue'    // 資訊/中性指令 (裝傻、轉移話題)
  | 'green'   // 正面/鼓勵指令 (鼓勵、多問問題)
  | 'yellow'  // 暫停/等待指令 (等一下)
  | 'red'     // 結束/緊急指令 (結束故事)
  | 'purple'  // 控制/引導指令 (回到主題、簡短回答)
  | 'orange'  // 自訂指令預設色
  | 'pink'    // 自訂指令備選色
  | 'cyan'    // 自訂指令備選色
```

## Store State Extension

擴展現有 `MagicDJState` (from `magic-dj.ts`):

```typescript
/** Extended state for AI prompt features */
interface MagicDJState {
  // ... existing fields from 010-magic-dj-controller ...

  // === 015: Prompt Templates ===
  /** Available prompt templates (ordered) */
  promptTemplates: PromptTemplate[]
  /** Available story prompts (ordered) */
  storyPrompts: StoryPrompt[]
  /** Last sent prompt (for visual feedback) */
  lastSentPromptId: string | null
  /** Timestamp of last sent prompt */
  lastSentPromptTime: number | null
}
```

## Store Actions Extension

```typescript
/** New actions for AI prompt features */
interface MagicDJActions {
  // ... existing actions ...

  // === 015: Prompt Template Actions ===
  /** Send a prompt template to AI via WebSocket */
  // Note: actual sending is handled in MagicDJPage via sendMessage('text_input', ...)
  setLastSentPrompt: (id: string) => void
  clearLastSentPrompt: () => void

  /** CRUD operations for prompt templates */
  addPromptTemplate: (template: Omit<PromptTemplate, 'id' | 'createdAt'>) => void
  updatePromptTemplate: (id: string, updates: Partial<PromptTemplate>) => void
  removePromptTemplate: (id: string) => void
  reorderPromptTemplates: (ids: string[]) => void

  /** CRUD operations for story prompts */
  addStoryPrompt: (prompt: Omit<StoryPrompt, 'id'>) => void
  updateStoryPrompt: (id: string, updates: Partial<StoryPrompt>) => void
  removeStoryPrompt: (id: string) => void
}
```

## Default Data

### Default Prompt Templates

```typescript
const DEFAULT_PROMPT_TEMPLATES: PromptTemplate[] = [
  {
    id: 'pt_01_play_dumb',
    name: '裝傻',
    prompt: '假裝你沒聽到剛才的問題，用可愛的方式岔開話題，不要直接回答。可以說「咦？我剛剛在想一個好玩的事情！」',
    color: 'blue',
    icon: 'smile',
    order: 1,
    isDefault: true,
  },
  {
    id: 'pt_02_change_topic',
    name: '轉移話題',
    prompt: '自然地轉移話題到一個有趣的新話題，比如問小朋友喜歡什麼動物或顏色。不要提到之前的話題。',
    color: 'blue',
    icon: 'shuffle',
    order: 2,
    isDefault: true,
  },
  {
    id: 'pt_03_encourage',
    name: '鼓勵',
    prompt: '用非常熱情和鼓勵的語氣讚美小朋友，告訴他做得很棒！可以拍手、歡呼。',
    color: 'green',
    icon: 'thumbs-up',
    order: 3,
    isDefault: true,
  },
  {
    id: 'pt_04_wait',
    name: '等一下',
    prompt: '告訴小朋友你需要想一想，請他等一下。可以建議他先數到十或唱一首歌。語氣要輕鬆有趣。',
    color: 'yellow',
    icon: 'clock',
    order: 4,
    isDefault: true,
  },
  {
    id: 'pt_05_end_story',
    name: '結束故事',
    prompt: '開始收尾這個故事，用一個溫馨快樂的結局。然後跟小朋友說今天的冒險結束了，下次再見！',
    color: 'red',
    icon: 'flag',
    order: 5,
    isDefault: true,
  },
  {
    id: 'pt_06_back_to_topic',
    name: '回到主題',
    prompt: '把對話帶回我們正在進行的故事或活動，自然地引導回來。可以說「對了！我們剛才說到哪裡了？」',
    color: 'purple',
    icon: 'undo',
    order: 6,
    isDefault: true,
  },
  {
    id: 'pt_07_short_answer',
    name: '簡短回答',
    prompt: '接下來的回覆請用一到兩句話就好，不要說太長。保持簡潔有力。',
    color: 'purple',
    icon: 'minus',
    order: 7,
    isDefault: true,
  },
  {
    id: 'pt_08_ask_more',
    name: '多問問題',
    prompt: '多問小朋友問題，引導他多說話。表現出對他說的話很有興趣，用「真的嗎？」「然後呢？」「你覺得呢？」這類的回應。',
    color: 'green',
    icon: 'help-circle',
    order: 8,
    isDefault: true,
  },
]
```

### Default Story Prompts

```typescript
const DEFAULT_STORY_PROMPTS: StoryPrompt[] = [
  {
    id: 'sp_01_magic_forest',
    name: '魔法森林',
    prompt: '現在開始一個魔法森林的故事。你帶著小朋友走進一座神奇的森林，裡面有會說話的大樹、調皮的精靈和友善的動物。用生動的描述讓小朋友感受到森林的神奇。問小朋友他想先去哪裡探險。',
    category: 'adventure',
    icon: 'trees',
    order: 1,
    isDefault: true,
  },
  {
    id: 'sp_02_ocean',
    name: '海底冒險',
    prompt: '現在開始一個海底冒險的故事。你和小朋友一起潛入美麗的海底世界，遇到各種海洋生物：彩色的魚、大海龜、可愛的海豚。有一個神秘的寶箱藏在珊瑚礁裡。引導小朋友一起尋找寶藏。',
    category: 'adventure',
    icon: 'waves',
    order: 2,
    isDefault: true,
  },
  {
    id: 'sp_03_space',
    name: '太空旅行',
    prompt: '現在開始一個太空旅行的故事。你和小朋友搭乘太空船出發，要去拜訪不同的星球。每個星球都有特別的東西：糖果星球、彩虹星球、動物星球。問小朋友想先去哪個星球。',
    category: 'adventure',
    icon: 'rocket',
    order: 3,
    isDefault: true,
  },
  {
    id: 'sp_04_animal_sports',
    name: '動物運動會',
    prompt: '現在開始一個動物運動會的故事。森林裡的動物們要舉辦運動會！有兔子跑步、大象舉重、猴子爬樹。但是裁判生病了，需要小朋友來幫忙當裁判。引導小朋友參與判斷比賽結果。',
    category: 'activity',
    icon: 'trophy',
    order: 4,
    isDefault: true,
  },
]
```

## Relationships

```
MagicDJState (store)
  ├── promptTemplates: PromptTemplate[]  (1:N, ordered by .order)
  ├── storyPrompts: StoryPrompt[]        (1:N, ordered by .order)
  ├── tracks: Track[]                    (existing, unchanged)
  └── settings: DJSettings               (existing, unchanged)

PromptTemplate → WebSocket text_input    (trigger: user click → sendMessage)
StoryPrompt    → WebSocket text_input    (trigger: user select/submit → sendMessage)
```

## Persistence

- **Storage**: localStorage via Zustand `persist` middleware
- **Store name**: `magic-dj-store` (existing)
- **Partialize**: Add `promptTemplates` and `storyPrompts` to persisted fields
- **Migration**: Use Zustand's `version` field to handle schema migration from pre-015 state

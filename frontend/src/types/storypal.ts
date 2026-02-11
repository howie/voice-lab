/**
 * StoryPal TypeScript types.
 * Feature: StoryPal — AI Interactive Story Companion
 *
 * Types for interactive story sessions with multi-role voice and branching narratives.
 */

// =============================================================================
// Enums and Constants
// =============================================================================

export type StoryCategory = 'fairy_tale' | 'adventure' | 'science' | 'fable' | 'daily_life'

export type StorySessionStatus = 'active' | 'paused' | 'completed'

export type StoryTurnType =
  | 'narration'
  | 'dialogue'
  | 'choice_prompt'
  | 'child_response'
  | 'question'
  | 'answer'

// WebSocket message types for story mode
export type StoryWSMessageType =
  // Client -> Server
  | 'story_configure'
  | 'story_choice'
  | 'audio_chunk'
  | 'text_input'
  | 'interrupt'
  | 'ping'
  // Server -> Client
  | 'connected'
  | 'story_segment'
  | 'choice_prompt'
  | 'scene_change'
  | 'audio'
  | 'story_end'
  | 'error'
  | 'pong'

// =============================================================================
// Character & Scene
// =============================================================================

export interface StoryCharacter {
  name: string
  description: string
  voice_provider: string
  voice_id: string
  voice_settings: Record<string, unknown>
  emotion: string
}

export interface SceneInfo {
  name: string
  description: string
  bgm_prompt: string
  mood: string
}

// =============================================================================
// Story Template
// =============================================================================

export interface StoryTemplate {
  id: string
  name: string
  description: string
  category: StoryCategory
  target_age_min: number
  target_age_max: number
  language: string
  characters: StoryCharacter[]
  scenes: SceneInfo[]
  opening_prompt: string
  system_prompt: string
  is_default: boolean
  created_at: string
  updated_at: string
}

// =============================================================================
// Story Session
// =============================================================================

export interface StoryState {
  current_position: string
  choices_made: Array<{ turn: number; choice: string }>
  memory: Record<string, unknown>
}

export interface StorySession {
  id: string
  user_id: string
  template_id: string | null
  title: string
  language: string
  status: StorySessionStatus
  story_state: StoryState
  characters_config: StoryCharacter[]
  interaction_session_id: string | null
  current_scene: string | null
  started_at: string
  ended_at: string | null
  created_at: string
  updated_at: string
}

// =============================================================================
// Story Turn
// =============================================================================

export interface StoryTurn {
  id: string
  session_id: string
  turn_number: number
  turn_type: StoryTurnType
  character_name: string | null
  content: string
  audio_path: string | null
  choice_options: string[] | null
  child_choice: string | null
  bgm_scene: string | null
  created_at: string
}

// =============================================================================
// WebSocket Messages
// =============================================================================

export interface StoryWSMessage {
  type: StoryWSMessageType
  data: Record<string, unknown>
  session_id?: string
}

export interface StoryConfigureData {
  template_id?: string
  language: string
  characters_config?: StoryCharacter[]
  custom_prompt?: string
}

export interface StorySegmentData {
  turn_type: StoryTurnType
  content: string
  character_name: string | null
  emotion: string
  scene: string | null
}

export interface ChoicePromptData {
  prompt: string
  options: string[]
  context: string
}

export interface SceneChangeData {
  scene_name: string
  description: string
  bgm_prompt: string
  mood: string
}

export interface StoryEndData {
  summary: string
  total_turns: number
  choices_made: number
}

// =============================================================================
// API Request/Response
// =============================================================================

export interface CreateStorySessionRequest {
  template_id?: string
  title?: string
  language?: string
  characters_config?: StoryCharacter[]
  custom_prompt?: string
}

export interface StorySessionResponse extends StorySession {
  turns?: StoryTurn[]
}

export interface StorySessionListParams {
  status?: StorySessionStatus
  page?: number
  page_size?: number
}

export interface StorySessionListResponse {
  sessions: StorySession[]
  total: number
  page: number
  page_size: number
}

export interface StoryTemplateListResponse {
  templates: StoryTemplate[]
  total: number
}

// =============================================================================
// Category metadata for UI display
// =============================================================================

export const STORY_CATEGORIES: Record<StoryCategory, { label: string; emoji: string; color: string }> = {
  fairy_tale: { label: '童話故事', emoji: '🧚', color: 'text-pink-500' },
  adventure: { label: '冒險探索', emoji: '🗺️', color: 'text-amber-500' },
  science: { label: '科學發現', emoji: '🔬', color: 'text-blue-500' },
  fable: { label: '寓言故事', emoji: '📖', color: 'text-green-500' },
  daily_life: { label: '生活趣事', emoji: '🏠', color: 'text-purple-500' },
}

/**
 * Scene BGM Indicator
 * Feature: StoryPal — AI Interactive Story Companion
 *
 * Shows current scene and background music status.
 */

import { Music, MapPin } from 'lucide-react'
import type { SceneChangeData } from '@/types/storypal'
import { cn } from '@/lib/utils'

interface SceneBGMIndicatorProps {
  scene: SceneChangeData | null
  bgmPlaying: boolean
}

const MOOD_EMOJI: Record<string, string> = {
  cheerful: '🌞',
  mysterious: '🌙',
  exciting: '⚡',
  peaceful: '🌸',
  suspenseful: '🔮',
  warm: '🕯️',
  adventurous: '🗺️',
}

export function SceneBGMIndicator({ scene, bgmPlaying }: SceneBGMIndicatorProps) {
  if (!scene) return null

  const moodEmoji = MOOD_EMOJI[scene.mood] ?? '🎵'

  return (
    <div className="flex items-center gap-3 rounded-lg border border-border/50 bg-card/50 px-3 py-1.5 text-xs backdrop-blur-sm">
      {/* Scene */}
      <div className="flex items-center gap-1 text-muted-foreground">
        <MapPin className="h-3 w-3" />
        <span>{scene.scene_name}</span>
        <span>{moodEmoji}</span>
      </div>

      {/* BGM Status */}
      <div className="flex items-center gap-1 text-muted-foreground">
        <Music
          className={cn(
            'h-3 w-3',
            bgmPlaying && 'animate-pulse text-primary'
          )}
        />
        <span>{bgmPlaying ? '播放中' : '靜音'}</span>
      </div>
    </div>
  )
}

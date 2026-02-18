/**
 * StoryExperiencePage - Main page for parent story experience
 * Feature: 016-story-experience-mvp
 *
 * Step-based wizard: Input → Preview → TTS
 */

import { useEffect } from 'react'

import { ContentPreview } from '@/components/story-experience/ContentPreview'
import { ParentInputForm } from '@/components/story-experience/ParentInputForm'
import { TTSPlayer } from '@/components/story-experience/TTSPlayer'
import { useStoryExperienceStore } from '@/stores/storyExperienceStore'

const STEP_LABELS = {
  input: '1. 輸入參數',
  preview: '2. 預覽內容',
  tts: '3. 音頻播放',
} as const

export function StoryExperiencePage() {
  const { currentStep, reset } = useStoryExperienceStore()

  // Clean up on unmount
  useEffect(() => {
    return () => {
      // Don't reset on unmount to preserve state during navigation
    }
  }, [])

  return (
    <div className="space-y-6 p-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">故事體驗</h1>
          <p className="text-sm text-muted-foreground">
            輸入參數讓 AI 生成專屬故事或兒歌，並轉為語音播放
          </p>
        </div>
        <button
          type="button"
          onClick={reset}
          className="rounded-md border border-input bg-background px-3 py-1.5 text-sm hover:bg-accent"
        >
          重新開始
        </button>
      </div>

      {/* Step indicator */}
      <div className="flex gap-1">
        {(Object.entries(STEP_LABELS) as [string, string][]).map(([step, label]) => (
          <div
            key={step}
            className={`flex-1 rounded-sm py-1.5 text-center text-xs font-medium ${
              step === currentStep
                ? 'bg-primary text-primary-foreground'
                : 'bg-muted text-muted-foreground'
            }`}
          >
            {label}
          </div>
        ))}
      </div>

      {/* Step content */}
      {currentStep === 'input' && <ParentInputForm />}
      {currentStep === 'preview' && <ContentPreview />}
      {currentStep === 'tts' && <TTSPlayer />}
    </div>
  )
}

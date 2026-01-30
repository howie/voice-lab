/**
 * VoiceSelector Component
 * T061: Create VoiceSelector component (dynamic voice list from API)
 * T025: Display display_name, exclude hidden, sort favorites first
 */

import { useEffect, useState } from 'react'
import { voiceCustomizationApi } from '@/lib/voiceCustomizationApi'
import type { VoiceWithCustomization } from '@/types/voice-customization'
import { Spinner } from './LoadingIndicator'

export type AgeGroup = 'child' | 'young' | 'adult' | 'senior'

// Common voice styles
export const COMMON_STYLES = [
  'news',
  'conversation',
  'cheerful',
  'narration',
  'assistant',
  'customerservice',
] as const

export type VoiceStyle = (typeof COMMON_STYLES)[number]

interface VoiceSelectorProps {
  provider: string
  language?: string
  gender?: string
  ageGroup?: AgeGroup
  style?: string
  value: string
  onChange: (voiceId: string) => void
  disabled?: boolean
  showAgeFilter?: boolean
  showStyleFilter?: boolean
}

export function VoiceSelector({
  provider,
  language,
  gender,
  ageGroup,
  style,
  value,
  onChange,
  disabled = false,
  showAgeFilter = false,
  showStyleFilter = false,
}: VoiceSelectorProps) {
  const [voices, setVoices] = useState<VoiceWithCustomization[]>([])
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [selectedAgeGroup, setSelectedAgeGroup] = useState<AgeGroup | undefined>(ageGroup)
  const [selectedStyle, setSelectedStyle] = useState<string | undefined>(style)

  // Load voices when filters change (uses /voices with customization data)
  useEffect(() => {
    const loadVoices = async () => {
      setIsLoading(true)
      setError(null)

      try {
        const response = await voiceCustomizationApi.listVoicesWithCustomizations({
          provider,
          language,
          gender: gender as 'male' | 'female' | 'neutral' | undefined,
          ageGroup: selectedAgeGroup,
          excludeHidden: true,
          limit: 500,
        })

        setVoices(response.items)
      } catch (err: unknown) {
        const message = err instanceof Error ? err.message : 'Failed to load voices'
        setError(message)
        setVoices([])
      } finally {
        setIsLoading(false)
      }
    }

    if (provider) {
      loadVoices()
    }
  }, [provider, language, gender, selectedAgeGroup, selectedStyle])

  // Auto-select first voice if current selection is invalid
  useEffect(() => {
    if (voices.length > 0 && !voices.find((v) => v.id === value)) {
      onChange(voices[0].id)
    }
  }, [voices, value, onChange])

  // Group voices by gender (favorites always first within each group)
  const groupedVoices = voices.reduce<Record<string, VoiceWithCustomization[]>>(
    (acc, voice) => {
      const genderKey = voice.gender || 'other'
      if (!acc[genderKey]) {
        acc[genderKey] = []
      }
      acc[genderKey].push(voice)
      return acc
    },
    {}
  )

  const genderLabels: Record<string, string> = {
    female: '女聲',
    male: '男聲',
    other: '其他',
  }

  const ageGroupLabels: Record<AgeGroup | 'all', string> = {
    all: '全部年齡',
    child: '兒童',
    young: '青年',
    adult: '成人',
    senior: '長者',
  }

  const styleLabels: Record<string, string> = {
    all: '全部風格',
    news: '新聞播報',
    conversation: '對話',
    cheerful: '愉快',
    narration: '旁白',
    assistant: '助手',
    customerservice: '客服',
  }

  return (
    <div className="space-y-2">
      <label className="text-sm font-medium">語音角色</label>

      {/* Filters row */}
      {(showAgeFilter || showStyleFilter) && (
        <div className="flex gap-2 flex-wrap">
          {/* Age group filter */}
          {showAgeFilter && (
            <select
              value={selectedAgeGroup || 'all'}
              onChange={(e) =>
                setSelectedAgeGroup(
                  e.target.value === 'all' ? undefined : (e.target.value as AgeGroup)
                )
              }
              disabled={disabled || isLoading}
              className="rounded-lg border bg-background p-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary disabled:cursor-not-allowed disabled:opacity-50"
            >
              <option value="all">{ageGroupLabels.all}</option>
              <option value="child">{ageGroupLabels.child}</option>
              <option value="young">{ageGroupLabels.young}</option>
              <option value="adult">{ageGroupLabels.adult}</option>
              <option value="senior">{ageGroupLabels.senior}</option>
            </select>
          )}

          {/* Style filter */}
          {showStyleFilter && (
            <select
              value={selectedStyle || 'all'}
              onChange={(e) =>
                setSelectedStyle(e.target.value === 'all' ? undefined : e.target.value)
              }
              disabled={disabled || isLoading}
              className="rounded-lg border bg-background p-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary disabled:cursor-not-allowed disabled:opacity-50"
            >
              <option value="all">{styleLabels.all}</option>
              {COMMON_STYLES.map((s) => (
                <option key={s} value={s}>
                  {styleLabels[s] || s}
                </option>
              ))}
            </select>
          )}
        </div>
      )}

      <div className="relative">
        <select
          value={value}
          onChange={(e) => onChange(e.target.value)}
          disabled={disabled || isLoading}
          className="w-full rounded-lg border bg-background p-2 pr-8 text-sm focus:outline-none focus:ring-2 focus:ring-primary disabled:cursor-not-allowed disabled:opacity-50"
        >
          {voices.length === 0 && !isLoading && (
            <option value="">選擇語音...</option>
          )}

          {Object.entries(groupedVoices).map(([genderKey, genderVoices]) => (
            <optgroup key={genderKey} label={genderLabels[genderKey] || genderKey}>
              {genderVoices.map((voice) => (
                <option key={voice.id} value={voice.id}>
                  {voice.isFavorite ? '★ ' : ''}{voice.displayName || voice.display_name}
                </option>
              ))}
            </optgroup>
          ))}
        </select>

        {isLoading && (
          <div className="absolute right-8 top-1/2 -translate-y-1/2">
            <Spinner className="h-4 w-4 text-primary" />
          </div>
        )}
      </div>

      {error && <p className="text-xs text-destructive">{error}</p>}

      {/* Voice count */}
      {!isLoading && voices.length > 0 && (
        <p className="text-xs text-muted-foreground">
          {voices.length} 個可用語音
        </p>
      )}
    </div>
  )
}

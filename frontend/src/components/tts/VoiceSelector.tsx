/**
 * VoiceSelector Component
 * T061: Create VoiceSelector component (dynamic voice list from API)
 */

import { useEffect, useState } from 'react'
import { ttsApi, VoiceProfile } from '@/lib/api'
import { Spinner } from './LoadingIndicator'

export type AgeGroup = 'child' | 'young' | 'adult' | 'senior'

interface VoiceSelectorProps {
  provider: string
  language?: string
  gender?: string
  ageGroup?: AgeGroup
  value: string
  onChange: (voiceId: string) => void
  disabled?: boolean
  showAgeFilter?: boolean
}

export function VoiceSelector({
  provider,
  language,
  gender,
  ageGroup,
  value,
  onChange,
  disabled = false,
  showAgeFilter = false,
}: VoiceSelectorProps) {
  const [voices, setVoices] = useState<VoiceProfile[]>([])
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [selectedAgeGroup, setSelectedAgeGroup] = useState<AgeGroup | undefined>(ageGroup)

  // Load voices when provider, language, gender, or ageGroup changes
  useEffect(() => {
    const loadVoices = async () => {
      setIsLoading(true)
      setError(null)

      try {
        const filters: { language?: string; gender?: string; age_group?: string } = {}
        if (language) filters.language = language
        if (gender) filters.gender = gender
        if (selectedAgeGroup) filters.age_group = selectedAgeGroup

        const response = await ttsApi.getVoices(provider, filters)
        setVoices(response.data)
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
  }, [provider, language, gender, selectedAgeGroup])

  // Auto-select first voice if current selection is invalid
  useEffect(() => {
    if (voices.length > 0 && !voices.find((v) => v.id === value)) {
      onChange(voices[0].id)
    }
  }, [voices, value, onChange])

  // Group voices by gender
  const groupedVoices = voices.reduce<Record<string, VoiceProfile[]>>(
    (acc, voice) => {
      const gender = voice.gender || 'other'
      if (!acc[gender]) {
        acc[gender] = []
      }
      acc[gender].push(voice)
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

  return (
    <div className="space-y-2">
      <label className="text-sm font-medium">語音角色</label>

      {/* Age group filter */}
      {showAgeFilter && (
        <div className="flex gap-2">
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
                  {voice.name}
                  {voice.age_group && ` (${ageGroupLabels[voice.age_group]})`}
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

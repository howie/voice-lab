/**
 * VoiceSelector Component
 * T061: Create VoiceSelector component (dynamic voice list from API)
 */

import { useEffect, useState } from 'react'
import { ttsApi, VoiceProfile } from '@/lib/api'
import { Spinner } from './LoadingIndicator'

interface VoiceSelectorProps {
  provider: string
  language?: string
  value: string
  onChange: (voiceId: string) => void
  disabled?: boolean
}

export function VoiceSelector({
  provider,
  language,
  value,
  onChange,
  disabled = false,
}: VoiceSelectorProps) {
  const [voices, setVoices] = useState<VoiceProfile[]>([])
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  // Load voices when provider or language changes
  useEffect(() => {
    const loadVoices = async () => {
      setIsLoading(true)
      setError(null)

      try {
        const response = await ttsApi.getVoices(provider, language)
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
  }, [provider, language])

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

  return (
    <div className="space-y-2">
      <label className="text-sm font-medium">語音角色</label>

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

          {Object.entries(groupedVoices).map(([gender, genderVoices]) => (
            <optgroup key={gender} label={genderLabels[gender] || gender}>
              {genderVoices.map((voice) => (
                <option key={voice.id} value={voice.id}>
                  {voice.name}
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

      {error && (
        <p className="text-xs text-destructive">{error}</p>
      )}

      {/* Voice count */}
      {!isLoading && voices.length > 0 && (
        <p className="text-xs text-muted-foreground">
          {voices.length} 個可用語音
        </p>
      )}
    </div>
  )
}

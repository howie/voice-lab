/**
 * SpeakerVoiceTable Component
 * T031: Table showing parsed speakers with voice selection dropdowns
 */

import { AlertTriangle, User } from 'lucide-react'
import type { VoiceProfile } from '@/lib/api'
import type { VoiceAssignment } from '@/types/multi-role-tts'
import { Spinner } from '@/components/tts/LoadingIndicator'

interface SpeakerVoiceTableProps {
  speakers: string[]
  voiceAssignments: VoiceAssignment[]
  voices: VoiceProfile[]
  voicesLoading: boolean
  maxSpeakers: number
  onVoiceChange: (speaker: string, voiceId: string, voiceName?: string) => void
  disabled?: boolean
}

export function SpeakerVoiceTable({
  speakers,
  voiceAssignments,
  voices,
  voicesLoading,
  maxSpeakers,
  onVoiceChange,
  disabled = false,
}: SpeakerVoiceTableProps) {
  const exceedsLimit = speakers.length > maxSpeakers

  // Get current voice assignment for a speaker
  const getVoiceId = (speaker: string): string => {
    const assignment = voiceAssignments.find((va) => va.speaker === speaker)
    return assignment?.voiceId || ''
  }

  // Group voices by gender for better UX
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

  if (speakers.length === 0) {
    return (
      <div className="rounded-lg border border-dashed p-6 text-center">
        <User className="mx-auto h-8 w-8 text-muted-foreground" />
        <p className="mt-2 text-sm text-muted-foreground">
          解析對話後，說話者會顯示在這裡
        </p>
      </div>
    )
  }

  return (
    <div className="space-y-3">
      {/* Limit warning */}
      {exceedsLimit && (
        <div className="flex items-start gap-2 rounded-lg border border-destructive bg-destructive/10 p-3">
          <AlertTriangle className="mt-0.5 h-4 w-4 flex-shrink-0 text-destructive" />
          <div className="text-xs text-destructive">
            <p className="font-medium">說話者數量超過限制</p>
            <p>
              目前有 {speakers.length} 位說話者，但此 Provider 最多支援{' '}
              {maxSpeakers} 位
            </p>
          </div>
        </div>
      )}

      {/* Table */}
      <div className="overflow-hidden rounded-lg border">
        <table className="w-full">
          <thead className="bg-muted/50">
            <tr>
              <th className="px-4 py-2 text-left text-xs font-medium text-muted-foreground">
                說話者
              </th>
              <th className="px-4 py-2 text-left text-xs font-medium text-muted-foreground">
                語音
              </th>
            </tr>
          </thead>
          <tbody className="divide-y">
            {speakers.map((speaker) => (
              <tr
                key={speaker}
                className="transition-colors hover:bg-muted/30"
              >
                <td className="px-4 py-3">
                  <div className="flex items-center gap-2">
                    <div className="flex h-7 w-7 items-center justify-center rounded-full bg-primary/10 text-xs font-medium text-primary">
                      {speaker.charAt(0).toUpperCase()}
                    </div>
                    <span className="text-sm font-medium">{speaker}</span>
                  </div>
                </td>
                <td className="px-4 py-3">
                  <div className="relative">
                    <select
                      value={getVoiceId(speaker)}
                      onChange={(e) => {
                        const voice = voices.find((v) => v.id === e.target.value)
                        onVoiceChange(speaker, e.target.value, voice?.name)
                      }}
                      disabled={disabled || voicesLoading}
                      className="w-full max-w-xs rounded-md border bg-background px-3 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-primary disabled:cursor-not-allowed disabled:opacity-50"
                    >
                      {voices.length === 0 && !voicesLoading && (
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

                    {voicesLoading && (
                      <div className="absolute right-8 top-1/2 -translate-y-1/2">
                        <Spinner className="h-4 w-4 text-primary" />
                      </div>
                    )}
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Summary */}
      <p className="text-xs text-muted-foreground">
        {speakers.length} 位說話者 · {voices.length} 個可用語音
      </p>
    </div>
  )
}

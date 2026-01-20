/**
 * ProviderCapabilityCard Component
 * T032: Display provider multi-role capabilities with support type indicators
 */

import {
  CheckCircle2,
  AlertTriangle,
  XCircle,
  Users,
  FileText,
  Sparkles,
  Info,
} from 'lucide-react'
import type { ProviderMultiRoleCapability } from '@/types/multi-role-tts'

interface ProviderCapabilityCardProps {
  capability: ProviderMultiRoleCapability | null
  onSegmentedConfirm?: () => void
}

// ElevenLabs Audio Tags descriptions
const ELEVENLABS_AUDIO_TAGS: Record<string, { description: string; example: string }> = {
  interrupting: {
    description: '打斷效果 - 模擬說話被打斷的情境',
    example: '[interrupting] 等等，我還沒說完...',
  },
  overlapping: {
    description: '重疊說話 - 多人同時發言',
    example: '[overlapping] 對對對',
  },
  laughs: {
    description: '笑聲 - 自然的笑聲效果',
    example: '[laughs] 那真的太好笑了',
  },
  sighs: {
    description: '嘆氣 - 表達情緒的嘆息聲',
    example: '[sighs] 好吧，我知道了',
  },
  whispers: {
    description: '耳語 - 低聲說話效果',
    example: '[whispers] 噓，別讓他們聽到',
  },
}

export function ProviderCapabilityCard({
  capability,
  onSegmentedConfirm,
}: ProviderCapabilityCardProps) {
  if (!capability) {
    return (
      <div className="rounded-lg border border-dashed p-4 text-center">
        <p className="text-sm text-muted-foreground">選擇 Provider 以查看功能</p>
      </div>
    )
  }

  const { supportType, maxSpeakers, characterLimit, advancedFeatures, notes } =
    capability

  // Support type indicator
  const supportIndicator = {
    native: {
      icon: CheckCircle2,
      label: '原生支援',
      description: '直接支援多角色合成，單次請求產生完整音訊',
      className: 'bg-green-50 border-green-200 text-green-800',
      iconClass: 'text-green-600',
    },
    segmented: {
      icon: AlertTriangle,
      label: '分段合併',
      description: '需分別合成每段對話後合併，可能略有延遲',
      className: 'bg-yellow-50 border-yellow-200 text-yellow-800',
      iconClass: 'text-yellow-600',
    },
    unsupported: {
      icon: XCircle,
      label: '不支援',
      description: '此 Provider 不支援多角色語音合成',
      className: 'bg-red-50 border-red-200 text-red-800',
      iconClass: 'text-red-600',
    },
  }[supportType]

  const SupportIcon = supportIndicator.icon

  return (
    <div className="space-y-4 rounded-lg border bg-card p-4">
      {/* Support type banner */}
      <div
        className={`flex items-start gap-3 rounded-md border p-3 ${supportIndicator.className}`}
      >
        <SupportIcon className={`mt-0.5 h-5 w-5 flex-shrink-0 ${supportIndicator.iconClass}`} />
        <div>
          <p className="font-medium">{supportIndicator.label}</p>
          <p className="text-xs opacity-80">{supportIndicator.description}</p>
        </div>
      </div>

      {/* Segmented mode confirmation */}
      {supportType === 'segmented' && onSegmentedConfirm && (
        <button
          onClick={onSegmentedConfirm}
          className="w-full rounded-md bg-yellow-100 px-3 py-2 text-xs text-yellow-800 hover:bg-yellow-200 transition-colors"
        >
          了解分段合併模式會有額外處理時間，繼續使用
        </button>
      )}

      {/* Capabilities grid */}
      <div className="grid gap-3 sm:grid-cols-2">
        {/* Max speakers */}
        <div className="flex items-center gap-2 rounded-md bg-muted/50 p-2">
          <Users className="h-4 w-4 text-muted-foreground" />
          <div>
            <p className="text-xs text-muted-foreground">最多說話者</p>
            <p className="text-sm font-medium">{maxSpeakers} 位</p>
          </div>
        </div>

        {/* Character limit */}
        <div className="flex items-center gap-2 rounded-md bg-muted/50 p-2">
          <FileText className="h-4 w-4 text-muted-foreground" />
          <div>
            <p className="text-xs text-muted-foreground">字數上限</p>
            <p className="text-sm font-medium">
              {characterLimit.toLocaleString()} 字
            </p>
          </div>
        </div>
      </div>

      {/* Advanced features */}
      {advancedFeatures.length > 0 && (
        <div>
          <div className="mb-2 flex items-center gap-1">
            <Sparkles className="h-4 w-4 text-primary" />
            <span className="text-xs font-medium">進階功能</span>
          </div>
          <div className="flex flex-wrap gap-2">
            {advancedFeatures.map((feature) => (
              <div
                key={feature}
                className="group relative rounded-full bg-primary/10 px-2.5 py-1 text-xs text-primary cursor-help transition-colors hover:bg-primary/20"
              >
                {feature}
                {/* Enhanced Tooltip for ElevenLabs Audio Tags */}
                {ELEVENLABS_AUDIO_TAGS[feature] && (
                  <div className="absolute bottom-full left-1/2 z-10 mb-2 hidden -translate-x-1/2 rounded-lg bg-foreground px-3 py-2 text-xs text-background shadow-lg group-hover:block w-56">
                    <p className="font-medium mb-1">{ELEVENLABS_AUDIO_TAGS[feature].description}</p>
                    <p className="text-[10px] opacity-70 font-mono">
                      範例: {ELEVENLABS_AUDIO_TAGS[feature].example}
                    </p>
                    <div className="absolute left-1/2 top-full -translate-x-1/2 border-4 border-transparent border-t-foreground" />
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Notes */}
      {notes && (
        <div className="flex items-start gap-2 rounded-md bg-muted/30 p-2">
          <Info className="mt-0.5 h-4 w-4 flex-shrink-0 text-muted-foreground" />
          <p className="text-xs text-muted-foreground">{notes}</p>
        </div>
      )}
    </div>
  )
}

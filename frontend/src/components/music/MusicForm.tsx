/**
 * Music Generation Form Component
 * Feature: 012-music-generation
 *
 * Form for submitting music generation requests.
 */

import { useState } from 'react'
import { Music, FileText, Mic2, Loader2, AlertCircle } from 'lucide-react'
import { useMusicStore, selectCanSubmit } from '@/stores/musicStore'
import type { MusicGenerationType, MusicModel } from '@/types/music'
import { MUSIC_TYPE_LABELS, MUSIC_MODEL_LABELS } from '@/types/music'

// Type configs
const TYPE_CONFIG: Record<MusicGenerationType, { icon: typeof Music; description: string }> = {
  instrumental: {
    icon: Music,
    description: '根據場景/風格描述生成純音樂/背景音樂',
  },
  song: {
    icon: Mic2,
    description: '根據歌詞和風格描述生成完整歌曲（含人聲）',
  },
  lyrics: {
    icon: FileText,
    description: '根據主題描述生成結構化歌詞',
  },
}

export function MusicForm() {
  const {
    formType,
    formPrompt,
    formLyrics,
    formModel,
    isSubmitting,
    error,
    quota,
    setFormType,
    setFormPrompt,
    setFormLyrics,
    setFormModel,
    submitInstrumental,
    submitSong,
    submitLyrics,
    clearError,
    resetForm,
  } = useMusicStore()

  const canSubmit = useMusicStore(selectCanSubmit)
  const [validationError, setValidationError] = useState<string | null>(null)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setValidationError(null)

    // Validation
    if (formType === 'instrumental') {
      if (formPrompt.length < 10) {
        setValidationError('場景描述至少需要 10 個字元')
        return
      }
      await submitInstrumental(formPrompt, formModel)
    } else if (formType === 'song') {
      if (!formPrompt && !formLyrics) {
        setValidationError('請至少提供風格描述或歌詞')
        return
      }
      await submitSong(formPrompt || undefined, formLyrics || undefined, formModel)
    } else if (formType === 'lyrics') {
      if (formPrompt.length < 2) {
        setValidationError('主題描述至少需要 2 個字元')
        return
      }
      await submitLyrics(formPrompt)
    }

    // Reset form after successful submission
    resetForm()
  }

  const TypeIcon = TYPE_CONFIG[formType].icon

  return (
    <div className="space-y-6">
      {/* Type selector */}
      <div>
        <label className="mb-2 block text-sm font-medium">生成類型</label>
        <div className="grid grid-cols-3 gap-2">
          {(Object.keys(TYPE_CONFIG) as MusicGenerationType[]).map((type) => {
            const config = TYPE_CONFIG[type]
            const Icon = config.icon
            return (
              <button
                key={type}
                type="button"
                onClick={() => setFormType(type)}
                className={`flex flex-col items-center gap-2 rounded-lg border p-4 transition-colors ${
                  formType === type
                    ? 'border-primary bg-primary/5'
                    : 'border-muted hover:border-primary/50'
                }`}
              >
                <Icon className="h-6 w-6" />
                <span className="text-sm font-medium">{MUSIC_TYPE_LABELS[type]}</span>
              </button>
            )
          })}
        </div>
        <p className="mt-2 text-sm text-muted-foreground">{TYPE_CONFIG[formType].description}</p>
      </div>

      <form onSubmit={handleSubmit} className="space-y-4">
        {/* Prompt input */}
        <div>
          <label className="mb-2 block text-sm font-medium">
            {formType === 'lyrics' ? '主題描述' : '場景/風格描述'}
            {formType !== 'song' && <span className="text-red-500"> *</span>}
          </label>
          <textarea
            value={formPrompt}
            onChange={(e) => setFormPrompt(e.target.value)}
            placeholder={
              formType === 'instrumental'
                ? '例如：magical fantasy forest, whimsical, children friendly'
                : formType === 'song'
                  ? '例如：pop, cheerful, children, chinese, female vocal'
                  : '例如：太空探險、友誼、成長'
            }
            className="min-h-[100px] w-full rounded-lg border bg-background p-3 text-sm focus:border-primary focus:outline-none focus:ring-1 focus:ring-primary"
            maxLength={formType === 'lyrics' ? 200 : 500}
          />
          <div className="mt-1 flex justify-between text-xs text-muted-foreground">
            <span>
              {formType === 'instrumental' ? '最少 10 字' : formType === 'lyrics' ? '最少 2 字' : '選填'}
            </span>
            <span>
              {formPrompt.length} / {formType === 'lyrics' ? 200 : 500}
            </span>
          </div>
        </div>

        {/* Lyrics input (only for song type) */}
        {formType === 'song' && (
          <div>
            <label className="mb-2 block text-sm font-medium">歌詞內容</label>
            <textarea
              value={formLyrics}
              onChange={(e) => setFormLyrics(e.target.value)}
              placeholder="輸入歌詞內容...&#10;[Verse]&#10;第一段歌詞...&#10;&#10;[Chorus]&#10;副歌歌詞..."
              className="min-h-[200px] w-full rounded-lg border bg-background p-3 font-mono text-sm focus:border-primary focus:outline-none focus:ring-1 focus:ring-primary"
              maxLength={3000}
            />
            <div className="mt-1 flex justify-between text-xs text-muted-foreground">
              <span>選填（可與風格描述配合使用）</span>
              <span>{formLyrics.length} / 3000</span>
            </div>
          </div>
        )}

        {/* Model selector (only for instrumental and song) */}
        {formType !== 'lyrics' && (
          <div>
            <label className="mb-2 block text-sm font-medium">模型選擇</label>
            <select
              value={formModel}
              onChange={(e) => setFormModel(e.target.value as MusicModel)}
              className="w-full rounded-lg border bg-background p-3 text-sm focus:border-primary focus:outline-none focus:ring-1 focus:ring-primary"
            >
              {(Object.keys(MUSIC_MODEL_LABELS) as MusicModel[]).map((model) => (
                <option key={model} value={model}>
                  {MUSIC_MODEL_LABELS[model]}
                </option>
              ))}
            </select>
          </div>
        )}

        {/* Error display */}
        {(error || validationError) && (
          <div className="flex items-center gap-2 rounded-lg bg-red-50 p-3 text-sm text-red-700 dark:bg-red-900/20 dark:text-red-400">
            <AlertCircle className="h-4 w-4 shrink-0" />
            <span>{validationError || error}</span>
            <button
              type="button"
              onClick={() => {
                setValidationError(null)
                clearError()
              }}
              className="ml-auto text-red-900 hover:underline dark:text-red-300"
            >
              關閉
            </button>
          </div>
        )}

        {/* Quota warning */}
        {quota && !quota.can_submit && (
          <div className="flex items-center gap-2 rounded-lg bg-yellow-50 p-3 text-sm text-yellow-700 dark:bg-yellow-900/20 dark:text-yellow-400">
            <AlertCircle className="h-4 w-4 shrink-0" />
            <span>
              {quota.concurrent_jobs >= quota.max_concurrent_jobs
                ? `已達同時處理上限（${quota.max_concurrent_jobs}），請等待現有任務完成`
                : quota.daily_used >= quota.daily_limit
                  ? `今日配額已用完（${quota.daily_limit}），請明天再試`
                  : `本月配額已用完（${quota.monthly_limit}），請聯繫管理員`}
            </span>
          </div>
        )}

        {/* Submit button */}
        <button
          type="submit"
          disabled={isSubmitting || !canSubmit}
          className="flex w-full items-center justify-center gap-2 rounded-lg bg-primary px-4 py-3 font-medium text-primary-foreground transition-colors hover:bg-primary/90 disabled:cursor-not-allowed disabled:opacity-50"
        >
          {isSubmitting ? (
            <>
              <Loader2 className="h-5 w-5 animate-spin" />
              提交中...
            </>
          ) : (
            <>
              <TypeIcon className="h-5 w-5" />
              生成{MUSIC_TYPE_LABELS[formType]}
            </>
          )}
        </button>
      </form>
    </div>
  )
}

export default MusicForm

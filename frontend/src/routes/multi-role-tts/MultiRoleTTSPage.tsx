/**
 * Multi-Role TTS Page
 * T034: Main page for multi-role dialogue text-to-speech
 */

import { useEffect, useState } from 'react'
import { Play, RotateCcw, FileText, Download, AlertTriangle, Clock, CheckCircle } from 'lucide-react'
import { useNavigate } from 'react-router-dom'
import { useMultiRoleTTSStore } from '@/stores/multiRoleTTSStore'
import { useJobStore } from '@/stores/jobStore'
import {
  DialogueInput,
  SpeakerVoiceTable,
  ProviderCapabilityCard,
  ErrorDisplay,
} from '@/components/multi-role-tts'
import { Spinner } from '@/components/tts/LoadingIndicator'
import { AudioPlayer } from '@/components/tts/AudioPlayer'
import type { MultiRoleTTSProvider } from '@/types/multi-role-tts'

const PROVIDERS: Array<{ value: MultiRoleTTSProvider; label: string }> = [
  { value: 'elevenlabs', label: 'ElevenLabs' },
  { value: 'azure', label: 'Azure' },
  { value: 'gcp', label: 'Google Cloud TTS' },
  { value: 'gemini', label: 'Gemini TTS' },
  { value: 'openai', label: 'OpenAI' },
  { value: 'cartesia', label: 'Cartesia' },
  { value: 'deepgram', label: 'Deepgram' },
  { value: 'voai', label: 'VoAI 台灣語音' },
]

export function MultiRoleTTSPage() {
  const navigate = useNavigate()
  const [jobSubmitSuccess, setJobSubmitSuccess] = useState<string | null>(null)
  const [jobSubmitError, setJobSubmitError] = useState<string | null>(null)

  const {
    dialogueText,
    setDialogueText,
    provider,
    setProvider,
    parsedTurns,
    speakers,
    voiceAssignments,
    currentCapability,
    voices,
    voicesLoading,
    result,
    audioUrl,
    isLoading,
    isParsing,
    error,
    showProviderSwitchConfirm,
    pendingProvider,
    language,
    outputFormat,
    gapMs,
    crossfadeMs,
    loadCapabilities,
    loadVoices,
    parseDialogue,
    synthesize,
    reset,
    setVoiceAssignment,
    confirmProviderSwitch,
    cancelProviderSwitch,
  } = useMultiRoleTTSStore()

  const { submitJob, isSubmitting } = useJobStore()

  // Handle background job submission
  const handleSubmitBackgroundJob = async () => {
    setJobSubmitSuccess(null)
    setJobSubmitError(null)

    try {
      const job = await submitJob({
        provider,
        turns: parsedTurns.map((turn) => ({
          speaker: turn.speaker,
          text: turn.text,
          index: turn.index,
        })),
        voice_assignments: voiceAssignments.map((va) => ({
          speaker: va.speaker,
          voice_id: va.voiceId,
        })),
        language,
        output_format: outputFormat as 'mp3' | 'wav',
        gap_ms: gapMs,
        crossfade_ms: crossfadeMs,
      })

      setJobSubmitSuccess(job.id)
    } catch (err) {
      const message = err instanceof Error ? err.message : '提交背景工作失敗'
      setJobSubmitError(message)
    }
  }

  // Load capabilities and voices on mount and provider change
  useEffect(() => {
    loadCapabilities()
  }, [loadCapabilities])

  useEffect(() => {
    loadVoices()
  }, [loadVoices, provider])

  // Handle download
  const handleDownload = () => {
    if (!audioUrl || !result) return

    const timestamp = new Date().toISOString().replace(/[:.]/g, '-')
    const filename = `multi-role-${provider}-${timestamp}.mp3`

    const link = document.createElement('a')
    link.href = audioUrl
    link.download = filename
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
  }

  const characterLimit = currentCapability?.characterLimit || 5000
  const maxSpeakers = currentCapability?.maxSpeakers || 6

  // Check if ready to synthesize
  const canSynthesize =
    parsedTurns.length > 0 &&
    speakers.every((s) =>
      voiceAssignments.some((va) => va.speaker === s && va.voiceId)
    )

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold">多角色 TTS</h1>
        <p className="mt-1 text-muted-foreground">
          輸入多角色對話逐字稿，為每位說話者指定語音，產生多角色交替說話的音訊
        </p>
      </div>

      <div className="grid gap-6 lg:grid-cols-2">
        {/* Input Panel */}
        <div className="space-y-6">
          {/* Provider Selection */}
          <div className="rounded-xl border bg-card p-6">
            <h2 className="mb-4 text-lg font-semibold">選擇 Provider</h2>

            <select
              value={provider}
              onChange={(e) => setProvider(e.target.value as MultiRoleTTSProvider)}
              disabled={isLoading}
              className="w-full rounded-lg border border-border bg-background px-4 py-2.5 text-sm font-medium transition-colors hover:border-primary focus:border-primary focus:outline-none focus:ring-2 focus:ring-primary/20 disabled:cursor-not-allowed disabled:opacity-50"
            >
              {PROVIDERS.map((p) => (
                <option key={p.value} value={p.value}>
                  {p.label}
                </option>
              ))}
            </select>

            <div className="mt-4 transition-all duration-300 ease-in-out">
              <ProviderCapabilityCard capability={currentCapability} />
            </div>
          </div>

          {/* Dialogue Input */}
          <div className="rounded-xl border bg-card p-6">
            <div className="mb-4 flex items-center justify-between">
              <h2 className="text-lg font-semibold">對話逐字稿</h2>
              <button
                onClick={() => parseDialogue()}
                disabled={isParsing || !dialogueText.trim()}
                className="flex items-center gap-1.5 rounded-md bg-primary px-3 py-1.5 text-xs font-medium text-primary-foreground hover:bg-primary/90 disabled:cursor-not-allowed disabled:opacity-50"
              >
                {isParsing ? (
                  <>
                    <Spinner className="h-3 w-3" />
                    解析中...
                  </>
                ) : (
                  <>
                    <FileText className="h-3 w-3" />
                    解析對話
                  </>
                )}
              </button>
            </div>

            <DialogueInput
              value={dialogueText}
              onChange={setDialogueText}
              characterLimit={characterLimit}
              disabled={isLoading}
              provider={provider}
            />
          </div>

          {/* Speaker Voice Assignment */}
          <div className="rounded-xl border bg-card p-6">
            <h2 className="mb-4 text-lg font-semibold">語音指定</h2>

            <SpeakerVoiceTable
              speakers={speakers}
              voiceAssignments={voiceAssignments}
              voices={voices}
              voicesLoading={voicesLoading}
              maxSpeakers={maxSpeakers}
              onVoiceChange={setVoiceAssignment}
              disabled={isLoading}
            />
          </div>
        </div>

        {/* Output Panel */}
        <div className="space-y-6">
          {/* Controls */}
          <div className="rounded-xl border bg-card p-6">
            <h2 className="mb-4 text-lg font-semibold">產生音訊</h2>

            {/* Error message with enhanced display */}
            {error && (
              <div className="mb-4">
                <ErrorDisplay
                  error={error}
                  onRetry={() => synthesize()}
                  showFormatHint={parsedTurns.length === 0}
                />
              </div>
            )}

            <div className="flex gap-3">
              <button
                onClick={() => synthesize()}
                disabled={isLoading || isSubmitting || !canSynthesize}
                className="flex flex-1 items-center justify-center gap-2 rounded-lg bg-primary py-3 text-primary-foreground hover:bg-primary/90 disabled:cursor-not-allowed disabled:opacity-50"
              >
                {isLoading ? (
                  <>
                    <Spinner className="h-4 w-4" />
                    合成中...
                  </>
                ) : (
                  <>
                    <Play className="h-4 w-4" />
                    即時合成
                  </>
                )}
              </button>

              <button
                onClick={handleSubmitBackgroundJob}
                disabled={isLoading || isSubmitting || !canSynthesize}
                className="flex flex-1 items-center justify-center gap-2 rounded-lg border border-primary py-3 text-primary hover:bg-primary/10 disabled:cursor-not-allowed disabled:opacity-50"
              >
                {isSubmitting ? (
                  <>
                    <Spinner className="h-4 w-4" />
                    提交中...
                  </>
                ) : (
                  <>
                    <Clock className="h-4 w-4" />
                    背景合成
                  </>
                )}
              </button>

              <button
                onClick={reset}
                disabled={isLoading || isSubmitting}
                className="flex items-center gap-2 rounded-lg border px-4 py-3 hover:bg-muted disabled:cursor-not-allowed disabled:opacity-50"
              >
                <RotateCcw className="h-4 w-4" />
                重置
              </button>
            </div>

            {/* Job submission success message */}
            {jobSubmitSuccess && (
              <div className="mt-3 flex items-center gap-2 rounded-lg bg-green-50 p-3 text-sm text-green-700 dark:bg-green-900/20 dark:text-green-400">
                <CheckCircle className="h-4 w-4 flex-shrink-0" />
                <span>工作已提交！</span>
                <button
                  onClick={() => navigate(`/jobs`)}
                  className="ml-auto text-xs font-medium underline hover:no-underline"
                >
                  查看工作列表
                </button>
              </div>
            )}

            {/* Job submission error message */}
            {jobSubmitError && (
              <div className="mt-3 flex items-center gap-2 rounded-lg bg-red-50 p-3 text-sm text-red-700 dark:bg-red-900/20 dark:text-red-400">
                <AlertTriangle className="h-4 w-4 flex-shrink-0" />
                <span>{jobSubmitError}</span>
              </div>
            )}

            {!canSynthesize && parsedTurns.length === 0 && (
              <p className="mt-3 text-center text-xs text-muted-foreground">
                請先輸入對話並點擊「解析對話」
              </p>
            )}

            {!canSynthesize && parsedTurns.length > 0 && (
              <p className="mt-3 text-center text-xs text-muted-foreground">
                請為所有說話者指定語音
              </p>
            )}
          </div>

          {/* Result */}
          <div className="rounded-xl border bg-card p-6">
            <h2 className="mb-4 text-lg font-semibold">輸出結果</h2>

            {/* Loading state */}
            {isLoading && (
              <div className="flex h-48 flex-col items-center justify-center rounded-lg border-2 border-dashed">
                <Spinner className="h-8 w-8 text-primary" />
                <p className="mt-3 text-sm text-muted-foreground">
                  正在合成多角色語音...
                </p>
              </div>
            )}

            {/* Empty state */}
            {!isLoading && !result && (
              <div className="flex h-48 items-center justify-center rounded-lg border-2 border-dashed">
                <p className="text-muted-foreground">產生的語音將顯示在這裡</p>
              </div>
            )}

            {/* Result state */}
            {!isLoading && result && audioUrl && (
              <div className="space-y-4">
                {/* Audio player */}
                <AudioPlayer
                  audioContent={result.audioContent || ''}
                  contentType={result.contentType}
                  duration={result.durationMs}
                />

                {/* Download button */}
                <button
                  onClick={handleDownload}
                  className="flex w-full items-center justify-center gap-2 rounded-lg border py-2 hover:bg-muted"
                >
                  <Download className="h-4 w-4" />
                  下載 MP3
                </button>

                {/* Stats */}
                <div className="space-y-2 rounded-lg bg-muted/50 p-4">
                  <div className="flex justify-between text-sm">
                    <span className="text-muted-foreground">延遲時間</span>
                    <span>{result.latencyMs} ms</span>
                  </div>
                  <div className="flex justify-between text-sm">
                    <span className="text-muted-foreground">音檔長度</span>
                    <span>{(result.durationMs / 1000).toFixed(1)} 秒</span>
                  </div>
                  <div className="flex justify-between text-sm">
                    <span className="text-muted-foreground">使用 Provider</span>
                    <span className="capitalize">{result.provider}</span>
                  </div>
                  <div className="flex justify-between text-sm">
                    <span className="text-muted-foreground">合成模式</span>
                    <span>
                      {result.synthesisMode === 'native' ? '原生' : '分段合併'}
                    </span>
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Provider Switch Confirmation Dialog */}
      {showProviderSwitchConfirm && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
          <div className="w-full max-w-md rounded-xl border bg-card p-6 shadow-lg">
            <div className="flex items-center gap-3 text-yellow-600">
              <AlertTriangle className="h-6 w-6" />
              <h3 className="text-lg font-semibold">確認切換 Provider</h3>
            </div>
            <p className="mt-4 text-sm text-muted-foreground">
              正在產生音訊中，切換到{' '}
              <span className="font-medium text-foreground">
                {PROVIDERS.find((p) => p.value === pendingProvider)?.label}
              </span>{' '}
              將取消目前的合成請求。
            </p>
            <p className="mt-2 text-sm text-muted-foreground">是否確定要切換？</p>
            <div className="mt-6 flex gap-3">
              <button
                onClick={cancelProviderSwitch}
                className="flex-1 rounded-lg border px-4 py-2 text-sm font-medium hover:bg-muted"
              >
                取消
              </button>
              <button
                onClick={confirmProviderSwitch}
                className="flex-1 rounded-lg bg-primary px-4 py-2 text-sm font-medium text-primary-foreground hover:bg-primary/90"
              >
                確定切換
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

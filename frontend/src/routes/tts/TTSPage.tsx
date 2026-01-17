/**
 * TTS Page
 * T049: Update TTSPage with all TTS components
 * T063: Update TTSPage to include all parameter controls
 */

import { useTTSStore } from '@/stores/ttsStore'
import { TextInput } from '@/components/tts/TextInput'
import { ProviderSelector } from '@/components/tts/ProviderSelector'
import { AudioPlayer } from '@/components/tts/AudioPlayer'
import { LoadingIndicator, Spinner } from '@/components/tts/LoadingIndicator'
import { SpeedSlider } from '@/components/tts/SpeedSlider'
import { PitchSlider } from '@/components/tts/PitchSlider'
import { VolumeSlider } from '@/components/tts/VolumeSlider'
import { VoiceSelector } from '@/components/tts/VoiceSelector'
import { LanguageSelector } from '@/components/tts/LanguageSelector'

export function TTSPage() {
  const {
    text,
    setText,
    provider,
    setProvider,
    voiceId,
    setVoiceId,
    language,
    setLanguage,
    speed,
    setSpeed,
    pitch,
    setPitch,
    volume,
    setVolume,
    result,
    isLoading,
    error,
    synthesize,
  } = useTTSStore()

  const handleSynthesize = async () => {
    await synthesize()
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold">TTS 測試</h1>
        <p className="mt-1 text-muted-foreground">
          輸入文字，比較各家 Text-to-Speech 服務的語音品質
        </p>
      </div>

      <div className="grid gap-6 lg:grid-cols-2">
        {/* Input Panel */}
        <div className="rounded-xl border bg-card p-6">
          <h2 className="mb-4 text-lg font-semibold">輸入文字</h2>

          <TextInput
            value={text}
            onChange={setText}
            disabled={isLoading}
          />

          <div className="mt-4 space-y-4">
            {/* Provider and Language Selection */}
            <div className="grid gap-4 sm:grid-cols-2">
              <ProviderSelector
                value={provider}
                onChange={setProvider}
                disabled={isLoading}
              />

              <LanguageSelector
                value={language}
                onChange={setLanguage}
                disabled={isLoading}
              />
            </div>

            {/* Voice Selection */}
            <VoiceSelector
              provider={provider}
              language={language}
              value={voiceId}
              onChange={setVoiceId}
              disabled={isLoading}
            />

            {/* Parameter Controls */}
            <div className="space-y-4 rounded-lg border p-4">
              <h3 className="text-sm font-medium text-muted-foreground">語音參數</h3>

              <SpeedSlider
                value={speed}
                onChange={setSpeed}
                disabled={isLoading}
              />

              <PitchSlider
                value={pitch}
                onChange={setPitch}
                disabled={isLoading}
              />

              <VolumeSlider
                value={volume}
                onChange={setVolume}
                disabled={isLoading}
              />
            </div>

            {/* Error message */}
            {error && (
              <div className="rounded-lg bg-destructive/10 p-3 text-sm text-destructive">
                {error}
              </div>
            )}

            {/* Synthesize button */}
            <button
              onClick={handleSynthesize}
              disabled={isLoading || !text.trim() || !voiceId}
              className="w-full rounded-lg bg-primary py-2 text-primary-foreground hover:bg-primary/90 disabled:cursor-not-allowed disabled:opacity-50"
            >
              {isLoading ? (
                <span className="flex items-center justify-center gap-2">
                  <Spinner className="h-4 w-4" />
                  合成中...
                </span>
              ) : (
                '產生語音'
              )}
            </button>
          </div>
        </div>

        {/* Output Panel */}
        <div className="rounded-xl border bg-card p-6">
          <h2 className="mb-4 text-lg font-semibold">輸出結果</h2>

          {/* Loading state */}
          {isLoading && (
            <LoadingIndicator
              isLoading={true}
              message="正在合成語音..."
            />
          )}

          {/* Empty state */}
          {!isLoading && !result && (
            <div className="flex h-64 items-center justify-center rounded-lg border-2 border-dashed">
              <p className="text-muted-foreground">產生的語音將顯示在這裡</p>
            </div>
          )}

          {/* Result state */}
          {!isLoading && result && (
            <div className="space-y-4">
              {/* Audio player */}
              <AudioPlayer
                audioContent={result.audio_content}
                contentType={result.content_type}
                duration={result.duration_ms}
              />

              {/* Stats */}
              <div className="space-y-2 rounded-lg bg-muted/50 p-4">
                <div className="flex justify-between text-sm">
                  <span className="text-muted-foreground">延遲時間</span>
                  <span>{result.latency_ms ?? '-'} ms</span>
                </div>
                <div className="flex justify-between text-sm">
                  <span className="text-muted-foreground">音檔長度</span>
                  <span>{((result.duration_ms || 0) / 1000).toFixed(1)} 秒</span>
                </div>
                <div className="flex justify-between text-sm">
                  <span className="text-muted-foreground">使用提供者</span>
                  <span className="capitalize">{provider}</span>
                </div>
                {result.storage_path && (
                  <div className="flex justify-between text-sm">
                    <span className="text-muted-foreground">儲存路徑</span>
                    <span className="truncate max-w-[200px]" title={result.storage_path}>
                      {result.storage_path}
                    </span>
                  </div>
                )}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

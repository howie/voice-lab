/**
 * STT Page
 * Feature: 003-stt-testing-module
 * T034: Create STTTest page
 * T043: Integrate AudioRecorder into STTTest page
 *
 * Main page for speech-to-text testing with audio upload,
 * microphone recording, provider selection, and transcription display.
 */

import { useState } from 'react'
import { useSTTStore } from '@/stores/sttStore'
import { AudioUploader } from '@/components/stt/AudioUploader'
import { AudioRecorder } from '@/components/stt/AudioRecorder'
import { ProviderSelector } from '@/components/stt/ProviderSelector'
import { TranscriptDisplay } from '@/components/stt/TranscriptDisplay'
import { WERDisplay } from '@/components/stt/WERDisplay'
import { GroundTruthInput } from '@/components/stt/GroundTruthInput'
import { SUPPORTED_LANGUAGES } from '@/types/stt'

type InputMode = 'upload' | 'record'

export function STTPage() {
  const [inputMode, setInputMode] = useState<InputMode>('upload')

  const {
    selectedProvider,
    availableProviders,
    language,
    setLanguage,
    childMode,
    setChildMode,
    groundTruth,
    setGroundTruth,
    audioFile,
    audioBlob,
    setAudioBlob,
    isRecording,
    setIsRecording,
    isTranscribing,
    transcriptionResult,
    werAnalysis,
    isCalculatingWER,
    error,
    transcribe,
    calculateErrorRate,
    clearAudio,
  } = useSTTStore()

  // Find current provider info
  const currentProvider = availableProviders.find((p) => p.name === selectedProvider)

  // Handle transcription
  const handleTranscribe = async () => {
    await transcribe()
  }

  // Handle WER calculation
  const handleCalculateWER = async () => {
    await calculateErrorRate()
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold">STT 測試</h1>
        <p className="mt-1 text-muted-foreground">
          測試各家語音辨識服務的準確度，支援檔案上傳與即時錄音
        </p>
      </div>

      <div className="grid gap-6 lg:grid-cols-2">
        {/* Input Panel */}
        <div className="space-y-6">
          {/* Provider Selection */}
          <div className="rounded-xl border bg-card p-6">
            <ProviderSelector disabled={isTranscribing} showCapabilities={true} />
          </div>

          {/* Audio Input */}
          <div className="rounded-xl border bg-card p-6">
            <h2 className="mb-4 text-lg font-semibold">音訊輸入</h2>

            {/* Input Mode Tabs */}
            <div className="mb-4 flex rounded-lg bg-muted p-1">
              <button
                onClick={() => setInputMode('upload')}
                className={`flex-1 rounded-md py-2 text-sm font-medium transition-colors ${
                  inputMode === 'upload'
                    ? 'bg-background text-foreground shadow'
                    : 'text-muted-foreground hover:text-foreground'
                }`}
              >
                <span className="flex items-center justify-center gap-2">
                  <svg
                    xmlns="http://www.w3.org/2000/svg"
                    viewBox="0 0 20 20"
                    fill="currentColor"
                    className="h-4 w-4"
                  >
                    <path d="M9.25 13.25a.75.75 0 001.5 0V4.636l2.955 3.129a.75.75 0 001.09-1.03l-4.25-4.5a.75.75 0 00-1.09 0l-4.25 4.5a.75.75 0 101.09 1.03L9.25 4.636v8.614z" />
                    <path d="M3.5 12.75a.75.75 0 00-1.5 0v2.5A2.75 2.75 0 004.75 18h10.5A2.75 2.75 0 0018 15.25v-2.5a.75.75 0 00-1.5 0v2.5c0 .69-.56 1.25-1.25 1.25H4.75c-.69 0-1.25-.56-1.25-1.25v-2.5z" />
                  </svg>
                  上傳檔案
                </span>
              </button>
              <button
                onClick={() => setInputMode('record')}
                className={`flex-1 rounded-md py-2 text-sm font-medium transition-colors ${
                  inputMode === 'record'
                    ? 'bg-background text-foreground shadow'
                    : 'text-muted-foreground hover:text-foreground'
                }`}
              >
                <span className="flex items-center justify-center gap-2">
                  <svg
                    xmlns="http://www.w3.org/2000/svg"
                    viewBox="0 0 20 20"
                    fill="currentColor"
                    className="h-4 w-4"
                  >
                    <path d="M7 4a3 3 0 016 0v6a3 3 0 11-6 0V4z" />
                    <path d="M5.5 9.643a.75.75 0 00-1.5 0V10c0 3.06 2.29 5.585 5.25 5.954V17.5h-1.5a.75.75 0 000 1.5h4.5a.75.75 0 000-1.5h-1.5v-1.546A6.001 6.001 0 0016 10v-.357a.75.75 0 00-1.5 0V10a4.5 4.5 0 01-9 0v-.357z" />
                  </svg>
                  即時錄音
                </span>
              </button>
            </div>

            {/* Input Content */}
            {inputMode === 'upload' ? (
              <AudioUploader provider={currentProvider} disabled={isTranscribing || isRecording} />
            ) : (
              <AudioRecorder
                onRecordingComplete={(blob) => {
                  setAudioBlob(blob)
                  setIsRecording(false)
                }}
                onRecordingStart={() => {
                  clearAudio()
                  setIsRecording(true)
                }}
                onRecordingStop={() => {
                  setIsRecording(false)
                }}
                onError={(err) => {
                  console.error('Recording error:', err)
                  setIsRecording(false)
                }}
                maxDuration={currentProvider?.max_duration_sec || 300}
                disabled={isTranscribing}
              />
            )}

            {/* Show recorded audio info */}
            {audioBlob && inputMode === 'record' && (
              <div className="mt-4 flex items-center justify-between rounded-lg bg-muted/50 p-3">
                <div className="flex items-center gap-2">
                  <svg
                    xmlns="http://www.w3.org/2000/svg"
                    viewBox="0 0 20 20"
                    fill="currentColor"
                    className="h-5 w-5 text-green-500"
                  >
                    <path
                      fillRule="evenodd"
                      d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.857-9.809a.75.75 0 00-1.214-.882l-3.483 4.79-1.88-1.88a.75.75 0 10-1.06 1.061l2.5 2.5a.75.75 0 001.137-.089l4-5.5z"
                      clipRule="evenodd"
                    />
                  </svg>
                  <span className="text-sm">
                    錄音完成 ({(audioBlob.size / 1024).toFixed(1)} KB)
                  </span>
                </div>
                <button
                  onClick={clearAudio}
                  className="text-sm text-red-500 hover:text-red-600"
                >
                  清除
                </button>
              </div>
            )}
          </div>

          {/* Options */}
          <div className="rounded-xl border bg-card p-6">
            <h2 className="mb-4 text-lg font-semibold">選項設定</h2>
            <div className="space-y-4">
              {/* Language Selection */}
              <div>
                <label className="mb-2 block text-sm font-medium text-gray-700 dark:text-gray-300">
                  辨識語言
                </label>
                <select
                  value={language}
                  onChange={(e) => setLanguage(e.target.value)}
                  disabled={isTranscribing}
                  className="w-full rounded-lg border bg-background p-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary disabled:opacity-50"
                >
                  {SUPPORTED_LANGUAGES.map((lang) => (
                    <option key={lang.code} value={lang.code}>
                      {lang.name}
                    </option>
                  ))}
                </select>
              </div>

              {/* Child Mode Toggle */}
              {currentProvider?.supports_child_mode && (
                <div className="flex items-center gap-3">
                  <input
                    type="checkbox"
                    id="childMode"
                    checked={childMode}
                    onChange={(e) => setChildMode(e.target.checked)}
                    disabled={isTranscribing}
                    className="h-4 w-4 rounded border-gray-300"
                  />
                  <label htmlFor="childMode" className="text-sm">
                    兒童語音模式最佳化
                  </label>
                </div>
              )}

              {/* Ground Truth Input */}
              <GroundTruthInput
                value={groundTruth}
                onChange={setGroundTruth}
                onCalculate={transcriptionResult ? handleCalculateWER : undefined}
                isCalculating={isCalculatingWER}
                disabled={isTranscribing}
                language={language}
              />
            </div>

            {/* Transcribe Button */}
            <button
              onClick={handleTranscribe}
              disabled={isTranscribing || isRecording || (!audioFile && !audioBlob)}
              className="mt-4 w-full rounded-lg bg-primary py-2 text-primary-foreground hover:bg-primary/90 disabled:cursor-not-allowed disabled:opacity-50"
            >
              {isTranscribing ? (
                <span className="flex items-center justify-center gap-2">
                  <svg
                    className="h-4 w-4 animate-spin"
                    fill="none"
                    viewBox="0 0 24 24"
                  >
                    <circle
                      className="opacity-25"
                      cx="12"
                      cy="12"
                      r="10"
                      stroke="currentColor"
                      strokeWidth="4"
                    />
                    <path
                      className="opacity-75"
                      fill="currentColor"
                      d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                    />
                  </svg>
                  辨識中...
                </span>
              ) : (
                '開始辨識'
              )}
            </button>
          </div>
        </div>

        {/* Output Panel */}
        <div className="space-y-6">
          {/* Transcription Result */}
          <div className="rounded-xl border bg-card p-6">
            <h2 className="mb-4 text-lg font-semibold">辨識結果</h2>
            <TranscriptDisplay
              result={transcriptionResult}
              isLoading={isTranscribing}
              error={error}
            />
          </div>

          {/* WER Analysis */}
          {transcriptionResult && (
            <div className="rounded-xl border bg-card p-6">
              <h2 className="mb-4 text-lg font-semibold">準確度分析</h2>
              <WERDisplay werAnalysis={werAnalysis} isCalculating={isCalculatingWER} />
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

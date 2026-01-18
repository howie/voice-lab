/**
 * STT Page
 * Feature: 003-stt-testing-module
 * T034: Create STTTest page
 *
 * Main page for speech-to-text testing with audio upload,
 * provider selection, and transcription display.
 */

import { useSTTStore } from '@/stores/sttStore'
import { AudioUploader } from '@/components/stt/AudioUploader'
import { ProviderSelector } from '@/components/stt/ProviderSelector'
import { TranscriptDisplay } from '@/components/stt/TranscriptDisplay'
import { SUPPORTED_LANGUAGES } from '@/types/stt'

export function STTPage() {
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
    isTranscribing,
    transcriptionResult,
    werAnalysis,
    isCalculatingWER,
    error,
    transcribe,
    calculateErrorRate,
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

          {/* Audio Upload */}
          <div className="rounded-xl border bg-card p-6">
            <h2 className="mb-4 text-lg font-semibold">音訊輸入</h2>
            <AudioUploader provider={currentProvider} disabled={isTranscribing} />
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
              <div>
                <label className="mb-2 block text-sm font-medium text-gray-700 dark:text-gray-300">
                  正確答案（用於計算 WER/CER）
                </label>
                <textarea
                  value={groundTruth}
                  onChange={(e) => setGroundTruth(e.target.value)}
                  placeholder="輸入正確的文字內容，將自動計算錯誤率..."
                  disabled={isTranscribing}
                  className="h-24 w-full rounded-lg border bg-background p-3 text-sm focus:outline-none focus:ring-2 focus:ring-primary disabled:opacity-50"
                />
              </div>
            </div>

            {/* Transcribe Button */}
            <button
              onClick={handleTranscribe}
              disabled={isTranscribing || !audioFile}
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

              {werAnalysis ? (
                <div className="space-y-4">
                  {/* Error Rate Display */}
                  <div className="flex items-center justify-between rounded-lg bg-muted p-4">
                    <span className="text-sm font-medium">
                      {werAnalysis.error_type === 'CER' ? '字元錯誤率 (CER)' : '字錯誤率 (WER)'}
                    </span>
                    <span
                      className={`text-2xl font-bold ${
                        werAnalysis.error_rate < 0.1
                          ? 'text-green-600 dark:text-green-400'
                          : werAnalysis.error_rate < 0.3
                            ? 'text-yellow-600 dark:text-yellow-400'
                            : 'text-red-600 dark:text-red-400'
                      }`}
                    >
                      {(werAnalysis.error_rate * 100).toFixed(1)}%
                    </span>
                  </div>

                  {/* Error Breakdown */}
                  <div className="grid grid-cols-3 gap-4">
                    <div className="rounded-lg bg-red-50 dark:bg-red-950 p-3 text-center">
                      <div className="text-lg font-semibold text-red-600 dark:text-red-400">
                        {werAnalysis.substitutions}
                      </div>
                      <div className="text-xs text-gray-500">替換</div>
                    </div>
                    <div className="rounded-lg bg-yellow-50 dark:bg-yellow-950 p-3 text-center">
                      <div className="text-lg font-semibold text-yellow-600 dark:text-yellow-400">
                        {werAnalysis.insertions}
                      </div>
                      <div className="text-xs text-gray-500">插入</div>
                    </div>
                    <div className="rounded-lg bg-orange-50 dark:bg-orange-950 p-3 text-center">
                      <div className="text-lg font-semibold text-orange-600 dark:text-orange-400">
                        {werAnalysis.deletions}
                      </div>
                      <div className="text-xs text-gray-500">刪除</div>
                    </div>
                  </div>

                  <div className="text-sm text-gray-500">
                    參考文字總數: {werAnalysis.total_reference}{' '}
                    {werAnalysis.error_type === 'CER' ? '字元' : '字'}
                  </div>
                </div>
              ) : (
                <div className="space-y-4">
                  <p className="text-sm text-gray-500">
                    {groundTruth
                      ? '點擊按鈕計算錯誤率'
                      : '請在上方輸入正確答案以計算錯誤率'}
                  </p>
                  {groundTruth && (
                    <button
                      onClick={handleCalculateWER}
                      disabled={isCalculatingWER || !groundTruth}
                      className="w-full rounded-lg border border-primary py-2 text-primary hover:bg-primary/10 disabled:cursor-not-allowed disabled:opacity-50"
                    >
                      {isCalculatingWER ? '計算中...' : '計算錯誤率'}
                    </button>
                  )}
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

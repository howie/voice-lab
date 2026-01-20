/**
 * InteractionPage Route
 * Feature: 004-interaction-module
 * T040: Main page for real-time voice interaction testing.
 *
 * Provides a dedicated page for testing voice interaction with configurable
 * modes (V2V Direct and Cascade) and providers.
 */

import { InteractionPanel } from '@/components/interaction/InteractionPanel'
import { useAuthStore } from '@/stores/authStore'

export function InteractionPage() {
  const user = useAuthStore((state) => state.user)

  // Use a default userId if not authenticated (for testing)
  const userId = user?.id || 'anonymous-user'

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div>
        <h1 className="text-2xl font-bold">即時語音互動</h1>
        <p className="mt-1 text-muted-foreground">
          測試即時語音對話 - 支援 V2V 直連模式和串接模式
        </p>
      </div>

      {/* Main Interaction Area */}
      <div className="mx-auto max-w-3xl">
        <InteractionPanel userId={userId} className="w-full" />
      </div>

      {/* Feature Description */}
      <div className="mx-auto max-w-3xl rounded-lg border bg-muted/30 p-4">
        <h3 className="mb-2 font-medium">功能說明</h3>
        <div className="space-y-2 text-sm text-muted-foreground">
          <p>
            <strong>即時模式 (V2V)：</strong>
            使用 OpenAI Realtime API 或 Gemini Live API 進行端對端語音對話，
            延遲最低但依賴特定提供者。
          </p>
          <p>
            <strong>串接模式：</strong>
            使用 STT → LLM → TTS 管線處理，可自由組合不同提供者，
            靈活性高但延遲較長。
          </p>
        </div>
      </div>
    </div>
  )
}

export default InteractionPage

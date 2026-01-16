export function InteractionPage() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold">互動測試</h1>
        <p className="mt-1 text-muted-foreground">
          測試即時語音對話的延遲、理解正確率和語音自然度
        </p>
      </div>

      <div className="grid gap-6 lg:grid-cols-3">
        {/* Config Panel */}
        <div className="rounded-xl border bg-card p-6">
          <h2 className="mb-4 text-lg font-semibold">Provider 設定</h2>

          <div className="space-y-4">
            <div>
              <label className="mb-2 block text-sm font-medium">
                STT Provider
              </label>
              <select className="w-full rounded-lg border bg-background p-2 text-sm">
                <option value="gcp">Google Cloud</option>
                <option value="azure">Azure</option>
                <option value="voai">VoAI</option>
              </select>
            </div>

            <div>
              <label className="mb-2 block text-sm font-medium">
                LLM Provider
              </label>
              <select className="w-full rounded-lg border bg-background p-2 text-sm">
                <option value="anthropic">Claude (Anthropic)</option>
                <option value="openai">GPT-4 (OpenAI)</option>
              </select>
            </div>

            <div>
              <label className="mb-2 block text-sm font-medium">
                TTS Provider
              </label>
              <select className="w-full rounded-lg border bg-background p-2 text-sm">
                <option value="azure">Azure</option>
                <option value="gcp">Google Cloud</option>
                <option value="elevenlabs">ElevenLabs</option>
                <option value="voai">VoAI</option>
              </select>
            </div>

            <div>
              <label className="mb-2 block text-sm font-medium">語音角色</label>
              <select className="w-full rounded-lg border bg-background p-2 text-sm">
                <option>zh-TW-HsiaoChenNeural</option>
              </select>
            </div>

            <div>
              <label className="mb-2 block text-sm font-medium">
                System Prompt
              </label>
              <textarea
                placeholder="設定 AI 的角色和行為..."
                className="h-24 w-full rounded-lg border bg-background p-3 text-sm"
              />
            </div>

            <button className="w-full rounded-lg bg-primary py-2 text-primary-foreground">
              開始對話
            </button>
          </div>
        </div>

        {/* Chat Panel */}
        <div className="rounded-xl border bg-card p-6 lg:col-span-2">
          <h2 className="mb-4 text-lg font-semibold">對話視窗</h2>

          <div className="flex h-96 flex-col rounded-lg border bg-background">
            <div className="flex-1 overflow-y-auto p-4">
              <div className="flex items-center justify-center h-full">
                <p className="text-muted-foreground">
                  點擊「開始對話」後，可以開始語音互動
                </p>
              </div>
            </div>

            <div className="border-t p-4">
              <div className="flex items-center justify-center gap-4">
                <button
                  disabled
                  className="flex h-12 w-12 items-center justify-center rounded-full bg-muted text-muted-foreground"
                >
                  🎤
                </button>
                <span className="text-sm text-muted-foreground">
                  按住說話
                </span>
              </div>
            </div>
          </div>

          {/* Metrics */}
          <div className="mt-4 grid grid-cols-4 gap-4">
            <div className="rounded-lg bg-muted p-3 text-center">
              <p className="text-xs text-muted-foreground">STT 延遲</p>
              <p className="text-lg font-semibold">- ms</p>
            </div>
            <div className="rounded-lg bg-muted p-3 text-center">
              <p className="text-xs text-muted-foreground">LLM 延遲</p>
              <p className="text-lg font-semibold">- ms</p>
            </div>
            <div className="rounded-lg bg-muted p-3 text-center">
              <p className="text-xs text-muted-foreground">TTS 延遲</p>
              <p className="text-lg font-semibold">- ms</p>
            </div>
            <div className="rounded-lg bg-muted p-3 text-center">
              <p className="text-xs text-muted-foreground">總延遲</p>
              <p className="text-lg font-semibold">- ms</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

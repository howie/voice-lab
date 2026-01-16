import { useState } from 'react'

export function TTSPage() {
  const [text, setText] = useState('')
  const [provider, setProvider] = useState('gcp')

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
          <textarea
            value={text}
            onChange={(e) => setText(e.target.value)}
            placeholder="請輸入要轉換成語音的文字..."
            className="h-40 w-full rounded-lg border bg-background p-3 text-sm focus:outline-none focus:ring-2 focus:ring-primary"
          />

          <div className="mt-4 space-y-4">
            <div>
              <label className="mb-2 block text-sm font-medium">
                選擇 Provider
              </label>
              <select
                value={provider}
                onChange={(e) => setProvider(e.target.value)}
                className="w-full rounded-lg border bg-background p-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary"
              >
                <option value="gcp">Google Cloud</option>
                <option value="azure">Azure</option>
                <option value="elevenlabs">ElevenLabs</option>
                <option value="voai">VoAI</option>
              </select>
            </div>

            <div>
              <label className="mb-2 block text-sm font-medium">語音角色</label>
              <select className="w-full rounded-lg border bg-background p-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary">
                <option>zh-TW-HsiaoChenNeural (女聲)</option>
                <option>zh-TW-YunJheNeural (男聲)</option>
              </select>
            </div>

            <div>
              <label className="mb-2 block text-sm font-medium">
                語速: 1.0x
              </label>
              <input
                type="range"
                min="0.5"
                max="2"
                step="0.1"
                defaultValue="1"
                className="w-full"
              />
            </div>

            <button className="w-full rounded-lg bg-primary py-2 text-primary-foreground hover:bg-primary/90">
              產生語音
            </button>
          </div>
        </div>

        {/* Output Panel */}
        <div className="rounded-xl border bg-card p-6">
          <h2 className="mb-4 text-lg font-semibold">輸出結果</h2>
          <div className="flex h-64 items-center justify-center rounded-lg border-2 border-dashed">
            <p className="text-muted-foreground">產生的語音將顯示在這裡</p>
          </div>

          <div className="mt-4 space-y-2">
            <div className="flex justify-between text-sm">
              <span className="text-muted-foreground">延遲時間</span>
              <span>- ms</span>
            </div>
            <div className="flex justify-between text-sm">
              <span className="text-muted-foreground">音檔長度</span>
              <span>- 秒</span>
            </div>
            <div className="flex justify-between text-sm">
              <span className="text-muted-foreground">預估成本</span>
              <span>$ -</span>
            </div>
          </div>

          <button
            disabled
            className="mt-4 w-full rounded-lg border py-2 text-muted-foreground"
          >
            下載音檔
          </button>
        </div>
      </div>
    </div>
  )
}

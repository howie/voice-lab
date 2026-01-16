import { useState } from 'react'
import { Mic, Upload } from 'lucide-react'

export function STTPage() {
  const [isRecording, setIsRecording] = useState(false)

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold">STT 測試</h1>
        <p className="mt-1 text-muted-foreground">
          測試各家語音辨識服務的準確度，支援即時錄音和檔案上傳
        </p>
      </div>

      <div className="grid gap-6 lg:grid-cols-2">
        {/* Input Panel */}
        <div className="rounded-xl border bg-card p-6">
          <h2 className="mb-4 text-lg font-semibold">音訊輸入</h2>

          <div className="space-y-4">
            {/* Recording */}
            <div className="flex flex-col items-center justify-center rounded-lg border-2 border-dashed p-8">
              <button
                onClick={() => setIsRecording(!isRecording)}
                className={`flex h-20 w-20 items-center justify-center rounded-full ${
                  isRecording
                    ? 'animate-pulse bg-red-500'
                    : 'bg-primary hover:bg-primary/90'
                } text-white`}
              >
                <Mic className="h-8 w-8" />
              </button>
              <p className="mt-4 text-sm text-muted-foreground">
                {isRecording ? '錄音中... 點擊停止' : '點擊開始錄音'}
              </p>
            </div>

            <div className="flex items-center gap-4">
              <div className="h-px flex-1 bg-border" />
              <span className="text-sm text-muted-foreground">或</span>
              <div className="h-px flex-1 bg-border" />
            </div>

            {/* Upload */}
            <div className="flex flex-col items-center justify-center rounded-lg border-2 border-dashed p-8">
              <Upload className="h-8 w-8 text-muted-foreground" />
              <p className="mt-2 text-sm text-muted-foreground">
                拖放音檔或點擊上傳
              </p>
              <p className="text-xs text-muted-foreground">
                支援 mp3, wav, m4a, webm
              </p>
            </div>

            <div>
              <label className="mb-2 block text-sm font-medium">
                選擇 Provider
              </label>
              <select className="w-full rounded-lg border bg-background p-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary">
                <option value="gcp">Google Cloud</option>
                <option value="azure">Azure</option>
                <option value="voai">VoAI</option>
              </select>
            </div>

            <div className="flex items-center gap-2">
              <input type="checkbox" id="childMode" />
              <label htmlFor="childMode" className="text-sm">
                兒童語音模式最佳化
              </label>
            </div>
          </div>
        </div>

        {/* Output Panel */}
        <div className="rounded-xl border bg-card p-6">
          <h2 className="mb-4 text-lg font-semibold">辨識結果</h2>

          <div className="min-h-40 rounded-lg border bg-background p-4">
            <p className="text-muted-foreground">辨識結果將顯示在這裡...</p>
          </div>

          <div className="mt-4 space-y-2">
            <div className="flex justify-between text-sm">
              <span className="text-muted-foreground">信心分數</span>
              <span>- %</span>
            </div>
            <div className="flex justify-between text-sm">
              <span className="text-muted-foreground">延遲時間</span>
              <span>- ms</span>
            </div>
          </div>

          <div className="mt-4">
            <label className="mb-2 block text-sm font-medium">
              正確答案（用於計算 WER）
            </label>
            <textarea
              placeholder="輸入正確的文字內容..."
              className="h-20 w-full rounded-lg border bg-background p-3 text-sm focus:outline-none focus:ring-2 focus:ring-primary"
            />
          </div>

          <div className="mt-4 flex justify-between rounded-lg bg-muted p-3">
            <span className="text-sm font-medium">字錯誤率 (WER)</span>
            <span className="text-sm">- %</span>
          </div>
        </div>
      </div>
    </div>
  )
}

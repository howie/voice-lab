export function HistoryPage() {
  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">歷史紀錄</h1>
          <p className="mt-1 text-muted-foreground">
            查看和管理所有測試紀錄
          </p>
        </div>
        <button className="rounded-lg border px-4 py-2 text-sm hover:bg-accent">
          匯出報表
        </button>
      </div>

      {/* Filters */}
      <div className="flex gap-4">
        <select className="rounded-lg border bg-background px-3 py-2 text-sm">
          <option value="">所有類型</option>
          <option value="tts">TTS</option>
          <option value="stt">STT</option>
          <option value="interaction">互動</option>
        </select>
        <select className="rounded-lg border bg-background px-3 py-2 text-sm">
          <option value="">所有 Provider</option>
          <option value="gcp">Google Cloud</option>
          <option value="azure">Azure</option>
          <option value="elevenlabs">ElevenLabs</option>
          <option value="voai">VoAI</option>
        </select>
        <input
          type="date"
          className="rounded-lg border bg-background px-3 py-2 text-sm"
        />
      </div>

      {/* Table */}
      <div className="rounded-xl border bg-card">
        <table className="w-full">
          <thead>
            <tr className="border-b text-left text-sm text-muted-foreground">
              <th className="p-4 font-medium">時間</th>
              <th className="p-4 font-medium">類型</th>
              <th className="p-4 font-medium">Provider</th>
              <th className="p-4 font-medium">內容</th>
              <th className="p-4 font-medium">延遲</th>
              <th className="p-4 font-medium">操作</th>
            </tr>
          </thead>
          <tbody>
            <tr>
              <td colSpan={6} className="p-8 text-center text-muted-foreground">
                尚無測試紀錄
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  )
}

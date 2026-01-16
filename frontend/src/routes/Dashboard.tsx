import { MessageSquare, Mic, MessagesSquare, BarChart3 } from 'lucide-react'
import { Link } from 'react-router-dom'

const features = [
  {
    name: 'TTS 測試',
    description: '測試各家 Text-to-Speech 服務的語音品質和參數',
    href: '/tts',
    icon: MessageSquare,
    color: 'bg-blue-500',
  },
  {
    name: 'STT 測試',
    description: '測試語音辨識準確度，支援錄音和檔案上傳',
    href: '/stt',
    icon: Mic,
    color: 'bg-green-500',
  },
  {
    name: '互動測試',
    description: '測試即時語音對話的延遲和回應品質',
    href: '/interaction',
    icon: MessagesSquare,
    color: 'bg-purple-500',
  },
]

const providers = [
  { name: 'Google Cloud', status: 'active', tts: true, stt: true },
  { name: 'Azure', status: 'active', tts: true, stt: true },
  { name: 'ElevenLabs', status: 'active', tts: true, stt: false },
  { name: 'VoAI', status: 'pending', tts: true, stt: true },
]

export function Dashboard() {
  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-2xl font-bold">歡迎使用 Voice Lab</h1>
        <p className="mt-1 text-muted-foreground">
          語音服務測試平台 - 比較各家 TTS、STT 和即時互動服務
        </p>
      </div>

      {/* Feature Cards */}
      <div className="grid gap-6 md:grid-cols-3">
        {features.map((feature) => (
          <Link
            key={feature.name}
            to={feature.href}
            className="group rounded-xl border bg-card p-6 transition-shadow hover:shadow-lg"
          >
            <div
              className={`inline-flex rounded-lg p-3 ${feature.color} text-white`}
            >
              <feature.icon className="h-6 w-6" />
            </div>
            <h3 className="mt-4 text-lg font-semibold group-hover:text-primary">
              {feature.name}
            </h3>
            <p className="mt-2 text-sm text-muted-foreground">
              {feature.description}
            </p>
          </Link>
        ))}
      </div>

      {/* Provider Status */}
      <div className="rounded-xl border bg-card">
        <div className="flex items-center justify-between border-b p-4">
          <h2 className="text-lg font-semibold">Provider 狀態</h2>
          <BarChart3 className="h-5 w-5 text-muted-foreground" />
        </div>
        <div className="p-4">
          <table className="w-full">
            <thead>
              <tr className="border-b text-left text-sm text-muted-foreground">
                <th className="pb-3 font-medium">Provider</th>
                <th className="pb-3 font-medium">狀態</th>
                <th className="pb-3 font-medium">TTS</th>
                <th className="pb-3 font-medium">STT</th>
              </tr>
            </thead>
            <tbody className="divide-y">
              {providers.map((provider) => (
                <tr key={provider.name}>
                  <td className="py-3 font-medium">{provider.name}</td>
                  <td className="py-3">
                    <span
                      className={`inline-flex items-center rounded-full px-2 py-1 text-xs font-medium ${
                        provider.status === 'active'
                          ? 'bg-green-100 text-green-700'
                          : 'bg-yellow-100 text-yellow-700'
                      }`}
                    >
                      {provider.status === 'active' ? '已連接' : '待設定'}
                    </span>
                  </td>
                  <td className="py-3">
                    {provider.tts ? (
                      <span className="text-green-600">✓</span>
                    ) : (
                      <span className="text-muted-foreground">-</span>
                    )}
                  </td>
                  <td className="py-3">
                    {provider.stt ? (
                      <span className="text-green-600">✓</span>
                    ) : (
                      <span className="text-muted-foreground">-</span>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  )
}

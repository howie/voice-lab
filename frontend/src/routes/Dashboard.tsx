import { MessageSquare, Mic, MessagesSquare, BarChart3, Loader2 } from 'lucide-react'
import { Link } from 'react-router-dom'
import { useEffect, useState } from 'react'
import { ttsApi, type ProviderInfo, type ProvidersSummaryResponse } from '@/lib/api'

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

interface ProviderSection {
  title: string
  type: 'tts' | 'stt' | 'llm'
  color: string
  providers: ProviderInfo[]
}

export function Dashboard() {
  const [providersSummary, setProvidersSummary] = useState<ProvidersSummaryResponse | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    async function fetchProviders() {
      try {
        setLoading(true)
        const response = await ttsApi.getProvidersSummary()
        setProvidersSummary(response.data)
        setError(null)
      } catch (err) {
        console.error('Failed to fetch providers:', err)
        setError('無法載入 Provider 資訊')
      } finally {
        setLoading(false)
      }
    }

    fetchProviders()
  }, [])

  const getStatusDisplay = (status: string) => {
    switch (status) {
      case 'available':
        return {
          label: '已連接',
          className: 'bg-green-100 text-green-700',
        }
      case 'unavailable':
        return {
          label: '未設定',
          className: 'bg-gray-100 text-gray-700',
        }
      case 'degraded':
        return {
          label: '降級',
          className: 'bg-yellow-100 text-yellow-700',
        }
      default:
        return {
          label: '未知',
          className: 'bg-gray-100 text-gray-700',
        }
    }
  }

  const sections: ProviderSection[] = providersSummary
    ? [
        {
          title: 'TTS (文字轉語音)',
          type: 'tts',
          color: 'border-l-blue-500',
          providers: providersSummary.tts,
        },
        {
          title: 'STT (語音辨識)',
          type: 'stt',
          color: 'border-l-green-500',
          providers: providersSummary.stt,
        },
        {
          title: 'LLM (大型語言模型)',
          type: 'llm',
          color: 'border-l-purple-500',
          providers: providersSummary.llm,
        },
      ]
    : []

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
          {loading ? (
            <div className="flex items-center justify-center py-8">
              <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
              <span className="ml-2 text-sm text-muted-foreground">載入中...</span>
            </div>
          ) : error ? (
            <div className="py-8 text-center">
              <p className="text-sm text-red-600">{error}</p>
            </div>
          ) : (
            <div className="space-y-6">
              {sections.map((section) => (
                <div key={section.type} className={`border-l-4 ${section.color} pl-4`}>
                  <h3 className="mb-3 text-sm font-semibold text-muted-foreground">
                    {section.title}
                  </h3>
                  <div className="overflow-x-auto">
                    <table className="w-full">
                      <thead>
                        <tr className="border-b text-left text-sm text-muted-foreground">
                          <th className="pb-2 pr-4 font-medium">Provider</th>
                          <th className="pb-2 pr-4 font-medium">狀態</th>
                          <th className="pb-2 pr-4 font-medium">支援格式</th>
                          <th className="pb-2 font-medium">支援語言</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y">
                        {section.providers.map((provider) => {
                          const statusDisplay = getStatusDisplay(provider.status)
                          return (
                            <tr key={`${section.type}-${provider.name}`}>
                              <td className="py-2 pr-4 font-medium">{provider.display_name}</td>
                              <td className="py-2 pr-4">
                                <span
                                  className={`inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium ${statusDisplay.className}`}
                                >
                                  {statusDisplay.label}
                                </span>
                              </td>
                              <td className="py-2 pr-4 text-sm text-muted-foreground">
                                {provider.supported_formats.length > 0
                                  ? provider.supported_formats.slice(0, 3).join(', ') +
                                    (provider.supported_formats.length > 3 ? '...' : '')
                                  : '-'}
                              </td>
                              <td className="py-2 text-sm text-muted-foreground">
                                {provider.supported_languages.slice(0, 3).join(', ')}
                                {provider.supported_languages.length > 3 && '...'}
                              </td>
                            </tr>
                          )
                        })}
                      </tbody>
                    </table>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

/**
 * ProviderSettings Page
 * T034: Provider API key management page
 */

import { useState, useEffect, useCallback } from 'react'
import { Key, RefreshCw, AlertCircle, Loader2 } from 'lucide-react'
import {
  credentialService,
  providerService,
  CredentialSummary,
  Provider,
  QuotaInfo,
  isValidationError,
} from '../../services/credentialService'
import { ProviderCard } from '../../components/settings/ProviderCard'

export function ProviderSettings() {
  const [providers, setProviders] = useState<Provider[]>([])
  const [credentials, setCredentials] = useState<CredentialSummary[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [refreshKey, setRefreshKey] = useState(0)

  // Load providers and credentials
  const loadData = useCallback(async () => {
    setIsLoading(true)
    setError(null)

    try {
      const [providersData, credentialsData] = await Promise.all([
        providerService.listProviders(),
        credentialService.listCredentials(),
      ])
      setProviders(providersData)
      setCredentials(credentialsData)
    } catch (err) {
      console.error('Failed to load data:', err)
      setError('載入 Provider 資訊失敗，請重試。')
    } finally {
      setIsLoading(false)
    }
  }, [])

  useEffect(() => {
    loadData()
  }, [loadData, refreshKey])

  // Get credential for a provider
  const getCredentialForProvider = (providerId: string) => {
    return credentials.find((c) => c.provider === providerId) ?? null
  }

  // Add new credential
  const handleAddKey = async (providerId: string, apiKey: string) => {
    try {
      await credentialService.addCredential({
        provider: providerId,
        api_key: apiKey,
      })
      // Refresh credentials
      const newCredentials = await credentialService.listCredentials()
      setCredentials(newCredentials)
    } catch (err) {
      if (isValidationError(err)) {
        throw new Error(err.response.data.message)
      }
      throw err
    }
  }

  // Update credential
  const handleUpdateKey = async (credentialId: string, apiKey: string) => {
    try {
      await credentialService.updateCredential(credentialId, {
        api_key: apiKey,
      })
      // Refresh credentials
      const newCredentials = await credentialService.listCredentials()
      setCredentials(newCredentials)
    } catch (err) {
      if (isValidationError(err)) {
        throw new Error(err.response.data.message)
      }
      throw err
    }
  }

  // Delete credential
  const handleDeleteKey = async (credentialId: string) => {
    await credentialService.deleteCredential(credentialId)
    // Refresh credentials
    const newCredentials = await credentialService.listCredentials()
    setCredentials(newCredentials)
  }

  // Validate credential
  const handleValidateKey = async (credentialId: string): Promise<QuotaInfo | null> => {
    const result = await credentialService.validateCredential(credentialId)
    // Refresh credentials to get updated status
    const newCredentials = await credentialService.listCredentials()
    setCredentials(newCredentials)

    if (!result.is_valid && result.error_message) {
      throw new Error(result.error_message)
    }

    return result.quota_info ?? null
  }

  // Select model
  const handleSelectModel = async (credentialId: string, modelId: string) => {
    await credentialService.updateCredential(credentialId, {
      selected_model_id: modelId,
    })
    // Refresh credentials
    const newCredentials = await credentialService.listCredentials()
    setCredentials(newCredentials)
  }

  // Refresh handler
  const handleRefresh = () => {
    setRefreshKey((prev) => prev + 1)
  }

  if (isLoading) {
    return (
      <div className="flex h-[50vh] items-center justify-center">
        <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
      </div>
    )
  }

  return (
    <div className="mx-auto max-w-3xl space-y-6 p-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="flex items-center gap-2 text-2xl font-bold">
            <Key className="h-6 w-6" />
            API 金鑰設定
          </h1>
          <p className="mt-1 text-sm text-muted-foreground">
            管理您的 TTS/STT 服務 API 金鑰
          </p>
        </div>

        <button
          onClick={handleRefresh}
          disabled={isLoading}
          className="flex items-center gap-1.5 rounded-md bg-secondary px-3 py-2 text-sm font-medium hover:bg-secondary/80 disabled:opacity-50"
        >
          <RefreshCw className={`h-4 w-4 ${isLoading ? 'animate-spin' : ''}`} />
          重新整理
        </button>
      </div>

      {/* Info Banner */}
      <div className="rounded-lg border border-blue-200 bg-blue-50 p-4">
        <h3 className="font-medium text-blue-900">
          自備金鑰 (BYOL)
        </h3>
        <p className="mt-1 text-sm text-blue-800">
          新增您自己的 API 金鑰來使用偏好的 TTS/STT 服務。您的金鑰會經過加密安全儲存。
          設定後，您的金鑰將優先於系統預設金鑰使用。
        </p>
      </div>

      {/* Error State */}
      {error && (
        <div className="flex items-start gap-3 rounded-lg border border-destructive/50 bg-destructive/10 p-4">
          <AlertCircle className="mt-0.5 h-5 w-5 text-destructive" />
          <div>
            <p className="font-medium text-destructive">錯誤</p>
            <p className="text-sm text-destructive/80">{error}</p>
          </div>
        </div>
      )}

      {/* Provider Cards */}
      <div className="space-y-4">
        {providers.length === 0 ? (
          <div className="rounded-lg border border-dashed p-8 text-center">
            <p className="text-muted-foreground">
              沒有可用的 Provider，請檢查網路連線。
            </p>
          </div>
        ) : (
          providers.map((provider) => (
            <ProviderCard
              key={provider.id}
              provider={provider}
              credential={getCredentialForProvider(provider.id)}
              onAddKey={handleAddKey}
              onUpdateKey={handleUpdateKey}
              onDeleteKey={handleDeleteKey}
              onValidateKey={handleValidateKey}
              onSelectModel={handleSelectModel}
              isLoading={isLoading}
            />
          ))
        )}
      </div>

      {/* Help Section */}
      <div className="rounded-lg border bg-muted/50 p-4">
        <h3 className="font-medium">如何取得 API 金鑰</h3>
        <ul className="mt-2 space-y-1.5 text-sm text-muted-foreground">
          <li>
            <strong>ElevenLabs:</strong>{' '}
            <a
              href="https://elevenlabs.io/app/settings/api-keys"
              target="_blank"
              rel="noopener noreferrer"
              className="text-primary hover:underline"
            >
              ElevenLabs Console
            </a>{' '}
            → Profile → API Key
          </li>
          <li>
            <strong>Azure:</strong>{' '}
            <a
              href="https://portal.azure.com"
              target="_blank"
              rel="noopener noreferrer"
              className="text-primary hover:underline"
            >
              Azure Portal
            </a>{' '}
            → Cognitive Services → Keys and Endpoint
          </li>
          <li>
            <strong>Gemini:</strong>{' '}
            <a
              href="https://aistudio.google.com/app/apikey"
              target="_blank"
              rel="noopener noreferrer"
              className="text-primary hover:underline"
            >
              Google AI Studio
            </a>{' '}
            → Get API Key
          </li>
        </ul>
      </div>
    </div>
  )
}

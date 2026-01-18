/**
 * ProviderCard Component
 * T033: Display card for a provider with credential status and actions
 */

import { useState } from 'react'
import {
  CheckCircle,
  XCircle,
  RefreshCw,
  Trash2,
  Edit2,
  ChevronDown,
  ChevronUp,
  Loader2,
} from 'lucide-react'
import {
  CredentialSummary,
  Provider,
  QuotaInfo,
  getProviderTheme,
} from '../../services/credentialService'
import { ApiKeyInput } from './ApiKeyInput'
import { ModelSelector } from './ModelSelector'

interface ProviderCardProps {
  provider: Provider
  credential?: CredentialSummary | null
  onAddKey: (providerId: string, apiKey: string) => Promise<void>
  onUpdateKey: (credentialId: string, apiKey: string) => Promise<void>
  onDeleteKey: (credentialId: string) => Promise<void>
  onValidateKey: (credentialId: string) => Promise<QuotaInfo | null>
  onSelectModel: (credentialId: string, modelId: string) => Promise<void>
  isLoading?: boolean
}

export function ProviderCard({
  provider,
  credential,
  onAddKey,
  onUpdateKey,
  onDeleteKey,
  onValidateKey,
  onSelectModel,
  isLoading = false,
}: ProviderCardProps) {
  const [isExpanded, setIsExpanded] = useState(false)
  const [isEditing, setIsEditing] = useState(false)
  const [newApiKey, setNewApiKey] = useState('')
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [isDeleting, setIsDeleting] = useState(false)
  const [isValidating, setIsValidating] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false)
  const [quotaInfo, setQuotaInfo] = useState<QuotaInfo | null>(null)
  const [validationError, setValidationError] = useState<string | null>(null)

  const theme = getProviderTheme(provider.id)
  const hasCredential = !!credential
  const isValid = credential?.is_valid ?? false

  const handleSubmit = async () => {
    if (!newApiKey.trim()) {
      setError('Please enter an API key')
      return
    }

    setError(null)
    setIsSubmitting(true)

    try {
      if (hasCredential && isEditing) {
        await onUpdateKey(credential!.id, newApiKey)
        setIsEditing(false)
      } else {
        await onAddKey(provider.id, newApiKey)
      }
      setNewApiKey('')
    } catch (err) {
      const message =
        err instanceof Error ? err.message : 'Failed to save API key'
      setError(message)
    } finally {
      setIsSubmitting(false)
    }
  }

  const handleValidate = async () => {
    if (!credential) return

    setIsValidating(true)
    setValidationError(null)
    try {
      const quota = await onValidateKey(credential.id)
      setQuotaInfo(quota)
    } catch (err) {
      console.error('Validation failed:', err)
      const message =
        err instanceof Error ? err.message : 'Validation failed'
      setValidationError(message)
    } finally {
      setIsValidating(false)
    }
  }

  const handleDelete = async () => {
    if (!credential) return

    setIsDeleting(true)
    try {
      await onDeleteKey(credential.id)
      setShowDeleteConfirm(false)
    } catch (err) {
      console.error('Delete failed:', err)
    } finally {
      setIsDeleting(false)
    }
  }

  const handleModelSelect = async (modelId: string) => {
    if (!credential) return
    try {
      await onSelectModel(credential.id, modelId)
    } catch (err) {
      console.error('Model selection failed:', err)
    }
  }

  const formatDate = (dateString: string | null) => {
    if (!dateString) return 'Never'
    return new Date(dateString).toLocaleDateString('zh-TW', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    })
  }

  return (
    <div
      className={`
        rounded-lg border bg-card shadow-sm transition-shadow hover:shadow-md
        ${isLoading ? 'opacity-50' : ''}
      `}
    >
      {/* Header */}
      <div
        className="flex cursor-pointer items-center justify-between p-4"
        onClick={() => setIsExpanded(!isExpanded)}
      >
        <div className="flex items-center gap-3">
          {/* Provider Icon/Badge */}
          <div
            className="flex h-10 w-10 items-center justify-center rounded-lg text-sm font-bold"
            style={{ backgroundColor: theme.bgColor, color: theme.color }}
          >
            {provider.display_name.charAt(0)}
          </div>

          <div>
            <h3 className="font-medium">{provider.display_name}</h3>
            <div className="flex items-center gap-2 text-xs text-muted-foreground">
              {provider.type?.map((t) => (
                <span key={t} className="uppercase">
                  {t}
                </span>
              ))}
            </div>
          </div>
        </div>

        <div className="flex items-center gap-2">
          {/* Status Badge */}
          {hasCredential ? (
            <div
              className={`
                flex items-center gap-1 rounded-full px-2.5 py-1 text-xs font-medium
                ${isValid ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-700'}
              `}
            >
              {isValid ? (
                <CheckCircle className="h-3 w-3" />
              ) : (
                <XCircle className="h-3 w-3" />
              )}
              {isValid ? 'Connected' : 'Invalid'}
            </div>
          ) : (
            <span className="text-xs text-muted-foreground">Not configured</span>
          )}

          {/* Expand/Collapse */}
          {isExpanded ? (
            <ChevronUp className="h-5 w-5 text-muted-foreground" />
          ) : (
            <ChevronDown className="h-5 w-5 text-muted-foreground" />
          )}
        </div>
      </div>

      {/* Expanded Content */}
      {isExpanded && (
        <div className="border-t px-4 pb-4 pt-3">
          {hasCredential && !isEditing ? (
            <>
              {/* Credential Info */}
              <div className="mb-4 space-y-2 text-sm">
                <div className="flex justify-between">
                  <span className="text-muted-foreground">API Key:</span>
                  <span className="font-mono">{credential.masked_key}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-muted-foreground">Last Validated:</span>
                  <span>{formatDate(credential.last_validated_at)}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-muted-foreground">Added:</span>
                  <span>{formatDate(credential.created_at)}</span>
                </div>
                {/* Quota Information */}
                {quotaInfo && (quotaInfo.character_limit || quotaInfo.tier) && (
                  <div className="mt-3 rounded-md bg-muted/50 p-2">
                    <div className="text-xs font-medium text-muted-foreground mb-1">
                      Usage Quota
                    </div>
                    {quotaInfo.tier && (
                      <div className="flex justify-between text-xs">
                        <span>Tier:</span>
                        <span className="font-medium">{quotaInfo.tier}</span>
                      </div>
                    )}
                    {quotaInfo.character_limit && (
                      <>
                        <div className="flex justify-between text-xs">
                          <span>Used:</span>
                          <span>
                            {(quotaInfo.character_count ?? 0).toLocaleString()} /{' '}
                            {quotaInfo.character_limit.toLocaleString()}
                          </span>
                        </div>
                        {quotaInfo.remaining_characters !== null && (
                          <div className="mt-1">
                            <div className="h-1.5 w-full rounded-full bg-muted">
                              <div
                                className="h-1.5 rounded-full bg-primary"
                                style={{
                                  width: `${Math.min(
                                    100,
                                    ((quotaInfo.character_count ?? 0) /
                                      quotaInfo.character_limit) *
                                      100
                                  )}%`,
                                }}
                              />
                            </div>
                          </div>
                        )}
                      </>
                    )}
                  </div>
                )}
                {/* Validation Error Message */}
                {validationError && (
                  <div className="mt-2 rounded-md bg-red-50 p-2 text-xs text-red-700">
                    {validationError}
                  </div>
                )}
              </div>

              {/* Model Selector */}
              {isValid && (
                <div className="mb-4">
                  <ModelSelector
                    credentialId={credential.id}
                    selectedModelId={credential.selected_model_id}
                    onSelect={handleModelSelect}
                  />
                </div>
              )}

              {/* Actions */}
              <div className="flex flex-wrap gap-2">
                <button
                  onClick={handleValidate}
                  disabled={isValidating}
                  className="flex items-center gap-1.5 rounded-md bg-secondary px-3 py-1.5 text-xs font-medium hover:bg-secondary/80 disabled:opacity-50"
                >
                  {isValidating ? (
                    <Loader2 className="h-3.5 w-3.5 animate-spin" />
                  ) : (
                    <RefreshCw className="h-3.5 w-3.5" />
                  )}
                  Validate
                </button>

                <button
                  onClick={() => {
                    setIsEditing(true)
                    setNewApiKey('')
                  }}
                  className="flex items-center gap-1.5 rounded-md bg-secondary px-3 py-1.5 text-xs font-medium hover:bg-secondary/80"
                >
                  <Edit2 className="h-3.5 w-3.5" />
                  Update Key
                </button>

                {showDeleteConfirm ? (
                  <div className="flex items-center gap-2">
                    <span className="text-xs text-muted-foreground">
                      Delete this key?
                    </span>
                    <button
                      onClick={handleDelete}
                      disabled={isDeleting}
                      className="flex items-center gap-1 rounded-md bg-destructive px-2 py-1 text-xs font-medium text-destructive-foreground hover:bg-destructive/90 disabled:opacity-50"
                    >
                      {isDeleting ? (
                        <Loader2 className="h-3 w-3 animate-spin" />
                      ) : (
                        'Yes'
                      )}
                    </button>
                    <button
                      onClick={() => setShowDeleteConfirm(false)}
                      className="rounded-md px-2 py-1 text-xs hover:bg-muted"
                    >
                      No
                    </button>
                  </div>
                ) : (
                  <button
                    onClick={() => setShowDeleteConfirm(true)}
                    className="flex items-center gap-1.5 rounded-md px-3 py-1.5 text-xs font-medium text-destructive hover:bg-destructive/10"
                  >
                    <Trash2 className="h-3.5 w-3.5" />
                    Delete
                  </button>
                )}
              </div>
            </>
          ) : (
            <>
              {/* API Key Input */}
              <div className="mb-4">
                <ApiKeyInput
                  value={newApiKey}
                  onChange={setNewApiKey}
                  onSubmit={handleSubmit}
                  placeholder={`Enter your ${provider.display_name} API key`}
                  disabled={isSubmitting}
                  isValidating={isSubmitting}
                  error={error}
                />
              </div>

              {/* Submit/Cancel Buttons */}
              <div className="flex gap-2">
                <button
                  onClick={handleSubmit}
                  disabled={isSubmitting || !newApiKey.trim()}
                  className="flex items-center gap-1.5 rounded-md bg-primary px-4 py-2 text-sm font-medium text-primary-foreground hover:bg-primary/90 disabled:opacity-50"
                >
                  {isSubmitting && (
                    <Loader2 className="h-4 w-4 animate-spin" />
                  )}
                  {isEditing ? 'Update' : 'Save & Validate'}
                </button>

                {isEditing && (
                  <button
                    onClick={() => {
                      setIsEditing(false)
                      setNewApiKey('')
                      setError(null)
                    }}
                    className="rounded-md px-4 py-2 text-sm font-medium hover:bg-muted"
                  >
                    Cancel
                  </button>
                )}
              </div>
            </>
          )}
        </div>
      )}
    </div>
  )
}

/**
 * ModelSelector Component
 * T045: Select voice/model for a provider credential
 */

import { useState, useEffect } from 'react'
import { ChevronDown, Loader2 } from 'lucide-react'
import {
  credentialService,
  ProviderModel,
} from '../../services/credentialService'

interface ModelSelectorProps {
  credentialId: string
  selectedModelId: string | null
  onSelect: (modelId: string) => void
  disabled?: boolean
}

export function ModelSelector({
  credentialId,
  selectedModelId,
  onSelect,
  disabled = false,
}: ModelSelectorProps) {
  const [models, setModels] = useState<ProviderModel[]>([])
  const [isLoading, setIsLoading] = useState(false)
  const [isOpen, setIsOpen] = useState(false)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    const loadModels = async () => {
      setIsLoading(true)
      setError(null)
      try {
        const data = await credentialService.getCredentialModels(credentialId)
        setModels(data)
      } catch (err) {
        console.error('Failed to load models:', err)
        setError('Failed to load models')
      } finally {
        setIsLoading(false)
      }
    }

    loadModels()
  }, [credentialId])

  const selectedModel = models.find((m) => m.id === selectedModelId)

  const handleSelect = (modelId: string) => {
    onSelect(modelId)
    setIsOpen(false)
  }

  if (isLoading) {
    return (
      <div className="flex items-center gap-2 text-sm text-muted-foreground">
        <Loader2 className="h-4 w-4 animate-spin" />
        Loading models...
      </div>
    )
  }

  if (error) {
    return (
      <div className="text-sm text-destructive">
        {error}
      </div>
    )
  }

  if (models.length === 0) {
    return (
      <div className="text-sm text-muted-foreground">
        No models available
      </div>
    )
  }

  return (
    <div className="space-y-1.5">
      <label className="text-xs font-medium text-muted-foreground">
        Default Voice/Model
      </label>

      <div className="relative">
        <button
          type="button"
          onClick={() => setIsOpen(!isOpen)}
          disabled={disabled}
          className={`
            flex w-full items-center justify-between rounded-lg border bg-background
            px-3 py-2 text-sm
            hover:bg-muted/50 disabled:cursor-not-allowed disabled:opacity-50
            ${isOpen ? 'ring-2 ring-primary' : ''}
          `}
        >
          <span className={selectedModel ? '' : 'text-muted-foreground'}>
            {selectedModel ? selectedModel.name : 'Select a model...'}
          </span>
          <ChevronDown
            className={`h-4 w-4 text-muted-foreground transition-transform ${
              isOpen ? 'rotate-180' : ''
            }`}
          />
        </button>

        {isOpen && (
          <div className="absolute z-10 mt-1 max-h-60 w-full overflow-auto rounded-lg border bg-popover shadow-lg">
            {models.map((model) => (
              <button
                key={model.id}
                type="button"
                onClick={() => handleSelect(model.id)}
                className={`
                  flex w-full items-center justify-between px-3 py-2 text-left text-sm
                  hover:bg-muted
                  ${model.id === selectedModelId ? 'bg-muted' : ''}
                `}
              >
                <div>
                  <div className="font-medium">{model.name}</div>
                  <div className="text-xs text-muted-foreground">
                    {model.language}
                    {model.gender && ` • ${model.gender}`}
                  </div>
                </div>
                {model.id === selectedModelId && (
                  <span className="text-primary">✓</span>
                )}
              </button>
            ))}
          </div>
        )}
      </div>

      {selectedModel?.description && (
        <p className="text-xs text-muted-foreground">
          {selectedModel.description}
        </p>
      )}
    </div>
  )
}

/**
 * ProviderSelector Component
 * T041: Create ProviderSelector component (dropdown for Azure/GCP/ElevenLabs/VoAI)
 */

interface Provider {
  id: string
  name: string
  displayName: string
  description?: string
}

const PROVIDERS: Provider[] = [
  {
    id: 'azure',
    name: 'azure',
    displayName: 'Azure Speech',
    description: 'Microsoft Azure 語音服務',
  },
  {
    id: 'gcp',
    name: 'gcp',
    displayName: 'Google Cloud',
    description: 'Google Cloud Text-to-Speech',
  },
  {
    id: 'elevenlabs',
    name: 'elevenlabs',
    displayName: 'ElevenLabs',
    description: '高品質 AI 語音合成',
  },
  {
    id: 'voai',
    name: 'voai',
    displayName: 'VoAI 台灣語音',
    description: '專為台灣中文優化',
  },
]

interface ProviderSelectorProps {
  value: string
  onChange: (value: string) => void
  disabled?: boolean
}

export function ProviderSelector({
  value,
  onChange,
  disabled = false,
}: ProviderSelectorProps) {
  return (
    <div className="space-y-2">
      <label className="block text-sm font-medium">選擇 Provider</label>
      <select
        value={value}
        onChange={(e) => onChange(e.target.value)}
        disabled={disabled}
        className="w-full rounded-lg border bg-background p-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary disabled:cursor-not-allowed disabled:opacity-50"
      >
        {PROVIDERS.map((provider) => (
          <option key={provider.id} value={provider.name}>
            {provider.displayName}
          </option>
        ))}
      </select>
      <p className="text-xs text-muted-foreground">
        {PROVIDERS.find((p) => p.name === value)?.description}
      </p>
    </div>
  )
}

export { PROVIDERS }
export type { Provider }

import { describe, expect, it } from 'vitest'
import { getProviderDisplayName, getProviderTheme } from '../credentialService'

describe('getProviderDisplayName', () => {
  const expectedNames: Record<string, string> = {
    elevenlabs: 'ElevenLabs',
    azure: 'Azure Cognitive Services',
    gemini: 'Google Gemini',
    openai: 'OpenAI',
    anthropic: 'Anthropic',
    gcp: 'Google Cloud Platform',
    voai: 'VoAI',
    speechmatics: 'Speechmatics',
  }

  for (const [id, name] of Object.entries(expectedNames)) {
    it(`returns "${name}" for provider "${id}"`, () => {
      expect(getProviderDisplayName(id)).toBe(name)
    })
  }

  it('falls back to raw id for unknown provider', () => {
    expect(getProviderDisplayName('unknown-provider')).toBe('unknown-provider')
  })
})

describe('getProviderTheme', () => {
  const knownProviders = [
    'elevenlabs',
    'azure',
    'gemini',
    'openai',
    'anthropic',
    'gcp',
    'voai',
    'speechmatics',
  ]

  for (const id of knownProviders) {
    it(`returns color and bgColor for provider "${id}"`, () => {
      const theme = getProviderTheme(id)
      expect(theme).toHaveProperty('color')
      expect(theme).toHaveProperty('bgColor')
      expect(theme.color).toBeTruthy()
      expect(theme.bgColor).toBeTruthy()
    })
  }

  it('returns default gray theme for unknown provider', () => {
    const theme = getProviderTheme('unknown')
    expect(theme).toEqual({ color: '#6b7280', bgColor: '#f3f4f6' })
  })
})

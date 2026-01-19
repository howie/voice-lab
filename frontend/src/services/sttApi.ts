/**
 * STT API Service for Speech-to-Text Testing Module
 * Feature: 003-stt-testing-module
 * T021: Create STT API client
 */

import { api } from '../lib/api'
import type {
  STTProviderName,
  STTProvider,
  TranscriptionResponse,
  TranscriptionHistoryPage,
  TranscriptionDetail,
  ComparisonResponse,
  WERAnalysis,
} from '../types/stt'

// --- Provider Endpoints ---

/**
 * List available STT providers with their capabilities
 */
export async function listSTTProviders(): Promise<STTProvider[]> {
  const response = await api.get<{ providers: STTProvider[] }>('/stt/providers')
  return response.data.providers
}

/**
 * Get a specific STT provider's information
 */
export async function getSTTProvider(providerName: STTProviderName): Promise<STTProvider> {
  const providers = await listSTTProviders()
  const provider = providers.find((p) => p.name === providerName)
  if (!provider) {
    throw new Error(`Unknown provider: ${providerName}`)
  }
  return provider
}

// --- Transcription Endpoints ---

export interface TranscribeOptions {
  provider: STTProviderName
  language?: string
  childMode?: boolean
  groundTruth?: string
  saveToHistory?: boolean
}

/**
 * Transcribe an audio file
 */
export async function transcribeAudio(
  audioFile: File | Blob,
  options: TranscribeOptions
): Promise<TranscriptionResponse> {
  const formData = new FormData()

  // Add audio file
  if (audioFile instanceof File) {
    formData.append('audio', audioFile)
  } else {
    formData.append('audio', audioFile, 'recording.webm')
  }

  // Add options
  formData.append('provider', options.provider)
  formData.append('language', options.language || 'zh-TW')
  formData.append('child_mode', String(options.childMode || false))
  formData.append('save_to_history', String(options.saveToHistory ?? true))

  if (options.groundTruth) {
    formData.append('ground_truth', options.groundTruth)
  }

  const response = await api.post<TranscriptionResponse>('/stt/transcribe', formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  })

  return response.data
}

// --- Comparison Endpoints ---

export interface CompareOptions {
  providers: STTProviderName[]
  language?: string
  groundTruth?: string
}

/**
 * Compare transcription results across multiple providers
 */
export async function compareProviders(
  audioFile: File | Blob,
  options: CompareOptions
): Promise<ComparisonResponse> {
  const formData = new FormData()

  // Add audio file
  if (audioFile instanceof File) {
    formData.append('audio', audioFile)
  } else {
    formData.append('audio', audioFile, 'recording.webm')
  }

  // Add providers (multiple values)
  options.providers.forEach((provider) => {
    formData.append('providers', provider)
  })

  // Add options
  formData.append('language', options.language || 'zh-TW')

  if (options.groundTruth) {
    formData.append('ground_truth', options.groundTruth)
  }

  const response = await api.post<ComparisonResponse>('/stt/compare', formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  })

  return response.data
}

// --- History Endpoints ---

export interface HistoryFilters {
  provider?: STTProviderName
  language?: string
  page?: number
  pageSize?: number
}

/**
 * List transcription history with pagination and filters
 */
export async function listTranscriptionHistory(
  filters?: HistoryFilters
): Promise<TranscriptionHistoryPage> {
  const params = new URLSearchParams()

  if (filters?.provider) params.append('provider', filters.provider)
  if (filters?.language) params.append('language', filters.language)
  if (filters?.page) params.append('page', String(filters.page))
  if (filters?.pageSize) params.append('page_size', String(filters.pageSize))

  const response = await api.get<TranscriptionHistoryPage>('/stt/history', { params })
  return response.data
}

/**
 * Get detailed transcription result by ID
 */
export async function getTranscriptionDetail(id: string): Promise<TranscriptionDetail> {
  const response = await api.get<TranscriptionDetail>(`/stt/history/${id}`)
  return response.data
}

/**
 * Delete a transcription record
 */
export async function deleteTranscription(id: string): Promise<void> {
  await api.delete(`/stt/history/${id}`)
}

// --- WER Analysis Endpoints ---

export interface WERAnalysisRequest {
  resultId: string
  groundTruth: string
}

/**
 * Calculate WER/CER for an existing transcription
 */
export async function calculateWER(request: WERAnalysisRequest): Promise<WERAnalysis> {
  const response = await api.post<WERAnalysis>('/stt/analysis/wer', {
    result_id: request.resultId,
    ground_truth: request.groundTruth,
  })
  return response.data
}

// --- Utility Functions ---

/**
 * Check if a file format is supported by a provider
 */
export function isFormatSupported(
  provider: STTProvider,
  format: string
): boolean {
  const normalizedFormat = format.toLowerCase().replace('.', '')
  return provider.supported_formats.includes(normalizedFormat as never)
}

/**
 * Check if file size is within provider limits
 */
export function isFileSizeValid(
  provider: STTProvider,
  fileSizeBytes: number
): boolean {
  const maxBytes = provider.max_file_size_mb * 1024 * 1024
  return fileSizeBytes <= maxBytes
}

/**
 * Get human-readable file size limit for a provider
 */
export function getFileSizeLimit(provider: STTProvider): string {
  return `${provider.max_file_size_mb} MB`
}

/**
 * Get human-readable duration limit for a provider
 */
export function getDurationLimit(provider: STTProvider): string {
  const minutes = Math.floor(provider.max_duration_sec / 60)
  const seconds = provider.max_duration_sec % 60
  if (seconds === 0) {
    return `${minutes} minutes`
  }
  return `${minutes}m ${seconds}s`
}

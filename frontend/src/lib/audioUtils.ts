/**
 * Audio Utilities
 * Feature: 010-magic-dj-controller
 *
 * Shared audio helper functions for Magic DJ module.
 */

/**
 * Convert a Blob to a base64 data URL string.
 * Used for persisting audio data to localStorage.
 */
export async function blobToBase64DataUrl(blob: Blob): Promise<string> {
  const arrayBuffer = await blob.arrayBuffer()
  const uint8Array = new Uint8Array(arrayBuffer)
  let binary = ''
  for (let i = 0; i < uint8Array.length; i++) {
    binary += String.fromCharCode(uint8Array[i])
  }
  return `data:${blob.type || 'audio/mpeg'};base64,${btoa(binary)}`
}

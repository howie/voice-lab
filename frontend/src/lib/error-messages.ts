/**
 * T026: Format retry_after to human-readable Chinese time strings.
 */

/**
 * Format retry_after seconds to a human-readable Chinese string.
 * Examples:
 *   - 30 -> "約 30 秒後可重試"
 *   - 60 -> "約 1 分鐘後可重試"
 *   - 3600 -> "約 1 小時後可重試"
 *   - 86400 -> "約 1 天後可重試"
 */
export function formatRetryAfter(seconds: number): string {
  if (seconds <= 0) {
    return '可以立即重試'
  }

  if (seconds < 60) {
    return `約 ${seconds} 秒後可重試`
  }

  if (seconds < 3600) {
    const minutes = Math.ceil(seconds / 60)
    return `約 ${minutes} 分鐘後可重試`
  }

  if (seconds < 86400) {
    const hours = Math.ceil(seconds / 3600)
    return `約 ${hours} 小時後可重試`
  }

  const days = Math.ceil(seconds / 86400)
  return `約 ${days} 天後可重試`
}

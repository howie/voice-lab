import { useLocation } from 'react-router-dom'

/**
 * Hook to get the redirect path after login
 */
export function useLoginRedirect() {
  const location = useLocation()
  const state = location.state as { from?: string } | null

  return state?.from || '/'
}

/**
 * ProtectedRoute Component
 * T050: Add protected route wrapper requiring authentication
 */

import { useEffect } from 'react'
import { useNavigate, useLocation } from 'react-router-dom'
import { useAuthStore } from '@/stores/authStore'
import { Spinner } from '@/components/tts/LoadingIndicator'

interface ProtectedRouteProps {
  children: React.ReactNode
  redirectTo?: string
}

export function ProtectedRoute({
  children,
  redirectTo = '/login',
}: ProtectedRouteProps) {
  // TEMPORARY: Bypass auth for local testing
  const DEV_BYPASS_AUTH = import.meta.env.DEV

  // Use individual selectors to prevent unnecessary re-renders
  const isAuthenticated = useAuthStore((state) => state.isAuthenticated)
  const isLoading = useAuthStore((state) => state.isLoading)
  const checkAuth = useAuthStore((state) => state.checkAuth)
  const navigate = useNavigate()
  const location = useLocation()

  // Check auth only on mount - empty dependency array ensures single execution
  useEffect(() => {
    if (!DEV_BYPASS_AUTH) {
      checkAuth()
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  // Redirect if not authenticated after loading
  useEffect(() => {
    if (!DEV_BYPASS_AUTH && !isLoading && !isAuthenticated) {
      // Save the attempted URL for redirecting after login
      navigate(redirectTo, {
        state: { from: location.pathname },
        replace: true,
      })
    }
  }, [DEV_BYPASS_AUTH, isAuthenticated, isLoading, navigate, redirectTo, location])

  // Bypass auth in dev mode
  if (DEV_BYPASS_AUTH) {
    return <>{children}</>
  }

  // Show loading state while checking auth
  if (isLoading) {
    return (
      <div className="flex min-h-screen items-center justify-center">
        <div className="flex flex-col items-center gap-4">
          <Spinner className="h-8 w-8 text-primary" />
          <p className="text-sm text-muted-foreground">驗證身份中...</p>
        </div>
      </div>
    )
  }

  // Don't render children if not authenticated
  if (!isAuthenticated) {
    return null
  }

  return <>{children}</>
}

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
  const { isAuthenticated, isLoading, checkAuth } = useAuthStore()
  const navigate = useNavigate()
  const location = useLocation()

  // Check auth on mount
  useEffect(() => {
    checkAuth()
  }, [checkAuth])

  // Redirect if not authenticated after loading
  useEffect(() => {
    if (!isLoading && !isAuthenticated) {
      // Save the attempted URL for redirecting after login
      navigate(redirectTo, {
        state: { from: location.pathname },
        replace: true,
      })
    }
  }, [isAuthenticated, isLoading, navigate, redirectTo, location])

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

import { useEffect } from 'react'
import { BrowserRouter, Routes, Route } from 'react-router-dom'
import { AppLayout } from '@/components/layout/AppLayout'
import { Dashboard } from '@/routes/Dashboard'
import { TTSPage } from '@/routes/tts/TTSPage'
import { STTPage } from '@/routes/stt/STTPage'
import { STTHistoryPage } from '@/routes/stt/STTHistoryPage'
import { InteractionPage } from '@/routes/interaction/InteractionPage'
import { InteractionHistoryPage } from '@/routes/interaction/InteractionHistoryPage'
import { HistoryPage } from '@/routes/history/HistoryPage'
import { AdvancedPage } from '@/routes/advanced/AdvancedPage'
import { ProviderSettings } from '@/routes/settings/ProviderSettings'
import { MultiRoleTTSPage } from '@/routes/multi-role-tts/MultiRoleTTSPage'
import { JobsPage } from '@/routes/jobs'
import { LoginPage } from '@/routes/auth/LoginPage'
import { AuthCallback } from '@/routes/auth/AuthCallback'
import { ProtectedRoute } from '@/components/auth/ProtectedRoute'
import { useAuthStore } from '@/stores/authStore'

function AppContent() {
  const checkAuth = useAuthStore((state) => state.checkAuth)
  const setToken = useAuthStore((state) => state.setToken)

  // Handle OAuth token from URL (after SSO redirect)
  useEffect(() => {
    const params = new URLSearchParams(window.location.search)
    const token = params.get('token')
    const error = params.get('error')

    if (token) {
      // Store token and clean URL
      setToken(token)
      window.history.replaceState({}, '', window.location.pathname)
    } else if (error) {
      // Handle error (e.g., domain_not_allowed)
      console.error('OAuth error:', error)
      window.history.replaceState({}, '', window.location.pathname)
    }
  }, [setToken])

  // Check auth on app load
  useEffect(() => {
    checkAuth()
  }, [checkAuth])

  return (
    <Routes>
      {/* Public routes */}
      <Route path="/login" element={<LoginPage />} />
      <Route path="/auth/callback" element={<AuthCallback />} />

      {/* Protected routes */}
      <Route
        path="/"
        element={
          <ProtectedRoute>
            <AppLayout />
          </ProtectedRoute>
        }
      >
        <Route index element={<Dashboard />} />
        <Route path="tts" element={<TTSPage />} />
        <Route path="multi-role-tts" element={<MultiRoleTTSPage />} />
        <Route path="jobs" element={<JobsPage />} />
        <Route path="stt" element={<STTPage />} />
        <Route path="stt/history" element={<STTHistoryPage />} />
        <Route path="interaction" element={<InteractionPage />} />
        <Route path="interaction/history" element={<InteractionHistoryPage />} />
        <Route path="history" element={<HistoryPage />} />
        <Route path="advanced" element={<AdvancedPage />} />
        <Route path="settings/providers" element={<ProviderSettings />} />
      </Route>
    </Routes>
  )
}

function App() {
  return (
    <BrowserRouter>
      <AppContent />
    </BrowserRouter>
  )
}

export default App

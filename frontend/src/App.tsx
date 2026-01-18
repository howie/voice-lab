import { useEffect } from 'react'
import { BrowserRouter, Routes, Route } from 'react-router-dom'
import { AppLayout } from '@/components/layout/AppLayout'
import { Dashboard } from '@/routes/Dashboard'
import { TTSPage } from '@/routes/tts/TTSPage'
import { STTPage } from '@/routes/stt/STTPage'
import { InteractionPage } from '@/routes/interaction/InteractionPage'
import { HistoryPage } from '@/routes/history/HistoryPage'
import { AdvancedPage } from '@/routes/advanced/AdvancedPage'
import { ProviderSettings } from '@/routes/settings/ProviderSettings'
import { LoginPage } from '@/routes/auth/LoginPage'
import { AuthCallback } from '@/routes/auth/AuthCallback'
import { ProtectedRoute } from '@/components/auth/ProtectedRoute'
import { useAuthStore } from '@/stores/authStore'

function AppContent() {
  const checkAuth = useAuthStore((state) => state.checkAuth)

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
        <Route path="stt" element={<STTPage />} />
        <Route path="interaction" element={<InteractionPage />} />
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

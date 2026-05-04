import { Routes, Route, Navigate } from 'react-router-dom'
import { useAuthStore } from '@/store/authStore'
import { useAdminStore } from '@/store/adminStore'
import { AgeGate } from '@/components/age-gate/AgeGate'
import { ErrorBoundary } from '@/components/ui/ErrorBoundary'

// Public pages
import { HomePage } from '@/pages/HomePage'
import { SearchPage } from '@/pages/SearchPage'
import { EscortProfilePage } from '@/pages/EscortProfilePage'
import { BoroughPage } from '@/pages/BoroughPage'
import { AreasPage } from '@/pages/AreasPage'
import { JoinPage } from '@/pages/JoinPage'
import { AboutPage } from '@/pages/AboutPage'
import { SafetyPage } from '@/pages/SafetyPage'

// Auth pages
import { LoginPage } from '@/pages/auth/LoginPage'
import { RegisterPage } from '@/pages/auth/RegisterPage'
import { VerifyEmailPage } from '@/pages/auth/VerifyEmailPage'

// Dashboard pages
import { DashboardPage } from '@/pages/dashboard/DashboardPage'
import { EditProfilePage } from '@/pages/dashboard/EditProfilePage'
import { SubscriptionPage } from '@/pages/dashboard/SubscriptionPage'
import { MySubscriptionsPage } from '@/pages/dashboard/MySubscriptionsPage'
import { VerifyPage } from '@/pages/dashboard/VerifyPage'

// Admin pages
import { AdminLoginPage } from '@/pages/admin/AdminLoginPage'
import { AdminDashboardPage } from '@/pages/admin/AdminDashboardPage'
import { AdminVerificationsPage } from '@/pages/admin/AdminVerificationsPage'
import { AdminVerificationDetailPage } from '@/pages/admin/AdminVerificationDetailPage'
import { AdminEscortsPage } from '@/pages/admin/AdminEscortsPage'
import { AdminDiscountsPage } from '@/pages/admin/AdminDiscountsPage'
import { AdminPricingPage } from '@/pages/admin/AdminPricingPage'

function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const { isAuthenticated } = useAuthStore()
  if (!isAuthenticated) return <Navigate to="/login" replace />
  return <>{children}</>
}

function GuestRoute({ children }: { children: React.ReactNode }) {
  const { isAuthenticated } = useAuthStore()
  if (isAuthenticated) return <Navigate to="/dashboard" replace />
  return <>{children}</>
}

function AdminRoute({ children }: { children: React.ReactNode }) {
  const { isAuthenticated } = useAdminStore()
  if (!isAuthenticated) return <Navigate to="/admin/login" replace />
  return <>{children}</>
}

export default function App() {
  return (
    <ErrorBoundary>
      {/* Admin portal — no age gate */}
      <Routes>
        <Route path="/admin/login" element={<AdminLoginPage />} />
        <Route path="/admin" element={<AdminRoute><AdminDashboardPage /></AdminRoute>} />
        <Route path="/admin/verifications" element={<AdminRoute><AdminVerificationsPage /></AdminRoute>} />
        <Route path="/admin/verifications/:id" element={<AdminRoute><AdminVerificationDetailPage /></AdminRoute>} />
        <Route path="/admin/escorts" element={<AdminRoute><AdminEscortsPage /></AdminRoute>} />
        <Route path="/admin/discounts" element={<AdminRoute><AdminDiscountsPage /></AdminRoute>} />
        <Route path="/admin/pricing" element={<AdminRoute><AdminPricingPage /></AdminRoute>} />

        {/* Escort-facing site — wrapped in age gate */}
        <Route path="*" element={
          <AgeGate>
            <Routes>
              {/* Public */}
              <Route path="/" element={<HomePage />} />
              <Route path="/escorts" element={<SearchPage />} />
              <Route path="/escorts/:slug" element={<EscortProfilePage />} />
              <Route path="/areas" element={<AreasPage />} />
              <Route path="/areas/:slug" element={<BoroughPage />} />
              <Route path="/join" element={<JoinPage />} />
              <Route path="/about" element={<AboutPage />} />
              <Route path="/safety" element={<SafetyPage />} />
              <Route path="/verify-email" element={<VerifyEmailPage />} />

              {/* Auth (guests only) */}
              <Route path="/login" element={<GuestRoute><LoginPage /></GuestRoute>} />
              <Route path="/register" element={<GuestRoute><RegisterPage /></GuestRoute>} />

              {/* Dashboard (protected) */}
              <Route path="/dashboard" element={<ProtectedRoute><DashboardPage /></ProtectedRoute>} />
              <Route path="/dashboard/profile" element={<ProtectedRoute><EditProfilePage /></ProtectedRoute>} />
              <Route path="/dashboard/photos" element={<Navigate to="/dashboard/profile" replace />} />
              <Route path="/dashboard/subscription" element={<ProtectedRoute><SubscriptionPage /></ProtectedRoute>} />
              <Route path="/dashboard/subscriptions" element={<ProtectedRoute><MySubscriptionsPage /></ProtectedRoute>} />
              <Route path="/dashboard/verify" element={<ProtectedRoute><VerifyPage /></ProtectedRoute>} />

              {/* Fallback */}
              <Route path="*" element={<Navigate to="/" replace />} />
            </Routes>
          </AgeGate>
        } />
      </Routes>
    </ErrorBoundary>
  )
}

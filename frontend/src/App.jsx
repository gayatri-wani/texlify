import { useEffect } from 'react'
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { Toaster } from 'react-hot-toast'
import useAuthStore from './store/authStore'
import Login         from './pages/auth/Login'
import Register      from './pages/auth/Register'
import ResetPassword from './pages/auth/ResetPassword'
import Dashboard     from './pages/dashboard/Dashboard'
import Profile       from './pages/profile/Profile'

const ProtectedRoute = ({ children }) => {
  const { isAuthenticated, isLoading } = useAuthStore()
  if (isLoading) return (
    <div style={{
      display:'flex', alignItems:'center', justifyContent:'center',
      height:'100vh', background:'var(--bg-primary)',
      color:'var(--text-muted)', fontSize:'14px',
      fontFamily:'var(--font-family)'
    }}>
      Loading Texlify...
    </div>
  )
  return isAuthenticated ? children : <Navigate to="/login" replace />
}

const PublicRoute = ({ children }) => {
  const { isAuthenticated, isLoading } = useAuthStore()
  if (isLoading) return null
  return !isAuthenticated ? children : <Navigate to="/dashboard" replace />
}

function App() {
  const { initializeAuth } = useAuthStore()
  useEffect(() => { initializeAuth() }, [])

  return (
    <BrowserRouter>
      <Toaster
        position="top-right"
        toastOptions={{
          duration: 3000,
          style: {
            background:   'var(--bg-card)',
            color:        'var(--text-dark)',
            border:       '1.5px solid var(--border-light)',
            borderRadius: 'var(--radius-md)',
            fontSize:     '13px',
            fontFamily:   'var(--font-family)',
          },
          success: { iconTheme: { primary: '#10B981', secondary: 'white' } },
          error:   { iconTheme: { primary: '#EF4444', secondary: 'white' } },
        }}
      />
      <Routes>
        <Route path="/" element={<Navigate to="/dashboard" replace />} />
        <Route path="/login"
          element={<PublicRoute><Login /></PublicRoute>} />
        <Route path="/register"
          element={<PublicRoute><Register /></PublicRoute>} />
        <Route path="/reset-password" element={<ResetPassword />} />
        <Route path="/dashboard"
          element={<ProtectedRoute><Dashboard /></ProtectedRoute>} />
        <Route path="/profile"
          element={<ProtectedRoute><Profile /></ProtectedRoute>} />
        <Route path="*" element={<Navigate to="/dashboard" replace />} />
      </Routes>
    </BrowserRouter>
  )
}

export default App
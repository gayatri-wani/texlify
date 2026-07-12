import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { Toaster } from 'react-hot-toast'
import Login from './pages/auth/Login'
import Register from './pages/auth/Register'
import useAuthStore from './store/authStore'
import './App.css'

const ProtectedRoute = ({ children }) => {
  const { isAuthenticated } = useAuthStore()
  return isAuthenticated ? children : <Navigate to="/login" replace />
}

const PublicRoute = ({ children }) => {
  const { isAuthenticated } = useAuthStore()
  return !isAuthenticated ? children : <Navigate to="/dashboard" replace />
}

const Dashboard = () => {
  const { user, logout } = useAuthStore()
  return (
    <div className="dashboard-placeholder">
      <div className="dashboard-placeholder__card">
        <div className="dashboard-placeholder__icon">🎉</div>
        <h1 className="dashboard-placeholder__title">Welcome to Texlify!</h1>
        <p className="dashboard-placeholder__name">{user?.full_name}</p>
        <p className="dashboard-placeholder__email">{user?.email}</p>
        <button className="dashboard-placeholder__logout" onClick={logout}>
          Sign Out
        </button>
      </div>
    </div>
  )
}

function App() {
  return (
    <BrowserRouter>
      <Toaster
        position="top-right"
        toastOptions={{
          style: {
            background: '#FFFFFF',
            color: '#064E3B',
            border: '1.5px solid #BBF7D0',
            borderRadius: '10px',
            fontSize: '14px',
            fontWeight: '500',
            boxShadow: '0 4px 16px rgba(16, 185, 129, 0.12)',
          },
          success: {
            iconTheme: { primary: '#10B981', secondary: '#FFFFFF' },
          },
          error: {
            iconTheme: { primary: '#EF4444', secondary: '#FFFFFF' },
          },
        }}
      />
      <Routes>
        <Route path="/" element={<Navigate to="/login" replace />} />
        <Route path="/login"    element={<PublicRoute><Login /></PublicRoute>} />
        <Route path="/register" element={<PublicRoute><Register /></PublicRoute>} />
        <Route path="/dashboard" element={<ProtectedRoute><Dashboard /></ProtectedRoute>} />
      </Routes>
    </BrowserRouter>
  )
}

export default App
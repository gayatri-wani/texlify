import { useState } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import { Mail, Lock, Eye, EyeOff, Sparkles, ArrowRight } from 'lucide-react'
import { authService } from '../../services/authService'
import useAuthStore from '../../store/authStore'
import { toast } from 'react-hot-toast'
import './Login.css'

const Login = () => {
  const [email, setEmail]             = useState('')
  const [password, setPassword]       = useState('')
  const [showPwd, setShowPwd]         = useState(false)
  const [loading, setLoading]         = useState(false)
  const [showForgot, setShowForgot]   = useState(false)
  const [forgotEmail, setForgotEmail] = useState('')
  const [forgotLoading, setForgotLoading] = useState(false)
  const [forgotSent, setForgotSent]   = useState(false)
  const { setAuth }                   = useAuthStore()
  const navigate                      = useNavigate()

  const handleLogin = async (e) => {
    e.preventDefault()
    if (!email || !password) { toast.error('Fill in all fields'); return }
    setLoading(true)
    try {
      const data = await authService.login(email, password)
      setAuth(data.user, data.access_token, data.refresh_token)
      toast.success(`Welcome back, ${data.user.full_name.split(' ')[0]}!`)
      navigate('/dashboard')
    } catch (err) {
      toast.error(err?.response?.data?.detail || 'Login failed')
    } finally {
      setLoading(false)
    }
  }

  const handleForgot = async (e) => {
    e.preventDefault()
    if (!forgotEmail) { toast.error('Enter your email'); return }
    setForgotLoading(true)
    try {
      await authService.forgotPassword(forgotEmail)
      setForgotSent(true)
      toast.success('Reset link sent! Check your email.')
    } catch (err) {
      toast.error(err?.response?.data?.detail || 'Failed to send reset email')
    } finally {
      setForgotLoading(false)
    }
  }

  return (
    <div className="auth-page">
      <div className="auth-left">
        <div className="auth-left__content">
          <div className="auth-left__logo"><Sparkles size={28} /></div>
          <h1 className="auth-left__title">Texlify</h1>
          <p className="auth-left__subtitle">
            AI-powered Word document editor. Edit and format documents
            using natural language commands.
          </p>
          <div className="auth-left__features">
            {[
              '100+ formatting actions',
              'SPPU, IEEE, APA, MLA formats',
              'Live preview as you edit',
              'Paragraph-level selection',
              'Dark mode + mobile ready',
            ].map((f, i) => (
              <div key={i} className="auth-left__feature">
                <span className="auth-left__feature-dot" />{f}
              </div>
            ))}
          </div>
        </div>
      </div>

      <div className="auth-right">
        <div className="auth-form-container">
          {!showForgot ? (
            <>
              <h2 className="auth-form__title">Welcome back</h2>
              <p className="auth-form__subtitle">Sign in to your Texlify account</p>
              <form className="auth-form" onSubmit={handleLogin}>
                <div className="auth-field">
                  <label className="auth-label">Email address</label>
                  <div className="auth-input-wrapper">
                    <Mail size={16} className="auth-input-icon" />
                    <input className="auth-input" type="email"
                      placeholder="you@example.com" value={email}
                      onChange={(e) => setEmail(e.target.value)} autoFocus />
                  </div>
                </div>
                <div className="auth-field">
                  <div className="auth-label-row">
                    <label className="auth-label">Password</label>
                    <button type="button" className="auth-forgot-link"
                      onClick={() => setShowForgot(true)}>
                      Forgot password?
                    </button>
                  </div>
                  <div className="auth-input-wrapper">
                    <Lock size={16} className="auth-input-icon" />
                    <input className="auth-input"
                      type={showPwd ? 'text' : 'password'}
                      placeholder="Your password" value={password}
                      onChange={(e) => setPassword(e.target.value)} />
                    <button type="button" className="auth-eye-btn"
                      onClick={() => setShowPwd(!showPwd)}>
                      {showPwd ? <EyeOff size={15} /> : <Eye size={15} />}
                    </button>
                  </div>
                </div>
                <button type="submit" className="auth-submit-btn" disabled={loading}>
                  {loading ? 'Signing in...' : <><span>Sign in</span><ArrowRight size={16} /></>}
                </button>
              </form>
              <p className="auth-switch">
                Don't have an account?{' '}
                <Link to="/register" className="auth-switch-link">Create one</Link>
              </p>
            </>
          ) : (
            <>
              <button className="auth-back-btn"
                onClick={() => { setShowForgot(false); setForgotSent(false) }}>
                ← Back to login
              </button>
              <h2 className="auth-form__title">Reset password</h2>
              <p className="auth-form__subtitle">
                Enter your email and we'll send you a reset link
              </p>
              {forgotSent ? (
                <div className="auth-success-box">
                  <div className="auth-success-icon">✓</div>
                  <h3>Check your email!</h3>
                  <p>
                    We sent a reset link to <strong>{forgotEmail}</strong>.
                    Click the link to reset your password. Expires in 1 hour.
                  </p>
                </div>
              ) : (
                <form className="auth-form" onSubmit={handleForgot}>
                  <div className="auth-field">
                    <label className="auth-label">Email address</label>
                    <div className="auth-input-wrapper">
                      <Mail size={16} className="auth-input-icon" />
                      <input className="auth-input" type="email"
                        placeholder="you@example.com" value={forgotEmail}
                        onChange={(e) => setForgotEmail(e.target.value)} autoFocus />
                    </div>
                  </div>
                  <button type="submit" className="auth-submit-btn" disabled={forgotLoading}>
                    {forgotLoading ? 'Sending...' : <><span>Send reset link</span><ArrowRight size={16} /></>}
                  </button>
                </form>
              )}
            </>
          )}
        </div>
      </div>
    </div>
  )
}

export default Login
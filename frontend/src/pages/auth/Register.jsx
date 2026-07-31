import { useState } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import { Mail, Lock, User, Eye, EyeOff, Sparkles, ArrowRight } from 'lucide-react'
import { authService } from '../../services/authService'
import useAuthStore from '../../store/authStore'
import { toast } from 'react-hot-toast'
import './Login.css'

const Register = () => {
  const [fullName, setFullName]   = useState('')
  const [email, setEmail]         = useState('')
  const [password, setPassword]   = useState('')
  const [confirm, setConfirm]     = useState('')
  const [showPwd, setShowPwd]     = useState(false)
  const [loading, setLoading]     = useState(false)
  const { setAuth }               = useAuthStore()
  const navigate                  = useNavigate()

  const strength = (pwd) => {
    let s = 0
    if (pwd.length >= 8)                     s++
    if (/[A-Z]/.test(pwd))                   s++
    if (/[a-z]/.test(pwd))                   s++
    if (/\d/.test(pwd))                      s++
    if (/[!@#$%^&*(),.?":{}|<>]/.test(pwd)) s++
    return s
  }

  const strengthColor = ['','#EF4444','#F59E0B','#EAB308','#10B981','#059669']
  const strengthLabel = ['','Very Weak','Weak','Fair','Strong','Very Strong']
  const sc = strength(password)

  const handleRegister = async (e) => {
    e.preventDefault()
    if (!fullName || !email || !password || !confirm) {
      toast.error('Fill in all fields'); return
    }
    if (password !== confirm) { toast.error('Passwords do not match'); return }
    if (sc < 3) { toast.error('Password is too weak'); return }
    setLoading(true)
    try {
      await authService.register({ full_name: fullName, email, password })
      const data = await authService.login(email, password)
      setAuth(data.user, data.access_token, data.refresh_token)
      toast.success(`Welcome to Texlify, ${fullName.split(' ')[0]}!`)
      navigate('/dashboard')
    } catch (err) {
      toast.error(err?.response?.data?.detail || 'Registration failed')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="auth-page">
      <div className="auth-left">
        <div className="auth-left__content">
          <div className="auth-left__logo"><Sparkles size={28} /></div>
          <h1 className="auth-left__title">Texlify</h1>
          <p className="auth-left__subtitle">
            Create your account and start editing Word documents
            with the power of AI.
          </p>
          <div className="auth-left__features">
            {[
              'Free to use','No credit card required',
              'Upload any .docx file',
              'AI-powered formatting',
              '100+ Word actions',
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
          <h2 className="auth-form__title">Create account</h2>
          <p className="auth-form__subtitle">Join Texlify — it's free</p>

          <form className="auth-form" onSubmit={handleRegister}>
            <div className="auth-field">
              <label className="auth-label">Full Name</label>
              <div className="auth-input-wrapper">
                <User size={16} className="auth-input-icon" />
                <input className="auth-input" type="text"
                  placeholder="Your full name" value={fullName}
                  onChange={(e) => setFullName(e.target.value)} autoFocus />
              </div>
            </div>
            <div className="auth-field">
              <label className="auth-label">Email address</label>
              <div className="auth-input-wrapper">
                <Mail size={16} className="auth-input-icon" />
                <input className="auth-input" type="email"
                  placeholder="you@example.com" value={email}
                  onChange={(e) => setEmail(e.target.value)} />
              </div>
            </div>
            <div className="auth-field">
              <label className="auth-label">Password</label>
              <div className="auth-input-wrapper">
                <Lock size={16} className="auth-input-icon" />
                <input className="auth-input"
                  type={showPwd ? 'text' : 'password'}
                  placeholder="Min 8 characters" value={password}
                  onChange={(e) => setPassword(e.target.value)} />
                <button type="button" className="auth-eye-btn"
                  onClick={() => setShowPwd(!showPwd)}>
                  {showPwd ? <EyeOff size={15} /> : <Eye size={15} />}
                </button>
              </div>
              {password && (
                <div style={{ display:'flex', alignItems:'center', gap:8, marginTop:4 }}>
                  <div style={{ display:'flex', gap:3, flex:1 }}>
                    {[1,2,3,4,5].map(i => (
                      <div key={i} style={{
                        height:4, flex:1, borderRadius:2,
                        background: i<=sc ? strengthColor[sc] : 'var(--border-light)',
                        transition:'background 0.3s'
                      }} />
                    ))}
                  </div>
                  <span style={{ fontSize:11, fontWeight:600, color:strengthColor[sc] }}>
                    {strengthLabel[sc]}
                  </span>
                </div>
              )}
            </div>
            <div className="auth-field">
              <label className="auth-label">Confirm Password</label>
              <div className="auth-input-wrapper">
                <Lock size={16} className="auth-input-icon" />
                <input className="auth-input" type="password"
                  placeholder="Confirm your password" value={confirm}
                  onChange={(e) => setConfirm(e.target.value)} />
              </div>
              {confirm && password !== confirm && (
                <p style={{ color:'var(--color-error)', fontSize:12, marginTop:4 }}>
                  Passwords do not match
                </p>
              )}
            </div>
            <button type="submit" className="auth-submit-btn" disabled={loading}>
              {loading ? 'Creating account...' : <><span>Create Account</span><ArrowRight size={16} /></>}
            </button>
          </form>

          <p className="auth-switch">
            Already have an account?{' '}
            <Link to="/login" className="auth-switch-link">Sign in</Link>
          </p>
        </div>
      </div>
    </div>
  )
}

export default Register
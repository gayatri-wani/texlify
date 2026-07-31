import { useState, useEffect } from 'react'
import { useNavigate, useSearchParams, Link } from 'react-router-dom'
import { Lock, Eye, EyeOff, Sparkles } from 'lucide-react'
import { authService } from '../../services/authService'
import { toast } from 'react-hot-toast'
import './Login.css'

const ResetPassword = () => {
  const [searchParams]              = useSearchParams()
  const [newPwd, setNewPwd]         = useState('')
  const [confirmPwd, setConfirmPwd] = useState('')
  const [showNew, setShowNew]       = useState(false)
  const [loading, setLoading]       = useState(false)
  const [done, setDone]             = useState(false)
  const navigate                    = useNavigate()
  const token                       = searchParams.get('token')

  useEffect(() => {
    if (!token) { toast.error('Invalid reset link'); navigate('/login') }
  }, [token])

  const handleReset = async (e) => {
    e.preventDefault()
    if (!newPwd || !confirmPwd) { toast.error('Fill in all fields'); return }
    if (newPwd !== confirmPwd)  { toast.error('Passwords do not match'); return }
    if (newPwd.length < 8)      { toast.error('Password too short'); return }
    setLoading(true)
    try {
      await authService.resetPassword(token, newPwd)
      setDone(true)
      toast.success('Password reset successfully!')
    } catch (err) {
      toast.error(err?.response?.data?.detail || 'Reset failed. Link may have expired.')
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
          <p className="auth-left__subtitle">Create a new secure password.</p>
        </div>
      </div>
      <div className="auth-right">
        <div className="auth-form-container">
          {done ? (
            <div className="auth-success-box">
              <div className="auth-success-icon">✓</div>
              <h3>Password reset!</h3>
              <p>Your password has been updated successfully.</p>
              <Link to="/login" className="auth-submit-btn"
                style={{ display:'flex', justifyContent:'center',
                         marginTop:16, textDecoration:'none' }}>
                Go to login
              </Link>
            </div>
          ) : (
            <>
              <h2 className="auth-form__title">Create new password</h2>
              <p className="auth-form__subtitle">Choose a strong password</p>
              <form className="auth-form" onSubmit={handleReset}>
                <div className="auth-field">
                  <label className="auth-label">New Password</label>
                  <div className="auth-input-wrapper">
                    <Lock size={16} className="auth-input-icon" />
                    <input className="auth-input"
                      type={showNew ? 'text' : 'password'}
                      placeholder="New password (min 8 chars)"
                      value={newPwd}
                      onChange={(e) => setNewPwd(e.target.value)} autoFocus />
                    <button type="button" className="auth-eye-btn"
                      onClick={() => setShowNew(!showNew)}>
                      {showNew ? <EyeOff size={15} /> : <Eye size={15} />}
                    </button>
                  </div>
                </div>
                <div className="auth-field">
                  <label className="auth-label">Confirm New Password</label>
                  <div className="auth-input-wrapper">
                    <Lock size={16} className="auth-input-icon" />
                    <input className="auth-input" type="password"
                      placeholder="Confirm new password"
                      value={confirmPwd}
                      onChange={(e) => setConfirmPwd(e.target.value)} />
                  </div>
                  {confirmPwd && newPwd !== confirmPwd && (
                    <p style={{ color:'var(--color-error)', fontSize:12, marginTop:4 }}>
                      Passwords do not match
                    </p>
                  )}
                </div>
                <button type="submit" className="auth-submit-btn"
                  disabled={loading || newPwd !== confirmPwd || newPwd.length < 8}>
                  {loading ? 'Resetting...' : 'Reset Password'}
                </button>
              </form>
            </>
          )}
        </div>
      </div>
    </div>
  )
}

export default ResetPassword
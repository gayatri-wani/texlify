import { useState, useEffect } from 'react'
import { useNavigate, useSearchParams, Link } from 'react-router-dom'
import { Lock, Eye, EyeOff, Sparkles, CheckCircle } from 'lucide-react'
import { authService } from '../../services/authService'
import { toast } from 'react-hot-toast'
import './Login.css'

const ResetPassword = () => {
  const [searchParams]              = useSearchParams()
  const [newPwd, setNewPwd]         = useState('')
  const [confirmPwd, setConfirmPwd] = useState('')
  const [showNew, setShowNew]       = useState(false)
  const [showConfirm, setShowConfirm] = useState(false)
  const [loading, setLoading]       = useState(false)
  const [done, setDone]             = useState(false)
  const navigate                    = useNavigate()
  const token                       = searchParams.get('token')

  useEffect(() => {
    if (!token) {
      toast.error('Invalid reset link')
      navigate('/login')
    }
  }, [token])

  const passwordStrength = (pwd) => {
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
  const pwdScore      = passwordStrength(newPwd)

  const handleReset = async (e) => {
    e.preventDefault()
    if (!newPwd || !confirmPwd) { toast.error('Fill in all fields'); return }
    if (newPwd !== confirmPwd)  { toast.error('Passwords do not match'); return }
    if (pwdScore < 3)           { toast.error('Password is too weak'); return }
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
          <p className="auth-left__subtitle">
            Create a new secure password for your account.
          </p>
        </div>
      </div>

      <div className="auth-right">
        <div className="auth-form-container">
          {done ? (
            <div className="auth-success-box">
              <div className="auth-success-icon">
                <CheckCircle size={32} color="#10B981" />
              </div>
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
              <p className="auth-form__subtitle">
                Choose a strong password for your account
              </p>

              <form className="auth-form" onSubmit={handleReset}>
                <div className="auth-field">
                  <label className="auth-label">New Password</label>
                  <div className="auth-input-wrapper">
                    <Lock size={16} className="auth-input-icon" />
                    <input
                      className="auth-input"
                      type={showNew ? 'text' : 'password'}
                      placeholder="New password"
                      value={newPwd}
                      onChange={(e) => setNewPwd(e.target.value)}
                      autoFocus
                    />
                    <button type="button" className="auth-eye-btn"
                            onClick={() => setShowNew(!showNew)}>
                      {showNew ? <EyeOff size={15} /> : <Eye size={15} />}
                    </button>
                  </div>
                  {newPwd && (
                    <div style={{ display:'flex', alignItems:'center',
                                  gap:8, marginTop:6 }}>
                      <div style={{ display:'flex', gap:3, flex:1 }}>
                        {[1,2,3,4,5].map(i => (
                          <div key={i} style={{
                            height:4, flex:1, borderRadius:2,
                            background: i <= pwdScore
                              ? strengthColor[pwdScore]
                              : 'var(--border-light)',
                            transition: 'background 0.3s'
                          }} />
                        ))}
                      </div>
                      <span style={{
                        fontSize:11, fontWeight:600,
                        color: strengthColor[pwdScore]
                      }}>
                        {strengthLabel[pwdScore]}
                      </span>
                    </div>
                  )}
                </div>

                <div className="auth-field">
                  <label className="auth-label">Confirm New Password</label>
                  <div className="auth-input-wrapper">
                    <Lock size={16} className="auth-input-icon" />
                    <input
                      className="auth-input"
                      type={showConfirm ? 'text' : 'password'}
                      placeholder="Confirm new password"
                      value={confirmPwd}
                      onChange={(e) => setConfirmPwd(e.target.value)}
                    />
                    <button type="button" className="auth-eye-btn"
                            onClick={() => setShowConfirm(!showConfirm)}>
                      {showConfirm ? <EyeOff size={15} /> : <Eye size={15} />}
                    </button>
                  </div>
                  {confirmPwd && newPwd !== confirmPwd && (
                    <p style={{ color:'var(--color-error)',
                                fontSize:12, marginTop:4 }}>
                      Passwords do not match
                    </p>
                  )}
                </div>

                <button
                  type="submit"
                  className="auth-submit-btn"
                  disabled={loading || pwdScore < 3 || newPwd !== confirmPwd}
                >
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
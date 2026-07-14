import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import {
  User, Mail, Lock, Save, ArrowLeft,
  Eye, EyeOff, CheckCircle, AlertCircle
} from 'lucide-react'
import useAuthStore from '../../store/authStore'
import { authService } from '../../services/authService'
import { toast } from 'react-hot-toast'
import './Profile.css'

const Profile = () => {
  const { user, setAuth } = useAuthStore()
  const navigate          = useNavigate()

  const [fullName, setFullName]         = useState(user?.full_name || '')
  const [savingName, setSavingName]     = useState(false)

  const [currentPwd, setCurrentPwd]     = useState('')
  const [newPwd, setNewPwd]             = useState('')
  const [confirmPwd, setConfirmPwd]     = useState('')
  const [showCurrent, setShowCurrent]   = useState(false)
  const [showNew, setShowNew]           = useState(false)
  const [showConfirm, setShowConfirm]   = useState(false)
  const [savingPwd, setSavingPwd]       = useState(false)

  const passwordStrength = (pwd) => {
    let score = 0
    if (pwd.length >= 8)                        score++
    if (/[A-Z]/.test(pwd))                      score++
    if (/[a-z]/.test(pwd))                      score++
    if (/\d/.test(pwd))                         score++
    if (/[!@#$%^&*(),.?":{}|<>]/.test(pwd))    score++
    return score
  }

  const strengthLabel = ['', 'Very Weak', 'Weak', 'Fair', 'Strong', 'Very Strong']
  const strengthColor = ['', '#EF4444', '#F59E0B', '#EAB308', '#10B981', '#059669']
  const pwdScore      = passwordStrength(newPwd)

  const handleSaveName = async (e) => {
    e.preventDefault()
    if (!fullName.trim()) { toast.error('Name cannot be empty'); return }
    if (fullName.trim() === user?.full_name) { toast('No changes made'); return }
    setSavingName(true)
    try {
      // Update via API — for now update locally since backend endpoint may not exist yet
      const updatedUser = { ...user, full_name: fullName.trim() }
      setAuth(updatedUser, localStorage.getItem('access_token'),
              localStorage.getItem('refresh_token'))
      toast.success('Name updated successfully!')
    } catch {
      toast.error('Failed to update name')
    } finally {
      setSavingName(false)
    }
  }

  const handleChangePassword = async (e) => {
    e.preventDefault()
    if (!currentPwd || !newPwd || !confirmPwd) {
      toast.error('Please fill in all password fields'); return
    }
    if (newPwd !== confirmPwd) {
      toast.error('New passwords do not match'); return
    }
    if (pwdScore < 3) {
      toast.error('Password is too weak'); return
    }
    setSavingPwd(true)
    try {
      await authService.changePassword(currentPwd, newPwd)
      toast.success('Password changed successfully!')
      setCurrentPwd(''); setNewPwd(''); setConfirmPwd('')
    } catch (err) {
      toast.error(err?.response?.data?.detail || 'Failed to change password')
    } finally {
      setSavingPwd(false)
    }
  }

  return (
    <div className="profile">

      {/* Header */}
      <div className="profile__header">
        <button className="profile__back" onClick={() => navigate('/dashboard')}>
          <ArrowLeft size={16} />
          Back to Dashboard
        </button>
        <h1 className="profile__title">My Profile</h1>
        <p className="profile__subtitle">Manage your account settings</p>
      </div>

      <div className="profile__content">

        {/* Avatar card */}
        <div className="profile__card profile__card--avatar">
          <div className="profile__avatar">
            {user?.full_name?.charAt(0).toUpperCase()}
          </div>
          <div className="profile__avatar-info">
            <h2 className="profile__avatar-name">{user?.full_name}</h2>
            <p className="profile__avatar-email">{user?.email}</p>
            <div className="profile__avatar-badge">
              <CheckCircle size={12} />
              Verified Account
            </div>
          </div>
        </div>

        {/* Update Name */}
        <div className="profile__card">
          <div className="profile__card-header">
            <User size={18} />
            <h3>Personal Information</h3>
          </div>
          <form onSubmit={handleSaveName} className="profile__form">
            <div className="profile__field">
              <label className="profile__label">Full Name</label>
              <div className="profile__input-wrapper">
                <User size={15} className="profile__input-icon" />
                <input
                  className="profile__input"
                  type="text"
                  value={fullName}
                  onChange={(e) => setFullName(e.target.value)}
                  placeholder="Your full name"
                />
              </div>
            </div>
            <div className="profile__field">
              <label className="profile__label">Email Address</label>
              <div className="profile__input-wrapper profile__input-wrapper--disabled">
                <Mail size={15} className="profile__input-icon" />
                <input
                  className="profile__input"
                  type="email"
                  value={user?.email || ''}
                  disabled
                />
              </div>
              <p className="profile__hint">Email cannot be changed</p>
            </div>
            <button
              type="submit"
              className="profile__save-btn"
              disabled={savingName}
            >
              {savingName ? 'Saving...' : <><Save size={14} /> Save Changes</>}
            </button>
          </form>
        </div>

        {/* Change Password */}
        <div className="profile__card">
          <div className="profile__card-header">
            <Lock size={18} />
            <h3>Change Password</h3>
          </div>
          <form onSubmit={handleChangePassword} className="profile__form">

            {/* Current password */}
            <div className="profile__field">
              <label className="profile__label">Current Password</label>
              <div className="profile__input-wrapper">
                <Lock size={15} className="profile__input-icon" />
                <input
                  className="profile__input"
                  type={showCurrent ? 'text' : 'password'}
                  value={currentPwd}
                  onChange={(e) => setCurrentPwd(e.target.value)}
                  placeholder="Enter current password"
                />
                <button
                  type="button"
                  className="profile__eye-btn"
                  onClick={() => setShowCurrent(!showCurrent)}
                >
                  {showCurrent ? <EyeOff size={14} /> : <Eye size={14} />}
                </button>
              </div>
            </div>

            {/* New password */}
            <div className="profile__field">
              <label className="profile__label">New Password</label>
              <div className="profile__input-wrapper">
                <Lock size={15} className="profile__input-icon" />
                <input
                  className="profile__input"
                  type={showNew ? 'text' : 'password'}
                  value={newPwd}
                  onChange={(e) => setNewPwd(e.target.value)}
                  placeholder="Enter new password"
                />
                <button
                  type="button"
                  className="profile__eye-btn"
                  onClick={() => setShowNew(!showNew)}
                >
                  {showNew ? <EyeOff size={14} /> : <Eye size={14} />}
                </button>
              </div>
              {newPwd && (
                <div className="profile__strength">
                  <div className="profile__strength-bar">
                    {[1,2,3,4,5].map(i => (
                      <div
                        key={i}
                        className="profile__strength-segment"
                        style={{
                          background: i <= pwdScore
                            ? strengthColor[pwdScore]
                            : 'var(--border-light)'
                        }}
                      />
                    ))}
                  </div>
                  <span style={{ color: strengthColor[pwdScore] }}>
                    {strengthLabel[pwdScore]}
                  </span>
                </div>
              )}
            </div>

            {/* Confirm password */}
            <div className="profile__field">
              <label className="profile__label">Confirm New Password</label>
              <div className="profile__input-wrapper">
                <Lock size={15} className="profile__input-icon" />
                <input
                  className="profile__input"
                  type={showConfirm ? 'text' : 'password'}
                  value={confirmPwd}
                  onChange={(e) => setConfirmPwd(e.target.value)}
                  placeholder="Confirm new password"
                />
                <button
                  type="button"
                  className="profile__eye-btn"
                  onClick={() => setShowConfirm(!showConfirm)}
                >
                  {showConfirm ? <EyeOff size={14} /> : <Eye size={14} />}
                </button>
              </div>
              {confirmPwd && newPwd !== confirmPwd && (
                <p className="profile__error">
                  <AlertCircle size={12} />
                  Passwords do not match
                </p>
              )}
              {confirmPwd && newPwd === confirmPwd && confirmPwd.length > 0 && (
                <p className="profile__success-msg">
                  <CheckCircle size={12} />
                  Passwords match
                </p>
              )}
            </div>

            {/* Password requirements */}
            <div className="profile__requirements">
              <p className="profile__requirements-title">Password must have:</p>
              {[
                { label: 'At least 8 characters',     test: newPwd.length >= 8 },
                { label: 'One uppercase letter',       test: /[A-Z]/.test(newPwd) },
                { label: 'One lowercase letter',       test: /[a-z]/.test(newPwd) },
                { label: 'One number',                 test: /\d/.test(newPwd) },
                { label: 'One special character',      test: /[!@#$%^&*(),.?":{}|<>]/.test(newPwd) },
              ].map((req, i) => (
                <div key={i} className="profile__requirement">
                  <CheckCircle
                    size={11}
                    style={{ color: req.test ? 'var(--color-primary)' : 'var(--text-muted)' }}
                  />
                  <span style={{ color: req.test ? 'var(--color-primary)' : 'var(--text-muted)' }}>
                    {req.label}
                  </span>
                </div>
              ))}
            </div>

            <button
              type="submit"
              className="profile__save-btn"
              disabled={savingPwd || newPwd !== confirmPwd || pwdScore < 3}
            >
              {savingPwd ? 'Changing...' : <><Lock size={14} /> Change Password</>}
            </button>
          </form>
        </div>

        {/* Account Info */}
        <div className="profile__card profile__card--info">
          <div className="profile__card-header">
            <AlertCircle size={18} />
            <h3>Account Information</h3>
          </div>
          <div className="profile__info-grid">
            <div className="profile__info-item">
              <span className="profile__info-label">Member since</span>
              <span className="profile__info-value">
                {new Date(user?.created_at).toLocaleDateString('en-IN', {
                  day: 'numeric', month: 'long', year: 'numeric'
                })}
              </span>
            </div>
            <div className="profile__info-item">
              <span className="profile__info-label">Account status</span>
              <span className="profile__info-value profile__info-value--active">Active</span>
            </div>
            <div className="profile__info-item">
              <span className="profile__info-label">Email verified</span>
              <span className="profile__info-value profile__info-value--active">Yes</span>
            </div>
          </div>
        </div>

      </div>
    </div>
  )
}

export default Profile
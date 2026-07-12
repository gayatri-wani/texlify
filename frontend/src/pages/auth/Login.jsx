import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { Mail, Lock, Eye, EyeOff } from 'lucide-react'
import { toast } from 'react-hot-toast'
import Input from '../../components/ui/Input'
import Button from '../../components/ui/Button'
import { authService } from '../../services/authService'
import useAuthStore from '../../store/authStore'
import './Login.css'

const Login = () => {
  const navigate = useNavigate()
  const { setAuth } = useAuthStore()
  const [loading, setLoading] = useState(false)
  const [showPassword, setShowPassword] = useState(false)
  const [form, setForm] = useState({ email: '', password: '' })
  const [errors, setErrors] = useState({})

  const validate = () => {
    const newErrors = {}
    if (!form.email.trim()) newErrors.email = 'Email is required'
    if (!form.password)     newErrors.password = 'Password is required'
    setErrors(newErrors)
    return Object.keys(newErrors).length === 0
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    if (!validate()) return
    setLoading(true)
    try {
      const data = await authService.login(form)
      setAuth(data.user, data.access_token, data.refresh_token)
      toast.success(`Welcome back, ${data.user.full_name}!`)
      navigate('/dashboard')
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Login failed')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="auth-page">

      <div className="auth-left">
        <div className="auth-left__inner">
          <div className="auth-logo">
            <div className="auth-logo__icon">T</div>
            <span className="auth-logo__text">Texlify</span>
          </div>
          <h1 className="auth-left__heading">
            Edit Documents<br />with the Power of AI
          </h1>
          <p className="auth-left__subtext">
            Type a command. Watch your document transform instantly.
            No clicking. No menus. Just natural language.
          </p>
          <div className="auth-features">
            {[
              'Format entire documents in seconds',
              'Insert tables, images and watermarks',
              'Convert to SPPU, APA, IEEE formats',
              'Undo any change instantly',
            ].map((f, i) => (
              <div className="auth-feature-item" key={i}>
                <span className="auth-feature-dot" />
                {f}
              </div>
            ))}
          </div>
        </div>
      </div>

      <div className="auth-right">
        <div className="auth-card animate-fadeInUp">

          <div className="auth-card__header">
            <h2 className="auth-card__title">Welcome back</h2>
            <p className="auth-card__subtitle">Sign in to your Texlify account</p>
          </div>

          <form className="auth-form" onSubmit={handleSubmit}>

            <Input
              label="Email Address"
              type="email"
              placeholder="you@example.com"
              icon={Mail}
              value={form.email}
              onChange={(e) => setForm({ ...form, email: e.target.value })}
              error={errors.email}
            />

            <div className="auth-password-group">
              <Input
                label="Password"
                type={showPassword ? 'text' : 'password'}
                placeholder="Enter your password"
                icon={Lock}
                value={form.password}
                onChange={(e) => setForm({ ...form, password: e.target.value })}
                error={errors.password}
              />
              <div className="auth-password-actions">
                <button
                  type="button"
                  className="auth-toggle-password"
                  onClick={() => setShowPassword(!showPassword)}
                >
                  {showPassword ? <EyeOff size={13} /> : <Eye size={13} />}
                  {showPassword ? 'Hide' : 'Show'}
                </button>
                <Link to="/forgot-password" className="auth-forgot-link">
                  Forgot password?
                </Link>
              </div>
            </div>

            <Button type="submit" loading={loading} size="md">
              Sign In
            </Button>

          </form>

          <p className="auth-card__footer">
            Don't have an account?{' '}
            <Link to="/register" className="auth-link">Create one free</Link>
          </p>

        </div>
      </div>

    </div>
  )
}

export default Login
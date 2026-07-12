import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { User, Mail, Lock, Eye, EyeOff } from 'lucide-react'
import { toast } from 'react-hot-toast'
import Input from '../../components/ui/Input'
import Button from '../../components/ui/Button'
import { authService } from '../../services/authService'
import './Register.css'

const Register = () => {
  const navigate = useNavigate()
  const [loading, setLoading] = useState(false)
  const [showPassword, setShowPassword] = useState(false)
  const [form, setForm] = useState({ full_name: '', email: '', password: '' })
  const [errors, setErrors] = useState({})

  const validate = () => {
    const newErrors = {}
    if (!form.full_name.trim())        newErrors.full_name = 'Full name is required'
    if (!form.email.trim())            newErrors.email = 'Email is required'
    if (!form.password)                newErrors.password = 'Password is required'
    else if (form.password.length < 8) newErrors.password = 'Min 8 characters required'
    setErrors(newErrors)
    return Object.keys(newErrors).length === 0
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    if (!validate()) return
    setLoading(true)
    try {
      await authService.register(form)
      toast.success('Account created! Please sign in.')
      navigate('/login')
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Registration failed')
    } finally {
      setLoading(false)
    }
  }

  const getPasswordStrength = () => {
    const p = form.password
    if (!p) return null
    let score = 0
    if (p.length >= 8)                       score++
    if (/[A-Z]/.test(p))                     score++
    if (/[0-9]/.test(p))                     score++
    if (/[!@#$%^&*(),.?":{}|<>]/.test(p))   score++
    if (score <= 1) return { label: 'Weak',   cls: 'strength--weak',   width: '25%'  }
    if (score === 2) return { label: 'Fair',  cls: 'strength--fair',   width: '50%'  }
    if (score === 3) return { label: 'Good',  cls: 'strength--good',   width: '75%'  }
    return               { label: 'Strong', cls: 'strength--strong', width: '100%' }
  }

  const strength = getPasswordStrength()

  return (
    <div className="auth-page">

      <div className="auth-left">
        <div className="auth-left__inner">
          <div className="auth-logo">
            <div className="auth-logo__icon">T</div>
            <span className="auth-logo__text">Texlify</span>
          </div>
          <h1 className="auth-left__heading">
            Your AI Document<br />Editor Awaits
          </h1>
          <p className="auth-left__subtext">
            Join thousands of students, researchers and professionals
            who edit documents 10× faster with Texlify.
          </p>
          <div className="register-stats">
            {[
              { value: '50+',  label: 'Document actions' },
              { value: '10×',  label: 'Faster editing'   },
              { value: '100%', label: 'Free to start'    },
            ].map((s, i) => (
              <div className="register-stat" key={i}>
                <span className="register-stat__value">{s.value}</span>
                <span className="register-stat__label">{s.label}</span>
              </div>
            ))}
          </div>
        </div>
      </div>

      <div className="auth-right">
        <div className="auth-card animate-fadeInUp">

          <div className="auth-card__header">
            <h2 className="auth-card__title">Create your account</h2>
            <p className="auth-card__subtitle">Start editing documents with AI — it's free</p>
          </div>

          <form className="auth-form" onSubmit={handleSubmit}>

            <Input
              label="Full Name"
              type="text"
              placeholder="John Doe"
              icon={User}
              value={form.full_name}
              onChange={(e) => setForm({ ...form, full_name: e.target.value })}
              error={errors.full_name}
            />

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
                placeholder="Min 8 chars, uppercase, number, symbol"
                icon={Lock}
                value={form.password}
                onChange={(e) => setForm({ ...form, password: e.target.value })}
                error={errors.password}
              />

              {strength && (
                <div className="strength-bar-wrapper">
                  <div className="strength-bar-track">
                    <div
                      className={`strength-bar-fill ${strength.cls}`}
                      style={{ width: strength.width }}
                    />
                  </div>
                  <span className={`strength-label ${strength.cls}`}>
                    {strength.label}
                  </span>
                </div>
              )}

              <button
                type="button"
                className="auth-toggle-password"
                onClick={() => setShowPassword(!showPassword)}
              >
                {showPassword ? <EyeOff size={13} /> : <Eye size={13} />}
                {showPassword ? 'Hide' : 'Show'} password
              </button>
            </div>

            <Button type="submit" loading={loading} size="md">
              Create Account
            </Button>

          </form>

          <p className="auth-card__footer">
            Already have an account?{' '}
            <Link to="/login" className="auth-link">Sign in</Link>
          </p>

        </div>
      </div>

    </div>
  )
}

export default Register
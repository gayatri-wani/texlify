import { useNavigate, useLocation } from 'react-router-dom'
import { LogOut, User, Moon, Sun, FileText, Sparkles } from 'lucide-react'
import useAuthStore from '../../store/authStore'
import { authService } from '../../services/authService'
import { useDarkMode } from '../../hooks/useDarkMode'
import { toast } from 'react-hot-toast'
import './Sidebar.css'

const Sidebar = () => {
  const { user, logout }    = useAuthStore()
  const { isDark, toggle }  = useDarkMode()
  const navigate            = useNavigate()
  const location            = useLocation()

  const handleLogout = async () => {
    try {
      await authService.logout()
    } catch { }
    logout()
    navigate('/login')
    toast.success('Logged out')
  }

  return (
    <aside className="sidebar">
      {/* Logo */}
      <div className="sidebar__logo">
        <div className="sidebar__logo-icon">
          <Sparkles size={18} />
        </div>
        <span className="sidebar__logo-text">Texlify</span>
      </div>

      {/* Nav */}
      <nav className="sidebar__nav">
        <button
          className={`sidebar__nav-item ${location.pathname === '/dashboard' ? 'sidebar__nav-item--active' : ''}`}
          onClick={() => navigate('/dashboard')}
        >
          <FileText size={16} />
          <span>Documents</span>
        </button>
        <button
          className={`sidebar__nav-item ${location.pathname === '/profile' ? 'sidebar__nav-item--active' : ''}`}
          onClick={() => navigate('/profile')}
        >
          <User size={16} />
          <span>Profile</span>
        </button>
      </nav>

      {/* Bottom */}
      <div className="sidebar__bottom">
        {/* Dark mode toggle */}
        <button className="sidebar__dark-toggle" onClick={toggle}>
          {isDark ? <Sun size={15} /> : <Moon size={15} />}
          <span>{isDark ? 'Light Mode' : 'Dark Mode'}</span>
        </button>

        {/* User info */}
        <div className="sidebar__user">
          <div className="sidebar__user-avatar">
            {user?.full_name?.charAt(0).toUpperCase()}
          </div>
          <div className="sidebar__user-info">
            <p className="sidebar__user-name">
              {user?.full_name?.split(' ')[0]}
            </p>
            <p className="sidebar__user-email">{user?.email}</p>
          </div>
        </div>

        {/* Logout */}
        <button className="sidebar__logout" onClick={handleLogout}>
          <LogOut size={15} />
          <span>Logout</span>
        </button>
      </div>
    </aside>
  )
}

export default Sidebar
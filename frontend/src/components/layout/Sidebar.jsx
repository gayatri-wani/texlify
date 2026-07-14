import { useState } from 'react'
import { useNavigate, useLocation } from 'react-router-dom'
import {
  FileText, LogOut, ChevronLeft, ChevronRight,
  Sparkles, User, Moon, Sun
} from 'lucide-react'
import useAuthStore from '../../store/authStore'
import { authService } from '../../services/authService'
import { useDarkMode } from '../../hooks/useDarkMode'
import { toast } from 'react-hot-toast'
import './Sidebar.css'

const NAV_ITEMS = [
  { icon: FileText, label: 'Documents', path: '/dashboard' },
  { icon: User,     label: 'Profile',   path: '/profile'   },
]

const Sidebar = () => {
  const [collapsed, setCollapsed] = useState(false)
  const { user, logout }          = useAuthStore()
  const navigate                  = useNavigate()
  const location                  = useLocation()
  const { isDark, toggle }        = useDarkMode()

  const handleLogout = async () => {
    try {
      await authService.logout()
    } catch { /* ignore */ }
    logout()
    navigate('/login')
    toast.success('Logged out successfully')
  }

  return (
    <aside className={`sidebar ${collapsed ? 'sidebar--collapsed' : ''}`}>

      {/* Logo */}
      <div className="sidebar__logo">
        <div className="sidebar__logo-icon">
          <Sparkles size={18} />
        </div>
        {!collapsed && (
          <div className="sidebar__logo-text">
            <span className="sidebar__logo-name">Texlify</span>
            <span className="sidebar__logo-tag">AI Editor</span>
          </div>
        )}
      </div>

      {/* Nav items */}
      <nav className="sidebar__nav">
        {NAV_ITEMS.map((item) => {
          const Icon    = item.icon
          const active  = location.pathname === item.path
          return (
            <button
              key={item.path}
              className={`sidebar__nav-item ${active ? 'sidebar__nav-item--active' : ''}`}
              onClick={() => navigate(item.path)}
              title={collapsed ? item.label : ''}
            >
              <Icon size={18} />
              {!collapsed && <span>{item.label}</span>}
            </button>
          )
        })}
      </nav>

      {/* Bottom */}
      <div className="sidebar__bottom">

        {/* Dark mode toggle */}
        <button
          className="sidebar__dark-toggle"
          onClick={toggle}
          title={isDark ? 'Switch to light mode' : 'Switch to dark mode'}
        >
          {isDark ? <Sun size={16} /> : <Moon size={16} />}
          {!collapsed && <span>{isDark ? 'Light mode' : 'Dark mode'}</span>}
        </button>

        {/* User info */}
        {!collapsed && (
          <div className="sidebar__user">
            <div className="sidebar__user-avatar">
              {user?.full_name?.charAt(0).toUpperCase()}
            </div>
            <div className="sidebar__user-info">
              <p className="sidebar__user-name">{user?.full_name}</p>
              <p className="sidebar__user-email">{user?.email}</p>
            </div>
          </div>
        )}

        {/* Logout */}
        <button
          className="sidebar__logout"
          onClick={handleLogout}
          title={collapsed ? 'Logout' : ''}
        >
          <LogOut size={16} />
          {!collapsed && <span>Logout</span>}
        </button>

        {/* Collapse toggle */}
        <button
          className="sidebar__collapse"
          onClick={() => setCollapsed(!collapsed)}
          title={collapsed ? 'Expand sidebar' : 'Collapse sidebar'}
        >
          {collapsed ? <ChevronRight size={16} /> : <ChevronLeft size={16} />}
        </button>
      </div>
    </aside>
  )
}

export default Sidebar
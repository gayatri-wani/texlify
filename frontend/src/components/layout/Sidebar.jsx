import { Link, useLocation } from 'react-router-dom'
import { useState } from 'react'
import {
  LayoutDashboard, FileText,
  History, Settings, LogOut,
  ChevronLeft, ChevronRight
} from 'lucide-react'
import useAuthStore from '../../store/authStore'
import './Sidebar.css'

const NAV_ITEMS = [
  { icon: LayoutDashboard, label: 'Dashboard', path: '/dashboard' },
  { icon: FileText,        label: 'Documents', path: '/documents' },
  { icon: History,         label: 'History',   path: '/history'   },
  { icon: Settings,        label: 'Settings',  path: '/settings'  },
]

const Sidebar = () => {
  const location = useLocation()
  const { user, logout } = useAuthStore()
  const [collapsed, setCollapsed] = useState(false)

  return (
    <aside className={`sidebar ${collapsed ? 'sidebar--collapsed' : ''}`}>

      <div className="sidebar__logo">
        <div className="sidebar__logo-icon">T</div>
        {!collapsed && <span className="sidebar__logo-text">Texlify</span>}
      </div>

      <button
        className="sidebar__toggle"
        onClick={() => setCollapsed(!collapsed)}
        title={collapsed ? 'Expand' : 'Collapse'}
      >
        {collapsed ? <ChevronRight size={16} /> : <ChevronLeft size={16} />}
      </button>

      <nav className="sidebar__nav">
        {NAV_ITEMS.map(({ icon: Icon, label, path }) => {
          const active = location.pathname === path
          return (
            <Link
              key={path}
              to={path}
              className={`sidebar__nav-item ${active ? 'sidebar__nav-item--active' : ''}`}
              title={collapsed ? label : ''}
            >
              <Icon size={18} className="sidebar__nav-icon" />
              {!collapsed && <span className="sidebar__nav-label">{label}</span>}
              {active && <span className="sidebar__nav-indicator" />}
            </Link>
          )
        })}
      </nav>

      <div className="sidebar__bottom">
        {!collapsed && (
          <div className="sidebar__user">
            <div className="sidebar__user-avatar">
              {user?.full_name?.charAt(0).toUpperCase()}
            </div>
            <div className="sidebar__user-info">
              <span className="sidebar__user-name">{user?.full_name}</span>
              <span className="sidebar__user-email">{user?.email}</span>
            </div>
          </div>
        )}
        <button className="sidebar__logout" onClick={logout} title="Logout">
          <LogOut size={16} />
          {!collapsed && <span>Logout</span>}
        </button>
      </div>

    </aside>
  )
}

export default Sidebar
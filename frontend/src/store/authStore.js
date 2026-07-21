import { create } from 'zustand'

const useAuthStore = create((set, get) => ({
  user:            null,
  isAuthenticated: false,
  isLoading:       true,

  setAuth: (user, accessToken, refreshToken) => {
    if (accessToken)  localStorage.setItem('access_token',  accessToken)
    if (refreshToken) localStorage.setItem('refresh_token', refreshToken)
    set({ user, isAuthenticated: true, isLoading: false })
  },

  logout: () => {
    localStorage.removeItem('access_token')
    localStorage.removeItem('refresh_token')
    set({ user: null, isAuthenticated: false, isLoading: false })
  },

  setLoading: (isLoading) => set({ isLoading }),

  // Call this on app start to verify token is still valid
  initializeAuth: async () => {
    const token = localStorage.getItem('access_token')
    if (!token) {
      set({ user: null, isAuthenticated: false, isLoading: false })
      return
    }
    try {
      // Verify token is valid by fetching user
      const response = await fetch(
        'http://127.0.0.1:8000/api/v1/auth/me',
        {
          headers: { Authorization: `Bearer ${token}` }
        }
      )
      if (response.ok) {
        const user = await response.json()
        set({ user, isAuthenticated: true, isLoading: false })
      } else {
        // Token invalid or expired — clear it
        localStorage.removeItem('access_token')
        localStorage.removeItem('refresh_token')
        set({ user: null, isAuthenticated: false, isLoading: false })
      }
    } catch {
      // Network error — still clear auth
      localStorage.removeItem('access_token')
      localStorage.removeItem('refresh_token')
      set({ user: null, isAuthenticated: false, isLoading: false })
    }
  },
}))

export default useAuthStore
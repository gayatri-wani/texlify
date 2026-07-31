import { create } from 'zustand'

const useAuthStore = create((set) => ({
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

  initializeAuth: async () => {
    const token = localStorage.getItem('access_token')
    if (!token) {
      set({ user: null, isAuthenticated: false, isLoading: false })
      return
    }
    try {
      const response = await fetch(
        'http://127.0.0.1:8000/api/v1/auth/me',
        { headers: { Authorization: `Bearer ${token}` } }
      )
      if (response.ok) {
        const user = await response.json()
        set({ user, isAuthenticated: true, isLoading: false })
      } else {
        localStorage.removeItem('access_token')
        localStorage.removeItem('refresh_token')
        set({ user: null, isAuthenticated: false, isLoading: false })
      }
    } catch {
      localStorage.removeItem('access_token')
      localStorage.removeItem('refresh_token')
      set({ user: null, isAuthenticated: false, isLoading: false })
    }
  },
}))

export default useAuthStore
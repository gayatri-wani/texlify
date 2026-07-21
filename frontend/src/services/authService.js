import api from '../utils/api'

export const authService = {
  register: async (data) => {
    const response = await api.post('/auth/register', data)
    return response.data
  },

  login: async (email, password) => {
    const response = await api.post('/auth/login', { email, password })
    return response.data
  },

  getMe: async () => {
    const response = await api.get('/auth/me')
    return response.data
  },

  logout: async () => {
    try {
      await api.post('/auth/logout')
    } catch { /* ignore */ }
    // Always clear tokens on logout
    localStorage.removeItem('access_token')
    localStorage.removeItem('refresh_token')
  },

  forgotPassword: async (email) => {
    const response = await api.post('/auth/forgot-password', { email })
    return response.data
  },

  resetPassword: async (token, newPassword) => {
    const response = await api.post('/auth/reset-password', {
      token,
      new_password: newPassword
    })
    return response.data
  },

  changePassword: async (currentPassword, newPassword) => {
    const response = await api.post('/auth/change-password', {
      current_password: currentPassword,
      new_password:     newPassword
    })
    return response.data
  },

  deleteAccount: async (password) => {
    const response = await api.delete('/auth/delete-account', {
      data: { password }
    })
    return response.data
  },
}
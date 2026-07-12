import axios from 'axios'

const API_BASE_URL = 'http://127.0.0.1:8000/api/v1'

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: { 'Content-Type': 'application/json' },
})

api.interceptors.request.use((config) => {
  const token = localStorage.getItem('access_token')
  if (token) config.headers.Authorization = `Bearer ${token}`
  return config
})

api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const original = error.config
    if (error.response?.status === 401 && !original._retry) {
      original._retry = true
      try {
        const refresh_token = localStorage.getItem('refresh_token')
        if (!refresh_token) {
          localStorage.clear()
          window.location.href = '/login'
          return Promise.reject(error)
        }
        const res = await axios.post(`${API_BASE_URL}/auth/refresh`, { refresh_token })
        const new_token = res.data.access_token
        localStorage.setItem('access_token', new_token)
        original.headers.Authorization = `Bearer ${new_token}`
        return api(original)
      } catch {
        localStorage.clear()
        window.location.href = '/login'
      }
    }
    return Promise.reject(error)
  }
)

export default api
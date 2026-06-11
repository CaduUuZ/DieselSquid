import axios from 'axios'

const api = axios.create({ baseURL: '/api' })

// Injeta o token em toda requisição — equivale ao interceptor do axios no SplashDesk
api.interceptors.request.use(cfg => {
  const token = localStorage.getItem('token')
  if (token) cfg.headers.Authorization = `Bearer ${token}`
  return cfg
})

// Redireciona para login se o token expirar
api.interceptors.response.use(
  r => r,
  err => {
    if (err.response?.status === 401) {
      localStorage.removeItem('token')
      window.location.href = '/login'
    }
    return Promise.reject(err)
  }
)

export default api

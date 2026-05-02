import axios from 'axios'
import toast from 'react-hot-toast'

const BASE_URL = import.meta.env.VITE_API_URL
  ? `${import.meta.env.VITE_API_URL}/api`
  : '/api'

export const apiClient = axios.create({
  baseURL: BASE_URL,
  headers: { 'Content-Type': 'application/json' },
  withCredentials: false,
})

apiClient.interceptors.request.use((config) => {
  const token = localStorage.getItem('bl_token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    const status = error?.response?.status
    const message = error?.response?.data?.detail ?? 'Something went wrong'

    if (status === 401) {
      localStorage.removeItem('bl_token')
      localStorage.removeItem('bl_auth')
      window.location.href = '/login'
      return Promise.reject(error)
    }

    if (status === 403) {
      toast.error(message)
    }

    if (status >= 500) {
      toast.error('Server error. Please try again shortly.')
    }

    return Promise.reject(error)
  }
)

export default apiClient

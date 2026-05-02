import { useAuthStore } from '@/store/authStore'
import { authApi } from '@/api/auth'
import { useNavigate } from 'react-router-dom'
import toast from 'react-hot-toast'

export function useAuth() {
  const store = useAuthStore()
  const navigate = useNavigate()

  const login = async (email: string, password: string) => {
    const data = await authApi.login(email, password)
    store.login(data)
    toast.success(`Welcome back, ${data.stage_name}!`)
    navigate('/dashboard')
  }

  const logout = () => {
    store.logout()
    navigate('/')
    toast.success('Logged out successfully')
  }

  return {
    ...store,
    login,
    logout,
  }
}

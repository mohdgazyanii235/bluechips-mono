import apiClient from './client'
import type { TokenResponse } from '@/types/auth'

export const authApi = {
  register: async (email: string, password: string, stage_name: string, invite_code?: string) => {
    const { data } = await apiClient.post('/auth/register', { email, password, stage_name, invite_code })
    return data
  },

  login: async (email: string, password: string): Promise<TokenResponse> => {
    const { data } = await apiClient.post<TokenResponse>('/auth/login', { email, password })
    return data
  },

  verifyEmail: async (token: string) => {
    const { data } = await apiClient.post(`/auth/verify-email?token=${token}`)
    return data
  },

  changePassword: async (current_password: string, new_password: string) => {
    const { data } = await apiClient.post('/auth/change-password', { current_password, new_password })
    return data
  },
}

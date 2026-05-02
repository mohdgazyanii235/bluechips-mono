import apiClient from './client'
import type { EscortCard, EscortProfile, EscortDashboard, PaginatedResponse, SearchFilters } from '@/types/escort'

export const escortsApi = {
  list: async (filters: SearchFilters = {}): Promise<PaginatedResponse<EscortCard>> => {
    const params = Object.fromEntries(
      Object.entries(filters).filter(([, v]) => v != null && v !== '')
    )
    const { data } = await apiClient.get<PaginatedResponse<EscortCard>>('/escorts', { params })
    return data
  },

  getBySlug: async (slug: string): Promise<EscortProfile> => {
    const { data } = await apiClient.get<EscortProfile>(`/escorts/${slug}`)
    return data
  },

  getMe: async (): Promise<EscortDashboard> => {
    const { data } = await apiClient.get<EscortDashboard>('/escorts/me')
    return data
  },

  updateMe: async (payload: Partial<EscortDashboard>) => {
    const { data } = await apiClient.put('/escorts/me', payload)
    return data
  },

  toggleAvailableNow: async (available: boolean) => {
    const { data } = await apiClient.patch(`/escorts/me/available-now?available=${available}`)
    return data
  },

  recordContactClick: async (slug: string) => {
    await apiClient.post(`/escorts/${slug}/contact-click`).catch(() => {})
  },
}

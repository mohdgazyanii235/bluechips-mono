import apiClient from './client'
import type { Borough } from '@/types/escort'

export const boroughsApi = {
  list: async (): Promise<Borough[]> => {
    const { data } = await apiClient.get<Borough[]>('/boroughs')
    return data
  },

  getBySlug: async (slug: string): Promise<Borough> => {
    const { data } = await apiClient.get<Borough>(`/boroughs/${slug}`)
    return data
  },
}

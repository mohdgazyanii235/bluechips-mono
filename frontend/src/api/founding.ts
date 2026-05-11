import { apiClient } from './client'

export interface FoundingOfferStatus {
  active: boolean
  limit: number
  signups: number
  remaining: number
  percent_off: number
  duration_months: number
  tier: string
  includes_blue_tick: boolean
  lifetime_discount_percent: number
  badge_label: string
}

export const foundingApi = {
  status: async (): Promise<FoundingOfferStatus> => {
    const { data } = await apiClient.get('/founding/status')
    return data
  },
}

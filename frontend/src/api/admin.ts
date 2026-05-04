import axios from 'axios'

const BASE_URL = import.meta.env.VITE_API_URL
  ? `${import.meta.env.VITE_API_URL}/api`
  : '/api'

const adminClient = axios.create({ baseURL: BASE_URL })

adminClient.interceptors.request.use((config) => {
  const token = localStorage.getItem('bl_admin_token')
  if (token) config.headers.Authorization = `Bearer ${token}`
  return config
})

export const adminApi = {
  login: async (email: string, password: string) => {
    const { data } = await adminClient.post('/admin/login', { email, password })
    return data as { access_token: string; email: string }
  },

  getStats: async () => {
    const { data } = await adminClient.get('/admin/stats')
    return data as { total_escorts: number; pending_verifications: number; paid_escorts: number }
  },

  getPendingVerifications: async () => {
    const { data } = await adminClient.get('/admin/verifications/pending')
    return data as {
      total: number
      items: Array<{
        id: string
        escort_id: string
        escort: { stage_name: string; email: string } | null
        level: number
        level_name: string
        submitted_at: string
        time_ago: string
      }>
    }
  },

  getVerification: async (id: string) => {
    const { data } = await adminClient.get(`/admin/verifications/${id}`)
    return data as {
      id: string
      escort: {
        id: string
        stage_name: string
        email: string
        subscription_tier: string
        subscription_expires_at: string | null
      } | null
      level: number
      level_name: string
      status: string
      submitted_at: string
      reviewed_at: string | null
      admin_notes: string | null
      id_document_signed_url: string | null
      selfie_signed_url: string | null
      match_selfie_signed_url: string | null
    }
  },

  approveVerification: async (id: string) => {
    const { data } = await adminClient.post(`/admin/verifications/${id}/approve`)
    return data
  },

  rejectVerification: async (id: string, admin_notes: string) => {
    const { data } = await adminClient.post(`/admin/verifications/${id}/reject`, { admin_notes })
    return data
  },

  getEscorts: async (page = 1) => {
    const { data } = await adminClient.get('/admin/escorts', { params: { page } })
    return data as Array<{
      id: string
      stage_name: string
      email: string
      subscription_tier: string
      verification_level: number
      is_active: boolean
      is_approved: boolean
      is_email_verified: boolean
      created_at: string
    }>
  },

  toggleEscortActive: async (id: string) => {
    const { data } = await adminClient.patch(`/admin/escorts/${id}/toggle-active`)
    return data
  },

  createDiscountCode: async (payload: {
    code: string
    name: string
    percent_off: number
    applicable_tiers: string[]
    duration_months: number
    max_redemptions?: number | null
  }) => {
    const { data } = await adminClient.post('/admin/discounts', payload)
    return data as { id: string; code: string; message: string }
  },

  listDiscountCodes: async () => {
    const { data } = await adminClient.get('/admin/discounts')
    return data as Array<{
      id: string
      code: string
      name: string
      percent_off: number
      applicable_tiers: string[]
      duration_months: number
      max_redemptions: number | null
      current_redemptions: number
      is_active: boolean
      created_at: string
    }>
  },

  deactivateDiscountCode: async (id: string) => {
    const { data } = await adminClient.patch(`/admin/discounts/${id}/deactivate`)
    return data
  },

  getPricing: async () => {
    const { data } = await adminClient.get('/admin/pricing')
    return data as {
      essential_monthly_pence: number
      essential_annual_pence: number
      premium_monthly_pence: number
      premium_annual_pence: number
      elite_monthly_pence: number
      elite_annual_pence: number
      blue_tick_setup_pence: number
      blue_tick_monthly_pence: number
      stripe_essential_monthly_id: string
      stripe_essential_annual_id: string
      stripe_premium_monthly_id: string
      stripe_premium_annual_id: string
      stripe_elite_monthly_id: string
      stripe_elite_annual_id: string
      stripe_blue_tick_setup_id: string
      stripe_blue_tick_monthly_id: string
      updated_at: string | null
      updated_by: string | null
    }
  },

  updatePricing: async (payload: {
    essential_monthly_pence?: number
    essential_annual_pence?: number
    premium_monthly_pence?: number
    premium_annual_pence?: number
    elite_monthly_pence?: number
    elite_annual_pence?: number
    blue_tick_setup_pence?: number
    blue_tick_monthly_pence?: number
  }) => {
    const { data } = await adminClient.put('/admin/pricing', payload)
    return data as { message: string }
  },
}

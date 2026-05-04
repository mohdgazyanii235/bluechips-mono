import apiClient from './client'

export const paymentsApi = {
  /** New subscription — opens Stripe Checkout page */
  createCheckout: async (
    tier: string,
    billing: 'monthly' | 'annual' = 'monthly',
    promo?: { type: 'discount' | 'referral'; code: string },
  ): Promise<{ url: string }> => {
    const payload: Record<string, string> = { tier, billing }
    if (promo?.type === 'discount') payload.discount_code = promo.code
    if (promo?.type === 'referral') payload.referral_code = promo.code
    const { data } = await apiClient.post('/payments/checkout', payload)
    return data
  },

  /** Existing subscriber switching tier — modifies Stripe sub in-place, no redirect */
  upgradeTier: async (tier: string, billing: 'monthly' | 'annual' = 'monthly'): Promise<{ message: string }> => {
    const { data } = await apiClient.post('/payments/upgrade-tier', { tier, billing })
    return data
  },

  createBlueTickCheckout: async (): Promise<{ url: string }> => {
    const { data } = await apiClient.post('/payments/blue-tick-checkout')
    return data
  },

  getSubscription: async () => {
    const { data } = await apiClient.get('/payments/subscription')
    return data
  },

  getInvoices: async (): Promise<{ invoices: any[] }> => {
    const { data } = await apiClient.get('/payments/invoices')
    return data
  },

  cancelSubscription: async () => {
    const { data } = await apiClient.post('/payments/cancel')
    return data
  },

  cancelBlueTick: async () => {
    const { data } = await apiClient.post('/payments/cancel-blue-tick')
    return data
  },

  reactivateSubscription: async () => {
    const { data } = await apiClient.post('/payments/reactivate')
    return data
  },

  reactivateBlueTick: async () => {
    const { data } = await apiClient.post('/payments/reactivate-blue-tick')
    return data
  },
}

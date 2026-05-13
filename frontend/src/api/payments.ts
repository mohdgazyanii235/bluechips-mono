import apiClient from './client'

export interface UpgradePreview {
  type: 'new' | 'upgrade_new_checkout' | 'downgrade'
  from_tier: string
  to_tier: string
  billing: string
  charge_now_pence: number
  then_pence: number
  remaining_days: number
  total_days: number
  next_billing_date: string
  effective_date?: string
  notice?: string
}

export const paymentsApi = {
  /** New subscription — opens the provider's hosted-checkout page (Verotel FlexPay). */
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

  /** Preview cost of changing tiers. NOTE: with Verotel, an "upgrade" means
   *  cancelling the old subscription and going through a fresh checkout. */
  getUpgradePreview: async (tier: string, billing: 'monthly' | 'annual' = 'monthly'): Promise<UpgradePreview> => {
    const { data } = await apiClient.get('/payments/upgrade-preview', { params: { tier, billing } })
    return data
  },

  /** Existing subscriber switching tier — cancels old sub + returns a new
   *  hosted-checkout URL for the user to redirect to. */
  upgradeTier: async (tier: string, billing: 'monthly' | 'annual' = 'monthly'): Promise<{ url: string }> => {
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

  getProviderConfig: async (): Promise<{ provider: string }> => {
    const { data } = await apiClient.get('/payments/config')
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

  /** Best-effort sync from the provider into our DB. Currently a no-op for
   *  Verotel (no list-subscriptions API). Kept for backwards-compat with
   *  the success-page handler. */
  syncFromProvider: async (): Promise<{ message: string }> => {
    const { data } = await apiClient.post('/payments/sync')
    return data
  },
}

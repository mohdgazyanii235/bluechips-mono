import apiClient from './client'

export interface UpgradePreview {
  type: 'new' | 'upgrade' | 'downgrade'
  from_tier: string
  to_tier: string
  billing: string
  charge_now_pence: number
  then_pence: number
  remaining_days: number
  total_days: number
  next_billing_date: string
  effective_date?: string
}

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

  /** Preview what the user will pay before confirming an upgrade/downgrade */
  getUpgradePreview: async (tier: string, billing: 'monthly' | 'annual' = 'monthly'): Promise<UpgradePreview> => {
    const { data } = await apiClient.get('/payments/upgrade-preview', { params: { tier, billing } })
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

  /** Pull current subscription state from Stripe into our DB.
   *  Used as a fallback when webhooks haven't arrived (e.g. local dev). */
  syncFromStripe: async (): Promise<{ message: string }> => {
    const { data } = await apiClient.post('/payments/sync')
    return data
  },
}

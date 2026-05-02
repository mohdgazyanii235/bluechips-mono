import { create } from 'zustand'
import { persist } from 'zustand/middleware'
import type { AuthState, TokenResponse } from '@/types/auth'

interface AuthStore extends AuthState {
  login: (data: TokenResponse) => void
  logout: () => void
  updateProfile: (data: Partial<AuthState>) => void
}

const initialState: AuthState = {
  token: null,
  escort_id: null,
  stage_name: null,
  subscription_tier: null,
  verification_level: 0,
  profile_complete: false,
  isAuthenticated: false,
}

export const useAuthStore = create<AuthStore>()(
  persist(
    (set) => ({
      ...initialState,

      login: (data: TokenResponse) => {
        localStorage.setItem('bl_token', data.access_token)
        set({
          token: data.access_token,
          escort_id: data.escort_id,
          stage_name: data.stage_name,
          subscription_tier: data.subscription_tier,
          verification_level: data.verification_level,
          profile_complete: data.profile_complete,
          isAuthenticated: true,
        })
      },

      logout: () => {
        localStorage.removeItem('bl_token')
        localStorage.removeItem('bl_auth')
        set(initialState)
      },

      updateProfile: (data) => set((state) => ({ ...state, ...data })),
    }),
    {
      name: 'bl_auth',
      partialize: (state) => ({
        token: state.token,
        escort_id: state.escort_id,
        stage_name: state.stage_name,
        subscription_tier: state.subscription_tier,
        verification_level: state.verification_level,
        profile_complete: state.profile_complete,
        isAuthenticated: state.isAuthenticated,
      }),
    }
  )
)

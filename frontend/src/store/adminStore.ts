import { create } from 'zustand'
import { persist } from 'zustand/middleware'

interface AdminStore {
  token: string | null
  email: string | null
  isAuthenticated: boolean
  login: (token: string, email: string) => void
  logout: () => void
}

export const useAdminStore = create<AdminStore>()(
  persist(
    (set) => ({
      token: null,
      email: null,
      isAuthenticated: false,

      login: (token, email) => {
        localStorage.setItem('bl_admin_token', token)
        set({ token, email, isAuthenticated: true })
      },

      logout: () => {
        localStorage.removeItem('bl_admin_token')
        set({ token: null, email: null, isAuthenticated: false })
      },
    }),
    {
      name: 'bl_admin',
      partialize: (state) => ({ token: state.token, email: state.email, isAuthenticated: state.isAuthenticated }),
    }
  )
)

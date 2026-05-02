import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { escortsApi } from '@/api/escorts'
import type { SearchFilters } from '@/types/escort'
import toast from 'react-hot-toast'

export function useEscorts(filters: SearchFilters = {}) {
  return useQuery({
    queryKey: ['escorts', filters],
    queryFn: () => escortsApi.list(filters),
    staleTime: 60_000,
    placeholderData: (prev) => prev,
  })
}

export function useEscortProfile(slug: string) {
  return useQuery({
    queryKey: ['escort', slug],
    queryFn: () => escortsApi.getBySlug(slug),
    enabled: !!slug,
    staleTime: 120_000,
  })
}

export function useMyProfile() {
  return useQuery({
    queryKey: ['escort', 'me'],
    queryFn: escortsApi.getMe,
    staleTime: 30_000,
  })
}

export function useUpdateProfile() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: escortsApi.updateMe,
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['escort', 'me'] })
      toast.success('Profile updated!')
    },
    onError: (err: any) => {
      toast.error(err?.response?.data?.detail ?? 'Failed to update profile')
    },
  })
}

export function useToggleAvailableNow() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (available: boolean) => escortsApi.toggleAvailableNow(available),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['escort', 'me'] })
    },
  })
}

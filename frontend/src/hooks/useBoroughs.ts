import { useQuery } from '@tanstack/react-query'
import { boroughsApi } from '@/api/boroughs'

export function useBoroughs() {
  return useQuery({
    queryKey: ['boroughs'],
    queryFn: boroughsApi.list,
    staleTime: 600_000,
  })
}

export function useBorough(slug: string) {
  return useQuery({
    queryKey: ['borough', slug],
    queryFn: () => boroughsApi.getBySlug(slug),
    enabled: !!slug,
    staleTime: 300_000,
  })
}

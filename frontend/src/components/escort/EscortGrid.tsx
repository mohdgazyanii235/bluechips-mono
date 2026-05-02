import { EscortCard } from './EscortCard'
import { SkeletonCard } from '@/components/ui/Spinner'
import type { EscortCard as EscortCardType } from '@/types/escort'

interface EscortGridProps {
  escorts: EscortCardType[]
  loading?: boolean
  skeletonCount?: number
}

export function EscortGrid({ escorts, loading, skeletonCount = 12 }: EscortGridProps) {
  if (loading) {
    return (
      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5 gap-4">
        {Array.from({ length: skeletonCount }).map((_, i) => (
          <SkeletonCard key={i} />
        ))}
      </div>
    )
  }

  if (escorts.length === 0) {
    return (
      <div className="text-center py-24 space-y-4">
        <p className="font-serif text-2xl text-stone-600">No companions found</p>
        <p className="text-stone-500 text-sm">Try adjusting your filters or browse a different area.</p>
      </div>
    )
  }

  return (
    <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5 gap-4">
      {escorts.map((escort, i) => (
        <EscortCard key={escort.id} escort={escort} index={i} />
      ))}
    </div>
  )
}

import { cn } from '@/utils/cn'
import { Loader2 } from 'lucide-react'

interface SpinnerProps {
  size?: 'sm' | 'md' | 'lg'
  className?: string
  fullPage?: boolean
}

export function Spinner({ size = 'md', className, fullPage }: SpinnerProps) {
  const sizes = { sm: 'w-4 h-4', md: 'w-6 h-6', lg: 'w-10 h-10' }

  if (fullPage) {
    return (
      <div className="flex items-center justify-center min-h-[50vh]">
        <Loader2 className={cn('animate-spin text-gold-400', sizes.lg)} />
      </div>
    )
  }

  return <Loader2 className={cn('animate-spin text-gold-400', sizes[size], className)} />
}

export function SkeletonCard() {
  return (
    <div className="card-surface overflow-hidden">
      <div className="aspect-[3/4] shimmer" />
      <div className="p-4 space-y-3">
        <div className="h-4 w-3/4 shimmer rounded" />
        <div className="h-3 w-1/2 shimmer rounded" />
        <div className="flex gap-1.5">
          <div className="h-5 w-12 shimmer rounded-full" />
          <div className="h-5 w-16 shimmer rounded-full" />
          <div className="h-5 w-10 shimmer rounded-full" />
        </div>
      </div>
    </div>
  )
}

import { cn } from '@/utils/cn'

interface BadgeProps {
  children: React.ReactNode
  variant?: 'gold' | 'blue-tick' | 'verified' | 'std' | 'available' | 'tier' | 'subtle'
  className?: string
}

export function Badge({ children, variant = 'subtle', className }: BadgeProps) {
  const variants = {
    gold: 'bg-gold-400/10 text-gold-400 border border-gold-400/30',
    'blue-tick': 'bg-blue-500/10 text-blue-400 border border-blue-500/30',
    verified: 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/30',
    std: 'bg-teal-500/10 text-teal-400 border border-teal-500/30',
    available: 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/40',
    tier: 'bg-gold-900/40 text-gold-300 border border-gold-700/40',
    subtle: 'bg-surface border border-surface-border text-stone-400',
  }

  return (
    <span className={cn('inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-medium', variants[variant], className)}>
      {children}
    </span>
  )
}

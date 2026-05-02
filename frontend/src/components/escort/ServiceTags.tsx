import { cn } from '@/utils/cn'

interface ServiceTagsProps {
  tags: string[]
  max?: number
  size?: 'sm' | 'md'
  className?: string
}

export function ServiceTags({ tags, max = 4, size = 'sm', className }: ServiceTagsProps) {
  const visible = tags.slice(0, max)
  const overflow = tags.length - max

  return (
    <div className={cn('flex flex-wrap gap-1.5', className)}>
      {visible.map((tag) => (
        <span
          key={tag}
          className={cn(
            'rounded-full border border-surface-border bg-surface text-stone-400 font-medium',
            size === 'sm' ? 'px-2 py-0.5 text-[11px]' : 'px-3 py-1 text-xs'
          )}
        >
          {tag}
        </span>
      ))}
      {overflow > 0 && (
        <span
          className={cn(
            'rounded-full border border-gold-400/20 bg-gold-400/5 text-gold-500 font-medium',
            size === 'sm' ? 'px-2 py-0.5 text-[11px]' : 'px-3 py-1 text-xs'
          )}
        >
          +{overflow} more
        </span>
      )}
    </div>
  )
}

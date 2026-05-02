import { cn } from '@/utils/cn'
import { type SelectHTMLAttributes, forwardRef } from 'react'
import { ChevronDown } from 'lucide-react'

interface SelectProps extends SelectHTMLAttributes<HTMLSelectElement> {
  label?: string
  error?: string
  options: { value: string; label: string }[]
  placeholder?: string
}

export const Select = forwardRef<HTMLSelectElement, SelectProps>(
  ({ label, error, options, placeholder, className, ...props }, ref) => (
    <div className="space-y-1.5">
      {label && (
        <label className="block text-xs font-medium text-stone-400 uppercase tracking-wider">
          {label}
        </label>
      )}
      <div className="relative">
        <select
          ref={ref}
          className={cn(
            'w-full appearance-none bg-surface border border-surface-border rounded-lg px-4 py-3 text-ivory-200',
            'focus:outline-none focus:border-gold-400 focus:ring-1 focus:ring-gold-400',
            'transition-colors duration-200 text-sm pr-10',
            error && 'border-red-700',
            !props.value && 'text-stone-600',
            className
          )}
          {...props}
        >
          {placeholder && <option value="">{placeholder}</option>}
          {options.map((opt) => (
            <option key={opt.value} value={opt.value} className="bg-surface-card text-ivory-200">
              {opt.label}
            </option>
          ))}
        </select>
        <ChevronDown className="absolute right-3 top-1/2 -translate-y-1/2 w-4 h-4 text-stone-500 pointer-events-none" />
      </div>
      {error && <p className="text-red-400 text-xs mt-1">{error}</p>}
    </div>
  )
)

Select.displayName = 'Select'

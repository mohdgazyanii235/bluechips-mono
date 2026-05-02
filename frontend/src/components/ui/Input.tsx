import { cn } from '@/utils/cn'
import { type InputHTMLAttributes, forwardRef } from 'react'

interface InputProps extends InputHTMLAttributes<HTMLInputElement> {
  label?: string
  error?: string
  hint?: string
}

export const Input = forwardRef<HTMLInputElement, InputProps>(
  ({ label, error, hint, className, ...props }, ref) => (
    <div className="space-y-1.5">
      {label && (
        <label className="block text-xs font-medium text-stone-400 uppercase tracking-wider">
          {label}
        </label>
      )}
      <input
        ref={ref}
        className={cn(
          'w-full bg-surface border border-surface-border rounded-lg px-4 py-3 text-ivory-200',
          'placeholder-stone-600 focus:outline-none focus:border-gold-400 focus:ring-1 focus:ring-gold-400',
          'transition-colors duration-200 text-sm',
          error && 'border-red-700 focus:border-red-500 focus:ring-red-500',
          className
        )}
        {...props}
      />
      {error && <p className="text-red-400 text-xs mt-1">{error}</p>}
      {hint && !error && <p className="text-stone-500 text-xs mt-1">{hint}</p>}
    </div>
  )
)

Input.displayName = 'Input'

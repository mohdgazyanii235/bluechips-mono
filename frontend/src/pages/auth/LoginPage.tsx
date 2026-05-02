import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { Link } from 'react-router-dom'
import { Helmet } from 'react-helmet-async'
import { motion } from 'framer-motion'
import { Input } from '@/components/ui/Input'
import { Button } from '@/components/ui/Button'
import { useAuth } from '@/hooks/useAuth'
import { Eye, EyeOff } from 'lucide-react'
import { useState } from 'react'

const schema = z.object({
  email: z.string().email('Enter a valid email'),
  password: z.string().min(1, 'Password is required'),
})

type FormData = z.infer<typeof schema>

export function LoginPage() {
  const { login } = useAuth()
  const [showPassword, setShowPassword] = useState(false)
  const { register, handleSubmit, formState: { errors, isSubmitting }, setError } = useForm<FormData>({
    resolver: zodResolver(schema),
  })

  const onSubmit = async (data: FormData) => {
    try {
      await login(data.email, data.password)
    } catch (err: any) {
      setError('root', { message: err?.response?.data?.detail ?? 'Login failed' })
    }
  }

  return (
    <div className="min-h-screen flex">
      <Helmet>
        <title>Sign In — Bluechips London</title>
      </Helmet>

      {/* Left decorative panel */}
      <div className="hidden lg:flex flex-col justify-between w-[45%] bg-surface-card border-r border-surface-border p-12">
        <Link to="/" className="space-y-1">
          <h1 className="font-serif text-3xl gold-text">BLUECHIPS</h1>
          <p className="text-stone-600 text-xs uppercase tracking-widest">London</p>
        </Link>
        <div className="space-y-6">
          <blockquote className="font-serif text-2xl text-ivory-200 leading-relaxed">
            "The only directory that treats companions with the premium respect they deserve."
          </blockquote>
          <p className="text-stone-500 text-sm">— Join 500+ independent companions advertising on Bluechips London</p>
        </div>
        <p className="text-stone-700 text-xs">© {new Date().getFullYear()} Bluechips London</p>
      </div>

      {/* Right: Form */}
      <div className="flex-1 flex items-center justify-center p-6">
        <motion.div
          initial={{ opacity: 0, y: 16 }}
          animate={{ opacity: 1, y: 0 }}
          className="w-full max-w-sm space-y-8"
        >
          {/* Mobile logo */}
          <Link to="/" className="lg:hidden block">
            <h1 className="font-serif text-2xl gold-text">BLUECHIPS LONDON</h1>
          </Link>

          <div className="space-y-2">
            <h2 className="font-serif text-3xl text-ivory-100">Sign in</h2>
            <p className="text-stone-500 text-sm">Access your companion dashboard</p>
          </div>

          <form onSubmit={handleSubmit(onSubmit)} className="space-y-5">
            <Input
              label="Email address"
              type="email"
              placeholder="your@email.com"
              autoComplete="email"
              {...register('email')}
              error={errors.email?.message}
            />

            <div className="relative">
              <Input
                label="Password"
                type={showPassword ? 'text' : 'password'}
                placeholder="••••••••"
                autoComplete="current-password"
                {...register('password')}
                error={errors.password?.message}
                className="pr-10"
              />
              <button
                type="button"
                onClick={() => setShowPassword(!showPassword)}
                className="absolute right-3 bottom-3 text-stone-500 hover:text-stone-300 transition-colors"
              >
                {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
              </button>
            </div>

            {errors.root && (
              <p className="text-red-400 text-sm bg-red-900/20 border border-red-900/40 rounded-lg px-4 py-3">
                {errors.root.message}
              </p>
            )}

            <Button type="submit" fullWidth size="lg" loading={isSubmitting}>
              Sign In
            </Button>
          </form>

          <div className="space-y-4 text-center text-sm">
            <p className="text-stone-500">
              Don't have an account?{' '}
              <Link to="/join" className="text-gold-400 hover:text-gold-300 transition-colors">
                Create one free
              </Link>
            </p>
          </div>
        </motion.div>
      </div>
    </div>
  )
}

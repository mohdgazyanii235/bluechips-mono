import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { Link, useNavigate, useSearchParams } from 'react-router-dom'
import { Helmet } from 'react-helmet-async'
import { motion } from 'framer-motion'
import { Input } from '@/components/ui/Input'
import { Button } from '@/components/ui/Button'
import { authApi } from '@/api/auth'
import { useState } from 'react'
import { BadgeCheck, Shield, Eye, EyeOff, Crown } from 'lucide-react'
import toast from 'react-hot-toast'

const schema = z.object({
  stage_name: z.string().min(2, 'Stage name must be at least 2 characters').max(50, 'Max 50 characters'),
  email: z.string().email('Enter a valid email'),
  password: z.string().min(8, 'Password must be at least 8 characters'),
  confirm_password: z.string(),
  age_confirm: z.literal(true, { errorMap: () => ({ message: 'You must confirm you are 18+' }) }),
  terms: z.literal(true, { errorMap: () => ({ message: 'You must agree to the terms' }) }),
}).refine((d) => d.password === d.confirm_password, {
  message: 'Passwords do not match',
  path: ['confirm_password'],
})

type FormData = z.infer<typeof schema>

export function RegisterPage() {
  const navigate = useNavigate()
  const [searchParams] = useSearchParams()
  const inviteCode = (searchParams.get('code') || '').trim().toUpperCase()
  const [showPass, setShowPass] = useState(false)
  const { register, handleSubmit, formState: { errors, isSubmitting }, setError } = useForm<FormData>({
    resolver: zodResolver(schema),
  })

  const onSubmit = async (data: FormData) => {
    try {
      await authApi.register(data.email, data.password, data.stage_name, inviteCode || undefined)
      toast.success('Account created! Check your email to verify.')
      navigate('/login')
    } catch (err: any) {
      setError('root', { message: err?.response?.data?.detail ?? 'Registration failed' })
    }
  }

  return (
    <div className="min-h-screen flex">
      <Helmet>
        <title>Create Your Profile — Bluechips London</title>
        <meta name="description" content="List your profile on Bluechips London, London's most exclusive companion directory. Free to join." />
      </Helmet>

      {/* Left decorative */}
      <div className="hidden lg:flex flex-col justify-between w-[45%] bg-surface-card border-r border-surface-border p-12">
        <Link to="/" className="space-y-1">
          <h1 className="font-serif text-3xl gold-text">BLUECHIPS</h1>
          <p className="text-stone-600 text-xs uppercase tracking-widest">London</p>
        </Link>

        <div className="space-y-8">
          {[
            { icon: BadgeCheck, title: 'Free to join', desc: 'Start with a free listing. Upgrade only when you\'re ready.' },
            { icon: Shield, title: 'Your identity is private', desc: 'You choose your stage name. Your real name is never displayed.' },
            { icon: Eye, title: 'You control everything', desc: 'Edit or remove your profile at any time. No contracts.' },
          ].map(({ icon: Icon, title, desc }) => (
            <div key={title} className="flex gap-4">
              <div className="w-10 h-10 shrink-0 rounded-lg bg-gold-400/10 border border-gold-400/20 flex items-center justify-center">
                <Icon className="w-5 h-5 text-gold-400" />
              </div>
              <div>
                <p className="text-ivory-200 font-medium text-sm">{title}</p>
                <p className="text-stone-500 text-sm mt-0.5">{desc}</p>
              </div>
            </div>
          ))}
        </div>
        <p className="text-stone-700 text-xs">© {new Date().getFullYear()} Bluechips London</p>
      </div>

      {/* Right: Form */}
      <div className="flex-1 flex items-center justify-center p-6 overflow-y-auto">
        <motion.div
          initial={{ opacity: 0, y: 16 }}
          animate={{ opacity: 1, y: 0 }}
          className="w-full max-w-sm space-y-7 py-8"
        >
          <Link to="/" className="lg:hidden block">
            <h1 className="font-serif text-2xl gold-text">BLUECHIPS LONDON</h1>
          </Link>

          <div className="space-y-2">
            <h2 className="font-serif text-3xl text-ivory-100">Create your account</h2>
            <p className="text-stone-500 text-sm">Free to join. No credit card required.</p>
          </div>

          {inviteCode && (
            <div className="flex items-center gap-3 p-3 rounded-lg border border-gold-400/30 bg-gold-400/5">
              <Crown className="w-5 h-5 text-gold-400 shrink-0" />
              <div className="flex-1 min-w-0">
                <p className="text-gold-300 text-sm font-medium">Founding code applied</p>
                <p className="text-stone-500 text-xs font-mono truncate">{inviteCode}</p>
              </div>
            </div>
          )}

          <form onSubmit={handleSubmit(onSubmit)} className="space-y-5">
            <Input
              label="Your stage name"
              placeholder="e.g. Sophia, Isabella..."
              hint="This is how clients will find you. Not your real name."
              {...register('stage_name')}
              error={errors.stage_name?.message}
            />

            <Input
              label="Email address"
              type="email"
              placeholder="your@email.com"
              hint="Used for account access only. Never shown publicly."
              autoComplete="email"
              {...register('email')}
              error={errors.email?.message}
            />

            <div className="relative">
              <Input
                label="Password"
                type={showPass ? 'text' : 'password'}
                placeholder="Minimum 8 characters"
                autoComplete="new-password"
                {...register('password')}
                error={errors.password?.message}
              />
              <button type="button" onClick={() => setShowPass(!showPass)} className="absolute right-3 bottom-3 text-stone-500 hover:text-stone-300">
                {showPass ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
              </button>
            </div>

            <Input
              label="Confirm password"
              type="password"
              placeholder="Repeat your password"
              {...register('confirm_password')}
              error={errors.confirm_password?.message}
            />

            {/* Checkboxes */}
            <div className="space-y-3">
              <label className="flex items-start gap-3 cursor-pointer">
                <input type="checkbox" {...register('age_confirm')} className="mt-0.5 accent-gold-400 w-4 h-4 shrink-0" />
                <span className="text-stone-400 text-sm">I confirm I am 18 years of age or older</span>
              </label>
              {errors.age_confirm && <p className="text-red-400 text-xs">{errors.age_confirm.message}</p>}

              <label className="flex items-start gap-3 cursor-pointer">
                <input type="checkbox" {...register('terms')} className="mt-0.5 accent-gold-400 w-4 h-4 shrink-0" />
                <span className="text-stone-400 text-sm">
                  I agree to the{' '}
                  <Link to="/terms" className="text-gold-400 hover:text-gold-300">Terms of Service</Link>
                  {' '}and{' '}
                  <Link to="/privacy" className="text-gold-400 hover:text-gold-300">Privacy Policy</Link>
                </span>
              </label>
              {errors.terms && <p className="text-red-400 text-xs">{errors.terms.message}</p>}
            </div>

            {errors.root && (
              <p className="text-red-400 text-sm bg-red-900/20 border border-red-900/40 rounded-lg px-4 py-3">
                {errors.root.message}
              </p>
            )}

            <Button type="submit" fullWidth size="lg" loading={isSubmitting}>
              Create Free Account
            </Button>
          </form>

          <p className="text-center text-stone-500 text-sm">
            Already have an account?{' '}
            <Link to="/login" className="text-gold-400 hover:text-gold-300">Sign in</Link>
          </p>
        </motion.div>
      </div>
    </div>
  )
}

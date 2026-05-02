import { useEffect, useState } from 'react'
import { Link, useSearchParams } from 'react-router-dom'
import { Helmet } from 'react-helmet-async'
import { motion } from 'framer-motion'
import { CheckCircle, XCircle, Loader2 } from 'lucide-react'
import { authApi } from '@/api/auth'
import { Button } from '@/components/ui/Button'

export function VerifyEmailPage() {
  const [searchParams] = useSearchParams()
  const token = searchParams.get('token')
  const [status, setStatus] = useState<'loading' | 'success' | 'error'>('loading')
  const [message, setMessage] = useState('')

  useEffect(() => {
    if (!token) {
      setStatus('error')
      setMessage('No verification token found. Please check your email link.')
      return
    }

    authApi.verifyEmail(token)
      .then((data) => {
        setStatus('success')
        setMessage(data.message)
      })
      .catch((err) => {
        setStatus('error')
        setMessage(err?.response?.data?.detail ?? 'Verification failed. The link may have expired.')
      })
  }, [token])

  return (
    <div className="min-h-screen flex items-center justify-center p-6">
      <Helmet><title>Verify Email — Bluechips London</title></Helmet>

      <motion.div
        initial={{ opacity: 0, scale: 0.97 }}
        animate={{ opacity: 1, scale: 1 }}
        className="max-w-sm w-full card-surface p-8 rounded-2xl text-center space-y-6"
      >
        <Link to="/" className="block">
          <h1 className="font-serif text-2xl gold-text">BLUECHIPS LONDON</h1>
        </Link>

        <div className="flex justify-center">
          {status === 'loading' && <Loader2 className="w-16 h-16 text-gold-400 animate-spin" />}
          {status === 'success' && <CheckCircle className="w-16 h-16 text-emerald-400" />}
          {status === 'error' && <XCircle className="w-16 h-16 text-red-400" />}
        </div>

        <div className="space-y-2">
          <h2 className="font-serif text-2xl text-ivory-100">
            {status === 'loading' && 'Verifying...'}
            {status === 'success' && 'Email Verified!'}
            {status === 'error' && 'Verification Failed'}
          </h2>
          <p className="text-stone-400 text-sm">{message}</p>
        </div>

        {status === 'success' && (
          <Link to="/login">
            <Button variant="gold" fullWidth>Sign In to Your Dashboard</Button>
          </Link>
        )}
        {status === 'error' && (
          <Link to="/login">
            <Button variant="outline-gold" fullWidth>Back to Sign In</Button>
          </Link>
        )}
      </motion.div>
    </div>
  )
}

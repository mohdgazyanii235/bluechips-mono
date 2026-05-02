import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { adminApi } from '@/api/admin'
import { useAdminStore } from '@/store/adminStore'
import { Button } from '@/components/ui/Button'
import { Input } from '@/components/ui/Input'
import toast from 'react-hot-toast'

export function AdminLoginPage() {
  const navigate = useNavigate()
  const { login } = useAdminStore()
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [loading, setLoading] = useState(false)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setLoading(true)
    try {
      const data = await adminApi.login(email, password)
      login(data.access_token, data.email)
      navigate('/admin')
    } catch {
      toast.error('Invalid credentials')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-black px-4">
      <div className="w-full max-w-sm space-y-8">
        <div className="text-center space-y-1">
          <h1 className="font-serif text-4xl gold-text">BLUECHIPS</h1>
          <p className="text-stone-500 text-xs uppercase tracking-widest">Admin Portal</p>
        </div>

        <form onSubmit={handleSubmit} className="card-surface p-8 rounded-2xl space-y-5">
          <Input
            label="Email"
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            autoComplete="email"
            required
          />
          <Input
            label="Password"
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            autoComplete="current-password"
            required
          />
          <Button type="submit" variant="gold" fullWidth size="lg" loading={loading}>
            Sign In
          </Button>
        </form>
      </div>
    </div>
  )
}

import { useState } from 'react'
import { motion } from 'framer-motion'
import { Button } from '@/components/ui/Button'
import { ShieldCheck } from 'lucide-react'

const AGE_GATE_KEY = 'bl_age_confirmed'

function AgeGateScreen({ onConfirm }: { onConfirm: () => void }) {
  return (
    <div className="min-h-screen flex items-center justify-center bg-black px-4">
      <motion.div
        initial={{ opacity: 0, y: 24 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.4 }}
        className="max-w-md w-full text-center space-y-8"
      >
        <div className="space-y-2">
          <h1 className="font-serif text-5xl gold-text tracking-tight">BLUECHIPS</h1>
          <p className="text-stone-500 text-xs uppercase tracking-[0.3em]">London</p>
        </div>

        <div className="w-px h-12 bg-gold-400/30 mx-auto" />

        <div className="space-y-4">
          <div className="flex justify-center">
            <div className="w-16 h-16 rounded-full bg-gold-400/10 border border-gold-400/30 flex items-center justify-center">
              <ShieldCheck className="w-8 h-8 text-gold-400" />
            </div>
          </div>
          <h2 className="font-serif text-2xl text-ivory-100">Age Verification Required</h2>
          <p className="text-stone-400 text-sm leading-relaxed max-w-xs mx-auto">
            This website contains adult content intended for individuals aged 18 and over.
            By entering, you confirm you are at least 18 years of age.
          </p>
        </div>

        <div className="space-y-3">
          <Button variant="gold" size="lg" fullWidth onClick={onConfirm}>
            I am 18 or older — Enter
          </Button>
          <a
            href="https://www.google.com"
            className="block text-center text-stone-600 text-sm hover:text-stone-400 transition-colors py-2"
          >
            I am under 18 — Exit
          </a>
        </div>

        <p className="text-stone-700 text-xs leading-relaxed border-t border-surface-border pt-6">
          Bluechips London is a marketing directory for independent adult entertainers.
          We are not an escort agency and do not handle any payments between clients and companions.
        </p>
      </motion.div>
    </div>
  )
}

export function AgeGate({ children }: { children: React.ReactNode }) {
  const [confirmed, setConfirmed] = useState(() => {
    try { return localStorage.getItem(AGE_GATE_KEY) === 'true' } catch { return false }
  })

  const handleConfirm = () => {
    try { localStorage.setItem(AGE_GATE_KEY, 'true') } catch { /* private browsing — continue anyway */ }
    setConfirmed(true)
  }

  if (!confirmed) {
    return <AgeGateScreen onConfirm={handleConfirm} />
  }

  return <>{children}</>
}

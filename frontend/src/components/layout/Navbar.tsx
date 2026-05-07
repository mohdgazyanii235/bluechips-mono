import { useState, useEffect } from 'react'
import { Link, useLocation, useNavigate } from 'react-router-dom'
import { motion, AnimatePresence } from 'framer-motion'
import { Menu, X, ChevronDown, User, LogOut, LayoutDashboard, CreditCard } from 'lucide-react'
import { useAuthStore } from '@/store/authStore'
import { Button } from '@/components/ui/Button'
import { cn } from '@/utils/cn'

const NAV_LINKS_PUBLIC = [
  { label: 'Browse', href: '/escorts' },
  { label: 'London Areas', href: '/areas' },
  { label: 'Blog', href: 'https://blog.bluechips.live', external: true },
  { label: 'Join Us', href: '/join' },
  { label: 'About', href: '/about' },
]

const NAV_LINKS_AUTH = [
  { label: 'Browse', href: '/escorts' },
  { label: 'London Areas', href: '/areas' },
  { label: 'Blog', href: 'https://blog.bluechips.live', external: true },
  { label: 'About', href: '/about' },
]

export function Navbar() {
  const [mobileOpen, setMobileOpen] = useState(false)
  const [scrolled, setScrolled] = useState(false)
  const [profileMenuOpen, setProfileMenuOpen] = useState(false)
  const { isAuthenticated, stage_name, logout } = useAuthStore()
  const location = useLocation()
  const navigate = useNavigate()
  const navLinks = isAuthenticated ? NAV_LINKS_AUTH : NAV_LINKS_PUBLIC

  useEffect(() => {
    const onScroll = () => setScrolled(window.scrollY > 20)
    window.addEventListener('scroll', onScroll, { passive: true })
    return () => window.removeEventListener('scroll', onScroll)
  }, [])

  useEffect(() => {
    setMobileOpen(false)
    setProfileMenuOpen(false)
  }, [location])

  return (
    <header
      className={cn(
        'fixed top-0 left-0 right-0 z-40 transition-all duration-300',
        scrolled
          ? 'bg-black/95 backdrop-blur-md border-b border-surface-border'
          : 'bg-transparent'
      )}
    >
      <nav className="page-container">
        <div className="flex items-center justify-between h-16 lg:h-20">
          {/* Logo */}
          <Link to="/" className="flex flex-col leading-none group">
            <span className="font-serif text-xl lg:text-2xl gold-text tracking-tight transition-all">
              BLUECHIPS
            </span>
            <span className="text-stone-500 text-[10px] uppercase tracking-[0.25em] -mt-0.5 group-hover:text-gold-500 transition-colors">
              London
            </span>
          </Link>

          {/* Desktop Nav */}
          <div className="hidden lg:flex items-center gap-8">
            {navLinks.map((link) =>
              link.external ? (
                <a
                  key={link.href}
                  href={link.href}
                  className="text-sm font-medium text-stone-400 hover:text-ivory-100 transition-colors duration-200"
                >
                  {link.label}
                </a>
              ) : (
                <Link
                  key={link.href}
                  to={link.href}
                  className={cn(
                    'text-sm font-medium transition-colors duration-200',
                    location.pathname === link.href
                      ? 'text-gold-400'
                      : 'text-stone-400 hover:text-ivory-100'
                  )}
                >
                  {link.label}
                </Link>
              )
            )}
          </div>

          {/* Desktop Auth */}
          <div className="hidden lg:flex items-center gap-3">
            {isAuthenticated ? (
              <div className="relative">
                <button
                  onClick={() => setProfileMenuOpen(!profileMenuOpen)}
                  className="flex items-center gap-2 text-sm text-ivory-200 hover:text-gold-400 transition-colors py-2 px-3 rounded-lg hover:bg-surface-hover"
                >
                  <div className="w-7 h-7 rounded-full bg-gold-400/20 border border-gold-400/40 flex items-center justify-center">
                    <span className="text-gold-400 text-xs font-semibold">{stage_name?.[0]?.toUpperCase()}</span>
                  </div>
                  <span className="max-w-[120px] truncate">{stage_name}</span>
                  <ChevronDown className={cn('w-3.5 h-3.5 transition-transform', profileMenuOpen && 'rotate-180')} />
                </button>

                <AnimatePresence>
                  {profileMenuOpen && (
                    <motion.div
                      initial={{ opacity: 0, y: 8, scale: 0.97 }}
                      animate={{ opacity: 1, y: 0, scale: 1 }}
                      exit={{ opacity: 0, y: 4, scale: 0.97 }}
                      transition={{ duration: 0.15 }}
                      className="absolute right-0 top-full mt-1 w-48 card-surface py-1 shadow-card z-50"
                    >
                      <Link to="/dashboard" className="flex items-center gap-2.5 px-4 py-2.5 text-sm text-stone-300 hover:text-ivory-100 hover:bg-surface-hover transition-colors">
                        <LayoutDashboard className="w-4 h-4" /> Dashboard
                      </Link>
                      <Link to="/dashboard/profile" className="flex items-center gap-2.5 px-4 py-2.5 text-sm text-stone-300 hover:text-ivory-100 hover:bg-surface-hover transition-colors">
                        <User className="w-4 h-4" /> My Profile
                      </Link>
                      <Link to="/dashboard/subscriptions" className="flex items-center gap-2.5 px-4 py-2.5 text-sm text-stone-300 hover:text-ivory-100 hover:bg-surface-hover transition-colors">
                        <CreditCard className="w-4 h-4" /> My Subscriptions
                      </Link>
                      <div className="border-t border-surface-border my-1" />
                      <button
                        onClick={logout}
                        className="flex items-center gap-2.5 w-full px-4 py-2.5 text-sm text-stone-400 hover:text-red-400 hover:bg-surface-hover transition-colors"
                      >
                        <LogOut className="w-4 h-4" /> Sign Out
                      </button>
                    </motion.div>
                  )}
                </AnimatePresence>
              </div>
            ) : (
              <>
                <Link to="/login">
                  <Button variant="ghost" size="sm">Sign In</Button>
                </Link>
                <Link to="/join">
                  <Button variant="outline-gold" size="sm">List Your Profile</Button>
                </Link>
              </>
            )}
          </div>

          {/* Mobile Hamburger */}
          <button
            onClick={() => setMobileOpen(!mobileOpen)}
            className="lg:hidden text-stone-300 hover:text-ivory-100 transition-colors p-2"
          >
            {mobileOpen ? <X className="w-6 h-6" /> : <Menu className="w-6 h-6" />}
          </button>
        </div>
      </nav>

      {/* Mobile Menu */}
      <AnimatePresence>
        {mobileOpen && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: 'auto' }}
            exit={{ opacity: 0, height: 0 }}
            className="lg:hidden bg-black/98 border-t border-surface-border overflow-hidden"
          >
            <div className="page-container py-4 space-y-1">
              {navLinks.map((link) =>
                link.external ? (
                  <a
                    key={link.href}
                    href={link.href}
                    className="block px-3 py-3 text-stone-300 hover:text-gold-400 font-medium transition-colors"
                  >
                    {link.label}
                  </a>
                ) : (
                  <Link
                    key={link.href}
                    to={link.href}
                    className="block px-3 py-3 text-stone-300 hover:text-gold-400 font-medium transition-colors"
                  >
                    {link.label}
                  </Link>
                )
              )}
              <div className="border-t border-surface-border pt-4 mt-4 space-y-2">
                {isAuthenticated ? (
                  <>
                    <Link to="/dashboard" className="block px-3 py-2 text-stone-300">Dashboard</Link>
                    <Link to="/dashboard/profile" className="block px-3 py-2 text-stone-300">My Profile</Link>
                    <Link to="/dashboard/subscriptions" className="block px-3 py-2 text-stone-300">My Subscriptions</Link>
                    <button onClick={logout} className="block px-3 py-2 text-stone-500 w-full text-left">Sign Out</button>
                  </>
                ) : (
                  <>
                    <Link to="/login" className="block"><Button variant="ghost" fullWidth>Sign In</Button></Link>
                    <Link to="/join"><Button variant="gold" fullWidth>List Your Profile</Button></Link>
                  </>
                )}
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </header>
  )
}

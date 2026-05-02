import { Link } from 'react-router-dom'

export function Footer() {
  return (
    <footer className="border-t border-surface-border bg-black mt-24">
      <div className="page-container py-16">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-10">
          {/* Brand */}
          <div className="md:col-span-1 space-y-4">
            <div>
              <h2 className="font-serif text-2xl gold-text tracking-tight">BLUECHIPS</h2>
              <p className="text-stone-600 text-[10px] uppercase tracking-[0.3em]">London</p>
            </div>
            <p className="text-stone-500 text-sm leading-relaxed">
              London's most exclusive companion marketing directory.
            </p>
          </div>

          {/* Browse */}
          <div className="space-y-4">
            <h3 className="text-xs uppercase tracking-widest text-stone-500 font-medium">Browse</h3>
            <ul className="space-y-2.5">
              {[
                { label: 'All Companions', href: '/escorts' },
                { label: 'London Areas', href: '/areas' },
                { label: 'Available Now', href: '/escorts?available_now=true' },
                { label: 'Blue Tick Verified', href: '/escorts?blue_tick_only=true' },
                { label: 'STD Tested', href: '/escorts?std_tested=true' },
              ].map((link) => (
                <li key={link.href}>
                  <Link to={link.href} className="text-stone-400 text-sm hover:text-gold-400 transition-colors">
                    {link.label}
                  </Link>
                </li>
              ))}
            </ul>
          </div>

          {/* For Companions */}
          <div className="space-y-4">
            <h3 className="text-xs uppercase tracking-widest text-stone-500 font-medium">For Companions</h3>
            <ul className="space-y-2.5">
              {[
                { label: 'List Your Profile', href: '/join' },
                { label: 'Pricing & Plans', href: '/join#pricing' },
                { label: 'Blue Tick Verification', href: '/join#verification' },
                { label: 'Sign In', href: '/login' },
                { label: 'Dashboard', href: '/dashboard' },
              ].map((link) => (
                <li key={link.href}>
                  <Link to={link.href} className="text-stone-400 text-sm hover:text-gold-400 transition-colors">
                    {link.label}
                  </Link>
                </li>
              ))}
            </ul>
          </div>

          {/* Legal */}
          <div className="space-y-4">
            <h3 className="text-xs uppercase tracking-widest text-stone-500 font-medium">Company</h3>
            <ul className="space-y-2.5">
              {[
                { label: 'About Us', href: '/about' },
                { label: 'Safety & Trust', href: '/safety' },
                { label: 'Privacy Policy', href: '/privacy' },
                { label: 'Terms of Service', href: '/terms' },
                { label: 'Contact', href: '/contact' },
              ].map((link) => (
                <li key={link.href}>
                  <Link to={link.href} className="text-stone-400 text-sm hover:text-gold-400 transition-colors">
                    {link.label}
                  </Link>
                </li>
              ))}
            </ul>
          </div>
        </div>

        {/* Legal Disclaimer */}
        <div className="mt-12 pt-8 border-t border-surface-border space-y-4">
          <p className="text-stone-600 text-xs leading-relaxed max-w-3xl">
            <strong className="text-stone-500">Platform Notice:</strong> Bluechips London is an independent advertising platform for self-employed adult entertainers, operating on the same model as Gumtree or Fiverr. We are a technology intermediary — we do not employ, represent, manage, or act as agent for any individual listed on this platform, and we have no involvement in any arrangement, booking, or payment made between clients and companions. All listings are created and controlled solely by the self-employed individuals advertising on this platform. All companions have self-certified they are 18+ years of age; paid subscribers undergo identity verification by our review team. By using this site you confirm you are 18 years of age or over and accept our Terms of Service.
          </p>
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
            <p className="text-stone-700 text-xs">
              © {new Date().getFullYear()} Bluechips London. All rights reserved. UK-based platform.
            </p>
            <p className="text-stone-700 text-xs">
              Adults only · 18+ · Compliant with UK Online Safety Act 2023 & UK GDPR
            </p>
          </div>
        </div>
      </div>
    </footer>
  )
}

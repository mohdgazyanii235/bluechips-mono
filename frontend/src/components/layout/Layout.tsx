import { Navbar } from './Navbar'
import { Footer } from './Footer'

interface LayoutProps {
  children: React.ReactNode
  hideFooter?: boolean
}

export function Layout({ children, hideFooter }: LayoutProps) {
  return (
    <div className="min-h-screen flex flex-col">
      <Navbar />
      <main className="flex-1 pt-16 lg:pt-20">
        {children}
      </main>
      {!hideFooter && <Footer />}
    </div>
  )
}

export function DashboardLayout({ children }: { children: React.ReactNode }) {
  return (
    <div className="min-h-screen flex flex-col">
      <Navbar />
      <div className="flex-1 pt-16 lg:pt-20">
        {children}
      </div>
    </div>
  )
}

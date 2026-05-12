export default function DevBanner() {
  if (!import.meta.env.DEV) return null

  return (
    <div style={{
      position: 'fixed',
      bottom: 0,
      left: 0,
      right: 0,
      zIndex: 9999,
      background: '#7c3aed',
      color: '#fff',
      textAlign: 'center',
      padding: '6px 12px',
      fontSize: '12px',
      fontFamily: 'monospace',
      letterSpacing: '0.5px',
      pointerEvents: 'none',
    }}>
      LOCAL DEV — API calls go to localhost · emails suppressed · not connected to production
    </div>
  )
}

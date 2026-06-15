import { useState } from 'react'
import { api } from '../api/client'
import { useSession } from '../store/sessionStore'

const DEVICE_TYPES = [
  { key: 'laptop',  label: 'Laptop',          icon: '💻', desc: 'Standard business laptop' },
  { key: 'charger', label: 'Charger',          icon: '🔌', desc: 'USB-C or laptop charger' },
  { key: 'mouse',   label: 'Mouse / Keyboard', icon: '🖱️', desc: 'Wired or wireless peripherals' },
  { key: 'monitor', label: 'Monitor',          icon: '🖥️', desc: 'External display' },
]

export default function LoanerScreen() {
  const { setScreen, setLoanerId, reset } = useSession()
  const [selected, setSelected] = useState('laptop')
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState<any>(null)

  const handleRequest = async () => {
    setLoading(true)
    try {
      const res = await api.post('/loaner/request', { device_type: selected })
      setResult(res.data); setLoanerId(res.data.loaner_id)
    } catch {
      setResult({ message: 'Request failed. Please speak to a Service Desk agent.' })
    } finally { setLoading(false) }
  }

  if (result) {
    return (
      <div className="ted-screen items-center justify-center text-center">
        <div className="orb" style={{ width: 400, height: 400, top: '50%', left: '50%', transform: 'translate(-50%,-50%)', background: 'radial-gradient(circle, rgba(34,211,238,.1) 0%, transparent 90%)' }} />
        <div style={{ position: 'relative', zIndex: 1, maxWidth: 440, padding: '0 24px', width: '100%' }}>
          <div className="ted-card" style={{ padding: 48 }}>
            <div style={{ width: 72, height: 72, borderRadius: '50%', background: 'rgba(34,211,238,.1)', border: '1px solid rgba(34,211,238,.3)', display: 'grid', placeItems: 'center', margin: '0 auto 28px', boxShadow: '0 0 30px var(--cyan-glow)' }}>
              <svg viewBox="0 0 24 24" fill="var(--cyan)" style={{ width: 34, height: 34 }}><path d="M20 6h-2.18c.07-.44.18-.88.18-1.34C18 2.54 15.8.36 13.18.04 11.68-.15 10.22.28 9.1 1.18L7.75 2.27C7.19 2.72 7 3.44 7.24 4.08L7.3 4.24c.37.98 1.41 1.5 2.41 1.24L11 5.12c.68-.18 1.4-.13 2.06.14l-.5.5c-.97.97-1.47 2.28-1.43 3.6L5 9.38V11h3l-2 4h2v7l1-1V15h6l1 1v-7h2l-2-4h3V9.38l-6.14.38c-.04-.54.14-1.07.5-1.48l1.28-1.43c.62.18 1.27.27 1.86.09L17 5.88c.67.37 1.1 1.05 1 1.79-.04.27-.05.55-.04.83H19c1.1 0 2 .9 2 2v9c0 1.1-.9 2-2 2H5c-1.1 0-2-.9-2-2V10.5C3 9.4 3.9 8.5 5 8.5h2v-2H5c-2.21 0-4 1.79-4 4V19c0 2.21 1.79 4 4 4h14c2.21 0 4-1.79 4-4v-8.5c0-2.21-1.79-4-4-4z"/></svg>
            </div>
            <span className="section-tag">Loaner Ready</span>
            <h1 style={{ fontSize: '1.9rem', fontWeight: 800, letterSpacing: '-.03em', color: 'var(--text)', marginBottom: 12 }}>Device Dispensed</h1>
            <p style={{ color: 'var(--text-muted)', marginBottom: 24, fontSize: '.95rem' }}>{result.message}</p>
            {result.loaner_id && (
              <div style={{ display: 'inline-flex', alignItems: 'center', gap: 10, padding: '10px 20px', background: 'var(--surface-hi)', border: '1px solid var(--border-hi)', borderRadius: 'var(--radius)', marginBottom: 32 }}>
                <span style={{ fontFamily: 'monospace', fontSize: '1rem', fontWeight: 700, color: 'var(--cyan)' }}>{result.loaner_id}</span>
              </div>
            )}
            <button onClick={reset} className="btn-primary" style={{ width: '100%', padding: '14px', fontSize: '1rem', borderRadius: 'var(--radius)' }}>
              Done — End Session
            </button>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="ted-screen">
      {/* Nav */}
      <nav className="ted-nav">
        <button className="btn-ghost" onClick={() => setScreen('HOME')} style={{ padding: '7px 14px', fontSize: '.82rem' }}>← Back</button>
        <span style={{ color: 'var(--text-dim)', fontSize: '.82rem' }}>TED · Loaner Device</span>
        <span style={{ width: 80 }} />
      </nav>

      <div style={{ flex: 1, display: 'flex', flexDirection: 'column', padding: '32px 40px', position: 'relative', zIndex: 1 }}>
        <div className="orb" style={{ width: 300, height: 300, top: -60, right: -60, background: 'radial-gradient(circle, rgba(34,211,238,.08) 0%, transparent 90%)' }} />

        <div style={{ marginBottom: 32 }}>
          <span className="section-tag">Device Lending</span>
          <h1 style={{ fontSize: '2rem', fontWeight: 800, letterSpacing: '-.03em', color: 'var(--text)', lineHeight: 1.1 }}>
            Request a loaner device
          </h1>
          <p style={{ color: 'var(--text-muted)', marginTop: 8, fontSize: '.9rem' }}>
            Select the device type and it will be dispensed from the locker
          </p>
        </div>

        {/* Device grid */}
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16, marginBottom: 28, flex: 1 }}>
          {DEVICE_TYPES.map((d) => {
            const isSelected = selected === d.key
            return (
              <button
                key={d.key}
                onClick={() => setSelected(d.key)}
                className="ted-card"
                style={{
                  display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center',
                  padding: '32px 20px', cursor: 'pointer', textAlign: 'center',
                  borderColor: isSelected ? 'var(--cyan)' : 'var(--border)',
                  background: isSelected ? 'rgba(34,211,238,.06)' : 'var(--surface)',
                  boxShadow: isSelected ? '0 0 30px rgba(34,211,238,.12)' : 'none',
                  transition: 'all .2s',
                }}
              >
                <div style={{ fontSize: '2.4rem', marginBottom: 12 }}>{d.icon}</div>
                <span style={{ fontWeight: 700, fontSize: '.95rem', color: isSelected ? 'var(--cyan)' : 'var(--text)', marginBottom: 4 }}>
                  {d.label}
                </span>
                <span style={{ fontSize: '.78rem', color: 'var(--text-dim)' }}>{d.desc}</span>
                {isSelected && (
                  <div style={{ marginTop: 10, width: 20, height: 20, borderRadius: '50%', background: 'var(--cyan)', display: 'grid', placeItems: 'center' }}>
                    <svg viewBox="0 0 24 24" fill="#07111e" style={{ width: 12, height: 12 }}><path d="M9 16.17L4.83 12l-1.42 1.41L9 19 21 7l-1.41-1.41z"/></svg>
                  </div>
                )}
              </button>
            )
          })}
        </div>

        <button
          onClick={handleRequest}
          disabled={loading}
          className="btn-primary"
          style={{ padding: '15px', fontSize: '1rem', borderRadius: 'var(--radius)', opacity: loading ? 0.5 : 1 }}
        >
          {loading ? 'Requesting…' : `Request ${DEVICE_TYPES.find(d => d.key === selected)?.label ?? 'Device'} →`}
        </button>
      </div>
    </div>
  )
}

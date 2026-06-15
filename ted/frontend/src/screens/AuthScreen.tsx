import { useState } from 'react'
import { api, setAuthHeader } from '../api/client'
import { useSession } from '../store/sessionStore'

export default function AuthScreen() {
  const { setAuth, setScreen } = useSession()
  const [employeeId, setEmployeeId] = useState('')
  const [displayName, setDisplayName] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  const handleLogin = async () => {
    if (!employeeId.trim()) { setError('Please enter your Employee ID'); return }
    setLoading(true); setError('')
    try {
      const res = await api.post('/auth/session', {
        employee_id: employeeId.trim(),
        display_name: displayName.trim() || employeeId.trim(),
        kiosk_id: 'KIOSK-001', auth_method: 'sso',
      })
      const { token, session_id, employee } = res.data
      setAuthHeader(token)
      setAuth(token, session_id, employee)
    } catch {
      setError('Login failed. Please try again or contact IT.')
    } finally { setLoading(false) }
  }

  return (
    <div className="ted-screen items-center justify-center">
      <div className="orb" style={{ width: 500, height: 500, top: -150, left: '50%', transform: 'translateX(-50%)', background: 'radial-gradient(circle, rgba(59,130,246,.14) 0%, transparent 70%)' }} />

      <div style={{ position: 'relative', zIndex: 1, width: '100%', maxWidth: 460, padding: '0 24px' }}>
        {/* Back */}
        <button onClick={() => setScreen('IDLE')} className="btn-ghost" style={{ padding: '8px 16px', fontSize: '.85rem', marginBottom: 40 }}>
          ← Back
        </button>

        {/* Card */}
        <div className="ted-card" style={{ padding: 40 }}>
          {/* Logo row */}
          <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 32 }}>
            <div style={{ width: 36, height: 36, borderRadius: 9, background: 'linear-gradient(135deg, var(--blue), var(--cyan))', display: 'grid', placeItems: 'center', boxShadow: '0 0 18px var(--cyan-glow)' }}>
              <svg viewBox="0 0 24 24" fill="white" style={{ width: 18, height: 18 }}><path d="M20 4H4c-1.1 0-2 .9-2 2v10c0 1.1.9 2 2 2h7v2H9v2h6v-2h-2v-2h7c1.1 0 2-.9 2-2V6c0-1.1-.9-2-2-2zm0 12H4V6h16v10z"/></svg>
            </div>
            <span style={{ fontWeight: 800, fontSize: '1.1rem', color: 'var(--text)', letterSpacing: '-.02em' }}>TED <span style={{ color: 'var(--cyan)' }}>Kiosk</span></span>
          </div>

          <span className="section-tag">Employee Authentication</span>
          <h1 style={{ fontSize: '2rem', fontWeight: 800, letterSpacing: '-.03em', color: 'var(--text)', marginBottom: 6 }}>Sign in</h1>
          <p style={{ color: 'var(--text-muted)', fontSize: '.95rem', marginBottom: 32 }}>Enter your Employee ID to start a support session</p>

          <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
            <div>
              <label style={{ display: 'block', fontSize: '.78rem', fontWeight: 600, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '.08em', marginBottom: 8 }}>Employee ID</label>
              <input
                className="ted-input"
                style={{ padding: '14px 18px', fontSize: '1.05rem' }}
                placeholder="e.g. EMP-12345"
                value={employeeId}
                onChange={(e) => setEmployeeId(e.target.value)}
                onKeyDown={(e) => e.key === 'Enter' && handleLogin()}
                autoFocus
              />
            </div>
            <div>
              <label style={{ display: 'block', fontSize: '.78rem', fontWeight: 600, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '.08em', marginBottom: 8 }}>Display Name <span style={{ color: 'var(--text-dim)', fontWeight: 400, textTransform: 'none' }}>(optional)</span></label>
              <input
                className="ted-input"
                style={{ padding: '14px 18px', fontSize: '1.05rem' }}
                placeholder="Your full name"
                value={displayName}
                onChange={(e) => setDisplayName(e.target.value)}
                onKeyDown={(e) => e.key === 'Enter' && handleLogin()}
              />
            </div>
          </div>

          {error && (
            <div style={{ marginTop: 14, padding: '10px 14px', background: 'rgba(239,68,68,.1)', border: '1px solid rgba(239,68,68,.3)', borderRadius: 8, color: '#fca5a5', fontSize: '.85rem' }}>
              {error}
            </div>
          )}

          <button
            className="btn-primary"
            onClick={handleLogin}
            disabled={loading}
            style={{ width: '100%', padding: '15px', fontSize: '1rem', marginTop: 28, borderRadius: 'var(--radius)' }}
          >
            {loading ? (
              <><span style={{ display: 'inline-block', width: 16, height: 16, border: '2px solid rgba(0,0,0,.3)', borderTop: '2px solid rgba(0,0,0,.8)', borderRadius: '50%', animation: 'spin .7s linear infinite' }} /> Signing in…</>
            ) : 'Continue →'}
          </button>
        </div>

        <p style={{ textAlign: 'center', color: 'var(--text-dim)', fontSize: '.78rem', marginTop: 20 }}>
          Session protected by JWT · Auto-expires in 60 min
        </p>
      </div>
    </div>
  )
}

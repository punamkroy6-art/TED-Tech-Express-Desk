import { api, setAuthHeader } from '../api/client'
import { useSession } from '../store/sessionStore'

const ISSUE_TYPES = [
  { key: 'software', label: 'Software / App', icon: '🖥️', desc: 'Crashes, errors, slow performance', color: 'var(--blue)' },
  { key: 'network',  label: 'Network / Wi-Fi', icon: '📡', desc: 'VPN, no internet, slow connection', color: 'var(--cyan)' },
  { key: 'hardware', label: 'Hardware',         icon: '🔧', desc: 'Screen, keyboard, power, USB',    color: 'var(--purple)' },
  { key: 'password', label: 'Password / Access',icon: '🔐', desc: 'Locked account, expired password', color: 'var(--amber)' },
  { key: 'loaner',   label: 'Loaner Device',    icon: '📦', desc: 'Borrow a temporary device',        color: 'var(--green)' },
  { key: 'other',    label: 'Something else',   icon: '💬', desc: 'Describe your issue in detail',    color: 'var(--text-muted)' },
]

export default function HomeScreen() {
  const { employee, setScreen, reset } = useSession()

  const handleLogout = async () => {
    try { await api.delete('/auth/session') } catch {}
    setAuthHeader(null); reset()
  }

  const handleSelect = (key: string) => {
    setScreen(key === 'loaner' ? 'LOANER' : 'DIAGNOSE')
  }

  return (
    <div className="ted-screen">
      {/* Top nav */}
      <nav className="ted-nav">
        <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
          <div style={{ width: 30, height: 30, borderRadius: 7, background: 'linear-gradient(135deg, var(--blue), var(--cyan))', display: 'grid', placeItems: 'center', boxShadow: '0 0 14px var(--cyan-glow)' }}>
            <svg viewBox="0 0 24 24" fill="white" style={{ width: 15, height: 15 }}><path d="M20 4H4c-1.1 0-2 .9-2 2v10c0 1.1.9 2 2 2h7v2H9v2h6v-2h-2v-2h7c1.1 0 2-.9 2-2V6c0-1.1-.9-2-2-2zm0 12H4V6h16v10z"/></svg>
          </div>
          <span style={{ fontWeight: 800, fontSize: '1rem', color: 'var(--text)', letterSpacing: '-.02em' }}>TED <span style={{ color: 'var(--cyan)' }}>Kiosk</span></span>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
          <span className="eyebrow" style={{ fontSize: '.65rem' }}>
            <span className="pulse-dot" />
            {employee?.name || 'Employee'}
          </span>
          <button
            className="btn-ghost"
            onClick={handleLogout}
            style={{ padding: '7px 16px', fontSize: '.82rem' }}
          >
            End Session
          </button>
        </div>
      </nav>

      {/* Body */}
      <div style={{ flex: 1, display: 'flex', flexDirection: 'column', padding: '36px 40px', position: 'relative', zIndex: 1, overflow: 'hidden' }}>
        <div className="orb" style={{ width: 400, height: 400, top: -100, right: -100, background: 'radial-gradient(circle, rgba(59,130,246,.12) 0%, transparent 70%)' }} />

        {/* Header */}
        <div style={{ marginBottom: 32 }}>
          <span className="section-tag">Support Session</span>
          <h1 style={{ fontSize: 'clamp(1.8rem, 4vw, 2.6rem)', fontWeight: 800, letterSpacing: '-.03em', color: 'var(--text)', lineHeight: 1.1 }}>
            Hi, {employee?.name?.split(' ')[0] || 'there'} 👋
          </h1>
          <p style={{ color: 'var(--text-muted)', marginTop: 8, fontSize: '1rem' }}>
            What can we help you with today?
          </p>
        </div>

        {/* Issue grid */}
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 16, flex: 1 }}>
          {ISSUE_TYPES.map((issue) => (
            <button
              key={issue.key}
              onClick={() => handleSelect(issue.key)}
              className="ted-card"
              style={{ display: 'flex', flexDirection: 'column', alignItems: 'flex-start', padding: '28px 24px', cursor: 'pointer', border: '1px solid var(--border)', textAlign: 'left', position: 'relative', overflow: 'hidden', transition: 'border-color .3s, transform .2s, box-shadow .3s' }}
              onMouseOver={e => { (e.currentTarget as HTMLElement).style.borderColor = issue.color; (e.currentTarget as HTMLElement).style.transform = 'translateY(-3px)'; (e.currentTarget as HTMLElement).style.boxShadow = `0 16px 40px rgba(0,0,0,.4)`; }}
              onMouseOut={e => { (e.currentTarget as HTMLElement).style.borderColor = 'var(--border)'; (e.currentTarget as HTMLElement).style.transform = 'none'; (e.currentTarget as HTMLElement).style.boxShadow = 'none'; }}
            >
              {/* Top accent line */}
              <div style={{ position: 'absolute', top: 0, left: 0, right: 0, height: 2, background: `linear-gradient(90deg, transparent, ${issue.color}, transparent)`, opacity: 0 }} />

              {/* Icon box */}
              <div style={{ width: 44, height: 44, borderRadius: 11, background: `${issue.color}22`, border: `1px solid ${issue.color}44`, display: 'grid', placeItems: 'center', fontSize: '1.3rem', marginBottom: 16 }}>
                {issue.icon}
              </div>

              <span style={{ fontWeight: 700, fontSize: '1rem', color: 'var(--text)', marginBottom: 6, letterSpacing: '-.01em' }}>
                {issue.label}
              </span>
              <span style={{ fontSize: '.82rem', color: 'var(--text-dim)', lineHeight: 1.5 }}>
                {issue.desc}
              </span>

              {/* Arrow */}
              <span style={{ position: 'absolute', bottom: 20, right: 20, color: 'var(--border-hi)', fontSize: '.8rem' }}>→</span>
            </button>
          ))}
        </div>
      </div>
    </div>
  )
}

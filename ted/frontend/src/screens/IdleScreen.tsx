import { useSession } from '../store/sessionStore'

export default function IdleScreen() {
  const setScreen = useSession((s) => s.setScreen)

  return (
    <div
      className="ted-screen items-center justify-center cursor-pointer select-none text-center"
      onClick={() => setScreen('AUTH')}
    >
      {/* Background orbs */}
      <div className="orb" style={{ width: 600, height: 600, top: -200, left: '50%', transform: 'translateX(-50%)', background: 'radial-gradient(circle, rgba(59,130,246,.18) 0%, transparent 90%)' }} />
      <div className="orb" style={{ width: 300, height: 300, bottom: 40, left: -80, background: 'radial-gradient(circle, rgba(139,92,246,.12) 0%, transparent 90%)' }} />
      <div className="orb" style={{ width: 250, height: 250, bottom: 60, right: -60, background: 'radial-gradient(circle, rgba(34,211,238,.1) 0%, transparent 90%)' }} />

      {/* Content */}
      <div style={{ position: 'relative', zIndex: 1 }}>
        {/* Logo mark */}
        <div style={{ display: 'inline-flex', alignItems: 'center', justifyContent: 'center', width: 96, height: 96, borderRadius: 24, background: 'linear-gradient(135deg, var(--blue), var(--cyan))', boxShadow: '0 0 60px var(--cyan-glow)', marginBottom: 32 }}>
          <svg viewBox="0 0 24 24" fill="white" style={{ width: 48, height: 48 }}>
            <path d="M20 4H4c-1.1 0-2 .9-2 2v10c0 1.1.9 2 2 2h7v2H9v2h6v-2h-2v-2h7c1.1 0 2-.9 2-2V6c0-1.1-.9-2-2-2zm0 12H4V6h16v10z"/>
          </svg>
        </div>

        {/* Eyebrow */}
        <div style={{ display: 'flex', justifyContent: 'center', marginBottom: 24 }}>
          <span className="eyebrow">
            <span className="pulse-dot" />
            AI-Powered IT Support
          </span>
        </div>

        {/* Headline */}
        <h1 style={{ fontSize: 'clamp(4rem, 10vw, 7rem)', fontWeight: 900, letterSpacing: '-0.04em', lineHeight: 1, marginBottom: 16 }}>
          <span className="gradient-text">TED</span>
        </h1>
        <p style={{ fontSize: '1.4rem', fontWeight: 300, color: 'var(--text-muted)', marginBottom: 8 }}>
          Tech Express Desk
        </p>
        <p style={{ fontSize: '1rem', color: 'var(--text-dim)', marginBottom: 56 }}>
          Self-service IT support · Instant AI diagnosis · Auto-fix
        </p>

        {/* CTA */}
        <div style={{ display: 'inline-flex', alignItems: 'center', gap: 12, background: 'linear-gradient(135deg, var(--blue), var(--cyan))', color: '#07111e', fontWeight: 700, fontSize: '1.05rem', padding: '16px 40px', borderRadius: 999, boxShadow: '0 0 40px var(--cyan-glow)', animation: 'pulse-glow 2.5s ease-in-out infinite' }}>
          <svg viewBox="0 0 24 24" fill="currentColor" style={{ width: 18, height: 18 }}>
            <path d="M9 11.24V7.5C9 6.12 10.12 5 11.5 5S14 6.12 14 7.5v3.74c1.21-.81 2-2.18 2-3.74C16 5.01 13.99 3 11.5 3S7 5.01 7 7.5c0 1.56.79 2.93 2 3.74zm9.84 4.63l-4.54-2.26c-.17-.07-.35-.11-.54-.11H13v-6c0-.83-.67-1.5-1.5-1.5S10 6.67 10 7.5v10.74l-3.43-.72c-.08-.01-.15-.03-.24-.03-.31 0-.59.13-.79.33l-.79.8 4.94 4.94c.27.27.65.44 1.06.44h6.79c.75 0 1.33-.55 1.44-1.28l.75-5.27c.01-.07.02-.14.02-.2 0-.62-.38-1.16-.91-1.38z"/>
          </svg>
          Tap anywhere to get started
        </div>

        {/* Footer info */}
        <div style={{ marginTop: 48, display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 24 }}>
          <span style={{ color: 'var(--text-dim)', fontSize: '.8rem' }}>KIOSK-001 · Building A · Level 2</span>
          <span style={{ width: 1, height: 14, background: 'var(--border-hi)' }} />
          <a
            href="https://keen-rabanadas-f6666c.netlify.app"
            target="_blank"
            rel="noopener noreferrer"
            onClick={(e) => e.stopPropagation()}
            style={{ display: 'inline-flex', alignItems: 'center', gap: 6, color: 'var(--text-dim)', fontSize: '.8rem', textDecoration: 'none', transition: 'color .2s' }}
            onMouseOver={e => (e.currentTarget.style.color = 'var(--cyan)')}
            onMouseOut={e => (e.currentTarget.style.color = 'var(--text-dim)')}
          >
            <svg viewBox="0 0 24 24" fill="currentColor" style={{ width: 12, height: 12 }}><path d="M12 4.5C7 4.5 2.73 7.61 1 12c1.73 4.39 6 7.5 11 7.5s9.27-3.11 11-7.5c-1.73-4.39-6-7.5-11-7.5zM12 17c-2.76 0-5-2.24-5-5s2.24-5 5-5 5 2.24 5 5-2.24 5-5 5zm0-8c-1.66 0-3 1.34-3 3s1.34 3 3 3 3-1.34 3-3-1.34-3-3-3z"/></svg>
            Powered by Vision AI ↗
          </a>
        </div>
      </div>
    </div>
  )
}

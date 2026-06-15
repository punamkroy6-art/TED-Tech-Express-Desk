import { useState } from 'react'
import { api } from '../api/client'
import { useSession } from '../store/sessionStore'

const LABELS: Record<number, { text: string; color: string }> = {
  1: { text: 'Very poor',  color: '#ef4444' },
  2: { text: 'Poor',       color: '#f97316' },
  3: { text: 'OK',         color: '#f59e0b' },
  4: { text: 'Good',       color: '#84cc16' },
  5: { text: 'Excellent',  color: '#22c55e' },
}

export default function CsatScreen() {
  const { reset } = useSession()
  const [score, setScore] = useState<number | null>(null)
  const [hovering, setHovering] = useState<number | null>(null)
  const [submitting, setSubmitting] = useState(false)
  const [done, setDone] = useState(false)

  const handleSubmit = async (s: number) => {
    setScore(s); setSubmitting(true)
    try { await api.post('/auth/session/outcome', { outcome: 'resolved', csat_score: s }) } catch {}
    setSubmitting(false); setDone(true)
    setTimeout(() => reset(), 2800)
  }

  if (done) {
    return (
      <div className="ted-screen items-center justify-center text-center">
        <div className="orb" style={{ width: 400, height: 400, top: '50%', left: '50%', transform: 'translate(-50%,-50%)', background: 'radial-gradient(circle, rgba(34,211,238,.12) 0%, transparent 90%)' }} />
        <div style={{ position: 'relative', zIndex: 1 }}>
          <div style={{ width: 80, height: 80, borderRadius: '50%', background: 'rgba(34,211,238,.12)', border: '2px solid var(--cyan)', display: 'grid', placeItems: 'center', margin: '0 auto 24px', boxShadow: '0 0 40px var(--cyan-glow)' }}>
            <svg viewBox="0 0 24 24" fill="var(--cyan)" style={{ width: 36, height: 36 }}><path d="M9 16.17L4.83 12l-1.42 1.41L9 19 21 7l-1.41-1.41z"/></svg>
          </div>
          <h1 style={{ fontSize: '2rem', fontWeight: 800, letterSpacing: '-.03em', color: 'var(--text)', marginBottom: 10 }}>Thanks for your feedback!</h1>
          <p style={{ color: 'var(--text-muted)' }}>Session ending in a moment…</p>
        </div>
      </div>
    )
  }

  const active = hovering ?? score
  const activeLabel = active ? LABELS[active] : null

  return (
    <div className="ted-screen items-center justify-center text-center">
      <div className="orb" style={{ width: 500, height: 500, top: -150, left: '50%', transform: 'translateX(-50%)', background: 'radial-gradient(circle, rgba(59,130,246,.12) 0%, transparent 90%)' }} />

      <div style={{ position: 'relative', zIndex: 1, maxWidth: 480, padding: '0 24px', width: '100%' }}>
        <div className="ted-card" style={{ padding: 48 }}>
          {/* Icon */}
          <div style={{ width: 64, height: 64, borderRadius: '50%', background: 'rgba(245,158,11,.12)', border: '1px solid rgba(245,158,11,.3)', display: 'grid', placeItems: 'center', margin: '0 auto 28px' }}>
            <svg viewBox="0 0 24 24" fill="#f59e0b" style={{ width: 30, height: 30 }}><path d="M12 17.27L18.18 21l-1.64-7.03L22 9.24l-7.19-.61L12 2 9.19 8.63 2 9.24l5.46 4.73L5.82 21z"/></svg>
          </div>

          <span className="section-tag">Session Complete</span>
          <h1 style={{ fontSize: '1.8rem', fontWeight: 800, letterSpacing: '-.03em', color: 'var(--text)', marginBottom: 8 }}>
            How was your experience?
          </h1>
          <p style={{ color: 'var(--text-muted)', fontSize: '.9rem', marginBottom: 36 }}>
            Rate your TED session — takes 5 seconds
          </p>

          {/* Stars */}
          <div style={{ display: 'flex', justifyContent: 'center', gap: 12, marginBottom: 16 }}>
            {[1, 2, 3, 4, 5].map((s) => {
              const lit = active !== null && s <= active
              return (
                <button
                  key={s}
                  onClick={() => handleSubmit(s)}
                  onMouseEnter={() => setHovering(s)}
                  onMouseLeave={() => setHovering(null)}
                  disabled={submitting}
                  style={{
                    fontSize: '2.6rem', background: 'none', border: 'none', cursor: 'pointer',
                    color: lit ? (activeLabel?.color ?? '#f59e0b') : 'var(--border-hi)',
                    transform: lit ? 'scale(1.2)' : 'scale(1)',
                    transition: 'all .15s ease',
                    filter: lit ? `drop-shadow(0 0 8px ${activeLabel?.color ?? '#f59e0b'})` : 'none',
                  }}
                >
                  ★
                </button>
              )
            })}
          </div>

          {/* Label */}
          <div style={{ height: 24, display: 'flex', justifyContent: 'center', alignItems: 'center' }}>
            {activeLabel && (
              <span style={{ fontSize: '.9rem', fontWeight: 600, color: activeLabel.color }}>
                {activeLabel.text}
              </span>
            )}
          </div>

          {/* Skip */}
          <button
            onClick={() => { api.post('/auth/session/outcome', { outcome: 'resolved' }).catch(() => {}); reset() }}
            style={{ marginTop: 28, background: 'none', border: 'none', color: 'var(--text-dim)', fontSize: '.82rem', cursor: 'pointer', transition: 'color .2s' }}
            onMouseOver={e => (e.currentTarget.style.color = 'var(--text-muted)')}
            onMouseOut={e => (e.currentTarget.style.color = 'var(--text-dim)')}
          >
            Skip →
          </button>
        </div>
      </div>
    </div>
  )
}

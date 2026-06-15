import { useState } from 'react'
import { api } from '../api/client'
import { useSession } from '../store/sessionStore'

const SEV_CONFIG: Record<string, { color: string; label: string }> = {
  low:      { color: '#22c55e', label: 'Low' },
  medium:   { color: '#f59e0b', label: 'Medium' },
  high:     { color: '#ef4444', label: 'High' },
  critical: { color: '#dc2626', label: 'Critical' },
}

const CONF_LABEL = (c: number) =>
  c >= 0.85 ? 'High confidence' : c >= 0.6 ? 'Moderate confidence' : 'Low confidence'

export default function ResultScreen() {
  const { diagnosis, setScreen, setTicketId } = useSession()
  const [checked, setChecked] = useState<boolean[]>(
    Array(diagnosis?.fix_steps.length ?? 0).fill(false)
  )
  const [submitting, setSubmitting] = useState(false)

  if (!diagnosis) { setScreen('HOME'); return null }

  const toggleStep = (i: number) =>
    setChecked(c => { const n = [...c]; n[i] = !n[i]; return n })

  const handleResolved = () => setScreen('CSAT')

  const handleNotFixed = async () => {
    setSubmitting(true)
    try {
      const res = await api.post('/ticket', { device_serial: '' })
      setTicketId(res.data.ticket_id)
    } catch {}
    setScreen('ESCALATE')
    setSubmitting(false)
  }

  const sev = SEV_CONFIG[diagnosis.severity || 'medium'] ?? SEV_CONFIG.medium
  const isAutoFix = diagnosis.action === 'self_resolve'
  const doneCount = checked.filter(Boolean).length
  const totalSteps = diagnosis.fix_steps.length

  return (
    <div className="ted-screen">
      {/* Nav */}
      <nav className="ted-nav">
        <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
          <div style={{ width: 30, height: 30, borderRadius: 7, background: 'linear-gradient(135deg, var(--blue), var(--cyan))', display: 'grid', placeItems: 'center' }}>
            <svg viewBox="0 0 24 24" fill="white" style={{ width: 15, height: 15 }}><path d="M20 4H4c-1.1 0-2 .9-2 2v10c0 1.1.9 2 2 2h7v2H9v2h6v-2h-2v-2h7c1.1 0 2-.9 2-2V6c0-1.1-.9-2-2-2zm0 12H4V6h16v10z"/></svg>
          </div>
          <span style={{ fontWeight: 800, fontSize: '1rem', color: 'var(--text)' }}>TED <span style={{ color: 'var(--cyan)' }}>Kiosk</span></span>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
          <span style={{ padding: '4px 12px', borderRadius: 999, fontSize: '.7rem', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '.08em', background: sev.color + '22', color: sev.color, border: `1px solid ${sev.color}44` }}>
            {sev.label}
          </span>
          <span style={{ fontSize: '.78rem', color: 'var(--text-dim)' }}>
            {CONF_LABEL(diagnosis.confidence)} · {Math.round(diagnosis.confidence * 100)}%
          </span>
        </div>
      </nav>

      <div style={{ flex: 1, display: 'flex', flexDirection: 'column', padding: '28px 40px', position: 'relative', zIndex: 1, overflow: 'hidden' }}>
        <div className="orb" style={{ width: 300, height: 300, top: -60, right: -60, background: `radial-gradient(circle, ${sev.color}18 0%, transparent 70%)` }} />

        {/* Auto-fix banner */}
        {isAutoFix && (
          <div style={{ display: 'flex', alignItems: 'center', gap: 12, padding: '12px 18px', background: 'rgba(34,211,238,.08)', border: '1px solid rgba(34,211,238,.25)', borderRadius: 'var(--radius)', marginBottom: 20 }}>
            <div style={{ width: 28, height: 28, borderRadius: '50%', background: 'rgba(34,211,238,.15)', display: 'grid', placeItems: 'center' }}>
              <svg viewBox="0 0 24 24" fill="var(--cyan)" style={{ width: 14, height: 14 }}><path d="M13 2L3 14h9l-1 8 10-12h-9l1-8z"/></svg>
            </div>
            <div>
              <span style={{ fontSize: '.82rem', fontWeight: 700, color: 'var(--cyan)' }}>Auto-fix detected</span>
              <span style={{ fontSize: '.82rem', color: 'var(--text-muted)', marginLeft: 6 }}>— review and confirm steps below</span>
            </div>
          </div>
        )}

        {/* Diagnosis summary */}
        <div style={{ marginBottom: 24 }}>
          <span className="section-tag">AI Diagnosis</span>
          <h1 style={{ fontSize: '1.7rem', fontWeight: 800, letterSpacing: '-.03em', color: 'var(--text)', lineHeight: 1.2, marginBottom: 10 }}>
            {isAutoFix ? '⚡ Issue Identified' : 'We found the issue'}
          </h1>
          <p style={{ color: 'var(--text-muted)', fontSize: '1rem', lineHeight: 1.6, maxWidth: 640 }}>
            {diagnosis.diagnosis}
          </p>
        </div>

        {/* Progress indicator */}
        <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 16 }}>
          <span style={{ fontSize: '.78rem', fontWeight: 600, color: 'var(--text-dim)', textTransform: 'uppercase', letterSpacing: '.1em' }}>
            Fix Steps
          </span>
          <div style={{ flex: 1, height: 4, background: 'var(--surface-hi)', borderRadius: 999, overflow: 'hidden' }}>
            <div style={{ height: '100%', width: `${totalSteps ? (doneCount / totalSteps) * 100 : 0}%`, background: 'linear-gradient(90deg, var(--blue), var(--cyan))', borderRadius: 999, transition: 'width .3s ease' }} />
          </div>
          <span style={{ fontSize: '.78rem', color: 'var(--text-dim)' }}>{doneCount}/{totalSteps}</span>
        </div>

        {/* Steps */}
        <div style={{ flex: 1, overflowY: 'auto', display: 'flex', flexDirection: 'column', gap: 10 }}>
          {diagnosis.fix_steps.map((step, i) => {
            const done = checked[i]
            return (
              <button
                key={i}
                onClick={() => toggleStep(i)}
                style={{
                  display: 'flex', alignItems: 'flex-start', gap: 14, padding: '14px 18px',
                  background: done ? 'rgba(34,211,238,.06)' : 'var(--surface)',
                  border: `1px solid ${done ? 'rgba(34,211,238,.25)' : 'var(--border)'}`,
                  borderRadius: 'var(--radius)', cursor: 'pointer', textAlign: 'left',
                  transition: 'all .2s',
                }}
              >
                <div style={{
                  width: 28, height: 28, borderRadius: '50%', flexShrink: 0,
                  display: 'grid', placeItems: 'center', fontSize: '.8rem', fontWeight: 700,
                  background: done ? 'var(--cyan)' : 'var(--surface-hi)',
                  border: `1px solid ${done ? 'var(--cyan)' : 'var(--border-hi)'}`,
                  color: done ? '#07111e' : 'var(--text-muted)',
                  transition: 'all .2s',
                }}>
                  {done ? '✓' : i + 1}
                </div>
                <span style={{ fontSize: '.92rem', color: done ? 'var(--cyan)' : 'var(--text-muted)', lineHeight: 1.6, transition: 'color .2s', paddingTop: 2 }}>
                  {typeof step === 'object' ? (step as any).instruction ?? JSON.stringify(step) : step}
                </span>
              </button>
            )
          })}
        </div>

        {/* Actions */}
        <div style={{ display: 'flex', gap: 12, marginTop: 20 }}>
          <button
            onClick={handleResolved}
            className="btn-primary"
            style={{ flex: 1, padding: '15px', fontSize: '1rem', borderRadius: 'var(--radius)' }}
          >
            <svg viewBox="0 0 24 24" fill="currentColor" style={{ width: 18, height: 18 }}><path d="M9 16.17L4.83 12l-1.42 1.41L9 19 21 7l-1.41-1.41z"/></svg>
            This fixed it
          </button>
          <button
            onClick={handleNotFixed}
            disabled={submitting}
            className="btn-ghost"
            style={{ flex: 1, padding: '15px', fontSize: '1rem', borderRadius: 'var(--radius)', opacity: submitting ? 0.5 : 1 }}
          >
            {submitting ? 'Raising ticket…' : 'Still not working →'}
          </button>
        </div>
      </div>
    </div>
  )
}

import { useState } from 'react'
import { api } from '../api/client'
import { useSession } from '../store/sessionStore'

const QUICK_ISSUES = [
  { label: 'Computer running very slowly',          icon: '🐢' },
  { label: 'Cannot connect to Wi-Fi or VPN',        icon: '📡' },
  { label: 'Password expired or account locked out', icon: '🔐' },
  { label: 'Application keeps crashing',             icon: '💥' },
  { label: 'Cannot access a website or shared drive',icon: '🌐' },
  { label: 'Screen flickering or display issues',    icon: '🖥️' },
]

export default function DiagnoseScreen() {
  const { employee, setScreen, setDiagnosis } = useSession()
  const [text, setText] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  const handleSubmit = async (errorText: string) => {
    if (!errorText.trim()) { setError('Please describe your issue'); return }
    setLoading(true); setError('')
    try {
      const res = await api.post('/diagnose', {
        error_text: errorText,
        device_info: { os: 'Windows 11' },
        issue_type: 'software',
        employee: { name: employee?.name || '', id: employee?.id || '', dept: employee?.dept || '' },
      })
      const diagnosis = res.data
      setDiagnosis(diagnosis)
      if (diagnosis.action === 'create_ticket') {
        setScreen('ESCALATE')
      } else if (diagnosis.action === 'self_resolve' && (diagnosis as any).auto_executable) {
        // High confidence + IoT commands available → auto-fix immediately
        setScreen('AUTOFIXING')
      } else {
        // guided_fix or no IoT script → show manual steps
        setScreen('RESULT')
      }
    } catch {
      setError('Diagnosis failed. Please try again.')
    } finally { setLoading(false) }
  }

  if (loading) {
    return (
      <div className="ted-screen items-center justify-center text-center">
        <div className="orb" style={{ width: 400, height: 400, top: '50%', left: '50%', transform: 'translate(-50%,-50%)', background: 'radial-gradient(circle, rgba(34,211,238,.12) 0%, transparent 90%)' }} />
        <div style={{ position: 'relative', zIndex: 1 }}>
          <div style={{ width: 72, height: 72, borderRadius: '50%', background: 'var(--cyan-dim)', border: '2px solid var(--cyan)', display: 'grid', placeItems: 'center', margin: '0 auto 28px', boxShadow: '0 0 40px var(--cyan-glow)', animation: 'pulse-dot 1.5s ease-in-out infinite' }}>
            <svg viewBox="0 0 24 24" fill="none" stroke="var(--cyan)" strokeWidth="2" style={{ width: 32, height: 32 }}>
              <circle cx="11" cy="11" r="8"/><path d="m21 21-4.35-4.35"/>
            </svg>
          </div>
          <span className="section-tag">AI Engine Active</span>
          <h2 style={{ fontSize: '2rem', fontWeight: 800, letterSpacing: '-.03em', color: 'var(--text)', marginBottom: 12 }}>Analysing your issue…</h2>
          <p style={{ color: 'var(--text-muted)' }}>Running diagnostics and matching knowledge base</p>
        </div>
      </div>
    )
  }

  return (
    <div className="ted-screen">
      {/* Nav */}
      <nav className="ted-nav">
        <button className="btn-ghost" onClick={() => setScreen('HOME')} style={{ padding: '7px 14px', fontSize: '.82rem' }}>← Back</button>
        <span style={{ color: 'var(--text-dim)', fontSize: '.82rem' }}>TED · AI Diagnosis</span>
        <span className="eyebrow" style={{ fontSize: '.65rem' }}><span className="pulse-dot" />Live</span>
      </nav>

      <div style={{ flex: 1, display: 'flex', flexDirection: 'column', padding: '32px 40px', position: 'relative', zIndex: 1, overflow: 'hidden' }}>
        <div className="orb" style={{ width: 350, height: 350, top: -80, right: -80, background: 'radial-gradient(circle, rgba(59,130,246,.1) 0%, transparent 90%)' }} />

        {/* Header */}
        <div style={{ marginBottom: 28 }}>
          <span className="section-tag">Describe Your Issue</span>
          <h1 style={{ fontSize: '2rem', fontWeight: 800, letterSpacing: '-.03em', color: 'var(--text)', lineHeight: 1.1 }}>
            What's going wrong?
          </h1>
          <p style={{ color: 'var(--text-muted)', marginTop: 8, fontSize: '.9rem' }}>
            Type your problem or pick a common issue — our AI handles the rest
          </p>
        </div>

        {/* Text area card */}
        <div className="ted-card" style={{ padding: 4, marginBottom: 16 }}>
          <textarea
            className="ted-input"
            style={{ padding: '18px 20px', fontSize: '1rem', lineHeight: 1.6, resize: 'none', minHeight: 120, border: 'none', borderRadius: 'var(--radius-lg)' }}
            placeholder="e.g. My laptop screen went blue and it restarted by itself. It says DRIVER_IRQL_NOT_LESS_OR_EQUAL…"
            value={text}
            onChange={(e) => setText(e.target.value)}
            autoFocus
          />
        </div>

        {error && (
          <div style={{ padding: '10px 14px', background: 'rgba(239,68,68,.1)', border: '1px solid rgba(239,68,68,.3)', borderRadius: 8, color: '#fca5a5', fontSize: '.85rem', marginBottom: 12 }}>
            {error}
          </div>
        )}

        <button
          className="btn-primary"
          onClick={() => handleSubmit(text)}
          style={{ padding: '14px 28px', fontSize: '1rem', borderRadius: 'var(--radius)', marginBottom: 28, alignSelf: 'stretch' }}
        >
          <svg viewBox="0 0 24 24" fill="currentColor" style={{ width: 18, height: 18 }}><path d="M13 2L3 14h9l-1 8 10-12h-9l1-8z"/></svg>
          Run AI Diagnosis
        </button>

        {/* Quick select */}
        <div style={{ marginBottom: 12 }}>
          <span style={{ fontSize: '.78rem', fontWeight: 600, color: 'var(--text-dim)', textTransform: 'uppercase', letterSpacing: '.1em' }}>
            Common issues
          </span>
        </div>
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 10, flex: 1, overflowY: 'auto' }}>
          {QUICK_ISSUES.map((q) => (
            <button
              key={q.label}
              onClick={() => handleSubmit(q.label)}
              className="ted-card"
              style={{ display: 'flex', alignItems: 'center', gap: 12, padding: '14px 16px', cursor: 'pointer', textAlign: 'left', transition: 'border-color .2s, background .2s' }}
              onMouseOver={e => { (e.currentTarget as HTMLElement).style.borderColor = 'var(--border-hi)'; (e.currentTarget as HTMLElement).style.background = 'var(--surface-hi)'; }}
              onMouseOut={e => { (e.currentTarget as HTMLElement).style.borderColor = 'var(--border)'; (e.currentTarget as HTMLElement).style.background = 'var(--surface)'; }}
            >
              <span style={{ fontSize: '1.2rem', flexShrink: 0 }}>{q.icon}</span>
              <span style={{ fontSize: '.88rem', color: 'var(--text-muted)', lineHeight: 1.4 }}>{q.label}</span>
            </button>
          ))}
        </div>
      </div>
    </div>
  )
}

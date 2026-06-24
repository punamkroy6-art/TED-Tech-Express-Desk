import { useEffect, useState, useRef } from 'react'
import { api } from '../api/client'
import { useSession } from '../store/sessionStore'
import { captureCurrentScreen, captureScreenText } from '../utils/screenshot'

interface Step {
  label: string
  status: 'pending' | 'running' | 'done' | 'failed'
  success: boolean
  output: string
  duration_ms: number
}

export default function AutoFixingScreen() {
  const { diagnosis, token, setScreen, setTicketId } = useSession()
  const [steps, setSteps] = useState<Step[]>([])
  const [fixName, setFixName] = useState('')
  const [done, setDone] = useState(false)
  const [success, setSuccess] = useState(false)
  const [summary, setSummary] = useState('')
  const [error, setError] = useState('')
  const pollerRef = useRef<ReturnType<typeof setInterval> | null>(null)

  const fixKey: string = (diagnosis as any)?.fix_key || ''

  useEffect(() => {
    if (!fixKey || !token) {
      setScreen('RESULT')
      return
    }
    startJob()
    return () => { if (pollerRef.current) clearInterval(pollerRef.current) }
  }, [])

  const startJob = async () => {
    try {
      // POST returns instantly — no subprocess blocking
      const res = await api.post('/autofix/start', {
        fix_key: fixKey, ssh_host: '', ssh_user: '', ssh_password: '',
      }, { headers: { Authorization: `Bearer ${token}` }, timeout: 5000 })

      const { job_id, fix_name } = res.data
      setFixName(fix_name || fixKey)

      // Poll every 1s — each poll is < 10ms (just reads job state)
      pollerRef.current = setInterval(() => pollStatus(job_id), 1000)

    } catch {
      setError('Auto-fix could not start. Showing manual steps instead.')
      setTimeout(() => setScreen('RESULT'), 2500)
    }
  }

  const pollStatus = async (job_id: string) => {
    try {
      const res = await api.get(`/autofix/status/${job_id}`, {
        headers: { Authorization: `Bearer ${token}` },
        timeout: 3000,  // must be fast
      })
      const job = res.data

      setSteps(job.steps || [])

      if (job.done) {
        clearInterval(pollerRef.current!)
        pollerRef.current = null
        const passed = (job.steps || []).filter((s: Step) => s.success).length
        setSuccess(passed > 0)
        setSummary(job.summary || '')
        setDone(true)

        // Auto-raise ticket if fix failed
        if (!passed) {
          try {
            const [screenshot_b64, screen_text] = await Promise.all([
              captureCurrentScreen(),
              Promise.resolve(captureScreenText()),
            ])
            const ticketRes = await api.post('/ticket', {
              device_serial: '',
              screenshot_b64,
              screen_text,
              ai_diagnosis: diagnosis,
              autofix_results: job.steps,
              error_description: `Auto-fix ran ${job.steps?.length} commands — all failed. Manual SD intervention needed.`,
              diagnostic_data: {},
              steps_attempted: [],
            }, { headers: { Authorization: `Bearer ${token}` } })
            setTicketId(ticketRes.data.ticket_id)
          } catch { /* ticket creation is best-effort */ }
        }
      }
    } catch {
      // Poll failed — stop and show error
      clearInterval(pollerRef.current!)
      pollerRef.current = null
      setError('Lost connection to fix engine.')
      setTimeout(() => setScreen('RESULT'), 2000)
    }
  }

  const handleDone = () => setScreen(success ? 'CSAT' : 'ESCALATE')
  const passedCount = steps.filter(s => s.success).length

  return (
    <div className="ted-screen">
      <nav className="ted-nav">
        <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
          <div style={{ width: 30, height: 30, borderRadius: 7, background: 'linear-gradient(135deg, var(--blue), var(--cyan))', display: 'grid', placeItems: 'center' }}>
            <svg viewBox="0 0 24 24" fill="white" style={{ width: 15, height: 15 }}><path d="M20 4H4c-1.1 0-2 .9-2 2v10c0 1.1.9 2 2 2h7v2H9v2h6v-2h-2v-2h7c1.1 0 2-.9 2-2V6c0-1.1-.9-2-2-2zm0 12H4V6h16v10z"/></svg>
          </div>
          <span style={{ fontWeight: 800, fontSize: '1rem', color: 'var(--text)' }}>TED <span style={{ color: 'var(--cyan)' }}>Kiosk</span></span>
        </div>
        <span className="eyebrow" style={{ fontSize: '.65rem' }}>
          <span className="pulse-dot" style={{ background: done ? (success ? 'var(--green)' : 'var(--red)') : 'var(--cyan)' }} />
          {done ? (success ? 'Fix Applied' : 'Partial Fix') : 'Auto-Fixing…'}
        </span>
      </nav>

      <div style={{ flex: 1, display: 'flex', flexDirection: 'column', padding: '32px 40px', position: 'relative', zIndex: 1, overflow: 'hidden' }}>
        <div className="orb" style={{ width: 350, height: 350, top: -80, right: -80, background: done ? `radial-gradient(circle, ${success ? 'rgba(34,197,94,.12)' : 'rgba(239,68,68,.1)'} 0%, transparent 90%)` : 'radial-gradient(circle, rgba(34,211,238,.1) 0%, transparent 90%)' }} />

        <div style={{ marginBottom: 28 }}>
          <span className="section-tag">IoT Auto-Fix Engine</span>
          <h1 style={{ fontSize: '2rem', fontWeight: 800, letterSpacing: '-.03em', color: 'var(--text)', lineHeight: 1.1 }}>
            {done ? (success ? '✓ Issue Fixed Automatically' : '⚠ Partial Fix Applied') : `Fixing: ${fixName || fixKey}…`}
          </h1>
          {diagnosis?.diagnosis && (
            <p style={{ color: 'var(--text-muted)', marginTop: 8, fontSize: '.9rem', maxWidth: 600 }}>{diagnosis.diagnosis}</p>
          )}
        </div>

        {/* Progress bar */}
        {steps.length > 0 && (
          <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 20 }}>
            <span style={{ fontSize: '.78rem', fontWeight: 600, color: 'var(--text-dim)', textTransform: 'uppercase', letterSpacing: '.1em' }}>Progress</span>
            <div style={{ flex: 1, height: 6, background: 'var(--surface-hi)', borderRadius: 999, overflow: 'hidden' }}>
              <div style={{ height: '100%', width: `${steps.length ? (passedCount / steps.length) * 100 : 0}%`, background: 'linear-gradient(90deg, var(--blue), var(--cyan))', borderRadius: 999, transition: 'width .5s ease' }} />
            </div>
            <span style={{ fontSize: '.78rem', color: 'var(--text-dim)', minWidth: 40, textAlign: 'right' }}>{passedCount}/{steps.length}</span>
          </div>
        )}

        {/* Step list */}
        <div style={{ flex: 1, overflowY: 'auto', display: 'flex', flexDirection: 'column', gap: 10 }}>
          {error ? (
            <div style={{ padding: '16px 20px', background: 'rgba(239,68,68,.1)', border: '1px solid rgba(239,68,68,.3)', borderRadius: 'var(--radius)', color: '#fca5a5' }}>{error}</div>
          ) : steps.length === 0 ? (
            [...Array(3)].map((_, i) => (
              <div key={i} style={{ padding: '16px 20px', background: 'var(--surface)', border: '1px solid var(--border)', borderRadius: 'var(--radius)', display: 'flex', alignItems: 'center', gap: 14 }}>
                <div style={{ width: 28, height: 28, borderRadius: '50%', background: 'var(--surface-hi)', animation: 'pulse-dot 1.5s ease infinite' }} />
                <div style={{ flex: 1, height: 12, background: 'var(--surface-hi)', borderRadius: 4, animation: 'pulse-dot 1.5s ease infinite' }} />
              </div>
            ))
          ) : steps.map((step, i) => {
            const isRunning = step.status === 'running'
            const isDone    = step.status === 'done'
            const isFailed  = step.status === 'failed'
            return (
              <div key={i} style={{
                display: 'flex', alignItems: 'flex-start', gap: 14, padding: '14px 18px',
                background: isDone ? 'rgba(34,211,238,.06)' : isFailed ? 'rgba(239,68,68,.06)' : isRunning ? 'rgba(34,211,238,.04)' : 'var(--surface)',
                border: `1px solid ${isDone ? 'rgba(34,211,238,.25)' : isFailed ? 'rgba(239,68,68,.25)' : isRunning ? 'rgba(34,211,238,.2)' : 'var(--border)'}`,
                borderRadius: 'var(--radius)', transition: 'all .3s ease', opacity: step.status === 'pending' ? 0.4 : 1,
              }}>
                <div style={{ width: 28, height: 28, borderRadius: '50%', flexShrink: 0, display: 'grid', placeItems: 'center', fontSize: '.8rem', fontWeight: 700,
                  background: isDone ? 'var(--cyan)' : isFailed ? 'var(--red)' : isRunning ? 'rgba(34,211,238,.2)' : 'var(--surface-hi)',
                  color: isDone ? '#07111e' : isFailed ? '#fff' : isRunning ? 'var(--cyan)' : 'var(--text-dim)',
                  animation: isRunning ? 'pulse-dot 1s ease infinite' : 'none',
                }}>
                  {isDone ? '✓' : isFailed ? '✗' : isRunning ? '⟳' : i + 1}
                </div>
                <div style={{ flex: 1 }}>
                  <div style={{ fontSize: '.9rem', fontWeight: 600, color: isDone ? 'var(--cyan)' : isFailed ? 'var(--red)' : isRunning ? 'var(--cyan)' : 'var(--text-muted)', marginBottom: 4 }}>
                    {step.label}
                    {(isDone || isFailed) && step.duration_ms > 0 && (
                      <span style={{ fontSize: '.72rem', color: 'var(--text-dim)', marginLeft: 8, fontWeight: 400 }}>
                        {step.duration_ms > 1000 ? `${(step.duration_ms / 1000).toFixed(1)}s` : `${step.duration_ms}ms`}
                      </span>
                    )}
                  </div>
                  {(isDone || isFailed) && step.output && (
                    <div style={{ fontSize: '.78rem', color: 'var(--text-dim)', fontFamily: 'monospace', background: 'rgba(0,0,0,.2)', padding: '4px 10px', borderRadius: 4 }}>
                      {step.output.substring(0, 120)}{step.output.length > 120 ? '…' : ''}
                    </div>
                  )}
                  {isRunning && <div style={{ fontSize: '.78rem', color: 'var(--cyan)', marginTop: 2 }}>Executing…</div>}
                </div>
              </div>
            )
          })}
        </div>

        {/* Done actions */}
        {done && (
          <div style={{ marginTop: 20, display: 'flex', flexDirection: 'column', gap: 12 }}>
            {summary && (
              <div style={{ padding: '12px 18px', borderRadius: 'var(--radius)', background: success ? 'rgba(34,197,94,.08)' : 'rgba(245,158,11,.08)', border: `1px solid ${success ? 'rgba(34,197,94,.25)' : 'rgba(245,158,11,.25)'}`, color: success ? 'var(--green)' : 'var(--amber)', fontSize: '.88rem' }}>
                {summary}
              </div>
            )}
            <div style={{ display: 'flex', gap: 12 }}>
              <button onClick={handleDone} className="btn-primary" style={{ flex: 1, padding: '14px', fontSize: '1rem', borderRadius: 'var(--radius)' }}>
                {success ? '✓ Issue Resolved' : '→ Raise Ticket for Remaining Steps'}
              </button>
              {success && (
                <button onClick={() => setScreen('RESULT')} className="btn-ghost" style={{ padding: '14px 20px', fontSize: '.9rem', borderRadius: 'var(--radius)' }}>
                  View Details
                </button>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  )
}

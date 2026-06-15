import { useEffect, useState } from 'react'
import { api } from '../api/client'
import { useSession } from '../store/sessionStore'

interface HardwareMetric { label: string; value: string; status: 'ok' | 'warning' | 'critical' }
interface DiagResult {
  overall_health: string
  issues_found: string[]
  suggested_queries: string[]
  hardware: any
  software: any
}

const STATUS_COLOR = { ok: 'var(--green)', warning: 'var(--amber)', critical: 'var(--red)' }
const STATUS_ICON  = { ok: '✓', warning: '⚠', critical: '✗' }

const SCAN_STEPS = [
  'Checking OS and system version…',
  'Scanning driver health…',
  'Analysing CPU and memory…',
  'Inspecting disk storage…',
  'Testing network connectivity…',
  'Running battery check…',
  'Compiling diagnostic report…',
]

export default function DiagnosticScreen() {
  const { employee, token, setScreen, setDiagnosis } = useSession()
  const [phase, setPhase] = useState<'scanning' | 'results' | 'error'>('scanning')
  const [stepIndex, setStepIndex] = useState(0)
  const [result, setResult] = useState<DiagResult | null>(null)
  const [errorMsg, setErrorMsg] = useState('')

  useEffect(() => {
    // Cycle through scan steps while fetching
    const interval = setInterval(() => {
      setStepIndex(i => Math.min(i + 1, SCAN_STEPS.length - 1))
    }, 700)

    // Run real diagnostic — pass token explicitly in case axios default isn't set
    api.post('/diagnostic/run', {}, { headers: { Authorization: `Bearer ${token}` } }).then(res => {
      clearInterval(interval)
      setResult(res.data)
      setPhase('results')
    }).catch(() => {
      clearInterval(interval)
      setErrorMsg('Diagnostic service unavailable. Please describe your issue manually.')
      setPhase('error')
    })

    return () => clearInterval(interval)
  }, [])

  // Auto-fix based on diagnostic result
  const handleAutoFix = async (query: string) => {
    try {
      const res = await api.post('/diagnose', {
        error_text: query,
        device_info: {
          os: result?.software?.os?.os || 'Windows',
          cpu_percent: result?.hardware?.cpu?.percent,
          ram_percent: result?.hardware?.memory?.percent,
          disk_free_gb: result?.hardware?.disk?.primary?.free_gb,
        },
        employee: { name: employee?.name || '', id: employee?.id || '' }
      }, { headers: { Authorization: `Bearer ${token}` } })
      setDiagnosis(res.data)
      if (res.data.action === 'create_ticket') setScreen('ESCALATE')
      else if (res.data.action === 'self_resolve' && res.data.auto_executable) setScreen('AUTOFIXING')
      else setScreen('RESULT')
    } catch {
      setScreen('DIAGNOSE')
    }
  }

  const handleDescribeManually = () => setScreen('DIAGNOSE')

  // Build metric cards from results
  const metrics: HardwareMetric[] = result ? [
    { label: 'CPU', value: `${result.hardware?.cpu?.percent}%`, status: result.hardware?.cpu?.status || 'ok' },
    { label: 'RAM', value: `${result.hardware?.memory?.percent}%`, status: result.hardware?.memory?.status || 'ok' },
    { label: 'Disk Free', value: `${result.hardware?.disk?.primary?.free_gb} GB`, status: result.hardware?.disk?.primary?.status || 'ok' },
    { label: 'Battery', value: result.hardware?.battery?.present ? `${result.hardware.battery.percent}%` : 'Desktop', status: result.hardware?.battery?.status || 'ok' },
    { label: 'Internet', value: result.software?.network?.internet === 'ok' ? 'Connected' : 'Offline', status: result.software?.network?.internet === 'ok' ? 'ok' : 'critical' },
    { label: 'Drivers', value: result.software?.drivers?.failed_drivers?.length > 0 ? `${result.software.drivers.failed_drivers.length} failed` : 'All OK', status: result.software?.drivers?.failed_drivers?.length > 0 ? 'warning' : 'ok' },
  ] : []

  const healthColor = result?.overall_health === 'healthy' ? 'var(--green)' : result?.overall_health === 'critical' ? 'var(--red)' : 'var(--amber)'

  // ── Scanning phase ──────────────────────────────────────────────────────
  if (phase === 'scanning') {
    return (
      <div className="ted-screen items-center justify-center text-center">
        <div className="orb" style={{ width: 400, height: 400, top: '50%', left: '50%', transform: 'translate(-50%,-50%)', background: 'radial-gradient(circle, rgba(34,211,238,.1) 0%, transparent 70%)' }} />
        <div style={{ position: 'relative', zIndex: 1 }}>
          {/* Animated scanner ring */}
          <div style={{ width: 110, height: 110, borderRadius: '50%', margin: '0 auto 28px', position: 'relative' }}>
            <div style={{ position: 'absolute', inset: 0, borderRadius: '50%', border: '2px solid var(--border-hi)' }} />
            <div style={{ position: 'absolute', inset: 0, borderRadius: '50%', border: '2px solid var(--cyan)', borderTopColor: 'transparent', animation: 'spin 1s linear infinite' }} />
            <div style={{ position: 'absolute', inset: '20%', borderRadius: '50%', border: '2px solid rgba(34,211,238,.3)', borderBottomColor: 'transparent', animation: 'spin 1.4s linear infinite reverse' }} />
            <div style={{ position: 'absolute', inset: 0, display: 'grid', placeItems: 'center' }}>
              <svg viewBox="0 0 24 24" fill="none" stroke="var(--cyan)" strokeWidth="1.5" style={{ width: 32, height: 32 }}>
                <circle cx="11" cy="11" r="8"/><path d="m21 21-4.35-4.35"/>
              </svg>
            </div>
          </div>

          <span className="section-tag">Auto-Diagnostic Running</span>
          <h2 style={{ fontSize: '1.8rem', fontWeight: 800, letterSpacing: '-.03em', color: 'var(--text)', marginBottom: 12 }}>
            Scanning Your System
          </h2>
          <p style={{ color: 'var(--text-muted)', marginBottom: 32, fontSize: '.95rem' }}>
            TED is checking your hardware and software automatically
          </p>

          {/* Scrolling step indicator */}
          <div style={{ width: 380, height: 28, overflow: 'hidden', position: 'relative', margin: '0 auto' }}>
            {SCAN_STEPS.map((step, i) => (
              <div key={i} style={{
                position: 'absolute', width: '100%', textAlign: 'center',
                fontSize: '.82rem', color: 'var(--cyan)',
                opacity: i === stepIndex ? 1 : 0,
                transform: `translateY(${(i - stepIndex) * 30}px)`,
                transition: 'all .4s ease',
              }}>
                {step}
              </div>
            ))}
          </div>

          {/* Mini progress bar */}
          <div style={{ width: 200, height: 3, background: 'var(--surface-hi)', borderRadius: 999, margin: '20px auto 0', overflow: 'hidden' }}>
            <div style={{
              height: '100%', borderRadius: 999,
              background: 'linear-gradient(90deg, var(--blue), var(--cyan))',
              width: `${((stepIndex + 1) / SCAN_STEPS.length) * 100}%`,
              transition: 'width .5s ease',
            }} />
          </div>
        </div>
      </div>
    )
  }

  // ── Error phase ─────────────────────────────────────────────────────────
  if (phase === 'error') {
    return (
      <div className="ted-screen items-center justify-center text-center">
        <div style={{ position: 'relative', zIndex: 1, maxWidth: 460, padding: '0 24px' }}>
          <div className="ted-card" style={{ padding: 40 }}>
            <div style={{ fontSize: '3rem', marginBottom: 20 }}>⚠️</div>
            <span className="section-tag">Diagnostic Unavailable</span>
            <h2 style={{ fontSize: '1.5rem', fontWeight: 700, color: 'var(--text)', marginBottom: 12 }}>{errorMsg}</h2>
            <button className="btn-primary" onClick={handleDescribeManually} style={{ width: '100%', padding: 14, marginTop: 24, borderRadius: 'var(--radius)' }}>
              Describe Issue Manually →
            </button>
          </div>
        </div>
      </div>
    )
  }

  // ── Results phase ───────────────────────────────────────────────────────
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
        <span style={{ padding: '4px 14px', borderRadius: 999, fontSize: '.72rem', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '.08em', background: healthColor + '22', color: healthColor, border: `1px solid ${healthColor}44` }}>
          {result?.overall_health?.toUpperCase()}
        </span>
        <button className="btn-ghost" onClick={() => setScreen('HOME')} style={{ padding: '7px 14px', fontSize: '.82rem' }}>← Back</button>
      </nav>

      <div style={{ flex: 1, display: 'flex', flexDirection: 'column', padding: '28px 40px', position: 'relative', zIndex: 1, overflow: 'hidden' }}>
        <div className="orb" style={{ width: 300, height: 300, top: -60, right: -60, background: `radial-gradient(circle, ${healthColor}18 0%, transparent 70%)` }} />

        {/* Header */}
        <div style={{ marginBottom: 24 }}>
          <span className="section-tag">Live System Diagnostic</span>
          <h1 style={{ fontSize: '1.8rem', fontWeight: 800, letterSpacing: '-.03em', color: 'var(--text)', lineHeight: 1.1 }}>
            {result?.issues_found.length === 0 ? '✓ Your system looks healthy' : `${result?.issues_found.length} issue${result!.issues_found.length > 1 ? 's' : ''} detected`}
          </h1>
          <p style={{ color: 'var(--text-muted)', marginTop: 6, fontSize: '.9rem' }}>
            Scanned by TED AI · {new Date().toLocaleTimeString()}
          </p>
        </div>

        {/* Metrics grid */}
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 12, marginBottom: 20 }}>
          {metrics.map(m => (
            <div key={m.label} className="ted-card" style={{ padding: '16px 18px', borderColor: STATUS_COLOR[m.status] + '44' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 4 }}>
                <span style={{ fontSize: '.75rem', fontWeight: 600, color: 'var(--text-dim)', textTransform: 'uppercase', letterSpacing: '.08em' }}>{m.label}</span>
                <span style={{ fontSize: '.8rem', color: STATUS_COLOR[m.status] }}>{STATUS_ICON[m.status]}</span>
              </div>
              <div style={{ fontSize: '1.4rem', fontWeight: 800, color: m.status === 'ok' ? 'var(--text)' : STATUS_COLOR[m.status], letterSpacing: '-.02em' }}>
                {m.value}
              </div>
            </div>
          ))}
        </div>

        {/* Issues found */}
        {result!.issues_found.length > 0 && (
          <div style={{ marginBottom: 20 }}>
            <span style={{ fontSize: '.78rem', fontWeight: 600, color: 'var(--text-dim)', textTransform: 'uppercase', letterSpacing: '.1em' }}>Issues Detected</span>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 8, marginTop: 10 }}>
              {result!.issues_found.map((issue, i) => (
                <div key={i} style={{ display: 'flex', alignItems: 'center', gap: 10, padding: '10px 16px', background: 'rgba(245,158,11,.08)', border: '1px solid rgba(245,158,11,.25)', borderRadius: 'var(--radius-sm)' }}>
                  <span style={{ color: 'var(--amber)', fontSize: '1rem' }}>⚠</span>
                  <span style={{ fontSize: '.88rem', color: 'var(--text-muted)' }}>{issue}</span>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Action buttons */}
        <div style={{ marginTop: 'auto', display: 'flex', flexDirection: 'column', gap: 12 }}>
          {result!.suggested_queries.length > 0 ? (
            <>
              <p style={{ fontSize: '.82rem', color: 'var(--text-dim)', textAlign: 'center' }}>
                TED detected these issues — tap to auto-fix:
              </p>
              {result!.suggested_queries.slice(0, 2).map((q, i) => (
                <button key={i} className="btn-primary" onClick={() => handleAutoFix(q)} style={{ padding: '14px 20px', borderRadius: 'var(--radius)', fontSize: '.95rem', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <span>⚡ Auto-fix: {q.length > 55 ? q.substring(0, 55) + '…' : q}</span>
                  <span style={{ fontSize: '.8rem', opacity: 0.7 }}>→</span>
                </button>
              ))}
              <button className="btn-ghost" onClick={handleDescribeManually} style={{ padding: '12px', borderRadius: 'var(--radius)', fontSize: '.88rem' }}>
                Describe a different issue instead
              </button>
            </>
          ) : (
            <>
              <div style={{ padding: '14px 18px', background: 'rgba(34,197,94,.08)', border: '1px solid rgba(34,197,94,.25)', borderRadius: 'var(--radius)', textAlign: 'center', color: 'var(--green)', fontSize: '.9rem' }}>
                ✓ No hardware issues found — your device looks healthy
              </div>
              <button className="btn-primary" onClick={handleDescribeManually} style={{ padding: '14px', borderRadius: 'var(--radius)', fontSize: '1rem' }}>
                Describe Your Issue →
              </button>
            </>
          )}
        </div>
      </div>
    </div>
  )
}

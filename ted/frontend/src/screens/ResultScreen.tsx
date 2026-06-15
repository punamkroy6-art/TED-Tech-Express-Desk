import { useState } from 'react'
import { api } from '../api/client'
import { useSession } from '../store/sessionStore'

const SEVERITY_COLORS: Record<string, string> = {
  low: '#22c55e',
  medium: '#f59e0b',
  high: '#ef4444',
  critical: '#dc2626',
}

const CONFIDENCE_LABEL = (c: number) =>
  c >= 0.85 ? 'High confidence' : c >= 0.6 ? 'Moderate confidence' : 'Low confidence'

export default function ResultScreen() {
  const { diagnosis, setScreen, setTicketId } = useSession()
  const [checked, setChecked] = useState<boolean[]>(
    Array(diagnosis?.fix_steps.length ?? 0).fill(false)
  )
  const [submitting, setSubmitting] = useState(false)

  if (!diagnosis) { setScreen('HOME'); return null }

  const toggleStep = (i: number) =>
    setChecked((c) => { const n = [...c]; n[i] = !n[i]; return n })

  const handleResolved = () => {
    setScreen('CSAT')
  }

  const handleNotFixed = async () => {
    setSubmitting(true)
    try {
      const res = await api.post('/ticket', { device_serial: '' })
      setTicketId(res.data.ticket_id)
      setScreen('ESCALATE')
    } catch {
      setScreen('ESCALATE')
    } finally {
      setSubmitting(false)
    }
  }

  const sev = diagnosis.severity || 'medium'

  return (
    <div
      className="flex flex-col h-screen px-8 py-6"
      style={{ background: 'linear-gradient(135deg, #0d1b2a 0%, #1a3a5c 100%)' }}
    >
      {/* Header */}
      <div className="mb-6">
        {/* Auto-fix banner */}
        {diagnosis.action === 'self_resolve' && (
          <div
            className="flex items-center gap-3 px-4 py-3 rounded-xl mb-4 text-sm font-semibold"
            style={{ background: '#0f3a2888', border: '1px solid #22c55e55', color: '#86efac' }}
          >
            <span className="text-lg">⚡</span>
            Auto-fix detected — review steps below to confirm resolution
          </div>
        )}
        <div className="flex items-center gap-3 mb-2">
          <span
            className="px-3 py-1 rounded-full text-xs font-bold uppercase"
            style={{ background: SEVERITY_COLORS[sev] + '22', color: SEVERITY_COLORS[sev] }}
          >
            {sev}
          </span>
          <span className="text-xs" style={{ color: '#5a8ab0' }}>
            {CONFIDENCE_LABEL(diagnosis.confidence)} · {Math.round(diagnosis.confidence * 100)}%
          </span>
        </div>
        <h1 className="text-3xl font-bold mb-2" style={{ color: '#e8f0fe' }}>
          {diagnosis.action === 'self_resolve' ? '⚡ Issue Identified' : 'We found the issue'}
        </h1>
        <p className="text-lg" style={{ color: '#90b8e0' }}>
          {diagnosis.diagnosis}
        </p>
      </div>

      {/* Steps */}
      <p className="text-sm mb-3" style={{ color: '#5a8ab0' }}>
        Follow these steps to resolve your issue:
      </p>
      <div className="flex flex-col gap-3 flex-1 overflow-y-auto">
        {diagnosis.fix_steps.map((step, i) => (
          <button
            key={i}
            onClick={() => toggleStep(i)}
            className="flex items-start gap-4 p-5 rounded-xl text-left transition-all"
            style={{
              background: checked[i] ? '#0f3a28' : '#1a2d42',
              border: `1px solid ${checked[i] ? '#22c55e55' : '#243d57'}`,
            }}
          >
            <div
              className="w-8 h-8 rounded-full flex-shrink-0 flex items-center justify-center text-sm font-bold mt-0.5"
              style={{
                background: checked[i] ? '#22c55e' : '#2E75B6',
                color: '#fff',
              }}
            >
              {checked[i] ? '✓' : i + 1}
            </div>
            <p className="text-base" style={{ color: checked[i] ? '#86efac' : '#c8dff0' }}>
              {step}
            </p>
          </button>
        ))}
      </div>

      {/* Actions */}
      <div className="flex gap-4 mt-6">
        <button
          onClick={handleResolved}
          className="flex-1 py-5 rounded-xl text-xl font-bold"
          style={{ background: '#1a6b3a', color: '#fff' }}
        >
          ✓ This fixed it
        </button>
        <button
          onClick={handleNotFixed}
          disabled={submitting}
          className="flex-1 py-5 rounded-xl text-xl font-bold transition-opacity"
          style={{
            background: 'transparent',
            border: '2px solid #2E75B6',
            color: '#2E75B6',
            opacity: submitting ? 0.6 : 1,
          }}
        >
          {submitting ? 'Raising ticket…' : 'Still not working'}
        </button>
      </div>
    </div>
  )
}

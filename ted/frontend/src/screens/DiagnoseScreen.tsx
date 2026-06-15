import { useState } from 'react'
import { api } from '../api/client'
import { useSession } from '../store/sessionStore'

const QUICK_ISSUES = [
  'My computer is running very slowly',
  'I cannot connect to Wi-Fi',
  'My password has expired or I am locked out',
  'An application keeps crashing',
  'I cannot access a website or shared drive',
  'My screen is flickering or has display issues',
]

export default function DiagnoseScreen() {
  const { setScreen, setDiagnosis } = useSession()
  const [text, setText] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  const handleSubmit = async (errorText: string) => {
    if (!errorText.trim()) { setError('Please describe your issue'); return }
    setLoading(true)
    setError('')
    try {
      const res = await api.post('/diagnose', {
        error_text: errorText,
        device_info: { os: 'Windows 11' },
        issue_type: 'software',
      })
      const diagnosis = res.data
      setDiagnosis(diagnosis)

      if (diagnosis.action === 'create_ticket') {
        // Nothing actionable — auto-escalate
        setScreen('ESCALATE')
      } else {
        // self_resolve or guided_fix — show steps
        setScreen('RESULT')
      }
    } catch {
      setError('Diagnosis failed. Please try again.')
    } finally {
      setLoading(false)
    }
  }

  if (loading) return <ScanningOverlay />

  return (
    <div
      className="flex flex-col h-screen px-8 py-6"
      style={{ background: 'linear-gradient(135deg, #0d1b2a 0%, #1a3a5c 100%)' }}
    >
      <button onClick={() => setScreen('HOME')} className="text-sm mb-6" style={{ color: '#5a8ab0' }}>
        ← Back
      </button>

      <h1 className="text-3xl font-bold mb-2" style={{ color: '#e8f0fe' }}>
        Describe your issue
      </h1>
      <p className="mb-6 text-sm" style={{ color: '#5a8ab0' }}>
        Type your problem or choose a common issue below
      </p>

      <textarea
        className="w-full rounded-xl p-5 text-lg resize-none outline-none mb-4"
        rows={4}
        style={{
          background: '#1a2d42',
          border: '2px solid #2E75B6',
          color: '#e8f0fe',
        }}
        placeholder="e.g. My laptop screen is black and won't turn on..."
        value={text}
        onChange={(e) => setText(e.target.value)}
        autoFocus
      />

      {error && <p className="text-red-400 text-sm mb-3">{error}</p>}

      <button
        onClick={() => handleSubmit(text)}
        className="w-full py-4 rounded-xl text-xl font-bold mb-6 transition-opacity"
        style={{ background: '#2E75B6', color: '#fff' }}
      >
        Diagnose →
      </button>

      <p className="text-sm mb-4" style={{ color: '#5a8ab0' }}>
        Or choose a common issue:
      </p>
      <div className="flex flex-col gap-3 overflow-auto">
        {QUICK_ISSUES.map((q) => (
          <button
            key={q}
            onClick={() => handleSubmit(q)}
            className="w-full text-left px-5 py-4 rounded-xl text-base transition-all hover:scale-[1.01]"
            style={{ background: '#1a2d42', border: '1px solid #243d57', color: '#90b8e0' }}
          >
            {q}
          </button>
        ))}
      </div>
    </div>
  )
}

function ScanningOverlay() {
  return (
    <div
      className="flex flex-col items-center justify-center h-screen"
      style={{ background: 'linear-gradient(135deg, #0d1b2a 0%, #1a3a5c 100%)' }}
    >
      <div className="text-6xl animate-pulse mb-6">🔍</div>
      <h2 className="text-3xl font-bold mb-3" style={{ color: '#e8f0fe' }}>
        Analysing your issue…
      </h2>
      <p style={{ color: '#5a8ab0' }}>
        TED AI is running diagnostics. This takes just a moment.
      </p>
    </div>
  )
}

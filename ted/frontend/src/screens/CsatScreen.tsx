import { useState } from 'react'
import { api } from '../api/client'
import { useSession } from '../store/sessionStore'

const LABELS: Record<number, string> = {
  1: 'Very poor',
  2: 'Poor',
  3: 'OK',
  4: 'Good',
  5: 'Excellent',
}

export default function CsatScreen() {
  const { reset } = useSession()
  const [score, setScore] = useState<number | null>(null)
  const [submitting, setSubmitting] = useState(false)
  const [done, setDone] = useState(false)

  const handleSubmit = async (s: number) => {
    setScore(s)
    setSubmitting(true)
    try {
      await api.post('/auth/session/outcome', { outcome: 'resolved', csat_score: s })
    } catch { /* ignore */ }
    setSubmitting(false)
    setDone(true)
    setTimeout(() => reset(), 2500)
  }

  if (done) {
    return (
      <div
        className="flex flex-col items-center justify-center h-screen text-center px-8"
        style={{ background: 'linear-gradient(135deg, #0d1b2a 0%, #1a3a5c 100%)' }}
      >
        <div className="text-6xl mb-6">🙌</div>
        <h1 className="text-3xl font-bold mb-3" style={{ color: '#e8f0fe' }}>
          Thanks for your feedback!
        </h1>
        <p style={{ color: '#5a8ab0' }}>Ending session…</p>
      </div>
    )
  }

  return (
    <div
      className="flex flex-col items-center justify-center h-screen px-8 text-center"
      style={{ background: 'linear-gradient(135deg, #0d1b2a 0%, #1a3a5c 100%)' }}
    >
      <div className="text-5xl mb-6">⭐</div>
      <h1 className="text-3xl font-bold mb-2" style={{ color: '#e8f0fe' }}>
        How was your experience?
      </h1>
      <p className="mb-10 text-lg" style={{ color: '#5a8ab0' }}>
        Rate your TED session — it takes 5 seconds
      </p>

      {/* Star rating */}
      <div className="flex gap-5 mb-4">
        {[1, 2, 3, 4, 5].map((s) => (
          <button
            key={s}
            onClick={() => handleSubmit(s)}
            disabled={submitting}
            className="text-5xl transition-transform hover:scale-125 active:scale-95"
            style={{ color: score !== null && s <= score ? '#f59e0b' : '#2a3f58' }}
          >
            ★
          </button>
        ))}
      </div>

      {score && (
        <p className="text-lg font-semibold" style={{ color: '#90b8e0' }}>
          {LABELS[score]}
        </p>
      )}

      <button
        onClick={() => { api.post('/auth/session/outcome', { outcome: 'resolved' }).catch(() => {}); reset() }}
        className="mt-10 text-sm"
        style={{ color: '#3d6a8a' }}
      >
        Skip
      </button>
    </div>
  )
}

import { useState } from 'react'
import { api } from '../api/client'
import { useSession } from '../store/sessionStore'

const DEVICE_TYPES = [
  { key: 'laptop', label: 'Laptop', icon: '💻' },
  { key: 'charger', label: 'Charger', icon: '🔌' },
  { key: 'mouse', label: 'Mouse / Keyboard', icon: '🖱️' },
  { key: 'monitor', label: 'Monitor', icon: '🖥️' },
]

export default function LoanerScreen() {
  const { setScreen, setLoanerId, reset } = useSession()
  const [selected, setSelected] = useState('laptop')
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState<any>(null)

  const handleRequest = async () => {
    setLoading(true)
    try {
      const res = await api.post('/loaner/request', { device_type: selected })
      setResult(res.data)
      setLoanerId(res.data.loaner_id)
    } catch {
      setResult({ message: 'Request failed. Please speak to a Service Desk agent.' })
    } finally {
      setLoading(false)
    }
  }

  if (result) {
    return (
      <div
        className="flex flex-col items-center justify-center h-screen px-8 text-center"
        style={{ background: 'linear-gradient(135deg, #0d1b2a 0%, #1a3a5c 100%)' }}
      >
        <div className="text-6xl mb-6">📦</div>
        <h1 className="text-3xl font-bold mb-3" style={{ color: '#e8f0fe' }}>
          Loaner ready
        </h1>
        <p className="text-xl mb-2" style={{ color: '#90b8e0' }}>
          {result.message}
        </p>
        {result.loaner_id && (
          <div
            className="mt-4 px-6 py-3 rounded-xl font-mono text-xl"
            style={{ background: '#1a2d42', color: '#2E75B6', border: '1px solid #243d57' }}
          >
            {result.loaner_id}
          </div>
        )}
        <button
          onClick={reset}
          className="mt-10 px-10 py-4 rounded-xl text-lg font-bold"
          style={{ background: '#2E75B6', color: '#fff' }}
        >
          Done — End Session
        </button>
      </div>
    )
  }

  return (
    <div
      className="flex flex-col h-screen px-8 py-6"
      style={{ background: 'linear-gradient(135deg, #0d1b2a 0%, #1a3a5c 100%)' }}
    >
      <button onClick={() => setScreen('HOME')} className="text-sm mb-6" style={{ color: '#5a8ab0' }}>
        ← Back
      </button>

      <h1 className="text-3xl font-bold mb-2" style={{ color: '#e8f0fe' }}>
        Request a loaner device
      </h1>
      <p className="mb-8 text-sm" style={{ color: '#5a8ab0' }}>
        Select the type of device you need
      </p>

      <div className="grid grid-cols-2 gap-4 mb-10">
        {DEVICE_TYPES.map((d) => (
          <button
            key={d.key}
            onClick={() => setSelected(d.key)}
            className="flex flex-col items-center py-8 rounded-2xl transition-all"
            style={{
              background: selected === d.key ? '#2E75B6' : '#1a2d42',
              border: `2px solid ${selected === d.key ? '#2E75B6' : '#243d57'}`,
              color: selected === d.key ? '#fff' : '#90b8e0',
            }}
          >
            <span className="text-4xl mb-3">{d.icon}</span>
            <span className="text-lg font-semibold">{d.label}</span>
          </button>
        ))}
      </div>

      <button
        onClick={handleRequest}
        disabled={loading}
        className="w-full py-5 rounded-xl text-xl font-bold transition-opacity"
        style={{ background: '#2E75B6', color: '#fff', opacity: loading ? 0.6 : 1 }}
      >
        {loading ? 'Requesting…' : 'Request Device →'}
      </button>
    </div>
  )
}

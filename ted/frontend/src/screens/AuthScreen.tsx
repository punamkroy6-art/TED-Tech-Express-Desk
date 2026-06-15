import { useState } from 'react'
import { api, setAuthHeader } from '../api/client'
import { useSession } from '../store/sessionStore'

export default function AuthScreen() {
  const { setAuth, setScreen } = useSession()
  const [employeeId, setEmployeeId] = useState('')
  const [displayName, setDisplayName] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  const handleLogin = async () => {
    if (!employeeId.trim()) { setError('Please enter your Employee ID'); return }
    setLoading(true)
    setError('')
    try {
      const res = await api.post('/auth/session', {
        employee_id: employeeId.trim(),
        display_name: displayName.trim() || employeeId.trim(),
        kiosk_id: 'KIOSK-001',
        auth_method: 'sso',
      })
      const { token, session_id, employee } = res.data
      setAuthHeader(token)
      setAuth(token, session_id, employee)
    } catch {
      setError('Login failed. Please try again or contact IT.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div
      className="flex flex-col items-center justify-center h-screen px-8"
      style={{ background: 'linear-gradient(135deg, #0d1b2a 0%, #1a3a5c 100%)' }}
    >
      <div className="w-full max-w-md">
        <button
          onClick={() => setScreen('IDLE')}
          className="mb-8 text-sm flex items-center gap-2"
          style={{ color: '#5a8ab0' }}
        >
          ← Back
        </button>

        <h1 className="text-4xl font-bold mb-2" style={{ color: '#e8f0fe' }}>
          Sign in
        </h1>
        <p className="mb-10" style={{ color: '#5a8ab0' }}>
          Enter your Employee ID to begin
        </p>

        <div className="space-y-4">
          <div>
            <label className="block text-sm mb-2" style={{ color: '#90b8e0' }}>
              Employee ID
            </label>
            <input
              className="w-full px-5 py-4 rounded-xl text-xl outline-none"
              style={{
                background: '#1a2d42',
                border: '2px solid #2E75B6',
                color: '#e8f0fe',
              }}
              placeholder="e.g. EMP12345"
              value={employeeId}
              onChange={(e) => setEmployeeId(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && handleLogin()}
              autoFocus
            />
          </div>
          <div>
            <label className="block text-sm mb-2" style={{ color: '#90b8e0' }}>
              Display Name (optional)
            </label>
            <input
              className="w-full px-5 py-4 rounded-xl text-xl outline-none"
              style={{
                background: '#1a2d42',
                border: '2px solid #243d57',
                color: '#e8f0fe',
              }}
              placeholder="Your name"
              value={displayName}
              onChange={(e) => setDisplayName(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && handleLogin()}
            />
          </div>
        </div>

        {error && (
          <p className="mt-4 text-red-400 text-sm">{error}</p>
        )}

        <button
          onClick={handleLogin}
          disabled={loading}
          className="mt-8 w-full py-5 rounded-xl text-xl font-bold transition-opacity"
          style={{ background: '#2E75B6', color: '#fff', opacity: loading ? 0.6 : 1 }}
        >
          {loading ? 'Signing in…' : 'Continue →'}
        </button>
      </div>
    </div>
  )
}

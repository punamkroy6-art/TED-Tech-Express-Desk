import { api, setAuthHeader } from '../api/client'
import { useSession } from '../store/sessionStore'

const ISSUE_TYPES = [
  { key: 'software', label: 'Software / App', icon: '🖥️', desc: 'Crashes, errors, slow performance' },
  { key: 'network', label: 'Network / Wi-Fi', icon: '📡', desc: 'No internet, VPN, slow connection' },
  { key: 'hardware', label: 'Hardware', icon: '🔧', desc: 'Screen, keyboard, power, USB' },
  { key: 'password', label: 'Password / Access', icon: '🔐', desc: 'Locked account, expired password' },
  { key: 'loaner', label: 'Loaner Device', icon: '📦', desc: 'Borrow a temporary device' },
  { key: 'other', label: 'Something else', icon: '💬', desc: 'Describe your issue' },
]

export default function HomeScreen() {
  const { employee, setScreen, reset } = useSession()

  const handleLogout = async () => {
    try {
      await api.delete('/auth/session')
    } catch { /* ignore */ }
    setAuthHeader(null)
    reset()
  }

  const handleSelect = (key: string) => {
    if (key === 'loaner') {
      setScreen('LOANER')
    } else {
      setScreen('DIAGNOSE')
    }
  }

  return (
    <div
      className="flex flex-col h-screen"
      style={{ background: 'linear-gradient(135deg, #0d1b2a 0%, #1a3a5c 100%)' }}
    >
      {/* Header */}
      <div className="flex items-center justify-between px-8 py-6">
        <div>
          <h1 className="text-3xl font-bold" style={{ color: '#e8f0fe' }}>
            Hi, {employee?.name || 'there'} 👋
          </h1>
          <p className="text-sm mt-1" style={{ color: '#5a8ab0' }}>
            What can we help you with today?
          </p>
        </div>
        <button
          onClick={handleLogout}
          className="px-5 py-2 rounded-lg text-sm"
          style={{ background: '#1a2d42', color: '#90b8e0', border: '1px solid #243d57' }}
        >
          End Session
        </button>
      </div>

      {/* Issue grid */}
      <div className="grid grid-cols-2 gap-4 px-8 pb-8 flex-1 overflow-auto">
        {ISSUE_TYPES.map((issue) => (
          <button
            key={issue.key}
            onClick={() => handleSelect(issue.key)}
            className="flex flex-col items-start p-6 rounded-2xl text-left transition-all hover:scale-[1.02] active:scale-95"
            style={{
              background: '#1a2d42',
              border: '1px solid #243d57',
            }}
          >
            <span className="text-4xl mb-3">{issue.icon}</span>
            <span className="text-xl font-semibold mb-1" style={{ color: '#e8f0fe' }}>
              {issue.label}
            </span>
            <span className="text-sm" style={{ color: '#5a8ab0' }}>
              {issue.desc}
            </span>
          </button>
        ))}
      </div>
    </div>
  )
}

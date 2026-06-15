import { useSession } from '../store/sessionStore'

export default function IdleScreen() {
  const setScreen = useSession((s) => s.setScreen)

  return (
    <div
      className="flex flex-col items-center justify-center h-screen cursor-pointer select-none"
      style={{ background: 'linear-gradient(135deg, #0d1b2a 0%, #1a3a5c 100%)' }}
      onClick={() => setScreen('AUTH')}
    >
      {/* Logo / Icon */}
      <div className="mb-8">
        <div
          className="w-32 h-32 rounded-full flex items-center justify-center text-6xl shadow-2xl"
          style={{ background: 'linear-gradient(135deg, #2E75B6, #1a5ca0)' }}
        >
          💻
        </div>
      </div>

      <h1 className="text-7xl font-black tracking-tight mb-2" style={{ color: '#e8f0fe' }}>
        TED
      </h1>
      <p className="text-2xl font-light mb-1" style={{ color: '#90b8e0' }}>
        Tech Express Desk
      </p>
      <p className="text-lg mb-16" style={{ color: '#5a8ab0' }}>
        AI-Powered IT Support
      </p>

      {/* Tap to start */}
      <div
        className="px-12 py-5 rounded-full text-xl font-semibold animate-pulse"
        style={{ background: '#2E75B6', color: '#fff' }}
      >
        Tap anywhere to get started
      </div>

      {/* Location badge */}
      <p className="mt-10 text-sm" style={{ color: '#3d6a8a' }}>
        KIOSK-001 · Building A · Level 2
      </p>

      {/* Vision AI brand link */}
      <a
        href="http://localhost:5500/landing-page.html"
        target="_blank"
        rel="noopener noreferrer"
        onClick={(e) => e.stopPropagation()}
        className="mt-6 flex items-center gap-2 text-xs px-4 py-2 rounded-full transition-all hover:opacity-80"
        style={{
          color: '#3d6a8a',
          border: '1px solid #1e3a52',
          textDecoration: 'none',
        }}
      >
        <span
          className="w-4 h-4 rounded flex items-center justify-center text-xs"
          style={{ background: 'linear-gradient(135deg, #2E75B6, #22d3ee)' }}
        >
          👁
        </span>
        Powered by Vision AI ↗
      </a>
    </div>
  )
}

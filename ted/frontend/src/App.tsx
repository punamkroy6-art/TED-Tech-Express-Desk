import { Component, type ReactNode } from 'react'
import { useSession } from './store/sessionStore'
import IdleScreen from './screens/IdleScreen'
import AuthScreen from './screens/AuthScreen'
import HomeScreen from './screens/HomeScreen'
import DiagnoseScreen from './screens/DiagnoseScreen'
import ResultScreen from './screens/ResultScreen'
import EscalateScreen from './screens/EscalateScreen'
import LoanerScreen from './screens/LoanerScreen'
import CsatScreen from './screens/CsatScreen'
import AutoFixingScreen from './screens/AutoFixingScreen'
import DiagnosticScreen from './screens/DiagnosticScreen'
import { useIdleTimeout } from './hooks/useIdleTimeout'
import './index.css'

// Global error boundary — catches render crashes and shows a safe fallback
class ScreenErrorBoundary extends Component<{ onReset: () => void; children: ReactNode }, { crashed: boolean }> {
  state = { crashed: false }
  static getDerivedStateFromError() { return { crashed: true } }
  componentDidCatch(e: Error) { console.error('[TED] Screen crash:', e.message) }
  render() {
    if (this.state.crashed) {
      return (
        <div className="ted-screen items-center justify-center text-center">
          <div style={{ position: 'relative', zIndex: 1, maxWidth: 420, padding: '0 24px' }}>
            <div className="ted-card" style={{ padding: 40 }}>
              <div style={{ fontSize: '3rem', marginBottom: 16 }}>⚠️</div>
              <span className="section-tag">Screen Error</span>
              <h2 style={{ fontSize: '1.5rem', fontWeight: 700, color: 'var(--text)', marginBottom: 12 }}>
                Something went wrong
              </h2>
              <p style={{ color: 'var(--text-muted)', fontSize: '.9rem', marginBottom: 24 }}>
                TED encountered an unexpected error on this screen.
              </p>
              <button
                className="btn-primary"
                onClick={() => { this.setState({ crashed: false }); this.props.onReset() }}
                style={{ width: '100%', padding: 14, borderRadius: 'var(--radius)' }}
              >
                Return to Home
              </button>
            </div>
          </div>
        </div>
      )
    }
    return this.props.children
  }
}

export default function App() {
  const screen = useSession((s) => s.screen)
  const setScreen = useSession((s) => s.setScreen)
  useIdleTimeout()

  return (
    <ScreenErrorBoundary onReset={() => setScreen('HOME')}>
      <div style={{ width: '100vw', height: '100vh', overflow: 'hidden', background: '#070b14' }}>
        {screen === 'IDLE' && <IdleScreen />}
        {screen === 'AUTH' && <AuthScreen />}
        {screen === 'HOME' && <HomeScreen />}
        {(screen === 'DIAGNOSE' || screen === 'SCANNING') && <DiagnoseScreen />}
        {screen === 'RESULT' && <ResultScreen />}
        {screen === 'ESCALATE' && <EscalateScreen />}
        {screen === 'LOANER' && <LoanerScreen />}
        {screen === 'DIAGNOSTIC' && <DiagnosticScreen />}
        {screen === 'AUTOFIXING' && <AutoFixingScreen />}
        {screen === 'CSAT' && <CsatScreen />}
      </div>
    </ScreenErrorBoundary>
  )
}

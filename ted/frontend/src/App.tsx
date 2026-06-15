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
import { useIdleTimeout } from './hooks/useIdleTimeout'
import './index.css'

export default function App() {
  const screen = useSession((s) => s.screen)
  useIdleTimeout()

  return (
    <div style={{ width: '100vw', height: '100vh', overflow: 'hidden', background: '#070b14' }}>
      {screen === 'IDLE' && <IdleScreen />}
      {screen === 'AUTH' && <AuthScreen />}
      {screen === 'HOME' && <HomeScreen />}
      {(screen === 'DIAGNOSE' || screen === 'SCANNING') && <DiagnoseScreen />}
      {screen === 'RESULT' && <ResultScreen />}
      {screen === 'ESCALATE' && <EscalateScreen />}
      {screen === 'LOANER' && <LoanerScreen />}
      {screen === 'AUTOFIXING' && <AutoFixingScreen />}
      {screen === 'CSAT' && <CsatScreen />}
    </div>
  )
}

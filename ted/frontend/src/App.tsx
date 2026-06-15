import { useSession } from './store/sessionStore'
import IdleScreen from './screens/IdleScreen'
import AuthScreen from './screens/AuthScreen'
import HomeScreen from './screens/HomeScreen'
import DiagnoseScreen from './screens/DiagnoseScreen'
import ResultScreen from './screens/ResultScreen'
import EscalateScreen from './screens/EscalateScreen'
import LoanerScreen from './screens/LoanerScreen'
import CsatScreen from './screens/CsatScreen'
import { useIdleTimeout } from './hooks/useIdleTimeout'
import './index.css'

export default function App() {
  const screen = useSession((s) => s.screen)
  useIdleTimeout()

  return (
    <div className="h-screen w-screen overflow-hidden">
      {screen === 'IDLE' && <IdleScreen />}
      {screen === 'AUTH' && <AuthScreen />}
      {screen === 'HOME' && <HomeScreen />}
      {(screen === 'DIAGNOSE' || screen === 'SCANNING') && <DiagnoseScreen />}
      {screen === 'RESULT' && <ResultScreen />}
      {screen === 'ESCALATE' && <EscalateScreen />}
      {screen === 'LOANER' && <LoanerScreen />}
      {screen === 'CSAT' && <CsatScreen />}
    </div>
  )
}

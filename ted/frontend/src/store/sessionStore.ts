import { create } from 'zustand'

export type Screen =
  | 'IDLE'
  | 'AUTH'
  | 'HOME'
  | 'DIAGNOSE'
  | 'SCANNING'
  | 'AUTOFIXING'
  | 'DIAGNOSTIC'
  | 'RESULT'
  | 'ESCALATE'
  | 'LOANER'
  | 'CSAT'

export interface DiagnosisResult {
  diagnosis: string
  confidence: number
  severity: string
  fix_steps: string[]
  kb_references: Array<{ id: string; title: string; url: string }>
  action: string
  suggested_group: string
  processing_ms?: number
}

interface SessionStore {
  screen: Screen
  token: string | null
  sessionId: string | null
  employee: { id: string; name: string; email: string; dept: string } | null
  diagnosis: DiagnosisResult | null
  ticketId: string | null
  loanerId: string | null
  // Actions
  setScreen: (s: Screen) => void
  setAuth: (token: string, sessionId: string, employee: SessionStore['employee']) => void
  setDiagnosis: (d: DiagnosisResult) => void
  setTicketId: (id: string) => void
  setLoanerId: (id: string) => void
  reset: () => void
}

const initial = {
  screen: 'IDLE' as Screen,
  token: null,
  sessionId: null,
  employee: null,
  diagnosis: null,
  ticketId: null,
  loanerId: null,
}

export const useSession = create<SessionStore>((set) => ({
  ...initial,
  setScreen: (screen) => set({ screen }),
  setAuth: (token, sessionId, employee) => set({ token, sessionId, employee, screen: 'HOME' }),
  setDiagnosis: (diagnosis) => set({ diagnosis }),
  setTicketId: (ticketId) => set({ ticketId }),
  setLoanerId: (loanerId) => set({ loanerId }),
  reset: () => set(initial),
}))

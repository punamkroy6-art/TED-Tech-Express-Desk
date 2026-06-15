import { useEffect, useRef } from 'react'
import { api, setAuthHeader } from '../api/client'
import { useSession } from '../store/sessionStore'

const IDLE_MS = 5 * 60 * 1000   // 5 minutes
const WARN_MS = 4 * 60 * 1000   // show warning at 4 min

const EVENTS = ['mousemove', 'mousedown', 'keydown', 'touchstart', 'click']

export function useIdleTimeout() {
  const { screen, reset } = useSession()
  const timer = useRef<ReturnType<typeof setTimeout> | null>(null)
  const warnTimer = useRef<ReturnType<typeof setTimeout> | null>(null)

  const active = !['IDLE', 'AUTH'].includes(screen)

  const clearTimers = () => {
    if (timer.current) clearTimeout(timer.current)
    if (warnTimer.current) clearTimeout(warnTimer.current)
  }

  const startTimers = () => {
    clearTimers()
    warnTimer.current = setTimeout(() => {
      // Could show a "Still there?" banner — for now just log
      console.warn('[TED] Idle warning — 1 min to auto-reset')
    }, WARN_MS)

    timer.current = setTimeout(async () => {
      try {
        await api.post('/auth/session/outcome', { outcome: 'abandoned' })
      } catch { /* ignore */ }
      setAuthHeader(null)
      reset()
    }, IDLE_MS)
  }

  useEffect(() => {
    if (!active) { clearTimers(); return }

    const handler = () => startTimers()
    EVENTS.forEach(e => window.addEventListener(e, handler, { passive: true }))
    startTimers()   // start immediately

    return () => {
      EVENTS.forEach(e => window.removeEventListener(e, handler))
      clearTimers()
    }
  }, [active])
}

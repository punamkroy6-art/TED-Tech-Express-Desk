import { useEffect, useState } from 'react'
import { api } from '../api/client'
import { useSession } from '../store/sessionStore'

export default function EscalateScreen() {
  const { ticketId, diagnosis, setTicketId, reset } = useSession()
  const [autoCreating, setAutoCreating] = useState(!ticketId)

  // Auto-create ticket if routed here directly from create_ticket action
  useEffect(() => {
    if (!ticketId) {
      api.post('/ticket', { device_serial: '' })
        .then(r => { setTicketId(r.data.ticket_id); setAutoCreating(false) })
        .catch(() => setAutoCreating(false))
    }
  }, [])

  return (
    <div
      className="flex flex-col items-center justify-center h-screen px-8 text-center"
      style={{ background: 'linear-gradient(135deg, #0d1b2a 0%, #1a3a5c 100%)' }}
    >
      {autoCreating ? (
        <>
          <div className="text-5xl animate-spin mb-6">⚙️</div>
          <h1 className="text-2xl font-bold" style={{ color: '#e8f0fe' }}>Creating ticket…</h1>
        </>
      ) : (
        <>
      <div className="text-6xl mb-6">🎫</div>
      <h1 className="text-3xl font-bold mb-3" style={{ color: '#e8f0fe' }}>
        Ticket raised
      </h1>
      <p className="text-lg mb-2" style={{ color: '#90b8e0' }}>
        A Service Desk agent will assist you shortly.
      </p>
      {ticketId && (
        <div
          className="mt-4 px-6 py-3 rounded-xl font-mono text-xl"
          style={{ background: '#1a2d42', color: '#2E75B6', border: '1px solid #243d57' }}
        >
          {ticketId}
        </div>
      )}
      {diagnosis?.suggested_group && (
        <p className="mt-4 text-sm" style={{ color: '#5a8ab0' }}>
          Assigned to: {diagnosis.suggested_group}
        </p>
      )}
      <p className="mt-8 text-sm" style={{ color: '#3d6a8a' }}>
        Your diagnostic data has been attached to the ticket.
      </p>
      <button
        onClick={reset}
        className="mt-10 px-10 py-4 rounded-xl text-lg font-bold"
        style={{ background: '#2E75B6', color: '#fff' }}
      >
        Done — End Session
      </button>
        </>
      )}
    </div>
  )
}

import { useEffect, useState } from 'react'
import { api } from '../api/client'
import { useSession } from '../store/sessionStore'

export default function EscalateScreen() {
  const { ticketId, diagnosis, setTicketId, reset } = useSession()
  const [autoCreating, setAutoCreating] = useState(!ticketId)

  useEffect(() => {
    if (!ticketId) {
      api.post('/ticket', { device_serial: '' })
        .then(r => { setTicketId(r.data.ticket_id); setAutoCreating(false) })
        .catch(() => setAutoCreating(false))
    }
  }, [])

  return (
    <div className="ted-screen items-center justify-center text-center">
      <div className="orb" style={{ width: 400, height: 400, top: '50%', left: '50%', transform: 'translate(-50%,-50%)', background: 'radial-gradient(circle, rgba(59,130,246,.12) 0%, transparent 70%)' }} />

      <div style={{ position: 'relative', zIndex: 1, maxWidth: 480, padding: '0 24px', width: '100%' }}>
        {autoCreating ? (
          <div className="ted-card" style={{ padding: 48 }}>
            <div style={{ width: 64, height: 64, borderRadius: '50%', background: 'var(--surface-hi)', border: '2px solid var(--border-hi)', display: 'grid', placeItems: 'center', margin: '0 auto 24px', animation: 'spin 1.2s linear infinite' }}>
              <svg viewBox="0 0 24 24" fill="none" stroke="var(--cyan)" strokeWidth="2" style={{ width: 30, height: 30 }}><path d="M12 2v4m0 12v4M4.93 4.93l2.83 2.83m8.48 8.48 2.83 2.83M2 12h4m12 0h4M4.93 19.07l2.83-2.83m8.48-8.48 2.83-2.83"/></svg>
            </div>
            <h2 style={{ fontSize: '1.5rem', fontWeight: 700, color: 'var(--text)', marginBottom: 8 }}>Creating your ticket…</h2>
            <p style={{ color: 'var(--text-muted)', fontSize: '.9rem' }}>Attaching diagnostic data to your request</p>
          </div>
        ) : (
          <div className="ted-card" style={{ padding: 48 }}>
            {/* Icon */}
            <div style={{ width: 72, height: 72, borderRadius: '50%', background: 'rgba(59,130,246,.12)', border: '1px solid rgba(59,130,246,.3)', display: 'grid', placeItems: 'center', margin: '0 auto 28px', boxShadow: '0 0 30px rgba(59,130,246,.2)' }}>
              <svg viewBox="0 0 24 24" fill="var(--blue)" style={{ width: 34, height: 34 }}><path d="M20 2H4c-1.1 0-2 .9-2 2v18l4-4h14c1.1 0 2-.9 2-2V4c0-1.1-.9-2-2-2zm-2 12H6v-2h12v2zm0-3H6V9h12v2zm0-3H6V6h12v2z"/></svg>
            </div>

            <span className="section-tag">Service Desk Notified</span>
            <h1 style={{ fontSize: '1.9rem', fontWeight: 800, letterSpacing: '-.03em', color: 'var(--text)', marginBottom: 10 }}>
              Ticket Raised
            </h1>
            <p style={{ color: 'var(--text-muted)', fontSize: '.95rem', marginBottom: 24 }}>
              A Service Desk agent will contact you shortly
            </p>

            {/* Ticket ID */}
            {ticketId && (
              <div style={{ display: 'inline-flex', alignItems: 'center', gap: 10, padding: '10px 20px', background: 'var(--surface-hi)', border: '1px solid var(--border-hi)', borderRadius: 'var(--radius)', marginBottom: 16 }}>
                <svg viewBox="0 0 24 24" fill="none" stroke="var(--cyan)" strokeWidth="2" style={{ width: 16, height: 16 }}><rect x="2" y="7" width="20" height="14" rx="2"/><path d="M16 7V5a2 2 0 0 0-2-2h-4a2 2 0 0 0-2 2v2"/></svg>
                <span style={{ fontFamily: 'monospace', fontSize: '1rem', fontWeight: 700, color: 'var(--cyan)', letterSpacing: '.05em' }}>{ticketId}</span>
              </div>
            )}

            {/* Meta */}
            <div style={{ display: 'flex', flexDirection: 'column', gap: 8, marginBottom: 32 }}>
              {diagnosis?.suggested_group && (
                <div style={{ display: 'flex', justifyContent: 'space-between', padding: '8px 14px', background: 'var(--surface)', borderRadius: 8 }}>
                  <span style={{ fontSize: '.82rem', color: 'var(--text-dim)' }}>Assigned to</span>
                  <span style={{ fontSize: '.82rem', color: 'var(--text-muted)', fontWeight: 600 }}>{diagnosis.suggested_group}</span>
                </div>
              )}
              <div style={{ display: 'flex', justifyContent: 'space-between', padding: '8px 14px', background: 'var(--surface)', borderRadius: 8 }}>
                <span style={{ fontSize: '.82rem', color: 'var(--text-dim)' }}>Status</span>
                <span style={{ fontSize: '.82rem', color: '#22c55e', fontWeight: 600 }}>● Open</span>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between', padding: '8px 14px', background: 'var(--surface)', borderRadius: 8 }}>
                <span style={{ fontSize: '.82rem', color: 'var(--text-dim)' }}>Diagnostic data</span>
                <span style={{ fontSize: '.82rem', color: 'var(--text-muted)', fontWeight: 600 }}>✓ Attached</span>
              </div>
            </div>

            <button
              onClick={reset}
              className="btn-primary"
              style={{ width: '100%', padding: '14px', fontSize: '1rem', borderRadius: 'var(--radius)' }}
            >
              Done — End Session
            </button>
          </div>
        )}
      </div>
    </div>
  )
}

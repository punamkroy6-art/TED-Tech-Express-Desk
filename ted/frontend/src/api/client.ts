import axios, { AxiosError } from 'axios'

// Production: point to hosted backend via VITE_API_URL.
// Development: Vite proxy (localhost:8000 via /api).
const BASE_URL = import.meta.env.VITE_API_URL
  ? `${import.meta.env.VITE_API_URL}/api`
  : '/api'

// 12s timeout — long enough for a warm backend, short enough to fall back fast
export const api = axios.create({ baseURL: BASE_URL, timeout: 12000 })

export const setAuthHeader = (token: string | null) => {
  if (token) {
    api.defaults.headers.common['Authorization'] = `Bearer ${token}`
  } else {
    delete api.defaults.headers.common['Authorization']
  }
}

/* ════════════════════════════════════════════════════════════════════════
 * DEMO-MODE FALLBACK
 * If the backend is unreachable (network error, timeout, 5xx, cold-start),
 * the kiosk still works end-to-end using realistic client-side mock data.
 * This guarantees the demo never breaks regardless of backend status.
 * ════════════════════════════════════════════════════════════════════════ */

let demoMode = false
export const isDemoMode = () => demoMode

const uid = (n = 8) =>
  Math.random().toString(36).slice(2, 2 + n).toUpperCase()

// Keyword → fix mapping (mirrors the backend rule engine)
function classify(text: string) {
  const t = (text || '').toLowerCase()
  const has = (...k: string[]) => k.some(w => t.includes(w))
  if (has('blue screen', 'bsod', 'crash')) return { fix_key: 'BSOD', sev: 'critical', dx: 'Driver IRQL not less or equal (Blue Screen of Death).' }
  if (has('vpn', 'tunnel')) return { fix_key: 'VPN', sev: 'high', dx: 'Corporate VPN tunnel connection failure or gateway timeout.' }
  if (has('wifi', 'wi-fi', 'internet', 'network', 'connect')) return { fix_key: 'WIFI', sev: 'medium', dx: 'Network adapter or DNS resolution issue detected.' }
  if (has('okta', 'mfa', 'login', 'lock', 'password')) return { fix_key: 'OKTA', sev: 'medium', dx: 'Authentication cache issue — account may be locked or MFA expired.' }
  if (has('printer', 'print')) return { fix_key: 'PRINTER', sev: 'low', dx: 'Print spooler stalled or print queue stuck.' }
  if (has('outlook', 'email', 'mail', 'calendar', 'sync')) return { fix_key: 'OUTLOOK', sev: 'medium', dx: 'Outlook mailbox not syncing — profile or cache issue.' }
  if (has('teams', 'meeting', 'audio', 'camera', 'mic')) return { fix_key: 'TEAMS', sev: 'medium', dx: 'Microsoft Teams audio/video or cache problem.' }
  if (has('disk', 'storage', 'space', 'full')) return { fix_key: 'DISK', sev: 'high', dx: 'System drive is critically low on free space.' }
  if (has('slow', 'freeze', 'memory', 'ram', 'lag')) return { fix_key: 'HIGH_MEMORY', sev: 'medium', dx: 'Device is running slow due to high memory usage.' }
  return { fix_key: 'HIGH_MEMORY', sev: 'medium', dx: 'General performance issue detected on the device.' }
}

const FIX_STEPS: Record<string, string[]> = {
  BSOD: ['Flush Windows event logs', 'Clear crash dump files', 'Free system memory', 'Run device health check'],
  VPN: ['Flush DNS cache', 'Reset Winsock catalog', 'Clear network route cache'],
  WIFI: ['Flush DNS cache', 'Reset Winsock catalog', 'Clear ARP cache'],
  OKTA: ['Clear Edge browser cache', 'Clear Chrome browser cache', 'Open Okta self-service portal'],
  PRINTER: ['Stop Print Spooler service', 'Clear stuck print queue', 'Restart Print Spooler service'],
  OUTLOOK: ['Close Outlook', 'Clear Outlook temp files', 'Restart Outlook'],
  TEAMS: ['Close Microsoft Teams', 'Clear Teams cache', 'Restart Teams'],
  DISK: ['Clear Windows temp files', 'Clear user temp folder', 'Remove Windows error reports'],
  HIGH_MEMORY: ['Check top memory consumers', 'Clear standby memory', 'Reclaim memory without closing browsers'],
}

const GROUP: Record<string, string> = {
  BSOD: 'IT_Desktop_Support', VPN: 'IT_Network', WIFI: 'IT_Network',
  OKTA: 'IT_IAM', PRINTER: 'IT_SD', OUTLOOK: 'IT_SD',
  TEAMS: 'IT_SD', DISK: 'IT_Desktop_Support', HIGH_MEMORY: 'IT_SD',
}

// Build a mock response for a given request
function mockResponse(url: string, body: any): any {
  // ── Auth ──
  if (url.includes('/auth/session') && !url.includes('outcome')) {
    return {
      token: 'demo.' + uid(24),
      session_id: uid(12).toLowerCase(),
      employee: {
        id: body?.employee_id || 'EMP-DEMO',
        name: body?.display_name || body?.employee_id || 'Demo User',
        email: `${(body?.employee_id || 'demo')}@company.com`,
        dept: 'Engineering',
      },
    }
  }
  if (url.includes('/auth/session/outcome')) return { status: 'ok', demo: true }

  // ── Full diagnostic scan ──
  if (url.includes('/diagnostic/run')) {
    return {
      overall_health: 'warning',
      issues_found: ['High RAM: 91%', '1 driver(s) flagged'],
      suggested_queries: ['computer running slow high memory usage', 'cannot connect to wifi network'],
      hardware: {
        cpu: { percent: 88, cores_logical: 8, status: 'warning' },
        memory: { percent: 91, used_gb: 14.6, total_gb: 16, status: 'warning' },
        disk: { primary: { percent: 72, free_gb: 48, status: 'ok' } },
        battery: { present: true, percent: 64, plugged: true, status: 'ok' },
      },
      software: {
        os: { os: 'Windows', release: '11', hostname: 'TED-DEMO-PC', defender_enabled: true },
        network: { internet: 'ok', dns: 'ok' },
        drivers: { failed_drivers: [{ name: 'Realtek Audio' }] },
      },
    }
  }

  // ── AI diagnosis ──
  if (url.includes('/diagnose')) {
    const { fix_key, sev, dx } = classify(body?.error_text || '')
    return {
      diagnosis: dx,
      confidence: 0.93,
      severity: sev,
      fix_steps: FIX_STEPS[fix_key] || [],
      kb_references: [],
      suggested_group: GROUP[fix_key] || 'IT_SD',
      action: 'self_resolve',
      llm_model: 'rule_engine',
      fix_key,
      auto_executable: true,
    }
  }

  // ── Auto-fix start ──
  if (url.includes('/autofix/start')) {
    const key = (body?.fix_key || 'HIGH_MEMORY').toUpperCase()
    const labels = FIX_STEPS[key] || FIX_STEPS.HIGH_MEMORY
    const jobId = 'demo-' + uid(8)
    _demoJobs[jobId] = {
      job_id: jobId, fix_key: key, fix_name: key.replace('_', ' '),
      labels, started: Date.now(),
    }
    return { job_id: jobId, fix_name: key.replace('_', ' '), total_steps: labels.length }
  }

  // ── Auto-fix status (simulated progress) ──
  if (url.includes('/autofix/status/')) {
    const jobId = url.split('/autofix/status/')[1]
    const job = _demoJobs[jobId]
    if (!job) return { done: true, overall_success: true, steps: [], summary: 'Auto-fix completed.' }
    const elapsed = Date.now() - job.started
    const perStep = 900
    const steps = job.labels.map((label: string, i: number) => {
      const startAt = i * perStep
      let status: string = 'pending'
      if (elapsed >= startAt + perStep) status = 'done'
      else if (elapsed >= startAt) status = 'running'
      return {
        label, status,
        success: status === 'done',
        output: status === 'done' ? `${label} — completed successfully` : '',
        duration_ms: status === 'done' ? perStep : 0,
      }
    })
    const done = elapsed >= job.labels.length * perStep
    const passed = steps.filter((s: any) => s.success).length
    return {
      job_id: jobId, fix_key: job.fix_key, fix_name: job.fix_name,
      done, current_step: Math.min(Math.floor(elapsed / perStep), job.labels.length - 1),
      overall_success: done && passed > 0,
      steps,
      summary: done ? `Auto-fix completed — ${passed}/${job.labels.length} steps succeeded. Issue should be resolved.` : '',
    }
  }

  // ── Ticket ──
  if (url.includes('/ticket')) {
    return { ticket_id: 'TED-' + uid(6), status: 'demo', url: '#' }
  }

  // ── Loaner ──
  if (url.includes('/loaner/request')) {
    return {
      loaner_id: 'LOAN-' + uid(6),
      device_type: body?.device_type || 'laptop',
      locker_bay: 'A3',
      status: 'dispensing',
      message: `Please collect your ${body?.device_type || 'device'} from Locker Bay A3.`,
    }
  }

  // ── Health ──
  if (url.includes('/health')) return { status: 'demo', database: 'mock', redis: 'mock' }

  return { demo: true }
}

const _demoJobs: Record<string, any> = {}

// Interceptor: on ANY network failure, serve a realistic mock so the demo continues
api.interceptors.response.use(
  (resp) => resp,
  (error: AxiosError) => {
    const cfg: any = error.config || {}
    const noResponse = !error.response          // network error / timeout / CORS
    const serverDown = error.response && error.response.status >= 500
    if (noResponse || serverDown) {
      demoMode = true
      const url = (cfg.url || '')
      let body: any = {}
      try { body = cfg.data ? JSON.parse(cfg.data) : {} } catch { body = {} }
      const data = mockResponse(url, body)
      // Return a resolved response so callers proceed normally
      return Promise.resolve({ data, status: 200, statusText: 'OK (demo)', headers: {}, config: cfg })
    }
    return Promise.reject(error)
  }
)

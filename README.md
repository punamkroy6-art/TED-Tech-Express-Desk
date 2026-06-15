# 💻 TED — Tech Express Desk

> **AI-powered self-service IT kiosk** — employees walk up, get instant hardware + software diagnostics, AI-driven auto-fix, and automatic Freshservice ticket creation — all without waiting for the Service Desk.

[![Python](https://img.shields.io/badge/Python-3.11-blue?logo=python)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.111-green?logo=fastapi)](https://fastapi.tiangolo.com)
[![React](https://img.shields.io/badge/React-19-61DAFB?logo=react)](https://react.dev)
[![TypeScript](https://img.shields.io/badge/TypeScript-6.0-3178C6?logo=typescript)](https://typescriptlang.org)
[![Groq](https://img.shields.io/badge/LLM-Groq%20LLaMA%203.3-orange)](https://groq.com)
[![Vision AI](https://img.shields.io/badge/Powered%20by-Vision%20AI-22d3ee)](http://localhost:5500/landing-page.html)

---

## 📋 Project Overview

**TED (Tech Express Desk)** is a physical AI kiosk installed on-site at office locations. It solves a real problem in corporate IT: **employees wait 45 minutes on average for a first response** to simple, repeatable issues — issues that could be resolved in under 5 minutes with guided automation.

### The Problem TED Solves

| Issue | Impact |
|---|---|
| Employees wait hours for simple fixes | **45 min** avg. first response time |
| Same issues repeat every month | **60–70%** of tickets are repeat / low-complexity |
| SD agents handle low-value work | **$22** cost per ticket resolved by an agent |
| Tickets arrive with no diagnostic context | Agents spend time investigating, not fixing |
| No walk-up intelligent support on-site | Employees self-diagnose unsuccessfully |

### How It Works — Three Intelligent Paths

```
Employee walks up → Badge / SSO login → AI diagnostics run in <60 sec
                                                    │
                    ┌───────────────────────────────┼───────────────────────────────┐
                    ▼                               ▼                               ▼
           Path A (~30%)                    Path B (majority)               Path C (hardware)
     Self-Service Resolution           Guided Fix + SD Ticket           Loaner Device Dispensed
   ─────────────────────────        ────────────────────────────       ──────────────────────────
   AI auto-fix applied               AI provides step-by-step fix      Hardware failure confirmed
   Employee confirms fix             Screenshot & diagnosis captured    Kiosk locker unlocks device
   Session ends — no ticket          Freshworks ticket auto-created     Asset logged in Freshworks
                                     Pre-filled, AI-enriched ticket     Zero downtime for employee
```

---

## 📈 Business Value & ROI

### Projected Outcomes (from Business Case)

| KPI | Target | Basis |
|---|---|---|
| **Ticket deflection rate** | > 30% | Sessions resolved without any SD ticket |
| **Self-service resolution** | > 25% | Issues resolved at kiosk — zero SD involvement |
| **Kiosk session time** | < 5 min | From login to resolution or ticket creation |
| **AI diagnosis accuracy** | > 80% | Category correct vs SD final outcome |
| **SD resolution speed** | 20% faster | Handle time vs standard tickets (pre-filled data) |
| **Employee CSAT** | > 4.0 / 5 | Post-session rating target |

### ROI Calculation

**Assumptions (1,000 SD tickets / month, $22 cost/ticket):**

```
Ticket Deflection (Path A)
  1,000 tickets/month × 30% deflection = 300 fewer tickets
  300 × $22 = $6,600 saved/month → $79,200/year

SD Efficiency (Path B — pre-filled tickets)
  700 remaining tickets × 20% faster handle time
  ~3 hours saved/agent/month at £50/hr = £1,800/year per agent

Employee Productivity
  Avg. wait time cut: 2.3 days → <5 min per issue
  ~500 employees × 1 issue/month × 2.3 days lost = 1,150 lost days/year
  Recovered at avg. £250/day = £287,500/year in productivity

Total Estimated Annual Saving: £300,000–£400,000+
```

> *Figures scale with ticket volume. 500-employee site with 1,000 tickets/month used as baseline.*

### Implementation Timeline

| Phase | Weeks | Deliverables |
|---|---|---|
| **01 Foundation** | 1–3 | Docker infra, PostgreSQL, SSO, Badge auth |
| **02 AI Core** | 4–7 | Error DB (100+ patterns), OCR, LLM, RAG |
| **03 ITSM** | 8–10 | Freshworks integration, auto-ticket, KB lookup |
| **04 Kiosk UI + QA** | 11–14 | React touch UI, all screen flows, OWASP scan |
| **05 Pilot + Rollout** | 15–20 | 1–2 kiosk pilot, Grafana, CSAT, full rollout |

**🎯 Go-Live Target: Week 20**

---

## 🎬 Live Demo

<p align="center">
  <img src="screenshots/ted-demo.gif" width="100%" alt="TED — Full session walkthrough: Idle → Auth → Home → Diagnose → IoT Auto-Fix → CSAT → Idle"/>
</p>

> **Full session walkthrough** — Idle · Employee sign-in · Issue selection · AI diagnosis · IoT auto-fix executing in real-time · CSAT rating · Session reset

---

## 🏗️ Architecture

```
TED PROJECT
├── landing-page.html          # Vision AI marketing page (static HTML)
├── ted/
│   ├── backend/               # FastAPI REST API
│   │   ├── app/
│   │   │   ├── routers/       # auth, diagnose, ticket, loaner, health
│   │   │   ├── services/      # ai_engine, auth_service, freshworks, rag
│   │   │   └── models/        # SQLAlchemy ORM (Employee, Session, Diagnosis...)
│   │   ├── seed_data.py       # Seeds 8 error patterns + demo employees
│   │   └── .env.example       # Environment template
│   ├── frontend/              # React + TypeScript + Tailwind kiosk UI
│   │   └── src/screens/       # 8 screens: Idle→Auth→Home→Diagnose→Result→CSAT
│   └── autofix/               # Hardware auto-fix engine
│       ├── engine.py          # Orchestrator
│       ├── diagnostics.py     # psutil hardware metrics
│       ├── executor.py        # Local + SSH fix execution (Paramiko)
│       ├── reporter.py        # Word incident reports (python-docx)
│       └── config.yaml        # Fix rules & thresholds
```

---

## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- Node.js 18+

### 1. Backend

```bash
cd ted/backend
cp .env.example .env          # fill in your API keys
pip install -r requirements.txt
python seed_data.py            # seed DB with error patterns
uvicorn app.main:app --reload --port 8000
```

### 2. Frontend

```bash
cd ted/frontend
npm install
npm run dev -- --port 3000
```

Open **http://localhost:3000** — the kiosk is live.

---

## 🧠 AI Diagnostic Engine

Three-tier system — fastest path always wins:

| Tier | Trigger | Examples | Confidence |
|------|---------|---------|-----------|
| **Rule Engine** | Keyword match on 8 built-in patterns | BSOD, VPN, Okta, Printer, Teams, Outlook, Disk, Wi-Fi | 0.55–0.95 |
| **Groq LLM** | No rule match → LLaMA 3.3 70B | SAP, custom apps, unknown issues | 0.65 |
| **Mock fallback** | LLM unavailable | Any | 0.3 |

### Action routing
```
self_resolve  →  ⚡ Auto-fix banner + fix steps
guided_fix    →  Fix steps (no banner)
create_ticket →  Auto-creates Freshservice ticket + Escalate screen
```

---

## ⚡ Auto-Fix Engine

Hardware diagnostics run on every session using **psutil**:

| Rule | Threshold | Fix |
|------|-----------|-----|
| `HIGH_CPU` | > 85% | Kill heavy processes |
| `HIGH_MEMORY` | > 88% | Task Manager guidance |
| `LOW_DISK` | < 5 GB free | Disk Cleanup |
| `DISK_PERCENT_HIGH` | > 90% | Storage cleanup |
| `LOW_BATTERY` | < 15% | Power guidance |

SSH-based remote fix execution via **Paramiko**.
Word incident reports generated via **python-docx** → saved to `ted/reports/`.

---

## 🔗 Freshservice Integration

Add 2 lines to `.env` — no code changes needed:

```env
FRESHWORKS_DOMAIN=yourcompany.freshservice.com
FRESHWORKS_API_KEY=your_raw_api_key_here
```

Test connection: `GET /api/health/freshworks`

Free dev sandbox: **https://freshservice.com/signup**

---

## 📡 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/auth/session` | Login, create kiosk session |
| `POST` | `/api/diagnose` | Run AI diagnosis |
| `POST` | `/api/ticket` | Create Freshservice ticket |
| `POST` | `/api/loaner/request` | Request loaner device |
| `POST` | `/api/auth/session/outcome` | Submit outcome + CSAT score |
| `GET`  | `/api/health` | Backend health check |
| `GET`  | `/api/health/freshworks` | Freshservice connection test |
| `GET`  | `/docs` | Swagger UI |

---

## 🛠️ Tech Stack

**Backend:** FastAPI · SQLAlchemy · SQLite (dev) / PostgreSQL (prod) · FakeRedis (dev) / Redis (prod) · python-jose JWT  
**AI:** Groq (LLaMA 3.3 70B) · xAI (Grok-3) · Rule-based engine · RAG  
**Frontend:** React 19 · TypeScript · Tailwind CSS v4 · Zustand · Axios · Vite  
**Auto-Fix:** psutil · Paramiko · python-docx · PyYAML  
**ITSM:** Freshservice API v2  
**Infra:** Docker Compose · Prometheus metrics · Uvicorn  

---

## 📄 License

MIT — built for the TED Project · Powered by Vision AI

# 💻 TED — Tech Express Desk

> **AI-powered self-service IT support kiosk** — employees walk up, describe their issue, and get instant AI-driven diagnosis, guided fixes, and automatic ticket creation. Built on Vision AI.

[![Python](https://img.shields.io/badge/Python-3.11-blue?logo=python)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.111-green?logo=fastapi)](https://fastapi.tiangolo.com)
[![React](https://img.shields.io/badge/React-19-61DAFB?logo=react)](https://react.dev)
[![TypeScript](https://img.shields.io/badge/TypeScript-6.0-3178C6?logo=typescript)](https://typescriptlang.org)
[![Groq](https://img.shields.io/badge/LLM-Groq%20LLaMA%203.3-orange)](https://groq.com)

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

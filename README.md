# Lead Reactivation Autonomous AI Agent

## Google Antigravity Platform

> AI-powered autonomous lead reactivation system that analyzes dormant leads,
> generates personalized SMS messages using Gemini 3 Pro, and dispatches them via Twilio.

---

## Table of Contents

1. [System Architecture Overview](#1-system-architecture-overview)
2. [Agent Workflow Logic](#2-agent-workflow-logic)
3. [External API Interaction Flow](#3-external-api-interaction-flow)
4. [Lead Data Model Schema](#4-lead-data-model-schema)
5. [Dashboard Feature Breakdown](#5-dashboard-feature-breakdown)
6. [Project Structure](#6-project-structure)
7. [Getting Started](#7-getting-started)
8. [Configuration](#8-configuration)
9. [API Reference](#9-api-reference)
10. [Deployment](#10-deployment)

---

## 1. System Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                    GOOGLE ANTIGRAVITY PLATFORM                  │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐      │
│  │   Next.js    │    │   FastAPI     │    │   SQLite/    │      │
│  │   Frontend   │◄──►│   Backend     │◄──►│   PostgreSQL │      │
│  │   (React)    │    │   (Python)    │    │   Database   │      │
│  └──────────────┘    └──────┬───────┘    └──────────────┘      │
│                             │                                   │
│                    ┌────────┼────────┐                          │
│                    │        │        │                          │
│              ┌─────▼──┐ ┌──▼─────┐ ┌▼──────────┐              │
│              │ Gemini  │ │ Twilio │ │ Scheduler  │              │
│              │ 3 Pro   │ │ SMS    │ │ (APSchedul-│              │
│              │ (AI)    │ │ API    │ │  er)       │              │
│              └─────────┘ └────────┘ └────────────┘              │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Component Responsibilities

| Component | Technology | Responsibility |
|-----------|-----------|---------------|
| **Frontend** | Next.js 14 + MUI 5 | CSV upload, configuration, dashboard, audit log |
| **Backend API** | FastAPI (async) | REST API, orchestration, business logic |
| **AI Reasoning** | Google Gemini 3 Pro | Intent classification, message generation |
| **SMS Layer** | Twilio API | Outbound messaging, webhook handling |
| **Database** | SQLite (dev) / PostgreSQL (prod) | Lead storage, message audit trail |
| **Scheduler** | APScheduler | Timeout checks, deferred message dispatch |

---

## 2. Agent Workflow Logic

### Autonomous Processing Pipeline

```
                    ┌─────────────┐
                    │  CSV Upload  │
                    └──────┬──────┘
                           │
                    ┌──────▼──────┐
                    │  Validate   │  Schema check, phone
                    │  & Clean    │  normalization, date parsing
                    └──────┬──────┘
                           │
                    ┌──────▼──────┐
                    │  Ingest to  │  Create batch, persist
                    │  Database   │  leads as 'pending'
                    └──────┬──────┘
                           │
              ┌────────────▼────────────┐
              │  FOR EACH pending lead  │
              └────────────┬────────────┘
                           │
                    ┌──────▼──────┐
                    │  Gemini AI  │  Analyze context, classify
                    │  Analysis   │  intent, generate SMS
                    └──────┬──────┘
                           │
                    ┌──────▼──────┐
                    │  Intent     │  High / Medium / Low /
                    │  Decision   │  Not Interested
                    └──────┬──────┘
                           │
                ┌──────────┼──────────┐
                │                     │
         ┌──────▼──────┐    ┌────────▼───────┐
         │Not Interested│    │ Send SMS via   │
         │   → Skip     │    │ Twilio         │
         └──────────────┘    └────────┬───────┘
                                      │
                              ┌───────▼───────┐
                              │ State →       │
                              │ message_sent  │
                              └───────┬───────┘
                                      │
                    ┌─────────────────┼────────────────────┐
                    │                 │                     │
             ┌──────▼──────┐  ┌──────▼──────┐  ┌─────────▼──────┐
             │  Reply       │  │  Timeout    │  │  Opt-out       │
             │  received    │  │  expired    │  │  keyword       │
             │  → replied   │  │  → ignored  │  │  → opted_out   │
             └──────────────┘  └─────────────┘  └────────────────┘
```

### Lead State Machine

```
                    ┌─────────┐
                    │ pending │
                    └────┬────┘
                         │ [SMS sent]
                    ┌────▼────────┐
                    │message_sent │
                    └──┬────┬──┬──┘
          [reply]      │    │  │    [opt-out keyword]
         ┌─────────────┘    │  └──────────────┐
         │                  │                  │
    ┌────▼───┐    ┌────────▼──┐    ┌─────────▼────┐
    │replied │    │  ignored  │    │  opted_out   │
    └────────┘    └───────────┘    │  (terminal)  │
                  [timeout]        └──────────────┘
```

**Valid Transitions:**
- `pending` → `message_sent`
- `message_sent` → `replied` | `ignored` | `opted_out`
- `replied` → `message_sent` (follow-up)
- `ignored` → `message_sent` (retry)
- `opted_out` → *(terminal, no transitions)*

---

## 3. External API Interaction Flow

### Gemini 3 Pro — AI Reasoning

```
┌──────────┐         ┌──────────────┐
│  Backend  │         │  Gemini API  │
│           │ ──────► │              │
│  Prompt:  │         │  Analyzes:   │
│  - Name   │         │  - Context   │
│  - Phone  │         │  - History   │
│  - Date   │         │  - Tone pref │
│  - Source  │         │              │
│  - Notes  │ ◄────── │  Returns:    │
│           │         │  - Intent    │
│           │         │  - Rationale │
│           │         │  - SMS text  │
│           │         │  - Tone      │
└──────────┘         └──────────────┘
```

**Retry Policy:** Exponential backoff, 3 attempts max.

### Twilio — SMS Communication

```
┌──────────┐         ┌──────────┐         ┌──────────┐
│  Backend  │ ──────► │  Twilio  │ ──────► │  Lead's  │
│           │  send   │  API     │  SMS    │  Phone   │
│           │         │          │         │          │
│           │ ◄────── │          │ ◄────── │          │
│           │  SID    │          │  Reply  │          │
└─────┬────┘         └──────────┘         └──────────┘
      │                    │
      │         ┌──────────▼──────────┐
      │ ◄────── │  Webhook callbacks  │
      │         │  - Inbound SMS      │
      │         │  - Status updates   │
      │         └─────────────────────┘
```

**Business Hours Enforcement:** Messages are only dispatched Mon-Fri within configured hours (timezone-aware).

---

## 4. Lead Data Model Schema

### Lead Table

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| `id` | Integer (PK) | No | Auto-increment primary key |
| `lead_id` | String(64) | No | Business identifier (from CSV) |
| `full_name` | String(256) | No | Lead's full name |
| `phone_number` | String(32) | No | E.164 normalized phone |
| `email` | String(256) | Yes | Email address |
| `last_interaction_date` | DateTime | No | Last recorded interaction |
| `lead_source` | String(128) | No | Marketing channel/source |
| `notes` | Text | Yes | Historical interaction notes |
| `intent_category` | Enum | Yes | AI-classified intent |
| `intent_rationale` | Text | Yes | AI reasoning explanation |
| `recommended_angle` | Text | Yes | AI-generated SMS text |
| `sms_tone` | Enum | Yes | Selected message tone |
| `state` | Enum | No | Current lifecycle state |
| `batch_id` | String(64) | Yes | Processing batch reference |
| `created_at` | DateTime | No | Record creation timestamp |
| `updated_at` | DateTime | No | Last modification timestamp |

### Message Table

| Column | Type | Description |
|--------|------|-------------|
| `id` | Integer (PK) | Auto-increment |
| `lead_id` | String(64) (FK) | References leads.lead_id |
| `direction` | String(8) | "outbound" or "inbound" |
| `body` | Text | Message content |
| `twilio_sid` | String(64) | Twilio message SID |
| `twilio_status` | String(32) | Delivery status |
| `intent_score` | String(32) | Intent at time of send |
| `message_variant` | String(64) | A/B tracking variant |
| `sms_tone` | Enum | Tone used for this message |
| `sent_at` | DateTime | Outbound timestamp |
| `received_at` | DateTime | Inbound timestamp |

### Batch Table

| Column | Type | Description |
|--------|------|-------------|
| `id` | Integer (PK) | Auto-increment |
| `batch_id` | String(64) | Unique batch identifier |
| `filename` | String(512) | Original CSV filename |
| `total_leads` | Integer | Count of leads in batch |
| `processed_leads` | Integer | Count processed |
| `status` | String(32) | processing / completed / failed |
| `created_at` | DateTime | Batch creation time |
| `completed_at` | DateTime | Batch completion time |

---

## 5. Dashboard Feature Breakdown

### KPI Cards
- **Total Leads** — Count of all ingested leads
- **Messages Sent** — Total outbound SMS count
- **Replies** — Leads who responded (with reply rate %)
- **Ignored** — Leads past timeout threshold (with rate %)
- **Opted Out** — Leads who sent opt-out keywords
- **Avg Reply Time** — Mean time between send and reply

### Visualizations
- **Daily Messages Chart** — Line chart of outbound volume over 30 days
- **State Distribution** — Donut chart of lead lifecycle states
- **Intent Performance** — Grouped bar chart comparing total vs. replies per intent
- **Source Distribution** — Horizontal bar chart of leads per source

### Lead Audit Log
- Paginated, searchable table of all leads
- Filter by: state, intent, source, date range
- Click-through to detail view with:
  - Lead metadata
  - AI rationale & recommended SMS
  - Full message history (inbound + outbound)
- CSV export with current filters

### Configuration Panel
- Business hours (start, end, timezone)
- Default SMS tone preference
- Ignore timeout threshold
- Max retry count
- API credentials managed via environment (security)

---

## 6. Project Structure

```
lead-reactivation-agent/
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py              # FastAPI app entry point
│   │   ├── config.py            # Settings from .env
│   │   ├── database.py          # SQLAlchemy async engine
│   │   ├── logging_config.py    # Structured logging
│   │   ├── models/
│   │   │   ├── __init__.py
│   │   │   ├── lead.py          # ORM models (Lead, Message, Batch)
│   │   │   └── schemas.py       # Pydantic request/response schemas
│   │   ├── routers/
│   │   │   ├── __init__.py
│   │   │   ├── leads.py         # Lead CRUD + upload + process
│   │   │   ├── webhooks.py      # Twilio inbound/status callbacks
│   │   │   ├── dashboard.py     # Analytics endpoints
│   │   │   └── config.py        # Configuration management
│   │   └── services/
│   │       ├── __init__.py
│   │       ├── ingestion.py     # CSV validation & data pipeline
│   │       ├── ai_reasoning.py  # Gemini integration
│   │       ├── twilio_sms.py    # Twilio send/receive
│   │       ├── state_machine.py # Lead state transitions + orchestrator
│   │       └── analytics.py     # Dashboard aggregation queries
│   ├── data/                    # SQLite database (dev)
│   ├── requirements.txt
│   └── .env.example
├── frontend/
│   ├── src/
│   │   ├── app/
│   │   │   ├── layout.tsx       # Root layout
│   │   │   └── page.tsx         # Home page
│   │   ├── components/
│   │   │   ├── DashboardShell.tsx   # Navigation shell
│   │   │   └── views/
│   │   │       ├── DashboardView.tsx  # KPIs + charts
│   │   │       ├── UploadView.tsx     # CSV drag-and-drop
│   │   │       ├── LeadsView.tsx      # Audit log table
│   │   │       └── ConfigView.tsx     # Settings panel
│   │   └── lib/
│   │       ├── api.ts           # Axios API client
│   │       └── theme.ts         # MUI dark theme
│   ├── package.json
│   ├── tsconfig.json
│   └── next.config.js
├── sample_leads.csv             # Sample data for testing
├── Dockerfile                   # Multi-stage Docker build
├── docker-compose.yml           # Full-stack orchestration
└── README.md                    # This file
```

---

## 7. Getting Started

### Prerequisites

- Python 3.11+
- Node.js 18+
- Twilio account (SID, Auth Token, Phone Number)
- Google Cloud project with Gemini API access

### Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate   # Windows

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your API keys

# Create data directory
mkdir -p data

# Start the server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Start development server
npm run dev
```

The frontend will be available at `http://localhost:3000` and will proxy API requests to the backend at `http://localhost:8000`.

---

## 8. Configuration

### Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `GEMINI_API_KEY` | Yes | Google Gemini API key |
| `GEMINI_MODEL` | No | Model name (default: `gemini-3-pro`) |
| `TWILIO_ACCOUNT_SID` | Yes | Twilio Account SID |
| `TWILIO_AUTH_TOKEN` | Yes | Twilio Auth Token |
| `TWILIO_PHONE_NUMBER` | Yes | Twilio sending number (E.164) |
| `DATABASE_URL` | No | Database connection string |
| `BUSINESS_HOURS_START` | No | Start time (default: `09:00`) |
| `BUSINESS_HOURS_END` | No | End time (default: `17:00`) |
| `BUSINESS_HOURS_TIMEZONE` | No | IANA timezone (default: `America/New_York`) |
| `DEFAULT_SMS_TONE` | No | Default tone (default: `professional`) |
| `IGNORE_TIMEOUT_HOURS` | No | Hours before marking ignored (default: `48`) |

---

## 9. API Reference

### Leads

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/v1/leads/upload` | Upload CSV file |
| `POST` | `/api/v1/leads/process/{batch_id}` | Start autonomous processing |
| `GET` | `/api/v1/leads/` | List leads (paginated, filterable) |
| `GET` | `/api/v1/leads/{lead_id}` | Get single lead |
| `GET` | `/api/v1/leads/{lead_id}/messages` | Get lead message history |
| `GET` | `/api/v1/leads/batches/list` | List all batches |
| `GET` | `/api/v1/leads/export/csv` | Export leads as CSV |

### Dashboard

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/v1/dashboard/` | Full dashboard data |
| `GET` | `/api/v1/dashboard/kpis` | KPIs only |

### Webhooks

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/v1/webhooks/twilio/inbound` | Inbound SMS handler |
| `POST` | `/api/v1/webhooks/twilio/status` | Message status callback |

### Configuration

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/v1/config/` | Get current config |
| `PUT` | `/api/v1/config/` | Update config |

### Health

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/health` | Service health check |

---

## 10. Deployment

### Docker Compose (Recommended)

```bash
docker-compose up --build
```

This starts:
- **Backend** on port 8000
- **Frontend** on port 3000

### Google Antigravity Deployment

The application is designed for deployment on the Google Antigravity platform:

1. Configure environment variables in the platform's secrets manager
2. Set the Twilio webhook URL to `https://your-domain/api/v1/webhooks/twilio/inbound`
3. Deploy using the provided Dockerfile or docker-compose.yml
4. The system is fully autonomous post-deployment — upload a CSV and processing begins

### Extensibility

The modular architecture supports future channel integrations:
- **Email:** Add a service module in `services/email_sender.py`
- **WhatsApp:** Extend the Twilio module with WhatsApp Business API
- **Slack/Teams:** Add notification webhooks for internal alerts

---

## License

Proprietary — Google Antigravity Platform

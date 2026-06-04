# Patient Financial Advocate — Setup Guide

> **What this is:** A step-by-step guide for everything YOU need to do on your end to get the Patient Financial Advocate module running in CureQuest. This covers MongoDB, Arize Phoenix, dependencies, and deployment.

---

## Table of Contents

1. [Prerequisites](#1-prerequisites)
2. [MongoDB Setup](#2-mongodb-setup)
3. [Arize Phoenix Setup](#3-arize-phoenix-setup)
4. [Python Dependencies](#4-python-dependencies)
5. [Frontend Dependencies](#5-frontend-dependencies)
6. [Environment Variables](#6-environment-variables)
7. [Database Initialization](#7-database-initialization)
8. [Local Development (Docker Compose)](#8-local-development-docker-compose)
9. [Cloud Deployment](#9-cloud-deployment)
10. [Verification Checklist](#10-verification-checklist)
11. [Reference Repos](#11-reference-repos)

---

## 1. Prerequisites

- [ ] Python 3.13+ installed
- [ ] Node.js 20+ and npm installed
- [ ] Docker and Docker Compose installed (for local dev)
- [ ] Google Cloud SDK (`gcloud`) installed and authenticated
- [ ] Git installed
- [ ] Access to your GCP project: `mystical-app-490317-v0`

---

## 2. MongoDB Setup

### Option A: Local MongoDB (for development)

```bash
# Start via Docker Compose (see Section 8)
docker compose up mongodb -d
```

MongoDB will be available at `mongodb://localhost:27017/curequest_finance`

### Option B: MongoDB Atlas (for production)

1. **Go to** [MongoDB Atlas](https://cloud.mongodb.com/)
2. **Create a free cluster** (or use an existing one)
3. **Create a database user:**
   - Username: `curequest_admin`
   - Password: Generate a strong password
   - Roles: `readWrite` on `curequest_finance`
4. **Whitelist your IP** (or allow `0.0.0.0/0` for Cloud Run)
5. **Get your connection string:**
   ```
   mongodb+srv://curequest_admin:<password>@<cluster>.mongodb.net/curequest_finance?retryWrites=true&w=majority
   ```
6. **Create the following collections manually** (or let the init script do it):
   - `bills`
   - `bill_audits`
   - `loan_offers`
   - `patient_gaps`
   - `policy_chunks`
   - `consent_logs`

### Required Indexes (create in Atlas UI or via script)

```javascript
// bill_audits
db.bill_audits.createIndex({ patient_id: 1, audit_timestamp: -1 });

// loan_offers
db.loan_offers.createIndex({ patient_id: 1 });

// policy_chunks
db.policy_chunks.createIndex({ source_doc_id: 1 });
db.policy_chunks.createIndex({ text: "text" }); // full-text search

// consent_logs
db.consent_logs.createIndex({ patient_id: 1, created_at: -1 });
```

---

## 3. Arize Phoenix Setup

### Option A: Self-hosted (recommended for dev)

```bash
# Via Docker Compose (see Section 8)
docker compose up arize-phoenix -d
```

Dashboard available at `http://localhost:6006`

### Option B: Standalone Docker

```bash
docker run -d --name phoenix \
  -p 6006:6006 \
  -v phoenix_data:/data \
  arizephoenix/phoenix:latest
```

### Option C: Arize Cloud (for production)

1. **Sign up at** [Arize AI](https://app.arize.com/)
2. **Create a space** for CureQuest
3. **Get your API key** from Settings → API Keys
4. **Set env vars:**
   ```
   ARIZE_API_KEY=your-api-key
   ARIZE_SPACE_KEY=your-space-key
   ```

### What Arize Phoenix Traces

Once integrated, you'll see traces for:
- ADK orchestrator workflow (full parent span)
- Bill parsing and audit operations
- Loan ranking decisions with feature importance
- PHI redaction events (entity counts, not the actual PHI)
- LLM calls: input/output, latency, token counts
- Agent routing decisions

---

## 4. Python Dependencies

Add these to `pyproject.toml` under `[project] dependencies`:

```toml
# MongoDB
"motor>=3.6",              # Async MongoDB driver
"pymongo>=4.9",            # Sync MongoDB driver (for scripts)

# Arize Phoenix (LLM Observability)
"arize-phoenix>=5.0",      # Arize Phoenix client
"opentelemetry-api>=1.28", # OpenTelemetry for tracing
"opentelemetry-sdk>=1.28",

# PHI De-identification
"presidio-analyzer>=2.2",  # Microsoft Presidio analyzer
"presidio-anonymizer>=2.2",# Microsoft Presidio anonymizer
"spacy>=3.7",              # NLP backend for Presidio

# PDF Extraction
"opendataloader-pdf>=0.1", # Structured PDF extraction with bboxes
```

### Install commands

```bash
cd Cure-Quest

# Install the updated project with new deps
pip install -e ".[dev]"

# Download spaCy English model for Presidio
python -m spacy download en_core_web_lg
```

---

## 5. Frontend Dependencies

```bash
cd Cure-Quest/frontend

# PDF viewer with annotations
npm install react-pdf-highlighter-extended

# Already installed (verify these exist):
# react, react-dom, motion, lucide-react, tailwindcss
```

### Add to App.tsx

You'll need to add a new route for the Financial Advocate screen:

```tsx
// In App.tsx, add to the page list and navigation:
// import FinancialAdvocateScreen from './patient/screens/FinancialAdvocateScreen'
// Add nav item with icon: Banknote from lucide-react
// Add case in the page renderer switch
```

---

## 6. Environment Variables

Copy `.env.example` to `.env` and fill in the **new** fields:

```bash
cd Cure-Quest
cp .env.example .env
```

### New variables you MUST set:

| Variable | Description | Example |
|----------|-------------|---------|
| `MONGODB_URI` | MongoDB connection string | `mongodb://localhost:27017/curequest_finance` |
| `MONGODB_DATABASE` | Database name | `curequest_finance` |
| `ARIZE_PHOENIX_URL` | Phoenix dashboard URL | `http://localhost:6006` |
| `ARIZE_PHOENIX_PROJECT` | Project name for traces | `curequest-patient-finance` |

### For production (Cloud Run), also set:

| Variable | Description |
|----------|-------------|
| `ARIZE_API_KEY` | Arize Cloud API key (if using cloud) |
| `ARIZE_SPACE_KEY` | Arize Cloud space key |
| `MONGODB_URI` | MongoDB Atlas connection string |

---

## 7. Database Initialization

### MongoDB (run after first setup)

```bash
# If using local Docker MongoDB:
docker exec -it curequest-mongodb mongosh < mongo-init/init-finance-collections.js

# If using Atlas, run the script via mongosh:
mongosh "mongodb+srv://<cluster>.mongodb.net/curequest_finance" \
  --username curequest_admin \
  < mongo-init/init-finance-collections.js
```

### PostgreSQL (existing — no changes needed)

The existing SQLAlchemy models and PostgreSQL database remain unchanged.
Patient finance data lives in MongoDB; the two databases run side-by-side.

---

## 8. Local Development (Docker Compose)

```bash
cd Cure-Quest

# Start everything
docker compose up -d

# This starts:
# - cure-quest-api    → http://localhost:8000
# - cure-quest-web    → http://localhost:3000
# - mongodb           → localhost:27017
# - arize-phoenix     → http://localhost:6006
```

### Without Docker (manual)

```bash
# Terminal 1: MongoDB
docker run -d -p 27017:27017 --name cq-mongo mongo:7

# Terminal 2: Arize Phoenix
docker run -d -p 6006:6006 --name cq-phoenix arizephoenix/phoenix:latest

# Terminal 3: Backend
cd Cure-Quest
pip install -e ".[dev]"
uvicorn nexus_ai.app:app --reload --port 8000

# Terminal 4: Frontend
cd Cure-Quest/frontend
npm install
npm run dev
```

---

## 9. Cloud Deployment

### Update Cloud Build for MongoDB and Phoenix

#### Backend (`cloudbuild.yaml`)

Add these env vars to the `--set-env-vars` step:

```yaml
- --set-env-vars
- APP_ENV=production,APP_HOST=0.0.0.0,MONGODB_URI=mongodb+srv://...,ARIZE_PHOENIX_URL=https://your-phoenix.run.app
```

#### MongoDB in Production

**Option A: MongoDB Atlas** (recommended)
- Use Atlas managed service. Set `MONGODB_URI` to your Atlas connection string.

**Option B: Self-hosted on GCE**
- Create a Compute Engine VM with MongoDB
- Use persistent disk for data
- Set up network peering with Cloud Run

#### Arize Phoenix in Production

**Option A: Arize Cloud** (recommended)
- Use Arize's managed cloud. Set `ARIZE_API_KEY` and `ARIZE_SPACE_KEY`.

**Option B: Self-hosted on Cloud Run**
```bash
gcloud run deploy arize-phoenix \
  --image arizephoenix/phoenix:latest \
  --port 6006 \
  --region us-central1 \
  --allow-unauthenticated
```

---

## 10. Verification Checklist

After setup, verify everything works:

- [ ] **MongoDB connection:** `mongosh $MONGODB_URI --eval "db.stats()"`
- [ ] **Arize Phoenix:** Open `$ARIZE_PHOENIX_URL` in browser — should show dashboard
- [ ] **Backend starts:** `uvicorn nexus_ai.app:app --reload` — no import errors
- [ ] **Frontend starts:** `npm run dev` — no compilation errors
- [ ] **API health:** `curl http://localhost:8000/api/finance/workflow-status/test` — should return SSE stream or 404 (not 500)
- [ ] **Presidio works:** `python -c "from presidio_analyzer import AnalyzerEngine; print('OK')"`
- [ ] **spaCy model:** `python -c "import spacy; spacy.load('en_core_web_lg'); print('OK')"`

---

## 11. Reference Repos

These have been cloned into `google_cloud_agent/` for your reference:

| Repo | Location | Purpose |
|------|----------|---------|
| `react-pdf-highlighter-extended` | `google_cloud_agent/ref--react-pdf-highlighter-extended/` | PDF viewer with annotation overlays — used for bill/policy citation highlights in frontend |
| `microsoft/presidio` | `google_cloud_agent/ref--presidio/` | PHI de-identification — used in `privacy.py` to scrub patient data before LLM calls |
| `opendataloader-pdf` | `google_cloud_agent/ref--opendataloader-pdf/` | Structured PDF extraction with bboxes — used for bill and policy PDF parsing |

### How to explore them

```bash
# PDF Highlighter — check the example app for usage patterns
cat google_cloud_agent/ref--react-pdf-highlighter-extended/README.md

# Presidio — check the samples directory
ls google_cloud_agent/ref--presidio/presidio-analyzer/presidio_analyzer/

# OpenDataLoader — check conversion API
cat google_cloud_agent/ref--opendataloader-pdf/README.md
```

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                    CureQuest Frontend                        │
│  ┌───────────────┐  ┌────────────┐  ┌────────────────────┐ │
│  │ Financial      │  │ Bill       │  │ Policy Citation    │ │
│  │ Advocate Screen│  │ Viewer     │  │ Panel              │ │
│  │               │  │ (pdf-hl-ext)│  │                    │ │
│  └───────┬───────┘  └────────────┘  └────────────────────┘ │
└──────────┼──────────────────────────────────────────────────┘
           │ REST API + SSE
┌──────────▼──────────────────────────────────────────────────┐
│                    FastAPI Backend                           │
│  ┌─────────────────────────────────────────────────────────┐│
│  │ patient_finance/api_routes.py                           ││
│  │ /upload-bill, /audit, /gap, /loans, /consent, /submit   ││
│  └──────────┬──────────────────────────────────────────────┘│
│  ┌──────────▼──────────────────────────────────────────────┐│
│  │ patient_finance/orchestrator.py (ADK Multi-Agent)       ││
│  │ ┌──────────┐ ┌────────┐ ┌────────────┐ ┌──────────┐   ││
│  │ │ Billing  │ │ Gap    │ │ Loan Broker│ │ Consent  │   ││
│  │ │ Agent    │ │ Agent  │ │ Agent      │ │ Gate     │   ││
│  │ └────┬─────┘ └───┬────┘ └─────┬──────┘ └─────┬────┘   ││
│  └──────┼───────────┼────────────┼───────────────┼────────┘│
│  ┌──────▼───────────▼────────────▼───────────────▼────────┐│
│  │ Deterministic Python Modules                            ││
│  │ billing.py | gap.py | loan.py | policy.py | privacy.py  ││
│  └─────────────────────┬───────────────────────────────────┘│
└────────────────────────┼────────────────────────────────────┘
           ┌─────────────┼─────────────┐
     ┌─────▼─────┐  ┌───▼────┐  ┌─────▼──────┐
     │ MongoDB   │  │ Arize  │  │ PostgreSQL │
     │ (finance) │  │ Phoenix│  │ (existing) │
     │           │  │(traces)│  │            │
     └───────────┘  └────────┘  └────────────┘
```

---

## File Map — What's New

```
Cure-Quest/
├── src/nexus_ai/patient_finance/     ← NEW MODULE
│   ├── __init__.py                   ← Package init
│   ├── models.py                     ← MongoDB document schemas (Pydantic)
│   ├── state.py                      ← ADK session state manager
│   ├── billing.py                    ← Bill parsing + audit (deterministic)
│   ├── gap.py                        ← Gap calculator (pure function)
│   ├── loan.py                       ← Loan discovery + ranking
│   ├── policy.py                     ← Policy ingestion + citations
│   ├── privacy.py                    ← PHI redaction (Presidio)
│   ├── orchestrator.py               ← ADK multi-agent workflow
│   ├── tools.py                      ← ADK tool definitions
│   ├── mongodb.py                    ← MongoDB connection manager
│   ├── arize_tracing.py              ← Arize Phoenix instrumentation
│   └── api_routes.py                 ← FastAPI router
│
├── frontend/src/patient/
│   ├── screens/
│   │   └── FinancialAdvocateScreen.tsx ← NEW SCREEN
│   ├── components/
│   │   ├── BillViewer.tsx             ← NEW (pdf-highlighter-extended)
│   │   ├── LoanComparison.tsx         ← NEW
│   │   ├── ConsentGate.tsx            ← NEW
│   │   ├── GapSummary.tsx             ← NEW
│   │   └── PolicyCitationPanel.tsx    ← NEW
│   └── hooks/
│       └── useFinancialWorkflow.ts    ← NEW
│
├── docker-compose.yml                 ← NEW (MongoDB + Phoenix + app)
├── mongo-init/
│   └── init-finance-collections.js    ← NEW
├── tests/fixtures/
│   ├── bills/sample_itemized_bill.json     ← NEW
│   ├── loans/sample_loan_offers.json       ← NEW
│   └── policies/sample_policy_chunks.json  ← NEW
│
├── .env.example                       ← UPDATED (MongoDB + Arize vars)
└── pyproject.toml                     ← NEEDS UPDATE (new deps)
```

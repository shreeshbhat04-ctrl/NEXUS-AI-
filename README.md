# Nexus AI

**An AI-powered multi-agent healthcare platform** that provides personalized chronic care management through intelligent conversational AI, real-time medication safety analysis, and transparent human-in-the-loop doctor handoffs.





## Table of Contents
- [Project Overview](#project-overview)
- [Demo Media](#demo-media)
- [Quick Start](#quick-start)
- [Tech Stack](#tech-stack)
- [Architecture](#architecture)
- [Directory Structure](#directory-structure)
- [Component Index](#component-index)
- [API Contracts](#api-contracts)
- [Data Flow & State Management](#data-flow--state-management)
- [AI/ML Section](#aiml-section)
- [Results and Metrics](docs/results_and_metrics.md)
- [Datasets Used](Datasets/)
- [Appendix](#appendix)

---

## Project Overview
Nexus AI coordinates care across multiple dimensions:
- **Voice/Chat AI** for patient questions and follow-up guidance.
- **Document upload** for prescription scans and medical artifacts.
- **HITL review** to produce doctor-ready summaries.
- **Medication reminders** and care notifications.
- **Recipe Studio** for condition-aware culinary guidance (curated from PostgreSQL).
- **HealthConnect Integration** for real-time vitals and watch-based monitoring.
- **Google Workspace integration** for Drive, Calendar, Gmail, Speech, and Maps.

### Demo Story — Shreesha's Care Journey
Shreesha is a 22-year-old patient managing two chronic conditions simultaneously:
- **Atopic Eczema** (moderate to severe) — recurring flares on forearms and neck, managed with topical Clobetasol Propionate.
- **Focal Epilepsy** — diagnosed at age 19, currently controlled with Levetiracetam 500 mg twice daily.

The demo walks through drug interaction questions, document uploads, doctor handoff reports, medication reminders, and Gmail-based care summaries.

---

## Demo Media

### This is an agentic workflow in ADK environment
![ADK demo video](assets/Working_adk_demo.gif)

### Detailed Agentic Breakdown Diagrams
For detailed diagrams of the agentic breakdown, refer here:
[Agent Diagrams](docs/Agent_Digrams)

---

## Key Features

### Recipe Studio (Browse Recipes)
The **Recipe Studio** provides personalized nutritional guidance by fetching curated recipes from **PostgreSQL** that are safe and beneficial for the patient's specific chronic conditions (e.g., eczema-friendly ingredients).
- **Curated Selection**: Pre-validated recipes for common care journeys.
- **AI-Generated**: Real-time generation of custom recipes based on available ingredients and dietary restrictions.
- **Marketplace Sync**: Direct link to ingredient marketplaces for seamless shopping.

### HealthConnect & Watch Integration
Nexus AI syncs with **Android HealthConnect** to monitor real-time patient vitals (heart rate, sleep, activity) via wearable devices.
- **Patient Brain Sync**: Watch data is periodically pushed to the PostgreSQL "Patient Brain" to ground the AI's conversational context.
- **Proactive Alerts**: If abnormal vitals are detected, the system can trigger a proactive check-in or escalate to the Doctor Workspace via Task Queue.

---

## Quick Start

### Prerequisites
- Python 3.13+
- Node.js 20+
- MongoDB instance (local or Atlas)
- Arize Phoenix (local or cloud)
- Google Cloud project with APIs enabled (Drive, Calendar, Gmail, Speech, Maps)
- PostgreSQL/PostgreSQL instance (or use SQLite for local dev)

### 1) Backend Setup
```powershell
# Create virtual environment
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -e .[dev]

# Download spaCy English model for Presidio PHI scrubbing
python -m spacy download en_core_web_lg

# Configure environment
copy .env.example .env
# Edit .env with your keys (including MONGODB_URI and ARIZE_PHOENIX_URL)

# Seed demo data
python -m nexus_ai.scripts.seed

# Run API
uvicorn nexus_ai.app:app --reload
```

### 2) Frontend Setup
```powershell
cd frontend
npm install
npm run dev
```

---

## Tech Stack

### Core
- **Backend**: FastAPI, SQLAlchemy, Pydantic.
- **Database**: 
  - **PostgreSQL** (PostgreSQL-compatible) for patient profile, vitals, conditions, and core relational records.
  - **MongoDB** for billing documents, audits, coverage gaps, policy text chunks, and loan offers (with GridFS for PDF storage).
- **Frontend**: React, Vite, TypeScript, Framer Motion, GSAP, and `react-pdf-highlighter-extended` for bill annotation.
- **State Management**: Zustand.

### AI & Agents
- **Gemini 3.1 Flash**: Clinical reasoning, conversational engine, multimodal vision classification, and billing audit/explanation.
- **Google ADK**: Multi-agent orchestration framework (orchestrates Billing Agent, Gap Agent, Loan Broker Agent, and Consent Gate).
- **MCP (Model Context Protocol)**: Standardized tool and data access.
- **Observability**: **Arize Phoenix** for OpenTelemetry LLM tracing and agent routing visualization.
- **Privacy**: **Microsoft Presidio** for local PHI (Protected Health Information) de-identification and scrubbing.

---

## Why this stack?

```mermaid
graph LR

%% Row 1
A1["React + Vite"] --> B1["Fast interactive SPA + rapid iteration"]
B1 --> C1["Responsive learning UX"]

%% Row 2
A2["Zustand persist"] --> B2["Simple global state + local persistence"]
B2 --> C2["Cross-page continuity"]

%% Row 3
A3["FastAPI + Pydantic"] --> B3["Typed contracts + auto docs"]
B3 --> C3["Faster API iteration"]

%% Row 4
A4["Gemini 3.1 Flash + PostgreSQL"] --> B4["LLM grounding with patient memory"]
B4 --> C4["Clinical context-aware responses"]

%% Row 5
A5["Google ADK"] --> B5["Multi-agent A2A orchestration"]
B5 --> C5["Specialist task delegation"]

%% Row 6
A6["Gemini Multimodal"] --> B6["Vision-based medical image classification"]
B6 --> C6["Prescription and symptom analysis"]

%% Row 7
A7["MCP (Model Context Protocol)"] --> B7["Standardised tool and data access"]
B7 --> C7["Safe agent-to-service boundaries"]

%% Row 8
A8["PostgreSQL + pgvector"] --> B8["Relational + vector patient brain"]
B8 --> C8["Unified memory and semantic search"]

%% Row 9
A9["Cloud Run"] --> B9["Stateless containerised deployment"]
B9 --> C9["Scalable serverless backend"]

%% Row 10
A10["MongoDB + GridFS"] --> B10["Flexible bill/audit storage + PDF archiving"]
B10 --> C10["Durable financial advocates"]

%% Row 11
A11["Arize Phoenix"] --> B11["OpenTelemetry LLM observability & tracing"]
B11 --> C11["Traceable clinical decisions"]

%% Row 12
A12["Microsoft Presidio"] --> B12["Local PHI scrubbing & de-identification"]
B12 --> C12["Strict compliance boundaries"]

%% Styling
classDef tech fill:#1a73e8,color:#fff,stroke:#0b57d0;
classDef capability fill:#f9ab00,color:#1a1a1a,stroke:#c88700;
classDef outcome fill:#0f9d58,color:#fff,stroke:#0b7d43;

class A1,A2,A3,A4,A5,A6,A7,A8,A9,A10,A11,A12 tech;
class B1,B2,B3,B4,B5,B6,B7,B8,B9,B10,B11,B12 capability;
class C1,C2,C3,C4,C5,C6,C7,C8,C9,C10,C11,C12 outcome;
```

---

## Architecture

### High-Level Design
Nexus AI uses a multi-agent approach where a **Root Agent** (ADK) orchestrates specialized sub-agents.

```mermaid
graph TD
    UI[React Frontend] --> API[FastAPI Backend]
    API --> ORCH[Multi-Agent Orchestrator]
    ORCH --> GEN[Gemini 3.1 Flash]
    ORCH --> MCP[MCP Server]
    MCP --> DB[(PostgreSQL Patient Brain)]
    ORCH --> AGENTS[ADK Sub-Agents: Vision, Recipe, Map, etc.]
    
    %% Patient Finance
    API --> FIN_ORCH[Patient Finance Orchestrator]
    FIN_ORCH --> MDB[(MongoDB Finance Store)]
    FIN_ORCH --> PHOENIX[Arize Phoenix Tracing]
    FIN_ORCH --> DB
```

For detailed sequence diagrams, see [Architecture and Design](docs/ARCHITECTURE_AND_DESIGN.md).

---

## Application Role Flows

```mermaid
flowchart LR

%% ================= ENTRY =================
LP["Landing Page"]

APP["/app"]
DASH["/dashboard"]
CARE["/caremaze"]
MEDS["/meds"]
DOC["/doctor"]
HIST["/history"]

LP --> APP
LP --> DASH
LP --> CARE
LP --> MEDS
LP --> DOC
LP --> HIST

%% ================= PATIENT JOURNEY =================
subgraph PJ[Patient Journey]

DASH --> PROF["Profile (Vitals / Conditions / Prescriptions)"]
DASH --> H1["History"]
H1 --> SNAP["Condition Snapshots (Accordion)"]
SNAP --> QRY["Agent History Query"]

CARE --> MAPA["Map Agent"]
MAPA --> MAPS["Nearby Pharmacy / Clinic / Hospital"]

CARE --> UP["Upload Image"]
UP --> VA["Vision Agent"]
VA -->|classify| FOLLOW["Follow-up / Doctor Handoff / Chat"]

MEDS --> SAFE["Drug Safety Check"]
SAFE --> GEM1["Gemini + PostgreSQL"]

MEDS --> RS["Recipe Studio"]
RS --> CUR["Curated Recipes"]
RS --> GEN["Generated Recipes"]
GEN --> MKT["Ingredient Marketplace"]

MEDS --> DOCUP["Document Upload"]
DOCUP --> PRES["Prescription Scan"]
PRES --> EXT["Extracted Medication Context"]

end

%% ================= CONVERSATIONAL AI =================
subgraph CAI[Conversational AI Journey]

APP --> CHAT["Chat Assistant"]
CHAT --> INPUT["Text / Voice Input"]
INPUT --> ORCH["Orchestrator"]
ORCH --> GEM2["Gemini 3.1 Flash"]

CHAT --> ACTION["Structured Action Draft"]
ACTION -->|confirm| CONFIRM["Action Confirm"]
CONFIRM --> EXEC["Execute"]

EXEC --> ASANA["Task Queue"]
EXEC --> GMAIL["Gmail"]
EXEC --> CAL["Google Calendar"]

APP --> VOICE["Voice Assistant"]
VOICE --> STT["Speech-to-Text"]
STT --> ORCH
ORCH --> TTS["Text-to-Speech"]
TTS --> AUDIO["Audio Response"]

end

%% ================= DOCTOR WORKSPACE =================
subgraph DW[Doctor Workspace Journey]

DOC --> QUEUE["Live Task Queue Task Queue"]
QUEUE -->|filter| TASKS["Tasks by Doctor GID"]

DOC --> OPEN["Open Task"]
OPEN --> ASANA2["Task Queue Permalink"]

DOC --> RECORDS["Patient Records"]
RECORDS --> PROF2["Profile + Snapshots"]

DOC --> CHATDOC["Doctor-Patient Chat"]
CHATDOC -->|poll| THREADS["Chat Threads"]

end

%% ================= STYLING =================
classDef route fill:#1a73e8,color:#fff,stroke:#0b57d0;
classDef patient fill:#0f9d58,color:#fff,stroke:#0b7d43;
classDef cai fill:#6a1b9a,color:#fff,stroke:#4a148c;
classDef doctor fill:#f9ab00,color:#1a1a1a,stroke:#c88700;
classDef external fill:#e64a19,color:#fff,stroke:#bf360c;
classDef agent fill:#3949ab,color:#fff,stroke:#1a237e;

%% Apply classes
class LP,APP,DASH,CARE,MEDS,DOC,HIST route;

class PROF,H1,SNAP,QRY,MAPS,FOLLOW,SAFE,RS,CUR,GEN,MKT,DOCUP,PRES,EXT patient;

class CHAT,INPUT,ACTION,CONFIRM,EXEC,VOICE,STT,TTS,AUDIO cai;

class QUEUE,TASKS,OPEN,RECORDS,PROF2,CHATDOC,THREADS doctor;

class ASANA,GMAIL,CAL,ASANA2 external;

class ORCH,VA,MAPA,GEM1,GEM2 agent;
```

---

## Directory Structure
```text
nexus_ai/
├── adk_agents/          # ADK agent packages
├── docs/                # Architecture and design plans
├── frontend/
│   ├── src/
│   │   ├── components/  # Chat, Voice, UI components
│   │   ├── hooks/       # Custom React hooks
│   │   ├── lib/         # API and data utilities
│   │   ├── screens/     # Route pages (Dashboard, CareMaze, etc.)
│   │   ├── patient/     # Patient portal modules (components, hooks, screens)
│   │   └── assets/      # Static assets
│   ├── package.json
│   └── vite.config.ts
├── src/
│   └── nexus_ai/
│       ├── adapters/    # External service connectors (Task Queue, Gmail, etc.)
│       ├── adk/         # ADK agent logic
│       ├── agents/      # Specialist Python agents
│       ├── api/         # FastAPI routes and models
│       ├── db/          # Database models and bootstrap
│       ├── mcp/         # Model Context Protocol server
│       ├── patient_finance/ # Patient Financial Advocate module (billing, gap, loans, privacy, mongodb)
│       ├── scripts/     # Utility scripts (seed, test)
│       ├── services/    # Business logic and model routing
│       └── app.py       # Main entry point
└── pyproject.toml
```

---

## Component Index

### Index Method
Each module is indexed with its purpose, inputs, and complexity. Where exact internals cannot be fully inferred without runtime interaction, entries are marked `manual-review`.

### Pattern-based Detail Map
| Pattern | Purpose | Inputs / Props | State / Lifecycle | Tests | Complexity |
| --- | --- | --- | --- | --- | --- |
| `frontend/src/screens/*` | Route-level composition | Router params + workspace context | React hooks lifecycle | Manual review | Render-bound |
| `frontend/src/components/*` | Shared UI blocks | Component props | React state/effects | Manual review | UI logic |
| `src/nexus_ai/api/*` | FastAPI routes | Pydantic request models | Per-request | `test_api_models.py` | Orchestration |
| `src/nexus_ai/agents/*` | Agent reasoning | Prompt context + tool definitions | Stateless | Unit tests exist | Reasoning O(token) |
| `src/nexus_ai/adapters/*` | Service mediation | Adapter method signatures | Managed sessions | Integration tests | Request-bound |

### Detailed Module Register
| Path | Purpose | Inputs/Props | Internal state/lifecycle | Key methods/exports | External dependencies | Tests | Complexity |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `frontend/src/screens/DashboardScreen.tsx` | Patient home view | Workspace context | Polling/refresh effects | Default component | Framer Motion, GSAP | Manual review | Render-bound |
| `frontend/src/screens/CareMazeScreen.tsx` | Symptom & Map view | Location context | Geolocation effects | Default component | Google Maps, Lucide | Manual review | UI logic |
| `frontend/src/screens/MedicationHubScreen.tsx` | Prescription manager | Patient id | Upload/Delete state | Default component | Axios, Framer Motion | Manual review | List-bound |
| `frontend/src/screens/DoctorWorkspaceScreen.tsx` | Clinician portal | Doctor context | Task queue state | Default component | Task Queue Adapter | Manual review | O(n) tasks |
| `frontend/src/screens/HistoryScreen.tsx` | Care timeline | Patient history | Grouping/Sorting logic | Default component | Date-fns | Manual review | O(n) events |
| `frontend/src/screens/HITLScreen.tsx` | Doctor review flow | Case id | Review submission state | Default component | Backend HITL API | Manual review | Form-bound |
| `frontend/src/screens/Profile.tsx` | User settings | User session | Edit/Save lifecycle | Default component | Zustand Store | Manual review | Form-bound |
| `frontend/src/components/ChatAssistant.tsx` | Conversational interface | Session id | Message history state | `ChatAssistant` | Backend Chat API | Manual review | O(history) |
| `frontend/src/components/VoiceAssistant.tsx` | Audio interaction | Audio stream | Recording/Speech state | `VoiceAssistant` | Google STT/TTS | Manual review | Async-bound |
| `frontend/src/components/DoctorCard.tsx` | Clinician profile UI | `Doctor` object | Hover/Expand state | `DoctorCard` | Tailwind CSS | Manual review | Render-bound |
| `frontend/src/hooks/useWorkspace.ts` | State provider | Config object | Global state sync | `useWorkspace` | Zustand | Manual review | O(1) access |
| `frontend/src/lib/api.ts` | API transport layer | Request config | Interceptor lifecycle | `api` instance | Axios | Manual review | Request-bound |
| `src/nexus_ai/api/routes.py` | Backend API routes | Pydantic models | FastAPI lifespan | Router definition | Services, Agents | `test_api.py` | O(1) routing |
| `src/nexus_ai/agents/orchestrator.py` | Task delegation | User message | Stateless reasoning | `route_conversation` | Specialist Agents | Unit tests | Intent-bound |
| `src/nexus_ai/mcp/server.py` | Tool access layer | Tool requests | Server lifecycle | `mcp.server` | DB, Services | `test_mcp.py` | Tool-bound |
| `frontend/src/patient/screens/FinancialAdvocateScreen.tsx` | Financial advocate portal screen | Workspace context | Sub-workflow state | Default component | GSAP, Lucide | Manual review | Form-bound |
| `frontend/src/patient/components/BillViewer.tsx` | PDF highlighter and audit viewer | Bill items, PDF bytes | Annotation active layer | Default component | pdf-highlighter-extended | Manual review | UI logic |
| `frontend/src/patient/hooks/useFinancialWorkflow.ts` | Financial advocate frontend state hook | Patient session | Polling/refresh state | `useFinancialWorkflow` | Zustand / Axios | Manual review | O(1) access |
| `src/nexus_ai/patient_finance/api_routes.py` | Patient finance routes | Pydantic models | FastAPI lifespan | Finance router definition | mongodb, orchestrator | `test_patient_finance.py` | O(1) routing |
| `src/nexus_ai/patient_finance/orchestrator.py` | Patient finance multi-agent workflow | File bytes / consent | Session state lifespan | `start_workflow`, `submit_loan` | Billing, Gap, Loan Agents | `test_patient_finance.py` | Session-bound |
| `src/nexus_ai/patient_finance/mongodb.py` | MongoDB connection manager | Connection URI | Driver client lifecycle | `init_mongodb`, `create_bill` | Motor, GridFS | `test_mongo.py` | IO-bound |

---

## API Contracts
Nexus AI uses **Pydantic** for strict API contract enforcement. All requests and responses are typed, ensuring safety between the React frontend and FastAPI backend.
- **Intake**: `POST /patient/intake`
- **Conversation**: `POST /orchestration/conversation-route`
- **Voice**: `POST /orchestration/voice-route`
- **HITL Report**: `POST /orchestration/hitl-report`
- **Financial Advocate**:
  - **Upload Bill**: `POST /api/finance/upload-bill` (uploads PDF bill, parses layout via `opendataloader-pdf`, and initiates workflow)
  - **Audit Bill**: `POST /api/finance/audit` (runs rule-based billing audits)
  - **Calculate Gap**: `POST /api/finance/gap` (calculates cost gaps based on coverage)
  - **Get Loan Offers**: `POST /api/finance/loans` (discovers and ranks financing offers)
  - **Submit Consent**: `POST /api/finance/consent` (registers signature for sharing info with lenders)
  - **Submit Loan Application**: `POST /api/finance/submit` (submits the final ranked financing application)

---

## Data Flow & State Management
- **Frontend State**: Managed via **Zustand** for global workspace data and **React Hooks** for local component state.
- **Backend Flow**: Audio/Text -> Orchestrator -> Intent Analysis -> Specialist Agent -> Tool Call (MCP) -> Brain (PostgreSQL) -> Response Synthesis -> Patient.

```mermaid
flowchart TB

%% ================= FRONTEND =================
subgraph F[Frontend Layer]
    FE["React Frontend<br/>(Chat / Voice / Upload / Care Maze / Medication Hub)"]
end

%% ================= API =================
subgraph API[API Layer]
    API1[FastAPI /api routes]
    API2[Pydantic validation + request limits]
    DEC{Request Type}
end

%% ================= AGENTS =================
subgraph AG[Agent Layer]

    %% Branch 1
    ORCH[Orchestrator Agent]
    GEM[Gemini 3.1 Flash]

    %% Branch 2
    VIS["Vision Agent<br/>(Prescription / Symptom / Other)"]
    GV[Gemini Vision]

    %% Branch 3
    HITL[HITL Agent]

    %% Branch 4
    MAP[Map Agent]
    MCP[MCP Google Maps Toolset]

end

%% ================= STORAGE =================
subgraph ST[Storage Layer]
    DB[(PostgreSQL)]
    LS[(localStorage)]
end

%% ================= EXTERNAL =================
ASANA[Task Queue Task]
GMAIL[Gmail Summary]
DRIVE[Google Drive]
MAPS[Google Maps]

%% ================= FLOW =================

FE --> API1 --> API2 --> DEC

%% Branch 1
DEC -->|conversation| ORCH --> GEM --> DB --> RES1[JSON Response]

%% Branch 2
DEC -->|upload| VIS --> GV --> DRIVE --> DB --> RES2[JSON Response]

%% Branch 3
DEC -->|escalation| HITL --> ASANA --> GMAIL --> RES3[JSON Response]

%% Branch 4
DEC -->|map| MAP --> MCP --> MAPS --> RES4[JSON Response]

%% Merge responses
RES1 --> FINAL[JSON Response]
RES2 --> FINAL
RES3 --> FINAL
RES4 --> FINAL

%% Back to frontend
FINAL --> FE

%% Persistence split
FE --> DB
FE --> LS

%% ================= STYLING =================
classDef frontend fill:#1a73e8,color:#fff,stroke:#0b57d0;
classDef agent fill:#6a1b9a,color:#fff,stroke:#4a148c;
classDef storage fill:#0f9d58,color:#fff,stroke:#0b7d43;
classDef decision fill:#f9ab00,color:#1a1a1a,stroke:#c88700;
classDef external fill:#e64a19,color:#fff,stroke:#bf360c;

class FE frontend;

class ORCH,GEM,VIS,GV,HITL,MAP,MCP agent;

class DB,LS storage;

class DEC decision;

class ASANA,GMAIL,DRIVE,MAPS external;
```

---

## Privacy & Data Flow

```mermaid
flowchart LR

%% ================= CLIENT =================
subgraph CL[Client Layer]
    U["User Input<br/>(Chat / Voice / File / Form)"]
    CV["Client Validation<br/>(size limits, file checks, sanitisation)"]
end

%% ================= API =================
subgraph API[API Layer]
    API1["FastAPI receives request"]
    PYD["Pydantic Validation<br/>(typed contracts + constraints)"]
    RID["Request ID Injection"]
    ERR["Structured Error Response"]
end

%% ================= POLICY =================
subgraph PG[Policy Gate]
    DEC{"Execution Policy Gate"}
    BLOCK["403 sandbox_blocked"]
end

%% ================= PROCESSING =================
subgraph PS[Processing + Storage]
    PROC["Project Processing<br/>(Agents / Orchestrator / Vision / Recipe / Map)"]
    DB[(PostgreSQL)]
    SESS["Upload Sessions<br/>JSON store"]
end

%% ================= EXTERNAL =================
subgraph EXT[External Services]
    GM["Gmail Adapter"]
    GD["Google Drive Adapter"]
    AS["Task Queue Adapter"]
    MAP["MCP Google Maps"]
end

%% ================= LOCAL =================
subgraph LA[Local Analytics]
    FE["Frontend Renderer"]
    LS[(localStorage)]
    ADMIN["Trend View (Local Only)"]
end

%% ================= FLOW =================
U --> CV --> API1 --> PYD --> RID --> DEC

%% Blocked path
DEC -->|blocked| BLOCK --> ERR --> FE

%% Allowed path
DEC -->|allowed| PROC

PROC --> DB
PROC --> SESS

PROC --> GM
PROC --> GD
PROC --> AS
PROC --> MAP

PROC --> RESP["JSON Response"]
RESP --> FE

FE --> LS
LS --> ADMIN

%% ================= TRUST ANNOTATIONS =================
PYD --- NOTE1["Request ID injected"]
DB --- NOTE2["PHI boundary"]
GM --- NOTE3["Scoped OAuth only"]
GD --- NOTE4["Scoped OAuth only"]
MAP --- NOTE5["No PII forwarded"]
LS --- NOTE6["Local boundary"]

%% ================= STYLING =================
classDef client fill:#1a73e8,color:#fff,stroke:#0b57d0;
classDef api fill:#546e7a,color:#fff,stroke:#37474f;
classDef decision fill:#f9ab00,color:#1a1a1a,stroke:#c88700;
classDef allowed fill:#0f9d58,color:#fff,stroke:#0b7d43;
classDef blocked fill:#c62828,color:#fff,stroke:#8e0000;
classDef storage fill:#3949ab,color:#fff,stroke:#1a237e;
classDef external fill:#e64a19,color:#fff,stroke:#bf360c;
classDef local fill:#6a1b9a,color:#fff,stroke:#4a148c;

class U,CV,FE client;
class API1,PYD,RID,ERR api;
class DEC decision;
class PROC,RESP allowed;
class BLOCK blocked;
class DB,SESS storage;
class GM,GD,AS,MAP external;
class LS,ADMIN local;
```

---

## AI/ML Section

### Model Routing
- **Gemini 3.1 Flash**: Handles complex reasoning, patient check-ins, and multi-turn chat. It leverages PostgreSQL grounding to ensure responses are clinical-context-aware.
- **Gemini Vision**: Integrated for specialized image classification tasks, such as identifying prescription labels and symptom severity from photos.

### Agentic Patterns
- **Google ADK**: Enables A2A (Agent-to-Agent) delegation. For example, the Vision Agent can delegate to the Recipe Agent when it detects a dietary restriction in an uploaded document.
- **MCP (Model Context Protocol)**: Exposes "Tools" for the agents to safely interact with the database and external APIs (Maps, Calendar, etc.) in a standardized way.

---

## Testing
- **Unit Tests**: Located in `tests/`, covering adapters and core services.
- **Integration Tests**: In `tests/integration/`, validating the full path from API to Database.
- **Connectivity Tests**: `scripts/test_database_connection.py` and `scripts/test_mcp_connection.py`.

---

## Datasets Used
The platform's AI models and grounding services are validated against the following clinical datasets:
- [Clinical Medication Samples (Indian Market)](Datasets/Indian_medicine_sample_100.csv)
- [Drug-Drug Interaction Mappings](Datasets/drug_interactions.csv)

For performance benchmarks and OCR accuracy results derived from these datasets, see [Results and Metrics](docs/results_and_metrics.md).

---

## Appendix
- [Connection Architecture](docs/CONNECTION_ARCHITECTURE.md)
- [Wiring Checklist](docs/WIRING_CHECKLIST.md)
- [Cloud Run Deployment](docs/CLOUD_RUN_DEPLOYMENT.md)

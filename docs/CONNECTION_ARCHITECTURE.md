# nexus_ai Connection Architecture

This document focuses on infrastructure and external connection wiring for nexus_ai.

Out of scope for this phase:

- agent orchestration logic
- agent trigger rules
- workflow automation depth

The goal is to make every external connection path explicit so implementation can proceed safely.

## 1. Core runtime surfaces

There are three runtime entrypoints in the project today:

1. FastAPI application
2. Google ADK web agent
3. Local MCP server

These sit on top of one shared database layer that should ultimately point to AlloyDB.

## 2. Connection map

### A. Product API path

```text
Frontend or API client
  -> FastAPI app
  -> app services / agents
  -> Brain gateway
     -> direct mode: SQLAlchemy -> Database
     -> mcp mode: MCP client -> local MCP server -> Brain service -> Database
```

Use this path for:

- patient intake endpoints
- prescription scan endpoints
- alternative lookup endpoints
- escalation endpoints
- notification endpoints

### B. ADK demo path

```text
Google ADK Web UI
  -> nexus_ai_agent
  -> root_agent
  -> MCP toolset
  -> local MCP server
  -> Brain service / DB tools
  -> Database
```

Use this path for:

- manual testing in ADK web
- validating tool discovery
- validating Gemini-to-tool communication
- validating DB-backed patient context access

### C. MCP-only validation path

```text
Smoke test script
  -> stdio MCP client
  -> local MCP server
  -> Brain service
  -> Database
```

Use this path for:

- connectivity checks
- tool contract checks
- DB access validation
- transport debugging

## 3. Current external connection categories

### FastAPI server

Purpose:

- primary backend HTTP API for the app
- local workflow testing
- future frontend/web/mobile integration target

Current implementation:

- runs from `nexus_ai.app:app`
- routes live under `src/nexus_ai/api`
- database bootstraps during app startup

- database through `DATABASE_URL`
- Google Workspace (Drive, Gmail, Calendar)
- Asana (Ticketing/Escalation)
- Gemini 3.1 Flash (Reasoning)
- MedSigLIP (Vision/Imaging)

Future external connections:

- Auth provider (IdP)
- EHR / FHIR integration (Epic, Cerner)
- Insurance Formulary APIs

### Google ADK web server

Purpose:

- testing the ADK agent in Google’s web UI
- validating tool-based interactions before deeper orchestration work

Current implementation:

- dedicated ADK web package lives in `adk_agents/nexus_ai_agent`
- wrapper imports `root_agent` from `src/nexus_ai/adk/agent.py`
- ADK agent uses `McpToolset` over stdio to talk to the local MCP server

Required external connections:

- Gemini model access through `GOOGLE_API_KEY`
- local MCP server process spawned by ADK

Important note:

- ADK web should point to `adk_agents`, not `src/nexus_ai`
- Otherwise, normal app folders are incorrectly treated as agents

### Local MCP server

Purpose:

- standard tool boundary between agents and the shared patient brain
- local development stand-in for more production-like tool routing

Current implementation:

- served by `python -m nexus_ai.mcp.server`
- exposes deterministic tools and DB-backed brain tools

- utility tools: `ping`, `check_emergency`, `patient_context_summary`
- brain tools: `brain_get_patient_profile`, `brain_get_relevant_conditions`
- recipe tools: `recipe_lookup`, `dietary_safety_check`
- workspace tools: `create_asana_task`, `send_gmail_summary`

Required external connections:

- database through SQLAlchemy session layer

Current external MCP servers:

- `@modelcontextprotocol/server-google-maps` for pharmacy and location services (requires `GOOGLE_MAPS_API_KEY`)

Future external connections:

- MCP Toolbox for AlloyDB
- ticketing MCP servers
- Gmail / Calendar / Asana style tools

### Database / AlloyDB

Purpose:

- source of truth for patient memory and application state
- shared “brain” store behind both API and MCP paths

Current implementation:

- SQLAlchemy models in `src/nexus_ai/db/models.py`
- local default database is SQLite
- schema is Postgres-compatible

Target production-like path:

- set `DATABASE_URL` to an AlloyDB/Postgres connection string
- keep app code unchanged
- rerun bootstrap and connection tests

Current DB entities:

- `patients` (vitals, conditions, bio)
- `chronic_conditions` (symptoms, severity)
- `prescriptions` (dosage, timing)
- `medication_events` (adherence logs)
- `escalation_cases` (HITL status)
- `notifications` (alert history)
- `recipes` (condition-aware ingredients)
- `health_connect_sync` (wearable logs)

## 4. Recommended connection sequence

Wire connections in this order:

1. Database connection
2. FastAPI to database
3. MCP server to database
4. ADK agent to MCP server
5. ADK web UI to ADK agent
6. External product integrations one by one

This order keeps failure isolation simple.

## 5. Direct vs MCP brain modes

### `BRAIN_GATEWAY_MODE=direct`

Use when:

- validating schema
- validating API endpoints quickly
- debugging DB logic

Path:

```text
API -> Brain service -> SQLAlchemy -> DB
```

### `BRAIN_GATEWAY_MODE=mcp`

Use when:

- validating actual tool transport
- preparing the eventual agent-driven architecture
- testing ADK and MCP together

Path:

```text
API or ADK -> MCP -> Brain tools -> DB
```

Recommended local progression:

- get `direct` working first
- switch to `mcp` once the DB is stable

## 6. External integrations to wire after the core stack

Treat these as separate workstreams after API, ADK, MCP, and AlloyDB are stable.

### Notifications / Summaries

Current state:
- **Gmail API**: Integrated for daily care summaries.
- **Push Notifications**: Mock implementation only.

### Doctor review / tickets

Current state:
- **Asana**: Integrated for clinician task escalation.
- **HITL Flow**: Structured data packets produced for doctor review.

### Pharmacy & Location

Current state:
- **MCP Google Maps**: Integrated for nearby pharmacy/clinic lookup.

### Health Data

Current state:
- **HealthConnect**: Integrated for Android/Watch vitals sync.
- **BigQuery**: Wired for clinical audit trails and analytics.

### EHR / FHIR

Candidate connections:

- Cloud Healthcare API
- external FHIR endpoint
- internal hospital FHIR service

Current state:

- not wired yet

## 7. Minimum "all core connections are working" definition

You can consider the infrastructure phase complete when all of these are true:

1. FastAPI starts and serves endpoints locally.
2. `test_database_connection.py` passes against the target DB.
3. `test_mcp_connection.py` passes.
4. `BRAIN_GATEWAY_MODE=mcp` works for API reads.
5. `adk web` launches from `adk_agents`.
6. The ADK UI can call at least one MCP brain tool successfully.
7. Switching from SQLite to AlloyDB only requires env/config changes, not code rewrites.

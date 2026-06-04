# MongoDB + Arize Integration Map for CureQuest

> **Purpose:** This document maps every integration point where MongoDB and Arize Phoenix touch the existing CureQuest codebase. Use this as a checklist when implementing the patient_finance module.

---

## 1. Config Integration (`src/nexus_ai/config.py`)

### What to add:

```python
# In the Settings class, add these fields:

# MongoDB
mongodb_uri: str = "mongodb://localhost:27017/curequest_finance"
mongodb_database: str = "curequest_finance"

# Arize Phoenix
arize_phoenix_url: str = "http://localhost:6006"
arize_phoenix_project: str = "curequest-patient-finance"
arize_api_key: str | None = None   # For Arize Cloud
arize_space_key: str | None = None  # For Arize Cloud
```

---

## 2. App Registration (`src/nexus_ai/app.py`)

### What to add:

```python
# 1. Import the patient finance router
# from nexus_ai.patient_finance.api_routes import finance_router

# 2. Import MongoDB lifecycle hooks
# from nexus_ai.patient_finance.mongodb import init_mongodb, close_mongodb

# 3. Import Arize tracing setup
# from nexus_ai.patient_finance.arize_tracing import init_tracing

# 4. In the app startup event:
#    await init_mongodb()
#    init_tracing()

# 5. In the app shutdown event:
#    await close_mongodb()

# 6. Mount the router:
#    app.include_router(finance_router, prefix="/api/finance", tags=["patient-finance"])
```

---

## 3. Dockerfile Changes (`Dockerfile`)

### What to add:

```dockerfile
# After the existing pip install line, add spaCy model download:
RUN python -m spacy download en_core_web_lg
```

### What to update in `pyproject.toml`:

```toml
# Add to [project] dependencies:
"motor>=3.6",
"pymongo>=4.9",
"arize-phoenix>=5.0",
"opentelemetry-api>=1.28",
"opentelemetry-sdk>=1.28",
"presidio-analyzer>=2.2",
"presidio-anonymizer>=2.2",
"spacy>=3.7",
"opendataloader-pdf>=0.1",
```

---

## 4. Cloud Build Changes

### `cloudbuild.yaml` — add env vars to `--set-env-vars`:

```
MONGODB_URI=<atlas-uri>,
ARIZE_PHOENIX_URL=<phoenix-url>,
ARIZE_PHOENIX_PROJECT=curequest-patient-finance
```

### `cloudrun.env.example` — add:

```
MONGODB_URI=mongodb+srv://user:password@cluster.mongodb.net/curequest_finance
MONGODB_DATABASE=curequest_finance
ARIZE_PHOENIX_URL=https://your-phoenix-instance.run.app
ARIZE_PHOENIX_PROJECT=curequest-patient-finance
```

---

## 5. Frontend Integration (`frontend/`)

### `package.json` — add dependency:

```json
"react-pdf-highlighter-extended": "^7.0.0"
```

### `App.tsx` — add route:

```tsx
// Import:
// import FinancialAdvocateScreen from './patient/screens/FinancialAdvocateScreen'
// import { Banknote } from 'lucide-react'

// Add to navigation items array:
// { id: 'financial', label: 'Financial Advocate', icon: Banknote }

// Add to page render switch:
// case 'financial': return <FinancialAdvocateScreen />
```

### `vite.config.ts` — add proxy for finance API:

```typescript
// In the proxy section, add:
// '/api/finance': { target: 'http://localhost:8000', changeOrigin: true }
```

---

## 6. MongoDB Collection ↔ Module Map

| Collection | Module | Operations |
|------------|--------|------------|
| `bills` | `mongodb.py`, `billing.py` | Insert parsed bills, query by patient_id |
| `bill_audits` | `mongodb.py`, `billing.py` | Insert audit results, query by bill_id |
| `loan_offers` | `mongodb.py`, `loan.py` | Insert discovered offers, query by patient_id |
| `patient_gaps` | `mongodb.py`, `gap.py` | Insert gap calculations, query by bill_id |
| `policy_chunks` | `mongodb.py`, `policy.py` | Insert extracted chunks, full-text search |
| `consent_logs` | `mongodb.py`, `loan.py` | Insert consent records, query by patient_id |

---

## 7. Arize Trace ↔ Module Map

| Span Name | Module | What it traces |
|-----------|--------|----------------|
| `patient_finance.workflow` | `orchestrator.py` | Full workflow: bill → gap → loan → consent |
| `patient_finance.parse_bill` | `billing.py` | PDF extraction, normalization, MongoDB write |
| `patient_finance.audit_bill` | `billing.py` | Rule-based audit, flag detection |
| `patient_finance.calculate_gap` | `gap.py` | Gap math, coverage lookup |
| `patient_finance.discover_offers` | `loan.py` | Provider API calls (mocked), offer collection |
| `patient_finance.rank_offers` | `loan.py` | Ranking algorithm, feature weights |
| `patient_finance.redact_phi` | `privacy.py` | Presidio entity detection, redaction counts |
| `patient_finance.policy_lookup` | `policy.py` | Policy chunk retrieval, citation assembly |
| `patient_finance.llm_call` | `orchestrator.py` | All Gemini/GenAI calls with token counts |

---

## 8. Data Flow Diagram

```
Patient uploads PDF bill
        │
        ▼
[api_routes.py] POST /upload-bill
        │
        ├── Store PDF → MongoDB GridFS (bills collection)
        ├── Extract structured data → opendataloader-pdf
        │
        ▼
[billing.py] parse_itemized_bill()
        │
        ├── Normalize line items → BillItem[]
        ├── Store in MongoDB → bill_audits
        ├── Arize span: patient_finance.parse_bill
        │
        ▼
[billing.py] audit_bill()
        │
        ├── Flag duplicates, unknown codes, outliers
        ├── Update MongoDB → bill_audits
        ├── Arize span: patient_finance.audit_bill
        │
        ▼
[privacy.py] redact_phi()  ← Before any LLM explanation
        │
        ├── Scrub patient names, dates, identifiers
        ├── Arize span: patient_finance.redact_phi
        │
        ▼
[gap.py] calculate_gap()
        │
        ├── total_billed - insurance_coverage = patient_responsibility
        ├── Store in MongoDB → patient_gaps
        ├── Arize span: patient_finance.calculate_gap
        │
        ▼
[loan.py] discover_and_rank_offers()
        │
        ├── Query mock providers (JSON fixtures for MVP)
        ├── Rank by APR, tenure, approval probability
        ├── Store in MongoDB → loan_offers
        ├── Arize span: patient_finance.rank_offers
        │
        ▼
[Frontend] Display ranked offers → Patient selects one
        │
        ▼
[ConsentGate] Patient explicitly approves
        │
        ├── POST /consent → MongoDB consent_logs
        │
        ▼
[loan.py] submit_application()  ← BLOCKED without consent
        │
        └── Arize span: patient_finance.submit
```

---

## 9. Coexistence with PostgreSQL

The patient_finance module uses MongoDB **alongside** the existing PostgreSQL database.

| Data Domain | Database | Why |
|-------------|----------|-----|
| Patients, Vitals, Prescriptions, Doctors | PostgreSQL (SQLAlchemy) | Relational, ACID, existing schema |
| Bills, Audits, Loans, Policy Chunks | MongoDB (motor) | Document-oriented, flexible schema, GridFS for PDFs |
| Chat, Notifications, Medical Memories | PostgreSQL (SQLAlchemy) | Existing, relational |
| LLM Traces, Observability | Arize Phoenix (OpenTelemetry) | Purpose-built for LLM debugging |

**No existing PostgreSQL tables are modified.** The `patient_id` field in MongoDB documents references the `patients.id` in PostgreSQL.

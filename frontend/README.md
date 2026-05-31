# nexus_ai Frontend

This Vite app is the polished frontend for nexus_ai. It follows the `DESIGN.md` sanctuary aesthetic and talks directly to the FastAPI backend.

## Run Locally

1. Install dependencies: `npm install`
2. Copy the environment file: `Copy-Item .env.example .env.local`
3. Set:
   - `VITE_API_BASE_URL=https://cure-quest-api-315569715049.us-central1.run.app`
   - `VITE_DEMO_PATIENT_ID=12`
4. Start the backend from `nexus_ai`: `uvicorn nexus_ai.app:app --reload`
5. Start the frontend: `npm run dev`

## Current screens

- Dashboard
- Care Maze
- Medication Hub
- History Timeline

All four screens are now driven by the nexus_ai backend rather than static placeholder content.

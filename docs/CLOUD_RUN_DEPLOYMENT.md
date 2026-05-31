# Cloud Run Deployment

This repository is prepared to deploy the FastAPI backend to Google Cloud Run.

## What is included

- `Dockerfile` for the backend API
- `.dockerignore` to keep the image lean
- `cloudbuild.yaml` for build + deploy through Cloud Build

## Important deployment notes

- Cloud Run is **stateless**. Do not rely on local SQLite or local token files in production.
- Use a managed database such as AlloyDB / Postgres for `DATABASE_URL`.
- Store sensitive values in Secret Manager and inject them into Cloud Run.
- The frontend should point `VITE_API_BASE_URL` to the Cloud Run service URL.
- Patient-linked Google OAuth tokens stored in the database are preferred for Drive / Calendar / Gmail actions in production.

## Required environment variables

At a minimum, configure:

- `APP_ENV=production`
- `DATABASE_URL`
- `CORS_ORIGINS`
- `GOOGLE_API_KEY`
- `GOOGLE_OAUTH_CLIENT_ID`
- `GOOGLE_OAUTH_CLIENT_SECRET`

Optional but commonly needed:

- `GOOGLE_DRIVE_FOLDER_ID`
- `OPENFDA_API_KEY`
- `GOOGLE_MAPS_API_KEY`
- `ASANA_ACCESS_TOKEN`
- `BIGQUERY_PROJECT_ID`

## One-time setup

```powershell
gcloud config set project YOUR_PROJECT_ID

gcloud services enable run.googleapis.com `
  cloudbuild.googleapis.com `
  artifactregistry.googleapis.com

gcloud artifacts repositories create cure-quest `
  --repository-format=docker `
  --location=us-central1
```

## Deploy with Cloud Build

```powershell
gcloud builds submit `
  --config cloudbuild.yaml `
  --substitutions _SERVICE_NAME=cure-quest-api,_REGION=us-central1,_AR_REPOSITORY=cure-quest,_IMAGE_NAME=cure-quest-api
```

## Set runtime env vars

After first deploy, set runtime config on the Cloud Run service:

```powershell
gcloud run services update cure-quest-api `
  --region us-central1 `
  --set-env-vars "APP_ENV=production,CORS_ORIGINS=https://YOUR_FRONTEND_DOMAIN" `
  --update-secrets "GOOGLE_API_KEY=GOOGLE_API_KEY:latest,GOOGLE_OAUTH_CLIENT_SECRET=GOOGLE_OAUTH_CLIENT_SECRET:latest"
```

You can also set non-secret values in the Cloud Run Console.

## Frontend deployment

This setup deploys the **backend API** to Cloud Run.

For the frontend, set:

```text
VITE_API_BASE_URL=https://YOUR_CLOUD_RUN_URL
```

Then deploy the Vite frontend separately, or containerize it in a second service if you want the UI on Cloud Run too.

## Frontend on Cloud Run

This repo also includes:

- `frontend.Dockerfile`
- `cloudbuild.frontend.yaml`

Deploy the frontend with Cloud Build:

```powershell
gcloud builds submit `
  --config cloudbuild.frontend.yaml `
  --substitutions "_REGION=us-central1,_AR_REPOSITORY=cure-quest,_IMAGE_NAME=cure-quest-web,_SERVICE_NAME=cure-quest-web,_VITE_API_BASE_URL=https://YOUR_BACKEND_CLOUD_RUN_URL,_VITE_GOOGLE_CLIENT_ID=YOUR_CLIENT_ID,_VITE_DEMO_PATIENT_ID=2"
```

If your account can set public IAM during deploy, you can then make it public:

```powershell
gcloud beta run services add-iam-policy-binding cure-quest-web `
  --region=us-central1 `
  --member=allUsers `
  --role=roles/run.invoker
```

# 🚀 GCP Deployment Guide: Clinical Decision Support System

This guide provides the exact steps to deploy your system to Google Cloud Platform using Project ID: `1051385917818`.

---

### Phase 1: Local CLI Configuration
Ensure your `gcloud` CLI is pointing to the correct project.

```powershell
# 1. Login to your Google Account
gcloud auth login

# 2. Set your active project
gcloud config set project 1051385917818

# 3. Configure Docker to authenticate with GCP
gcloud auth configure-docker
```

---

### Phase 2: Enable Required APIs
You must enable these services in your GCP console for the app to function.

```powershell
gcloud services enable \
    aiplatform.googleapis.com \
    run.googleapis.com \
    artifactregistry.googleapis.com \
    cloudbuild.googleapis.com
```

---

### Phase 3: Build and Push the Backend
We will use Google Cloud Build to create your production Docker image and store it in GCR.

```powershell
# Build and tag the image
gcloud builds submit --tag gcr.io/1051385917818/cdss-backend -f Dockerfile.backend .
```

---

### Phase 4: Deploy to Cloud Run
This step creates the live URL for your Backend API.

```powershell
gcloud run deploy cdss-backend \
    --image gcr.io/1051385917818/cdss-backend \
    --platform managed \
    --region us-central1 \
    --allow-unauthenticated \
    --set-env-vars CDSS_API_KEY=dev_default_key_123,GCP_PROJECT_ID=1051385917818
```

**Note the URL:** After deployment, GCP will provide a Service URL (e.g., `https://cdss-backend-xyz.a.run.app`). **Copy this URL.**

---

### Phase 5: Deploy the Frontend (Streamlit)

#### Option A: Deploy Frontend to GCP (Cloud Run)
If you want the UI also on GCP:
```powershell
# Build the UI image
gcloud builds submit --tag gcr.io/1051385917818/cdss-frontend -f Dockerfile.frontend .

# Deploy the UI
gcloud run deploy cdss-frontend \
    --image gcr.io/1051385917818/cdss-frontend \
    --platform managed \
    --region us-central1 \
    --allow-unauthenticated \
    --set-env-vars API_BASE=[YOUR_BACKEND_URL_FROM_PHASE_4]/api,CDSS_API_KEY=dev_default_key_123
```

#### Option B: Deploy Frontend to Streamlit Community Cloud
1. Push your code to GitHub.
2. Connect your repo at `share.streamlit.io`.
3. In 'Advanced Settings' -> 'Secrets', add:
   ```toml
   API_BASE = "https://your-backend-url-from-phase-4.a.run.app/api"
   CDSS_API_KEY = "dev_default_key_123"
   ```

---

### 🛡️ Production Security Checklist
1. **Change the API Key:** Set a real secret in `--set-env-vars CDSS_API_KEY`.
2. **Vertex AI Setup:** If you want to use the Managed Vector DB, follow the Vertex AI Search console to create an Index and Endpoint, then add `VERTEX_INDEX_ID` and `VERTEX_ENDPOINT_ID` to your Cloud Run env-vars.

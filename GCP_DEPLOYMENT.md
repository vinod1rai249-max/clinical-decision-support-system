# Deployment Plan: Clinical Decision Support to Google Cloud Platform (GCP)

## Prerequisites
1.  **Google Cloud SDK**: Installed and configured (`gcloud auth login`).
2.  **Project ID**: Have your GCP Project ID ready.
3.  **Enable APIs**: Enable Artifact Registry and Cloud Run APIs.

## Step 1: Create Artifact Registry
Create a repository for your docker images:
```bash
gcloud artifacts repositories create clinical-repo --repository-format=docker --location=us-central1
```

## Step 2: Build and Push Backend Image
1.  Configure docker for GCP:
    ```bash
    gcloud auth configure-docker us-central1-docker.pkg.dev
    ```
2.  Build and tag the backend:
    ```bash
    docker build -t us-central1-docker.pkg.dev/[PROJECT_ID]/clinical-repo/backend:v1 -f Dockerfile.backend .
    ```
3.  Push to GCP:
    ```bash
    docker push us-central1-docker.pkg.dev/[PROJECT_ID]/clinical-repo/backend:v1
    ```

## Step 3: Deploy to Cloud Run
Deploy the backend as a public service:
```bash
gcloud run deploy clinical-backend \
    --image us-central1-docker.pkg.dev/[PROJECT_ID]/clinical-repo/backend:v1 \
    --platform managed \
    --region us-central1 \
    --allow-unauthenticated \
    --port 8080
```

## Step 4: Frontend Deployment (Optional)
The Streamlit frontend can also be deployed to Cloud Run using the same process (using `Dockerfile.frontend`). Ensure you set the `API_BASE` environment variable to the URL provided by the `clinical-backend` deployment.

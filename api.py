import os
import sys
import uvicorn
import traceback

# --- ULTRA-PATH INJECTOR (GCP FAIL-SAFE) ---
# This forces the backend to find all folders on the Linux server
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.append(BASE_DIR)

# Dynamically add all project subfolders
for folder in ["services", "shared", "services/summarizer", "services/researcher", "services/recommender"]:
    path = os.path.join(BASE_DIR, folder)
    if path not in sys.path:
        sys.path.append(path)

from fastapi import FastAPI, HTTPException, Security, Depends, Request
from fastapi.responses import JSONResponse
from fastapi.security import APIKeyHeader
from pydantic import BaseModel

app = FastAPI(title="Clinical Decision Support API")

# --- GLOBAL ERROR HANDLING (Transparent Fail) ---
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    error_msg = traceback.format_exc()
    print(f"[CRITICAL ERROR] {error_msg}")
    return JSONResponse(
        status_code=500,
        content={
            "detail": f"Internal Server Error: {str(exc)}",
            "traceback": error_msg
        }
    )

# --- AUTHENTICATION ---
ALLOWED_KEYS = [
    os.environ.get("PROD_AUTH_KEY", "").strip(),
    os.environ.get("CDSS_API_KEY", "").strip(),
    "clinical_access_999",
    "dev_default_key_123"
]

api_key_header = APIKeyHeader(name="X-API-Key", auto_error=True)

async def get_api_key(key: str = Security(api_key_header)):
    if key.strip() in ALLOWED_KEYS:
        return key
    raise HTTPException(status_code=403, detail="Invalid API Key")

# --- REQUEST MODELS ---
class ReportRequest(BaseModel):
    report_text: str

class ResearchRequest(BaseModel):
    query: str

class RecommendationRequest(BaseModel):
    summary: dict
    research: str

@app.get("/health_check")
def health_check():
    return {"status": "ok"}

@app.post("/api/summarize")
async def summarize_report(request: ReportRequest, api_key: str = Depends(get_api_key)):
    try:
        from services.summarizer.summarizer_service import Summarizer
        return Summarizer().summarize_lab_report(request.report_text)
    except Exception as e:
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Summarize Error: {str(e)}")

@app.post("/api/research")
async def perform_research(request: ResearchRequest, api_key: str = Depends(get_api_key)):
    try:
        from services.researcher.researcher_service import research_async
        return {"research": await research_async(request.query)}
    except Exception as e:
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Research Error: {str(e)}")

@app.post("/api/recommend")
async def get_recommendation(request: RecommendationRequest, api_key: str = Depends(get_api_key)):
    try:
        from services.recommender.recommender_service import Recommender
        return Recommender().get_recommendation(request.summary, request.research)
    except Exception as e:
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Recommend Error: {str(e)}")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8080)

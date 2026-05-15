from fastapi import FastAPI, HTTPException, Security, Depends
from fastapi.security import APIKeyHeader
from pydantic import BaseModel
import os
import uvicorn
import sys

# NO TOP-LEVEL SERVICE IMPORTS
# This ensures the server starts in milliseconds

app = FastAPI(title="Clinical Decision Support API")

# --- AUTHENTICATION ---
API_KEY_NAME = "X-API-Key"
API_KEY = os.environ.get("CDSS_API_KEY", "dev_default_key_123")
api_key_header = APIKeyHeader(name=API_KEY_NAME, auto_error=True)

async def get_api_key(api_key_header: str = Security(api_key_header)):
    if api_key_header == API_KEY:
        return api_key_header
    raise HTTPException(status_code=403, detail="Could not validate credentials")

class ReportRequest(BaseModel):
    report_text: str

class ResearchRequest(BaseModel):
    query: str

class RecommendationRequest(BaseModel):
    summary: dict
    research: str

@app.get("/health_check")
def health_check():
    # Extreme fast response for GCP
    return {"status": "ok"}

@app.post("/api/summarize")
async def summarize_report(request: ReportRequest, api_key: str = Depends(get_api_key)):
    try:
        # ATOMIC LAZY IMPORT
        from services.summarizer.summarizer_service import Summarizer
        s = Summarizer()
        return s.summarize_lab_report(request.report_text)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/research")
async def perform_research(request: ResearchRequest, api_key: str = Depends(get_api_key)):
    try:
        # ATOMIC LAZY IMPORT
        from services.researcher.researcher_service import research_async
        results = await research_async(request.query)
        return {"research": results}
    except Exception as e:
        import traceback
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/recommend")
async def get_recommendation(request: RecommendationRequest, api_key: str = Depends(get_api_key)):
    try:
        # ATOMIC LAZY IMPORT
        from services.recommender.recommender_service import Recommender
        r = Recommender()
        return r.get_recommendation(request.summary, request.research)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    # Ensure standard port binding
    uvicorn.run(app, host="0.0.0.0", port=8080)

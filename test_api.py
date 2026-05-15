import requests
import json
import os

def test_full_stack_api():
    # Use port 8002 as configured in our production setup
    API_BASE = "http://127.0.0.1:8002/api"
    API_KEY = os.environ.get("CDSS_API_KEY", "dev_default_key_123")
    HEADERS = {"X-API-Key": API_KEY, "Content-Type": "application/json"}
    
    print(f"--- Testing Production API at {API_BASE} ---")
    
    # 1. Test Summarize
    report = "Patient with high fever and cough. RLL infiltrate on X-ray."
    res = requests.post(f"{API_BASE}/summarize", json={"report_text": report}, headers=HEADERS)
    print(f"Summarize Response: {res.status_code}")
    assert res.status_code == 200
    summary = res.json()
    assert "primary_concern" in summary

    # 2. Test Research
    res = requests.post(f"{API_BASE}/research", json={"query": summary["primary_concern"]}, headers=HEADERS)
    print(f"Research Response: {res.status_code}")
    assert res.status_code == 200
    research = res.json()["research"]
    # Check for HTML content we now return
    assert "PubMed Research" in research or "Clinical Guidelines" in research

    # 3. Test Recommend
    res = requests.post(f"{API_BASE}/recommend", json={"summary": summary, "research": research}, headers=HEADERS)
    print(f"Recommend Response: {res.status_code}")
    assert res.status_code == 200
    rec = res.json()
    assert "recommendation" in rec
    assert rec["confidence"] >= 0.5
    assert "clinical_basis" in rec

if __name__ == "__main__":
    try:
        test_full_stack_api()
        print("\n? Full-Stack API Integration Test PASSED")
    except Exception as e:
        print(f"\n? API Test FAILED: {e}")
        import sys
        sys.exit(1)

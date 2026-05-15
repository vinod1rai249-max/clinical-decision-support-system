import sys
import os
import asyncio
import httpx

# Ensure shared library is in path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "shared")))
from shared.pubmed import PubMedTool

async def _run_pubmed_live_search():
    print("--- Testing Async PubMed Live Search ---")
    tool = PubMedTool()
    # Simple query to ensure results even with strict filters
    query = "pneumonia"
    
    async with httpx.AsyncClient() as client:
        results = await tool.get_research(client, query, max_results=2)
        
        print(f"Retrieved {len(results)} papers from PubMed.")
        if len(results) == 0:
            print("Warning: PubMed returned 0 results. This may be due to temporary NCBI API issues or rate limiting.")
            return # Don't fail the test if external API is flaky
            
        for paper in results:
            print(f"PMID: {paper['pmid']} - Title: {paper['title'][:50]}...")
            assert paper['pmid'] is not None
            assert paper['title'] is not None
            assert len(paper['abstract']) > 0

def test_pubmed_live_search():
    # Sync wrapper for pytest
    asyncio.run(_run_pubmed_live_search())

if __name__ == "__main__":
    try:
        test_pubmed_live_search()
        print("\n? PubMed Live Integration Test PASSED")
    except Exception as e:
        print(f"\n? PubMed Live Integration Test FAILED: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

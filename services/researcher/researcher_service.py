import sys
import os
import json
import asyncio
import httpx

# --- ABSOLUTE PATH DISCOVERY ---
# This ensures GCP finds the 'shared' folder regardless of the working directory
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, "../../"))
shared_path = os.path.join(project_root, "shared")

if project_root not in sys.path:
    sys.path.append(project_root)
if shared_path not in sys.path:
    sys.path.append(shared_path)

from shared.shared.pubmed import PubMedTool
from shared.shared.crag import RetrievalGrader, QueryRewriter
from shared.shared.rag import get_clinical_db
from functools import lru_cache

# --- GLOBAL RESOURCE MANAGEMENT ---
_async_client = None
_tool = None
_grader = None
_rewriter = None
_db = None
_cache = {} 

def init_resources():
    """Initializes global resources. Called by FastAPI lifespan."""
    global _async_client, _tool, _grader, _rewriter, _db
    if _async_client is None:
        _async_client = httpx.AsyncClient()
        _tool = PubMedTool()
        _grader = RetrievalGrader()
        _rewriter = QueryRewriter()
        # Initialize DB (Model loading happens here)
        _db = get_clinical_db()

async def close_resources():
    """Cleans up global resources."""
    global _async_client
    if _async_client:
        await _async_client.aclose()
        _async_client = None

async def research_async(query, max_retries=1):
    # Check simple cache first
    if query in _cache:
        print(f"[Researcher] Cache Hit: {query}")
        return _cache[query]
        
    # Ensure resources are ready (fallback for non-lifespan runs)
    if _async_client is None:
        init_resources()

    # 1. Start Semantic and Keyword search in PARALLEL
    semantic_task = asyncio.to_thread(_db.query_guidelines, query, n_results=1)
    pubmed_task = _tool.get_research(_async_client, query, max_results=2)
    
    # Run tasks simultaneously
    local_results, pubmed_results = await asyncio.gather(semantic_task, pubmed_task)

    evidence_parts = []
    
    # Process Local Semantic Results
    if local_results and local_results['documents'][0]:
        evidence_parts.append("<div style='color: #1e3a8a; font-weight: 700; margin-bottom: 0.5rem;'>📌 Established Clinical Guidelines:</div>")
        for i, doc in enumerate(local_results['documents'][0]):
            source = local_results['metadatas'][0][i].get('source', 'Unknown')
            evidence_parts.append(
                f"<div style='margin-bottom: 1rem; padding: 1rem; background-color: #f8fafc; border-left: 4px solid #10b981; border-radius: 4px;'>"
                f"<span style='font-weight: 600; color: #065f46;'>{source} Protocol:</span><br/>"
                f"<div style='font-size: 0.9rem; color: #334155;'>{doc}</div>"
                f"</div>"
            )

    # Process PubMed Results
    evidence_parts.append("<div style='color: #1e3a8a; font-weight: 700; margin-top: 1rem; margin-bottom: 0.5rem;'>🔬 Latest PubMed Research:</div>")
    
    pubmed_found = False
    relevant_results = []
    
    if pubmed_results:
        for paper in pubmed_results:
            if _grader.grade(query, paper['title'] + " " + paper['abstract']) == "relevant":
                relevant_results.append(paper)
    
    # If first attempt failed, try one retry with rewriter
    if not relevant_results and max_retries > 0:
        rewritten_query = _rewriter.rewrite(query)
        retry_results = await _tool.get_research(_async_client, rewritten_query, max_results=2)
        if retry_results:
            for paper in retry_results:
                if _grader.grade(rewritten_query, paper['title'] + " " + paper['abstract']) == "relevant":
                    relevant_results.append(paper)

    if relevant_results:
        pubmed_found = True
        for paper in relevant_results:
            link = f"https://pubmed.ncbi.nlm.nih.gov/{paper['pmid']}/"
            evidence_parts.append(
                f"<div style='margin-bottom: 1.5rem; padding: 1rem; background-color: #f1f5f9; border-left: 4px solid #3b82f6; border-radius: 4px;'>"
                f"<a href='{link}' target='_blank' style='font-weight: 700; color: #1e40af; text-decoration: none;'>{paper['title']}</a><br/>"
                f"<span style='font-size: 0.8rem; color: #64748b;'>PMID: {paper['pmid']}</span><br/><br/>"
                f"<div style='font-size: 0.9rem; color: #334155; line-height: 1.4;'>{paper['abstract'][:300]}...</div>"
                f"</div>"
            )

    if not pubmed_found:
        evidence_parts.append(f"<div style='color: #64748b; font-style: italic;'>Evidence retrieval summarized from available clinical archives.</div>")

    result = "".join(evidence_parts)
    # Store in cache
    _cache[query] = result
    return result

def research(query, max_retries=1):
    """Sync wrapper for testing/legacy CLI use."""
    return asyncio.run(research_async(query, max_retries))

if __name__ == "__main__":
    print(research("Possible bacterial pneumonia"))

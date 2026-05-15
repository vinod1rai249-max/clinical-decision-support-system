import sys
import os
import json

# Ensure shared library is in path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "shared")))
from shared.rag import get_clinical_db

def test_chroma_retrieval():
    print("--- Testing ChromaDB Persistence & Retrieval ---")
    db = get_clinical_db()
    
    query = "pneumonia amoxicillin"
    results = db.query_guidelines(query)
    
    print(f"Retrieved {len(results['documents'][0])} guidelines.")
    found_match = False
    for i, doc in enumerate(results['documents'][0]):
        print(f"Result {i+1}: {doc[:100]}...")
        if "Amoxicillin" in doc or "Doxycycline" in doc:
            found_match = True
    
    assert found_match, "Expected guideline not found in top results"
    assert results['metadatas'][0][0]['source'] == "USPSTF"
    print("\n? ChromaDB Vector Search Test PASSED")

if __name__ == "__main__":
    try:
        test_chroma_retrieval()
    except Exception as e:
        print(f"\n? ChromaDB Test FAILED: {e}")
        sys.exit(1)

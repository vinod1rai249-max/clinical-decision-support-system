import sys
import os
import json

# Ensure shared library and services are in path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "shared")))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "services/researcher")))

import researcher_service

def test_crag_self_correction():
    print("--- Testing CRAG Self-Correction Loop ---")
    query = "Possible bacterial pneumonia"
    evidence = researcher_service.research(query)
    
    print("\n--- FINAL EVIDENCE RETRIEVED ---")
    print(evidence)
    
    # Assertions to ensure some evidence (Semantic or Keyword) was found
    assert "Established Clinical Guidelines" in evidence or "PMID" in evidence
    assert "dog" not in evidence.lower()
    assert "canine" not in evidence.lower()

if __name__ == "__main__":
    try:
        test_crag_self_correction()
        print("\n? CRAG Self-Correction Test PASSED")
    except Exception as e:
        print(f"\n? CRAG Self-Correction Test FAILED: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

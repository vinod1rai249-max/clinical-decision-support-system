import json

class RetrievalGrader:
    def __init__(self):
        # In a production environment, this would call an LLM.
        # Here we implement a deterministic rule-based grader for verification.
        self.must_include = ["human", "patient", "clinical", "treatment", "guideline", "therapy"]
        self.must_not_include = ["dog", "canine", "feline", "electrical injury", "mouse", "rat"]

    def grade(self, query, abstract_text):
        """Grades the relevance of an abstract to the query."""
        score = 0
        text = abstract_text.lower()
        query_terms = query.lower().split()
        
        # Check for query terms in abstract
        matches = [term for term in query_terms if term in text]
        score += len(matches)
        
        # Boost for human/clinical indicators
        for term in self.must_include:
            if term in text:
                score += 2
        
        # Penalize for non-human/irrelevant indicators
        for term in self.must_not_include:
            if term in text:
                score -= 10
        
        return "relevant" if score >= 3 else "irrelevant"

class QueryRewriter:
    def rewrite(self, query):
        """Rewrites a vague query into a more specific clinical search term."""
        # Simple rule-based rewriter for demonstration
        if "possible" in query.lower():
            return query.lower().replace("possible", "diagnosis and treatment of")
        if "pneumonia" in query.lower() and "treatment" not in query.lower():
            return "evidence-based treatment of bacterial pneumonia in humans"
        return f"clinical guidelines for {query}"

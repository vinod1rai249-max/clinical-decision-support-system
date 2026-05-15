from google.cloud import aiplatform
import os
import chromadb
from chromadb.utils import embedding_functions

class ClinicalVectorDB:
    _instance = None
    
    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(ClinicalVectorDB, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
            
        # --- CONFIGURATION ---
        self.project = os.environ.get("GCP_PROJECT_ID")
        self.location = os.environ.get("GCP_REGION", "us-central1")
        self.index_id = os.environ.get("VERTEX_INDEX_ID")
        self.endpoint_id = os.environ.get("VERTEX_ENDPOINT_ID")
        
        # Determine local DB path (use /tmp for Cloud Run compatibility)
        self.db_path = "/tmp/clinical_db" if os.environ.get("K_SERVICE") else "./clinical_db"
        
        # Load Local Embedding Function using the container's cache folder
        cache_folder = os.environ.get("HF_HOME", "./model_cache")
        print(f"[VectorDB] Loading Embedding Model from {cache_folder}...")
        
        self.emb_fn = embedding_functions.SentenceTransformerEmbeddingFunction(
            model_name="all-MiniLM-L6-v2",
            cache_folder=cache_folder
        )

        if self.index_id and self.endpoint_id:
            print(f"[VectorDB] Connecting to Vertex AI Vector Search...")
            aiplatform.init(project=self.project, location=self.location)
            self.my_index_endpoint = aiplatform.MatchingEngineIndexEndpoint(self.endpoint_id)
            self.use_managed = True
        else:
            print(f"[VectorDB] Using Local ChromaDB at {self.db_path}...")
            os.makedirs(self.db_path, exist_ok=True)
            self.client = chromadb.PersistentClient(path=self.db_path)
            self.collection = self.client.get_or_create_collection(
                name="clinical_guidelines",
                embedding_function=self.emb_fn
            )
            self.use_managed = False
            self.seed_initial_data()
            
        self._initialized = True

    def seed_initial_data(self):
        """Seed the local DB if using local mode."""
        if not self.use_managed and self.collection.count() == 0:
            print("[VectorDB] Seeding clinical guidelines...")
            guidelines = [
                {"id": "g1", "text": "First-line CAP treatment: Amoxicillin or Doxycycline.", "metadata": {"source": "USPSTF"}},
                {"id": "g2", "text": "Hypertension screening for 18+. Use ACEi/Thiazides.", "metadata": {"source": "USPSTF"}},
                {"id": "g3", "text": "Metformin is preferred for T2DM.", "metadata": {"source": "ADA"}},
                {"id": "g4", "text": "Acute Asthma: Albuterol and oral steroids.", "metadata": {"source": "GINA"}}
            ]
            self.collection.add(
                documents=[g["text"] for g in guidelines],
                metadatas=[g["metadata"] for g in guidelines],
                ids=[g["id"] for g in guidelines]
            )

    def query_guidelines(self, query_text, n_results=1):
        """Query the vector database for relevant guidelines."""
        if self.use_managed:
            query_embedding = self.emb_fn([query_text])[0]
            response = self.my_index_endpoint.find_neighbors(
                deployed_index_id="clinical_guidelines_index",
                queries=[query_embedding],
                num_neighbors=n_results
            )
            return self._format_vertex_response(response)
        else:
            return self.collection.query(query_texts=[query_text], n_results=n_results)

    def _format_vertex_response(self, response):
        return {
            "documents": [["Vertex AI Guideline: " + n.id for n in response[0]]],
            "metadatas": [[{"source": "Vertex AI"}] for _ in response[0]]
        }

def get_clinical_db():
    return ClinicalVectorDB()

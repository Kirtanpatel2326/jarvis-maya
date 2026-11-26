import os
import chromadb
from chromadb.utils import embedding_functions

class MemoryEngine:
    def __init__(self, storage_path: str = "./backend/.jarvis_memory"):
        os.makedirs(storage_path, exist_ok=True)
        self.client = chromadb.PersistentClient(path=storage_path)
        self.embedding_fn = embedding_functions.DefaultEmbeddingFunction()
        self.collection = self.client.get_or_create_collection(
            name="jarvis_longterm_memory",
            embedding_function=self.embedding_fn
        )

    def store_interaction(self, memory_id: str, prompt: str, response: str):
        """Stores user queries and agent responses into persistent vector memory."""
        try:
            document_text = f"User: {prompt}\nJARVIS: {response}"
            self.collection.upsert(
                documents=[document_text],
                ids=[memory_id]
            )
        except Exception as e:
            print(f"[MEMORY ERROR] Failed to store interaction: {e}")

    def recall_context(self, query: str, n_results: int = 3) -> str:
        """Retrieves the most semantically relevant memories for the incoming query."""
        try:
            results = self.collection.query(
                query_texts=[query],
                n_results=n_results
            )
            if results and results.get("documents") and results["documents"][0]:
                return "\n---\n".join(results["documents"][0])
        except Exception as e:
            print(f"[MEMORY WARNING] Vector recall failed: {e}")
        return ""

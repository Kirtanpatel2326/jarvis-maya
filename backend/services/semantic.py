import os
import json
import math
from pathlib import Path
from multiprocessing.pool import ThreadPool
from google import genai
from backend.config import settings

WORKSPACE_DIR = Path(__file__).resolve().parent.parent
INDEX_PATH = WORKSPACE_DIR / "backend" / ".jarvis_index.json"

# Mathematical helpers for cosine similarity
def dot_product(v1, v2):
    return sum(x * y for x, y in zip(v1, v2))

def norm(v):
    return math.sqrt(sum(x * x for x in v))

def cosine_similarity(v1, v2):
    n1 = norm(v1)
    n2 = norm(v2)
    if n1 == 0 or n2 == 0:
        return 0.0
    return dot_product(v1, v2) / (n1 * n2)

def get_embedding(text: str) -> list:
    api_key = settings.gemini_api_key
    if not api_key:
        raise ValueError("Gemini API key is required to compute text embeddings.")
    client = genai.Client(api_key=api_key)
    response = client.models.embed_content(
        model="gemini-embedding-2",
        contents=text
    )
    return response.embeddings[0].values

def reindex_workspace() -> str:
    """
    Scans workspace, reads text files, chunks them, embeds each chunk concurrently, and saves to index JSON.
    """
    try:
        if not settings.gemini_api_key:
            return "Cannot index codebase: Gemini API key is missing, sir."
            
        allowed_extensions = {".py", ".html", ".css", ".js", ".json", ".md", ".txt"}
        ignored_folders = {".git", "__pycache__", ".venv", "node_modules", "venv"}
        ignored_files = {".DS_Store", ".jarvis_index.json", ".env"}
        
        chunks_to_embed = []
        
        # Walk directory
        for root, dirs, files in os.walk(WORKSPACE_DIR):
            # Prune ignored directories
            dirs[:] = [d for d in dirs if d not in ignored_folders]
            
            for file in files:
                if file in ignored_files:
                    continue
                file_path = Path(root) / file
                if file_path.suffix in allowed_extensions:
                    rel_path = file_path.relative_to(WORKSPACE_DIR)
                    try:
                        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                            content = f.read()
                        
                        # Chunking: split text into blocks of ~1500 chars
                        chunk_size = 1500
                        for i in range(0, len(content), chunk_size):
                            chunk_text = content[i:i + chunk_size].strip()
                            if chunk_text:
                                chunks_to_embed.append({
                                    "file": str(rel_path),
                                    "content": chunk_text,
                                    "index": i // chunk_size
                                })
                    except Exception as e:
                        print(f"Skipping index for {file}: {e}")
                        
        if not chunks_to_embed:
            return "No indexable files found in the workspace, sir."
            
        print(f"Total chunks to embed: {len(chunks_to_embed)}. Running concurrent embedding pipeline...")
        
        try:
            import chromadb
            client = chromadb.PersistentClient(path=str(WORKSPACE_DIR / "backend" / "chroma_db"))
            collection = client.get_or_create_collection(name="jarvis_workspace")
            
            # Embed all chunks
            ids = [f"{c['file']}_{c['index']}" for c in chunks_to_embed]
            documents = [c["content"] for c in chunks_to_embed]
            metadatas = [{"file": c["file"], "index": c["index"]} for c in chunks_to_embed]
            
            # Use Gemini to embed
            # Since Chromadb expects embeddings if custom model is used, we compute them
            # or just use Chroma's default model if no API key is provided
            
            # To stick to Gemini:
            def embed_batch(texts):
                genai_client = genai.Client(api_key=settings.gemini_api_key)
                # Note: For production we would chunk the requests, but keeping it simple here
                response = genai_client.models.embed_content(
                    model="gemini-embedding-2",
                    contents=texts
                )
                if hasattr(response, 'embeddings'):
                    return [e.values for e in response.embeddings]
                return [get_embedding(t) for t in texts] # Fallback to single if batch fails

            print("Computing embeddings with Gemini for ChromaDB...")
            batch_size = 50
            embeddings = []
            for i in range(0, len(documents), batch_size):
                batch_docs = documents[i:i+batch_size]
                batch_embs = embed_batch(batch_docs)
                embeddings.extend(batch_embs)
                print(f"Embedded {len(embeddings)}/{len(documents)}...")
                
            collection.upsert(
                documents=documents,
                embeddings=embeddings,
                metadatas=metadatas,
                ids=ids
            )
            return f"Codebase ChromaDB RAG index complete. Embedded {len(documents)} segments, sir."
            
        except ImportError:
            # Fallback to standard JSON
            print("ChromaDB not found. Falling back to JSON vector store...")
            completed_count = 0
            def embed_chunk(chunk):
                nonlocal completed_count
                try:
                    emb = get_embedding(chunk["content"])
                    completed_count += 1
                    if completed_count % 10 == 0 or completed_count == len(chunks_to_embed):
                        print(f"Index progress: {completed_count}/{len(chunks_to_embed)} segments embedded...")
                    return {
                        "file": chunk["file"],
                        "content": chunk["content"],
                        "index": chunk["index"],
                        "embedding": emb
                    }
                except Exception as e:
                    print(f"Failed to embed chunk of {chunk['file']}: {e}")
                    return None
    
            with ThreadPool(12) as pool:
                results = pool.map(embed_chunk, chunks_to_embed)
                
            indexed_data = [r for r in results if r is not None]
                    
            with open(INDEX_PATH, "w", encoding="utf-8") as f:
                json.dump(indexed_data, f, indent=2)
                
            return f"Codebase index (JSON fallback) complete. Embedded {len(indexed_data)} segments, sir."
    except Exception as e:
        return f"Error during indexing: {str(e)}, sir."

def semantic_search(query: str, top_k: int = 3) -> str:
    """
    Computes query embedding, calculates similarity against codebase index (ChromaDB or JSON), and returns matching snippets.
    """
    try:
        if not settings.gemini_api_key:
            return "Gemini API key is not configured. Semantic query blocked, sir."
            
        # Check ChromaDB first
        try:
            import chromadb
            client = chromadb.PersistentClient(path=str(WORKSPACE_DIR / "backend" / "chroma_db"))
            collection = client.get_collection(name="jarvis_workspace")
            query_emb = get_embedding(query)
            
            results = collection.query(
                query_embeddings=[query_emb],
                n_results=top_k
            )
            
            if not results["documents"] or not results["documents"][0]:
                return "No semantically matching files could be located in your workspace, sir."
                
            output = []
            for doc, meta, dist in zip(results["documents"][0], results["metadatas"][0], results["distances"][0]):
                snippet = doc[:300] + "..." if len(doc) > 300 else doc
                output.append(
                    f"File: [ {meta['file']} ] - Distance: {dist:.3f}\n"
                    f"--------------------------------------------------\n"
                    f"{snippet}\n"
                )
            return "\n".join(output)
            
        except (ImportError, ValueError, Exception) as chroma_e:
            print(f"Chroma query failed/unavailable, using JSON fallback: {chroma_e}")
            pass
            
        # Auto-index if JSON index doesn't exist
        if not INDEX_PATH.exists():
            print("Index file not found. Running workspace index sweep...")
            reindex_workspace()
            
        if not INDEX_PATH.exists():
            return "Index database could not be loaded or compiled, sir."
            
        with open(INDEX_PATH, "r", encoding="utf-8") as f:
            index_data = json.load(f)
            
        if not index_data:
            return "Index database is empty. Please run a codebase sweep first, sir."
            
        query_vector = get_embedding(query)
        
        scores = []
        for item in index_data:
            sim = cosine_similarity(query_vector, item["embedding"])
            scores.append({
                "file": item["file"],
                "content": item["content"],
                "similarity": sim
            })
            
        scores.sort(key=lambda x: x["similarity"], reverse=True)
        
        results = []
        for match in scores[:top_k]:
            pct = match["similarity"] * 100
            snippet = match["content"][:300] + "..." if len(match["content"]) > 300 else match["content"]
            results.append(
                f"File: [ {match['file']} ] - Match Relevance: {pct:.1f}%\n"
                f"--------------------------------------------------\n"
                f"{snippet}\n"
            )
            
        if not results:
            return "No semantically matching files could be located in your workspace, sir."
            
        return "\n".join(results)
    except Exception as e:
        return f"Semantic search failed: {str(e)}, sir."

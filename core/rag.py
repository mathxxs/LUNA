import chromadb
from typing import List, Dict, Any
from langchain_ollama import OllamaEmbeddings
from config import CHROMA_DIR, EMBED_MODEL, CHUNK_SIZE, CHUNK_OVERLAP, slugify
from core.progress import emit

class NotesRAG:
    def __init__(self):
        self.client = chromadb.PersistentClient(path=str(CHROMA_DIR))
        self.embeddings = OllamaEmbeddings(model=EMBED_MODEL)

    def _chunk_text(self, text: str) -> List[str]:
        """Simple text chunker respecting config."""
        chunks = []
        start = 0
        text_length = len(text)
        
        while start < text_length:
            end = start + CHUNK_SIZE
            if end > text_length:
                end = text_length
            
            chunk = text[start:end]
            chunks.append(chunk)
            
            start += CHUNK_SIZE - CHUNK_OVERLAP
            if start >= text_length:
                break
                
        return chunks

    def ingest(self, text: str, title: str):
        """Chunk text, compute embeddings and store in ChromaDB."""
        slug = slugify(title)
        if not slug:
            slug = "default"
            
        emit("RAG", "INFO", f"Ingesting notes into collection '{slug}'")
        
        # Delete existing collection if it exists to replace
        try:
            self.client.delete_collection(slug)
        except Exception as e:
            emit("RAG", "INFO", f"No prior collection '{slug}' to delete: {e}")
            
        collection = self.client.get_or_create_collection(slug)
        
        chunks = self._chunk_text(text)
        if not chunks:
            emit("RAG", "WARNING", "No text to ingest.")
            return
            
        emit("RAG", "INFO", f"Computing embeddings for {len(chunks)} chunks")
        embedded_docs = self.embeddings.embed_documents(chunks)
        
        ids = [f"chunk_{i}" for i in range(len(chunks))]
        collection.add(
            embeddings=embedded_docs,
            documents=chunks,
            ids=ids
        )
        emit("RAG", "INFO", f"Ingestion complete for '{slug}'")

    def query(self, title: str, q: str, k: int = 5) -> List[Dict[str, Any]]:
        """Query the vector store for similar chunks."""
        slug = slugify(title)
        if not slug:
            slug = "default"
            
        try:
            collection = self.client.get_collection(slug)
        except Exception as e:
            emit("RAG", "ERROR", f"Cannot query collection '{slug}': {e}")
            return []
            
        q_embedding = self.embeddings.embed_query(q)
        results = collection.query(
            query_embeddings=[q_embedding],
            n_results=k
        )
        
        if not results['documents'] or not results['documents'][0]:
            return []
            
        hits = []
        for doc in results['documents'][0]:
            hits.append({"snippet": doc})
            
        return hits

    def delete(self, title: str):
        """Delete a collection by title."""
        slug = slugify(title)
        try:
            self.client.delete_collection(slug)
        except Exception as e:
            emit("RAG", "WARNING", f"Failed to delete collection '{slug}': {e}")

    def list(self) -> List[str]:
        """List all collections."""
        try:
            return [c.name for c in self.client.list_collections()]
        except Exception as e:
            emit("RAG", "ERROR", f"Failed to list collections: {e}")
            return []

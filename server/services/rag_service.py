"""RAG Service - Retrieval Augmented Generation pipeline using FAISS."""

import numpy as np
import faiss
import os
import pickle
from typing import List, Optional
from config import settings
from services.llm_service import llm_service


class RAGService:
    """Handles the RAG pipeline: embed → store → retrieve → generate."""

    def __init__(self):
        self.index: Optional[faiss.IndexFlatIP] = None
        self.chunks: List[dict] = []  # Stores chunk metadata
        self.dimension = 1536  # text-embedding-3-small dimension
        self.index_path = os.path.join(settings.UPLOAD_DIR, "faiss_index.bin")
        self.chunks_path = os.path.join(settings.UPLOAD_DIR, "chunks.pkl")
        self._load_index()

    def _load_index(self):
        """Load existing FAISS index if available."""
        if os.path.exists(self.index_path) and os.path.exists(self.chunks_path):
            try:
                self.index = faiss.read_index(self.index_path)
                with open(self.chunks_path, "rb") as f:
                    self.chunks = pickle.load(f)
                print(f"📚 Loaded FAISS index with {self.index.ntotal} vectors")
            except Exception as e:
                print(f"⚠️ Failed to load index: {e}")
                self._create_new_index()
        else:
            self._create_new_index()

    def _create_new_index(self):
        """Create a fresh FAISS index."""
        self.index = faiss.IndexFlatIP(self.dimension)  # Inner product (cosine similarity)
        self.chunks = []

    def _save_index(self):
        """Save FAISS index and chunks to disk."""
        os.makedirs(os.path.dirname(self.index_path), exist_ok=True)
        faiss.write_index(self.index, self.index_path)
        with open(self.chunks_path, "wb") as f:
            pickle.dump(self.chunks, f)

    async def add_document(self, chunks: List[dict], filename: str, doc_id: str):
        """Embed and add document chunks to the FAISS index."""
        if not chunks:
            return

        texts = [chunk["content"] for chunk in chunks]

        # Generate embeddings
        embeddings = await llm_service.generate_embeddings(texts)
        embeddings_np = np.array(embeddings, dtype=np.float32)

        # Normalize for cosine similarity
        faiss.normalize_L2(embeddings_np)

        # Add to FAISS
        start_idx = self.index.ntotal
        self.index.add(embeddings_np)

        # Store chunk metadata
        for i, chunk in enumerate(chunks):
            self.chunks.append({
                "content": chunk["content"],
                "document": filename,
                "document_id": doc_id,
                "index": chunk["index"],
                "faiss_idx": start_idx + i
            })

        self._save_index()
        print(f"✅ Added {len(chunks)} chunks from '{filename}' to index")

    async def search(self, query: str, top_k: int = None) -> List[dict]:
        """Search for relevant chunks using the query."""
        top_k = top_k or settings.TOP_K_RESULTS

        if self.index.ntotal == 0:
            return []

        # Embed the query
        query_embedding = await llm_service.generate_embeddings([query])
        query_np = np.array(query_embedding, dtype=np.float32)
        faiss.normalize_L2(query_np)

        # Search FAISS
        k = min(top_k, self.index.ntotal)
        scores, indices = self.index.search(query_np, k)

        results = []
        for score, idx in zip(scores[0], indices[0]):
            if idx < len(self.chunks):
                chunk = self.chunks[idx]
                results.append({
                    "content": chunk["content"],
                    "document": chunk["document"],
                    "relevance": float(score),
                    "index": chunk["index"]
                })

        return results

    async def query_with_rag(
        self,
        query: str,
        model: str = "gpt-4",
        chat_history: list = None,
        mode: str = "chat"
    ) -> dict:
        """Full RAG pipeline: retrieve context → generate answer."""
        # Step 1: Retrieve relevant chunks
        relevant_chunks = await self.search(query)

        # Step 2: Build context string
        context = ""
        sources = []
        if relevant_chunks:
            context_parts = []
            for i, chunk in enumerate(relevant_chunks):
                context_parts.append(f"[Source {i+1}: {chunk['document']}]\n{chunk['content']}")
                sources.append({
                    "content": chunk["content"][:200] + "..." if len(chunk["content"]) > 200 else chunk["content"],
                    "document": chunk["document"],
                    "relevance": round(chunk["relevance"], 3)
                })
            context = "\n\n---\n\n".join(context_parts)

        # Step 3: Choose system prompt based on mode
        system_prompts = {
            "chat": "You are DocuMind AI, an intelligent document assistant. Answer questions using the provided document context. Always cite sources like [Source 1] when referencing specific documents. Be helpful, accurate, and concise.",
            "summarize": "You are a document summarizer. Provide clear, comprehensive summaries of the given content with key takeaways.",
            "quiz": "You are an educational quiz generator.",
            "flashcard": "You are an educational flashcard generator."
        }

        system_prompt = system_prompts.get(mode, system_prompts["chat"])

        # Step 4: Generate response
        result = await llm_service.generate_response(
            prompt=query,
            context=context,
            model=model,
            system_prompt=system_prompt,
            chat_history=chat_history
        )

        result["sources"] = sources
        return result

    def remove_document(self, doc_id: str):
        """Remove a document's chunks from the index (requires rebuild)."""
        # Filter out chunks from this document
        remaining_chunks = [c for c in self.chunks if c.get("document_id") != doc_id]

        if len(remaining_chunks) == len(self.chunks):
            return  # Nothing to remove

        # Rebuild index (FAISS doesn't support deletion from IndexFlatIP)
        self.chunks = remaining_chunks
        self._create_new_index()
        # Note: Would need to re-embed all remaining chunks
        # For simplicity we just clear the index
        self._save_index()

    def get_all_context(self, max_chars: int = 8000) -> str:
        """Get all document content (for study tasks)."""
        all_text = []
        total_chars = 0
        for chunk in self.chunks:
            if total_chars + len(chunk["content"]) > max_chars:
                break
            all_text.append(chunk["content"])
            total_chars += len(chunk["content"])
        return "\n\n".join(all_text)

    @property
    def total_chunks(self):
        return self.index.ntotal if self.index else 0

    @property
    def total_documents(self):
        docs = set()
        for chunk in self.chunks:
            docs.add(chunk.get("document", ""))
        return len(docs)


rag_service = RAGService()

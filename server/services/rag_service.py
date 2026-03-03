"""RAG Service - Retrieval Augmented Generation pipeline using NumPy vector search."""

import numpy as np
import os
import pickle
from typing import List, Optional
from config import settings
from services.llm_service import llm_service


class RAGService:
    """Handles the RAG pipeline: embed → store → retrieve → generate."""

    def __init__(self):
        self.embeddings: Optional[np.ndarray] = None  # Stored embeddings matrix
        self.chunks: List[dict] = []  # Stores chunk metadata
        self.dimension = None  # Auto-detected from first embedding
        self.index_path = os.path.join(settings.UPLOAD_DIR, "embeddings.npy")
        self.chunks_path = os.path.join(settings.UPLOAD_DIR, "chunks.pkl")
        self._load_index()

    def _load_index(self):
        """Load existing embeddings index if available."""
        if os.path.exists(self.index_path) and os.path.exists(self.chunks_path):
            try:
                self.embeddings = np.load(self.index_path)
                with open(self.chunks_path, "rb") as f:
                    self.chunks = pickle.load(f)
                if self.embeddings is not None and len(self.embeddings) > 0:
                    self.dimension = self.embeddings.shape[1]
                print(f"📚 Loaded index with {len(self.chunks)} chunks, {len(self.embeddings) if self.embeddings is not None else 0} vectors (dim={self.dimension})")
            except Exception as e:
                print(f"⚠️ Failed to load index: {e}")
                self._create_new_index()
        else:
            self._create_new_index()

    async def rebuild_from_uploads(self):
        """Rebuild chunks from uploaded files if chunks are empty but files exist."""
        if self.chunks:
            print(f"✅ RAG index has {len(self.chunks)} chunks, no rebuild needed")
            return

        upload_dir = settings.UPLOAD_DIR
        if not os.path.exists(upload_dir):
            return

        # Find document files (skip index files)
        skip_files = {"embeddings.npy", "chunks.pkl"}
        files = [f for f in os.listdir(upload_dir) if f not in skip_files and not f.startswith(".")]

        if not files:
            print("📂 No uploaded files to rebuild from")
            return

        print(f"🔄 Rebuilding chunks from {len(files)} uploaded file(s)...")

        # Import document service for text extraction and chunking
        from services.document_service import doc_service

        for filename in files:
            filepath = os.path.join(upload_dir, filename)
            if not os.path.isfile(filepath):
                continue

            try:
                text = await doc_service.extract_text(filepath, filename)
                if not text.strip():
                    print(f"  ⚠️ No text extracted from {filename}")
                    continue

                chunks = doc_service.chunk_text(text)
                doc_id = f"rebuilt_{filename}"

                # Store chunks without embeddings (keyword search only)
                start_idx = len(self.chunks)
                for i, chunk in enumerate(chunks):
                    self.chunks.append({
                        "content": chunk["content"],
                        "document": filename,
                        "document_id": doc_id,
                        "index": chunk["index"],
                        "vec_idx": start_idx + i
                    })

                print(f"  ✅ Rebuilt {len(chunks)} chunks from '{filename}'")
            except Exception as e:
                print(f"  ❌ Failed to process '{filename}': {e}")

        if self.chunks:
            self._save_index()
            print(f"🔄 Rebuild complete: {len(self.chunks)} total chunks (keyword search mode)")
        else:
            print("⚠️ No chunks rebuilt from uploaded files")

    def _create_new_index(self):
        """Create a fresh index."""
        self.embeddings = None
        self.chunks = []
        self.dimension = None

    def _save_index(self):
        """Save embeddings and chunks to disk."""
        os.makedirs(os.path.dirname(self.index_path), exist_ok=True)
        if self.embeddings is not None and len(self.embeddings) > 0:
            np.save(self.index_path, self.embeddings)
        with open(self.chunks_path, "wb") as f:
            pickle.dump(self.chunks, f)

    @staticmethod
    def _normalize(vectors: np.ndarray) -> np.ndarray:
        """L2-normalize vectors for cosine similarity."""
        norms = np.linalg.norm(vectors, axis=1, keepdims=True)
        norms = np.where(norms == 0, 1, norms)
        return vectors / norms

    async def add_document(self, chunks: List[dict], filename: str, doc_id: str):
        """Embed and add document chunks to the index."""
        if not chunks:
            return

        texts = [chunk["content"] for chunk in chunks]

        # Try to generate embeddings (may fail if API quotas exhausted)
        embedded = False
        try:
            embeddings = await llm_service.generate_embeddings(texts)
            embeddings_np = np.array(embeddings, dtype=np.float32)

            # Normalize for cosine similarity
            embeddings_np = self._normalize(embeddings_np)

            # Auto-detect dimension and handle dimension mismatch
            if self.dimension is None:
                self.dimension = embeddings_np.shape[1]
            elif self.dimension != embeddings_np.shape[1]:
                print(f"⚠️ Embedding dimension changed ({self.dimension} → {embeddings_np.shape[1]}), resetting index")
                self._create_new_index()
                self.dimension = embeddings_np.shape[1]

            # Add to index
            start_idx = len(self.embeddings) if self.embeddings is not None else 0
            if self.embeddings is not None and len(self.embeddings) > 0:
                self.embeddings = np.vstack([self.embeddings, embeddings_np])
            else:
                self.embeddings = embeddings_np
            embedded = True
        except Exception as e:
            print(f"⚠️ Embedding generation failed: {e}")
            print("📝 Storing chunks without embeddings (text search only)")
            start_idx = len(self.chunks)

        # Store chunk metadata
        for i, chunk in enumerate(chunks):
            self.chunks.append({
                "content": chunk["content"],
                "document": filename,
                "document_id": doc_id,
                "index": chunk["index"],
                "vec_idx": start_idx + i
            })

        self._save_index()
        print(f"✅ Added {len(chunks)} chunks from '{filename}' to index")

    async def search(self, query: str, top_k: int = None) -> List[dict]:
        """Search for relevant chunks using cosine similarity or keyword fallback."""
        top_k = top_k or settings.TOP_K_RESULTS

        if not self.chunks:
            return []

        # If we have embeddings, use vector search
        if self.embeddings is not None and len(self.embeddings) == len(self.chunks):
            try:
                query_embedding = await llm_service.generate_embeddings([query])
                query_np = np.array(query_embedding, dtype=np.float32)
                query_np = self._normalize(query_np)

                scores = np.dot(self.embeddings, query_np.T).flatten()
                k = min(top_k, len(scores))
                top_indices = np.argsort(scores)[::-1][:k]

                results = []
                for idx in top_indices:
                    if idx < len(self.chunks):
                        chunk = self.chunks[idx]
                        results.append({
                            "content": chunk["content"],
                            "document": chunk["document"],
                            "relevance": float(scores[idx]),
                            "index": chunk["index"]
                        })
                return results
            except Exception as e:
                print(f"⚠️ Vector search failed: {e}, using keyword search")

        # Keyword-based fallback search
        return self._keyword_search(query, top_k)

    def _keyword_search(self, query: str, top_k: int) -> List[dict]:
        """Simple keyword-based search fallback."""
        query_words = set(query.lower().split())
        scored = []
        for chunk in self.chunks:
            content_lower = chunk["content"].lower()
            # Score = number of query words found in chunk
            score = sum(1 for w in query_words if w in content_lower) / max(len(query_words), 1)
            if score > 0:
                scored.append((score, chunk))

        # Sort by score descending
        scored.sort(key=lambda x: x[0], reverse=True)

        results = []
        for score, chunk in scored[:top_k]:
            results.append({
                "content": chunk["content"],
                "document": chunk["document"],
                "relevance": round(score, 3),
                "index": chunk["index"]
            })

        # If no keyword matches, return first chunks as context
        if not results:
            for chunk in self.chunks[:top_k]:
                results.append({
                    "content": chunk["content"],
                    "document": chunk["document"],
                    "relevance": 0.5,
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
        remaining = [(i, c) for i, c in enumerate(self.chunks) if c.get("document_id") != doc_id]

        if len(remaining) == len(self.chunks):
            return  # Nothing to remove

        if remaining:
            indices = [i for i, _ in remaining]
            self.chunks = [c for _, c in remaining]
            self.embeddings = self.embeddings[indices]
        else:
            self._create_new_index()

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
        return len(self.chunks)

    @property
    def total_documents(self):
        docs = set()
        for chunk in self.chunks:
            docs.add(chunk.get("document", ""))
        return len(docs)


rag_service = RAGService()

"""Document processing service - handles file parsing, chunking."""

import os
import re
from typing import List
from datetime import datetime
from bson import ObjectId

from config import settings


class DocumentService:
    """Handles document upload, parsing, and chunking."""

    ALLOWED_EXTENSIONS = settings.ALLOWED_EXTENSIONS

    @staticmethod
    def validate_file(filename: str, file_size: int) -> tuple[bool, str]:
        """Validate uploaded file."""
        ext = os.path.splitext(filename)[1].lower()
        if ext not in settings.ALLOWED_EXTENSIONS:
            return False, f"File type {ext} not allowed. Allowed: {', '.join(settings.ALLOWED_EXTENSIONS)}"
        if file_size > settings.MAX_FILE_SIZE:
            return False, f"File too large. Max size: {settings.MAX_FILE_SIZE // (1024*1024)}MB"
        return True, "OK"

    @staticmethod
    async def extract_text(filepath: str, filename: str) -> str:
        """Extract text from a file."""
        ext = os.path.splitext(filename)[1].lower()

        if ext == ".pdf":
            return await DocumentService._extract_pdf(filepath)
        else:
            # Text-based files
            with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
                return f.read()

    @staticmethod
    async def _extract_pdf(filepath: str) -> str:
        """Extract text from PDF using PyPDF2."""
        try:
            import PyPDF2
            text = ""
            with open(filepath, "rb") as f:
                reader = PyPDF2.PdfReader(f)
                for page in reader.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n\n"
            return text.strip()
        except Exception as e:
            raise ValueError(f"Failed to parse PDF: {str(e)}")

    @staticmethod
    def chunk_text(text: str, chunk_size: int = None, overlap: int = None) -> List[dict]:
        """Split text into overlapping chunks for RAG."""
        chunk_size = chunk_size or settings.CHUNK_SIZE
        overlap = overlap or settings.CHUNK_OVERLAP

        # Clean up text
        text = re.sub(r'\n{3,}', '\n\n', text)
        text = re.sub(r' {2,}', ' ', text)

        # Split by paragraphs first
        paragraphs = text.split('\n\n')
        chunks = []
        current_chunk = ""

        for para in paragraphs:
            para = para.strip()
            if not para:
                continue

            if len(current_chunk) + len(para) <= chunk_size:
                current_chunk += ("\n\n" + para if current_chunk else para)
            else:
                if current_chunk:
                    chunks.append(current_chunk)
                # If paragraph itself is too long, split by sentences
                if len(para) > chunk_size:
                    sentences = re.split(r'(?<=[.!?])\s+', para)
                    current_chunk = ""
                    for sentence in sentences:
                        if len(current_chunk) + len(sentence) <= chunk_size:
                            current_chunk += (" " + sentence if current_chunk else sentence)
                        else:
                            if current_chunk:
                                chunks.append(current_chunk)
                            current_chunk = sentence
                else:
                    current_chunk = para

        if current_chunk:
            chunks.append(current_chunk)

        # Add overlap
        overlapped_chunks = []
        for i, chunk in enumerate(chunks):
            chunk_data = {
                "content": chunk,
                "index": i,
                "char_count": len(chunk)
            }
            overlapped_chunks.append(chunk_data)

        return overlapped_chunks

    @staticmethod
    async def save_document_metadata(db, filename: str, file_type: str, file_size: int, num_chunks: int) -> str:
        """Save document metadata to MongoDB."""
        doc = {
            "filename": filename,
            "file_type": file_type,
            "size": file_size,
            "chunks": num_chunks,
            "uploaded_at": datetime.utcnow().isoformat(),
        }
        result = await db.documents.insert_one(doc)
        return str(result.inserted_id)

    @staticmethod
    async def get_all_documents(db) -> list:
        """Get all uploaded documents."""
        docs = []
        async for doc in db.documents.find().sort("uploaded_at", -1):
            docs.append({
                "id": str(doc["_id"]),
                "filename": doc["filename"],
                "file_type": doc["file_type"],
                "size": doc["size"],
                "chunks": doc["chunks"],
                "uploaded_at": doc["uploaded_at"]
            })
        return docs

    @staticmethod
    async def delete_document(db, doc_id: str) -> bool:
        """Delete a document and its chunks."""
        result = await db.documents.delete_one({"_id": ObjectId(doc_id)})
        await db.chunks.delete_many({"document_id": doc_id})
        return result.deleted_count > 0


doc_service = DocumentService()

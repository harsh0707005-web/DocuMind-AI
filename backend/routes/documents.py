"""Document routes - handles file upload, listing, deletion."""

import os
import shutil
from fastapi import APIRouter, UploadFile, File, HTTPException
from datetime import datetime

from database import get_db, is_local, get_local_db
from services.document_service import doc_service
from services.rag_service import rag_service
from config import settings

router = APIRouter(prefix="/api/documents", tags=["Documents"])


@router.post("/upload")
async def upload_document(file: UploadFile = File(...)):
    """Upload a document for RAG processing."""
    db = get_db()

    # Validate file
    valid, message = doc_service.validate_file(file.filename, file.size or 0)
    if not valid:
        raise HTTPException(status_code=400, detail=message)

    # Save file
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    filepath = os.path.join(settings.UPLOAD_DIR, file.filename)

    try:
        with open(filepath, "wb") as f:
            content = await file.read()
            f.write(content)

        # Extract text
        text = await doc_service.extract_text(filepath, file.filename)
        if not text.strip():
            os.remove(filepath)
            raise HTTPException(status_code=400, detail="Could not extract text from file")

        # Chunk the text
        chunks = doc_service.chunk_text(text)

        # Save metadata
        file_ext = os.path.splitext(file.filename)[1].lower()
        if is_local():
            ldb = get_local_db()
            doc_id = ldb.insert_one("documents", {
                "filename": file.filename,
                "file_type": file_ext,
                "size": len(content),
                "chunks": len(chunks),
                "uploaded_at": datetime.utcnow().isoformat()
            })
        else:
            doc_id = await doc_service.save_document_metadata(
                db, file.filename, file_ext, len(content), len(chunks)
            )

        # Add to vector index
        await rag_service.add_document(chunks, file.filename, doc_id)

        return {
            "message": f"Document '{file.filename}' uploaded successfully",
            "document_id": doc_id,
            "chunks": len(chunks),
            "characters": len(text)
        }

    except HTTPException:
        raise
    except Exception as e:
        if os.path.exists(filepath):
            os.remove(filepath)
        raise HTTPException(status_code=500, detail=f"Error processing file: {str(e)}")


@router.get("/")
async def list_documents():
    """List all uploaded documents."""
    if is_local():
        ldb = get_local_db()
        docs = ldb.find("documents", sort_key="uploaded_at")
        docs = [{"id": d["_id"], "filename": d["filename"], "file_type": d.get("file_type",""), "size": d.get("size",0), "chunks": d.get("chunks",0), "uploaded_at": d.get("uploaded_at","")} for d in docs]
    else:
        db = get_db()
        docs = await doc_service.get_all_documents(db)
    return {
        "documents": docs,
        "total": len(docs),
        "total_chunks": rag_service.total_chunks
    }


@router.delete("/{doc_id}")
async def delete_document(doc_id: str):
    """Delete a document and its embeddings."""
    if is_local():
        ldb = get_local_db()
        deleted = ldb.delete_one("documents", doc_id)
    else:
        db = get_db()
        deleted = await doc_service.delete_document(db, doc_id)

    if not deleted:
        raise HTTPException(status_code=404, detail="Document not found")

    rag_service.remove_document(doc_id)

    return {"message": "Document deleted successfully"}


@router.delete("/")
async def delete_all_documents():
    """Delete all documents and reset the index."""
    if is_local():
        ldb = get_local_db()
        ldb.delete_many("documents")
    else:
        db = get_db()
        await db.documents.delete_many({})
        await db.chunks.delete_many({})

    # Clear uploads folder
    if os.path.exists(settings.UPLOAD_DIR):
        for f in os.listdir(settings.UPLOAD_DIR):
            fpath = os.path.join(settings.UPLOAD_DIR, f)
            if os.path.isfile(fpath):
                os.remove(fpath)

    # Reset FAISS index
    rag_service._create_new_index()
    rag_service._save_index()

    return {"message": "All documents deleted"}

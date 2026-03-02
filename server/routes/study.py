"""Study routes - quiz generation, flashcards, summarization."""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional

from services.llm_service import llm_service
from services.rag_service import rag_service

router = APIRouter(prefix="/api/study", tags=["Study Tools"])


class StudyRequest(BaseModel):
    model: str = "gpt-4"
    num_items: int = 5
    topic: Optional[str] = None


@router.post("/quiz")
async def generate_quiz(request: StudyRequest):
    """Generate quiz questions from uploaded documents."""
    context = rag_service.get_all_context(max_chars=6000)

    if not context:
        raise HTTPException(status_code=400, detail="No documents uploaded. Upload documents first to generate quizzes.")

    if request.topic:
        # Search for topic-specific content
        results = await rag_service.search(request.topic, top_k=8)
        if results:
            context = "\n\n".join([r["content"] for r in results])

    try:
        quiz_data = await llm_service.generate_quiz(
            context=context,
            num_questions=request.num_items,
            model=request.model
        )
        return {
            "topic": request.topic or "All Documents",
            "questions": quiz_data.get("questions", [])
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/flashcards")
async def generate_flashcards(request: StudyRequest):
    """Generate flashcards from uploaded documents."""
    context = rag_service.get_all_context(max_chars=6000)

    if not context:
        raise HTTPException(status_code=400, detail="No documents uploaded. Upload documents first to generate flashcards.")

    if request.topic:
        results = await rag_service.search(request.topic, top_k=8)
        if results:
            context = "\n\n".join([r["content"] for r in results])

    try:
        cards_data = await llm_service.generate_flashcards(
            context=context,
            num_cards=request.num_items,
            model=request.model
        )
        return {
            "topic": request.topic or "All Documents",
            "cards": cards_data.get("cards", [])
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/summarize")
async def summarize_documents(request: StudyRequest):
    """Summarize uploaded documents."""
    context = rag_service.get_all_context(max_chars=8000)

    if not context:
        raise HTTPException(status_code=400, detail="No documents uploaded. Upload documents first to summarize.")

    if request.topic:
        results = await rag_service.search(request.topic, top_k=10)
        if results:
            context = "\n\n".join([r["content"] for r in results])

    try:
        summary_data = await llm_service.generate_summary(
            context=context,
            model=request.model
        )
        return {
            "summary": summary_data.get("summary", ""),
            "key_points": summary_data.get("key_points", []),
            "word_count": len(context.split())
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats")
async def get_study_stats():
    """Get document statistics."""
    return {
        "total_chunks": rag_service.total_chunks,
        "total_documents": rag_service.total_documents,
        "index_ready": rag_service.total_chunks > 0
    }

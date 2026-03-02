"""DocuMind AI - FastAPI Backend Server."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from config import settings
from database import connect_db, close_db
from routes.chat import router as chat_router
from routes.documents import router as documents_router
from routes.study import router as study_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifecycle: startup and shutdown."""
    await connect_db()
    print("🧠 DocuMind AI Backend is ready!")
    print(f"📊 OpenAI: {'✅ Configured' if settings.OPENAI_API_KEY else '❌ Not set'}")
    print(f"🌟 Gemini: {'✅ Configured' if settings.GEMINI_API_KEY else '❌ Not set'}")
    yield
    await close_db()


app = FastAPI(
    title="DocuMind AI",
    description="Intelligent Document Q&A Assistant with RAG pipeline, multi-LLM support, and study tools.",
    version="1.0.0",
    lifespan=lifespan
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routes
app.include_router(chat_router)
app.include_router(documents_router)
app.include_router(study_router)


@app.get("/")
async def root():
    return {
        "name": "DocuMind AI",
        "version": "1.0.0",
        "status": "running",
        "endpoints": {
            "docs": "/docs",
            "chat": "/api/chat/",
            "documents": "/api/documents/",
            "study": "/api/study/"
        }
    }


@app.get("/api/health")
async def health_check():
    return {
        "status": "healthy",
        "openai_configured": bool(settings.OPENAI_API_KEY),
        "gemini_configured": bool(settings.GEMINI_API_KEY)
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)

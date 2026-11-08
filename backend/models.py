"""Pydantic models for request/response schemas."""

from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


# --- Chat Models ---
class ChatRequest(BaseModel):
    message: str
    conversation_id: Optional[str] = None
    model: str = "gpt-4"  # "gpt-4" or "gemini"
    mode: str = "chat"  # "chat", "quiz", "summarize", "flashcard"


class SourceChunk(BaseModel):
    content: str
    document: str
    relevance: float


class ChatResponse(BaseModel):
    model_config = {"protected_namespaces": ()}

    reply: str
    conversation_id: str
    sources: List[SourceChunk] = []
    model_used: str
    tokens_used: Optional[int] = None


class ConversationSummary(BaseModel):
    id: str
    title: str
    message_count: int
    model: str
    created_at: str
    last_message: str


# --- Document Models ---
class DocumentInfo(BaseModel):
    id: str
    filename: str
    file_type: str
    size: int
    chunks: int
    uploaded_at: str


class DocumentListResponse(BaseModel):
    documents: List[DocumentInfo]
    total: int


# --- Study Models ---
class QuizQuestion(BaseModel):
    question: str
    options: List[str]
    correct: int
    explanation: str


class QuizResponse(BaseModel):
    topic: str
    questions: List[QuizQuestion]


class Flashcard(BaseModel):
    front: str
    back: str


class FlashcardResponse(BaseModel):
    topic: str
    cards: List[Flashcard]


class SummaryResponse(BaseModel):
    summary: str
    key_points: List[str]
    word_count: int

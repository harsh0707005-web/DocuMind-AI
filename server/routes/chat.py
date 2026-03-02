"""Chat routes - handles conversations and RAG-based Q&A."""

from fastapi import APIRouter, HTTPException
from datetime import datetime
from bson import ObjectId

from models import ChatRequest, ChatResponse
from database import get_db
from services.rag_service import rag_service

router = APIRouter(prefix="/api/chat", tags=["Chat"])


@router.post("/", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """Send a message and get an AI response with RAG context."""
    db = get_db()

    # Get or create conversation
    conversation_id = request.conversation_id
    chat_history = []

    if conversation_id:
        # Load chat history
        messages = await db.messages.find(
            {"conversation_id": conversation_id}
        ).sort("timestamp", 1).to_list(length=50)
        chat_history = [{"role": m["role"], "content": m["content"]} for m in messages]
    else:
        # Create new conversation
        conv = {
            "title": request.message[:60] + ("..." if len(request.message) > 60 else ""),
            "model": request.model,
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat(),
            "message_count": 0
        }
        result = await db.conversations.insert_one(conv)
        conversation_id = str(result.inserted_id)

    # Save user message
    user_msg = {
        "conversation_id": conversation_id,
        "role": "user",
        "content": request.message,
        "timestamp": datetime.utcnow().isoformat()
    }
    await db.messages.insert_one(user_msg)

    try:
        # Generate response using RAG
        result = await rag_service.query_with_rag(
            query=request.message,
            model=request.model,
            chat_history=chat_history,
            mode=request.mode
        )

        # Save assistant message
        assistant_msg = {
            "conversation_id": conversation_id,
            "role": "assistant",
            "content": result["reply"],
            "sources": result.get("sources", []),
            "timestamp": datetime.utcnow().isoformat()
        }
        await db.messages.insert_one(assistant_msg)

        # Update conversation
        await db.conversations.update_one(
            {"_id": ObjectId(conversation_id)},
            {
                "$set": {
                    "updated_at": datetime.utcnow().isoformat(),
                    "last_message": result["reply"][:100]
                },
                "$inc": {"message_count": 2}
            }
        )

        return ChatResponse(
            reply=result["reply"],
            conversation_id=conversation_id,
            sources=result.get("sources", []),
            model_used=result["model_used"],
            tokens_used=result.get("tokens_used")
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/conversations")
async def get_conversations():
    """Get all conversations."""
    db = get_db()
    conversations = []
    async for conv in db.conversations.find().sort("updated_at", -1):
        conversations.append({
            "id": str(conv["_id"]),
            "title": conv.get("title", "Untitled"),
            "message_count": conv.get("message_count", 0),
            "model": conv.get("model", "gpt-4"),
            "created_at": conv.get("created_at", ""),
            "last_message": conv.get("last_message", "")
        })
    return {"conversations": conversations}


@router.get("/conversations/{conversation_id}/messages")
async def get_messages(conversation_id: str):
    """Get all messages in a conversation."""
    db = get_db()
    messages = []
    async for msg in db.messages.find(
        {"conversation_id": conversation_id}
    ).sort("timestamp", 1):
        messages.append({
            "id": str(msg["_id"]),
            "role": msg["role"],
            "content": msg["content"],
            "sources": msg.get("sources", []),
            "timestamp": msg["timestamp"]
        })
    return {"messages": messages}


@router.delete("/conversations/{conversation_id}")
async def delete_conversation(conversation_id: str):
    """Delete a conversation and its messages."""
    db = get_db()
    await db.conversations.delete_one({"_id": ObjectId(conversation_id)})
    await db.messages.delete_many({"conversation_id": conversation_id})
    return {"message": "Conversation deleted"}

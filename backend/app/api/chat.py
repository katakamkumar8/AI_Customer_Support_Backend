"""
app/api/chat.py
POST /chat endpoint.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.engine import get_db
from app.schemas.chat import ChatRequest, ChatResponse
from app.services.chat_service import process_chat

router = APIRouter(prefix="/chat", tags=["Chat"])


@router.post("", response_model=ChatResponse, summary="Send a chat message")
async def chat(
    request: ChatRequest,
    db: AsyncSession = Depends(get_db),
) -> ChatResponse:
    """
    Process a customer support message through the multi-agent LangGraph pipeline.

    - Classifies intent
    - Retrieves relevant knowledge
    - Creates tickets when appropriate
    - Escalates to human when needed
    - Returns a final AI-composed answer
    """
    try:
        return await process_chat(request, db)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc

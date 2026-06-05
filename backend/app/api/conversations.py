"""
app/api/conversations.py
GET /conversations/{session_id}  – retrieve chat history for a session
DELETE /conversations/{session_id} – clear a session's history
"""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.engine import get_db
from app.models.conversation import ConversationMessage
from app.services.memory_service import load_history

router = APIRouter(prefix="/conversations", tags=["Conversations"])


class MessageOut(BaseModel):
    role: str
    content: str
    intent: str | None
    turn_index: int


class ConversationHistoryResponse(BaseModel):
    session_id: str
    total_messages: int
    messages: list[MessageOut]


@router.get(
    "/{session_id}",
    response_model=ConversationHistoryResponse,
    summary="Get conversation history for a session",
)
async def get_history(
    session_id: str,
    limit: int = 50,
    db: AsyncSession = Depends(get_db),
) -> ConversationHistoryResponse:
    result = await db.execute(
        select(ConversationMessage)
        .where(ConversationMessage.session_id == session_id)
        .order_by(ConversationMessage.turn_index.asc())
        .limit(limit)
    )
    rows = result.scalars().all()

    if not rows:
        raise HTTPException(
            status_code=404,
            detail=f"No conversation found for session '{session_id}'.",
        )

    return ConversationHistoryResponse(
        session_id=session_id,
        total_messages=len(rows),
        messages=[
            MessageOut(
                role=r.role,
                content=r.content,
                intent=r.intent,
                turn_index=r.turn_index,
            )
            for r in rows
        ],
    )


@router.delete(
    "/{session_id}",
    status_code=204,
    summary="Clear conversation history for a session",
)
async def clear_history(
    session_id: str,
    db: AsyncSession = Depends(get_db),
) -> None:
    await db.execute(
        delete(ConversationMessage).where(
            ConversationMessage.session_id == session_id
        )
    )

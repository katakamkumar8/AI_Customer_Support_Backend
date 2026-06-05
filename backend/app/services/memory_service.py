"""
app/services/memory_service.py
Stores and retrieves per-session conversation history in PostgreSQL.
"""

from __future__ import annotations

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.conversation import ConversationMessage


async def load_history(session_id: str, db: AsyncSession, limit: int = 20) -> list[dict]:
    """Return the last `limit` messages for a session, ordered oldest-first."""
    result = await db.execute(
        select(ConversationMessage)
        .where(ConversationMessage.session_id == session_id)
        .order_by(ConversationMessage.turn_index.asc())
        .limit(limit)
    )
    rows = result.scalars().all()
    return [{"role": r.role, "content": r.content} for r in rows]


async def get_turn_index(session_id: str, db: AsyncSession) -> int:
    result = await db.execute(
        select(func.count()).where(ConversationMessage.session_id == session_id)
    )
    return result.scalar_one()


async def save_turn(
    session_id: str,
    user_message: str,
    assistant_message: str,
    intent: str | None,
    db: AsyncSession,
) -> None:
    """Persist both user and assistant turns atomically."""
    turn_index = await get_turn_index(session_id, db)

    user_msg = ConversationMessage(
        session_id=session_id,
        role="user",
        content=user_message,
        intent=intent,
        turn_index=turn_index,
    )
    assistant_msg = ConversationMessage(
        session_id=session_id,
        role="assistant",
        content=assistant_message,
        intent=intent,
        turn_index=turn_index + 1,
    )
    db.add(user_msg)
    db.add(assistant_msg)
    await db.flush()

"""
app/services/chat_service.py
Drives the full LangGraph workflow for a single chat turn.
"""

from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from app.graph.workflow import get_compiled_graph
from app.graph.state import AgentState
from app.schemas.chat import ChatRequest, ChatResponse
from app.services.memory_service import load_history, save_turn


async def process_chat(request: ChatRequest, db: AsyncSession) -> ChatResponse:
    # 1. Load conversation history
    history = await load_history(request.session_id, db)

    # 2. Build initial state
    initial_state: AgentState = {
        "session_id": request.session_id,
        "user_message": request.message,
        "customer_name": request.customer_name or "Customer",
        "email": request.email or "unknown@example.com",
        "history": history,
        "intent": "",
        "intent_confidence": 0.0,
        "rag_answer": "",
        "rag_sources": [],
        "rag_confidence": 0.0,
        "ticket_created": False,
        "ticket_id": None,
        "escalated": False,
        "escalation_reason": "",
        "final_answer": "",
        "error": None,
    }

    # 3. Run LangGraph workflow
    graph = get_compiled_graph()
    final_state: AgentState = await graph.ainvoke(initial_state)

    # 4. Persist conversation turn
    await save_turn(
        session_id=request.session_id,
        user_message=request.message,
        assistant_message=final_state.get("final_answer", ""),
        intent=final_state.get("intent"),
        db=db,
    )

    return ChatResponse(
        session_id=request.session_id,
        intent=final_state.get("intent", "FAQ Query"),
        answer=final_state.get("final_answer", ""),
        ticket_created=final_state.get("ticket_created", False),
        ticket_id=final_state.get("ticket_id"),
        escalated=final_state.get("escalated", False),
        sources=final_state.get("rag_sources", []),
        confidence=final_state.get("rag_confidence", 1.0),
    )

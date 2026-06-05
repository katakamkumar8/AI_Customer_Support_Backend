"""
app/graph/state.py
Shared TypedDict state passed between LangGraph nodes.
"""

from __future__ import annotations

from typing import Optional
from typing_extensions import TypedDict


class AgentState(TypedDict, total=False):
    # Input
    session_id: str
    user_message: str
    customer_name: str
    email: str

    # Conversation history  (list of {"role": ..., "content": ...})
    history: list[dict]

    # Intent classification
    intent: str                     # FAQ | Technical Issue | Refund Request | Order Tracking | Human Escalation
    intent_confidence: float

    # RAG output
    rag_answer: str
    rag_sources: list[str]
    rag_confidence: float

    # Ticket
    ticket_created: bool
    ticket_id: Optional[str]

    # Escalation
    escalated: bool
    escalation_reason: str

    # Final response
    final_answer: str

    # Flow control
    error: Optional[str]

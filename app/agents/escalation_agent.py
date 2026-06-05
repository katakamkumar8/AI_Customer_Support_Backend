"""
app/agents/escalation_agent.py
Agent D – Escalation Agent.
Decides whether to escalate to a human agent.
"""

from __future__ import annotations

from app.graph.state import AgentState
from app.models.ticket import Ticket, TicketPriority, TicketStatus
from app.database.engine import AsyncSessionLocal

_LOW_CONFIDENCE_THRESHOLD = 0.45
_ESCALATION_INTENTS = {"Human Escalation"}

# Keywords that signal user dissatisfaction
_DISSATISFACTION_KEYWORDS = [
    "frustrated", "angry", "unacceptable", "useless", "terrible",
    "worst", "horrible", "ridiculous", "disappointed", "never again",
]


def _user_is_dissatisfied(message: str) -> bool:
    msg_lower = message.lower()
    return any(kw in msg_lower for kw in _DISSATISFACTION_KEYWORDS)


async def run_escalation_agent(state: AgentState) -> AgentState:
    intent = state.get("intent", "FAQ Query")
    rag_confidence = state.get("rag_confidence", 1.0)
    user_message = state.get("user_message", "")

    should_escalate = (
        intent in _ESCALATION_INTENTS
        or rag_confidence < _LOW_CONFIDENCE_THRESHOLD
        or _user_is_dissatisfied(user_message)
    )

    if not should_escalate:
        return {**state, "escalated": False}

    reason = (
        "User explicitly requested human support."
        if intent in _ESCALATION_INTENTS
        else (
            "User appears dissatisfied."
            if _user_is_dissatisfied(user_message)
            else f"Low AI confidence ({rag_confidence:.0%})."
        )
    )

    # Create / update ticket with ESCALATED status
    async with AsyncSessionLocal() as session:
        ticket = Ticket(
            customer_name=state.get("customer_name", "Unknown"),
            email=state.get("email", "unknown@example.com"),
            issue_description=state.get("user_message", ""),
            status=TicketStatus.ESCALATED,
            priority=TicketPriority.CRITICAL,
            session_id=state.get("session_id"),
            intent=intent,
        )
        session.add(ticket)
        await session.commit()
        await session.refresh(ticket)
        ticket_id = ticket.id

    return {
        **state,
        "escalated": True,
        "escalation_reason": reason,
        "ticket_created": True,
        "ticket_id": state.get("ticket_id") or ticket_id,
    }

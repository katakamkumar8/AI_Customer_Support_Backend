"""
app/agents/ticket_agent.py
Agent C – Ticket Agent.
Creates support tickets in PostgreSQL for actionable intents.
"""

from __future__ import annotations

from app.graph.state import AgentState
from app.models.ticket import Ticket, TicketPriority, TicketStatus
from app.database.engine import AsyncSessionLocal

# Intents that automatically warrant a ticket
_TICKET_INTENTS = {"Refund Request", "Technical Issue", "Order Tracking"}

# Priority mapping
_PRIORITY_MAP: dict[str, TicketPriority] = {
    "Refund Request": TicketPriority.HIGH,
    "Technical Issue": TicketPriority.MEDIUM,
    "Order Tracking": TicketPriority.LOW,
    "Human Escalation": TicketPriority.CRITICAL,
    "FAQ Query": TicketPriority.LOW,
}


async def run_ticket_agent(state: AgentState) -> AgentState:
    intent = state.get("intent", "FAQ Query")

    if intent not in _TICKET_INTENTS:
        return {**state, "ticket_created": False, "ticket_id": None}

    priority = _PRIORITY_MAP.get(intent, TicketPriority.MEDIUM)

    async with AsyncSessionLocal() as session:
        ticket = Ticket(
            customer_name=state.get("customer_name", "Unknown"),
            email=state.get("email", "unknown@example.com"),
            issue_description=state.get("user_message", ""),
            status=TicketStatus.OPEN,
            priority=priority,
            session_id=state.get("session_id"),
            intent=intent,
        )
        session.add(ticket)
        await session.commit()
        await session.refresh(ticket)
        ticket_id = ticket.id

    return {**state, "ticket_created": True, "ticket_id": ticket_id}

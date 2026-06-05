"""
app/services/ticket_service.py
CRUD operations for support tickets.
"""

from __future__ import annotations

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.ticket import Ticket
from app.schemas.ticket import TicketCreate, TicketUpdate


async def create_ticket(data: TicketCreate, db: AsyncSession) -> Ticket:
    ticket = Ticket(
        customer_name=data.customer_name,
        email=data.email,
        issue_description=data.issue_description,
        priority=data.priority,
        session_id=data.session_id,
        intent=data.intent,
    )
    db.add(ticket)
    await db.flush()
    await db.refresh(ticket)
    return ticket


async def get_ticket(ticket_id: str, db: AsyncSession) -> Ticket | None:
    result = await db.execute(select(Ticket).where(Ticket.id == ticket_id))
    return result.scalar_one_or_none()


async def list_tickets(
    db: AsyncSession,
    skip: int = 0,
    limit: int = 20,
) -> tuple[int, list[Ticket]]:
    count_result = await db.execute(select(func.count()).select_from(Ticket))
    total = count_result.scalar_one()

    result = await db.execute(
        select(Ticket).order_by(Ticket.created_at.desc()).offset(skip).limit(limit)
    )
    tickets = result.scalars().all()
    return total, list(tickets)


async def update_ticket(
    ticket_id: str, data: TicketUpdate, db: AsyncSession
) -> Ticket | None:
    ticket = await get_ticket(ticket_id, db)
    if not ticket:
        return None
    if data.status is not None:
        ticket.status = data.status
    if data.priority is not None:
        ticket.priority = data.priority
    if data.issue_description is not None:
        ticket.issue_description = data.issue_description
    await db.flush()
    await db.refresh(ticket)
    return ticket

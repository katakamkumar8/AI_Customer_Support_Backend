"""
tests/services/test_ticket_service.py
Unit tests for the ticket CRUD service.
"""

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas.ticket import TicketCreate, TicketUpdate
from app.models.ticket import TicketPriority, TicketStatus
from app.services.ticket_service import (
    create_ticket,
    get_ticket,
    list_tickets,
    update_ticket,
)


@pytest.mark.asyncio
async def test_create_ticket(db_session: AsyncSession):
    data = TicketCreate(
        customer_name="Frank",
        email="frank@example.com",
        issue_description="App crashes on login.",
        priority=TicketPriority.HIGH,
    )
    ticket = await create_ticket(data, db_session)
    assert ticket.id.startswith("SUP-")
    assert ticket.customer_name == "Frank"
    assert ticket.status == TicketStatus.OPEN
    assert ticket.priority == TicketPriority.HIGH


@pytest.mark.asyncio
async def test_get_ticket_found(db_session: AsyncSession):
    data = TicketCreate(
        customer_name="Grace",
        email="grace@example.com",
        issue_description="Cannot checkout.",
    )
    created = await create_ticket(data, db_session)
    fetched = await get_ticket(created.id, db_session)
    assert fetched is not None
    assert fetched.id == created.id


@pytest.mark.asyncio
async def test_get_ticket_not_found(db_session: AsyncSession):
    result = await get_ticket("SUP-000000", db_session)
    assert result is None


@pytest.mark.asyncio
async def test_list_tickets(db_session: AsyncSession):
    for i in range(3):
        await create_ticket(
            TicketCreate(
                customer_name=f"User{i}",
                email=f"u{i}@test.com",
                issue_description="Test",
            ),
            db_session,
        )
    total, tickets = await list_tickets(db_session, skip=0, limit=10)
    assert total >= 3
    assert len(tickets) >= 3


@pytest.mark.asyncio
async def test_update_ticket_status(db_session: AsyncSession):
    ticket = await create_ticket(
        TicketCreate(
            customer_name="Hank",
            email="hank@example.com",
            issue_description="Slow loading.",
        ),
        db_session,
    )
    updated = await update_ticket(
        ticket.id, TicketUpdate(status=TicketStatus.RESOLVED), db_session
    )
    assert updated.status == TicketStatus.RESOLVED


@pytest.mark.asyncio
async def test_update_ticket_not_found(db_session: AsyncSession):
    result = await update_ticket(
        "SUP-ZZZZZZ", TicketUpdate(status=TicketStatus.CLOSED), db_session
    )
    assert result is None

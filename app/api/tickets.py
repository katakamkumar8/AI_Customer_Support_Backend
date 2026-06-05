"""
app/api/tickets.py
CRUD routes for support tickets.
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.engine import get_db
from app.schemas.ticket import (
    TicketCreate,
    TicketListResponse,
    TicketResponse,
    TicketUpdate,
)
from app.services.ticket_service import (
    create_ticket,
    get_ticket,
    list_tickets,
    update_ticket,
)

router = APIRouter(prefix="/tickets", tags=["Tickets"])


@router.post("", response_model=TicketResponse, status_code=201, summary="Create a ticket")
async def create_ticket_route(
    body: TicketCreate,
    db: AsyncSession = Depends(get_db),
) -> TicketResponse:
    ticket = await create_ticket(body, db)
    return TicketResponse.model_validate(ticket)


@router.get("", response_model=TicketListResponse, summary="List all tickets")
async def list_tickets_route(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
) -> TicketListResponse:
    total, tickets = await list_tickets(db, skip=skip, limit=limit)
    return TicketListResponse(
        total=total,
        tickets=[TicketResponse.model_validate(t) for t in tickets],
    )


@router.get("/{ticket_id}", response_model=TicketResponse, summary="Get a ticket by ID")
async def get_ticket_route(
    ticket_id: str,
    db: AsyncSession = Depends(get_db),
) -> TicketResponse:
    ticket = await get_ticket(ticket_id, db)
    if not ticket:
        raise HTTPException(status_code=404, detail=f"Ticket '{ticket_id}' not found.")
    return TicketResponse.model_validate(ticket)


@router.patch("/{ticket_id}", response_model=TicketResponse, summary="Update a ticket")
async def update_ticket_route(
    ticket_id: str,
    body: TicketUpdate,
    db: AsyncSession = Depends(get_db),
) -> TicketResponse:
    ticket = await update_ticket(ticket_id, body, db)
    if not ticket:
        raise HTTPException(status_code=404, detail=f"Ticket '{ticket_id}' not found.")
    return TicketResponse.model_validate(ticket)

"""
app/schemas/ticket.py
Pydantic v2 request / response schemas for the ticket API.
"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr, Field

from app.models.ticket import TicketPriority, TicketStatus


# ── Request ───────────────────────────────────────────────────────────────────

class TicketCreate(BaseModel):
    customer_name: str = Field(..., min_length=1, max_length=255, examples=["Jane Doe"])
    email: EmailStr = Field(..., examples=["jane@example.com"])
    issue_description: str = Field(..., min_length=5, examples=["My order hasn't arrived."])
    priority: TicketPriority = Field(default=TicketPriority.MEDIUM)
    session_id: Optional[str] = None
    intent: Optional[str] = None


class TicketUpdate(BaseModel):
    status: Optional[TicketStatus] = None
    priority: Optional[TicketPriority] = None
    issue_description: Optional[str] = None


# ── Response ──────────────────────────────────────────────────────────────────

class TicketResponse(BaseModel):
    model_config = {"from_attributes": True}

    id: str
    customer_name: str
    email: str
    issue_description: str
    status: TicketStatus
    priority: TicketPriority
    session_id: Optional[str]
    intent: Optional[str]
    created_at: datetime
    updated_at: datetime


class TicketListResponse(BaseModel):
    total: int
    tickets: list[TicketResponse]

"""
app/schemas/chat.py
Pydantic v2 request / response schemas for the chat API.
"""

from typing import Optional
from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    session_id: str = Field(..., examples=["session-abc-123"])
    message: str = Field(..., min_length=1, examples=["I want a refund for my order."])
    customer_name: Optional[str] = Field(default="Customer", examples=["Jane Doe"])
    email: Optional[str] = Field(default=None, examples=["jane@example.com"])


class ChatResponse(BaseModel):
    session_id: str
    intent: str
    answer: str
    ticket_created: bool = False
    ticket_id: Optional[str] = None
    escalated: bool = False
    sources: list[str] = []
    confidence: float = 1.0

"""
app/schemas/knowledge.py
Pydantic v2 schemas for Knowledge Base management.
"""

from pydantic import BaseModel


class DocumentUploadResponse(BaseModel):
    filename: str
    chunks_stored: int
    message: str


class KBSearchRequest(BaseModel):
    query: str
    top_k: int = 5


class KBSearchResult(BaseModel):
    content: str
    source: str
    score: float


class KBSearchResponse(BaseModel):
    results: list[KBSearchResult]

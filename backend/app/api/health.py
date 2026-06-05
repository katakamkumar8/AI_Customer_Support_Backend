"""
app/api/health.py
Liveness and readiness endpoints.
"""

from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter(tags=["Health"])


class HealthResponse(BaseModel):
    status: str
    version: str = "1.0.0"
    service: str = "AI Customer Support Agent"


@router.get("/health", response_model=HealthResponse, summary="Health check")
async def health() -> HealthResponse:
    return HealthResponse(status="ok")


@router.get("/", include_in_schema=False)
async def root():
    return {"message": "AI Customer Support Agent API", "docs": "/docs"}

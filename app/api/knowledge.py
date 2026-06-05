"""
app/api/knowledge.py
Knowledge base management: PDF upload, search, delete.
"""

from fastapi import APIRouter, File, HTTPException, Query, UploadFile

from app.schemas.knowledge import (
    DocumentUploadResponse,
    KBSearchRequest,
    KBSearchResponse,
    KBSearchResult,
)
from app.services.knowledge_service import (
    delete_document,
    ingest_pdf,
    search_knowledge_base,
)

router = APIRouter(prefix="/knowledge", tags=["Knowledge Base"])

_ALLOWED_CONTENT_TYPES = {"application/pdf"}
_MAX_FILE_SIZE_MB = 50


@router.post(
    "/upload",
    response_model=DocumentUploadResponse,
    status_code=201,
    summary="Upload a PDF to the knowledge base",
)
async def upload_document(file: UploadFile = File(...)) -> DocumentUploadResponse:
    if file.content_type not in _ALLOWED_CONTENT_TYPES:
        raise HTTPException(
            status_code=415,
            detail=f"Only PDF files are accepted. Got: {file.content_type}",
        )

    file_bytes = await file.read()

    if len(file_bytes) > _MAX_FILE_SIZE_MB * 1024 * 1024:
        raise HTTPException(
            status_code=413,
            detail=f"File too large. Maximum size is {_MAX_FILE_SIZE_MB} MB.",
        )

    if not file_bytes:
        raise HTTPException(status_code=400, detail="Empty file.")

    try:
        chunks_stored = await ingest_pdf(file_bytes, file.filename)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    return DocumentUploadResponse(
        filename=file.filename,
        chunks_stored=chunks_stored,
        message=f"Successfully ingested '{file.filename}' into the knowledge base.",
    )


@router.post("/search", response_model=KBSearchResponse, summary="Semantic search")
async def search_kb(body: KBSearchRequest) -> KBSearchResponse:
    try:
        hits = await search_knowledge_base(body.query, top_k=body.top_k)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    return KBSearchResponse(
        results=[
            KBSearchResult(content=h.content, source=h.source, score=h.score)
            for h in hits
        ]
    )


@router.delete("/{filename}", status_code=204, summary="Remove a document from the KB")
async def delete_doc(filename: str) -> None:
    try:
        await delete_document(filename)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc

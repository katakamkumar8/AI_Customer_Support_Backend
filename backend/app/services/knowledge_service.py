"""
app/services/knowledge_service.py
Orchestrates the PDF → chunks → embeddings → Zilliz pipeline.
"""

from __future__ import annotations

from app.rag.chunker import extract_text_from_pdf, chunk_text
from app.rag.vector_store import get_vector_store


async def ingest_pdf(file_bytes: bytes, filename: str) -> int:
    """
    Full ingestion pipeline:
    1. Extract text from PDF
    2. Chunk text
    3. Embed and store in Zilliz
    Returns the number of chunks stored.
    """
    text = extract_text_from_pdf(file_bytes, filename)
    if not text.strip():
        raise ValueError(f"No extractable text found in {filename}")

    chunks = chunk_text(text, source=filename)
    if not chunks:
        raise ValueError(f"Chunking produced zero chunks for {filename}")

    store = get_vector_store()
    texts = [c.content for c in chunks]
    sources = [c.source for c in chunks]
    stored = store.upsert_chunks(texts, sources)
    return stored


async def delete_document(filename: str) -> None:
    store = get_vector_store()
    store.delete_by_source(filename)


async def search_knowledge_base(query: str, top_k: int = 5):
    store = get_vector_store()
    return store.similarity_search(query, top_k=top_k)

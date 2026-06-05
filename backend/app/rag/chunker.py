"""
app/rag/chunker.py
PDF text extraction and recursive character-level chunking.
"""

import io
from dataclasses import dataclass

import pdfplumber
from langchain.text_splitter import RecursiveCharacterTextSplitter

from app.config import get_settings

settings = get_settings()


@dataclass
class TextChunk:
    content: str
    source: str
    chunk_index: int


def extract_text_from_pdf(file_bytes: bytes, filename: str) -> str:
    """Extract all text from a PDF byte stream."""
    text_parts: list[str] = []
    with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                text_parts.append(page_text.strip())
    return "\n\n".join(text_parts)


def chunk_text(text: str, source: str) -> list[TextChunk]:
    """Split raw text into overlapping chunks ready for embedding."""
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=settings.chunk_size,
        chunk_overlap=settings.chunk_overlap,
        separators=["\n\n", "\n", ". ", " ", ""],
    )
    raw_chunks = splitter.split_text(text)
    return [
        TextChunk(content=chunk, source=source, chunk_index=i)
        for i, chunk in enumerate(raw_chunks)
        if chunk.strip()
    ]

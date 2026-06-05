"""
tests/rag/test_chunker.py
Unit tests for the PDF chunker.
"""

import pytest
from app.rag.chunker import chunk_text, TextChunk


def test_chunk_text_basic():
    text = "Hello world. " * 100  # ~1300 chars
    chunks = chunk_text(text, source="test.pdf")
    assert len(chunks) >= 1
    for chunk in chunks:
        assert isinstance(chunk, TextChunk)
        assert chunk.source == "test.pdf"
        assert len(chunk.content) > 0


def test_chunk_text_assigns_sequential_indices():
    text = ("This is a sentence about customer support. " * 50)
    chunks = chunk_text(text, source="doc.pdf")
    indices = [c.chunk_index for c in chunks]
    assert indices == list(range(len(chunks)))


def test_chunk_text_filters_empty():
    text = "   \n\n   \n   "
    chunks = chunk_text(text, source="empty.pdf")
    assert chunks == []


def test_chunk_text_respects_chunk_size():
    long_text = "word " * 2000
    chunks = chunk_text(long_text, source="large.pdf")
    # Each chunk should be at most chunk_size + some overlap tolerance
    for chunk in chunks:
        assert len(chunk.content) <= 700   # generous upper bound


def test_chunk_source_preserved():
    chunks = chunk_text("Some support text " * 30, source="manual.pdf")
    assert all(c.source == "manual.pdf" for c in chunks)

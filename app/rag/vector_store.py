"""
app/rag/vector_store.py
Zilliz Cloud (Milvus) vector store client.
Handles collection creation, upsert, and similarity search.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from functools import lru_cache
from typing import Optional

from pymilvus import (
    Collection,
    CollectionSchema,
    DataType,
    FieldSchema,
    MilvusClient,
    connections,
    utility,
)

from app.config import get_settings
from app.rag.embeddings import get_embedding_service

settings = get_settings()

# ── Schema constants ──────────────────────────────────────────────────────────
_DIM = settings.embedding_dimension
_COLLECTION = settings.zilliz_collection_name
_MAX_TEXT_LEN = 4096
_MAX_SOURCE_LEN = 512
_INDEX_PARAMS = {
    "metric_type": "COSINE",
    "index_type": "HNSW",
    "params": {"M": 16, "efConstruction": 200},
}
_SEARCH_PARAMS = {"metric_type": "COSINE", "params": {"ef": 100}}


@dataclass
class SearchResult:
    id: str
    content: str
    source: str
    score: float


class VectorStore:
    """Thin wrapper around the Milvus Python SDK for Zilliz Cloud."""

    def __init__(self) -> None:
        connections.connect(
            alias="default",
            uri=settings.zilliz_uri,
            token=settings.zilliz_token,
        )
        self._collection = self._get_or_create_collection()
        self._embedder = get_embedding_service()

    # ── Private helpers ───────────────────────────────────────────────────────

    def _get_or_create_collection(self) -> Collection:
        if utility.has_collection(_COLLECTION):
            col = Collection(_COLLECTION)
            col.load()
            return col

        fields = [
            FieldSchema(name="id", dtype=DataType.VARCHAR, is_primary=True, max_length=36),
            FieldSchema(name="content", dtype=DataType.VARCHAR, max_length=_MAX_TEXT_LEN),
            FieldSchema(name="source", dtype=DataType.VARCHAR, max_length=_MAX_SOURCE_LEN),
            FieldSchema(name="embedding", dtype=DataType.FLOAT_VECTOR, dim=_DIM),
        ]
        schema = CollectionSchema(fields, description="Customer support knowledge base")
        col = Collection(_COLLECTION, schema)
        col.create_index("embedding", _INDEX_PARAMS)
        col.load()
        return col

    # ── Public API ─────────────────────────────────────────────────────────────

    def upsert_chunks(
        self,
        texts: list[str],
        sources: list[str],
    ) -> int:
        """Embed texts and insert into the collection. Returns inserted count."""
        embeddings = self._embedder.embed_batch(texts)
        ids = [str(uuid.uuid4()) for _ in texts]

        # Truncate texts to max Milvus VARCHAR length
        safe_texts = [t[:_MAX_TEXT_LEN] for t in texts]
        safe_sources = [s[:_MAX_SOURCE_LEN] for s in sources]

        data = [ids, safe_texts, safe_sources, embeddings]
        self._collection.insert(data)
        self._collection.flush()
        return len(ids)

    def similarity_search(
        self,
        query: str,
        top_k: int = 5,
        source_filter: Optional[str] = None,
    ) -> list[SearchResult]:
        """Return top-k semantically similar chunks."""
        query_embedding = self._embedder.embed_text(query)
        expr = f'source == "{source_filter}"' if source_filter else None

        results = self._collection.search(
            data=[query_embedding],
            anns_field="embedding",
            param=_SEARCH_PARAMS,
            limit=top_k,
            expr=expr,
            output_fields=["id", "content", "source"],
        )

        hits: list[SearchResult] = []
        for hit in results[0]:
            hits.append(
                SearchResult(
                    id=str(hit.get("id") or hit.id),
                    content=hit.get("content") or "",
                    source=hit.get("source") or "",
                    score=float(hit.score),
                )
            )
        return hits

    def delete_by_source(self, source: str) -> None:
        """Remove all vectors belonging to a document source."""
        self._collection.delete(expr=f'source == "{source}"')
        self._collection.flush()


@lru_cache(maxsize=1)
def get_vector_store() -> VectorStore:
    return VectorStore()

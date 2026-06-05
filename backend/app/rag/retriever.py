"""
app/rag/retriever.py
High-level RAG retrieval + answer generation using Groq LLM.
"""

from __future__ import annotations

from dataclasses import dataclass

from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage, SystemMessage

from app.config import get_settings
from app.rag.vector_store import get_vector_store, SearchResult

settings = get_settings()

_RAG_SYSTEM_PROMPT = """You are a helpful customer support assistant.
Use ONLY the provided context to answer the question.
If the context doesn't contain enough information, say so honestly.
Be concise, professional, and empathetic.

Context:
{context}
"""


@dataclass
class RAGAnswer:
    answer: str
    sources: list[str]
    confidence: float


def _build_context(hits: list[SearchResult]) -> str:
    parts = []
    for i, hit in enumerate(hits, 1):
        parts.append(f"[{i}] (Source: {hit.source})\n{hit.content}")
    return "\n\n".join(parts)


def _estimate_confidence(hits: list[SearchResult]) -> float:
    """Simple heuristic: average cosine similarity of top results."""
    if not hits:
        return 0.0
    avg = sum(h.score for h in hits) / len(hits)
    return round(float(avg), 3)


class RAGRetriever:
    def __init__(self) -> None:
        self._store = get_vector_store()
        self._llm = ChatGroq(
            api_key=settings.groq_api_key,
            model=settings.groq_model,
            temperature=settings.groq_temperature,
            max_tokens=settings.groq_max_tokens,
        )

    def answer(self, query: str, top_k: int = 5) -> RAGAnswer:
        hits = self._store.similarity_search(query, top_k=top_k)
        confidence = _estimate_confidence(hits)

        if not hits:
            return RAGAnswer(
                answer="I don't have specific information about that in my knowledge base. "
                       "Let me connect you with a support agent.",
                sources=[],
                confidence=0.0,
            )

        context = _build_context(hits)
        system_msg = SystemMessage(content=_RAG_SYSTEM_PROMPT.format(context=context))
        human_msg = HumanMessage(content=query)

        response = self._llm.invoke([system_msg, human_msg])
        sources = list({h.source for h in hits})

        return RAGAnswer(
            answer=response.content,
            sources=sources,
            confidence=confidence,
        )


_retriever: RAGRetriever | None = None


def get_rag_retriever() -> RAGRetriever:
    global _retriever
    if _retriever is None:
        _retriever = RAGRetriever()
    return _retriever

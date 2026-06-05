"""
app/agents/knowledge_agent.py
Agent B – Knowledge Agent.
Uses RAG to answer questions from the vector knowledge base.
"""

from __future__ import annotations

from app.graph.state import AgentState
from app.rag.retriever import get_rag_retriever


def run_knowledge_agent(state: AgentState) -> AgentState:
    query = state.get("user_message", "")
    retriever = get_rag_retriever()
    result = retriever.answer(query)

    return {
        **state,
        "rag_answer": result.answer,
        "rag_sources": result.sources,
        "rag_confidence": result.confidence,
    }

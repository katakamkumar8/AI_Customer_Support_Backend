"""
tests/api/test_chat.py
Integration tests for POST /chat with mocked external services.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from httpx import AsyncClient

pytestmark = pytest.mark.asyncio

_CHAT_PAYLOAD = {
    "session_id": "test-session-001",
    "message": "What is your return policy?",
    "customer_name": "Dave",
    "email": "dave@example.com",
}


@patch("app.agents.intent_agent.ChatGroq")
@patch("app.agents.knowledge_agent.get_rag_retriever")
@patch("app.agents.response_agent.ChatGroq")
async def test_chat_faq_query(
    mock_response_llm_cls,
    mock_retriever_fn,
    mock_intent_llm_cls,
    client: AsyncClient,
):
    # ── Mock Intent LLM ──────────────────────────────────────────────────────
    intent_resp = MagicMock()
    intent_resp.content = '{"intent": "FAQ Query", "confidence": 0.95}'
    mock_intent_llm = MagicMock()
    mock_intent_llm.invoke.return_value = intent_resp
    mock_intent_llm_cls.return_value = mock_intent_llm

    # ── Mock RAG Retriever ───────────────────────────────────────────────────
    from app.rag.retriever import RAGAnswer
    mock_retriever = MagicMock()
    mock_retriever.answer.return_value = RAGAnswer(
        answer="Our return policy allows returns within 30 days.",
        sources=["returns_policy.pdf"],
        confidence=0.88,
    )
    mock_retriever_fn.return_value = mock_retriever

    # ── Mock Response LLM ────────────────────────────────────────────────────
    resp_msg = MagicMock()
    resp_msg.content = "Thank you for your question! You can return items within 30 days."
    mock_resp_llm = MagicMock()
    mock_resp_llm.invoke.return_value = resp_msg
    mock_response_llm_cls.return_value = mock_resp_llm

    response = await client.post("/chat", json=_CHAT_PAYLOAD)

    assert response.status_code == 200
    data = response.json()
    assert data["intent"] == "FAQ Query"
    assert data["session_id"] == "test-session-001"
    assert "answer" in data
    assert isinstance(data["ticket_created"], bool)
    assert isinstance(data["escalated"], bool)


@patch("app.agents.intent_agent.ChatGroq")
@patch("app.agents.knowledge_agent.get_rag_retriever")
@patch("app.agents.ticket_agent.AsyncSessionLocal")
@patch("app.agents.response_agent.ChatGroq")
async def test_chat_refund_creates_ticket(
    mock_response_llm_cls,
    mock_session_cls,
    mock_retriever_fn,
    mock_intent_llm_cls,
    client: AsyncClient,
):
    # Intent: Refund Request
    intent_resp = MagicMock()
    intent_resp.content = '{"intent": "Refund Request", "confidence": 0.97}'
    mock_intent_llm = MagicMock()
    mock_intent_llm.invoke.return_value = intent_resp
    mock_intent_llm_cls.return_value = mock_intent_llm

    # RAG
    from app.rag.retriever import RAGAnswer
    mock_retriever = MagicMock()
    mock_retriever.answer.return_value = RAGAnswer(
        answer="Refunds are processed in 5-7 business days.",
        sources=["refund_policy.pdf"],
        confidence=0.82,
    )
    mock_retriever_fn.return_value = mock_retriever

    # Ticket DB session mock
    mock_ticket = MagicMock()
    mock_ticket.id = "SUP-TEST01"
    mock_session = AsyncMock()
    mock_session.__aenter__ = AsyncMock(return_value=mock_session)
    mock_session.__aexit__ = AsyncMock(return_value=False)
    mock_session.add = MagicMock()
    mock_session.commit = AsyncMock()
    mock_session.refresh = AsyncMock(side_effect=lambda t: setattr(t, "id", "SUP-TEST01"))
    mock_session_cls.return_value = mock_session

    # Response LLM
    resp_msg = MagicMock()
    resp_msg.content = "We've logged a refund ticket SUP-TEST01 for you."
    mock_resp_llm = MagicMock()
    mock_resp_llm.invoke.return_value = resp_msg
    mock_response_llm_cls.return_value = mock_resp_llm

    response = await client.post(
        "/chat",
        json={
            "session_id": "refund-session",
            "message": "I want a refund for my order",
            "customer_name": "Eve",
            "email": "eve@example.com",
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert data["intent"] == "Refund Request"


async def test_chat_missing_message(client: AsyncClient):
    resp = await client.post("/chat", json={"session_id": "s1"})
    assert resp.status_code == 422

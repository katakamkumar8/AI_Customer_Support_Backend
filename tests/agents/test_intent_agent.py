"""
tests/agents/test_intent_agent.py
Unit tests for the Intent Classifier Agent.
"""

import pytest
from unittest.mock import MagicMock, patch

from app.agents.intent_agent import run_intent_agent
from app.graph.state import AgentState


def _make_state(message: str) -> AgentState:
    return AgentState(
        session_id="test",
        user_message=message,
        customer_name="Test User",
        email="test@example.com",
        history=[],
    )


@pytest.mark.parametrize(
    "llm_json, expected_intent",
    [
        ('{"intent": "FAQ Query", "confidence": 0.9}', "FAQ Query"),
        ('{"intent": "Refund Request", "confidence": 0.95}', "Refund Request"),
        ('{"intent": "Technical Issue", "confidence": 0.88}', "Technical Issue"),
        ('{"intent": "Order Tracking", "confidence": 0.92}', "Order Tracking"),
        ('{"intent": "Human Escalation", "confidence": 0.99}', "Human Escalation"),
    ],
)
@patch("app.agents.intent_agent.ChatGroq")
def test_intent_classification(mock_llm_cls, llm_json, expected_intent):
    mock_resp = MagicMock()
    mock_resp.content = llm_json
    mock_llm = MagicMock()
    mock_llm.invoke.return_value = mock_resp
    mock_llm_cls.return_value = mock_llm

    state = run_intent_agent(_make_state("some message"))
    assert state["intent"] == expected_intent
    assert 0.0 <= state["intent_confidence"] <= 1.0


@patch("app.agents.intent_agent.ChatGroq")
def test_fallback_on_invalid_json(mock_llm_cls):
    mock_resp = MagicMock()
    mock_resp.content = "not valid json at all"
    mock_llm = MagicMock()
    mock_llm.invoke.return_value = mock_resp
    mock_llm_cls.return_value = mock_llm

    state = run_intent_agent(_make_state("what?"))
    assert state["intent"] == "FAQ Query"
    assert state["intent_confidence"] == 0.5


@patch("app.agents.intent_agent.ChatGroq")
def test_fallback_on_unknown_intent(mock_llm_cls):
    mock_resp = MagicMock()
    mock_resp.content = '{"intent": "Unknown Intent XYZ", "confidence": 0.5}'
    mock_llm = MagicMock()
    mock_llm.invoke.return_value = mock_resp
    mock_llm_cls.return_value = mock_llm

    state = run_intent_agent(_make_state("???"))
    assert state["intent"] == "FAQ Query"


@patch("app.agents.intent_agent.ChatGroq")
def test_strips_markdown_fences(mock_llm_cls):
    mock_resp = MagicMock()
    mock_resp.content = '```json\n{"intent": "Refund Request", "confidence": 0.9}\n```'
    mock_llm = MagicMock()
    mock_llm.invoke.return_value = mock_resp
    mock_llm_cls.return_value = mock_llm

    state = run_intent_agent(_make_state("I need a refund"))
    assert state["intent"] == "Refund Request"

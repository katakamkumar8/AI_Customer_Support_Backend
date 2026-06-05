"""
tests/agents/test_escalation_agent.py
Unit tests for the Escalation Agent.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from app.agents.escalation_agent import run_escalation_agent, _user_is_dissatisfied
from app.graph.state import AgentState


def _state(**kwargs) -> AgentState:
    defaults = AgentState(
        session_id="s1",
        user_message="help me",
        customer_name="Test",
        email="t@t.com",
        history=[],
        intent="FAQ Query",
        rag_confidence=0.9,
        ticket_created=False,
        ticket_id=None,
        escalated=False,
    )
    return {**defaults, **kwargs}


@pytest.mark.asyncio
async def test_no_escalation_for_normal_faq():
    state = await run_escalation_agent(_state(intent="FAQ Query", rag_confidence=0.9))
    assert state["escalated"] is False


@pytest.mark.asyncio
async def test_escalation_for_human_escalation_intent():
    with patch("app.agents.escalation_agent.AsyncSessionLocal") as mock_cls:
        mock_session = AsyncMock()
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=False)
        mock_session.add = MagicMock()
        mock_session.commit = AsyncMock()
        mock_session.refresh = AsyncMock(
            side_effect=lambda t: setattr(t, "id", "SUP-ESC001")
        )
        mock_cls.return_value = mock_session

        state = await run_escalation_agent(
            _state(intent="Human Escalation", rag_confidence=0.9)
        )
        assert state["escalated"] is True
        assert "human" in state["escalation_reason"].lower()


@pytest.mark.asyncio
async def test_escalation_for_low_confidence():
    with patch("app.agents.escalation_agent.AsyncSessionLocal") as mock_cls:
        mock_session = AsyncMock()
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=False)
        mock_session.add = MagicMock()
        mock_session.commit = AsyncMock()
        mock_session.refresh = AsyncMock(
            side_effect=lambda t: setattr(t, "id", "SUP-LOW001")
        )
        mock_cls.return_value = mock_session

        state = await run_escalation_agent(
            _state(intent="FAQ Query", rag_confidence=0.2)
        )
        assert state["escalated"] is True
        assert "confidence" in state["escalation_reason"].lower()


@pytest.mark.parametrize(
    "message, expected",
    [
        ("I am so frustrated with your service", True),
        ("This is unacceptable!", True),
        ("I am never using your service again", True),
        ("How do I reset my password?", False),
        ("What are your business hours?", False),
    ],
)
def test_dissatisfaction_detection(message, expected):
    assert _user_is_dissatisfied(message) is expected

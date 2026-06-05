"""
tests/services/test_memory_service.py
Unit tests for the conversation memory service.
"""

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.memory_service import load_history, save_turn, get_turn_index


@pytest.mark.asyncio
async def test_save_and_load_history(db_session: AsyncSession):
    session_id = "mem-test-001"

    await save_turn(
        session_id=session_id,
        user_message="What are your hours?",
        assistant_message="We are open 9am-5pm.",
        intent="FAQ Query",
        db=db_session,
    )

    history = await load_history(session_id, db_session)
    assert len(history) == 2
    assert history[0]["role"] == "user"
    assert history[0]["content"] == "What are your hours?"
    assert history[1]["role"] == "assistant"
    assert history[1]["content"] == "We are open 9am-5pm."


@pytest.mark.asyncio
async def test_turn_index_increments(db_session: AsyncSession):
    session_id = "mem-test-002"

    for i in range(3):
        await save_turn(
            session_id=session_id,
            user_message=f"message {i}",
            assistant_message=f"reply {i}",
            intent="FAQ Query",
            db=db_session,
        )

    total = await get_turn_index(session_id, db_session)
    assert total == 6  # 3 turns × 2 messages each


@pytest.mark.asyncio
async def test_empty_history(db_session: AsyncSession):
    history = await load_history("nonexistent-session", db_session)
    assert history == []


@pytest.mark.asyncio
async def test_load_history_limit(db_session: AsyncSession):
    session_id = "mem-test-003"

    for i in range(5):
        await save_turn(
            session_id=session_id,
            user_message=f"q{i}",
            assistant_message=f"a{i}",
            intent=None,
            db=db_session,
        )

    # 5 turns = 10 messages; limit to 4
    history = await load_history(session_id, db_session, limit=4)
    assert len(history) == 4


@pytest.mark.asyncio
async def test_sessions_are_isolated(db_session: AsyncSession):
    await save_turn("session-A", "hello", "hi there", None, db_session)
    await save_turn("session-B", "world", "earth", None, db_session)

    hist_a = await load_history("session-A", db_session)
    hist_b = await load_history("session-B", db_session)

    assert all(m["content"] in ("hello", "hi there") for m in hist_a)
    assert all(m["content"] in ("world", "earth") for m in hist_b)

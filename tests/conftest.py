"""
tests/conftest.py
Shared fixtures for the entire test suite.
Uses an in-memory SQLite database so no real Postgres is needed.
"""

from __future__ import annotations

import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from unittest.mock import AsyncMock, MagicMock, patch

from app.database.engine import Base, get_db
from app.main import create_app

# ── In-memory SQLite engine for tests ─────────────────────────────────────────
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

test_engine = create_async_engine(TEST_DATABASE_URL, echo=False)
TestSessionLocal = async_sessionmaker(
    bind=test_engine, class_=AsyncSession, expire_on_commit=False
)


@pytest_asyncio.fixture(scope="session", autouse=True)
async def setup_test_db():
    """Create all tables once per test session."""
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture
async def db_session():
    """Yield a fresh DB session, rolled back after each test."""
    async with TestSessionLocal() as session:
        yield session
        await session.rollback()


@pytest_asyncio.fixture
async def client(db_session):
    """Async HTTP test client with DB dependency overridden."""

    async def override_get_db():
        yield db_session

    app = create_app()
    app.dependency_overrides[get_db] = override_get_db

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        yield ac


# ── Mock helpers ───────────────────────────────────────────────────────────────

@pytest.fixture
def mock_groq_intent():
    """Return a mock Groq response for intent classification."""
    mock_response = MagicMock()
    mock_response.content = '{"intent": "FAQ Query", "confidence": 0.95}'
    return mock_response


@pytest.fixture
def mock_groq_answer():
    mock_response = MagicMock()
    mock_response.content = "Here is your answer based on the knowledge base."
    return mock_response

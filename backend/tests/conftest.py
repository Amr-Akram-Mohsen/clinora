"""
tests/conftest.py

Pytest configuration and shared fixtures for Clinora backend tests.

Fixtures:
- engine: Async SQLAlchemy engine connected to a test database.
  Each test session creates the schema fresh and drops it after.
- session: Per-test async database session with automatic rollback.
- client: HTTPX AsyncClient against the FastAPI test app.

Test database: Uses the DATABASE_URL from .env but with the database name
suffixed with "_test" (e.g., clinora_test). The test database must exist.
Alternatively, set TEST_DATABASE_URL in the environment.
"""

import os
from collections.abc import AsyncGenerator

import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from api.deps import get_db_session
from api.main import app
from core.config import get_settings
from infrastructure.database.base import Base
from infrastructure.database.models import *  # noqa: F401,F403 — ensure all models registered

# ---------------------------------------------------------------------------
# Test database URL
# ---------------------------------------------------------------------------

_settings = get_settings()
_TEST_DB_URL = os.getenv(
    "TEST_DATABASE_URL",
    _settings.database_url.rsplit("/", 1)[0] + "/clinora_test",
)


# ---------------------------------------------------------------------------
# Engine / schema fixtures
# ---------------------------------------------------------------------------

@pytest_asyncio.fixture(scope="session")
async def engine():
    """Create a test engine and apply the full schema once per test session."""
    _engine = create_async_engine(_TEST_DB_URL, echo=False)
    async with _engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    yield _engine
    async with _engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await _engine.dispose()


@pytest_asyncio.fixture
async def session(engine) -> AsyncGenerator[AsyncSession, None]:
    """
    Per-test session that rolls back after each test.
    Ensures test isolation without dropping/recreating the schema every test.
    """
    connection = await engine.connect()
    trans = await connection.begin()
    _session = AsyncSession(
        bind=connection,
        expire_on_commit=False,
        join_transaction_mode="create_savepoint",
    )

    yield _session

    await _session.close()
    await trans.rollback()
    await connection.close()


@pytest_asyncio.fixture
async def client(session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """
    HTTPX async client that overrides the DB session dependency.
    Each test gets a fresh client backed by the isolated per-test session.
    """

    async def _override_session():
        yield session

    app.dependency_overrides[get_db_session] = _override_session

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as c:
        yield c

    app.dependency_overrides.clear()

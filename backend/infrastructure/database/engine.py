"""
infrastructure/database/engine.py

SQLAlchemy async engine and session factory.

Responsibilities:
- Create and hold the async engine singleton.
- Provide an async session factory for dependency injection.
- Expose `get_db_session` as an async generator for use in FastAPI deps.

Notes:
- echo=True only when DATABASE_ECHO=true in config (development convenience).
- Connection pool tuning uses sensible defaults; adjust for production loads.
- Session is NOT autocommit. Each request or workflow controls its own
  transaction boundary.
"""

from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from core.config import settings

_engine = create_async_engine(
    settings.database_url,
    echo=settings.database_echo,
    pool_pre_ping=True,       # Detect stale connections before use
    pool_size=10,
    max_overflow=20,
)

_async_session_factory = async_sessionmaker(
    bind=_engine,
    class_=AsyncSession,
    expire_on_commit=False,   # Avoid lazy-loading surprises after commit
    autoflush=False,
    autocommit=False,
)


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Async generator that yields a database session per request.

    Usage (FastAPI dependency):
        async def my_route(session: AsyncSession = Depends(get_db_session)):
            ...

    The session is committed on success and rolled back on exception.
    """
    async with _async_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
